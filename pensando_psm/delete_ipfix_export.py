"""delete_ipfix_export operation """

from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint
from .constants import LOGGER_NAME


logger = get_logger(LOGGER_NAME)


def delete_ipfix_export(config, params):
    """Will delete an IPFIX Flow Export Policy with the name of:
       ftnt-<src_ip>-<collector_ip>
    """
    tenant = config.get('tenant')
    endpoint = f'/configs/monitoring/v1/tenant/{tenant}/flowExportPolicy'
    host_source_ip = params.get('host_source_ip')
    ipfix_collector_ip = params.get('ipfix_collector_ip')

    if not endpoint or not host_source_ip:
        logger.exception('Missing required input')
        raise ConnectorError('Missing required input')

    endpoint = f'{endpoint}/ftnt-{host_source_ip}-{ipfix_collector_ip}'

    api_response = invoke_rest_endpoint(config, endpoint, 'DELETE')

    return api_response
