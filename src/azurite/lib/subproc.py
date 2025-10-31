import subprocess
import sys

from azurite.lib.logger import Logger as logger

class Subproc():

    def __init__(self):
        self.logger = logger.get_logger()
        self.logger.propagate = False

    def run_command(self, command):
        result = subprocess.run(command.split(' '), capture_output=True, check=False)
        if result.stdout is not False:
            if type(result.stdout) == bytes:
                return result.stdout.decode("utf-8") + result.stderr.decode("utf-8")
            else:
                return result.stdout + result.stderr
        else:
            return result.stderr

    def run_command_exit_code(self, command):
        result = subprocess.run(command.split(' '), capture_output=True, check=False)
        return result.returncode

    def get_resource_groups(self):
        return self.run_command("az group list --output json")        

    def create_resource_group(self, resource_group, location):
        self.logger.info(f"Creating resource group: '{resource_group}' in {location}")
        azure_cli_command = f"az group create --location {location} --name {resource_group} --output json"
        self.run_command(azure_cli_command)     

    def deploy_group_create(self, bicep, resource_group, deployment_name, parameters):
        azure_cli_command = f"az deployment group create -f bicep/{bicep} -g {resource_group} --mode Incremental --name {deployment_name} --parameters {parameters} --output json"
        self.logger.debug(f"command: {azure_cli_command}")
        return self.run_command(azure_cli_command)    

    def deploy_subscription_create(self, bicep, deployment_name, parameters, location):
        azure_cli_command = f"az deployment sub create -f bicep/{bicep} --name {deployment_name} --parameters {parameters} --location {location} --output json"
        self.logger.debug(f"command: {azure_cli_command}")
        return self.run_command(azure_cli_command)    

    def get_deployment_output(self, deployment_name, resource_group, output_name):
        azure_cli_command = f"az deployment group show --name {deployment_name} --resource-group {resource_group} --output json"
        self.logger.debug(f"Getting Deployment Output: {deployment_name}:{output_name}")
        self.logger.debug(f"Azure Command: {azure_cli_command}")
        return self.run_command(azure_cli_command)

    def list_subscriptions(self):
        return self.run_command("az account list --output json")

    def get_current_subscription(self):
        return self.run_command("az account show --output json")

    def set_subscription(self, subscription_id):
        azure_cli_command = f"az account set --subscription {subscription_id} --output json"
        self.run_command(azure_cli_command)
