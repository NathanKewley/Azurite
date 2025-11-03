import json

from azurite.lib.orchestrator import Orchestrator


orchestrator = Orchestrator()

def test_deploy_load_config2():
    config_path = "azurite-sample/rg-azurite-sample-01/azurite_automation_account.yaml"
    config_expected_loaded_output = json.loads(open('tests/test_output/test_deploy_load_config.json', 'r').read())

    config_loaded = orchestrator.load_config(config_path)
    assert type(config_loaded) == dict
    assert config_loaded["bicep_path"] == "automation/automation_account.bicep"
    assert config_loaded["params"]["location"] == "Ref:azurite-sample.rg-azurite-sample-01.azurite_automation_storage:storageLocation"
    assert config_loaded["params"]["appName"] == "azuriteAutomation"
    assert config_loaded["params"]["skuName"] == "Free"
    assert config_loaded == config_expected_loaded_output

def test_deploy_load_location2():
    config_path = "azurite-sample/rg-azurite-sample-01/azurite_automation_account.yaml"
    config_expected_loaded_location = "australiaeast"

    location_config_loaded = orchestrator.load_location(config_path)
    assert type(location_config_loaded) == str
    assert location_config_loaded == config_expected_loaded_location
