from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: zerotier_node_config
version_added: "0.0.2"
short_description: Manages ZeroTier Node Config
description:
    - Manages ZeroTier Node Config
options:
    networks:
        description:
            - Dictionary of Networks that the ZeroTier Node should join as well as their configs.
        type: dict
        required: true
    api_url:
        description:
            - URL of the local ZeroTier API
        type: dict
        required: false
author:
- MyStarInYourSky (@mystarinyoursky)
'''

EXAMPLES = '''
- name: Set Networks enabled in ZeroTier
  zerotier_node_config:
    networks:
      12345:
        node_config:
          allowManaged: 1
'''

import grp
import os
import socket
import shutil
import json
import time

from ansible.module_utils._text import to_bytes
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url
from time import sleep
import urllib.error

class ZeroTierNodeConfig(object):
    """
    ZeroTier Node Config Class
    """

    def __init__(self, module):
        self.module = module
        self.network_config_bundle = module.params['networks']
        self.local_api_url = module.params['local_api_url']
        self.waitForZeroTierNodeStatus()

        # Set Defaults
        self.result = {}
        self.result['changed'] = False

    def getAPIKey(self):
        """
        Get ZeroTier Local Node API Key
        """
        try:
            with open('/var/lib/zerotier-one/authtoken.secret') as f:
                zerotier_token = f.readlines()
        except Exception as e:
            self.module.fail_json(changed=False, msg="Unable to read auth token of currently running ZeroTier Node", reason=str(e))
        return zerotier_token[0]

    def callAPI(self, api_url, method, error_mappings, data=None):
        """
        API call wrapper
        """
        api_auth = {'X-ZT1-Auth': self.getAPIKey(), 'Content-Type': 'application/json', 'Accept': 'application/json'}
        try:
            raw_resp = open_url(api_url, headers=api_auth, validate_certs=True, method=method, timeout=10, data=data, follow_redirects='all')
            resp = json.loads(raw_resp.read())
            return resp
        except urllib.error.HTTPError as err:
            if err.code in error_mappings.keys():
                self.module.fail_json(changed=False, msg=f'Unable to reach ZeroTier Node API', reason=error_mappings[err.code])
            else:
                self.module.fail_json(changed=False, msg=f'Unable to reach ZeroTier Node API', reason=json.loads(err.fp.read())['error'])  

    def waitForZeroTierNodeStatus(self):
        """
        Check if ZeroTier Node is ready to work with us
        """
        # make sure we are online
        node_online = False
        node_online_checks = 0
        while not node_online:
            sleep(5)
            node_status = self.callAPI(api_url=f'{self.local_api_url}/status', method="GET", error_mappings={401: "Access is unauthorized."})
            node_online = node_status['online']
            node_online_checks += 1
            if node_online_checks > 5:
                self.module.fail_json(changed=False, msg=f'ZeroTier Node is not reporting online', reason="")

    def getNetworks(self):
        """
        Get networks configured on the ZeroTier Node
        """
        networks = self.callAPI(api_url=f'{self.local_api_url}/network', method="GET", error_mappings={401: "Access is unauthorized."})

        return networks
    
    def getChangedNetworks(self, local_networks):
        """
        Determine which networks we need to leave, join, and change
        """

        # Get network IDs
        target_network_ids = self.network_config_bundle.keys()
        local_network_ids = [network['id'] for network in local_networks]

        # Get Network that we need to join
        networks_to_configure = list(set(target_network_ids) - set(local_network_ids))

        # Get Networks that we need to leave
        networks_to_leave = list(set(local_network_ids) - set(target_network_ids))

        # Get Networks that we need to check the config on
        networks_to_check =  list(set(local_network_ids).intersection(target_network_ids))

        # Check if there is a config change
        for network in networks_to_check:
            current_config = ([i for i in local_networks if i['id'] == network] or [None])[0]
            target_config = self.network_config_bundle[network]['node_config'] if 'node_config' in self.network_config_bundle[network].keys() else {}
            if current_config != {**current_config, **target_config}:
                networks_to_configure.append(network)

        return (networks_to_leave, networks_to_configure)
    
    def leaveNetwork(self, network):
        """
        Leave ZeroTier Network
        """
        leave_network = self.callAPI(api_url=f'{self.local_api_url}/network/{network}', method="DELETE", error_mappings={401: "Access is unauthorized.", 404: "The server cannot find the requested resource."})
        self.result['changed'] = True

    def configureNetwork(self, network):
        """
        Join/Configure ZeroTier Network
        """
        network_config = self.network_config_bundle[network]['node_config']
        configure_network = self.callAPI(api_url=f'{self.local_api_url}/network/{network}', method="POST", data=json.dumps(network_config), error_mappings={401: "Access is unauthorized.", 404: "The server cannot find the requested resource."})
        self.result['changed'] = True

def main():
    ssh_defaults = dict(
        bits=0,
        type='rsa',
        passphrase=None,
        comment='ansible-generated on %s' % socket.gethostname()
    )

    # Init Node Config
    ansible_module = AnsibleModule(
        argument_spec=dict(
            networks=dict(type='dict', required=True),
            local_api_url=dict(type='str', required=False, default="http://localhost:9993")
        ),
        supports_check_mode=True,
    )
    zerotier_node = ZeroTierNodeConfig(ansible_module)

    current_networks = zerotier_node.getNetworks()
    networks_to_leave, networks_to_configure = zerotier_node.getChangedNetworks(current_networks)

    for network in networks_to_leave:
        zerotier_node.leaveNetwork(network)

    for network in networks_to_configure:
        zerotier_node.configureNetwork(network)

    # Emit status
    if zerotier_node.result['changed']:
        ansible_module.exit_json(changed=True, msg="")
    else:
        ansible_module.exit_json(changed=False, msg="ZTNet config unchanged")


# import module snippets
if __name__ == '__main__':
    main()