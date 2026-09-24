from unittest.mock import patch
import json
import os

from azurite.lib.subproc import Subproc
from azurite.lib.deployer import Deployer
from azurite.lib.subscription import Subscription


def test_resource_group_exists():
    sample_azure_response = open('tests/test_output/test_subproc_get_resource_groups.json', 'r').read()
    with patch.object(Subproc, 'get_resource_groups', return_value = sample_azure_response):
        subproc = Subproc()
        subscription = Subscription(subproc)
        deployer = Deployer(subproc, subscription)

        assert deployer.resource_group_exists("rg-azurite-sample-01")
        assert not deployer.resource_group_exists("rg-azurite-sample-02")

def test_get_deployment_output():
    sample_azure_response = open('tests/test_output/test_subproc_get_deployment_output.json', 'r').read()
    with patch.object(Subproc, 'get_deployment_output', return_value = sample_azure_response):
        subproc = Subproc()
        subscription = Subscription(subproc)
        deployer = Deployer(subproc, subscription)
        assert deployer.get_deployment_output("azurite-sample.rg-azurite-sample-01.azurite_automation_storage", "storageLocation","rg-azurite-sample-01") == "australiaeast"

def test_get_deployment_output_param():
    sample_azure_response = open('tests/test_output/test_subproc_get_deployment_output.json', 'r').read()
    with patch.object(Subproc, 'get_deployment_output', return_value = sample_azure_response):
        with patch.object(Subproc, 'set_subscription', return_value = True):
            with patch.object(Subscription, 'set_subscription', return_value = True):
                subproc = Subproc()
                subscription = Subscription(subproc)
                deployer = Deployer(subproc, subscription)
                assert deployer.get_deployment_output_param("Ref:azurite-sample.rg-azurite-sample-01.azurite_automation_storage:storageLocation", "azurite-sample")
                assert True

def test_build_parameters():
    with patch.object(Deployer, 'get_deployment_output_param', return_value = "australiaeast"):
        subproc = Subproc()
        subscription = Subscription(subproc)
        deployer = Deployer(subproc, subscription)
        params = {
            'location': 'Ref:azurite-sample.rg-azurite-sample-01.azurite_automation_storage:storageLocation',
            'storageName': 'azurisampleorekew',
            'displayName': 'Name With Spaces',
            'addressPrefixes': ['10.0.0.0/20', '10.1.0.0/20'],
            'tags': {'env': 'prod'},
            'enabled': True,
            'count': 3
        }
        assert deployer.build_parameters(params, "azurite-sample") == {
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
    parameters_file = deployer.write_parameters_file({'allowedLocations': ['australiaeast'], 'enabled': False}, "azurite-sample")
    try:
        parameters = json.loads(open(parameters_file, 'r').read())
        assert parameters['contentVersion'] == "1.0.0.0"
        assert parameters['parameters'] == {'allowedLocations': {'value': ['australiaeast']}, 'enabled': {'value': False}}
    finally:
        os.remove(parameters_file)
