"""Pensando Utils """

import os
from datetime import datetime
import pickle
import requests
from requests import Request
from connectors.core.connector import get_logger, ConnectorError
from .constants import LOGGER_NAME, TMP_FILE_ROOT, PSM_SESSION_FILE, PSM_COOKIE_EXP_FILE


logger = get_logger(LOGGER_NAME)


class PensandoPSM():
    """Keeps session state, including the session cookie and cookie expiration value"""

    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.cookie_expiration = None
        self.get_state()

        # login if needed
        if not self.cookie_expiration:
            logger.info('Authentication cookie not found. Logging in.')
            self.login()
        elif self.cookie_expiration and datetime.fromtimestamp(self.cookie_expiration) < datetime.now():
            logger.info('Authentication cookie expired. Logging in.')
            self.login()

    def get_state(self):
        """Load global state from disk and unpickle"""
        try:
            config_id = self.config.get('config_id', 'generic')
            psm_session_unique = f'{PSM_SESSION_FILE}_{config_id}'
            psm_cookie_exp_unique = f'{PSM_COOKIE_EXP_FILE}_{config_id}'

            with open(os.path.join(TMP_FILE_ROOT, psm_session_unique), 'rb') as file:
                self.session = pickle.load(file)

            with open(os.path.join(TMP_FILE_ROOT, psm_cookie_exp_unique), 'rb') as file:
                self.cookie_expiration = pickle.load(file)

            logger.info('Loaded session state successfully')

        except Exception as ex:
            logger.warning(f'Error loading session state: {ex}')

    def set_state(self):
        """Pickle global state and save to disk"""
        try:
            config_id = self.config.get('config_id', 'generic')
            psm_session_unique = f'{PSM_SESSION_FILE}_{config_id}'
            psm_cookie_exp_unique = f'{PSM_COOKIE_EXP_FILE}_{config_id}'

            with open(os.path.join(TMP_FILE_ROOT, psm_session_unique), 'wb') as file:
                # Pickle the Requests Session() object
                pickle.dump(self.session, file, pickle.HIGHEST_PROTOCOL)

            with open(os.path.join(TMP_FILE_ROOT, psm_cookie_exp_unique), 'wb') as file:
                # Pickle the cookie_expiration variable
                pickle.dump(self.cookie_expiration, file, pickle.HIGHEST_PROTOCOL)

        except Exception as ex:
            logger.exception(f'Error saving session state: {ex}')
            raise ConnectorError(f'Error saving session state: {ex}')

        logger.info('Saved session state successfully')

    def login(self):
        """Authenticates, grabs the cookie, and returns True if login succeeds"""
        headers = {'accept': 'application/json'}
        server_address = self.config.get('server_address')
        endpoint = '/v1/login'
        port = self.config.get('port')
        username = self.config.get('username')
        password = self.config.get('password')
        tenant = self.config.get('tenant')
        protocol = self.config.get('protocol').lower()
        verify_ssl = self.config.get('verify_ssl')

        if not all((server_address, port, username, password, tenant, protocol)):
            raise ConnectorError('Missing required parameters')

        url = f'{protocol}://{server_address}:{port}{endpoint}'
        data = {
            'username': username,
            'password': password,
            'tenant': tenant
        }

        req = Request('POST', url, json=data, headers=headers)
        prepped = self.session.prepare_request(req)

        try:
            response = self.session.send(prepped, verify=verify_ssl)
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
        for cookie in self.session.cookies:
            if cookie.name == 'sid':
                cookie_found = True
                self.cookie_expiration = cookie.expires
                self.set_state()
                break

        if cookie_found:
            expiration_str = datetime.fromtimestamp(self.cookie_expiration).isoformat()
            logger.info(f'Login Success - Authentication expires: {expiration_str}')
            return True

        logger.exception('Login Failed: Auth Cookie not found.')
        raise ConnectorError('Login Failed: Auth Cookie not found.')

    def _debug_remove_session_state(self):
        try:
            config_id = self.config.get('config_id', 'generic')
            psm_session_unique = f'{PSM_SESSION_FILE}_{config_id}'
            psm_cookie_exp_unique = f'{PSM_COOKIE_EXP_FILE}_{config_id}'
            os.remove(os.path.join(TMP_FILE_ROOT, psm_session_unique))
            os.remove(os.path.join(TMP_FILE_ROOT, psm_cookie_exp_unique))
            logger.debug('Debug: Session state removed from disk')
        except Exception as ex:
            logger.debug(f'Debug: Error removing Session State from disk: {ex}')

    def _debug_reset_session_state(self):
        try:
            config_id = self.config.get('config_id', 'generic')
            psm_session_unique = f'{PSM_SESSION_FILE}_{config_id}'
            psm_cookie_exp_unique = f'{PSM_COOKIE_EXP_FILE}_{config_id}'
            reset_session = requests.Session()
            reset_cookie_expiration = None

            with open(os.path.join(TMP_FILE_ROOT, psm_session_unique), 'wb') as file:
                pickle.dump(reset_session, file, pickle.HIGHEST_PROTOCOL)

            with open(os.path.join(TMP_FILE_ROOT, psm_cookie_exp_unique), 'wb') as file:
                pickle.dump(reset_cookie_expiration, file, pickle.HIGHEST_PROTOCOL)

            logger.debug('Session state reset on disk')
        except Exception as ex:
            logger.debug(f'Error resetting Session State on disk: {ex}')

    def _debug_expire_cookie(self):
        # login to create cookie
        self.login()
        # then set the expiration to now - 100
        try:
            for cookie in self.session.cookies:
                if cookie.name == 'sid':
                    cookie.expires = int(datetime.timestamp(datetime.now())) - 100
                    self.cookie_expiration = cookie.expires
                    self.set_state()
                    logger.debug('Debug: Session cookie expired on disk')
        except Exception as ex:
            logger.debug(f'Debug: Error expiring session cookie on disk: {ex}')


def invoke_rest_endpoint(config, endpoint, method='GET', data=None, headers=None):
    """Runs the API request"""
    if headers is None:
        headers = {'accept': 'application/json'}

    psm = PensandoPSM(config)
    server_address = config.get('server_address')
    port = config.get('port', '443')
    username = config.get('username')
    password = config.get('password')
    tenant = config.get('tenant')
    protocol = config.get('protocol').lower()
    verify_ssl = config.get('verify_ssl')

    if not all((server_address, port, username, password, tenant, protocol)):
        logger.exception('Missing required parameters')
        raise ConnectorError('Missing required parameters')

    url = f'{protocol}://{server_address}:{port}{endpoint}'

    try:
        req = Request(method, url, json=data, headers=headers)
        prepped = psm.session.prepare_request(req)
        response = psm.session.send(prepped, verify=verify_ssl)
        logger.info(f'REST request sent: {url}')

    except Exception as ex:
        logger.exception(f'Error invoking endpoint: {endpoint}')
        raise ConnectorError(f'Error: {ex}')

    if response.ok:
        return response.json()

    if response.status_code == 401:
        logger.warning('Unauthorized request - Trying to Login...')

        # try to login - if success, then rerun the request. if login fails, then stop
        if psm.login():
            logger.info('Login Success: Retrying REST Request...')
            return invoke_rest_endpoint(config, endpoint, method, data, headers)

    logger.exception(response.content)
    raise ConnectorError(f'Request error: {response.status_code} - {response.content}')


def normalize_list_input(user_input):
    """user_input can be a comma separated string or a list object. Convert to list if a string. """
    if isinstance(user_input, str):
        result = [i.strip() for i in user_input.split(',')]
        return list(filter(None, result))

    return user_input
