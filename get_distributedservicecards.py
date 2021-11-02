"""get_distributedservicescards operation"""

from connectors.core.connector import get_logger
from .utils import invoke_rest_endpoint
from .constants import LOGGER_NAME


logger = get_logger(LOGGER_NAME)


def get_distributedservicecards(config, params):
    """Get Pensando distributed service cards"""
    endpoint = '/configs/cluster/v1/distributedservicecards'
    api_response = invoke_rest_endpoint(config, endpoint, 'GET')
    return api_response
