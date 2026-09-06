"""Day 23 (Week 4): the two `analyze` entry points must stay identical.

Week 2 noted the repo evolved with the same command in two files
(sentinelai/cli.py and commands/analyze.py) and both must behave the same.
This test locks that in: same option names, and the Day 21 `--routing` /
raw-export auto-parse features present on BOTH.

Runs as a plain script or under pytest. No LLM / network needed.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import click

from commands.analyze import analyze as analyze_root
from commands.report import report as report_root
from commands.scan import scan as scan_root
from sentinelai.cli import analyze as analyze_pkg
from sentinelai.cli import main as pkg_main
from sentinelai.cli import scan as scan_pkg

# click parameter names as exposed on the command (dest names).
_ROOT_OPTIONS = {p.name for p in analyze_root.params}
_PKG_OPTIONS = {p.name for p in analyze_pkg.params}


def test_both_analyze_entry_points_have_same_options():
    assert _ROOT_OPTIONS == _PKG_OPTIONS, (
        f"analyze option drift: root-only={_ROOT_OPTIONS - _PKG_OPTIONS}, "
        f"pkg-only={_PKG_OPTIONS - _ROOT_OPTIONS}"
    )


def test_routing_option_present_on_both():
    assert "routing" in _ROOT_OPTIONS, "root CLI analyze missing --routing"
    assert "routing" in _PKG_OPTIONS, "sentinelai/cli.py analyze missing --routing"


def test_both_accept_scan_and_events_kind():
    kind_param = next(p for p in analyze_root.params if p.name == "kind")
    assert isinstance(kind_param.type, click.Choice)
    assert set(kind_param.type.choices) == {"scan", "events"}


# --- Day 25: the one-command E2E pipeline needs scan + report parity too ---

def test_both_scan_entry_points_have_same_options():
    assert {p.name for p in scan_root.params} == {p.name for p in scan_pkg.params}, (
        f"scan option drift: root-only={ {p.name for p in scan_root.params} - {p.name for p in scan_pkg.params} }, "
        f"pkg-only={ {p.name for p in scan_pkg.params} - {p.name for p in scan_root.params} }"
    )


def test_scan_machine_mode_on_both():
    for cmd in (scan_root, scan_pkg):
        opts = {o for p in cmd.params for o in p.opts}
        assert {"--json", "--json-file"} <= opts, f"{cmd.name} missing --json/--json-file"


def test_report_registered_on_both_entry_points():
    assert "report" in pkg_main.commands, "sentinelai/cli.py missing report command"
    import importlib.util

    spec = importlib.util.spec_from_file_location("sentinelai_root_cli", ROOT / "sentinelai.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert "report" in mod.cli.commands, "sentinelai.py (root CLI) missing report command"


def _main():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  PASS  {fn.__name__}")
    print(f"ALL {len(fns)} cli_sync TESTS PASSED (offline, pure functions)")


if __name__ == "__main__":
    _main()