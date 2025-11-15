# Azurite

Azurite is an Azure Bicep orchestration tool. The main goal is to separate environment configuration from templates. This is inspired by the AWS Sceptre tool.

There is some additional getting started info in the [wiki](https://github.com/NathanKewley/Azurite/wiki)

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

* Python 3.8+
* Azure CLI
* Azure Bicep CLI

## Building From Source

* Clone this repo
* Install requirements `pip3 install -r requirements.txt`
* Build the project `python3 -m build`
* Install `pip3 install dist/Azurite-0.0.4-py3-none-any.whl`

## Assumptions

* You are working within a single Azure Tenancy
* Each subscription has a unique name

## Possible Future Features

* Deploy Azure Policy at MG Level

## Azurite project structure

A Azurite project is structured in the following way:

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

This is just a standard bicep template, for example when creating a storage account and container you might have a file such as `storage_account_and_container.yaml` that looks something like:

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
bicep_path: storage_account.bicep
scope: resource_group
action_on_unmanage: deleteResources
deny_settings_mode: None

pre_hooks:
  PythonScript: scripts/test_python_hook.py

params:
  storageName: storagesampleazurite1
  containerName: blog
  skuName: Standard_LRS
  location: Ref:Subscription_1.Resource_Group_1.config2:storageLocation

post_hooks:
  BashScript: scripts/test_bash_hook.sh
  
```

The `bicep_path` here points to the template in the `bicep/` folder of the project. This bicep template is then deployed using the provided `params` block to the subscription and resource group determined by the configuration files path.

`scope` is an optional parameter, where the default value is not specified is `resource_group`. The other valid value is `subscription`. This sets the deployment at a subscription scope rather than a resource group scope. This is particularly useful for setting up `Azure Policy`. Please see the [Working with Azure Policy](https://github.com/NathanKewley/Azurite/wiki/Working-with-Azure-Policy) wiki page for more details on this.

`action_on_unmanage` and `deny_settings_mode` set these settings for the [stack group](https://learn.microsoft.com/en-us/cli/azure/stack/group?view=azure-cli-latest#az-stack-group-show) that is created by this configuration. Both are optional and default to `deleteResources` and `None` respectively.

`pre_hooks` and `post_hooks` allow you to specify external scripts that should be run before or after the bicep deployment respectively. If A hook returns a non-success code deployment will be terminated. At current there is only support for `Python3` scripts and `Bash` scripts. `pre_commit` and `post_commit` Hooks are both optional optional.

#### Referencing Other Deployment Outputs

Any parameter in the config file prefixes with `Ref:` is a reference to an output from a different deployment. The format for referencing an output from a different deployment is:
`<Ref>:<deployment_path>:<output_name>` where the `deployment_path` replaces `/` with `.`.

When referencing the output from a different deployment Azurite will first check if the dependent deployment exists then deploy it if required. If the dependent deployment does exist Azurite will look up the output value and use it for the deployment. deployment hierarchy can be of an arbitrary depth and span across the whole project.

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

`Azurite deploy Subscription_1/Resource_Group_1/storage_account_and_container.yaml`

This will deploy a single configuration / template

### Deploying at resource group scope

From the root folder of your repository run the following command:

`Azurite deploy-resource-group Subscription_1/Resource_Group_1`

This will deploy every configuration file under that resource group

### Deploying at subscription scope

From the root folder of your repository run the following command:

`Azurite deploy-subscription Subscription_1`

This will deploy each configuration file for each resource group in the specified subscription

### Deploying at account scope

From the root folder of your repository run the following command:

`Azurite deploy-account`

This will deploy every configuration file in the project to the appropriate subscriptions and resource groups

## Usage - Destroying

Destroy will NOT destroy resource groups. This is because there could be resources in a resource group not managed by an Azurite stack and we don't want to delete those along with a resource group being deleted.

* Destroy will NOT run pre and post hooks.
* Destroy will NOT build a hierarchy of inputs and outputs. It will just destroy sequentially.
* The scope of these commands is the same as the deploy commands

### Destroy a single configuration

`Azurite destroy Subscription_1/Resource_Group_1/storage_account_and_container.yaml`

### Destroying at resource group scope

`Azurite destroy-resource-group Subscription_1/Resource_Group_1`

### Destroying at subscription scope

`Azurite destroy-subscription Subscription_1`

### Destroying at account scope

`Azurite destroy-account`

## Environment Variables

Please see the [Environment Variables](https://github.com/NathanKewley/Azurite/wiki/Environment-Variables) wiki page for details.
