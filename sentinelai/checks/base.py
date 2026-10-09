"""Shared contracts for SentinelAI vulnerability-check plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


RISK_SCORES = {
    "critical": 80,
    "high": 65,
    "medium": 45,
    "low": 25,
    "informational": 10,
    "info": 10,
}
CONFIDENCE_BONUS = {
    "high": 10,
    "medium": 6,
    "low": 2,
    "unknown": 0,
}


class CheckType(str, Enum):
    """Whether a check observes traffic or sends test requests."""

    PASSIVE = "passive"
    ACTIVE = "active"


@dataclass
class Finding:
    """Normalized finding exchanged by checks, orchestration, and reports."""

    name: str
    risk: str
    confidence: str
    check_type: CheckType
    source: str
    description: str = ""
    url: str = ""
    method: str = ""
    parameter: str = ""
    evidence: str = ""
    attack: str = ""
    plugin_id: Optional[int] = None
    cwe_id: Optional[int] = None
    solution: str = ""
    reference: str = ""
    tags: Dict[str, Any] = field(default_factory=dict)
    owasp: Optional[Dict[str, Any]] = None
    mitre: Optional[Dict[str, Any]] = None

    @property
    def confirmed(self) -> bool:
        """Active findings are confirmed observations, not passive signals."""
        return self.check_type is CheckType.ACTIVE

    @property
    def risk_score(self) -> int:
        """Return a deterministic 0-100 score with confirmation weighting.

        The confirmation bonus is deliberately separate from severity: active
        evidence increases priority, but does not change the scanner-reported
        risk label or pretend to prove business impact.
        """
        severity = RISK_SCORES.get(self.risk.strip().lower(), 10)
        confidence = CONFIDENCE_BONUS.get(self.confidence.strip().lower(), 0)
        confirmation = 20 if self.confirmed else 0
        return min(100, severity + confidence + confirmation)

    @property
    def risk_posture(self) -> str:
        """Describe whether the finding is confirmed or only potential."""
        return "confirmed" if self.confirmed else "potential"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the finding while preserving the JSON schema contract."""
        data = asdict(self)
        data["check_type"] = self.check_type.value
        data["param"] = data.pop("parameter")
        data["confirmed"] = self.confirmed
        data["risk_posture"] = self.risk_posture
        data["risk_score"] = self.risk_score
        return data


class VulnerabilityCheck(ABC):
    """Base class for independently runnable passive or active checks."""

    name: str
    check_type: CheckType

    @abstractmethod
    def run(self, target: str, *, active_authorized: bool = False) -> List[Finding]:
        """Run the check and return normalized findings."""
        raise NotImplementedError
