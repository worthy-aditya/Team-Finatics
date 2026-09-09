import json

import click
from sentinelai.ui import error, info, print_panel, spinner, step, success, warn
from sentinelai.scanner import NmapScanner, Scanner
from sentinelai.approval import ApprovalError, request_approval
from sentinelai.active_gate import active_scan_host, authorize_active_testing

@click.command()
@click.option("--target", required=True, help="Target IP or hostname to scan")
@click.option("--aggressive", is_flag=True, help="Run aggressive scan (slow, full port scan)")
@click.option("--fast", is_flag=True, help="Run fast scan (top 20 ports only)")
@click.option("--timeout", type=int, default=120, help="Scan timeout in seconds (default: 120)")
@click.option("--json", "output_json", is_flag=True, help="Output results as JSON (no prompts)")
@click.option("--json-file", type=str, default=None, help="Save JSON results to specified file")
@click.option("--confirm", "require_confirmation", is_flag=True, help="Ask for approval before scanning")
@click.option("--yes", "assume_yes", is_flag=True, help="Approve a confirmed operation non-interactively")
@click.option("--active", "active_test", is_flag=True, help="Active testing: block until consent attestation + domain verification pass")
@click.option("--verify-token", "verify_token", default=None, help="Token published at .well-known/sentinelai-verify.txt (prompted if omitted)")
def scan(target, aggressive, fast, timeout, output_json, json_file, require_confirmation, assume_yes, active_test, verify_token):
    """Run security scan on target using Nmap."""
    
    # Day 34: --active blocks until BOTH authorization checks pass
    # (consent attestation -> domain verification). Fail-closed everywhere.
    if active_test:
        if assume_yes:
            raise click.ClickException(
                "Active testing cannot be approved with --yes: you must type "
                "the attestation sentence verbatim (Day 32 consent gate)."
            )
        if output_json or json_file:
            raise click.ClickException(
                "Active testing is interactive (consent attestation + domain "
                "verification) and cannot be combined with --json / --json-file."
            )
        auth = authorize_active_testing(target, verify_token=verify_token)
        if not auth.authorized:
            error(f"Active testing blocked: {auth.blocked_reason}")
            return None
        success("Both authorization checks passed - active testing authorized")
        scan_host = active_scan_host(target)
        if scan_host != target:
            info(f"Scan stage target: {scan_host}")
    else:
        scan_host = target
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
    if not Scanner.validate_target(scan_host):
        warn(f"Warning: Target '{scan_host}' format may be invalid")

    # Day 25 parity: machine mode (--json / --json-file) must behave exactly
    # like sentinelai/cli.py's scan so the E2E pipeline can drive one
    # command line end to end on EITHER entry point.
    machine_mode = bool(output_json or json_file)

    if not machine_mode:
        info(f"Scanning target: {target}")

    if fast:
        # Fast: top 20 most common ports
        arguments = "-p 22,80,443,3306,5432,8080,8443,25,53,110,143,3389,1433,27017,5000,5900,9200,9300,11211,6379"
        if not machine_mode:
            info("Fast scan mode (top 20 ports) - ~30 seconds")
    elif aggressive:
        # Aggressive: full scan with scripts
        arguments = "-sV -sC -p 1-1000"
        if not machine_mode:
            info("Aggressive scan mode (may take 5-10 minutes)")
    else:
        # Standard: service detection on common ports
        arguments = "-sV -p 1-1000"
        if not machine_mode:
            info("Standard scan mode (~2-3 minutes)")

    scanner = NmapScanner(scan_host, quiet=machine_mode)

    # Day 24: spinner progress indicator while nmap works. The scanner's own
    # status lines print through the same ui console (rendered above the
    # spinner in a live terminal; plain text when output is not a TTY).
    with spinner(f"Running nmap scan on {scan_host} (this can take a while)..."):
        scan_ok = scanner.scan(arguments=arguments)

    if scan_ok:
        if machine_mode:
            if output_json:
                # Output JSON to stdout (machine-readable, nothing else).
                click.echo(scanner.to_json_string())
            if json_file:
                scanner.export_json(json_file)
            return scanner.get_results()

        success("Scan completed successfully!")
        step("SCAN RESULTS")
        summary = scanner.get_summary()
        print_panel(summary, title=f"Scan results - {target}")
        return scanner.get_results()

    if machine_mode and output_json:
        error_dict = {
            "error": "Scan failed",
            "target": target,
            "errors": scanner.scan_errors,
        }
        click.echo(json.dumps(error_dict, indent=2))
        return None

    error("Scan failed")
    if scanner.scan_errors:
        error(f"Details: {'; '.join(scanner.scan_errors)}")
    return None
