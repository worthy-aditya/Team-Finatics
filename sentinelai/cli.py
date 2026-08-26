"""
CLI entry point for SentinelAI
"""

import click
import json
from colorama import Fore, Style, init
from sentinelai.scanner import NmapScanner, Scanner
from sentinelai.natural_cli import NaturalLanguageCLI
from sentinelai.prompt_engine import analyze_scan_file, resolve_provider

init(autoreset=True)

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
def scan(target, aggressive, fast, timeout, output_json, json_file):
    """Run security scan on target"""
    
    # Validate target format
    if not Scanner.validate_target(target):
        click.echo(f"{Fore.YELLOW}[!] Warning: Target '{target}' format may be invalid. Proceeding anyway...{Style.RESET_ALL}")
    
    if not output_json:
        click.echo(f"{Fore.CYAN}[*] Scanning target: {target}{Style.RESET_ALL}")
    
    # Build Nmap arguments based on speed preference
    if fast:
        # Top 20 most common ports only - very fast
        arguments = "-p 22,80,443,3306,5432,8080,8443,25,53,110,143,3389,1433,27017,5000,5900,9200,9300,11211,6379"
        if not output_json:
            click.echo(f"{Fore.YELLOW}[*] Fast scan mode (top 20 ports){Style.RESET_ALL}")
    elif aggressive:
        # Full scan with scripts - very slow
        arguments = "-sV -sC -p 1-1000"
        if not output_json:
            click.echo(f"{Fore.YELLOW}[*] Aggressive scan mode enabled (may take several minutes){Style.RESET_ALL}")
    else:
        # Balanced: service detection on common ports
        arguments = "-sV -p 1-1000"
        if not output_json:
            click.echo(f"{Fore.YELLOW}[*] Standard scan mode{Style.RESET_ALL}")
    
    # Execute Nmap scan using NmapScanner wrapper
    scanner = NmapScanner(target)
    
    if scanner.scan(arguments=arguments):
        if output_json:
            # Output JSON to stdout
            click.echo(scanner.to_json_string())
        else:
            click.echo(f"{Fore.GREEN}[+] Scan completed successfully!{Style.RESET_ALL}\n")
            click.echo("=" * 60)
            click.echo("SCAN RESULTS")
            click.echo("=" * 60)
            # Print results
            summary = scanner.get_summary()
            click.echo(summary)
            
            # Handle JSON file output
            if json_file:
                scanner.export_json(json_file)
            else:
                # Suggest saving to JSON file
                default_json_filename = f"scan_{target.replace('.', '_').replace('/', '_')}.json"
                if click.confirm(f"\n{Fore.CYAN}Save results to {default_json_filename}?{Style.RESET_ALL}", default=False):
                    scanner.export_json(default_json_filename)
    else:
        if not output_json:
            click.echo(f"{Fore.RED}[!] Scan failed{Style.RESET_ALL}")
            if scanner.scan_errors:
                click.echo(f"{Fore.RED}[!] Errors: {'; '.join(scanner.scan_errors)}{Style.RESET_ALL}")
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
@click.option("--llm", "llm_name", type=click.Choice(LLM_CHOICES, case_sensitive=False), default="gemini", show_default=True, help="LLM provider (free: gemini, ollama)")
@click.option("--model", default=None, help="Preferred model for the chosen provider")
@click.option("--no-save", is_flag=True, help="Print analysis without saving a Markdown file")
def analyze(input_file, output_file, llm_name, model, no_save):
    """Analyze saved Nmap JSON via an LLM (--llm gemini|ollama)."""
    click.echo(f"{Fore.CYAN}[*] Analyzing scan file: {input_file}{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}[*] LLM provider: {llm_name.lower()}{Style.RESET_ALL}")

    try:
        provider = resolve_provider(llm_name)
        used_model, analysis = analyze_scan_file(
            input_file=input_file,
            output_file=None if no_save else output_file,
            preferred_model=model,
            provider=provider,
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


if __name__ == "__main__":
    main()
