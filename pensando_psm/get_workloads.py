"""get_workloads operation"""

from connectors.core.connector import get_logger
from .constants import LOGGER_NAME
from .utils import invoke_rest_endpoint


logger = get_logger(LOGGER_NAME)


def get_workloads(config, params):
    """Get Pensando workloads"""
    endpoint = '/configs/workload/v1/workloads'
    api_response = invoke_rest_endpoint(config, endpoint, 'GET')
    return api_response
