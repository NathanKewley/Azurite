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
    with patch.object(Subproc, 'resource_group_exists', return_value = (0, "true\n")):
        assert deployer.resource_group_exists("rg-nitra-sample-01")
    with patch.object(Subproc, 'resource_group_exists', return_value = (0, "false\n")):
        assert not deployer.resource_group_exists("rg-nitra-sample-02")

def test_resource_group_exists_az_error():
    subproc = Subproc()
    subscription = Subscription(subproc)
    deployer = Deployer(subproc, subscription)
    with patch.object(Subproc, 'resource_group_exists', return_value = (1, "ERROR: AADSTS700082: The refresh token has expired")):
        with pytest.raises(SystemExit) as e:
            deployer.resource_group_exists("rg-nitra-sample-01")
        assert e.value.code == 1

def test_create_resource_group_failure():
    subproc = Subproc()
    subscription = Subscription(subproc)
    deployer = Deployer(subproc, subscription)
    with patch.object(Subproc, 'create_resource_group', return_value = (1, "ERROR: AuthorizationFailed")):
        with pytest.raises(SystemExit) as e:
            deployer.create_resource_group("rg-nitra-sample-01", "australiaeast")
        assert e.value.code == 1

def test_deploy_bicep_stops_when_resource_group_check_fails():
    subproc = Subproc()
    subscription = Subscription(subproc)
    deployer = Deployer(subproc, subscription)
    with patch.object(Subscription, 'set_subscription'), \
         patch.object(Subproc, 'resource_group_exists', return_value = (1, "ERROR: AADSTS700082: The refresh token has expired")), \
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
        assert deployer.get_deployment_output("nitra-sample.rg-nitra-sample-01.nitra_automation_storage", "storageLocation","rg-nitra-sample-01") == "australiaeast"
        get_stack.assert_called_with("nitra-sample.rg-nitra-sample-01.nitra_automation_storage", "rg-nitra-sample-01")

def test_get_deployment_output_subscription_scope():
    sample_azure_response = open('tests/test_output/test_subproc_get_deployment_output.json', 'r').read()
    with patch.object(Subproc, 'get_stack', return_value = (0, sample_azure_response)) as get_stack:
        subproc = Subproc()
        subscription = Subscription(subproc)
        deployer = Deployer(subproc, subscription)
        assert deployer.get_deployment_output("nitra-sample.policy.allowed-locations", "storageLocation", "policy", "subscription") == "australiaeast"
        get_stack.assert_called_with("nitra-sample.policy.allowed-locations", None)

def test_get_deployment_output_not_found():
    with patch.object(Subproc, 'get_stack', return_value = (3, "")):
        subproc = Subproc()
        subscription = Subscription(subproc)
        deployer = Deployer(subproc, subscription)
        with pytest.raises(SystemExit) as e:
            deployer.get_deployment_output("nitra-sample.rg-nitra-sample-01.missing", "storageLocation", "rg-nitra-sample-01")
        assert e.value.code == 1

def test_get_deployment_output_missing_output():
    sample_azure_response = open('tests/test_output/test_subproc_get_deployment_output.json', 'r').read()
    with patch.object(Subproc, 'get_stack', return_value = (0, sample_azure_response)):
        subproc = Subproc()
        subscription = Subscription(subproc)
        deployer = Deployer(subproc, subscription)
        with pytest.raises(SystemExit) as e:
            deployer.get_deployment_output("nitra-sample.rg-nitra-sample-01.nitra_automation_storage", "notAnOutput", "rg-nitra-sample-01")
        assert e.value.code == 1

def test_get_deployment_output_param():
    sample_azure_response = open('tests/test_output/test_subproc_get_deployment_output.json', 'r').read()
    with patch.object(Subproc, 'get_stack', return_value = (0, sample_azure_response)) as get_stack:
        with patch.object(Deployer, 'get_reference_scope', return_value = "resource_group"):
            with patch.object(Subscription, 'set_subscription', return_value = True):
                subproc = Subproc()
                subscription = Subscription(subproc)
                deployer = Deployer(subproc, subscription)
                assert deployer.get_deployment_output_param("Ref:services-prod.rg-nitra-sample-01.nitra_automation_storage:storageLocation", "services-prod") == "australiaeast"
                get_stack.assert_called_with("services-prod.rg-nitra-sample-01.nitra_automation_storage", "rg-nitra-sample-01")

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
        assert deployer.build_parameters(params, "nitra-sample") == {
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
    parameters_file = deployer.write_parameters_file({'allowedLocations': ['australiaeast'], 'enabled': False}, "nitra-sample")
    try:
        parameters = json.loads(open(parameters_file, 'r').read())
        assert parameters['contentVersion'] == "1.0.0.0"
        assert parameters['parameters'] == {'allowedLocations': {'value': ['australiaeast']}, 'enabled': {'value': False}}
    finally:
        os.remove(parameters_file)
