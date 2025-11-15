import yaml
import json
import os

from azurite.lib.subproc import Subproc
from azurite.lib.logger import Logger as logger
from azurite.lib.deployer import Deployer
from azurite.lib.subscription import Subscription
from azurite.lib.hook_orchestrator import HookOrchestrator

class Orchestrator():

    def __init__(self):
        self.logger = logger.get_logger()
        self.logger.propagate = False
        self.subproc = Subproc()
        self.subscription = Subscription(self.subproc)
        self.deployer = Deployer(self.subproc, self.subscription)
        self.hook_orchestrator = HookOrchestrator()
        self.deploys = []

    def get_deployment_name(self, configuration):
        return configuration.replace("/",".")[:-5]

    def get_resource_group(self, configuration):
        return configuration.split('/')[1]

    def get_subscription(self, configuration):
        return configuration.split('/')[0]

    def get_child_items(self, path):
        return(os.listdir(path))

    def load_config(self, config):
        with open(f"configuration/{config}") as file:
            return yaml.load(file, Loader=yaml.FullLoader)

    def load_location(self, config):
        location_path = "configuration/" + config.split("/")[0] + "/" + config.split("/")[1] + "/location.yaml"
        with open(location_path) as file:
            location = yaml.load(file, Loader=yaml.FullLoader)        
            return(location['location'])

    def get_deployment(self, deployment_name, resource_group):
        # This needs to move to subproc
        azure_cli_command = f"az stack group show --name {deployment_name} --resource-group {resource_group}"
        result = ""
        try:
            result = self.subproc.run_command(azure_cli_command)
        except:
            self.logger.error(f"Error running: {azure_cli_command}")
        if "\"provisioningState\": \"succeeded\"" in result:
            return True
        return False

    def check_deployment_dependancy(self, value, subscription):
        deployment_name = value.split(":")[1]
        output_name = value.split(":")[2]
        resource_group = value.split(":")[1][1:].split(".")[1]
        parameter_subscription = value.split(":")[1].split(".")[0]

        self.subscription.set_subscription(parameter_subscription)
        # if not self.get_deployment(deployment_name, resource_group):
        #     deployment_config_path = deployment_name.replace(".","/") + ".yaml"
        #     self.logger.info("Deployment has dependencies. Resolving...")
        #     self.deploy(deployment_config_path)

        # We are going to deploy regardless here as it will update existing deployments.
        # If no changes then this still takes about 30 sec per stack so in undesirable.
        # maybe we can convert the bicep to be deployed to ARM and call the existing deployment
        # do a diff and only re-deploy if there are changes?
        deployment_config_path = deployment_name.replace(".","/") + ".yaml"
        self.logger.info("Deployment has dependencies. Resolving...")
        self.deploy(deployment_config_path)        
        self.subscription.set_subscription(subscription)

    def deploy(self, configuration, deploy_mode="deploy", dry_run=False):
        if configuration not in self.deploys:
            self.deploys.append(configuration)
            config = self.load_config(configuration)
            location = self.load_location(configuration)
            deployment_name = self.get_deployment_name(configuration)
            subscription = self.get_subscription(configuration)
            resource_group = self.get_resource_group(configuration)

            # Configuration Settings with defaults
            if "action_on_unmanage" in config.keys():
                action_on_unmanage = config["action_on_unmanage"]
            else:
                action_on_unmanage = "deleteResources"
            if "deny_settings_mode" in config.keys():
                deny_settings_mode = config["deny_settings_mode"]
            else:
                deny_settings_mode = "None"

            # deploy dependant deployments before this one
            # destroy does not need to be ordered by params
            if deploy_mode == "deploy":
                for param, value in config['params'].items():
                    if "Ref:" in value:
                        if not dry_run:
                            self.check_deployment_dependancy(value, subscription)

            self.logger.info(f"{deploy_mode}ing: {configuration} to {subscription}")
            if not dry_run:
                # Run pre-delpoy hooks
                if ('pre_hooks' in config.keys()) and deploy_mode == "deploy":
                    self.hook_orchestrator.run_hooks(config['pre_hooks'])

                # Run main deployment
                if deploy_mode == "deploy":
                    if 'scope' in config:
                        if config['scope'] == 'subscription':
                                self.deployer.deploy_bicep_subscription(config['params'], config['bicep_path'], location, deployment_name, action_on_unmanage, deny_settings_mode, subscription)   
                        if config['scope'] == 'resource_group':     
                            self.deployer.deploy_bicep(config['params'], config['bicep_path'], resource_group, location, deployment_name, action_on_unmanage, deny_settings_mode, subscription)
                    else:
                        self.deployer.deploy_bicep(config['params'], config['bicep_path'], resource_group, location, deployment_name, action_on_unmanage, deny_settings_mode, subscription)
                elif deploy_mode == "destroy":
                    if self.get_deployment(deployment_name, resource_group):
                        if 'scope' in config:
                            if config['scope'] == 'subscription':
                                self.deployer.destroy_bicep_subscription(deployment_name, subscription, action_on_unmanage)   
                            if config['scope'] == 'resource_group':     
                                self.deployer.destroy_bicep(resource_group, deployment_name, subscription, action_on_unmanage)
                        else:
                            self.deployer.destroy_bicep(resource_group, deployment_name, subscription, action_on_unmanage)

                # Run post-delpoy hooks
                if ('post_hooks' in config.keys()) and deploy_mode == "deploy":
                    self.hook_orchestrator.run_hooks(config['post_hooks'])
            else:
                return [config['params'], config['bicep_path'], resource_group, location, deployment_name, subscription]
        else:
            return
        
    def deploy_resource_group(self, configuration, deploy_mode="deploy", dry_run=False):
        test_results = []

        subscription = self.get_subscription(configuration)
        resource_group = self.get_resource_group(configuration)
        deployments = self.get_child_items(f"configuration/{configuration}/")
        for deployment in deployments:
            if deployment != "location.yaml":
                if not dry_run:
                    self.deploy(f"{subscription}/{resource_group}/{deployment}", deploy_mode=deploy_mode)
                else:
                    test_results.append(f"{subscription}/{resource_group}/{deployment}")
        if dry_run:
            return test_results

    def deploy_subscription(self, configuration, deploy_mode="deploy", dry_run=False):
        test_results = []
        resource_groups = self.get_child_items(f"configuration/{configuration}/")
        for resource_group in resource_groups:
            if not dry_run:
                self.deploy_resource_group(f"{configuration}/{resource_group}", deploy_mode=deploy_mode)
            else:
                test_results.append(f"{configuration}/{resource_group}")
        if dry_run:
            return test_results                

    def deploy_account(self, deploy_mode="deploy", dry_run=False):
        test_results = []
        subscriptions = self.get_child_items("configuration/")
        for subscription in subscriptions:
            if not dry_run:
                self.deploy_subscription(subscription, deploy_mode=deploy_mode)
            else:
                test_results.append(subscription)
        if dry_run:
            return test_results                        

    def destroy(self, configuration, deploy_mode="destroy", dry_run=False):
        self.deploy(configuration, deploy_mode=deploy_mode)

    def destroy_resource_group(self, configuration, deploy_mode="destroy", dry_run=False):
        self.deploy_resource_group(configuration, deploy_mode=deploy_mode)

    def destroy_subscription(self, configuration, deploy_mode="destroy", dry_run=False):
        self.deploy_subscription(configuration, deploy_mode=deploy_mode)

    def destroy_account(self, deploy_mode="destroy", dry_run=False):
        self.deploy_account(deploy_mode=deploy_mode)
        