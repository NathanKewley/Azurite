from unittest.mock import patch
import json

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

def test_build_param_string():
    sample_azure_response = open('tests/test_output/test_subproc_get_deployment_output.json', 'r').read()
    with patch.object(Subproc, 'get_deployment_output', return_value = sample_azure_response):
        with patch.object(Subproc, 'set_subscription', return_value = True):
            with patch.object(Subscription, 'set_subscription', return_value = True):
                subproc = Subproc()
                subscription = Subscription(subproc)
                deployer = Deployer(subproc, subscription)    
                params = {'location': 'australiaeast', 'storageName': 'azurisampleorekew', 'containerName': 'azuriteautomation', 'skuName': 'Standard_LRS'}
                assert deployer.build_param_string(params, "azurite-sample") == "location=australiaeast storageName=azurisampleorekew containerName=azuriteautomation skuName=Standard_LRS"
                assert True
