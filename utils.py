import os
from datetime import datetime
import requests
from requests import Request, Session
import pickle
from connectors.core.connector import get_logger, ConnectorError
from .constants import LOGGER_NAME, TMP_FILE_ROOT
from .global_state import session, cookie_expiration

logger = get_logger(LOGGER_NAME)


def invoke_rest_endpoint(config, endpoint, method='GET', data=None, headers=None):
    global session
    global cookie_expiration

    if headers is None:
        headers = {'accept': 'application/json'}

    # check if we need to login
    _get_state()
    # logger.info(f'rest globals: {globals()}\nlocals: {locals()}')

    if not cookie_expiration:
        logger.info('Authentication cookie not found. Logging in.')
        _login(config)
    elif cookie_expiration and datetime.fromtimestamp(cookie_expiration) < datetime.now():
        logger.info('Authentication cookie expired. Logging in.')
        _login(config)

    server_address = config.get('server_address')
    port = config.get('port', '443')
    username = config.get('username')
    password = config.get('password')
    tenant = config.get('tenant')
    protocol = config.get('protocol', 'https').lower()
    verify_ssl = config.get('verify_ssl', True)

    if not server_address or not username or not password or not tenant:
        raise ConnectorError('Missing required parameters')

    url = f'{protocol}://{server_address}:{port}{endpoint}'

    try:
        req = Request(method, url, json=data, headers=headers)
        prepped = session.prepare_request(req)
        response = session.send(prepped, verify=verify_ssl)
        logger.info(f'REST request sent: {url}')

    except Exception as e:
        logger.exception(f'Error invoking endpoint: {endpoint}')
        raise ConnectorError(f'Error: {e}')

    if response.ok:
        return response.json()

    elif response.status_code == 401:
        logger.warning('Unauthorized request - Trying to Login...')

        # try to login - if success, then rerun the request. if login fails, then stop
        if _login(config):
            logger.info('Login Success: Retrying REST Request...')
            return invoke_rest_endpoint(config, endpoint, method, data, headers)

    else:
        logger.exception(response.content)
        raise ConnectorError(f'Request error: {response.status_code} - {response.content}')


def _login(config):
    """Returns True if login succeeds"""
    global session
    global cookie_expiration

    # logger.info(f'pre-login globals: {globals()}\nlocals: {locals()}')

    headers = {'accept': 'application/json'}
    server_address = config.get('server_address')
    endpoint = '/v1/login'
    port = config.get('port', '443')
    username = config.get('username')
    password = config.get('password')
    tenant = config.get('tenant')
    protocol = config.get('protocol', 'https').lower()
    verify_ssl = config.get('verify_ssl', True)

    if not server_address or not username or not password or not tenant:
        raise ConnectorError('Missing required parameters')

    url = f'{protocol}://{server_address}:{port}{endpoint}'
    data = {
        'username': username,
        'password': password,
        'tenant': tenant
    }

    _get_state()
    req = Request('POST', url, json=data, headers=headers)
    prepped = session.prepare_request(req)

    try:
        response = session.send(prepped, verify=verify_ssl)
        logger.info('Login: Authentication credentials sent.')

    except Exception as e:
        logger.exception(f'Login Error: {e}')
        raise ConnectorError(f'Login Error: {e}')

    if response.status_code == 401:
        logger.exception('Login Failed: Unauthorized request')
        raise ConnectorError(f'Login Failed: Unauthorized request: {response.content}')

    elif not response.ok:
        logger.exception(f'Login Failed - Bad Response Code: {response.status_code} - {response.content}')
        raise ConnectorError(f'Login Failed - Bad Response Code: {response.status_code} - {response.content}')

    cookie_found = False
    for cookie in session.cookies:
        if cookie.name == 'sid':
            cookie_found = True
            cookie_expiration = cookie.expires
            _set_state()
            break

    if cookie_found:
        expiration_str = datetime.fromtimestamp(cookie_expiration).isoformat()
        logger.info(f'Login Success - Authentication expires: {expiration_str}')
        return True
    else:
        logger.exception('Login Failed: Auth Cookie not found.')
        raise ConnectorError('Login Failed: Auth Cookie not found.')


def _get_state():
    """Load global state from disk and unpickle"""
    global session
    global cookie_expiration

    try:
        with open(os.path.join(TMP_FILE_ROOT, 'pensando_state_session'), 'rb') as f:
            session = pickle.load(f)

        with open(os.path.join(TMP_FILE_ROOT, 'pensando_state_cookie_expiration'), 'rb') as f:
            cookie_expiration = pickle.load(f)

        logger.info('Loaded session state successfully')

    except Exception as e:
        logger.warning(f'Error loading session state: {e}')


def _set_state():
    """Pickle global state and save to disk"""
    global session
    global cookie_expiration

    try:
        with open(os.path.join(TMP_FILE_ROOT, 'pensando_state_session'), 'wb') as f:
            # Pickle the Requests Session() object
            pickle.dump(session, f, pickle.HIGHEST_PROTOCOL)

        with open(os.path.join(TMP_FILE_ROOT, 'pensando_state_cookie_expiration'), 'wb') as f:
            # Pickle the cookie_expiration variable
            pickle.dump(cookie_expiration, f, pickle.HIGHEST_PROTOCOL)

    except Exception as e:
        logger.exception(f'Error saving session state: {e}')
        raise ConnectorError(f'Error saving session state: {e}')

    logger.info('Saved session state successfully')


def _debug_remove_session_state():
    try:
        os.remove(os.path.join(TMP_FILE_ROOT, 'pensando_state_session'))
        os.remove(os.path.join(TMP_FILE_ROOT, 'pensando_state_cookie_expiration'))
        logger.info('Debug: Session state removed from disk')
    except Exception as e:
        logger.warning(f'Debug: Error removing Session State from disk: {e}')


def _debug_reset_session_state():
    try:
        reset_session = requests.Session()
        reset_cookie_expiration = None
        with open(os.path.join(TMP_FILE_ROOT, 'pensando_state_session'), 'wb') as f:
            pickle.dump(reset_session, f, pickle.HIGHEST_PROTOCOL)

        with open(os.path.join(TMP_FILE_ROOT, 'pensando_state_cookie_expiration'), 'wb') as f:
            pickle.dump(reset_cookie_expiration, f, pickle.HIGHEST_PROTOCOL)
        logger.info('Debug: Session state reset on disk')
    except Exception as e:
        logger.warning(f'Debug: Error resetting Session State on disk: {e}')


def _debug_expire_cookie(config):
    global session
    global cookie_expiration

    # login to create cookie
    _login(config)

    # then set the expiration to now - 100
    try:
        for cookie in session.cookies:
            if cookie.name == 'sid':
                cookie.expires = int(datetime.timestamp(datetime.now())) - 100
                cookie_expiration = cookie.expires
                _set_state()
                logger.info('Debug: Session cookie expired on disk')
    except Exception as e:
        logger.warning(f'Debug: Error expiring session cookie on disk: {e}')
