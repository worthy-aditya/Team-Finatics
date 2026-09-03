import click
from colorama import Fore, Style, init
from sentinelai.scanner import NmapScanner, Scanner
from sentinelai.approval import ApprovalError, request_approval

init(autoreset=True)

@click.command()
@click.option("--target", required=True, help="Target IP or hostname to scan")
@click.option("--aggressive", is_flag=True, help="Run aggressive scan (slow, full port scan)")
@click.option("--fast", is_flag=True, help="Run fast scan (top 20 ports only)")
@click.option("--timeout", type=int, default=120, help="Scan timeout in seconds (default: 120)")
@click.option("--confirm", "require_confirmation", is_flag=True, help="Ask for approval before scanning")
@click.option("--yes", "assume_yes", is_flag=True, help="Approve a confirmed operation non-interactively")
def scan(target, aggressive, fast, timeout, require_confirmation, assume_yes):
    """Run security scan on target using Nmap."""
    
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
            return None

    # Validate target
    if not Scanner.validate_target(target):
        click.echo(f"{Fore.YELLOW}[!] Warning: Target '{target}' format may be invalid{Style.RESET_ALL}")
    
    click.echo(f"{Fore.CYAN}[*] Scanning target: {target}{Style.RESET_ALL}")

    if fast:
        # Fast: top 20 most common ports
        arguments = "-p 22,80,443,3306,5432,8080,8443,25,53,110,143,3389,1433,27017,5000,5900,9200,9300,11211,6379"
        click.echo(f"{Fore.YELLOW}[*] Fast scan mode (top 20 ports) - ~30 seconds{Style.RESET_ALL}")
    elif aggressive:
        # Aggressive: full scan with scripts
        arguments = "-sV -sC -p 1-1000"
        click.echo(f"{Fore.YELLOW}[*] Aggressive scan mode (may take 5-10 minutes){Style.RESET_ALL}")
    else:
        # Standard: service detection on common ports
        arguments = "-sV -p 1-1000"
        click.echo(f"{Fore.YELLOW}[*] Standard scan mode (~2-3 minutes){Style.RESET_ALL}")

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
