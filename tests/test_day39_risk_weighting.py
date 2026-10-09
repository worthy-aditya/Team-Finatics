"""Day 39 tests for confirmed-versus-potential risk weighting."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sentinelai.checks import CheckType, Finding, rank_findings


def make_finding(check_type, name="same alert", risk="High", confidence="Medium"):
    return Finding(
        name=name,
        risk=risk,
        confidence=confidence,
        check_type=check_type,
        source="test",
    )


def test_confirmed_active_score_exceeds_potential_passive_score():
    passive = make_finding(CheckType.PASSIVE)
    active = make_finding(CheckType.ACTIVE)

    assert active.risk_score > passive.risk_score
    assert active.risk_posture == "confirmed"
    assert passive.risk_posture == "potential"


def test_score_is_bounded_and_keeps_reported_risk_label():
    finding = make_finding(CheckType.ACTIVE, risk="Critical", confidence="High")
    data = finding.to_dict()

    assert 0 <= finding.risk_score <= 100
    assert data["risk"] == "Critical"
    assert data["risk_score"] == finding.risk_score
    assert data["confirmed"] is True
    assert data["risk_posture"] == "confirmed"


def test_rank_findings_prioritizes_confirmation_then_score():
    potential_critical = make_finding(
        CheckType.PASSIVE, name="potential critical", risk="Critical", confidence="High"
    )
    confirmed_low = make_finding(
        CheckType.ACTIVE, name="confirmed low", risk="Low", confidence="Low"
    )
    confirmed_high = make_finding(
        CheckType.ACTIVE, name="confirmed high", risk="High", confidence="High"
    )

    ranked = rank_findings([potential_critical, confirmed_low, confirmed_high])

    assert [finding.name for finding in ranked] == [
        "confirmed high",
        "confirmed low",
        "potential critical",
    ]
