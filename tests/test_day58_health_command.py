"""Day 58 unit tests for the `health` command group (Week 9).

Offline - no LLM or network. Exercises the health command group (profiles,
save, show, delete, status) via Click's CliRunner against a throwaway working
directory so the real provider_profiles/ is never touched, and checks that the
command is registered on BOTH CLI entry points.
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import click
from click.testing import CliRunner

from sentinelai.health_command import build_health_command


def _run(args, cwd):
    """Invoke the health group inside an isolated working directory."""
    prev = os.getcwd()
    os.chdir(cwd)
    try:
        return CliRunner().invoke(build_health_command(), args)
    finally:
        os.chdir(prev)


def test_profiles_empty():
    with tempfile.TemporaryDirectory() as d:
        result = _run(["profiles"], d)
        assert result.exit_code == 0
        assert "No provider health profiles" in result.output


def test_save_then_profiles_lists_it():
    with tempfile.TemporaryDirectory() as d:
        r1 = _run(["save", "baseline", "--scores", '{"gemini": 90, "ollama": 80}'], d)
        assert r1.exit_code == 0, r1.output
        r2 = _run(["profiles"], d)
        assert "baseline" in r2.output


def test_save_from_file():
    with tempfile.TemporaryDirectory() as d:
        scores_file = Path(d) / "scores.json"
        scores_file.write_text('{"gemini": 75.0}', encoding="utf-8")
        result = _run(["save", "fromfile", "--scores-file", str(scores_file)], d)
        assert result.exit_code == 0, result.output
        assert "fromfile" in _run(["profiles"], d).output


def test_show_profile():
    with tempfile.TemporaryDirectory() as d:
        _run(["save", "demo", "--scores", '{"gemini": 66.5}'], d)
        result = _run(["show", "demo"], d)
        assert result.exit_code == 0, result.output
        assert "gemini" in result.output
        assert "66.5" in result.output


def test_show_missing_profile_errors():
    with tempfile.TemporaryDirectory() as d:
        result = _run(["show", "ghost"], d)
        assert result.exit_code != 0


def test_delete_profile():
    with tempfile.TemporaryDirectory() as d:
        _run(["save", "temp", "--scores", '{"gemini": 90.0}'], d)
        result = _run(["delete", "temp"], d)
        assert result.exit_code == 0, result.output
        assert "temp" not in _run(["profiles"], d).output


def test_delete_missing_profile_warns_not_fatal():
    with tempfile.TemporaryDirectory() as d:
        result = _run(["delete", "ghost"], d)
        # Deletes are best-effort: a missing profile is a warning, not a crash.
        assert result.exit_code == 0, result.output


def test_save_requires_scores():
    with tempfile.TemporaryDirectory() as d:
        result = _run(["save", "empty"], d)
        assert result.exit_code != 0


def test_status_renders_dashboard():
    with tempfile.TemporaryDirectory() as d:
        result = _run(["status"], d)
        assert result.exit_code == 0, result.output
        assert "Provider" in result.output
        assert "Score" in result.output


def test_status_with_profile():
    with tempfile.TemporaryDirectory() as d:
        _run(["save", "degraded", "--scores", '{"gemini": 92, "ollama": 55, "deepseek": 80}'], d)
        result = _run(["status", "--profile", "degraded"], d)
        assert result.exit_code == 0, result.output
        # ollama at 55 is below threshold -> LOW in the dashboard.
        assert "LOW" in result.output


def test_status_with_unknown_profile_errors():
    with tempfile.TemporaryDirectory() as d:
        result = _run(["status", "--profile", "ghost"], d)
        assert result.exit_code != 0


def test_health_registered_on_both_entry_points():
    from commands.logs import logs  # noqa: F401  (ensure commands importable)
    from sentinelai.cli import main as pkg_main
    from sentinelai.health_command import build_health_command as factory

    assert "health" in pkg_main.commands, "sentinelai/cli.py main missing health group"

    import importlib.util

    spec = importlib.util.spec_from_file_location("sentinelai_root_cli", ROOT / "sentinelai.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert "health" in mod.cli.commands, "root sentinelai.py cli missing health group"

    # The factory is deterministic (same group name/subcommands).
    group = factory()
    assert isinstance(group, click.Group)
    assert set(group.commands) >= {"profiles", "save", "show", "delete", "status"}


def _main() -> None:
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  PASS  {fn.__name__}")
    print(f"ALL {len(fns)} day58 health-command TESTS PASSED (offline, CliRunner)")


if __name__ == "__main__":
    _main()
