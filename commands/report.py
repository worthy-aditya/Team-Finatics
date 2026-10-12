import re
from pathlib import Path

import click
from rich.console import Console

from event_log_report_pipeline import run_event_log_to_report
from nmap_report_pipeline import run_nmap_to_report

console = Console()


def _looks_like_nmap_text(text):
    """Heuristic to choose the Nmap pipeline when raw scan output is provided."""
    normalized = text.strip()
    if not normalized:
        return False
    if re.search(r"^\s*PORT\b", text, flags=re.IGNORECASE | re.MULTILINE):
        return True
    if "/tcp" in text.lower() or "/udp" in text.lower():
        return True
    if re.search(r"^\s*\d+/\w+\s+\w+\s+\w+", text, flags=re.IGNORECASE | re.MULTILINE):
        return True
    return False


@click.command()
@click.argument("source", required=False)
@click.option(
    "--format",
    "report_format",
    default="text",
    show_default=True,
    type=click.Choice(["text", "json", "markdown"], case_sensitive=False),
    help="Output format for the generated report.",
)
@click.option("--audience", default="general", show_default=True, help="Audience profile for the analysis summary.")
@click.option("--no-llm", is_flag=True, default=False, help="Disable LLM-backed analysis and use the offline summary fallback.")
def report(source, report_format, audience, no_llm):
    """Generate a SentinelAI security report from a scan file or raw input text."""
    if not source:
        console.print(
            "[yellow]Provide a file path or scan text. Example: python sentinelai.py report scan.txt --format markdown[/yellow]"
        )
        return

    source_path = Path(source)
    if source_path.exists():
        try:
            source_text = source_path.read_text(encoding="utf-8")
        except OSError:
            source_text = source
    else:
        source_text = source

    if not source_text.strip():
        console.print("[red]The selected source is empty.[/red]")
        return

    use_llm = not no_llm
    if _looks_like_nmap_text(source_text):
        result = run_nmap_to_report(
            source_text,
            report_format=report_format.lower(),
            audience=audience,
            use_llm=use_llm,
        )
    else:
        result = run_event_log_to_report(
            source_text,
            report_format=report_format.lower(),
            audience=audience,
            use_llm=use_llm,
        )

    console.print(result["report"])
