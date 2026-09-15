"""Data structures for active dynamic-scan findings."""

from dataclasses import dataclass, field
from typing import List, Optional


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
class ActiveScanReportData:
    target: str
    timestamp: str
    authorization_status: str
    active_findings: List[ActiveFinding] = field(default_factory=list)