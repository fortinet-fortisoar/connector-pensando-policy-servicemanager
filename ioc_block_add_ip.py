from collections import deque
from connectors.core.connector import get_logger, ConnectorError
from .constants import LOGGER_NAME, SENTINEL_IP
from .get_network_security_policies import get_network_security_policies
from .utils import invoke_rest_endpoint


logger = get_logger(LOGGER_NAME)


def ioc_block_add_ip(config, params):
    """Will create two NetworkSecurityPolicy rules under an existing Policy.
       Creates two rules to block all inbound traffic to the list of IOC IP
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
    ioc_ip = params.get('ioc_ip')

    # ioc_ip can be a comma separated string or a list object. Convert to list if a string.
    if isinstance(ioc_ip, str):
        ioc_ip = [ip.strip() for ip in ioc_ip.split(',')]
        ioc_ip = list(filter(None, ioc_ip))

    if not ioc_ip:
        logger.exception('IOC IP field is required but blank.')
        raise ConnectorError('IOC IP field is required but blank.')

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
                    SENTINEL_IP in rule.get('to-ip-addresses', None),
                    SENTINEL_IP in rule.get('from-ip-addresses', None)
                )
        ):
            match_list.append(index)

    logger.info(f'rule matches: {match_list}')

    # check length of match_list to see if there two or more matches. if not fail gracefully.
    if len(match_list) == 1:
        logger.exception(f'Expected two rules, but found one. Rule update aborted.')
        raise ConnectorError(f'Expected two rules, but found one. Rule update aborted.')

    # ensure rules are contiguous
    if match_list:
        if match_list[1] != match_list[0] + 1:
            logger.exception('Rules are not contiguous. Rule update aborted.')
            raise ConnectorError('Rules are not contiguous. Rule update aborted.')

    # grab the IOC list and run it through a dict to remove any duplicates.
    # using dict.fromkeys instead of set to preserve order of IP addresses.
    # using collections.deque to keep list to 900 items and FIFO old ones.
    existing_ioc_list = []
    if match_list:
        if SENTINEL_IP in rules[match_list[0]]['to-ip-addresses']:
            existing_ioc_list = rules[match_list[0]]['to-ip-addresses']
        else:
            existing_ioc_list = rules[match_list[0]]['from-ip-addresses']

        existing_ioc_list.remove(SENTINEL_IP)

    ioc_ip = list(dict.fromkeys(ioc_ip))

    new_ioc_list = list(dict.fromkeys(existing_ioc_list))
    new_ioc_list.extend(ioc_ip)

    ioc_list = deque(dict.fromkeys(new_ioc_list), maxlen=900)
    ioc_list.append(SENTINEL_IP)
    ioc_list = list(ioc_list)

    # remove old rules
    if match_list:
        del rules[match_list[0]]
        del rules[match_list[0]]

    # add two IOC Block rules to the top of the NetworkSecurityPolicy
    inbound_rule = {
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
        "to-ip-addresses": ioc_list
    }

    outbound_rule = {
        "proto-ports": [
            {
                "protocol": "any",
                "ports": ""
            }
        ],
        "action": "deny",
        "from-ip-addresses": ioc_list,
        "to-ip-addresses": [
            "0.0.0.0/0"
        ]
    }

    rules.insert(0, inbound_rule)
    rules.insert(0, outbound_rule)

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
