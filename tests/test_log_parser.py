"""Day 19 unit tests for sentinelai.log_parser (pure functions, offline).

Covers: schema shape, order-independent column detection, Windows event-ID
metadata enrichment, and message-text fallback extraction when CSV columns
are sparse. No LLM or network is required.

Runs as a plain script (`py tests/test_log_parser.py`) or under pytest.
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sentinelai.log_parser import (
    parse_logs_csv_text,
    parse_logs_to_file,
    _normalize_level,
    LOGON_TYPE_NAMES,
)

# Columns deliberately in a "weird" order to prove header-name auto-detection.
_WEIRD_CSV = (
    "Computer,Message,Event ID,Logon Type,Level,Account,Date,IP Address,Domain,Count,Workstation,Source\n"
    "HOST-DB01,An account failed to log on.,4625,3,Warning,svc_web,2026-08-28 08:02:11,10.0.5.23,CORP,1,WORKSTATION-23,Microsoft-Windows-Security-Auditing\n"
    "DC01,A user account was created.,4720,,Warning,devops,2026-08-28 08:35:22,,CORP,1,WORKSTATION-23,Microsoft-Windows-Security-Auditing\n"
)

# Minimal CSV where account/source_ip/logon_type are ONLY in the message text.
_MINIMAL_CSV = (
    "Date,Event ID,Level,Message\n"
    "2026-08-28 08:14:05,4648,Information,A logon was attempted using explicit credentials. Target Account: devops. Logon Type: 9. Source Network Address: 10.0.5.23\n"
)


def test_schema_top_level_keys():
    d = parse_logs_csv_text(_WEIRD_CSV, host_name="CORP-LOGS")
    assert set(d) >= {"source", "host", "collected_at", "window_start",
                      "window_end", "count", "events"}
    assert d["host"] == "CORP-LOGS"
    assert d["count"] == len(d["events"]) == 2


def test_event_ids_and_fields():
    d = parse_logs_csv_text(_WEIRD_CSV)
    assert [e["event_id"] for e in d["events"]] == [4625, 4720]
    first = d["events"][0]
    assert first["account"] == "svc_web"
    assert first["source_ip"] == "10.0.5.23"
    assert first["logon_type"] == 3
    assert first["logon_type_name"] == "Network"
    assert first["channel"] == "Security"
    second = d["events"][1]            # 4720 had no Logon Type column
    assert second["logon_type"] is None
    assert second["source_ip"] is None


def test_unknown_event_id_passthrough():
    d = parse_logs_csv_text("Date,Event ID,Level,Message\n2026-08-28 09:00:00,9999,Information,Some custom event.\n")
    e = d["events"][0]
    assert e["event_id"] == 9999
    assert e["message"] == "Some custom event."
    assert e["level"] == "information"


def test_fallback_extraction_from_message():
    d = parse_logs_csv_text(_MINIMAL_CSV)
    e = d["events"][0]
    assert e["event_id"] == 4648
    assert e["account"] == "devops"        # pulled from "Target Account:"
    assert e["source_ip"] == "10.0.5.23"   # pulled from message IP
    assert e["logon_type"] == 9
    assert e["logon_type_name"] == "RunAs"


def test_empty_csv_raises():
    try:
        parse_logs_csv_text("Date,Event ID,Level,Message\n")
    except ValueError:
        return
    raise AssertionError("empty CSV should raise ValueError")


def test_parse_logs_to_file():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "in.csv"
        p.write_text("Date,Event ID,Level,Message\n2026-08-28 00:00:00,4625,Warning,Bad logon.\n", encoding="utf-8")
        out = Path(td) / "out.json"
        host, n = parse_logs_to_file(str(p), str(out), host_name="X")
        assert host == "X" and n == 1
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["events"][0]["event_id"] == 4625


def test_normalize_level():
    assert _normalize_level("Warning") == "warning"
    assert _normalize_level("ERROR") == "error"
    assert _normalize_level("Information") == "information"
    assert _normalize_level("3") == "warning"
    assert _normalize_level(None) is None


def test_logon_type_names_complete():
    assert LOGON_TYPE_NAMES[3] == "Network"
    assert LOGON_TYPE_NAMES[9] == "RunAs"


def _main():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  PASS  {fn.__name__}")
    print(f"ALL {len(fns)} log_parser TESTS PASSED (offline, pure functions)")


if __name__ == "__main__":
    _main()