import shutil
import subprocess
from pathlib import Path

import click
from rich.console import Console

from nmap_report_pipeline import run_nmap_to_report

console = Console()


@click.command()
@click.argument("target", required=False)
@click.option(
    "--format",
    "report_format",
    default="text",
    show_default=True,
    type=click.Choice(["text", "json", "markdown"], case_sensitive=False),
    help="Output format for the generated report.",
)
@click.option("--audience", default="general", show_default=True, help="Audience profile for the summary.")
@click.option("--no-llm", is_flag=True, default=False, help="Disable LLM-backed analysis and use the offline summary fallback.")
@click.option("--ports", default=None, help="Optional port range for nmap when running a live scan.")
def scan(target, report_format, audience, no_llm, ports):
    """Run a scan on a target and generate a SentinelAI report."""
    if not target:
        console.print("[yellow]Provide a target or scan file. Example: python sentinelai.py scan 192.168.1.1[/yellow]")
        return

    target_path = Path(target)
    if target_path.exists():
        source_text = target_path.read_text(encoding="utf-8")
    elif shutil.which("nmap"):
        command = ["nmap", "-sV"]
        if ports:
            command.extend(["-p", ports])
        command.append(target)
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        source_text = (completed.stdout or "") + ("\n" + (completed.stderr or "") if completed.stderr else "")
        if not source_text.strip():
            console.print("[red]nmap returned no output for the target.[/red]")
            return
    else:
        console.print(
            "[red]Target is not a file and nmap is not installed. Provide a saved Nmap output file or install nmap.[/red]"
        )
        return

    result = run_nmap_to_report(
        source_text,
        report_format=report_format.lower(),
        audience=audience,
        use_llm=not no_llm,
    )
    console.print(result["report"])
