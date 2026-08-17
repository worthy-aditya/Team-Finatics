"""
CLI entry point for SentinelAI
"""

import click
from colorama import Fore, Style, init
from sentinelai.scanner import NmapScanner

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
    
    # Build Nmap arguments
    if aggressive:
        arguments = "-sV -sC -p 1-1000"
        click.echo(f"{Fore.YELLOW}[*] Aggressive scan mode enabled{Style.RESET_ALL}")
    else:
        arguments = "-sV -p 1-1000"
    
    # Execute Nmap scan using NmapScanner wrapper
    scanner = NmapScanner(target)
    
    if scanner.scan(arguments=arguments):
        click.echo(f"{Fore.GREEN}[+] Scan completed successfully!{Style.RESET_ALL}\n")
        click.echo("=" * 60)
        click.echo("RAW NMAP OUTPUT")
        click.echo("=" * 60)
        # Print raw results
        if scanner.parsed_results:
            summary = scanner.get_summary()
            click.echo(summary)
    else:
        click.echo(f"{Fore.RED}[!] Scan failed{Style.RESET_ALL}")


@main.command()
def version():
    """Show version"""
    click.echo("SentinelAI CLI v0.1.0")


if __name__ == "__main__":
    main()
