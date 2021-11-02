"""Pensando Utils """

import os
from datetime import datetime
import pickle
import requests
from requests import Request
from connectors.core.connector import get_logger, ConnectorError
from .constants import LOGGER_NAME, TMP_FILE_ROOT

logger = get_logger(LOGGER_NAME)


class PensandoState():
    """Keeps session state, including the session cookie and cookie expiration value """

    def _init_(self, session=None, cookie_expiration=None):
        self.session = session
        self.cookie_expiration = cookie_expiration


pensando = PensandoState(session=requests.Session(), cookie_expiration=None)


def invoke_rest_endpoint(config, endpoint, method='GET', data=None, headers=None):
    """Runs the API request"""
    if headers is None:
        headers = {'accept': 'application/json'}

    # check if we need to login
    _get_state()

    if not pensando.cookie_expiration:
        logger.info('Authentication cookie not found. Logging in.')
        _login(config)
    elif pensando.cookie_expiration and datetime.fromtimestamp(pensando.cookie_expiration) < datetime.now():
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
        prepped = pensando.session.prepare_request(req)
        response = pensando.session.send(prepped, verify=verify_ssl)
        logger.info(f'REST request sent: {url}')

    except Exception as ex:
        logger.exception(f'Error invoking endpoint: {endpoint}')
        raise ConnectorError(f'Error: {ex}')

    if response.ok:
        return response.json()

    if response.status_code == 401:
        logger.warning('Unauthorized request - Trying to Login...')

        # try to login - if success, then rerun the request. if login fails, then stop
        if _login(config):
            logger.info('Login Success: Retrying REST Request...')
            return invoke_rest_endpoint(config, endpoint, method, data, headers)

    logger.exception(response.content)
    raise ConnectorError(f'Request error: {response.status_code} - {response.content}')


def normalize_list_input(user_input):
    """user_input can be a comma separated string or a list object. Convert to list if a string. """
    if isinstance(user_input, str):
        result = [prot.strip() for prot in user_input.split(',')]
        return list(filter(None, result))

    return user_input


def _login(config):
    """Returns True if login succeeds"""
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
    prepped = pensando.session.prepare_request(req)

    try:
        response = pensando.session.send(prepped, verify=verify_ssl)
        logger.info('Login: Authentication credentials sent.')

    except Exception as ex:
        logger.exception(f'Login Error: {ex}')
        raise ConnectorError(f'Login Error: {ex}')

    if response.status_code == 401:
        logger.exception('Login Failed: Unauthorized request')
        raise ConnectorError(f'Login Failed: Unauthorized request: {response.content}')

    if not response.ok:
        logger.exception(f'Login Failed - Bad Response Code: {response.status_code} - {response.content}')
        raise ConnectorError(f'Login Failed - Bad Response Code: {response.status_code} - {response.content}')

    cookie_found = False
    for cookie in pensando.session.cookies:
        if cookie.name == 'sid':
            cookie_found = True
            pensando.cookie_expiration = cookie.expires
            _set_state()
            break

    if cookie_found:
        expiration_str = datetime.fromtimestamp(pensando.cookie_expiration).isoformat()
        logger.info(f'Login Success - Authentication expires: {expiration_str}')
        return True

    logger.exception('Login Failed: Auth Cookie not found.')
    raise ConnectorError('Login Failed: Auth Cookie not found.')


def _get_state():
    """Load global state from disk and unpickle"""
    try:
        with open(os.path.join(TMP_FILE_ROOT, 'pensando_state_session'), 'rb') as file:
            pensando.session = pickle.load(file)

        with open(os.path.join(TMP_FILE_ROOT, 'pensando_state_cookie_expiration'), 'rb') as file:
            pensando.cookie_expiration = pickle.load(file)

        logger.info('Loaded session state successfully')

    except Exception as ex:
        logger.warning(f'Error loading session state: {ex}')


def _set_state():
    """Pickle global state and save to disk"""
    try:
        with open(os.path.join(TMP_FILE_ROOT, 'pensando_state_session'), 'wb') as file:
            # Pickle the Requests Session() object
            pickle.dump(pensando.session, file, pickle.HIGHEST_PROTOCOL)

        with open(os.path.join(TMP_FILE_ROOT, 'pensando_state_cookie_expiration'), 'wb') as file:
            # Pickle the cookie_expiration variable
            pickle.dump(pensando.cookie_expiration, file, pickle.HIGHEST_PROTOCOL)

    except Exception as ex:
        logger.exception(f'Error saving session state: {ex}')
        raise ConnectorError(f'Error saving session state: {ex}')

    logger.info('Saved session state successfully')


def _debug_remove_session_state():
    try:
        os.remove(os.path.join(TMP_FILE_ROOT, 'pensando_state_session'))
        os.remove(os.path.join(TMP_FILE_ROOT, 'pensando_state_cookie_expiration'))
        logger.info('Debug: Session state removed from disk')
    except Exception as ex:
        logger.warning(f'Debug: Error removing Session State from disk: {ex}')


def _debug_reset_session_state():
    try:
        reset_session = requests.Session()
        reset_cookie_expiration = None
        with open(os.path.join(TMP_FILE_ROOT, 'pensando_state_session'), 'wb') as file:
            pickle.dump(reset_session, file, pickle.HIGHEST_PROTOCOL)

        with open(os.path.join(TMP_FILE_ROOT, 'pensando_state_cookie_expiration'), 'wb') as file:
            pickle.dump(reset_cookie_expiration, file, pickle.HIGHEST_PROTOCOL)
        logger.info('Debug: Session state reset on disk')
    except Exception as ex:
        logger.warning(f'Debug: Error resetting Session State on disk: {ex}')


def _debug_expire_cookie(config):
    # login to create cookie
    _login(config)

    # then set the expiration to now - 100
    try:
        for cookie in pensando.session.cookies:
            if cookie.name == 'sid':
                cookie.expires = int(datetime.timestamp(datetime.now())) - 100
                pensando.cookie_expiration = cookie.expires
                _set_state()
                logger.info('Debug: Session cookie expired on disk')
    except Exception as ex:
        logger.warning(f'Debug: Error expiring session cookie on disk: {ex}')
