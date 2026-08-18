import click
from colorama import Fore, Style, init
from sentinelai.scanner import NmapScanner, Scanner

init(autoreset=True)

@click.command()
@click.option("--target", required=True, help="Target IP or hostname to scan")
@click.option("--aggressive", is_flag=True, help="Run aggressive scan")
def scan(target, aggressive):
    """Run security scan on target using Nmap."""
    
    # Validate target
    if not Scanner.validate_target(target):
        click.echo(f"{Fore.YELLOW}[!] Warning: Target '{target}' format may be invalid{Style.RESET_ALL}")
    
    click.echo(f"{Fore.CYAN}[*] Scanning target: {target}{Style.RESET_ALL}")

    if aggressive:
        arguments = "-sV -sC -p 1-1000"
        click.echo(f"{Fore.YELLOW}[*] Aggressive scan mode enabled{Style.RESET_ALL}")
    else:
        arguments = "-sV -p 1-1000"

    scanner = NmapScanner(target)

    if scanner.scan(arguments=arguments):
        click.echo(f"{Fore.GREEN}[+] Scan completed successfully!{Style.RESET_ALL}\n")
        click.echo("=" * 60)
        click.echo("SCAN RESULTS")
        click.echo("=" * 60)
        summary = scanner.get_summary()
        click.echo(summary)
        return scanner.get_results()
    else:
        click.echo(f"{Fore.RED}[!] Scan failed{Style.RESET_ALL}")
        if scanner.scan_errors:
            click.echo(f"{Fore.RED}[!] Details: {'; '.join(scanner.scan_errors)}{Style.RESET_ALL}")
        return None
