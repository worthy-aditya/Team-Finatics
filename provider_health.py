"""Provider health scoring and recommendation helpers for SentinelAI.

This lightweight module gives the project a simple decision aid for choosing
between the supported providers (Gemini and Ollama) based on availability,
response latency, cost, and privacy characteristics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ProviderHealth:
    """Health snapshot for a single provider."""

    name: str
    availability: float
    latency_ms: float
    cost: float = 0.0
    privacy: str = "local"


def score_provider_health(health: ProviderHealth) -> float:
    """Return a single 0-100 score for a provider.

    Higher availability and lower latency improve the score. Local/private
    providers get a modest privacy bonus. Cost is weighted lightly since this
    project uses mostly free or local options.
    """
    availability_score = max(0.0, min(1.0, health.availability)) * 55
    latency_score = max(0.0, 100.0 - min(health.latency_ms, 10000) / 100.0)
    cost_score = max(0.0, 100.0 - health.cost * 12.5)
    privacy_bonus = 10 if health.privacy == "local" else 0
    final_score = availability_score + (latency_score * 0.35) + (cost_score * 0.15) + privacy_bonus
    return round(max(0.0, min(100.0, final_score)), 2)


def recommend_provider_for_task(
    task_type: str,
    is_sensitive: bool = False,
    has_api_key: bool = False,
    provider_scores: Optional[Dict[str, float]] = None,
) -> List[Dict[str, float | str]]:
    """Return a ranked provider recommendation list for a given task.

    provider_scores should be keyed by provider name and already represent a
    normalized health score in the 0-100 range. If omitted, a minimal default
    set is used.
    """
    if provider_scores is None:
        provider_scores = {
            "gemini": 80.0,
            "ollama": 78.0,
        }

    ranked = []
    for provider, score in provider_scores.items():
        adjusted = float(score)
        provider_name = str(provider).lower()

        if is_sensitive and provider_name == "gemini":
            adjusted -= 15
        if not is_sensitive and provider_name == "ollama":
            adjusted += 5
        if task_type == "private-analysis" and provider_name == "ollama":
            adjusted += 10
        if task_type == "summarization" and provider_name == "gemini" and has_api_key:
            adjusted += 10
        if task_type == "private-analysis" and provider_name == "gemini" and not has_api_key:
            adjusted -= 10

        ranked.append({"provider": provider_name, "score": round(max(0.0, min(100.0, adjusted)), 2)})

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked


if __name__ == "__main__":
    sample = ProviderHealth(name="gemini", availability=0.95, latency_ms=1200, cost=1.5, privacy="cloud")
    print(f"Gemini score: {score_provider_health(sample)}")
    print(recommend_provider_for_task("private-analysis", is_sensitive=True, has_api_key=True))
