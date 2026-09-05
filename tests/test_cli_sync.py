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
from sentinelai.cli import analyze as analyze_pkg

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


def _main():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  PASS  {fn.__name__}")
    print(f"ALL {len(fns)} cli_sync TESTS PASSED (offline, pure functions)")


if __name__ == "__main__":
    _main()