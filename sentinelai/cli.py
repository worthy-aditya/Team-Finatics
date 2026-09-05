"""
CLI entry point for SentinelAI
"""

import click
import json

from sentinelai.ui import error, info, print_markdown, print_panel, spinner, step, success, warn
from sentinelai.scanner import NmapScanner, Scanner
from sentinelai.natural_cli import NaturalLanguageCLI
from sentinelai.approval import ApprovalError, request_approval
from sentinelai.routing import auto_parse_to_file, is_raw_log_export, route_provider
from sentinelai.logs_command import build_logs_command
from sentinelai.prompt_engine import (
    PromptMode,
    analyze_event_log_file,
    analyze_scan_file,
    resolve_provider,
)

# Free providers the team actually uses right now; others are accepted by
# the switcher but fail with a friendly "paid/pending" message (Day 13).
LLM_CHOICES = ["gemini", "ollama", "openai", "claude"]


@click.group(help="SentinelAI CLI - AI-powered cybersecurity agent")
def main():
    """SentinelAI CLI - AI-powered cybersecurity agent"""
    pass


@main.command()
@click.option("--target", required=True, help="Target IP or hostname to scan")
@click.option("--aggressive", is_flag=True, help="Run aggressive scan (slow, full port scan)")
@click.option("--fast", is_flag=True, help="Run fast scan (top 20 ports only)")
@click.option("--timeout", type=int, default=120, help="Scan timeout in seconds (default: 120)")
@click.option("--json", "output_json", is_flag=True, help="Output results as JSON (no prompts)")
@click.option("--json-file", type=str, default=None, help="Save JSON results to specified file")
@click.option("--confirm", "require_confirmation", is_flag=True, help="Ask for approval before scanning")
@click.option("--yes", "assume_yes", is_flag=True, help="Approve a confirmed operation non-interactively")
def scan(target, aggressive, fast, timeout, output_json, json_file, require_confirmation, assume_yes):
    """Run security scan on target"""
    
    # Day 20 human-in-the-loop approval (reuses sentinelai.approval).
    if require_confirmation:
        try:
            approved = request_approval(
                "security scan",
                target,
                assume_yes=assume_yes,
            )
        except ApprovalError as exc:
            raise click.ClickException(str(exc)) from exc
        if not approved:
            click.echo("Scan cancelled: approval was not granted.")
            return

    # Validate target format
    if not Scanner.validate_target(target):
        warn(f"Warning: Target '{target}' format may be invalid. Proceeding anyway...")
    
    if not output_json:
        info(f"Scanning target: {target}")
    
    # Build Nmap arguments based on speed preference
    if fast:
        # Top 20 most common ports only - very fast
        arguments = "-p 22,80,443,3306,5432,8080,8443,25,53,110,143,3389,1433,27017,5000,5900,9200,9300,11211,6379"
        if not output_json:
            info("Fast scan mode (top 20 ports)")
    elif aggressive:
        # Full scan with scripts - very slow
        arguments = "-sV -sC -p 1-1000"
        if not output_json:
            info("Aggressive scan mode enabled (may take several minutes)")
    else:
        # Balanced: service detection on common ports
        arguments = "-sV -p 1-1000"
        if not output_json:
            info("Standard scan mode")
    
    # Execute Nmap scan using NmapScanner wrapper
    # Day 24: quiet in --output-json mode so stdout stays JSON-pure.
    scanner = NmapScanner(target, quiet=output_json)
    
    if scanner.scan(arguments=arguments):
        if output_json:
            # Output JSON to stdout
            click.echo(scanner.to_json_string())
        else:
            success("Scan completed successfully!")
            step("SCAN RESULTS")
            # Print results
            summary = scanner.get_summary()
            print_panel(summary, title=f"Scan results - {target}")
            
            # Handle JSON file output
            if json_file:
                scanner.export_json(json_file)
            else:
                # Suggest saving to JSON file
                default_json_filename = f"scan_{target.replace('.', '_').replace('/', '_')}.json"
                if click.confirm(f"\nSave results to {default_json_filename}?", default=False):
                    scanner.export_json(default_json_filename)
    else:
        if not output_json:
            error("Scan failed")
            if scanner.scan_errors:
                error(f"Errors: {'; '.join(scanner.scan_errors)}")
        else:
            error_dict = {
                "error": "Scan failed",
                "target": target,
                "errors": scanner.scan_errors
            }
            click.echo(json.dumps(error_dict, indent=2))


@main.command()
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
    kind_label = "event log" if kind == "events" else "scan"
    info(f"Analyzing {kind_label} file: {input_file}")
    effective_llm = route_provider(llm_name, routing)
    info(f"LLM provider: {effective_llm}")
    info(f"Mode: {mode}")

    try:
        provider = resolve_provider(effective_llm)
        prompt_mode = PromptMode(mode.lower())
        if kind == "events":
            # Day 21: accept a raw CSV/EVTX export directly and auto-parse it
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


@main.command()
@click.option("-i", "--input", "input_file", required=True, type=click.Path(exists=True),
              help="Windows event-log export (CSV or .evtx)")
@click.option("-o", "--output", "output_file", default="parsed_events.json",
              help="Output JSON file in the analysis-ready schema")
@click.option("--logs", is_flag=True, required=True,
              help="Parse as a Windows event-log export (CSV or EVTX)")
@click.option("--host", default=None, help="Override the host name for this export")
def parse(input_file, output_file, logs, host):
    """Parse raw Windows event exports (CSV / EVTX) into analysis-ready JSON."""
    from sentinelai.log_parser import parse_logs_to_file
    try:
        used_host, n = parse_logs_to_file(input_file, output_file, host_name=host)
        success(f"Parsed {n} events (host={used_host}) -> {output_file}")
    except Exception as exc:
        error(f"Parse failed: {exc}")
        raise click.Abort()


@main.command(help="Natural Language CLI Interface")
def natural_cli():
    """
    🤖 Natural Language CLI Interface

    Start an interactive session where you can use plain English commands
    to run security scans and generate reports.
    
    Examples:
        > scan localhost quickly
        > fast scan on google.com
        > aggressive scan 192.168.1.1
        > show network info
        > generate a report
        > analyze the results
        > help
    """
    cli = NaturalLanguageCLI()
    cli.run_interactive()


@main.command()
def version():
    """Show version"""
    click.echo("SentinelAI CLI v0.1.0")


main.add_command(build_logs_command())


if __name__ == "__main__":
    main()
