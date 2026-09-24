from unittest.mock import patch
import pytest

from azurite.lib.orchestrator import Orchestrator
from azurite.lib.deployer import Deployer
from azurite.lib.subproc import Subproc
from azurite.lib.subscription import Subscription


orchestrator = Orchestrator()

def test_get_deployment_name():
    config_path = "services-prod/rg-azurite-sample-01/azurite_automation_account.yaml"
    result = orchestrator.get_deployment_name(config_path)
    assert result == "services-prod.rg-azurite-sample-01.azurite_automation_account"

def test_get_resource_group():
    config_path = "services-prod/rg-azurite-sample-01/azurite_automation_account.yaml"
    result = orchestrator.get_resource_group(config_path)
    assert result == "rg-azurite-sample-01"

def test_get_subscription():
    config_path = "services-prod/rg-azurite-sample-01/azurite_automation_account.yaml"
    result = orchestrator.get_subscription(config_path)
    assert result == "services-prod"

def test_get_child_items():
    path = "configuration/services-prod/"
    result = orchestrator.get_child_items(path)
    assert sorted(result) == ["policy", "rg-azurite-sample-01", "rg-azurite-sample-02"]

def test_deploy():
    configuration = "services-prod/rg-azurite-sample-01/azurite_automation_account.yaml"
    result = Orchestrator().deploy(configuration, dry_run=True)
    assert result[0] == {'location': 'Ref:services-prod.rg-azurite-sample-01.azurite_automation_storage:storageLocation', 'appName': 'azuriteAutomation', 'skuName': 'Free'}
    assert result[1] == "automation/automation_account.bicep"
    assert result[2] == "rg-azurite-sample-01"
    assert result[3] == "australiaeast"
    assert result[4] == "services-prod.rg-azurite-sample-01.azurite_automation_account"
    assert result[5] == "services-prod"

def test_deploy_resource_group():
    configuration = "services-prod/rg-azurite-sample-01"
    result = orchestrator.deploy_resource_group(configuration, dry_run=True)
    assert sorted(result) == [
        "services-prod/rg-azurite-sample-01/azurite_automation_account.yaml",
        "services-prod/rg-azurite-sample-01/azurite_automation_storage.yaml",
        "services-prod/rg-azurite-sample-01/azurite_module_virtualnetwork.yaml"
    ]

def test_deploy_subscription():
    configuration = "services-prod"
    result = orchestrator.deploy_subscription(configuration, dry_run=True)
    assert sorted(result) == ["services-prod/policy", "services-prod/rg-azurite-sample-01", "services-prod/rg-azurite-sample-02"]

def test_deploy_account():
    result = orchestrator.deploy_account(dry_run=True)
    assert result == ["services-prod"]

def test_destroy_subscription_scope():
    orchestrator = Orchestrator()
    with patch.object(Orchestrator, 'stack_exists', return_value = True) as stack_exists, \
         patch.object(Deployer, 'destroy_bicep_subscription') as destroy_subscription, \
         patch.object(Deployer, 'destroy_bicep') as destroy_group:
        orchestrator.destroy("services-prod/policy/allowed-locations.yaml")
        stack_exists.assert_called_with("services-prod.policy.allowed-locations", "policy", "services-prod", "subscription")
        destroy_subscription.assert_called_once_with("services-prod.policy.allowed-locations", "services-prod", "deleteResources")
        destroy_group.assert_not_called()

def test_destroy_resource_group_scope():
    orchestrator = Orchestrator()
    with patch.object(Orchestrator, 'stack_exists', return_value = True) as stack_exists, \
         patch.object(Deployer, 'destroy_bicep_subscription') as destroy_subscription, \
         patch.object(Deployer, 'destroy_bicep') as destroy_group:
        orchestrator.destroy("services-prod/rg-azurite-sample-02/sample_storage.yaml")
        stack_exists.assert_called_with("services-prod.rg-azurite-sample-02.sample_storage", "rg-azurite-sample-02", "services-prod", "resource_group")
        destroy_group.assert_called_once_with("rg-azurite-sample-02", "services-prod.rg-azurite-sample-02.sample_storage", "services-prod", "deleteResources")
        destroy_subscription.assert_not_called()

def test_destroy_missing_stack_is_skipped():
    orchestrator = Orchestrator()
    with patch.object(Orchestrator, 'stack_exists', return_value = False), \
         patch.object(Deployer, 'destroy_bicep_subscription') as destroy_subscription, \
         patch.object(Deployer, 'destroy_bicep') as destroy_group:
        orchestrator.destroy("services-prod/policy/allowed-locations.yaml")
        destroy_subscription.assert_not_called()
        destroy_group.assert_not_called()

def test_stack_exists_subscription_scope_has_no_resource_group():
    orchestrator = Orchestrator()
    with patch.object(Subscription, 'set_subscription') as set_subscription, \
         patch.object(Subproc, 'get_stack', return_value = (0, "{}")) as get_stack:
        assert orchestrator.stack_exists("services-prod.policy.allowed-locations", "policy", "services-prod", "subscription")
        set_subscription.assert_called_with("services-prod")
        get_stack.assert_called_with("services-prod.policy.allowed-locations", None)

def test_stack_exists_not_found():
    orchestrator = Orchestrator()
    with patch.object(Subscription, 'set_subscription'), \
         patch.object(Subproc, 'get_stack', return_value = (3, "")) as get_stack:
        assert not orchestrator.stack_exists("services-prod.rg-azurite-sample-02.sample_storage", "rg-azurite-sample-02", "services-prod", "resource_group")
        get_stack.assert_called_with("services-prod.rg-azurite-sample-02.sample_storage", "rg-azurite-sample-02")

def test_deploy_invalid_scope():
    orchestrator = Orchestrator()
    config = {"bicep_path": "storage/storage_account.bicep", "scope": "subscriptoin", "params": {}}
    with patch.object(Orchestrator, 'load_config', return_value = config), \
         patch.object(Deployer, 'deploy_bicep') as deploy_group:
        with pytest.raises(SystemExit) as e:
            orchestrator.deploy("services-prod/rg-azurite-sample-02/sample_storage.yaml")
        assert e.value.code == 1
        deploy_group.assert_not_called()
