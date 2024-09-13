import json
import time
from urllib.parse import urlparse

import requests
from six.moves.urllib.parse import urljoin

import analyzere
from analyzere import errors, utils

TOKEN_EXPIRY_BUFFER = 120

session = requests.Session()


def handle_api_error(resp, code):
    body = resp.text
    json_body = None
    message = None

    try:
        json_body = json.loads(body, cls=utils.DateTimeDecoder)
    except (TypeError, ValueError):
        pass

    if isinstance(json_body, dict) and 'message' in json_body:
        message = json_body['message']

    if code in [400, 404, 405, 409]:
        raise errors.InvalidRequestError(message, body, code, json_body)
    elif code == 401:
        raise errors.AuthenticationError(
            'Failed to authenticate. Please check the username and password '
            'you provided.', body, code, json_body)
    elif code == 503:
        raise errors.RetryAfter(message, body, code, json_body)
    else:
        raise errors.ServerError(message, body, code, json_body)


def request(method, path, params=None, data=None, auto_retry=True):
    """
    method - HTTP method. e.g. get, put, post, etc.
    path - Path to resource. e.g. /loss_sets/1234
    params - Parameter to pass in the query string
    data - Dictionary of parameters to pass in the request body
    """
    body = None
    if data is not None:
        body = json.dumps(data, cls=utils.DateTimeEncoder)

    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'user-agent': analyzere.user_agent,
    }
    resp = request_raw(method, path, params=params, body=body, headers=headers,
                       auto_retry=auto_retry)
    content = resp.text
    if content:
        try:
            content = json.loads(content, cls=utils.DateTimeDecoder)
        except ValueError:
            raise errors.ServerError('Unable to parse JSON response returned '
                                     'from server.', resp, resp.status_code)
    return content


def post_to_url(url, payload):
    token_session = requests.Session()
    headers = {'content-type': "application/x-www-form-urlencoded"}

    resp = token_session.request("POST", url, payload, headers)
    return resp.text


def request_token(payload):
    response_dict = json.loads(post_to_url(analyzere.okta_token_url, payload))
    return response_dict["access_token"], response_dict["expires_in"]


def get_client_credentials_token():
    payload = (f"grant_type=client_credentials"
               f"&client_id={analyzere.okta_client_id}"
               f"&client_secret={analyzere.okta_client_secret}"
               f"&scope={analyzere.okta_m2m_scope}")

    return request_token(payload)


class BearerAuth:
    def __init__(self):
        self.token = None
        self.expiry = None

    def _set_token_and_expiry(self):
        if analyzere.bearer_auth_token:
            self.token = analyzere.bearer_auth_token

        else:
            self.token, expiry = get_client_credentials_token()
            self.expiry = time.time() + expiry

    def get_auth_header(self):
        # Set token if not initialized
        if not self.token:
            self._set_token_and_expiry()

        # Refresh token if close to expiring
        elif analyzere.okta_client_id and (time.time() > (self.expiry - TOKEN_EXPIRY_BUFFER)):
            self._set_token_and_expiry()

        auth_header = {"authorization": "Bearer " + self.token}
        return auth_header


bearer_auth = BearerAuth()


def request_raw(method, path, params=None, body=None, headers=None,
                handle_errors=True, auto_retry=True):
    kwargs = {
        'params': params,
        'data': body,
        'headers': headers,
        'verify': analyzere.tls_verify,
    }

    username = analyzere.username
    password = analyzere.password
    if username and password:
        kwargs['auth'] = (username, password)
    elif analyzere.bearer_auth_token or analyzere.okta_client_id:
        if kwargs['headers']:
            kwargs['headers'] = {**kwargs['headers'], **bearer_auth.get_auth_header()}
        else:
            kwargs['headers'] = bearer_auth.get_auth_header()

    resp = session.request(method, urljoin(analyzere.base_url, path),
                           **kwargs)

    # Handle HTTP 503 with the Retry-After header by automatically retrying
    # request after sleeping for the recommended amount of time
    retry_after = resp.headers.get('Retry-After')
    while auto_retry and (resp.status_code == 503 and retry_after):
        time.sleep(float(retry_after))
        # Repeat original request after Retry-After time has elapsed.
        resp = session.request(method, urljoin(analyzere.base_url, path),
                               **kwargs)
        retry_after = resp.headers.get('Retry-After')

    if handle_errors and (not 200 <= resp.status_code < 300):
        handle_api_error(resp, resp.status_code)

    return resp
