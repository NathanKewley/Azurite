from unittest.mock import patch
import json
import pytest

from azurite.lib.subproc import Subproc
from azurite.lib.subscription import Subscription


def test_check_if_current():
    sample_azure_response = open('tests/test_output/test_subproc_get_current_subscription.json', 'r').read()
    with patch.object(Subproc, 'get_current_subscription', return_value = sample_azure_response):
        subproc = Subproc()
        subscription = Subscription(subproc)

        assert subscription.check_if_current("azurite-sample")
        assert not subscription.check_if_current("not-azurite-sample")

def test_set_subscription():
    sample_azure_response = open('tests/test_output/test_subproc_get_current_subscription.json', 'r').read()
    subscriptions = json.dumps([{"name": "azurite-sample", "id": "1111"}, {"name": "services-prod", "id": "2222"}])
    with patch.object(Subproc, 'get_current_subscription', return_value = sample_azure_response), \
         patch.object(Subproc, 'list_subscriptions', return_value = subscriptions), \
         patch.object(Subproc, 'set_subscription') as set_subscription:
        subproc = Subproc()
        subscription = Subscription(subproc)

        subscription.set_subscription("azurite-sample")
        set_subscription.assert_not_called()

        subscription.set_subscription("services-prod")
        set_subscription.assert_called_once_with("2222")

def test_set_subscription_not_found():
    sample_azure_response = open('tests/test_output/test_subproc_get_current_subscription.json', 'r').read()
    with patch.object(Subproc, 'get_current_subscription', return_value = sample_azure_response), \
         patch.object(Subproc, 'list_subscriptions', return_value = "[]"):
        subproc = Subproc()
        subscription = Subscription(subproc)

        with pytest.raises(SystemExit) as e:
            subscription.set_subscription("does-not-exist")
        assert e.value.code == 1
