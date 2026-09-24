# Azurite

Azurite is an Azure Bicep orchestration tool. The main goal is to separate environment configuration from templates. This is inspired by the AWS Sceptre tool.

There is some additional getting started info in the [wiki](https://github.com/NathanKewley/Azurite/wiki)

There is also a sample project with some examples of usage [here](https://github.com/NathanKewley/azurite-sample-project)

## Goals

* Separation of Bicep configuration and templates
* Automated Resource Group Creation
* Deploy individual configurations or bulk configurations at different scopes: Resource Group, Subscription or Account
* Deploy output and input chaining
* Automated deployment hierarchy based on output bindings

## Not Goals

* Support for anything other than Bicep on Azure
* Support for multiple Azure tenancies

## Requirements

* Python 3.9+
* Azure CLI
* Azure Bicep CLI

## Building From Source

* Clone this repo
* Install requirements `pip3 install -r requirements.txt`
* Build the project `python3 -m build`
* Install `pip3 install .` (or `make build`, which also builds the wheel into `dist/`)

## Assumptions

* You are working within a single Azure Tenancy
* Each subscription has a unique name

## Possible Future Features

* Deploy Azure Policy at MG Level

## Azurite project structure

An Azurite project is structured in the following way:

```
- root/
    - bicep/
        - storage_account_and_container.bicep
    - configuration/
        - Subscription_1/
            - Resource_Group_1/
                - location.yaml
                - storage_account_and_container.yaml
                - config_2.yaml
            - Resource_Group_2/
                - location.yaml
                - config_1.yaml
        - Subscription_2/
            - Resource_Group_1/
                - location.yaml
                - config_1.yaml
    - scripts/
        - script1.py
        - script2.sh                
```

Given the example structure above a few important things to note:

* `bicep` - this folder contains all of your bicep templates.
* `configuration` - this contains your configuration for deployments, the hierarchy is important.
* `Subscription_1` - This is the root level under configuration. `Subscription_1` matched exactly the name of a subscription in Azure.
* `Resource_Group_1` - At the root level of a given subscription. This sets the resource group for a deployment within that subscription.
* `location.yaml` - A special configuration file to set the location of the resource group.
* `storage_account_and_container.yaml` - This is a deployable configuration. It will link to a template in the `bicep` folder and contain the required parameters.
* `scripts` - Scripts folder for pre and post hooks. Python3 and bash scripts are supported.

Sample `bicep`, `configuration` and `scripts` folders are included in the root of this repo.

### Bicep files

This is just a standard bicep template, for example when creating a storage account and container you might have a file such as `storage_account_and_container.bicep` that looks something like:

```
param location string
param storageName string
param containerName string
param skuName string

resource StorageAccount 'Microsoft.Storage/storageAccounts@2019-06-01' = {
  name: storageName
  location: location
  kind: 'Storage'
  sku: {
    name: skuName
  }
}

resource StorageContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2019-06-01' = {
  name: '${StorageAccount.name}/default/${containerName}'
  properties: {
    publicAccess: 'None'
  }
}

output storageLocation string = StorageAccount.properties.primaryLocation
```

### Configuration files

Given the configuration file 

`configuration/Subscription_1/Resource_Group_1/storage_account_and_container.yaml`:
This is broken down into sections as such: 

`<discarded>/<Subscription>/<resource_group>/<config_to_deploy>`

in this case `storage_account_and_container.yaml` might look like the following:

```
---
bicep_path: storage_account_and_container.bicep
scope: resource_group
action_on_unmanage: deleteResources
deny_settings_mode: None

pre_hooks:
  Python3Script: script1.py

params:
  storageName: storagesampleazurite1
  containerName: blog
  skuName: Standard_LRS
  location: Ref:Subscription_1/Resource_Group_1/config_2:storageLocation

post_hooks:
  BashScript: script2.sh
  
```

The `bicep_path` here points to the template in the `bicep/` folder of the project. This bicep template is then deployed using the provided `params` block to the subscription and resource group determined by the configuration files path.

`params` values are passed to Bicep with their YAML types, so use native YAML for `array`, `object`, `bool` and `int` parameters rather than quoted strings:

```
params:
  addressPrefixes:
    - 10.0.0.0/20
    - 10.1.0.0/20
  tags:
    environment: prod
  enableHttpsOnly: true
  instanceCount: 2
```

`scope` is an optional parameter, defaulting to `resource_group` when not specified. The other valid value is `subscription`. This sets the deployment at a subscription scope rather than a resource group scope. This is particularly useful for setting up `Azure Policy`. Please see the [Working with Azure Policy](https://github.com/NathanKewley/Azurite/wiki/Working-with-Azure-Policy) wiki page for more details on this.

`action_on_unmanage` and `deny_settings_mode` set these settings for the [stack group](https://learn.microsoft.com/en-us/cli/azure/stack/group?view=azure-cli-latest#az-stack-group-show) that is created by this configuration. Both are optional and default to `deleteResources` and `None` respectively.

`pre_hooks` and `post_hooks` allow you to specify external scripts that should be run before or after the bicep deployment respectively. Scripts are looked up in the `scripts/` folder, and their output is shown as they run. If a hook returns a non-success exit code the deployment is stopped. The supported hook types are `Python3Script` and `BashScript`. `pre_hooks` and `post_hooks` are both optional.

#### Referencing Other Deployment Outputs

Any parameter in the config file prefixed with `Ref:` is a reference to an output from a different deployment. The format is the path of the other configuration file (relative to `configuration/`, without `.yaml`) followed by the output name:

```
params:
  location: Ref:Subscription_1/Resource_Group_1/config_2:storageLocation
```

The original dotted form, `Ref:Subscription_1.Resource_Group_1.config_2:storageLocation`, also still works. If a subscription, resource group or config name itself contains a dot and the dotted form could match more than one configuration file, Azurite will ask you to use the `/` form instead.

When a configuration references the output of another deployment, Azurite deploys that other configuration first (including its hooks) and then looks up the output value. Deployment hierarchy can be of an arbitrary depth and span across the whole project. Circular references are detected and stop the deploy before anything runs.

By default a dependency is redeployed every time something that references it is deployed, so its hooks run and its outputs are current. To skip that, set `redeploy_as_dependency: false` in the referenced configuration:

```
---
bicep_path: storage/storage_account.bicep
redeploy_as_dependency: false
```

When a configuration is only being deployed because another configuration references it, and its stack is already deployed successfully, Azurite will then use the existing outputs rather than redeploying it. It is still deployed if its stack does not exist or last failed, and it is always deployed when it is part of what you asked to deploy (e.g. it is in the resource group passed to `deploy-resource-group`).

If the resource group for a deployment does not exist Azurite will create it for you using the location specified by the `location.yaml` file.

### location.yaml

This is a super simple file that is required for every resource group. It tells Azurite what location to create the resource group in if it does not exist. Each resource deployed into that resource group inherits the location. An example of a location.yaml:

```
---
location: australiaeast

```

## Usage - Deploying

Azurite is designed to be easy to use and allow scoped control of deployments.

### Deploying a single configuration

From the root folder of your repository run the following command:

`azurite deploy Subscription_1/Resource_Group_1/storage_account_and_container.yaml`

This will deploy a single configuration / template

### Deploying at resource group scope

From the root folder of your repository run the following command:

`azurite deploy-resource-group Subscription_1/Resource_Group_1`

This will deploy every configuration file under that resource group

### Deploying at subscription scope

From the root folder of your repository run the following command:

`azurite deploy-subscription Subscription_1`

This will deploy each configuration file for each resource group in the specified subscription

### Deploying at account scope

From the root folder of your repository run the following command:

`azurite deploy-account`

This will deploy every configuration file in the project to the appropriate subscriptions and resource groups

## Usage - Destroying

Destroy will NOT destroy resource groups. This is because there could be resources in a resource group not managed by an Azurite stack and we don't want to delete those along with a resource group being deleted.

* Destroy will NOT run pre and post hooks.
* Destroy runs in reverse dependency order: a configuration is destroyed before any configuration it references with `Ref:`, across resource groups and subscriptions within the destroy.
* If a configuration outside the destroy still references one being destroyed, Azurite logs a warning but does not destroy it.
* The scope of these commands is the same as the deploy commands

### Destroy a single configuration

`azurite destroy Subscription_1/Resource_Group_1/storage_account_and_container.yaml`

### Destroying at resource group scope

`azurite destroy-resource-group Subscription_1/Resource_Group_1`

### Destroying at subscription scope

`azurite destroy-subscription Subscription_1`

### Destroying at account scope

`azurite destroy-account`

## Environment Variables

Please see the [Environment Variables](https://github.com/NathanKewley/Azurite/wiki/Environment-Variables) wiki page for details.
