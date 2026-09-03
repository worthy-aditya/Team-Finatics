"""
sentinelai/logs_command.py
Day 22 (Week 4): ONE shared `logs` Click command, used by both CLI entry
points (sentinelai/cli.py and commands/logs.py) so there is no duplicate
implementation.

It reads Windows Security events with Affan's native reader (or the built-in
--sample corpus for a no-admin/low-risk demo), converts them to the harness
schema, and can feed them straight through the unified LLM analysis pipeline:

    sentinelai logs --sample --json              # native-style doc (no LLM)
    sentinelai logs --sample -o events.json      # harness schema for analyze
    sentinelai logs --sample --analyze           # sample -> unified LLM analysis
    sentinelai logs --analyze                    # real Security log -> LLM

The LLM path reuses sentinelai.routing (--llm / --routing policy) and
prompt_engine.analyze_event_log_data(); the human summary reuses Affan's
EventFilter. Nothing here re-implements analysis.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import click
from colorama import Fore, Style

from sentinelai.event_bridge import (
    collect_events,
    events_to_schema_file,
    summarize,
)

def build_logs_command():
    """Construct and return the shared `logs` Click command."""

    @click.command(name="logs")
    @click.option("--hours", default=24, show_default=True, type=click.IntRange(min=1),
                  help="Read events from the last N hours (real log only).")
    @click.option("--event-ids", multiple=True, type=int,
                  help="Filter by Event ID; may be repeated (e.g. 4624 4625).")
    @click.option("--max-events", default=1000, show_default=True,
                  type=click.IntRange(min=1), help="Maximum events to read.")
    @click.option("--json", "output_json", is_flag=True,
                  help="Print events + (optional) analysis as JSON.")
    @click.option("-o", "--output", "output_file", default=None,
                  help="Save a harness-schema JSON file (feed to `analyze -i <f> --kind events`).")
    @click.option("--analyze", is_flag=True,
                  help="Run the unified LLM event analysis (prompt_engine).")
    @click.option("--llm", "llm_name", default=None,
                  type=click.Choice(["gemini", "ollama", "openai", "claude"], case_sensitive=False),
                  help="LLM provider for --analyze (free: gemini, ollama).")
    @click.option("--routing", default=None, type=click.Choice(["report", "private"],
                                                               case_sensitive=False),
                  help="Provider policy for --analyze: report->gemini, private->ollama.")
    @click.option("--mode", type=click.Choice(["standard", "remediation"], case_sensitive=False),
                  default="standard", show_default=True,
                  help="Analysis mode (events support standard & remediation).")
    @click.option("--sample", is_flag=True,
                  help="Use the built-in sample corpus instead of Windows logs (no admin needed).")
    def logs(hours, event_ids, max_events, output_json, output_file,
             analyze, llm_name, routing, mode, sample):
        """Read and analyze Windows Security events (real log or --sample)."""
        ids = list(event_ids) or None

        try:
            events, source, host = collect_events(
                use_sample=sample, hours=hours, event_ids=ids, max_events=max_events
            )
        except RuntimeError as exc:
            click.echo(f"{Fore.RED}[!] {exc}{Style.RESET_ALL}")
            raise click.Abort()

        source_label = "sample" if source == "sample" else "Windows Security log"
        click.echo(f"{Fore.CYAN}[*] Read {len(events)} event(s) from {source_label} "
                   f"(host={host}){Style.RESET_ALL}")

        # Save the harness-schema JSON for later `analyze -i <file> --kind events`.
        if output_file:
            n = events_to_schema_file(events, host, output_file)
            click.echo(f"{Fore.GREEN}[+] Saved {n} events to {output_file} "
                       f"(schema JSON for `analyze --kind events`){Style.RESET_ALL}")

        summary = summarize(events)

        # Optional LLM analysis through the unified pipeline (routing aware).
        llm_markdown = None
        if analyze:
            llm_markdown = _run_llm_analysis(events, host, llm_name, routing, mode)

        if output_json:
            doc: Dict[str, Any] = {
                "log_metadata": {
                    "source": source,
                    "host": host,
                    "hours_back": hours,
                    "event_ids": ids,
                },
                "events": events,
                "critical_events_found": summary.get("critical_events_found", len(events)),
                "threat_level": summary.get("threat_level", "UNKNOWN"),
                "analysis": summary,
            }
            if llm_markdown:
                doc["llm_analysis_markdown"] = llm_markdown
            click.echo(json.dumps(doc, indent=2, default=str))
            return

        click.echo(f"Threat level: {summary.get('threat_level', 'N/A')}")
        for alert in summary.get("alerts", []):
            sev = alert.get("severity", "?")
            atype = alert.get("type", "?")
            desc = alert.get("description", "")
            click.echo(f"[{sev}] {atype}: {desc}")
        if summary.get("recommendations"):
            click.echo("Recommendations:")
            for rec in summary["recommendations"]:
                click.echo(f"  - {rec}")
        if llm_markdown:
            click.echo()
            click.echo(llm_markdown)

    return logs


def _run_llm_analysis(events: List[Dict[str, Any]], host: str,
                      llm_name: Optional[str], routing: Optional[str],
                      mode: str) -> str:
    """Run unified event-log LLM analysis on the collected events."""
    from sentinelai.event_bridge import native_events_to_schema
    from sentinelai.prompt_engine import (
        PromptMode,
        analyze_event_log_data,
        resolve_provider,
    )
    from sentinelai.routing import route_provider

    effective_llm = route_provider(llm_name, routing)
    provider = resolve_provider(effective_llm)
    prompt_mode = PromptMode(mode.lower())

    data = native_events_to_schema(events, host=host)
    click.echo(f"{Fore.CYAN}[*] Analyzing {data['count']} event(s) via "
               f"{provider.value} (mode={mode}){Style.RESET_ALL}")
    result = analyze_event_log_data(data, provider=provider, mode=prompt_mode)
    return (
        f"### LLM Analysis ({provider.value} / `{result.model}`)\n\n"
        f"{result.analysis}"
    )