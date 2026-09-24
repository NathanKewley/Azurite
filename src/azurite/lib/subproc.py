import shlex
import subprocess

from azurite.lib.logger import Logger as logger

class Subproc():

    def __init__(self):
        self.logger = logger.get_logger()
        self.logger.propagate = False

    def _run(self, command):
        # Commands are argument lists, each item reaches the process as one argument so values can contain spaces
        self.logger.debug(f"command: {shlex.join(command)}")
        return subprocess.run(command, capture_output=True, text=True, check=False)

    def run_command(self, command):
        # stdout only, az writes warnings to stderr which would break json parsing
        return self._run(command).stdout

    def run_command_exit_code(self, command):
        return self._run(command).returncode

    def run_command_with_exit_code(self, command):
        result = self._run(command)
        return result.returncode, result.stdout + result.stderr

    def get_resource_groups(self):
        return self.run_command(["az", "group", "list", "--output", "json"])

    def create_resource_group(self, resource_group, location):
        self.logger.info(f"Creating resource group: '{resource_group}' in {location}")
        self.run_command(["az", "group", "create", "--location", location, "--name", resource_group, "--output", "json"])

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

    def get_current_subscription(self):
        return self.run_command(["az", "account", "show", "--output", "json"])

    def set_subscription(self, subscription_id):
        self.run_command(["az", "account", "set", "--subscription", subscription_id, "--output", "json"])
