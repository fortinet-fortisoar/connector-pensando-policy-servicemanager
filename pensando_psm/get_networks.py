"""get_networks operation"""

from connectors.core.connector import get_logger
from .utils import invoke_rest_endpoint
from .constants import LOGGER_NAME


logger = get_logger(LOGGER_NAME)


def get_networks(config, params):
    """Get Pensando networks"""
    endpoint = '/configs/network/v1/networks'
    api_response = invoke_rest_endpoint(config, endpoint, 'GET')
    return api_response
