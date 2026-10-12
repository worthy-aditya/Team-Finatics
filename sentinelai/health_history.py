"""sentinelai/health_history.py - Day 54 (Week 8).

Provider health history and trend tracking.

Records provider health scores as timestamped snapshots and classifies each
provider's recent trajectory as improving, degrading, or stable. This extends
the Day 53 dashboard (a point-in-time view) with a longitudinal view so an
operator can spot a provider slipping before it crosses the healthy threshold.

All functions are pure Python and offline: no LLM or network calls.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# A provider is only "improving"/"degrading" when its score moves by at least
# this many points across the trend window; smaller moves are "stable".
TREND_THRESHOLD = 5.0

# How many of the most recent snapshots to consider when classifying a trend.
DEFAULT_WINDOW = 3

# Default on-disk location for the JSON snapshot history. Only written when a
# caller explicitly records a snapshot (never as an import side effect).
DEFAULT_HISTORY_PATH = "provider_health_history.json"


@dataclass
class HealthSnapshot:
    """A single timestamped capture of provider health scores."""

    scores: Dict[str, float]
    timestamp: str

    def to_dict(self) -> Dict[str, object]:
        return {"timestamp": self.timestamp, "scores": dict(self.scores)}

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "HealthSnapshot":
        scores = data.get("scores", {})
        if not isinstance(scores, dict):
            scores = {}
        return cls(
            scores={str(k): float(v) for k, v in scores.items()},
            timestamp=str(data.get("timestamp", "")),
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_snapshot(
    scores: Dict[str, float],
    path: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> HealthSnapshot:
    """Create and (when ``path`` is given) persist a health snapshot.

    Returns the snapshot that was created. When ``path`` is provided the
    snapshot is appended to the JSON history file at that path (the file and
    its parent directory are created if missing; it holds a JSON array of
    snapshots).
    """
    snapshot = HealthSnapshot(
        scores={str(k): float(v) for k, v in scores.items()},
        timestamp=timestamp or _now_iso(),
    )
    if path is not None:
        history = load_history(path)
        history.append(snapshot)
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps([s.to_dict() for s in history], indent=2),
            encoding="utf-8",
        )
    return snapshot


def load_history(path: str) -> List[HealthSnapshot]:
    """Load health snapshots from a JSON history file.

    Returns an empty list when the file is missing or unreadable, so callers
    can treat "no history yet" the same as "empty history".
    """
    p = Path(path)
    if not p.exists():
        return []
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError):
        return []
    if not isinstance(raw, list):
        return []
    return [HealthSnapshot.from_dict(item) for item in raw if isinstance(item, dict)]


def provider_series(history: List[HealthSnapshot], provider: str) -> List[float]:
    """Return the ordered list of scores recorded for one provider."""
    series: List[float] = []
    for snap in history:
        if provider in snap.scores:
            series.append(float(snap.scores[provider]))
    return series


def compute_trend(
    history: List[HealthSnapshot],
    provider: str,
    window: int = DEFAULT_WINDOW,
    threshold: float = TREND_THRESHOLD,
) -> str:
    """Classify a provider's recent trajectory.

    Returns one of ``"improving"``, ``"degrading"``, ``"stable"``, or
    ``"unknown"``. ``"unknown"`` is returned when there are fewer than two
    recorded points to judge a direction from. The classification compares the
    first and last score within the most recent ``window`` points against
    ``threshold``.
    """
    series = provider_series(history, provider)
    if len(series) < 2:
        return "unknown"
    recent = series[-window:] if window and window > 0 else series
    delta = recent[-1] - recent[0]
    if delta >= threshold:
        return "improving"
    if delta <= -threshold:
        return "degrading"
    return "stable"


def summarize_trends(
    history: List[HealthSnapshot],
    window: int = DEFAULT_WINDOW,
    threshold: float = TREND_THRESHOLD,
) -> Dict[str, str]:
    """Return ``{provider: trend}`` for every provider seen in the history."""
    providers = set()
    for snap in history:
        providers.update(snap.scores.keys())
    return {
        provider: compute_trend(history, provider, window=window, threshold=threshold)
        for provider in sorted(providers)
    }


def build_history_report(
    history: List[HealthSnapshot],
    window: int = DEFAULT_WINDOW,
    threshold: float = TREND_THRESHOLD,
) -> str:
    """Render a text report of provider score trends from history."""
    if not history:
        return "No provider health history recorded yet."
    trends = summarize_trends(history, window=window, threshold=threshold)
    count = len(history)
    lines = [
        f"Provider health history ({count} snapshot{'s' if count != 1 else ''}):",
        f"{'Provider':<12} {'Trend':<10} {'Latest':>7} {'Points':>6}",
        "-" * 40,
    ]
    for provider, trend in trends.items():
        series = provider_series(history, provider)
        latest = series[-1] if series else 0.0
        lines.append(f"{provider:<12} {trend:<10} {latest:>7.1f} {len(series):>6}")
    return "\n".join(lines)
