import json
import time

import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from six.moves.urllib.parse import urljoin

import analyzere
from analyzere import errors, utils


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


class BearerAuth:
    def __init__(self):
        self.oauth = None
        self.token = None
        self.expiry = None

    def _set_oauth_client(self):
        client = BackendApplicationClient(client_id=analyzere.oauth_client_id)
        self.oauth = OAuth2Session(client=client)

    def get_auth_header(self):
        if analyzere.bearer_auth_token:
            self.token = analyzere.bearer_auth_token
        else:
            # Refresh token if uninitialized or expired
            if not self.expiry or time.time() > self.expiry:
                if not self.oauth or (self.oauth.client_id != analyzere.oauth_client_id):
                    self._set_oauth_client()

                token_result = self.oauth.fetch_token(
                    token_url=analyzere.oauth_token_url,
                    client_id=analyzere.oauth_client_id,
                    client_secret=analyzere.oauth_client_secret,
                    scope=analyzere.oauth_scope)
                self.token = token_result["access_token"]
                self.expiry = time.time() + token_result["expires_in"]

        return {"authorization": "Bearer " + self.token}


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
    elif analyzere.bearer_auth_token or analyzere.oauth_client_id:
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
