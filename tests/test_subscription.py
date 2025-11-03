from unittest.mock import patch
import json

from azurite.lib.subproc import Subproc
from azurite.lib.subscription import Subscription


def test_check_if_current():
    sample_azure_response = open('tests/test_output/test_subproc_get_current_subscription.json', 'r').read()
    with patch.object(Subproc, 'get_current_subscription', return_value = sample_azure_response):
        subproc = Subproc()
        subscription = Subscription(subproc)

        assert subscription.check_if_current("azurite-sample")
        assert not subscription.check_if_current("not-azurite-sample")
