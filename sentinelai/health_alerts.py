"""sentinelai/health_alerts.py - Day 55 (Week 8).

Provider health alerting.

Turns recorded health history (Day 54) into actionable alerts. An alert is
raised when a provider is either:

  * **critical** - its latest score is below the healthy threshold, or
  * **warning**  - it is still healthy but actively *degrading* (falling fast
    enough to risk crossing the threshold soon).

This closes the loop from observability (Day 54 trends) to alerting: an
operator no longer has to read the dashboard to notice a provider slipping.

All functions are pure Python and offline: no LLM or network calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from sentinelai.health_history import (
    DEFAULT_WINDOW,
    TREND_THRESHOLD,
    HealthSnapshot,
    provider_series,
    summarize_trends,
)

# A provider whose latest score is below this value is "critical". Kept in
# sync with the healthy threshold used by sentinelai.routing.provider_is_healthy.
HEALTHY_THRESHOLD = 70.0

# Severity labels, ordered most-severe first (used when sorting alerts).
SEVERITY_ORDER = {"critical": 0, "warning": 1}


@dataclass
class HealthAlert:
    """A single actionable alert about a provider's health."""

    provider: str
    severity: str  # "critical" | "warning"
    reason: str
    score: float
    trend: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "provider": self.provider,
            "severity": self.severity,
            "reason": self.reason,
            "score": self.score,
            "trend": self.trend,
        }


def detect_alerts(
    history: List[HealthSnapshot],
    healthy_threshold: float = HEALTHY_THRESHOLD,
    window: int = DEFAULT_WINDOW,
    trend_threshold: float = TREND_THRESHOLD,
) -> List[HealthAlert]:
    """Return actionable alerts derived from recorded health history.

    * ``critical`` - the provider's latest score is below ``healthy_threshold``.
    * ``warning``  - the provider is healthy but its trend is ``degrading``.

    Alerts are sorted most-severe first, then alphabetically by provider. An
    empty history (or history with no alertable providers) yields ``[]``.
    """
    if not history:
        return []

    trends = summarize_trends(history, window=window, threshold=trend_threshold)
    alerts: List[HealthAlert] = []

    for provider in sorted(trends):
        series = provider_series(history, provider)
        latest = series[-1] if series else 0.0
        trend = trends[provider]
        recent = series[-window:] if (window and window > 0) else series
        start = recent[0] if recent else latest

        if latest < healthy_threshold:
            alerts.append(
                HealthAlert(
                    provider=provider,
                    severity="critical",
                    reason=(
                        f"score {latest:.1f} is below the healthy "
                        f"threshold {healthy_threshold:.0f}"
                    ),
                    score=latest,
                    trend=trend,
                )
            )
        elif trend == "degrading":
            alerts.append(
                HealthAlert(
                    provider=provider,
                    severity="warning",
                    reason=(
                        f"trend degrading: dropped from {start:.1f} to {latest:.1f}"
                    ),
                    score=latest,
                    trend=trend,
                )
            )

    alerts.sort(key=lambda a: (SEVERITY_ORDER.get(a.severity, 99), a.provider))
    return alerts


def summarize_alerts(alerts: List[HealthAlert]) -> Dict[str, int]:
    """Return counts of alerts by severity, e.g. ``{"critical": 1, "warning": 0}``."""
    counts = {"critical": 0, "warning": 0}
    for alert in alerts:
        if alert.severity in counts:
            counts[alert.severity] += 1
    return counts


def build_alerts_report(alerts: List[HealthAlert]) -> str:
    """Render a human-readable alerts report."""
    if not alerts:
        return "No provider health alerts. All providers healthy and stable."

    counts = summarize_alerts(alerts)
    lines = [
        f"Provider health alerts ({len(alerts)} total: "
        f"{counts['critical']} critical, {counts['warning']} warning):",
        f"{'Severity':<9} {'Provider':<12} {'Score':>6} {'Trend':<10}  Reason",
        "-" * 64,
    ]
    for alert in alerts:
        lines.append(
            f"{alert.severity.upper():<9} {alert.provider:<12} "
            f"{alert.score:>6.1f} {alert.trend:<10}  {alert.reason}"
        )
    return "\n".join(lines)
