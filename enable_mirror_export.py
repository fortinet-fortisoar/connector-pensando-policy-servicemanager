"""enable_mirror_export operation """

from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint, normalize_list_input
from .constants import LOGGER_NAME
logger = get_logger(LOGGER_NAME)


def enable_mirror_export(config, params):
    """Will create Mirror Traffic Export Policy with the name of:
       ftnt-<src_ip>-<collector_ip>
       Creates two rules - one for inbound traffic and one for outbound
    """
    tenant = config.get('tenant')
    endpoint = f'/configs/monitoring/v1/tenant/{tenant}/MirrorSession'
    host_source_ip = params.get('host_source_ip')
    erspan_id = params.get('erspan_id')
    packet_size = params.get('packet_size')
    erspan_type = params.get('erspan_type')
    erspan_collector_ip = params.get('erspan_collector_ip')
    erspan_collector_gw_ip = params.get('erspan_collector_gw_ip')
    strip_vlan = params.get('strip_vlan')
    erspan_match_dest_ip = params.get('erspan_match_dest_ip')
    erspan_match_protocols = params.get('erspan_match_protocols')

    if not endpoint or not host_source_ip or not erspan_id or not erspan_type or not erspan_collector_ip:
        raise ConnectorError('Missing required input')

    erspan_name = f'ftnt-{host_source_ip}-{erspan_collector_ip}'

    # user input can be a comma separated string or a list object. Convert to list if a string.
    erspan_match_dest_ip = normalize_list_input(erspan_match_dest_ip)
    erspan_match_protocols = normalize_list_input(erspan_match_protocols)

    logger.info(f'erspan_name = {erspan_name}')
    logger.info(f'erspan_match_dest_ip = {erspan_match_dest_ip}')
    logger.info(f'erspan_match_protocols = {erspan_match_protocols}')

    request_body = {
        "kind": None,
        "api-version": None,
        "meta": {
            "name": erspan_name,
            "tenant": tenant or None,
            "namespace": None,
            "generation-id": None,
            "resource-version": None,
            "uuid": None,
            "labels": None,
            "self-link": None
        },
        "spec": {
            "packet-size": packet_size or None,
            "collectors": [
                {
                    "type": erspan_type,
                    "export-config": {
                        "destination": erspan_collector_ip,
                        "gateway": erspan_collector_gw_ip or None
                    },
                    "strip-vlan-hdr": strip_vlan
                }
            ],
            "match-rules": [
                {
                    "source": {
                        "ip-addresses": [
                            host_source_ip
                        ]
                    },
                    "destination": {
                        "ip-addresses": erspan_match_dest_ip
                    },
                    "app-protocol-selectors": {
                        "proto-ports": erspan_match_protocols
                    }
                },
                {
                    "source": {
                        "ip-addresses": erspan_match_dest_ip
                    },
                    "destination": {
                        "ip-addresses": [
                            host_source_ip
                        ]
                    },
                    "app-protocol-selectors": {
                        "proto-ports": erspan_match_protocols
                    }
                }
            ],
            "packet-filters": [
                "all-packets"
            ],
            "interfaces": None,
            "span-id": erspan_id
        }
    }

    api_response = invoke_rest_endpoint(config, endpoint, 'POST', request_body)

    return api_response
