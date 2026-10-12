"""sentinelai/routing.py - Day 52 (Week 8).

Provider routing helpers extended to use Day 51 health scoring.

  * route_provider(): maps --routing report|private to a provider, with an
    explicit --llm winning over routing.
    - report  -> gemini (rich, analyst-facing - Day 20 recommendation)
    - private -> ollama (data stays on the host - zero cloud egress)
  * recommend_provider(): health-aware routing. When provider health scores
    (from provider_health.py) are supplied, they are ranked and the top
    provider is returned for the task, subject to sensitivity constraints.
  * is_raw_log_export(): detects .csv/.evtx inputs.
  * load_event_input(): turns a raw export into analysis-ready schema JSON
    (via sentinelai.log_parser) and passes already-structured JSON through.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure the project root is on sys.path when this module is imported
# directly (e.g. from tests or a standalone script), so the top-level
# provider_health.py can be imported.
_ROOT_PATH = str(Path(__file__).resolve().parent.parent)
if _ROOT_PATH not in sys.path:
    sys.path.insert(0, _ROOT_PATH)

from sentinelai.log_parser import parse_logs
from provider_health import recommend_provider_for_task

# Day 20 conclusion: use gemini for analyst-facing report work, ollama when the
# log data must not leave the host.
ROUTING_PROVIDER: Dict[str, str] = {
    "report": "gemini",
    "private": "ollama",
}

DEFAULT_PROVIDER = "gemini"  # backward-compatible CLI default

RAW_LOG_SUFFIXES = (".csv", ".evtx")


def route_provider(llm_name: Optional[str] = None, routing: Optional[str] = None) -> str:
    """Resolve the effective provider name.

    Priority: explicit ``llm_name`` > ``routing`` policy > DEFAULT_PROVIDER.
    ``routing`` is validated against ROUTING_PROVIDER keys first. This is the
    backward-compatible Day 20-21 routing function; it does not consult health
    scores so that Day 20 behavior is unchanged for callers that rely on it.
    """
    if llm_name:
        return llm_name.strip().lower()
    if routing:
        routing = routing.strip().lower()
        if routing not in ROUTING_PROVIDER:
            raise ValueError(
                f"Unknown routing policy '{routing}'. "
                f"Valid: {', '.join(sorted(ROUTING_PROVIDER))}."
            )
        return ROUTING_PROVIDER[routing]
    return DEFAULT_PROVIDER


def recommend_provider(
    routing: Optional[str] = None,
    is_sensitive: bool = False,
    has_api_key: bool = False,
    provider_scores: Optional[Dict[str, float]] = None,
) -> str:
    """Return the single best provider for a task, combining routing policy
    with Day 51 provider health scoring.

    Behavior:
    - An explicit ``routing`` policy ('report' or 'private') is honoured first
      for sensitivity constraints, but the final choice among eligible
      providers is the one with the highest health score.
    - If no routing policy is given, the provider with the highest score
      wins unconditionally.

    Returns the provider name (e.g. 'gemini' or 'ollama') chosen for analysis.
    """
    # Validate any routing policy before using it.
    if routing is not None and routing.strip().lower() not in ROUTING_PROVIDER:
        raise ValueError(
            f"Unknown routing policy '{routing}'. Valid: {', '.join(sorted(ROUTING_PROVIDER))}."
        )

    # Fall back to a minimal health snapshot when none supplied.
    if provider_scores is None:
        provider_scores = {"gemini": 80.0, "ollama": 78.0}

    # When a routing policy is set, only eligible providers may be chosen.
    if routing is not None:
        policy = routing.strip().lower()
        eligible: List[str] = []
        for provider, score in provider_scores.items():
            if policy == "report" and provider == "ollama":
                continue  # privacy-sensitive cloud provider not allowed for reports
            if policy == "private" and provider == "gemini":
                continue  # cloud provider discouraged for private data
            eligible.append(provider)
        if not eligible:
            # No provider satisfies this policy; fall back to the overall best.
            eligible = list(provider_scores.keys())
        return _select_best_provider(eligible, provider_scores, is_sensitive, has_api_key)

    # No routing policy: pick the provider with the single highest health score.
    return _select_best_provider(list(provider_scores.keys()), provider_scores, is_sensitive, has_api_key)


def _select_best_provider(
    eligible: List[str],
    provider_scores: Dict[str, float],
    is_sensitive: bool,
    has_api_key: bool,
) -> str:
    """Rank eligible providers and return the top one.

    Applies sensitivity adjustments consistent with provider_health.py:
    - Gemini (cloud) is penalised for sensitive data (-15)
    - Ollama (local) is preferred for non-sensitive data (+5)
    - Reports with an API key favour Gemini (+10)
    Returns the provider name with the highest adjusted score.
    """
    ranked = []
    for provider in eligible:
        score = float(provider_scores[provider])
        adjusted = score
        # Day 51 sensitivity rules (consistent with provider_health.py)
        if is_sensitive and provider == "gemini":
            adjusted -= 15  # cloud provider penalised for sensitive data
        if not is_sensitive and provider == "ollama":
            adjusted += 5  # local provider preferred for non-sensitive data
        # Reports with API key: gemini gets a bonus (rich cloud model)
        if not is_sensitive and provider == "gemini" and has_api_key:
            adjusted += 10
        ranked.append((provider, round(max(0.0, min(100.0, adjusted)), 2)))
    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked[0][0]


def is_raw_log_export(path: str) -> bool:
    """True when the input file is a raw CSV/EVTX event-log export."""
    return Path(path).suffix.lower() in RAW_LOG_SUFFIXES


def load_event_input(input_file: str) -> Dict[str, Any]:
    """Load event analysis input, auto-parsing raw exports.

    For .csv/.evtx inputs this runs the real parser and returns the structured
    schema dict directly; for .json inputs it is a passthrough.
    """
    if is_raw_log_export(input_file):
        return parse_logs(input_file)
    from sentinelai.prompt_engine import load_event_log_data
    return load_event_log_data(input_file)


def auto_parse_to_file(input_file: str) -> Tuple[str, int]:
    """Parse a raw export to a temporary JSON file; returns (json_path, count).

    Used so the rest of the pipeline (analyze_event_log_file) can consume the
    same file-shaped interface it already understands - no engine changes.
    """
    data = parse_logs(input_file)
    tmp = Path(tempfile.gettempdir()) / f"sentinelai_auto_{abs(hash(Path(input_file))) % 10**8}.json"
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(tmp), int(data["count"])


# Day 53: central registry of supported providers and their metadata.
# This is the single source of truth for which providers exist and how to
# present them (used by the routing helpers below and the health dashboard).
PROVIDER_REGISTRY: Dict[str, Dict[str, Any]] = {
    "gemini": {
        "name": "Gemini",
        "type": "cloud",
        "api_key_required": True,
        "default_model": "gemini-3.6-flash",
        "note": "Cloud LLM; rich analyst-facing reports (Day 20 default).",
    },
    "ollama": {
        "name": "Ollama",
        "type": "local",
        "api_key_required": False,
        "default_model": "llama3.2",
        "note": "Local LLM; keeps sensitive data on-host (zero cloud egress).",
    },
    "deepseek": {
        "name": "DeepSeek",
        "type": "cloud",
        "api_key_required": True,
        "default_model": "deepseek-chat",
        "note": "Cost-effective cloud LLM alternative for bulk analysis.",
    },
}


# Day 53 additions
def provider_is_healthy(provider_name: str, provider_scores: Dict[str, float], threshold: float = 70.0) -> bool:
    """Check if a provider's health score meets the healthy threshold.

    Args:
        provider_name: Name of the provider to check.
        provider_scores: Dict of provider_name -> health_score.
        threshold: Minimum health score to be considered healthy (default 70).

    Returns:
        True if the provider exists and its score >= threshold.
    """
    score = float(provider_scores.get(provider_name, 0.0))
    return score >= threshold


def get_all_providers() -> List[str]:
    """Return a list of all registered provider names (lowercase).

    Returns:
        List of provider names from the provider registry.
    """
    return list(PROVIDER_REGISTRY.keys())


def get_provider_registry() -> Dict[str, Dict[str, Any]]:
    """Return the full provider registry with metadata.

    Each entry maps provider name -> metadata dict with keys:
        name, type, api_key_required, default_model, note

    Returns:
        Dict of provider metadata.
    """
    return {k: dict(v) for k, v in PROVIDER_REGISTRY.items()}


