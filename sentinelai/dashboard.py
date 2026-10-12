"""sentinelai/dashboard.py - Day 53 (Week 8).

Health dashboard for CLI: displays all registered providers, their
scores, and eligibility status in a formatted table.
"""


from typing import Any, Dict, List, Optional

from sentinelai.routing import (
    get_all_providers,
    get_provider_registry,
    provider_is_healthy,
)


def _format_score(score: float, total_width: int = 8) -> str:
    """Format a score as a string with aligned columns."""
    return f"{score:>{total_width}.1f}"


def _get_provider_name(provider: str, registry: Dict[str, Dict[str, Any]]) -> str:
    """Get the display name for a provider from the registry."""
    info = registry.get(provider, {})
    return info.get("name", provider)


def build_dashboard(
    provider_scores: Dict[str, float] = None,
    trends: Optional[Dict[str, str]] = None,
) -> str:
    """Build a formatted health dashboard for all providers.

    Args:
        provider_scores: Optional dict of provider_name -> health_score.
            If None, default scores are used.
        trends: Optional dict of provider_name -> trend label (Day 54). When
            provided, an extra "Trend" column is appended to the table. When
            omitted, the output is identical to the Day 53 dashboard.

    Returns:
        Formatted string showing provider health dashboard.
    """
    if provider_scores is None:
        provider_scores = {"gemini": 80.0, "ollama": 78.0, "deepseek": 85.0}

    registry = get_provider_registry()
    providers = get_all_providers()

    show_trends = trends is not None

    # Build table header
    header = f"{'Provider':<16} {'Type':<8} {'Score':>6} {'Healthy':>8}  Status"
    if show_trends:
        header += f"  {'Trend':<10}"
    separator = "-" * len(header)

    lines = [header, separator]

    for provider in providers:
        info = registry.get(provider, {})
        name = _get_provider_name(provider, registry)
        ptype = info.get("type", "unknown")
        score = provider_scores.get(provider, 0.0)
        healthy = provider_is_healthy(provider, provider_scores)
        status = "OK" if healthy else "LOW"

        line = f"{name:<16} {ptype:<8} {_format_score(score):>6} {str(healthy):>8}  {status}"
        if show_trends:
            trend = trends.get(provider, "unknown")
            line += f"  {trend:<10}"
        lines.append(line)

    lines.append(separator)
    total = f"{'Total providers':<16} {'':<8} {'':>6} {'':>8}  {len(providers)}"
    if show_trends:
        total += f"  {'':<10}"
    lines.append(total)

    return "\n".join(lines)


def main() -> None:
    """CLI entry point for the dashboard."""
    print(build_dashboard())


if __name__ == "__main__":
    main()
