import base64

import pytest
import mock

import analyzere
from analyzere import AuthenticationError, InvalidRequestError, ServerError
import analyzere.requestor
from analyzere.requestor import handle_api_error, request, request_raw, BearerAuth


class TestErrorHandling:
    def test_exception_info(self):
        resp = mock.Mock(text='{"message": "foo"}')
        with pytest.raises(InvalidRequestError) as e:
            handle_api_error(resp, 400)

        e = e.value
        assert str(e) == 'foo'
        assert e.http_body == '{"message": "foo"}'
        assert e.http_status == 400
        assert e.json_body == {'message': 'foo'}

    def test_with_empty_body(self):
        resp = mock.Mock(text='')
        with pytest.raises(InvalidRequestError) as e:
            handle_api_error(resp, 400)

        assert str(e.value) == 'None'
        assert e.value.json_body is None

    def test_with_malformed_json(self):
        resp = mock.Mock(text='{foo')
        with pytest.raises(InvalidRequestError) as e:
            handle_api_error(resp, 400)

        assert str(e.value) == 'None'
        assert e.value.json_body is None

    def test_invalid_request(self):
        resp = mock.Mock(text='')
        with pytest.raises(InvalidRequestError):
            handle_api_error(resp, 404)
        with pytest.raises(InvalidRequestError):
            handle_api_error(resp, 405)
        with pytest.raises(InvalidRequestError):
            handle_api_error(resp, 409)

    def test_authentication_error(self):
        resp = mock.Mock(text='')
        with pytest.raises(AuthenticationError):
            handle_api_error(resp, 401)

    def test_server_error(self):
        resp = mock.Mock(text='')
        with pytest.raises(ServerError):
            handle_api_error(resp, 500)


class TestRequest:
    def setup_method(self, _):
        analyzere.base_url = 'https://api'

    def teardown_method(self, _):
        analyzere.base_url = ''

    def test_request_user_agent(self, reqmock):
        reqmock.post('https://api/bar', status_code=201)
        request('post', 'bar', data=None)
        assert (reqmock.last_request.headers['User-Agent'] == analyzere.user_agent)

    def test_request_serialized(self, reqmock):
        reqmock.post('https://api/bar', status_code=201)
        request('post', 'bar', data={'foo': 'bar'})
        assert reqmock.last_request.body == '{"foo": "bar"}'

    def test_none_request_serialized(self, reqmock):
        reqmock.post('https://api/bar', status_code=201)
        request('post', 'bar', data=None)
        assert reqmock.last_request.body is None

    def test_empty_str_request_serialized(self, reqmock):
        reqmock.post('https://api/bar', status_code=201)
        request('post', 'bar', data='')
        assert reqmock.last_request.body == '""'

    def test_response_deserialized(self, reqmock):
        reqmock.get('https://api/bar', status_code=200, text='{"foo": "bar"}')
        assert request('get', 'bar') == {'foo': 'bar'}

    def test_empty_str_response_deserialized(self, reqmock):
        reqmock.get('https://api/bar', status_code=200, text='')
        assert request('get', 'bar') == ''

    def test_malformed_response(self, reqmock):
        reqmock.get('https://api/bar', status_code=200, text='{foo')
        with pytest.raises(ServerError):
            request('get', 'bar')


def setup_client_credentials(reqmock):
    reqmock.get('https://api/bar', status_code=200)

    analyzere.okta_token_url = 'https://does-not-matter-url'
    analyzere.okta_client_id = 'does-not-matter-client-id'
    analyzere.okta_client_secret = 'does-not-matter-secret'
    analyzere.okta_m2m_scope = 'does-not-matter-scope'


def teardown_client_credentials(reqmock):
    analyzere.okta_token_url = ''
    analyzere.okta_client_id = ''
    analyzere.okta_client_secret = ''
    analyzere.okta_m2m_scope = ''

    reqmock.reset()

    analyzere.requestor.bearer_auth = BearerAuth()


class TestRequestRaw:
    def setup_method(self, _):
        analyzere.base_url = 'https://api'

    def teardown_method(self, _):
        analyzere.base_url = ''

    def test_basic_authentication(self, reqmock):
        reqmock.get('https://api/bar', status_code=200)

        analyzere.username = 'user'
        analyzere.password = 'pa55'
        request_raw('get', 'bar')

        assert reqmock.last_request.headers['Authorization'] == f"Basic {base64.b64encode(b'user:pa55').decode('ascii')}"

        # Reset for other tests
        analyzere.username = ''
        analyzere.password = ''

    def test_bearer_authentication(self, reqmock):
        reqmock.get('https://api/bar', status_code=200)

        analyzere.bearer_auth_token = 's1234567890'
        request_raw('get', 'bar')

        assert reqmock.last_request.headers['Authorization'] == f'Bearer {analyzere.bearer_auth_token}'

        # Reset for other tests
        analyzere.bearer_auth_token = ''
        analyzere.requestor.bearer_auth = BearerAuth()

    def test_client_credentials_authentication(self, reqmock):
        setup_client_credentials(reqmock)

        mock_token = 's000'
        reqmock.post(analyzere.okta_token_url, text=f'{{"access_token": "{mock_token}", "expires_in": 3600}}')

        request_raw('get', 'bar')

        # One GET to API root, one POST to token URL
        assert reqmock.last_request.headers['Authorization'] == f'Bearer {mock_token}'
        assert reqmock.call_count == 2

        # No token refresh
        request_raw('get', 'bar')
        assert reqmock.call_count == 3
        assert reqmock.last_request.url == 'https://api/bar'
        assert reqmock.last_request.headers['Authorization'] == f'Bearer {mock_token}'

        teardown_client_credentials(reqmock)

    def test_client_credentials_authentication_refresh(self, reqmock):
        setup_client_credentials(reqmock)

        first_mock_token = 's001'
        reqmock.post(analyzere.okta_token_url, text=f'{{"access_token": "{first_mock_token}", "expires_in": 1}}')

        request_raw('get', 'bar')

        # One GET to API root, one POST to token URL
        assert reqmock.last_request.headers['Authorization'] == f'Bearer {first_mock_token}'
        assert reqmock.call_count == 2

        # Mock a second token and make another request
        second_mock_token = 's002'
        reqmock.post(analyzere.okta_token_url, text=f'{{"access_token": "{second_mock_token}", "expires_in": 1}}')
        request_raw('get', 'bar')

        # Additional GET to API root, additional POST to token URL
        assert reqmock.last_request.headers['Authorization'] == f'Bearer {second_mock_token}'
        assert reqmock.call_count == 4

        teardown_client_credentials(reqmock)

    def test_request_with_params(self, reqmock):
        reqmock.get('https://api/bar', status_code=200)
        request_raw('get', 'bar', params={'baz': 'qux'}, body='bazqux',
                    headers={'foo': 'bar'})

        req = reqmock.last_request
        assert req.query == 'baz=qux'
        assert req.text == 'bazqux'
        assert req.headers['foo'] == 'bar'

    def test_request_with_no_params(self, reqmock):
        reqmock.get('https://api/bar', status_code=200)
        request_raw('get', 'bar')

        req = reqmock.last_request
        assert req.url == 'https://api/bar'
        assert req.text is None

    def test_errors_handled(self, reqmock):
        reqmock.get('https://api/bar', status_code=400)
        with pytest.raises(InvalidRequestError):
            request_raw('get', 'bar')

    def test_request_retying(self, reqmock):
        reqmock.get('https://api/bar', [
            {'status_code': 503, 'headers': {'Retry-After': '1.0'}},
            {'status_code': 200, 'text': 'foo'},
        ])
        with mock.patch('time.sleep') as sleep:
            resp = request_raw('get', 'bar')
        assert resp.text == 'foo'
        sleep.assert_called_once_with(1.0)
