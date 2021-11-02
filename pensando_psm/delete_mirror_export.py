"""delete_mirror_export operation """

from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint
from .constants import LOGGER_NAME
logger = get_logger(LOGGER_NAME)


def delete_mirror_export(config, params):
    """Will delete Mirror Traffic Export Policy with the name of:
       ftnt-<src_ip>-<collector_ip>
    """
    tenant = config.get('tenant')
    endpoint = f'/configs/monitoring/v1/tenant/{tenant}/MirrorSession'
    host_source_ip = params.get('host_source_ip')
    erspan_collector_ip = params.get('erspan_collector_ip')

    if not endpoint or not host_source_ip:
        logger.exception('Missing required input')
        raise ConnectorError('Missing required input')

    endpoint = f'{endpoint}/ftnt-{host_source_ip}-{erspan_collector_ip}'

    api_response = invoke_rest_endpoint(config, endpoint, 'DELETE')

    return api_response
