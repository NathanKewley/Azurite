from unittest.mock import Mock
import json

from azurite.lib.subproc import Subproc


subproc = Subproc()
mocker = Mock()

def test_run_command():
    sample_azure_response = json.loads(open('tests/test_output/test_subproc_run_command.json', 'r').read())
    mocker.subproc.run_command.return_value = sample_azure_response

    run_command_result = mocker.subproc.run_command("az deployment group create -f bicep/automation/automation_account.bicep -g rg-azurite-sample-01 --mode Incremental --name azurite-sample.rg-azurite-sample-01.azurite_automation_account --parameters location=australiaeast appName=azuriteAutomation skuName=Free --output json")
    assert run_command_result['name'] == "azurite-sample.rg-azurite-sample-01.azurite_automation_account"
    assert run_command_result['properties']['provisioningState'] == "Succeeded"

def test_get_current_subscription():
    sample_azure_response = json.loads(open('tests/test_output/test_subproc_get_current_subscription.json', 'r').read())
    mocker.subproc.get_current_subscription.return_value = sample_azure_response

    current_subscription = mocker.subproc.get_current_subscription()
    assert current_subscription == sample_azure_response
    assert current_subscription['name'] == "azurite-sample"
