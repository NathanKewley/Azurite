from azurite.lib.orchestrator import Orchestrator


orchestrator = Orchestrator()

def test_get_deployment_name():
    config_path = "azurite-sample/rg-azurite-sample-01/azurite_automation_account.yaml"
    result = orchestrator.get_deployment_name(config_path)
    assert result == "azurite-sample.rg-azurite-sample-01.azurite_automation_account"

def test_get_resource_group():
    config_path = "azurite-sample/rg-azurite-sample-01/azurite_automation_account.yaml"
    result = orchestrator.get_resource_group(config_path)
    assert result == "rg-azurite-sample-01"

def test_get_subscription():
    config_path = "azurite-sample/rg-azurite-sample-01/azurite_automation_account.yaml"
    result = orchestrator.get_subscription(config_path)
    assert result == "azurite-sample"

def test_get_child_items():
    path = "configuration/azurite-sample/"
    result = orchestrator.get_child_items(path)
    assert "rg-azurite-sample-01" in result
    assert "rg-azurite-sample-02" in result
    assert len(result) == 2

def test_deploy():
    configuration = "azurite-sample/rg-azurite-sample-01/azurite_automation_account.yaml"
    result = orchestrator.deploy(configuration, dry_run=True)
    assert len(result[0]) == 3
    assert result[0].items() == {('location', 'Ref:azurite-sample.rg-azurite-sample-01.azurite_automation_storage:storageLocation'), ('appName', 'azuriteAutomation'), ('skuName', 'Free')}
    assert result[1] == "automation/automation_account.bicep"
    assert result[2] == "rg-azurite-sample-01"
    assert result[3] == "australiaeast"
    assert result[4] == "azurite-sample.rg-azurite-sample-01.azurite_automation_account"
    assert result[5] == "azurite-sample"

def test_deploy_resource_group():
    configuration = "azurite-sample/rg-azurite-sample-01"
    result = orchestrator.deploy_resource_group(configuration, dry_run=True)
    assert len(result) == 2
    assert "azurite-sample/rg-azurite-sample-01/azurite_automation_account.yaml" in result
    assert "azurite-sample/rg-azurite-sample-01/azurite_automation_storage.yaml" in result

def test_deploy_subscription():
    configuration = "azurite-sample"
    result = orchestrator.deploy_subscription(configuration, dry_run=True)
    assert len(result) == 2
    assert "azurite-sample/rg-azurite-sample-01" in result
    assert "azurite-sample/rg-azurite-sample-02" in result

def test_deploy_account():
    result = orchestrator.deploy_account(dry_run=True)
    assert len(result) == 1
    assert "azurite-sample" in result
