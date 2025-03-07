# Ansible role for using ZeroTier Clients with ZTNET

This ansible role provides configuration of the local node (ZeroTier Client/Node) and [ZTNET](https://ztnet.network) at the same time.

Still a WIP

## Implemented
- Joining ZeroTier Clients to networks
- Configuration of local ZeroTier Client settings
- Configuration of ZeroTier Client settings in ZTNET Personal Networks
- Configuration of ZeroTier Client settings in ZTNET Organization Networks
- Custom ZeroTier Planets

## Tested Operating Systems

- Ubuntu 18.04
- Ubuntu 20.04
- Ubuntu 22.04
- Ubuntu 24.04
- Debian 11 Bullseye
- Debian 12 Bookworm

## Parameters

### `zerotier_version`

The ZeroTier version that will be installed

### `zerotier_networks`

Configuration of ZeroTier networks that the node will join. It uses the following base structure.

```yaml
{{zerotier network id}}:
  node_config: {}
  ztnet_config: {}
```

#### `node_config`

This section allows you to perform local network specific configuration. See [here](https://docs.zerotier.com/config/#network-specific-configuration) for available options.

Example Config:
```yaml
{{zerotier network id}}:
  node_config:
    allowManaged: 1
  ztnet_config: {}
```

#### `ztnet_config`

This section allows you to configure node settings on ZTNET. See [here](https://ztnet.network/Rest%20Api/Personal/Network-Members/modify-a-network-member) for all possible options. By default, the inventory hostname of the host is set as the name of the host, and the node is authorized. Some (like tags) may not be functional yet and will return an error such as `{"fieldErrors": {"": ["Unrecognized key(s) in object: 'tags'"]}, "message": "Validation error"}}`

Example Config:
```yaml
{{zerotier network id}}:
  node_config: {}
  ztnet_config:
    authorized: true
```

### `zerotier_localconfig`

Any [local configuration (locals.conf)](https://docs.zerotier.com/config/#local-configuration-options) that needs to be set on the node.

For example:
```yaml
zerotier_localconfig:
  settings:
    primaryPort: 9993
```

### `zerotier_local_api_address`

If you change the ZeroTier port via `zerotier_localconfig` or a similar option, you will need to update this to the correct `host:port` pair (ex: `localhost:9994`)

### `zerotier_planet`

If you need a custom planet, follow the instructions [here](https://ztnet.network/usage/private_root). After the setup, download the config and unpack it. Encode the file `planet.custom` with base64 and that will become the value of `zerotier_planet`

For example: `cat planet.custom | base64`

### `zerotier_ztnet_api_key`

The ZTNET Api Key

### `zerotier_ztnet_api_base_url`

The ZTNET installation URL, not including `/api/v1`

