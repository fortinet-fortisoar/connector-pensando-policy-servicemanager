"""health_check operation"""

from connectors.core.connector import get_logger
from .constants import LOGGER_NAME
from .utils import invoke_rest_endpoint


logger = get_logger(LOGGER_NAME)


def health_check(config=None, *args, **kwargs):
    """Get Pensando health check"""
    auth_endpoint = '/configs/workload/v1/workloads'
    invoke_rest_endpoint(config, auth_endpoint, 'GET')
    logger.info('Health Check succeeded')
    return 'Connector is Available'
