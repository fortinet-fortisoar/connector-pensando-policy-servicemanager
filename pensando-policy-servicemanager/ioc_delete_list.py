"""ioc_delete_list operation"""

from connectors.core.connector import get_logger, ConnectorError
from .constants import LOGGER_NAME, SENTINEL_IP
from .utils import invoke_rest_endpoint
from .get_network_security_policies import get_network_security_policies


logger = get_logger(LOGGER_NAME)


def ioc_delete_list(config, params):
    """Will delete two NetworkSecurityPolicy rules under an existing Policy.
       Deletes a rule that blocks all inbound traffic to the list of IOC IP
       addresses and one to block all outbound traffic from the the list of
       IOC IP addresses.

       IOC rules will always contain a SENTINEL_IP, which is an RFC 5737 IP
       address that should never be found in production traffic. This SENTINEL_IP
       allows us to identify IOC block rules so they can be modified or deleted.

       Block IOC rules will always look like this:

       "spec": {
         "attach-tenant": true,
         "rules": [
           {
             "proto-ports": [
               {
                 "protocol": "any",
                 "ports": ""
               }
             ],
             "action": "deny",
             "from-ip-addresses": [
               "<IOC_IP_LIST>"
             ],
             "to-ip-addresses": [
               "0.0.0.0/0"
             ]
           },
           {
             "proto-ports": [
               {
                 "protocol": "any",
                 "ports": ""
               }
             ],
             "action": "deny",
             "from-ip-addresses": [
               "0.0.0.0/0"
             ],
             "to-ip-addresses": [
               "<IOC_IP_LIST>"
             ]
           }
         ]
       }
    """
    tenant = config.get('tenant')

    # first query Pensando SVC Mgr to get the NetworkSecurityPolicy name
    policy_name_result = get_network_security_policies(config, params)
    policy_name = policy_name_result['items'][0]['meta']['name']
    logger.info(f'policy name: {policy_name}')

    # pull the network security policy
    endpoint = f'/configs/security/v1/tenant/{tenant}/networksecuritypolicies/{policy_name}'
    security_policy = invoke_rest_endpoint(config, endpoint, 'GET')
    rules = security_policy['spec']['rules']
    logger.info(f'rules: {rules}')

    # find existing IOC Block rules
    match_list = []
    for index, rule in enumerate(rules):
        if any(
            (
                SENTINEL_IP in rule.get('to-ip-addresses', ''),
                SENTINEL_IP in rule.get('from-ip-addresses', '')
            )
        ):
            match_list.append(index)

    logger.info(f'rule matches: {match_list}')

    # check length of match_list to see if there two or more matches. if not fail gracefully.
    if len(match_list) == 1:
        logger.exception('Expected two rules, but found one. Rule update aborted.')
        raise ConnectorError('Expected two rules, but found one. Rule update aborted.')

    # remove old rules
    if match_list:
        # ensure rules are contiguous
        if match_list[1] != match_list[0] + 1:
            logger.exception('Rules are not contiguous. Rule deletion aborted.')
            raise ConnectorError('Rules are not contiguous. Rule deletion aborted.')

        del rules[match_list[0]]
        del rules[match_list[0]]

    else:
        logger.exception('No matching IOC Block rules. Rule update aborted.')
        raise ConnectorError('No matching IOC Block rules. Rule update aborted.')

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
