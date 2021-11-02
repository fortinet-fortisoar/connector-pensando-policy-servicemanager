"""get_alerts operation"""

from connectors.core.connector import get_logger
from .utils import invoke_rest_endpoint
from .constants import LOGGER_NAME


logger = get_logger(LOGGER_NAME)


def get_alerts(config, params):
    """Get Pensando alerts"""
    endpoint = '/configs/monitoring/v1/alerts'
    api_response = invoke_rest_endpoint(config, endpoint, 'GET')
    return api_response
