"""Day 22 unit tests for sentinelai.event_bridge (offline, no LLM / network).

Covers: the sample ("fake scenario") collector, the native-event -> harness
schema adapter, schema-file writing, and the EventFilter-based summary that
reuses Affan's event_logs.py. Runs as a plain script or under pytest.
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sentinelai.event_bridge import (
    collect_events,
    events_to_schema_file,
    native_events_to_schema,
    summarize,
)


def test_collect_sample_returns_native_events():
    events, source, host = collect_events(use_sample=True)
    assert source == "sample"
    assert host  # host name present
    assert len(events) >= 3
    # Native shape (Affan's event_logs.py contract), not yet the harness schema.
    first = events[0]
    for key in ("log", "event_id", "event_type", "source", "computer",
                "timestamp", "message"):
        assert key in first


def test_collect_sample_event_id_filter():
    events, _src, _host = collect_events(use_sample=True, event_ids=[4624])
    assert all(e["event_id"] == 4624 for e in events)
    seen = {e["event_id"] for e in events}
    assert seen == {4624}


def test_native_to_schema_maps_fields():
    events, _src, host = collect_events(use_sample=True)
    data = native_events_to_schema(events, host=host)
    assert data["source"] == "Windows Security Event Log"
    assert data["host"] == host
    assert data["count"] == len(events) == len(data["events"])

    ev = data["events"][0]
    for key in ("event_id", "timestamp", "level", "channel", "account",
                "domain", "logon_type", "logon_type_name", "source_ip",
                "source_host", "message", "count"):
        assert key in ev

    # DOMAIN\\user is split into account + domain.
    assert ev["account"] == "Administrator"
    assert ev["domain"] == "DOMAIN"
    # Logon type 2 -> Interactive.
    assert ev["logon_type"] == 2
    assert ev["logon_type_name"] == "Interactive"
    # event_type "Information" -> level "information".
    assert ev["level"] == "information"


def test_events_to_schema_file():
    events, _src, host = collect_events(use_sample=True)
    with tempfile.TemporaryDirectory() as td:
        out = str(Path(td) / "events.json")
        n = events_to_schema_file(events, host, out)
        assert n == len(events)
        loaded = json.loads(Path(out).read_text(encoding="utf-8"))
        assert loaded["count"] == len(events)
        assert loaded["events"][0]["event_id"] == events[0]["event_id"]


def test_summarize_uses_affan_eventfilter():
    events, _src, _host = collect_events(use_sample=True)
    analysis = summarize(events)
    assert "threat_level" in analysis
    assert "alerts" in analysis
    assert "recommendations" in analysis


def _main():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  PASS  {fn.__name__}")
    print(f"ALL {len(fns)} event_bridge TESTS PASSED (offline, pure functions)")


if __name__ == "__main__":
    _main()