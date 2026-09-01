import click
from colorama import Fore, Style, init

from sentinelai.prompt_engine import (
    PromptMode,
    analyze_event_log_file,
    analyze_scan_file,
    resolve_provider,
)


init(autoreset=True)

# Free providers the team actually uses right now; others are accepted by the
# switcher but fail with a friendly "paid/pending" message (Day 13).
LLM_CHOICES = ["gemini", "ollama", "openai", "claude"]


@click.command()
@click.option("--input", "-i", "input_file", default="scan_results.json", help="Input JSON scan file")
@click.option("--output", "-o", "output_file", default="day9_nmap_llm_analysis.md", help="Markdown file to save analysis")
@click.option("--kind", type=click.Choice(["scan", "events"], case_sensitive=False), default="scan", show_default=True, help="Data kind to analyze: scan (Nmap JSON) or events (Windows Event Log JSON)")
@click.option("--llm", "llm_name", type=click.Choice(LLM_CHOICES, case_sensitive=False), default="gemini", show_default=True, help="LLM provider (free: gemini, ollama)")
@click.option("--model", default=None, help="Preferred model for the chosen provider")
@click.option("--mode", type=click.Choice(["standard", "beginner", "remediation"], case_sensitive=False), default="standard", show_default=True, help="Analysis mode: standard risk report, remediation plan (event logs + scans), or beginner-friendly")
@click.option("--no-save", is_flag=True, help="Print analysis without saving a Markdown file")
def analyze(input_file, output_file, kind, llm_name, model, mode, no_save):
    """Analyze saved Nmap scan or Windows Event Log JSON via an LLM (--llm gemini|ollama)."""
    kind_label = "event log" if kind == "events" else "scan"
    click.echo(f"{Fore.CYAN}[*] Analyzing {kind_label} file: {input_file}{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}[*] LLM provider: {llm_name.lower()}{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}[*] Mode: {mode}{Style.RESET_ALL}")

    try:
        provider = resolve_provider(llm_name)
        prompt_mode = PromptMode(mode.lower())
        if kind == "events":
            used_model, analysis = analyze_event_log_file(
                input_file=input_file,
                output_file=None if no_save else output_file,
                preferred_model=model,
                provider=provider,
                mode=prompt_mode,
            )
        else:
            used_model, analysis = analyze_scan_file(
                input_file=input_file,
                output_file=None if no_save else output_file,
                preferred_model=model,
                provider=provider,
                mode=prompt_mode,
            )
    except Exception as exc:
        click.echo(f"{Fore.RED}[!] Analysis failed: {exc}{Style.RESET_ALL}")
        raise click.Abort()

    click.echo(
        f"{Fore.GREEN}[+] LLM analysis generated via {provider.value} "
        f"with {used_model}{Style.RESET_ALL}"
    )
    if not no_save:
        click.echo(f"{Fore.GREEN}[+] Saved analysis to {output_file}{Style.RESET_ALL}")

    click.echo()
    click.echo(analysis)
