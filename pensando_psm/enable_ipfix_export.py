"""enable_ipfix_export operation """

from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint
from .constants import LOGGER_NAME
logger = get_logger(LOGGER_NAME)


def enable_ipfix_export(config, params):
    """Will create an IPFIX Flow Export Policy with the name of:
       ftnt-<src_ip>-<collector_ip>
       Exports flows for all traffic to/from the Host
    """
    tenant = config.get('tenant')
    endpoint = f'/configs/monitoring/v1/tenant/{tenant}/flowExportPolicy'
    host_source_ip = params.get('host_source_ip')
    interval = params.get('interval')
    template_interval = params.get('template_interval')
    ipfix_collector_ip = params.get('ipfix_collector_ip')
    ipfix_collector_gw_ip = params.get('ipfix_collector_gw_ip')
    ipfix_collector_protocol = params.get('ipfix_collector_protocol')
    ipfix_collector_port = params.get('ipfix_collector_port')

    if not all(
        (endpoint, host_source_ip, interval, template_interval, ipfix_collector_ip,
         ipfix_collector_protocol, ipfix_collector_port)
    ):
        logger.exception('Missing required input')
        raise ConnectorError('Missing required input')

    ipfix_name = f'ftnt-{host_source_ip}-{ipfix_collector_ip}'
    transport = f'{ipfix_collector_protocol}/{ipfix_collector_port}'

    request_body = {
        "kind": None,
        "api-version": None,
        "meta": {
            "name": ipfix_name,
            "tenant": tenant or None,
            "namespace": None,
            "generation-id": None,
            "resource-version": None,
            "uuid": None,
            "labels": None,
            "self-link": None
        },
        "spec": {
            "vrf-name": None,
            "interval": interval,
            "template-interval": template_interval,
            "format": "ipfix",
            "match-rules": [
                {
                    "source": {
                        "ip-addresses": [
                            host_source_ip
                        ]
                    },
                    "destination": {
                        "ip-addresses": [
                            "0.0.0.0/0"
                        ]
                    },
                    "app-protocol-selectors": {
                        "proto-ports": [
                            "any"
                        ]
                    }
                },
                {
                    "source": {
                        "ip-addresses": [
                            "0.0.0.0/0"
                        ]
                    },
                    "destination": {
                        "ip-addresses": [
                            host_source_ip
                        ]
                    },
                    "app-protocol-selectors": {
                        "proto-ports": [
                            "any"
                        ]
                    }
                }
            ],
            "exports": [
                {
                    "destination": ipfix_collector_ip,
                    "gateway": ipfix_collector_gw_ip,
                    "transport": transport
                }
            ]
        }
    }

    api_response = invoke_rest_endpoint(config, endpoint, 'POST', request_body)

    return api_response
