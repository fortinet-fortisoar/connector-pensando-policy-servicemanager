from connectors.core.connector import get_logger, ConnectorError
from .constants import LOGGER_NAME
from .get_network_security_policies import get_network_security_policies
from .unisolate_host import unisolate_host
from .utils import invoke_rest_endpoint


logger = get_logger(LOGGER_NAME)


def isolate_host(config, params):
    """Will create two NetworkSecurityPolicy rules under an existing Policy.
       Creates two rules - one to block all inbound traffic to the host and one
       to block all outbound traffic from the host.

       Isolate rules will always look like:

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
               "<host_source_ip>"
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
               "<host_source_ip>"
             ]
           }
         ]
       }
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

    # remove rules if they already exist. keeps from duplicating rules.
    logger.info(f'removing isolation rules for {host_source_ip} if they already exist.')
    try:
        unisolate_result = unisolate_host(config, params)
        logger.info(f'matching isolation rules for {host_source_ip} found and removed.')
        rules = unisolate_result['spec']['rules']
    except Exception:
        # it's ok if this fails - just means the rules did not already exist
        logger.info('no isolation rules removed.')

    # add two isolation rules to the top of the NetworkSecurityPolicy
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
        "to-ip-addresses": [
            host_source_ip
        ]
    }

    outbound_rule = {
        "proto-ports": [
            {
                "protocol": "any",
                "ports": ""
            }
        ],
        "action": "deny",
        "from-ip-addresses": [
            host_source_ip
        ],
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
