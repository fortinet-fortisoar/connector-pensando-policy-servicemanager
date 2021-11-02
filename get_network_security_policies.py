from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)


def get_network_security_policies(config, params):
    endpoint = '/configs/security/v1/networksecuritypolicies'
    api_response = invoke_rest_endpoint(config, endpoint, 'GET')
    return api_response
