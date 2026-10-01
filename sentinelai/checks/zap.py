"""OWASP ZAP adapter for the Day 38 active-check box.

SentinelAI delegates active request generation to ZAP. This module only calls
ZAP's API, enforces the explicit authorization boundary, and normalizes alert
records for the existing ZAP findings/LLM pipeline.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

import requests

from sentinelai.checks.base import CheckType, Finding, VulnerabilityCheck


class ZAPError(RuntimeError):
    """Raised when ZAP cannot execute or return an active scan."""


class ZAPClient:
    """Small JSON API client for a locally running OWASP ZAP daemon."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8080",
        *,
        api_key: Optional[str] = None,
        timeout: float = 10.0,
        request: Optional[Callable[..., Any]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._request = request or requests.request

    def _call(self, method: str, path: str, **params: Any) -> Dict[str, Any]:
        if self.api_key:
            params.setdefault("apikey", self.api_key)
        url = f"{self.base_url}{path}"
        try:
            response = self._request(
                method, url, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            raise ZAPError(
                f"Could not reach ZAP at {self.base_url}: {exc}. "
                "Start the ZAP daemon and retry."
            ) from exc
        except (TypeError, ValueError) as exc:
            raise ZAPError(f"ZAP returned an invalid JSON response: {exc}") from exc

        if not isinstance(payload, dict):
            raise ZAPError("ZAP returned a non-object JSON response.")
        if payload.get("code") == "FAIL" or payload.get("message", "").startswith("Error"):
            raise ZAPError(str(payload.get("message") or payload))
        return payload

    def version(self) -> str:
        """Return the ZAP version, proving the API is reachable."""
        payload = self._call("GET", "/JSON/core/view/version/")
        return str(payload.get("version", "unknown"))

    def run_active_scan(
        self,
        target: str,
        *,
        poll_interval: float = 1.0,
        max_wait: float = 300.0,
    ) -> Dict[str, Any]:
        """Start and wait for ZAP's active scan, then return raw alerts."""
        self.version()
        scan = self._call("GET", "/JSON/ascan/action/scan/", url=target)
        scan_id = scan.get("scan")
        if scan_id is None:
            raise ZAPError(f"ZAP did not return an active-scan ID: {scan}")

        deadline = time.monotonic() + max_wait
        while True:
            status_payload = self._call(
                "GET", "/JSON/ascan/view/status/", scanId=scan_id
            )
            try:
                progress = int(status_payload.get("status", 0))
            except (TypeError, ValueError):
                progress = 0
            if progress >= 100:
                break
            if time.monotonic() >= deadline:
                raise ZAPError(
                    f"ZAP active scan timed out after {max_wait:.0f} seconds "
                    f"(scan id {scan_id})."
                )
            time.sleep(poll_interval)

        return self._call("GET", "/JSON/core/view/alerts/", baseurl=target)


def _risk_and_confidence(alert: Dict[str, Any]) -> tuple[str, str]:
    risk = alert.get("risk") or alert.get("riskdesc") or "Informational"
    confidence = alert.get("confidence") or alert.get("confidenceDesc") or "Unknown"
    return str(risk).split(" ")[0], str(confidence).split(" ")[0]


def normalize_zap_alert(alert: Dict[str, Any]) -> Finding:
    """Convert one ZAP alert shape into the shared Finding contract."""
    risk, confidence = _risk_and_confidence(alert)
    plugin_id = alert.get("plugin_id", alert.get("pluginId"))
    cwe_id = alert.get("cwe_id", alert.get("cweid"))
    try:
        plugin_id = int(plugin_id) if plugin_id not in (None, "") else None
    except (TypeError, ValueError):
        plugin_id = None
    try:
        cwe_id = int(cwe_id) if cwe_id not in (None, "", "0") else None
    except (TypeError, ValueError):
        cwe_id = None

    tags = alert.get("tags") or {}
    if isinstance(tags, list):
        tags = {"values": tags}

    return Finding(
        name=str(alert.get("name", alert.get("alert", "Unnamed ZAP alert"))),
        risk=risk,
        confidence=confidence,
        check_type=CheckType.ACTIVE,
        source="zap-active-scan",
        description=str(alert.get("description", "")),
        url=str(alert.get("url", "")),
        method=str(alert.get("method", "")),
        parameter=str(alert.get("param", "")),
        evidence=str(alert.get("evidence", "")),
        attack=str(alert.get("attack", "")),
        plugin_id=plugin_id,
        cwe_id=cwe_id,
        solution=str(alert.get("solution", "")),
        reference=str(alert.get("reference", "")),
        tags=tags,
    )


class ZAPActiveCheck(VulnerabilityCheck):
    """Active ZAP check that is fail-closed until authorization is explicit."""

    name = "zap-active-scan"
    check_type = CheckType.ACTIVE

    def __init__(self, client: ZAPClient) -> None:
        self.client = client

    def run(self, target: str, *, active_authorized: bool = False) -> List[Finding]:
        if not active_authorized:
            raise ZAPError(
                "ZAP active scanning requires active_authorized=True after "
                "the consent and domain-verification gates pass."
            )
        parsed = urlparse(target)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ZAPError(
                "ZAP active scanning requires a complete http:// or https:// URL."
            )
        payload = self.client.run_active_scan(target)
        alerts = payload.get("alerts", [])
        if not isinstance(alerts, list):
            raise ZAPError("ZAP alerts response must contain an 'alerts' list.")
        return [normalize_zap_alert(alert) for alert in alerts if isinstance(alert, dict)]
