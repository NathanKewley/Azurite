from unittest.mock import patch
import json
import os
import pytest

from nitra.lib.subproc import Subproc
from nitra.lib.deployer import Deployer
from nitra.lib.subscription import Subscription


def test_resource_group_exists():
    subproc = Subproc()
    subscription = Subscription(subproc)
    deployer = Deployer(subproc, subscription)
    with patch.object(Subproc, 'resource_group_exists', return_value = (0, "true\n")) as exists:
        assert deployer.resource_group_exists("rg-nitra-sample-01", "id-services-prod")
        exists.assert_called_with("rg-nitra-sample-01", "id-services-prod")
    with patch.object(Subproc, 'resource_group_exists', return_value = (0, "false\n")):
        assert not deployer.resource_group_exists("rg-nitra-sample-02", "id-services-prod")

def test_resource_group_exists_az_error():
    subproc = Subproc()
    subscription = Subscription(subproc)
    deployer = Deployer(subproc, subscription)
    with patch.object(Subproc, 'resource_group_exists', return_value = (1, "ERROR: AADSTS700082: The refresh token has expired")):
        with pytest.raises(SystemExit) as e:
            deployer.resource_group_exists("rg-nitra-sample-01", "id-services-prod")
        assert e.value.code == 1

def test_create_resource_group_failure():
    subproc = Subproc()
    subscription = Subscription(subproc)
    deployer = Deployer(subproc, subscription)
    with patch.object(Subproc, 'create_resource_group', return_value = (1, "ERROR: AuthorizationFailed")):
        with pytest.raises(SystemExit) as e:
            deployer.create_resource_group("rg-nitra-sample-01", "australiaeast", "id-services-prod")
        assert e.value.code == 1

def test_deploy_bicep_stops_when_resource_group_check_fails():
    subproc = Subproc()
    subscription = Subscription(subproc)
    deployer = Deployer(subproc, subscription)
    with patch.object(Subproc, 'resource_group_exists', return_value = (1, "ERROR: AADSTS700082: The refresh token has expired")), \
         patch.object(Subproc, 'create_resource_group') as create_resource_group, \
         patch.object(Subproc, 'deploy_group_create') as deploy_group_create:
        with pytest.raises(SystemExit) as e:
            deployer.deploy_bicep({}, "storage/storage_account.bicep", "rg-nitra-sample-01", "australiaeast", "sub.rg.config", "deleteResources", "None", "services-prod")
        assert e.value.code == 1
        create_resource_group.assert_not_called()
        deploy_group_create.assert_not_called()

def test_get_deployment_output():
    sample_azure_response = open('tests/test_output/test_subproc_get_deployment_output.json', 'r').read()
    with patch.object(Subproc, 'get_stack', return_value = (0, sample_azure_response)) as get_stack:
        subproc = Subproc()
        subscription = Subscription(subproc)
        deployer = Deployer(subproc, subscription)
        assert deployer.get_deployment_output("nitra-sample.rg-nitra-sample-01.nitra_automation_storage", "storageLocation", "rg-nitra-sample-01", "nitra-sample") == "australiaeast"
        get_stack.assert_called_with("nitra-sample.rg-nitra-sample-01.nitra_automation_storage", "rg-nitra-sample-01", "id-nitra-sample")

def test_get_deployment_output_subscription_scope():
    sample_azure_response = open('tests/test_output/test_subproc_get_deployment_output.json', 'r').read()
    with patch.object(Subproc, 'get_stack', return_value = (0, sample_azure_response)) as get_stack:
        subproc = Subproc()
        subscription = Subscription(subproc)
        deployer = Deployer(subproc, subscription)
        assert deployer.get_deployment_output("nitra-sample.policy.allowed-locations", "storageLocation", "policy", "nitra-sample", "subscription") == "australiaeast"
        get_stack.assert_called_with("nitra-sample.policy.allowed-locations", None, "id-nitra-sample")

def test_get_deployment_output_not_found():
    with patch.object(Subproc, 'get_stack', return_value = (3, "")):
        subproc = Subproc()
        subscription = Subscription(subproc)
        deployer = Deployer(subproc, subscription)
        with pytest.raises(SystemExit) as e:
            deployer.get_deployment_output("nitra-sample.rg-nitra-sample-01.missing", "storageLocation", "rg-nitra-sample-01", "nitra-sample")
        assert e.value.code == 1

def test_get_deployment_output_missing_output():
    sample_azure_response = open('tests/test_output/test_subproc_get_deployment_output.json', 'r').read()
    with patch.object(Subproc, 'get_stack', return_value = (0, sample_azure_response)):
        subproc = Subproc()
        subscription = Subscription(subproc)
        deployer = Deployer(subproc, subscription)
        with pytest.raises(SystemExit) as e:
            deployer.get_deployment_output("nitra-sample.rg-nitra-sample-01.nitra_automation_storage", "notAnOutput", "rg-nitra-sample-01", "nitra-sample")
        assert e.value.code == 1

def test_get_deployment_output_param():
    sample_azure_response = open('tests/test_output/test_subproc_get_deployment_output.json', 'r').read()
    with patch.object(Subproc, 'get_stack', return_value = (0, sample_azure_response)) as get_stack:
        with patch.object(Deployer, 'get_reference_scope', return_value = "resource_group"):
            subproc = Subproc()
            subscription = Subscription(subproc)
            deployer = Deployer(subproc, subscription)
            assert deployer.get_deployment_output_param("Ref:services-prod.rg-nitra-sample-01.nitra_automation_storage:storageLocation") == "australiaeast"
            # looked up in the referenced config's subscription, without switching the default subscription
            get_stack.assert_called_with("services-prod.rg-nitra-sample-01.nitra_automation_storage", "rg-nitra-sample-01", "id-services-prod")

def test_get_reference_scope():
    subproc = Subproc()
    subscription = Subscription(subproc)
    deployer = Deployer(subproc, subscription)
    assert deployer.get_reference_scope("services-prod/policy/allowed-locations.yaml") == "subscription"
    assert deployer.get_reference_scope("services-prod/rg-nitra-sample-01/nitra_automation_storage.yaml") == "resource_group"

def test_build_parameters():
    with patch.object(Deployer, 'get_deployment_output_param', return_value = "australiaeast"):
        subproc = Subproc()
        subscription = Subscription(subproc)
        deployer = Deployer(subproc, subscription)
        params = {
            'location': 'Ref:nitra-sample.rg-nitra-sample-01.nitra_automation_storage:storageLocation',
            'storageName': 'azurisampleorekew',
            'displayName': 'Name With Spaces',
            'addressPrefixes': ['10.0.0.0/20', '10.1.0.0/20'],
            'tags': {'env': 'prod'},
            'enabled': True,
            'count': 3
        }
        assert deployer.build_parameters(params) == {
            'location': {'value': 'australiaeast'},
            'storageName': {'value': 'azurisampleorekew'},
            'displayName': {'value': 'Name With Spaces'},
            'addressPrefixes': {'value': ['10.0.0.0/20', '10.1.0.0/20']},
            'tags': {'value': {'env': 'prod'}},
            'enabled': {'value': True},
            'count': {'value': 3}
        }

def test_write_parameters_file():
    subproc = Subproc()
    subscription = Subscription(subproc)
    deployer = Deployer(subproc, subscription)
    parameters_file = deployer.write_parameters_file({'allowedLocations': ['australiaeast'], 'enabled': False})
    try:
        parameters = json.loads(open(parameters_file, 'r').read())
        assert parameters['contentVersion'] == "1.0.0.0"
        assert parameters['parameters'] == {'allowedLocations': {'value': ['australiaeast']}, 'enabled': {'value': False}}
    finally:
        os.remove(parameters_file)

def test_deploy_bicep_targets_subscription_without_switching():
    subproc = Subproc()
    subscription = Subscription(subproc)
    deployer = Deployer(subproc, subscription)
    with patch.object(Subproc, 'resource_group_exists', return_value = (0, "false")) as exists, \
         patch.object(Subproc, 'create_resource_group', return_value = (0, "{}")) as create, \
         patch.object(Subproc, 'deploy_group_create', return_value = (0, "{}")) as deploy_group_create:
        deployer.deploy_bicep({}, "storage.bicep", "rg", "australiaeast", "sub.rg.config", "deleteResources", "None", "sub")
    exists.assert_called_once_with("rg", "id-sub")
    create.assert_called_once_with("rg", "australiaeast", "id-sub")
    assert deploy_group_create.call_args.args[-1] == "id-sub"

def test_destroy_targets_subscription_without_switching():
    subproc = Subproc()
    subscription = Subscription(subproc)
    deployer = Deployer(subproc, subscription)
    with patch.object(Subproc, 'resource_group_exists', return_value = (0, "true")), \
         patch.object(Subproc, 'deploy_group_destroy', return_value = (0, "")) as group_destroy, \
         patch.object(Subproc, 'deploy_subscription_destroy', return_value = (0, "")) as sub_destroy:
        deployer.destroy_bicep("rg", "sub.rg.config", "sub", "deleteResources")
        deployer.destroy_bicep_subscription("sub.policy.config", "sub", "deleteResources")
    group_destroy.assert_called_once_with("rg", "sub.rg.config", "deleteResources", "id-sub")
    sub_destroy.assert_called_once_with("sub.policy.config", "deleteResources", "id-sub")
