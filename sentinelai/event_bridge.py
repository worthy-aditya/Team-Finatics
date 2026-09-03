"""
sentinelai/event_bridge.py
Day 22 (Week 4) reconciliation bridge.

Connects Affan's native Windows Event Log reader (sentinelai/event_logs.py)
to the unified analysis pipeline (sentinelai/prompt_engine.py) so BOTH real
Security-log events AND the built-in sample/fake scenario flow through the
SAME code path:

    sentinelai logs --sample -o events.json      # fake/sample scenario
    sentinelai logs --sample --analyze           # sample through the LLM
    sentinelai logs --analyze                    # real Security log through the LLM
    sentinelai analyze -i events.json --kind events   # reuse existing pipeline

The key function is native_events_to_schema(): Affan's native event dicts
(log/event_id/event_type/source/computer/timestamp/message/user/logon_type/
ip_address) are normalized into the harness event schema the prompt engine
already expects (the day15_sample_events.json contract:
event_id/timestamp/level/channel/account/domain/logon_type/logon_type_name/
source_ip/source_host/message/count). No analysis logic is duplicated here -
the LLM analysis stays in prompt_engine.analyze_event_log_data().
"""

from __future__ import annotations

import json
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sentinelai.event_logs import (
    EventFilter,
    EventLogReader,
    SAMPLE_SECURITY_EVENTS,
)
from sentinelai.log_parser import LOGON_TYPE_NAMES, SECURITY_EVENT_META

# Map Windows event *type* text (from pywin32 / sample data) to our canonical
# level strings. Falls back to the log_parser metadata table for known Event
# IDs (e.g. 1102 -> critical) before defaulting to "information".
_LEVEL_BY_EVENT_TYPE: Dict[str, str] = {
    "information": "information",
    "info": "information",
    "success": "information",
    "audit success": "information",
    "warning": "warning",
    "warn": "warning",
    "error": "error",
    "critical": "critical",
}

DEFAULT_SAMPLE_HOST = "DESKTOP-SAMPLE"
UNKNOWN_HOST = "UNKNOWN-HOST"


def collect_events(
    use_sample: bool = False,
    hours: int = 24,
    event_ids: Optional[List[int]] = None,
    max_events: int = 1000,
    log_name: str = "Security",
) -> Tuple[List[Dict[str, Any]], str, str]:
    """Read Windows Security events, returning (native_events, source, host).

    * ``use_sample=True``  -> the built-in sample corpus (works with no admin
      rights and no pywin32; this is the "fake scenario" path, identical in
      shape to the real reader's output).
    * ``use_sample=False`` -> Affan's native ``EventLogReader`` (pywin32).
      Requires pywin32 + (for the Security log) admin privileges. When the
      provider is unavailable it raises a RuntimeError that tells the user to
      fall back to ``--sample`` - never a silent empty result.

    ``event_ids`` optionally filters to specific Event IDs.
    """
    if use_sample:
        events: List[Dict[str, Any]] = [dict(e) for e in SAMPLE_SECURITY_EVENTS]
        if event_ids:
            events = [e for e in events if e.get("event_id") in set(event_ids)]
        host = (events[0].get("computer") if events else None) or DEFAULT_SAMPLE_HOST
        return events, "sample", str(host)

    reader = EventLogReader()
    events = reader.read_events(
        log_name=log_name,
        max_events=max_events,
        hours_back=hours,
        event_ids=event_ids,
    )
    host = (events[0].get("computer") if events else None) or (
        socket.gethostname() or UNKNOWN_HOST
    )
    if not events and getattr(reader, "last_error", None):
        raise RuntimeError(
            f"{reader.last_error} "
            "(pywin32 not installed, or the Security log needs administrator "
            "privileges). Use --sample for a local demonstration without "
            "Windows log access."
        )
    return events, "windows", str(host)
def _split_account(account: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Split 'DOMAIN\\user' into (user, domain); plain 'user' -> (user, None)."""
    if not account:
        return None, None
    if "\\" in account:
        domain, _, user = account.partition("\\")
        return (user or None), (domain or None)
    return account, None


def native_events_to_schema(
    events: List[Dict[str, Any]], host: Optional[str] = None
) -> Dict[str, Any]:
    """Convert Affan's native event dicts into the harness schema.

    This is the single adapter that lets both the real reader output and the
    ``--sample`` corpus feed ``analyze --kind events`` unchanged.
    """
    norm_events: List[Dict[str, Any]] = []
    timestamps: List[str] = []

    for ev in events:
        raw_id = ev.get("event_id")
        if raw_id is None:
            continue
        try:
            event_id = int(raw_id)
        except (TypeError, ValueError):
            continue

        account, domain = _split_account(ev.get("user"))
        lt_raw = ev.get("logon_type")
        try:
            logon_type = int(lt_raw) if lt_raw is not None else None
        except (TypeError, ValueError):
            logon_type = None

        ts = ev.get("timestamp")
        if ts:
            timestamps.append(str(ts))

        event_type = str(ev.get("event_type") or "").strip().lower()
        level = (
            _LEVEL_BY_EVENT_TYPE.get(event_type)
            or SECURITY_EVENT_META.get(event_id, {}).get("level")
            or "information"
        )
        message = ev.get("message") or SECURITY_EVENT_META.get(event_id, {}).get(
            "message"
        ) or ""

        norm_events.append(
            {
                "event_id": event_id,
                "timestamp": ts,
                "level": level,
                "channel": ev.get("log") or "Security",
                "account": account,
                "domain": domain,
                "logon_type": logon_type,
                "logon_type_name": LOGON_TYPE_NAMES.get(logon_type)
                if logon_type is not None
                else None,
                "source_ip": ev.get("ip_address"),
                "source_host": ev.get("computer"),
                "message": message,
                "count": 1,
            }
        )

    used_host = host or (events[0].get("computer") if events else None) or UNKNOWN_HOST
    return {
        "source": "Windows Security Event Log",
        "host": str(used_host),
        "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_start": timestamps[0] if timestamps else None,
        "window_end": timestamps[-1] if timestamps else None,
        "count": len(norm_events),
        "events": norm_events,
    }


def events_to_schema_file(
    events: List[Dict[str, Any]], host: Optional[str], output_path: str
) -> int:
    """Write the harness-schema JSON for `analyze -i <file> --kind events`."""
    data = native_events_to_schema(events, host=host)
    Path(output_path).write_text(json.dumps(data, indent=2), encoding="utf-8")
    return int(data["count"])


def summarize(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Human-friendly threat summary using Affan's EventFilter (no LLM needed)."""
    return EventFilter().analyze_events(events)