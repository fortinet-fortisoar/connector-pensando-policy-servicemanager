from .utils import invoke_rest_endpoint
from connectors.core.connector import get_logger, ConnectorError
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)


def health_check(config=None, *args, **kwargs):
    auth_endpoint = '/configs/workload/v1/workloads'
    invoke_rest_endpoint(config, auth_endpoint, 'GET')
    logger.info('Health Check succeeded')
    return 'Connector is Available'
