"""Day 21 unit tests for sentinelai.routing (offline, pure functions).

Covers provider routing (explicit --llm > --routing > default), raw-export
auto-detection, and loading event input (auto-parse CSV - schema correct).
No LLM or network is required.
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sentinelai.routing import (
    ROUTING_PROVIDER,
    DEFAULT_PROVIDER,
    route_provider,
    is_raw_log_export,
    load_event_input,
    auto_parse_to_file,
)


CRITICAL_IDS = {1102, 4624, 4625, 4648, 4663, 4672, 4720, 5145}


def _mini_csv() -> str:
    return (
        "Date,Event ID,Level,Message,Account,IP Address,Logon Type,Domain\n"
        "2026-08-28 08:02:11,4625,Warning,An account failed to log on.,svc_web,10.0.5.23,3,CORP\n"
        "2026-08-28 08:41:09,1102,Critical,The audit log was cleared.,SYSTEM,,,CORP\n"
    )


def test_route_provider_priority():
    # explicit --llm wins over routing
    assert route_provider("ollama", "report") == "ollama"
    assert route_provider("gemini", "private") == "gemini"
    # routing maps to the Day 20 recommendation
    assert route_provider(routing="report") == "gemini"
    assert route_provider(routing="private") == "ollama"
    # default stays gemini (backward compatible)
    assert route_provider() == DEFAULT_PROVIDER == "gemini"


def test_route_provider_invalid_policy():
    try:
        route_provider(routing="bogus")
    except ValueError:
        return
    raise AssertionError("invalid routing policy should raise ValueError")


def test_is_raw_log_export():
    assert is_raw_log_export("x.CSV") is True   # case-insensitive
    assert is_raw_log_export("x.evtx") is True
    assert is_raw_log_export("x.json") is False
    assert is_raw_log_export("x.txt") is False


def test_load_event_input_auto_parse():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "events.csv"
        p.write_text(_mini_csv(), encoding="utf-8")
        d = load_event_input(str(p))
        assert d["count"] == 2
        assert {int(e["event_id"]) for e in d["events"]} == {4625, 1102}
        assert d["host"] == "UNKNOWN-HOST"


def test_auto_parse_to_file(tmp_write=True):
    import tempfile as _t
    with _t.TemporaryDirectory() as td:
        p = Path(td) / "events.csv"
        p.write_text(_mini_csv(), encoding="utf-8")
        jpath, n = auto_parse_to_file(str(p))
        assert n == 2
        data = json.loads(Path(jpath).read_text(encoding="utf-8"))
        assert data["count"] == 2
        ids = {int(e["event_id"]) for e in data["events"]}
        assert ids == {4625, 1102}


def _main():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  PASS  {fn.__name__}")
    print(f"ALL {len(fns)} routing TESTS PASSED (offline, pure functions)")


if __name__ == "__main__":
    _main()