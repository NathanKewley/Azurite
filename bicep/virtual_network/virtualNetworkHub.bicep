param name string
param location string
param addressPrefixs array
param firewallSubnetName string
param firewallSubnetAddressPrefix string
param vpnSubnetName string
param vpnSubnetAddressPrefix string

resource virtual_network 'Microsoft.Network/virtualNetworks@2020-08-01' = {
  name: name
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: addressPrefixs 
    }
    subnets: [
      {
        name: firewallSubnetName
        properties: {
          addressPrefix: firewallSubnetAddressPrefix
        }
      }
      {
        name: vpnSubnetName
        properties: {
          addressPrefix: vpnSubnetAddressPrefix
        }
      }
    ]
  }
}

output virtualNetworkId string = virtual_network.id
output firewallSubnetName string = firewallSubnetName
output networkName string = name
