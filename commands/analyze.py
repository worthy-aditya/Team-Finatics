import click
from colorama import Fore, Style, init

from sentinelai.prompt_engine import analyze_scan_file


init(autoreset=True)


@click.command()
@click.option("--input", "-i", "input_file", default="scan_results.json", help="Input JSON scan file")
@click.option("--output", "-o", "output_file", default="day9_nmap_llm_analysis.md", help="Markdown file to save analysis")
@click.option("--model", default=None, help="Preferred Gemini model")
@click.option("--no-save", is_flag=True, help="Print analysis without saving a Markdown file")
def analyze(input_file, output_file, model, no_save):
    """Analyze saved Nmap JSON with the Day 9 LLM prompt."""
    click.echo(f"{Fore.CYAN}[*] Analyzing scan file: {input_file}{Style.RESET_ALL}")

    try:
        used_model, analysis = analyze_scan_file(
            input_file=input_file,
            output_file=None if no_save else output_file,
            preferred_model=model,
        )
    except Exception as exc:
        click.echo(f"{Fore.RED}[!] Analysis failed: {exc}{Style.RESET_ALL}")
        raise click.Abort()

    click.echo(f"{Fore.GREEN}[+] LLM analysis generated with {used_model}{Style.RESET_ALL}")
    if not no_save:
        click.echo(f"{Fore.GREEN}[+] Saved analysis to {output_file}{Style.RESET_ALL}")

    click.echo()
    click.echo(analysis)
