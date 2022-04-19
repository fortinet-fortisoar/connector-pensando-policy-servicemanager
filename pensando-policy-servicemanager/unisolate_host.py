"""unisolate_host operation"""

from connectors.core.connector import get_logger, ConnectorError
from .constants import LOGGER_NAME
from .utils import invoke_rest_endpoint
from .get_network_security_policies import get_network_security_policies


logger = get_logger(LOGGER_NAME)


def unisolate_host(config, params):
    """Will delete two NetworkSecurityPolicy rules under an existing Policy.
       Deletes two rules - one to block all inbound traffic to the host and one
       to block all outbound traffic from the host.
    """
    tenant = config.get('tenant')
    host_source_ip = params.get('host_source_ip')

    if not host_source_ip:
        logger.exception('Host IP field is required but blank.')
        raise ConnectorError('Host IP field is required but blank.')

    # first query Pensando SVC Mgr to get the NetworkSecurityPolicy name
    policy_name_result = get_network_security_policies(config, params)
    policy_name = policy_name_result['items'][0]['meta']['name']
    logger.info(f'policy name: {policy_name}')

    # pull the network security policy
    endpoint = f'/configs/security/v1/tenant/{tenant}/networksecuritypolicies/{policy_name}'
    security_policy = invoke_rest_endpoint(config, endpoint, 'GET')
    rules = security_policy['spec']['rules']
    logger.info(f'rules: {rules}')

    # find matching isolation rules and delete them (inbound and outbound)
    match_list = []
    for index, rule in enumerate(rules):
        if all(
            (
                rule['proto-ports'][0]['protocol'] == 'any',
                rule['proto-ports'][0]['ports'] == '',
                rule['action'] == 'deny',
                rule['from-ip-addresses'] == [host_source_ip],
                rule['to-ip-addresses'] == ['0.0.0.0/0']
            )
        ):
            match_list.append(index)

        if all(
            (
                rule['proto-ports'][0]['protocol'] == 'any',
                rule['proto-ports'][0]['ports'] == '',
                rule['action'] == 'deny',
                rule['from-ip-addresses'] == ['0.0.0.0/0'],
                rule['to-ip-addresses'] == [host_source_ip]
            )
        ):
            match_list.append(index)

    logger.info(f'rule matches: {match_list}')

    # check length of match_list to see if there are any matches. if not fail gracefully.
    if len(match_list) < 2:
        logger.exception(f'Expected two or more rules, but found {len(match_list)}. Rule deletion aborted.')
        raise ConnectorError(f'Expected two or more rules, but found {len(match_list)}. Rule deletion aborted.')

    # ensure rules are contiguous
    if match_list[1] != match_list[0] + 1:
        logger.exception('Rules are not contiguous. Rule deletion aborted.')
        raise ConnectorError('Rules are not contiguous. Rule deletion aborted.')

    # remove the matched rules with a simple method. only works on contiguous rules.
    del rules[match_list[0]]
    del rules[match_list[0]]

    new_security_policy = {
        'kind': 'NetworkSecurityPolicy',
        'api-version': 'v1',
        'spec': {
            'attach-tenant': True,
            'rules': rules
        }
    }

    logger.info(f'Updating NetworkSecurityPolicy {policy_name} with {new_security_policy}')
    result = invoke_rest_endpoint(config, endpoint, 'PUT', new_security_policy)

    return result
