from unittest.mock import patch
import json
import subprocess

from azurite.lib.subproc import Subproc


subproc = Subproc()

def completed(command, returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(command, returncode, stdout=stdout, stderr=stderr)

def test_run_command():
    sample_azure_response = open('tests/test_output/test_subproc_run_command.json', 'r').read()
    with patch("subprocess.run", return_value = completed([], 0, sample_azure_response.encode("utf-8"), b"")) as run:
        run_command_result = json.loads(subproc.run_command("az stack group show --name test --resource-group rg"))
        run.assert_called_once_with(["az", "stack", "group", "show", "--name", "test", "--resource-group", "rg"], capture_output=True, check=False)
    assert run_command_result['name'] == "azurite-sample.rg-azurite-sample-01.azurite_automation_account"
    assert run_command_result['properties']['provisioningState'] == "Succeeded"

def test_run_command_with_exit_code():
    with patch("subprocess.run", return_value = completed([], 1, "out", "ERROR: failed")):
        assert subproc.run_command_with_exit_code("az stack group create") == (1, "outERROR: failed")

def test_get_stack_resource_group():
    with patch("subprocess.run", return_value = completed([], 0, "{}", "WARNING: something")) as run:
        assert subproc.get_stack("sub.rg.config", "rg") == (0, "{}")
        assert run.call_args[0][0] == ["az", "stack", "group", "show", "--name", "sub.rg.config", "--resource-group", "rg", "--output", "json"]

def test_get_stack_subscription():
    with patch("subprocess.run", return_value = completed([], 0, "{}")) as run:
        assert subproc.get_stack("sub.policy.config") == (0, "{}")
        assert run.call_args[0][0] == ["az", "stack", "sub", "show", "--name", "sub.policy.config", "--output", "json"]

def test_deploy_group_create():
    with patch("subprocess.run", return_value = completed([], 0, "{}")) as run:
        assert subproc.deploy_group_create("storage/storage_account.bicep", "rg", "sub.rg.config", "deleteResources", "None", "/tmp/azurite-params.json") == (0, "{}")
        command = run.call_args[0][0]
        assert command[:6] == ["az", "stack", "group", "create", "-f", "bicep/storage/storage_account.bicep"]
        assert command[command.index("--parameters") + 1] == "@/tmp/azurite-params.json"

def test_deploy_subscription_create():
    with patch("subprocess.run", return_value = completed([], 0, "{}")) as run:
        assert subproc.deploy_subscription_create("policy/assignAllowedLocations.bicep", "sub.policy.config", "deleteResources", "None", "/tmp/azurite-params.json", "australiaeast") == (0, "{}")
        command = run.call_args[0][0]
        assert command[:4] == ["az", "stack", "sub", "create"]
        assert command[command.index("--parameters") + 1] == "@/tmp/azurite-params.json"
        assert command[command.index("--location") + 1] == "australiaeast"
