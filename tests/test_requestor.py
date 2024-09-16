import base64

import pytest
import mock
import time

import analyzere
from analyzere import AuthenticationError, InvalidRequestError, ServerError
from analyzere.requestor import handle_api_error, request, request_raw


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


class TestClientCredentialsOAuth:
    def setup_method(self, _):
        self.api_path = 'bar'
        self.api_url = f'https://api/{self.api_path}'

        analyzere.base_url = 'https://api'
        analyzere.oauth_token_url = 'https://does-not-matter-url/'
        analyzere.oauth_client_id = 'does-not-matter-client-id'
        analyzere.oauth_client_secret = 'does-not-matter-secret'
        analyzere.oauth_scope = 'does-not-matter-scope'

    def teardown_method(self, _):
        analyzere.base_url = ''
        analyzere.oauth_token_url = ''
        analyzere.oauth_client_id = ''
        analyzere.oauth_client_secret = ''
        analyzere.oauth_scope = ''

        # Avoid token re-use between tests
        analyzere.requestor.session = None

    @pytest.fixture(autouse=True)
    def pretest_cleanup(self):
        # Avoid token re-use between tests
        analyzere.requestor.session = None

    def _validate_token_params(self, request_text):
        assert 'grant_type=client_credentials' in request_text
        assert f'client_id={analyzere.oauth_client_id}' in request_text
        assert f'client_secret={analyzere.oauth_client_secret}' in request_text
        assert f'scope={analyzere.oauth_scope}' in request_text

    def _make_first_request_with_token(self, reqmock, mock_token, expires_in):
        reqmock.get(self.api_url, status_code=200)

        reqmock.post(analyzere.oauth_token_url, text=f'{{"access_token": "{mock_token}", "expires_in": {expires_in}}}')

        request_raw('get', self.api_path)

        # One POST to token URL, one GET to API with bearer auth header
        assert reqmock.call_count == 2

        assert reqmock.request_history[0].url == analyzere.oauth_token_url
        assert reqmock.request_history[0].method == 'POST'
        self._validate_token_params(reqmock.request_history[0].text)

        assert reqmock.request_history[1].url == self.api_url
        assert reqmock.request_history[1].method == 'GET'
        assert reqmock.request_history[1].headers['Authorization'] == f'Bearer {mock_token}'

    def test_client_credentials_authentication(self, reqmock):
        mock_token = 's000'
        self._make_first_request_with_token(reqmock, mock_token, 3600)
        call_count_after_first_request = reqmock.call_count

        # Make another request, and given the hour-long token expiry, expect no further calls to the token endpoint
        request_raw('get', self.api_path)
        assert reqmock.call_count == call_count_after_first_request + 1
        assert reqmock.last_request.url == 'https://api/bar'

        # Expect the original token to be re-used
        assert reqmock.last_request.headers['Authorization'] == f'Bearer {mock_token}'

    def test_client_credentials_authentication_refresh(self, reqmock):
        first_mock_token = 's001'
        self._make_first_request_with_token(reqmock, first_mock_token, 1)
        call_count_after_first_request = reqmock.call_count

        # Wait for token to expire
        time.sleep(1)

        # Mock a second token and make another request
        second_mock_token = 's002'
        reqmock.post(analyzere.oauth_token_url, text=f'{{"access_token": "{second_mock_token}", "expires_in": 1}}')
        request_raw('get', self.api_path)

        # Expect additional POST to token URL given the token expiry
        assert reqmock.call_count == call_count_after_first_request + 2

        assert analyzere.oauth_token_url in reqmock.request_history[2].url
        assert reqmock.request_history[2].method == 'POST'
        self._validate_token_params(reqmock.request_history[2].text)

        assert reqmock.request_history[3].url == self.api_url
        assert reqmock.request_history[3].method == 'GET'

        # Expect to see the new token
        assert reqmock.request_history[3].headers['Authorization'] == f'Bearer {second_mock_token}'

    def test_retry_on_401(self, reqmock):
        reqmock.get(self.api_url, [
            {'status_code': 401},
            {'status_code': 200},
        ])

        first_token = 's101'
        second_token = 's102'
        reqmock.post(analyzere.oauth_token_url, [
            {'text': f'{{"access_token": "{first_token}", "expires_in": 3600}}'},
            {'text': f'{{"access_token": "{second_token}", "expires_in": 3600}}'},
        ])

        request_raw('get', self.api_path)

        assert reqmock.call_count == 4

        # Get first token, try to call API
        assert reqmock.request_history[0].url == analyzere.oauth_token_url
        assert reqmock.request_history[1].url == self.api_url
        assert reqmock.request_history[1].headers['Authorization'] == f'Bearer {first_token}'

        # Re-fetch token after 401, re-call API with new token
        assert reqmock.request_history[2].url == analyzere.oauth_token_url
        assert reqmock.request_history[3].url == self.api_url
        assert reqmock.request_history[3].headers['Authorization'] == f'Bearer {second_token}'


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

    def test_request_retrying(self, reqmock):
        reqmock.get('https://api/bar', [
            {'status_code': 503, 'headers': {'Retry-After': '1.0'}},
            {'status_code': 200, 'text': 'foo'},
        ])
        with mock.patch('time.sleep') as sleep:
            resp = request_raw('get', 'bar')
        assert resp.text == 'foo'
        sleep.assert_called_once_with(1.0)
