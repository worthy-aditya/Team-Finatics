import click
from sentinelai.ui import error, info, print_panel, spinner, step, success, warn
from sentinelai.scanner import NmapScanner, Scanner
from sentinelai.approval import ApprovalError, request_approval

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
        warn(f"Warning: Target '{target}' format may be invalid")
    
    info(f"Scanning target: {target}")

    if fast:
        # Fast: top 20 most common ports
        arguments = "-p 22,80,443,3306,5432,8080,8443,25,53,110,143,3389,1433,27017,5000,5900,9200,9300,11211,6379"
        info("Fast scan mode (top 20 ports) - ~30 seconds")
    elif aggressive:
        # Aggressive: full scan with scripts
        arguments = "-sV -sC -p 1-1000"
        info("Aggressive scan mode (may take 5-10 minutes)")
    else:
        # Standard: service detection on common ports
        arguments = "-sV -p 1-1000"
        info("Standard scan mode (~2-3 minutes)")

    scanner = NmapScanner(target)

    # Day 24: spinner progress indicator while nmap works. The scanner's own
    # status lines print through the same ui console (rendered above the
    # spinner in a live terminal; plain text when output is not a TTY).
    with spinner(f"Running nmap scan on {target} (this can take a while)..."):
        scan_ok = scanner.scan(arguments=arguments)

    if scan_ok:
        success("Scan completed successfully!")
        step("SCAN RESULTS")
        summary = scanner.get_summary()
        print_panel(summary, title=f"Scan results - {target}")
        return scanner.get_results()

    error("Scan failed")
    if scanner.scan_errors:
        error(f"Details: {'; '.join(scanner.scan_errors)}")
    return None
