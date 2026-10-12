"""Day 54 unit tests for provider health history and trend tracking.

Offline, pure functions - no LLM or network. Covers snapshot recording,
JSON persistence/loading, trend classification (improving/degrading/stable/
unknown), the history report, the dashboard's optional Trend column, and
--health-history parity across both analyze entry points.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import click

from sentinelai.health_history import (
    DEFAULT_HISTORY_PATH,
    TREND_THRESHOLD,
    build_history_report,
    compute_trend,
    load_history,
    provider_series,
    record_snapshot,
    summarize_trends,
    HealthSnapshot,
)
from sentinelai.dashboard import build_dashboard


def test_record_snapshot_returns_snapshot():
    snap = record_snapshot({"gemini": 80.0, "ollama": 78.0})
    assert isinstance(snap, HealthSnapshot)
    assert snap.scores == {"gemini": 80.0, "ollama": 78.0}
    assert snap.timestamp  # auto-filled


def test_record_snapshot_persists_and_loads(tmp_path):
    path = tmp_path / "hist.json"
    record_snapshot({"gemini": 80.0}, path=str(path), timestamp="2026-10-12T00:00:00+00:00")
    record_snapshot({"gemini": 70.0}, path=str(path), timestamp="2026-10-12T01:00:00+00:00")
    history = load_history(str(path))
    assert len(history) == 2
    assert history[0].scores == {"gemini": 80.0}
    assert history[1].scores == {"gemini": 70.0}
    assert history[0].timestamp == "2026-10-12T00:00:00+00:00"


def test_load_history_missing_file_returns_empty(tmp_path):
    assert load_history(str(tmp_path / "nope.json")) == []


def test_load_history_corrupt_file_returns_empty(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{ this is not valid json", encoding="utf-8")
    assert load_history(str(path)) == []


def test_provider_series_skips_missing():
    history = [
        HealthSnapshot({"gemini": 80.0}, "t0"),
        HealthSnapshot({"ollama": 50.0}, "t1"),
        HealthSnapshot({"gemini": 85.0}, "t2"),
    ]
    assert provider_series(history, "gemini") == [80.0, 85.0]
    assert provider_series(history, "ollama") == [50.0]
    assert provider_series(history, "deepseek") == []


def test_compute_trend_unknown_with_single_point():
    assert compute_trend([HealthSnapshot({"gemini": 80.0}, "t0")], "gemini") == "unknown"


def test_compute_trend_degrading():
    history = [
        HealthSnapshot({"gemini": 90.0}, "t0"),
        HealthSnapshot({"gemini": 70.0}, "t1"),
        HealthSnapshot({"gemini": 50.0}, "t2"),
    ]
    assert compute_trend(history, "gemini") == "degrading"


def test_compute_trend_improving():
    history = [
        HealthSnapshot({"gemini": 50.0}, "t0"),
        HealthSnapshot({"gemini": 70.0}, "t1"),
        HealthSnapshot({"gemini": 90.0}, "t2"),
    ]
    assert compute_trend(history, "gemini") == "improving"


def test_compute_trend_stable_below_threshold():
    history = [
        HealthSnapshot({"gemini": 80.0}, "t0"),
        HealthSnapshot({"gemini": 81.5}, "t1"),
        HealthSnapshot({"gemini": 83.0}, "t2"),
    ]
    # Total move (3.0) is below the 5.0 threshold -> stable.
    assert compute_trend(history, "gemini") == "stable"


def test_summarize_trends_covers_all_providers():
    history = [
        HealthSnapshot({"gemini": 50.0, "ollama": 90.0}, "t0"),
        HealthSnapshot({"gemini": 90.0, "ollama": 50.0}, "t1"),
    ]
    trends = summarize_trends(history)
    assert trends == {"gemini": "improving", "ollama": "degrading"}


def test_build_history_report_empty():
    assert "No provider health history" in build_history_report([])


def test_build_history_report_renders_trends():
    history = [
        HealthSnapshot({"gemini": 50.0}, "t0"),
        HealthSnapshot({"gemini": 90.0}, "t1"),
    ]
    report = build_history_report(history)
    assert "gemini" in report
    assert "improving" in report


def test_dashboard_without_trends_is_unchanged():
    # Day 54 must not alter the default (no-trends) dashboard output.
    output = build_dashboard()
    assert "Trend" not in output
    assert "Score" in output
    assert "Healthy" in output


def test_dashboard_with_trends_adds_column():
    output = build_dashboard(
        {"gemini": 90.0, "ollama": 78.0, "deepseek": 85.0},
        trends={"gemini": "improving", "ollama": "stable", "deepseek": "degrading"},
    )
    assert "Trend" in output
    assert "improving" in output
    assert "degrading" in output
    assert "stable" in output


def test_health_history_flag_on_both_analyze_entry_points():
    # Day 4/54 sync: --health-history must exist on both analyze entry points.
    from commands.analyze import analyze as analyze_root
    from sentinelai.cli import analyze as analyze_pkg

    root_opts = {o for p in analyze_root.params for o in p.opts}
    pkg_opts = {o for p in analyze_pkg.params for o in p.opts}
    assert "--health-history" in root_opts, "root analyze missing --health-history"
    assert "--health-history" in pkg_opts, "sentinelai/cli.py analyze missing --health-history"


def test_default_history_path_constant():
    assert DEFAULT_HISTORY_PATH.endswith(".json")
    assert TREND_THRESHOLD == 5.0


def _main() -> None:
    import tempfile

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    # Provide a throwaway tmp_path for the two tests that need one.
    tmp = tempfile.mkdtemp()
    for fn in fns:
        params = fn.__code__.co_varnames[: fn.__code__.co_argcount]
        if "tmp_path" in params:
            fn(Path(tmp))
        else:
            fn()
        print(f"  PASS  {fn.__name__}")
    print(f"ALL {len(fns)} day54 health-history TESTS PASSED (offline, pure functions)")


if __name__ == "__main__":
    _main()
