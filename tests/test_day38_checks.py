"""Day 38 tests for the plugin contract and ZAP active-check adapter."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sentinelai.checks import CheckType, ZAPActiveCheck, ZAPClient, ZAPError, run_all_checks
from sentinelai.checks.zap import normalize_zap_alert


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_active_check_refuses_without_authorization():
    called = []

    def request(*args, **kwargs):
        called.append((args, kwargs))
        return FakeResponse({"version": "2.0"})

    check = ZAPActiveCheck(ZAPClient(request=request))
    with pytest.raises(ZAPError, match="active_authorized=True"):
        check.run("http://juice-shop.local")
    assert called == []


def test_active_check_requires_complete_url():
    check = ZAPActiveCheck(ZAPClient(request=lambda *args, **kwargs: None))
    with pytest.raises(ZAPError, match="complete http://"):
        check.run("juice-shop.local", active_authorized=True)


def test_zap_alerts_are_normalized_to_shared_finding():
    finding = normalize_zap_alert(
        {
            "pluginId": "40018",
            "alert": "SQL Injection",
            "riskdesc": "High (Medium)",
            "confidence": "Medium",
            "cweid": "89",
            "url": "http://juice-shop.local/search?q=1",
            "method": "GET",
            "param": "q",
            "evidence": "database error",
            "tags": {"OWASP": "A03:2021 - Injection"},
        }
    )
    data = finding.to_dict()
    assert data["plugin_id"] == 40018
    assert data["cwe_id"] == 89
    assert data["param"] == "q"
    assert data["check_type"] == "active"
    assert data["confirmed"] is True
    assert data["tags"]["OWASP"].startswith("A03")


def test_zap_check_runs_and_polls_then_returns_findings():
    calls = []
    responses = iter(
        [
            {"version": "2.15.0"},
            {"scan": "7"},
            {"status": "50"},
            {"status": "100"},
            {"alerts": [{"pluginId": "10020", "alert": "Header missing", "risk": "Low"}]},
        ]
    )

    def request(method, url, **kwargs):
        calls.append((method, url, kwargs["params"]))
        return FakeResponse(next(responses))

    check = ZAPActiveCheck(
        ZAPClient(request=request, timeout=2),
    )
    findings = check.run(
        "http://juice-shop.local", active_authorized=True
    )
    assert len(findings) == 1
    assert findings[0].name == "Header missing"
    assert findings[0].check_type is CheckType.ACTIVE
    assert [call[1].split("/JSON/")[1] for call in calls] == [
        "core/view/version/",
        "ascan/action/scan/",
        "ascan/view/status/",
        "ascan/view/status/",
        "core/view/alerts/",
    ]


def test_orchestrator_isolates_failed_check():
    class BrokenCheck:
        name = "broken"

        def run(self, target, *, active_authorized=False):
            raise RuntimeError("daemon unavailable")

    class EmptyCheck:
        name = "empty"

        def run(self, target, *, active_authorized=False):
            return []

    result = run_all_checks(
        "http://juice-shop.local",
        [BrokenCheck(), EmptyCheck()],
        active_authorized=True,
    )
    assert result["checks"] == ["broken", "empty"]
    assert result["findings"] == []
    assert result["errors"] == [{"check": "broken", "error": "daemon unavailable"}]
