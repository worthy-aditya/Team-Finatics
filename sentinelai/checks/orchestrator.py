"""Orchestrate independent SentinelAI vulnerability checks."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from sentinelai.checks.base import Finding, VulnerabilityCheck


def run_all_checks(
    target: str,
    checks: Iterable[VulnerabilityCheck],
    *,
    active_authorized: bool = False,
) -> Dict[str, Any]:
    """Run checks independently and return findings plus per-check errors.

    A failed optional check does not erase findings from checks that completed.
    Active checks receive the authorization flag and must enforce it themselves.
    """
    findings: List[Finding] = []
    errors: List[Dict[str, str]] = []
    executed: List[str] = []

    for check in checks:
        executed.append(check.name)
        try:
            findings.extend(
                check.run(target, active_authorized=active_authorized)
            )
        except Exception as exc:  # noqa: BLE001 - isolate independent boxes
            errors.append({"check": check.name, "error": str(exc)})

    return {
        "target": target,
        "findings": [finding.to_dict() for finding in findings],
        "errors": errors,
        "checks": executed,
        "count": len(findings),
    }
