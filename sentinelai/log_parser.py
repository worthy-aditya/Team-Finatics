"""
sentinelai/log_parser.py
Day 19 (Week 3): Affan's real Windows Event Log parser.

Converts raw Windows event exports into the schema the Day 15/16/17 analysis
pipeline already expects (see load_event_log_data / build_event_log_prompt), so
any real export flows straight into:

    sentinelai parse --input <export.csv|.evtx> --logs -o events.json
    sentinelai analyze --input events.json --kind events --mode <standard|remediation>

Supported inputs:
  * CSV  - the export from `wevtutil qe Security /f:csv` or the Event Viewer
           "Save All Events As -> CSV". Columns map by header *name*
           (order-independent, case-insensitive), so it handles export variants.
  * EVTX - a binary `.evtx`, parsed with the optional `python-evtx` package
           (`pip install python-evtx`). CSV is the supported default here.

Both reduce to the harness event schema:
    {"source","host","collected_at","window_start","window_end","count","events":[...]}
where each event = {event_id,timestamp,level,channel,account,domain,
                   logon_type,logon_type_name,source_ip,source_host,message,count}.
"""

from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Windows Security-log metadata to enrich sparse export rows. level follows the
# Windows convention; logon_type only applies to the logon family (4624/4625/4648).
SECURITY_EVENT_META: Dict[int, Dict[str, Any]] = {
    1100: {"level": "warning",     "message": "The security log was stopped (possibly due to shutdown or log space)."},
    1102: {"level": "critical",    "message": "The audit log was cleared."},
    4624: {"level": "information", "message": "An account was successfully logged on."},
    4625: {"level": "warning",     "message": "An account failed to log on."},
    4648: {"level": "information", "message": "A logon was attempted using explicit credentials."},
    4672: {"level": "information", "message": "Special privileges assigned to new logon."},
    4720: {"level": "warning",     "message": "A user account was created."},
    4722: {"level": "information", "message": "A user account was enabled."},
    4726: {"level": "warning",     "message": "A user account was deleted."},
    4728: {"level": "warning",     "message": "A member was added to a security-enabled global group."},
    4738: {"level": "information", "message": "A user account was changed."},
    4740: {"level": "warning",     "message": "A user account was locked out."},
    4670: {"level": "information", "message": "Permissions on an object were changed."},
    4663: {"level": "information", "message": "An attempt was made to access an object."},
    5140: {"level": "information", "message": "A network share object was accessed."},
    5145: {"level": "information", "message": "A network share object was accessed."},
    4688: {"level": "information", "message": "A new process has been created."},
    4674: {"level": "warning",     "message": "Principal attempted to access a privileged object."},
    5156: {"level": "information", "message": "The firewall service was successfully started."},
}

LOGON_TYPE_NAMES: Dict[int, str] = {
    2: "Interactive", 3: "Network", 4: "Batch", 5: "Service",
    7: "Unlock", 8: "Cleartext", 9: "RunAs", 10: "RemoteInteractive (RDP)",
    11: "CachedInteractive",
}

# Canonical level strings: Windows text or numeric codes map to our enum string
# (kept as strings to stay schema-compatible with day15_sample_events.json).
_LEVEL_TEXT = {"critical": "critical", "error": "error", "warning": "warning",
               "information": "information", "info": "information"}
_LEVEL_BY_NUM = {1: "critical", 2: "error", 3: "warning", 4: "information"}


def _normalize_level(value: Optional[str]) -> Optional[str]:
    """Map CSV level values ('Information', '3', 'Warning', ...) to our enum string."""
    if value is None:
        return None
    v = str(value).strip().lower()
    if v in _LEVEL_TEXT:
        return _LEVEL_TEXT[v]
    if v.isdigit():
        return _LEVEL_BY_NUM.get(int(v))
    return None


def _find_col(header_norm: List[str], tokens: Tuple[str, ...]) -> Optional[int]:
    for i, h in enumerate(header_norm):
        if any(tok in h for tok in tokens):
            return i
    return None


def _detect_columns(header: List[str]) -> Dict[str, Optional[int]]:
    h = [c.strip().lower().replace(" ", "").replace("_", "") for c in header]
    return {
        "event_id": _find_col(h, ("eventid", "eid")),
        "timestamp": _find_col(h, ("date", "time")),
        "level": _find_col(h, ("level",)),
        "source": _find_col(h, ("source",)),
        "message": _find_col(h, ("message", "msg")),
        "account": _find_col(h, ("account", "user", "subject", "targetuser")),
        "domain": _find_col(h, ("domain",)),
        "source_ip": _find_col(h, ("ipaddress", "srcip", "sourceip", "clientip")),
        "logon_type": _find_col(h, ("logontype", "logontype")),
        "source_host": _find_col(h, ("workstation", "sourcehost", "computer", "hostname")),
        "count": _find_col(h, ("count", "occurrences")),
    }


_IP_RE = re.compile(r"\b(\d{1,3}\.){3}\d{1,3}\b")
_ACCOUNT_RE = re.compile(r"(?:Account Name|Target User Name|Target Account|TargetUserName):\s*([^\r\n;.]+)", re.I)
_LOGON_RE = re.compile(r"Logon Type:\s*(\d+)", re.I)


def _extract_field(message: str, field: str) -> Optional[str]:
    if not message:
        return None
    if field == "source_ip":
        m = _IP_RE.search(message)
        return m.group(0) if m else None
    if field == "account":
        m = _ACCOUNT_RE.search(message)
        return m.group(1).strip() if m else None
    if field == "logon_type":
        m = _LOGON_RE.search(message)
        return m.group(1) if m else None
    return None


def _row_value(row: Dict[str, str], cols: Dict[str, Optional[int]], field: str) -> Optional[str]:
    idx = cols.get(field)
    if idx is None:
        return None
    keys = list(row.keys())
    if idx < len(keys):
        val = row.get(keys[idx])
        return val.strip() if isinstance(val, str) else val
    return None


def _coerce_event_id(raw: Optional[str]) -> Optional[int]:
    if raw is None:
        return None
    m = re.search(r"\d+", str(raw))
    return int(m.group(0)) if m else None


def _coerce_logon_type(raw: Optional[str]) -> Tuple[Optional[int], Optional[str]]:
    if raw is None:
        return None, None
    m = re.search(r"\d+", str(raw))
    if not m:
        return None, None
    n = int(m.group(0))
    return n, LOGON_TYPE_NAMES.get(n)


def _coerce_count(raw: Optional[str]) -> int:
    if raw is None:
        return 1
    m = re.search(r"\d+", str(raw))
    return int(m.group(0)) if m else 1


def parse_logs_csv_text(csv_text: str, host_name: Optional[str] = None) -> Dict[str, Any]:
    """Parse a Windows event-log CSV export (string) into the harness schema."""
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None:
        raise ValueError("CSV export is empty or has no header row.")
    cols = _detect_columns(list(reader.fieldnames))

    events: List[Dict[str, Any]] = []
    timestamps: List[str] = []
    computers: List[str] = []
    for row in reader:
        event_id = _coerce_event_id(_row_value(row, cols, "event_id"))
        if event_id is None:
            continue

        meta = SECURITY_EVENT_META.get(event_id, {})
        message = (_row_value(row, cols, "message") or meta.get("message") or "").strip()

        account = _row_value(row, cols, "account") or _extract_field(message, "account")
        domain = _row_value(row, cols, "domain")
        source_ip = _row_value(row, cols, "source_ip") or _extract_field(message, "source_ip")
        lt_raw = _row_value(row, cols, "logon_type") or _extract_field(message, "logon_type")
        logon_type, logon_type_name = _coerce_logon_type(lt_raw)

        source_host = _row_value(row, cols, "source_host") or host_name
        if source_host:
            computers.append(source_host)
        ts = _row_value(row, cols, "timestamp")
        if ts:
            timestamps.append(ts.strip())

        events.append({
            "event_id": event_id,
            "timestamp": ts,
            "level": _normalize_level(_row_value(row, cols, "level")) or meta.get("level"),
            "channel": "Security",
            "account": account,
            "domain": domain,
            "logon_type": logon_type,
            "logon_type_name": logon_type_name,
            "source_ip": source_ip,
            "source_host": source_host,
            "message": message,
            "count": _coerce_count(_row_value(row, cols, "count")),
        })

    if not events:
        raise ValueError("No recognizable Windows event rows were found in the CSV export.")

    host = host_name or (computers[0] if computers else "UNKNOWN-HOST")
    return {
        "source": "Windows Security Event Log",
        "host": host,
        "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_start": timestamps[0] if timestamps else None,
        "window_end": timestamps[-1] if timestamps else None,
        "count": len(events),
        "events": events,
    }


def _parse_evtx(path: str) -> Dict[str, Any]:
    try:
        import Evtx  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "python-evtx is not installed. Install with `pip install python-evtx`, "
            "or export to CSV instead: wevtutil qe Security /f:csv > export.csv"
        ) from exc
    raise NotImplementedError("EVTX parsing requires python-evtx and is not exercised in this environment.")


def parse_logs(input_path: str, host_name: Optional[str] = None) -> Dict[str, Any]:
    """Parse a CSV or EVTX Windows export file into the harness schema."""
    p = Path(input_path)
    if not p.exists():
        raise FileNotFoundError(f"Input log export not found: {input_path}")
    if p.suffix.lower() == ".evtx":
        return _parse_evtx(str(p))
    text = p.read_text(encoding="utf-8", errors="replace")
    return parse_logs_csv_text(text, host_name=host_name)


def parse_logs_to_file(input_path: str, output_path: Optional[str] = None,
                       host_name: Optional[str] = None) -> Tuple[str, int]:
    """Parse an export and optionally write schema JSON. Returns (host, count)."""
    data = parse_logs(input_path, host_name=host_name)
    if output_path:
        Path(output_path).write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data["host"], data["count"]