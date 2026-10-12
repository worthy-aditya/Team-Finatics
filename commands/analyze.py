import click
import json
from typing import Dict

from sentinelai.ui import error, info, print_markdown, spinner, success
from sentinelai.prompt_engine import (
    PromptMode,
    analyze_event_log_file,
    analyze_scan_file,
    resolve_provider,
)
from sentinelai.routing import auto_parse_to_file, is_raw_log_export, recommend_provider, route_provider
from sentinelai.dashboard import build_dashboard
from sentinelai.health_history import (
    DEFAULT_HISTORY_PATH,
    load_history,
    record_snapshot,
    summarize_trends,
)


# Free providers the team actually uses right now; others are accepted by the
# switcher but fail with a friendly "paid/pending" message (Day 13).
LLM_CHOICES = ["gemini", "ollama", "openai", "claude"]


@click.command()
@click.option("--input", "-i", "input_file", default="scan_results.json", help="Input JSON scan file")
@click.option("--output", "-o", "output_file", default="day9_nmap_llm_analysis.md", help="Markdown file to save analysis")
@click.option("--kind", type=click.Choice(["scan", "events"], case_sensitive=False), default="scan", show_default=True, help="Data kind to analyze: scan (Nmap JSON) or events (Windows Event Log JSON)")
@click.option("--llm", "llm_name", type=click.Choice(LLM_CHOICES, case_sensitive=False), default=None, show_default="gemini", help="LLM provider (free: gemini, ollama)")
@click.option("--routing", type=click.Choice(["report", "private"], case_sensitive=False), default=None, show_default="llm-or-gemini", help="Provider policy: report -> gemini, private -> ollama (explicit --llm wins)")
@click.option("--model", default=None, help="Preferred model for the chosen provider")
@click.option("--mode", type=click.Choice(["standard", "beginner", "remediation"], case_sensitive=False), default="standard", show_default=True, help="Analysis mode: standard risk report, remediation plan (event logs + scans), or beginner-friendly")
@click.option("--no-save", is_flag=True, help="Print analysis without saving a Markdown file")
@click.option("--provider-scores", "provider_scores_json", default=None, help="JSON file with provider health scores {<provider>: <score>} used for health-aware routing (Day 52)")
@click.option("--dashboard", is_flag=True, help="Print the provider health dashboard and exit (no analysis)")
@click.option("--health-history", is_flag=True, help="With --dashboard: record current scores to the history file and show per-provider trends (Day 54)")
def analyze(input_file, output_file, kind, llm_name, routing, model, mode, no_save, provider_scores_json, dashboard, health_history):
    """Analyze saved Nmap scan or Windows Event Log JSON via an LLM (--llm gemini|ollama)."""
    # Day 4 sync: this root entry point must behave EXACTLY like
    # sentinelai/cli.py's analyze (same --routing / --model / --no-save /
    # raw-export auto-parse) so both CLIs produce identical results.
    kind_label = "event log" if kind == "events" else "scan"
    info(f"Analyzing {kind_label} file: {input_file}")

    # Day 52: use health-aware provider routing. When health scores are not
    # supplied, the legacy --routing policy (report -> gemini, private ->
    # ollama) governs. When scores are available, they rank providers and the
    # top one wins, subject to the routing sensitivity constraint.
    provider_scores: Dict[str, float] = {}
    if provider_scores_json:
        with open(provider_scores_json, encoding="utf-8") as _fh:
            provider_scores = json.load(_fh)
            info(f"Loaded provider health scores: {provider_scores}")

    # Day 53: --dashboard short-circuits analysis to show provider health.
    if dashboard:
        trends = None
        if health_history:
            # Day 54: persist the current scores as a snapshot, then show how
            # each provider is trending relative to its recent history.
            snapshot_scores = provider_scores or {"gemini": 80.0, "ollama": 78.0, "deepseek": 85.0}
            record_snapshot(snapshot_scores, path=DEFAULT_HISTORY_PATH)
            info(f"Recorded provider health snapshot to {DEFAULT_HISTORY_PATH}")
            trends = summarize_trends(load_history(DEFAULT_HISTORY_PATH))
        click.echo(build_dashboard(provider_scores or None, trends=trends))
        return

    effective_llm = None
    if provider_scores:
        effective_llm = recommend_provider(
            routing=routing,
            is_sensitive=(routing == "private"),
            has_api_key=(llm_name in (None, "gemini")),
            provider_scores=provider_scores,
        )
        info(f"LLM provider (health-aware): {effective_llm}")
    else:
        effective_llm = route_provider(llm_name, routing)
        info(f"LLM provider: {effective_llm}")
    info(f"Mode: {mode}")

    try:
        provider = resolve_provider(effective_llm)
        prompt_mode = PromptMode(mode.lower())
        if kind == "events":
            # Day 21: accept a raw CSV/EVTX export directly and auto-parse it.
            resolved_input = input_file
            if is_raw_log_export(resolved_input):
                resolved_input, _parsed_n = auto_parse_to_file(resolved_input)
                info(f"Auto-parsed raw event-log export -> {_parsed_n} events")
            # Day 24: spinner while the LLM works (prompt_engine retry
            # notices print above it through the same console).
            with spinner(f"Generating event-log analysis via {effective_llm} (free providers can take 1-2 minutes)..."):
                used_model, analysis = analyze_event_log_file(
                    input_file=resolved_input,
                    output_file=None if no_save else output_file,
                    preferred_model=model,
                    provider=provider,
                    mode=prompt_mode,
                )
        else:
            with spinner(f"Generating scan analysis via {effective_llm} (free providers can take 1-2 minutes)..."):
                used_model, analysis = analyze_scan_file(
                    input_file=input_file,
                    output_file=None if no_save else output_file,
                    preferred_model=model,
                    provider=provider,
                    mode=prompt_mode,
                )
    except Exception as exc:
        error(f"Analysis failed: {exc}")
        raise click.Abort()

    success(f"LLM analysis generated via {provider.value} with {used_model}")
    if not no_save:
        success(f"Saved analysis to {output_file}")

    click.echo()
    # Day 24: render the Markdown analysis with Rich instead of a raw echo.
    print_markdown(analysis)
