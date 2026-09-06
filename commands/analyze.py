import click

from sentinelai.ui import error, info, print_markdown, spinner, success
from sentinelai.prompt_engine import (
    PromptMode,
    analyze_event_log_file,
    analyze_scan_file,
    resolve_provider,
)
from sentinelai.routing import auto_parse_to_file, is_raw_log_export, route_provider


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
def analyze(input_file, output_file, kind, llm_name, routing, model, mode, no_save):
    """Analyze saved Nmap scan or Windows Event Log JSON via an LLM (--llm gemini|ollama)."""
    # Day 4 sync: this root entry point must behave EXACTLY like
    # sentinelai/cli.py's analyze (same --routing / --model / --no-save /
    # raw-export auto-parse) so both CLIs produce identical results.
    kind_label = "event log" if kind == "events" else "scan"
    info(f"Analyzing {kind_label} file: {input_file}")
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
