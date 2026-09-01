"""sentinelai/routing.py - Day 21 (Week 3).

Small, pure helpers that let `sentinelai analyze --kind events` accept a RAW
Windows event-log export (CSV / EVTX) directly and route it to the right LLM
provider - no manual `parse` step and no guessing.

  * route_provider(): maps `--routing report|private` to a provider, with an
    explicit `--llm` winning over routing.
    - report  -> gemini (rich, analyst-facing - Day 20 recommendation)
    - private -> ollama (data stays on the host - zero cloud egress)
  * is_raw_log_export(): detects .csv/.evtx inputs.
  * load_event_input(): turns a raw export into analysis-ready schema JSON
    (via sentinelai.log_parser) and passes already-structured JSON through.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from sentinelai.log_parser import parse_logs

# Day 20 conclusion: use gemini for analyst-facing report work, ollama when the
# log data must not leave the host.
ROUTING_PROVIDER: Dict[str, str] = {
    "report": "gemini",
    "private": "ollama",
}

DEFAULT_PROVIDER = "gemini"  # backward-compatible CLI default

RAW_LOG_SUFFIXES = (".csv", ".evtx")


def route_provider(llm_name: Optional[str] = None, routing: Optional[str] = None) -> str:
    """Resolve the effective provider name.

    Priority: explicit ``llm_name`` > ``routing`` policy > DEFAULT_PROVIDER.
    ``routing`` is validated against ROUTING_PROVIDER keys first.
    """
    if llm_name:
        return llm_name.strip().lower()
    if routing:
        routing = routing.strip().lower()
        if routing not in ROUTING_PROVIDER:
            raise ValueError(
                f"Unknown routing policy '{routing}'. "
                f"Valid: {', '.join(sorted(ROUTING_PROVIDER))}."
            )
        return ROUTING_PROVIDER[routing]
    return DEFAULT_PROVIDER


def is_raw_log_export(path: str) -> bool:
    """True when the input file is a raw CSV/EVTX event-log export."""
    return Path(path).suffix.lower() in RAW_LOG_SUFFIXES


def load_event_input(input_file: str) -> Dict[str, Any]:
    """Load event analysis input, auto-parsing raw exports.

    For .csv/.evtx inputs this runs the real parser and returns the structured
    schema dict directly; for .json inputs it is a passthrough.
    """
    if is_raw_log_export(input_file):
        return parse_logs(input_file)
    from sentinelai.prompt_engine import load_event_log_data
    return load_event_log_data(input_file)


def auto_parse_to_file(input_file: str) -> Tuple[str, int]:
    """Parse a raw export to a temporary JSON file; returns (json_path, count).

    Used so the rest of the pipeline (analyze_event_log_file) can consume the
    same file-shaped interface it already understands - no engine changes.
    """
    data = parse_logs(input_file)
    tmp = Path(tempfile.gettempdir()) / f"sentinelai_auto_{abs(hash(Path(input_file))) % 10**8}.json"
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(tmp), int(data["count"])