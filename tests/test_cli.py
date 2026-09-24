from unittest.mock import patch
import sys
import pytest

import azurite
from azurite.lib.orchestrator import Orchestrator
from azurite.lib.subproc import Subproc


def test_login_checked_before_operation():
    calls = []
    with patch.object(sys, 'argv', ["azurite", "deploy", "services-prod/rg-azurite-sample-02/sample_storage.yaml"]), \
         patch.object(Subproc, 'check_azure_login', side_effect = lambda: calls.append("login") or (0, "2026-09-24 18:19:50.000000\n")), \
         patch.object(Orchestrator, 'deploy', side_effect = lambda configuration: calls.append(f"deploy {configuration}")):
        azurite.azurite()
    assert calls == ["login", "deploy services-prod/rg-azurite-sample-02/sample_storage.yaml"]

def test_expired_login_stops_before_operation():
    with patch.object(sys, 'argv', ["azurite", "deploy-account"]), \
         patch.object(Subproc, 'check_azure_login', return_value = (1, "ERROR: AADSTS700082: The refresh token has expired due to inactivity.")), \
         patch.object(Orchestrator, 'deploy_account') as deploy_account:
        with pytest.raises(SystemExit) as e:
            azurite.azurite()
        assert e.value.code == 1
        deploy_account.assert_not_called()
