import requests
from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint
from .constants import LOGGER_NAME
logger = get_logger(LOGGER_NAME)


def get_workloads(config, params):
    endpoint = '/configs/workload/v1/workloads'
    api_response = invoke_rest_endpoint(config, endpoint, 'GET')
    return api_response