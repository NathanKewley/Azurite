param name string
param location string
param addressPrefixs array
param firewallSubnetName string
param firewallSubnetAddressPrefix string
param vpnSubnetName string
param vpnSubnetAddressPrefix string

module virtualNetworkHub './virtualNetworkHub.bicep' = {
  name: 'virtualNetworkHub'
  params: {
     name: name
     location: location
     addressPrefixs: addressPrefixs
     firewallSubnetName: firewallSubnetName
     firewallSubnetAddressPrefix: firewallSubnetAddressPrefix
     vpnSubnetName: vpnSubnetName
     vpnSubnetAddressPrefix: vpnSubnetAddressPrefix
  }
}

module NSGDenyAllInbound './networkSecurityGroup.bicep' = {
  name: 'NSGDenyAllInbound'
  params: {
    networkSecurityGroupName: 'NSGDenyAllInbound'
    location: location
  }
}

module NSGSameTemplate './networkSecurityGroup.bicep' = {
  name: 'NSGSameTemplate'
  params: {
    networkSecurityGroupName: 'NSGSameTemplate'
    location: location
  }
}

output virtualNetworkId string = virtualNetworkHub.outputs.virtualNetworkId
output firewallSubnetName string = virtualNetworkHub.outputs.firewallSubnetName
output networkName string = virtualNetworkHub.outputs.networkName
output NSGOutput1 string = NSGDenyAllInbound.outputs.networkSecurityGroupId
output NSGOutput2 string = NSGSameTemplate.outputs.networkSecurityGroupId
