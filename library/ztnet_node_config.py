from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ztnet_node_config
version_added: "0.0.2"
short_description: Manages ZTNET Node Config
description:
    - Manages ZTNET Node Config
options:
    node:
        description:
            - Node ID of the current Node
        type: str
        required: true    
    network:
        description:
            - Name of the network where the Node will be configured
        type: str
        required: true
    api_key:
        description:
            - ZTNet API Key
        type: str
        required: true
    config:
        description:
            - Config that should be updated
        type: dict
        required: true
    api_url:
        description:
            - URL of the API
        type: dict
        required: true
author:
- MyStarInYourSky (@mystarinyoursky)
'''

EXAMPLES = '''
- name: Add host to ZeroTier Network
  ztnet_node_config:
    node: zz1234
    network: 1234
    api_key: 1234
    api_url: https://somesdn.mysite.com
    config:
      authorized: true
'''

RETURN = r'''
node:
  description: ZTNet Node
  returned: always
  type: str
  sample: zz12345
network:
  description: Network where node will be configured
  returned: always
  type: str
  sample: mynetwork
config:
  description: New config of node
  returned: always
  type: dict
  sample: {'authorised': true}
'''

import grp
import os
import socket
import shutil
import json
import time
import os.path
import psutil

from ansible.module_utils._text import to_bytes
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url

class ZTNetNodeConfig(object):
    """
    ZTNet Node Config Class
    """

    def __init__(self, module):
        self.module = module
        self.node = module.params['node']
        self.nwid = module.params['network']
        self.api_url = module.params['api_url']
        self.api_key = module.params['api_key']
        self.target_config = module.params['config']

        # Set Defaults
        self.result = {}
        self.result['changed'] = False

    def checkNetwork(self):
        """
        Check if we have access to the target network
        """
        api_url = self.api_url + '/network'
        api_auth = {'x-ztnet-auth': self.api_key, 'Accept': 'application/json'}
        try:
            raw_resp = open_url(api_url, headers=api_auth, validate_certs=True, method='GET', timeout=10)
            if raw_resp.getcode() in [401, 429, 500]:
                resp = json.loads(raw_resp.read())
                self.module.fail_json(changed=False, msg=resp.error)
            elif raw_resp.getcode() == 200 and any(network['nwid'] == self.nwid for network in json.loads(raw_resp.read())):
                return True
            elif raw_resp.getcode() == 200 and not any(network['nwid'] == self.nwid for network in json.loads(raw_resp.read())):
                self.module.fail_json(changed=False, msg=f'Cannot find network {self.nwid}')
            else:
                resp = json.loads(raw_resp.read())
                self.module.fail_json(changed=False, msg=f'Unknown error: {resp}')
        except Exception as e:
            self.module.fail_json(changed=False, msg="Unable to reach ZTNET API", reason=str(e))

    def configureNode(self):
        """
        Configures ZTNET Node
        """
        api_url = f'{self.api_url}/network/{self.nwid}/member/{self.node}'
        api_auth = {'x-ztnet-auth': self.api_key, 'Content-Type': 'application/json', 'Accept': 'application/json'}
        config_json = json.dumps(self.target_config)
        try:
            raw_resp = open_url(api_url, headers=api_auth, validate_certs=True, method='POST', timeout=10, data=config_json, follow_redirects="all")
            if raw_resp.getcode() in [401, 429, 500]:
                resp = json.loads(raw_resp.read())
                self.module.fail_json(changed=False, msg=resp.error)
            elif raw_resp.getcode() == 200:
                self.result['changed'] = True
                resp = json.loads(raw_resp.read())
                return resp
            else:
                resp = json.loads(raw_resp.read())
                self.module.fail_json(changed=False, msg=f'Unknown error: {resp}')
        except Exception as e:
            self.module.fail_json(changed=False, msg="Unable to reach ZTNET API", reason=str(e))

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
            node=dict(type='str', required=True),
            network=dict(type='str', required=True),
            api_key=dict(type='str', required=True),
            config=dict(type='str', required=True),
            api_url=dict(type='str', required=True),
        ),
        supports_check_mode=True,
    )
    zerotier_node = ZTNetNodeConfig(ansible_module)

    # Check to see if network exists
    zerotier_node.checkNetwork()

    # Apply Changes
    result=zerotier_node.configureNode()

    # Emit status
    if zerotier_node.result['changed']:
        ansible_module.exit_json(changed=True, msg=result)
    else:
        ansible_module.exit_json(changed=False, msg="ZTNet config unchanged")


# import module snippets
if __name__ == '__main__':
    main()