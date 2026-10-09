"""Day 41 live ZAP harness smoke test for the authorized scan path."""

from __future__ import annotations

from unittest.mock import patch

from sentinelai.active_gate import run_authorized_active_checks


def test_run_authorized_active_checks_verifies_zap_reachability_first():
    with patch("sentinelai.active_gate.ZAPClient.version", return_value="2.15.0") as mock_version, patch(
        "sentinelai.active_gate.ZAPActiveCheck"
    ) as mock_check_cls, patch("sentinelai.active_gate.run_all_checks") as mock_orchestrator:
        mock_check = object()
        mock_check_cls.return_value = mock_check
        mock_orchestrator.return_value = {"count": 0, "findings": [], "errors": []}

        result = run_authorized_active_checks("http://juice-shop.local")

        assert result["count"] == 0
        mock_version.assert_called_once_with()
        mock_check_cls.assert_called_once()
        mock_orchestrator.assert_called_once_with(
            "http://juice-shop.local",
            [mock_check],
            active_authorized=True,
        )
