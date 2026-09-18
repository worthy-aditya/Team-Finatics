"""Data structures for active dynamic-scan and authorization findings."""

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, List, Optional, Union


@dataclass
class ActiveFinding:
    id: str
    title: str
    severity: str
    confidence: str
    target_url: str
    description: str
    evidence_request: Optional[str] = None
    evidence_response: Optional[str] = None
    cve_id: Optional[str] = None
    remediation: Optional[str] = None


@dataclass
class AuthorizationRecord:
    target_domain: str
    attestation_user: str
    attestation_timestamp: str
    verification_status: str
    verification_method: str
    token_used: Optional[str] = None


def load_authorization_record(
    audit_log_path: Union[str, Path],
) -> Optional[AuthorizationRecord]:
    """Load the latest valid authorization event from a JSONL audit log."""
    path = Path(audit_log_path)
    if not path.is_file():
        return None

    latest: Optional[dict[str, Any]] = None
    with path.open("r", encoding="utf-8") as audit_log:
        for line in audit_log:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                latest = event

    if latest is None:
        return None

    # Accept either the record itself or an audit event containing it.
    values = latest.get("authorization_record", latest)
    if not isinstance(values, dict):
        return None

    required = (
        "target_domain",
        "attestation_user",
        "attestation_timestamp",
        "verification_status",
        "verification_method",
    )
    if any(key not in values for key in required):
        return None
    return AuthorizationRecord(
        **{key: str(values[key]) for key in required},
        token_used=(str(values["token_used"]) if values.get("token_used") else None),
    )


@dataclass
class ActiveScanReportData:
    target: str
    timestamp: str
    authorization_status: str
    active_findings: List[ActiveFinding] = field(default_factory=list)