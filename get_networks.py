import requests
from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint
from .constants import LOGGER_NAME
logger = get_logger(LOGGER_NAME)


def get_networks(config, params):
    endpoint = '/configs/network/v1/networks'
    api_response = invoke_rest_endpoint(config, endpoint, 'GET')
    return api_response