import shlex
import subprocess
import sys

from nitra.lib.logger import Logger as logger

class Subproc():

    def __init__(self):
        self.logger = logger.get_logger()
        self.logger.propagate = False

    def _run(self, command, capture=True):
        # Commands are argument lists, each item reaches the process as one argument so values can contain spaces
        self.logger.debug(f"command: {shlex.join(command)}")
        try:
            return subprocess.run(command, capture_output=capture, text=True, check=False)
        except FileNotFoundError:
            if command[0] == "az":
                self.logger.error("Azure CLI (az) not found on PATH, is it installed? https://learn.microsoft.com/cli/azure/install-azure-cli")
            else:
                self.logger.error(f"'{command[0]}' not found on PATH")
            sys.exit(1)

    def run_command(self, command):
        # stdout only, az writes warnings to stderr which would break json parsing
        return self._run(command).stdout

    def run_command_streamed(self, command):
        # Output is not captured, it goes straight to the terminal / CI log as the command runs
        return self._run(command, capture=False).returncode

    def run_command_with_exit_code(self, command):
        result = self._run(command)
        return result.returncode, result.stdout + result.stderr

    def run_command_output_or_error(self, command):
        # stdout on success so it can be parsed, or az's error message on failure (e.g. not logged in)
        result = self._run(command)
        if result.returncode != 0:
            return result.returncode, result.stderr
        return result.returncode, result.stdout

    def resource_group_exists(self, resource_group):
        # stdout is "true" or "false"
        return self.run_command_output_or_error(["az", "group", "exists", "--name", resource_group])

    def create_resource_group(self, resource_group, location):
        self.logger.info(f"Creating resource group: '{resource_group}' in {location}")
        return self.run_command_with_exit_code(["az", "group", "create", "--location", location, "--name", resource_group, "--output", "json"])

    def deploy_group_create(self, bicep, resource_group, deployment_name, action_on_unmanage, deny_settings_mode, parameters_file):
        return self.run_command_with_exit_code([
            "az", "stack", "group", "create",
            "-f", f"bicep/{bicep}",
            "-g", resource_group,
            "--name", deployment_name,
            "--action-on-unmanage", action_on_unmanage,
            "--deny-settings-mode", deny_settings_mode,
            "--parameters", f"@{parameters_file}",
            "--yes", "--output", "json"
        ])

    def deploy_group_destroy(self, resource_group, deployment_name, action_on_unmanage):
        return self.run_command_with_exit_code([
            "az", "stack", "group", "delete",
            "-g", resource_group,
            "--name", deployment_name,
            "--action-on-unmanage", action_on_unmanage,
            "--yes", "--verbose", "--output", "json"
        ])

    def deploy_subscription_create(self, bicep, deployment_name, action_on_unmanage, deny_settings_mode, parameters_file, location):
        return self.run_command_with_exit_code([
            "az", "stack", "sub", "create",
            "-f", f"bicep/{bicep}",
            "--name", deployment_name,
            "--action-on-unmanage", action_on_unmanage,
            "--deny-settings-mode", deny_settings_mode,
            "--parameters", f"@{parameters_file}",
            "--location", location,
            "--yes", "--output", "json"
        ])

    def deploy_subscription_destroy(self, deployment_name, action_on_unmanage):
        return self.run_command_with_exit_code([
            "az", "stack", "sub", "delete",
            "--name", deployment_name,
            "--action-on-unmanage", action_on_unmanage,
            "--yes", "--output", "json"
        ])

    def get_stack(self, deployment_name, resource_group=None):
        # Subscription scoped stacks have no resource group
        if resource_group is None:
            command = ["az", "stack", "sub", "show", "--name", deployment_name, "--output", "json"]
        else:
            command = ["az", "stack", "group", "show", "--name", deployment_name, "--resource-group", resource_group, "--output", "json"]
        # stdout only, az writes warnings to stderr which would break json parsing
        result = self._run(command)
        return result.returncode, result.stdout

    def list_subscriptions(self):
        return self.run_command(["az", "account", "list", "--output", "json"])

    def check_azure_login(self):
        # Requesting a token authenticates against Azure, unlike 'az account show' which only reads the local cache.
        # Only the expiry is returned so the token itself never reaches the logs
        return self.run_command_output_or_error(["az", "account", "get-access-token", "--query", "expiresOn", "--output", "tsv"])

    def get_current_subscription(self):
        return self.run_command_output_or_error(["az", "account", "show", "--output", "json"])

    def set_subscription(self, subscription_id):
        self.run_command(["az", "account", "set", "--subscription", subscription_id, "--output", "json"])
