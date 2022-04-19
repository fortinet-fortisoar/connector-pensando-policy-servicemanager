"""get_network_security_policies"""

from connectors.core.connector import get_logger
from .constants import LOGGER_NAME
from .utils import invoke_rest_endpoint


logger = get_logger(LOGGER_NAME)


def get_network_security_policies(config, params):
    """Get Pensando network security policies"""
    endpoint = '/configs/security/v1/networksecuritypolicies'
    api_response = invoke_rest_endpoint(config, endpoint, 'GET')
    return api_response
