"""
CLI entry point for SentinelAI
"""

import click
from colorama import Fore, Style, init

init(autoreset=True)


@click.group()
def main():
    """SentinelAI CLI - AI-powered cybersecurity agent"""
    pass


@main.command()
@click.option("--target", required=True, help="Target IP or hostname to scan")
@click.option("--aggressive", is_flag=True, help="Run aggressive scan")
def scan(target, aggressive):
    """Run security scan on target"""
    click.echo(f"{Fore.CYAN}[*] Scanning target: {target}{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}[*] Aggressive mode: {aggressive}{Style.RESET_ALL}")
    click.echo(f"{Fore.GREEN}[+] Scan initiated...{Style.RESET_ALL}")


@main.command()
def version():
    """Show version"""
    click.echo("SentinelAI CLI v0.1.0")


if __name__ == "__main__":
    main()
