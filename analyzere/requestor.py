import json
import time

import requests
from oauthlib.oauth2 import BackendApplicationClient, TokenExpiredError
from requests_oauthlib import OAuth2Session
from six.moves.urllib.parse import urljoin

import analyzere
from analyzere import errors, utils


direct_auth_session = requests.Session()
oauth_session = None


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


def request_raw(method, path, params=None, body=None, headers=None,
                handle_errors=True, auto_retry=True):
    kwargs = {
        'params': params,
        'data': body,
        'headers': headers,
        'verify': analyzere.tls_verify,
    }

    url = urljoin(analyzere.base_url, path)

    session = direct_auth_session
    global oauth_session
    oauth_kwargs = {}

    # Basic Auth
    if analyzere.username and analyzere.password:
        kwargs['auth'] = (analyzere.username, analyzere.password)

    # Direct token
    elif analyzere.bearer_auth_token:
        if headers is None:
            headers = {}

        headers['Authorization'] = f'Bearer {analyzere.bearer_auth_token}'
        kwargs['headers'] = headers

    # Client Credentials
    elif analyzere.oauth_client_id:
        oauth_kwargs = {
            "include_client_id": True,
            "client_secret": analyzere.oauth_client_secret
        }

        if not oauth_session or oauth_session.client_id != analyzere.oauth_client_id:
            oauth_session = OAuth2Session(client=BackendApplicationClient(client_id=analyzere.oauth_client_id,
                                                                          scope=analyzere.oauth_scope))
            oauth_session.fetch_token(analyzere.oauth_token_url, **oauth_kwargs)

        session = oauth_session

    try:
        resp = session.request(
            method,
            url,
            **kwargs
        )
    # Raised by Client Credentials flow if the token expired
    # Not using auto-refresh because that sends a request of grant type `refresh_token`, and
    # Client Credentials doesn't support refresh tokens.
    except TokenExpiredError:
        oauth_session.fetch_token(analyzere.oauth_token_url, **oauth_kwargs)
        resp = session.request(
            method,
            url,
            **kwargs
        )

    # Handle HTTP 503 with the Retry-After header by automatically retrying
    # request after sleeping for the recommended amount of time
    retry_after = resp.headers.get('Retry-After')
    while auto_retry and (resp.status_code == 503 and retry_after):
        time.sleep(float(retry_after))
        # Repeat original request after Retry-After time has elapsed.
        resp = session.request(method, url,
                               **kwargs)
        retry_after = resp.headers.get('Retry-After')

    if handle_errors and (not 200 <= resp.status_code < 300):
        handle_api_error(resp, resp.status_code)

    return resp
