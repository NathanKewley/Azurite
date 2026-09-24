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

def test_get_child_directories():
    path = "configuration/services-prod/"
    result = orchestrator.get_child_directories(path)
    assert result == ["policy", "rg-azurite-sample-01", "rg-azurite-sample-02"]

def make_messy_configuration(root):
    resource_group = root / "configuration" / "sub-a" / "rg-a"
    resource_group.mkdir(parents=True)
    (root / "configuration" / "sub-b" / "rg-b").mkdir(parents=True)
    (root / "configuration" / ".hidden-sub").mkdir()
    (root / "configuration" / "README.md").write_text("docs")
    (root / "configuration" / "sub-a" / "notes.txt").write_text("notes")
    (root / "configuration" / "sub-a" / ".DS_Store").write_text("")
    for name in ["location.yaml", "b_storage.yaml", "a_network.yaml", "legacy.yml", "README.md", ".DS_Store", ".hidden.yaml"]:
        (resource_group / name).write_text("---\n")
    (resource_group / "subfolder.yaml").mkdir()
    (resource_group / "archive").mkdir()

def test_get_configurations_skips_non_configurations(tmp_path, monkeypatch, caplog):
    make_messy_configuration(tmp_path)
    monkeypatch.chdir(tmp_path)
    orchestrator = Orchestrator()
    orchestrator.logger.propagate = True
    with caplog.at_level("WARNING", logger="logging"):
        assert orchestrator.get_configurations("configuration/sub-a/rg-a/") == ["a_network.yaml", "b_storage.yaml"]
    assert "legacy.yml: configuration files must use the .yaml extension" in caplog.text
    assert "README.md" not in caplog.text

def test_deploy_walkers_skip_stray_files(tmp_path, monkeypatch):
    make_messy_configuration(tmp_path)
    monkeypatch.chdir(tmp_path)
    orchestrator = Orchestrator()
    assert orchestrator.deploy_account(dry_run=True) == ["sub-a", "sub-b"]
    assert orchestrator.deploy_subscription("sub-a", dry_run=True) == ["sub-a/rg-a"]
    assert orchestrator.deploy_resource_group("sub-a/rg-a", dry_run=True) == ["sub-a/rg-a/a_network.yaml", "sub-a/rg-a/b_storage.yaml"]

def test_deploy_resource_group_only_deploys_configurations(tmp_path, monkeypatch):
    make_messy_configuration(tmp_path)
    monkeypatch.chdir(tmp_path)
    orchestrator = Orchestrator()
    with patch.object(Orchestrator, 'deploy') as deploy:
        orchestrator.deploy_resource_group("sub-a/rg-a", deploy_mode="destroy")
    assert [c.args[0] for c in deploy.call_args_list] == ["sub-a/rg-a/a_network.yaml", "sub-a/rg-a/b_storage.yaml"]

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

def test_deploy_invalid_scope(tmp_path, monkeypatch):
    resource_group = tmp_path / "configuration" / "sub" / "rg"
    resource_group.mkdir(parents=True)
    (tmp_path / "bicep").mkdir()
    (tmp_path / "bicep" / "storage.bicep").write_text("")
    (resource_group / "location.yaml").write_text("---\nlocation: australiaeast\n")
    (resource_group / "app.yaml").write_text("---\nbicep_path: storage.bicep\nscope: subscriptoin\n")
    monkeypatch.chdir(tmp_path)
    orchestrator = Orchestrator()
    with patch.object(Deployer, 'deploy_bicep') as deploy_group, \
         patch.object(Deployer, 'deploy_bicep_subscription') as deploy_subscription:
        with pytest.raises(SystemExit) as e:
            orchestrator.deploy("sub/rg/app.yaml")
        assert e.value.code == 1
        deploy_group.assert_not_called()
        deploy_subscription.assert_not_called()
