"""Day 56 unit tests for health-gated provider selection.

Offline, pure functions - no LLM or network. Covers quarantine detection,
the health gate summary, and health-gated provider selection (quarantining
unhealthy providers, honouring routing, and the all-unhealthy fallback).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest

from sentinelai.health_router import (
    ProviderChoice,
    health_gate,
    quarantine_by_score,
    recommend_healthy_provider,
)
from sentinelai.health_alerts import HEALTHY_THRESHOLD


def test_quarantine_by_score_flags_below_threshold():
    scores = {"gemini": 90.0, "ollama": 45.0, "deepseek": 70.0}
    # deepseek at exactly 70.0 is healthy (>= threshold); ollama is quarantined.
    assert quarantine_by_score(scores) == ["ollama"]


def test_quarantine_by_score_empty_when_all_healthy():
    assert quarantine_by_score({"gemini": 90.0, "ollama": 80.0}) == []


def test_quarantine_custom_threshold():
    scores = {"gemini": 90.0, "ollama": 80.0}
    assert quarantine_by_score(scores, healthy_threshold=85.0) == ["ollama"]


def test_health_gate_partitions_providers():
    gate = health_gate({"gemini": 90.0, "ollama": 45.0, "deepseek": 70.0})
    assert gate["healthy"] == ["deepseek", "gemini"]
    assert gate["quarantined"] == ["ollama"]
    assert gate["all_unhealthy"] is False
    assert gate["threshold"] == HEALTHY_THRESHOLD


def test_health_gate_all_unhealthy():
    gate = health_gate({"gemini": 40.0, "ollama": 30.0})
    assert gate["all_unhealthy"] is True
    assert gate["healthy"] == []


def test_recommend_healthy_avoids_quarantined_provider():
    # ollama has the higher raw score but is below threshold -> must be skipped.
    scores = {"gemini": 75.0, "ollama": 69.0}
    choice = recommend_healthy_provider(provider_scores=scores)
    assert choice.provider == "gemini"
    assert choice.quarantined == ["ollama"]
    assert choice.all_unhealthy is False
    assert choice.fallback_used is False


def test_recommend_healthy_picks_best_healthy():
    scores = {"gemini": 90.0, "ollama": 80.0, "deepseek": 50.0}
    choice = recommend_healthy_provider(provider_scores=scores)
    assert choice.provider == "gemini"
    assert choice.quarantined == ["deepseek"]


def test_recommend_healthy_all_unhealthy_fallback():
    scores = {"gemini": 40.0, "ollama": 55.0}
    choice = recommend_healthy_provider(provider_scores=scores)
    # No healthy provider: falls back to the least-bad of the full pool.
    assert choice.all_unhealthy is True
    assert choice.fallback_used is True
    assert choice.provider in ("gemini", "ollama")
    assert sorted(choice.quarantined) == ["gemini", "ollama"]


def test_recommend_healthy_honours_routing_policy():
    # report policy excludes ollama; private policy excludes gemini.
    scores = {"gemini": 90.0, "ollama": 85.0, "deepseek": 80.0}
    private = recommend_healthy_provider(routing="private", is_sensitive=True, provider_scores=scores)
    assert private.provider != "gemini"  # cloud provider discouraged for private
    report = recommend_healthy_provider(routing="report", provider_scores=scores)
    assert report.provider != "ollama"   # ollama excluded for report policy


def test_recommend_healthy_empty_scores_raises():
    with pytest.raises(ValueError):
        recommend_healthy_provider(provider_scores={})


def test_provider_choice_to_dict():
    choice = ProviderChoice(provider="gemini", quarantined=["ollama"], all_unhealthy=False)
    d = choice.to_dict()
    assert d["provider"] == "gemini"
    assert d["quarantined"] == ["ollama"]
    assert d["all_unhealthy"] is False


def test_healthy_threshold_reexported():
    assert HEALTHY_THRESHOLD == 70.0


def _main() -> None:
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  PASS  {fn.__name__}")
    print(f"ALL {len(fns)} day56 health-router TESTS PASSED (offline, pure functions)")


if __name__ == "__main__":
    _main()
