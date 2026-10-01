"""Shared contracts for SentinelAI vulnerability-check plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


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

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the finding while preserving the JSON schema contract."""
        data = asdict(self)
        data["check_type"] = self.check_type.value
        data["param"] = data.pop("parameter")
        data["confirmed"] = self.confirmed
        return data


class VulnerabilityCheck(ABC):
    """Base class for independently runnable passive or active checks."""

    name: str
    check_type: CheckType

    @abstractmethod
    def run(self, target: str, *, active_authorized: bool = False) -> List[Finding]:
        """Run the check and return normalized findings."""
        raise NotImplementedError
