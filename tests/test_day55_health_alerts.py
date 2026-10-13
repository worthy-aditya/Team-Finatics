"""Day 55 unit tests for provider health alerting.

Offline, pure functions - no LLM or network. Covers alert detection
(critical vs warning), severity sorting, alert summaries, the alerts report,
and --alerts parity across both analyze entry points.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sentinelai.health_alerts import (
    HEALTHY_THRESHOLD,
    HealthAlert,
    build_alerts_report,
    detect_alerts,
    summarize_alerts,
)
from sentinelai.health_history import HealthSnapshot


def _hist(*snaps):
    return [HealthSnapshot(scores, ts) for scores, ts in snaps]


def test_empty_history_no_alerts():
    assert detect_alerts([]) == []


def test_critical_when_below_threshold():
    history = _hist(
        ({"gemini": 50.0}, "t0"),
        ({"gemini": 45.0}, "t1"),
    )
    alerts = detect_alerts(history)
    assert len(alerts) == 1
    assert alerts[0].provider == "gemini"
    assert alerts[0].severity == "critical"
    assert "below the healthy threshold" in alerts[0].reason


def test_warning_when_degrading_but_healthy():
    # Still above the 70 threshold, but fell by >= 5 -> degrading warning.
    history = _hist(
        ({"gemini": 90.0}, "t0"),
        ({"gemini": 75.0}, "t1"),
    )
    alerts = detect_alerts(history)
    assert len(alerts) == 1
    assert alerts[0].severity == "warning"
    assert alerts[0].trend == "degrading"


def test_no_alert_when_healthy_and_stable():
    history = _hist(
        ({"gemini": 90.0}, "t0"),
        ({"gemini": 91.0}, "t1"),
    )
    assert detect_alerts(history) == []


def test_critical_takes_priority_over_degrading_trend():
    # Below threshold AND degrading -> only one (critical) alert, not two.
    history = _hist(
        ({"gemini": 80.0}, "t0"),
        ({"gemini": 60.0}, "t1"),
    )
    alerts = detect_alerts(history)
    assert len(alerts) == 1
    assert alerts[0].severity == "critical"


def test_alerts_sorted_critical_before_warning():
    history = _hist(
        ({"gemini": 90.0, "ollama": 40.0}, "t0"),
        ({"gemini": 78.0, "ollama": 38.0}, "t1"),
    )
    alerts = detect_alerts(history)
    # ollama is critical (below threshold); gemini is warning (degrading).
    severities = [a.severity for a in alerts]
    assert severities == sorted(severities, key=lambda s: {"critical": 0, "warning": 1}[s])
    assert alerts[0].provider == "ollama"
    assert alerts[0].severity == "critical"


def test_summarize_alerts_counts():
    history = _hist(
        ({"gemini": 90.0, "ollama": 40.0, "deepseek": 85.0}, "t0"),
        ({"gemini": 78.0, "ollama": 38.0, "deepseek": 86.0}, "t1"),
    )
    alerts = detect_alerts(history)
    counts = summarize_alerts(alerts)
    assert counts["critical"] >= 1  # ollama
    assert counts["warning"] >= 1   # gemini
    assert counts["critical"] + counts["warning"] == len(alerts)


def test_summarize_alerts_empty():
    assert summarize_alerts([]) == {"critical": 0, "warning": 0}


def test_build_alerts_report_empty():
    assert "No provider health alerts" in build_alerts_report([])


def test_build_alerts_report_renders_alerts():
    history = _hist(
        ({"gemini": 50.0}, "t0"),
        ({"gemini": 45.0}, "t1"),
    )
    report = build_alerts_report(detect_alerts(history))
    assert "CRITICAL" in report
    assert "gemini" in report
    assert "alerts" in report


def test_healthy_threshold_constant():
    assert HEALTHY_THRESHOLD == 70.0


def test_health_alert_to_dict():
    alert = HealthAlert("gemini", "critical", "too low", 50.0, "degrading")
    d = alert.to_dict()
    assert d["provider"] == "gemini"
    assert d["severity"] == "critical"
    assert d["score"] == 50.0


def test_alerts_flag_on_both_analyze_entry_points():
    # Day 4/55 sync: --alerts must exist on both analyze entry points.
    from commands.analyze import analyze as analyze_root
    from sentinelai.cli import analyze as analyze_pkg

    root_opts = {o for p in analyze_root.params for o in p.opts}
    pkg_opts = {o for p in analyze_pkg.params for o in p.opts}
    assert "--alerts" in root_opts, "root analyze missing --alerts"
    assert "--alerts" in pkg_opts, "sentinelai/cli.py analyze missing --alerts"


def _main() -> None:
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  PASS  {fn.__name__}")
    print(f"ALL {len(fns)} day55 health-alerts TESTS PASSED (offline, pure functions)")


if __name__ == "__main__":
    _main()
