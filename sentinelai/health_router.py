"""sentinelai/health_router.py - Day 56 (Week 8).

Health-gated provider selection.

Day 52's recommend_provider() picks the eligible provider with the highest
health score, but it will still choose a provider that is *below* the healthy
threshold if that happens to be the best of a bad bunch. Day 55 detects this
condition as a "critical" alert. Day 56 closes the automation loop: routing now
*quarantines* providers whose current score is below the healthy threshold so
they are excluded from selection whenever a healthy alternative exists.

All functions are pure Python and offline: no LLM or network calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from sentinelai.routing import recommend_provider
from sentinelai.health_alerts import HEALTHY_THRESHOLD


def quarantine_by_score(
    provider_scores: Dict[str, float],
    healthy_threshold: float = HEALTHY_THRESHOLD,
) -> List[str]:
    """Return the sorted list of providers whose score is below the threshold.

    These are the providers that health-gated routing will avoid.
    """
    return sorted(
        provider
        for provider, score in provider_scores.items()
        if float(score) < healthy_threshold
    )


def health_gate(
    provider_scores: Dict[str, float],
    healthy_threshold: float = HEALTHY_THRESHOLD,
) -> Dict[str, object]:
    """Summarise which providers are healthy vs quarantined.

    Returns a dict with:
      * ``healthy``    - sorted list of providers at/above the threshold
      * ``quarantined`` - sorted list of providers below the threshold
      * ``all_unhealthy`` - True when every provider is below the threshold
      * ``threshold``  - the threshold used
    """
    quarantined = quarantine_by_score(provider_scores, healthy_threshold)
    healthy = sorted(
        provider for provider in provider_scores if provider not in set(quarantined)
    )
    return {
        "healthy": healthy,
        "quarantined": quarantined,
        "all_unhealthy": bool(provider_scores) and not healthy,
        "threshold": healthy_threshold,
    }


@dataclass
class ProviderChoice:
    """The outcome of health-gated provider selection."""

    provider: str
    quarantined: List[str] = field(default_factory=list)
    all_unhealthy: bool = False

    @property
    def fallback_used(self) -> bool:
        """True when the chosen provider was itself below the threshold.

        This happens only when *every* candidate is unhealthy and there is no
        healthy alternative to fall back to.
        """
        return self.all_unhealthy

    def to_dict(self) -> Dict[str, object]:
        return {
            "provider": self.provider,
            "quarantined": list(self.quarantined),
            "all_unhealthy": self.all_unhealthy,
        }


def recommend_healthy_provider(
    routing: str = None,
    is_sensitive: bool = False,
    has_api_key: bool = False,
    provider_scores: Dict[str, float] = None,
    healthy_threshold: float = HEALTHY_THRESHOLD,
) -> ProviderChoice:
    """Choose the best provider while quarantining unhealthy ones.

    Providers below ``healthy_threshold`` are excluded from the candidate pool.
    The Day 52 recommend_provider() logic then selects the winner among the
    remaining (healthy) providers, honouring the routing/sensitivity rules.

    If *every* provider is below the threshold (no healthy alternative), the
    selection falls back to the full candidate pool and ``all_unhealthy`` is
    set so the caller can warn that no healthy provider is available.

    Raises ValueError for an empty ``provider_scores`` (nothing to choose from).
    """
    if not provider_scores:
        raise ValueError("provider_scores must contain at least one provider")

    quarantined = quarantine_by_score(provider_scores, healthy_threshold)
    healthy_pool = {p: s for p, s in provider_scores.items() if p not in set(quarantined)}

    if healthy_pool:
        provider = recommend_provider(
            routing=routing,
            is_sensitive=is_sensitive,
            has_api_key=has_api_key,
            provider_scores=healthy_pool,
        )
        return ProviderChoice(provider=provider, quarantined=quarantined, all_unhealthy=False)

    # No healthy provider: fall back to the least-bad of the full pool.
    provider = recommend_provider(
        routing=routing,
        is_sensitive=is_sensitive,
        has_api_key=has_api_key,
        provider_scores=provider_scores,
    )
    return ProviderChoice(provider=provider, quarantined=quarantined, all_unhealthy=True)
