"""
CLI entry point for SentinelAI
"""

import click
import json
from colorama import Fore, Style, init
from sentinelai.scanner import NmapScanner
from sentinelai.event_logs import EventFilter, EventLogReader, SAMPLE_SECURITY_EVENTS
from sentinelai.prompt_engine import PromptEngine, get_mock_analysis
from sentinelai.approval import ApprovalError, request_approval

init(autoreset=True)


@click.group()
def main():
    """SentinelAI CLI - AI-powered cybersecurity agent"""
    pass


@main.command()
@click.option("--target", required=True, help="Target IP or hostname to scan")
@click.option("--aggressive", is_flag=True, help="Run aggressive scan")
@click.option("--json", "output_json", is_flag=True, help="Output results as JSON")
@click.option("--llm-format", is_flag=True, help="Output in LLM-ready format")
@click.option("--analyze", is_flag=True, help="Analyze results with LLM")
@click.option("--llm", default="openai", type=click.Choice(["openai", "claude", "ollama"]), help="LLM provider to use")
@click.option("--timeout", default=60, type=int, help="Scan timeout in seconds (default: 60)")
@click.option("--confirm", "require_confirmation", is_flag=True, help="Ask for approval before scanning")
@click.option("--yes", "assume_yes", is_flag=True, help="Approve a confirmed operation non-interactively")
def scan(target, aggressive, output_json, llm_format, analyze, llm, timeout, require_confirmation, assume_yes):
    """Run security scan on target"""
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
            return

    click.echo(f"{Fore.CYAN}[*] Scanning target: {target}{Style.RESET_ALL}")
    
    # Build Nmap arguments
    if aggressive:
        arguments = "-sV -sC -p 1-1000"
        click.echo(f"{Fore.YELLOW}[*] Aggressive scan mode enabled{Style.RESET_ALL}")
    else:
        arguments = "-sV -p 1-1000"
    
    # Execute Nmap scan using NmapScanner wrapper
    scanner = NmapScanner(target)
    scanner.set_timeout(timeout)  # Set custom timeout
    
    if scanner.scan(arguments=arguments):
        click.echo(f"{Fore.GREEN}[+] Scan completed successfully!{Style.RESET_ALL}\n")
        
        # Validate structure
        if not scanner.validate_structure():
            click.echo(f"{Fore.RED}[!] Scan results failed validation{Style.RESET_ALL}")
            return
        
        # Get LLM-ready format for potential analysis
        llm_ready_data = scanner.get_llm_ready_format()
        
        # Check if any open ports were found
        open_ports = llm_ready_data.get("scan_statistics", {}).get("open_ports", 0)
        if open_ports == 0:
            click.echo(f"{Fore.YELLOW}[⚠] No open ports found on target{Style.RESET_ALL}")
        
        # Perform LLM analysis if requested
        if analyze:
            click.echo("=" * 60)
            click.echo(f"LLM SECURITY ANALYSIS ({llm.upper()})")
            click.echo("=" * 60)
            
            if open_ports == 0:
                click.echo(f"{Fore.GREEN}[+] No open ports - Low risk profile{Style.RESET_ALL}")
                click.echo("Recommendation: Continue monitoring network security posture.")
            else:
                try:
                    # Using mock analysis for now (Aditya will implement actual LLM)
                    mock_analysis = get_mock_analysis(llm_ready_data)
                    click.echo(json.dumps(mock_analysis, indent=2))
                    click.echo("\n" + "=" * 60)
                    click.echo("NOTE: Using mock analysis. Actual LLM integration pending.")
                    click.echo("=" * 60)
                except Exception as e:
                    click.echo(f"{Fore.RED}[!] Analysis failed: {e}{Style.RESET_ALL}")
            
            return
        
        # Output in requested format
        if llm_format:
            click.echo("=" * 60)
            click.echo("LLM-READY SCAN OUTPUT")
            click.echo("=" * 60)
            click.echo(json.dumps(llm_ready_data, indent=2))
        elif output_json:
            click.echo("=" * 60)
            click.echo("JSON SCAN OUTPUT")
            click.echo("=" * 60)
            click.echo(json.dumps(scanner.get_results(), indent=2))
        else:
            click.echo("=" * 60)
            click.echo("SCAN SUMMARY")
            click.echo("=" * 60)
            summary = scanner.get_summary()
            click.echo(summary)
            
            # Show statistics
            click.echo("\n" + "=" * 60)
            click.echo("SCAN STATISTICS")
            click.echo("=" * 60)
            stats = scanner.get_statistics()
            click.echo(f"Target: {stats.get('target')}")
            click.echo(f"Hosts Up: {stats.get('hosts_up')}")
            click.echo(f"Total Ports Scanned: {stats.get('total_ports_scanned')}")
            click.echo(f"Open Ports: {stats.get('open_ports_found')}")
            click.echo(f"Filtered Ports: {stats.get('filtered_ports')}")
            click.echo(f"Closed Ports: {stats.get('closed_ports')}")
            click.echo(f"Services Detected: {stats.get('services_detected')}")
    else:
        # Scan failed - provide specific error guidance
        click.echo(f"{Fore.RED}[!] Scan failed{Style.RESET_ALL}")
        
        error_msg = scanner.last_error
        if error_msg:
            click.echo(f"{Fore.YELLOW}Error: {error_msg}{Style.RESET_ALL}")
            
            # Provide specific guidance based on error type
            if "timeout" in error_msg.lower():
                click.echo("\n" + f"{Fore.CYAN}Troubleshooting Tips:{Style.RESET_ALL}")
                click.echo("1. Increase timeout: sentinelai --scan <target> --timeout 180")
                click.echo("2. Try reduced port range: sentinelai --scan <target> -p 80,443,22")
                click.echo("3. Check network connectivity: ping <target>")
            elif "unreachable" in error_msg.lower() or "down" in error_msg.lower():
                click.echo("\n" + f"{Fore.CYAN}Troubleshooting Tips:{Style.RESET_ALL}")
                click.echo("1. Verify target is online: ping <target>")
                click.echo("2. Check firewall rules")
                click.echo("3. Ensure target is accessible from your network")
            elif "permission denied" in error_msg.lower():
                click.echo("\n" + f"{Fore.CYAN}Troubleshooting Tips:{Style.RESET_ALL}")
                click.echo("1. Some Nmap options require administrator privileges")
                click.echo("2. Try running as administrator")
                click.echo("3. Use basic scan without aggressive flags")


@main.command()
@click.option("--hours", default=24, show_default=True, type=click.IntRange(min=1), help="Read events from the last N hours")
@click.option("--event-ids", multiple=True, type=int, help="Filter by event ID; may be repeated")
@click.option("--max-events", default=1000, show_default=True, type=click.IntRange(min=1), help="Maximum events to read")
@click.option("--json", "output_json", is_flag=True, help="Output events and analysis as JSON")
@click.option("--llm-format", is_flag=True, help="Output an LLM-ready event log document")
@click.option("--analyze", is_flag=True, help="Include threat analysis")
@click.option("--sample", is_flag=True, help="Use built-in sample events instead of Windows logs")
@click.option("--llm", default="openai", type=click.Choice(["openai", "claude", "ollama"]), help="LLM provider label")
def logs(hours, event_ids, max_events, output_json, llm_format, analyze, sample, llm):
    """Read, filter, and analyze Windows security events."""
    reader = EventLogReader()
    requested_ids = list(event_ids) or None

    if sample:
        events = list(SAMPLE_SECURITY_EVENTS)
        source = "sample"
        if requested_ids:
            events = [event for event in events if event.get("event_id") in requested_ids]
    else:
        events = reader.read_events(
            log_name="Security",
            max_events=max_events,
            hours_back=hours,
            event_ids=requested_ids,
        )
        source = "windows"
        if not events and reader.last_error:
            click.echo(f"{Fore.YELLOW}[!] {reader.last_error}{Style.RESET_ALL}")
            click.echo("Use --sample for a local demonstration without Windows log access.")
            return

    event_filter = EventFilter()
    critical_events = event_filter.filter_critical(events)
    analysis = event_filter.analyze_events(critical_events)
    stats = reader.get_statistics(events)
    document = {
        "log_metadata": {
            "source": source,
            "log_name": "Security",
            "hours_back": hours,
            "event_ids": requested_ids,
        },
        "events": critical_events,
        "statistics": stats,
        "analysis": analysis,
    }

    if analyze:
        document["llm_analysis"] = PromptEngine(llm).analyze_event_logs(critical_events, analysis)

    if output_json or llm_format:
        click.echo(json.dumps(document, indent=2, default=str))
        return

    click.echo(f"Events read: {len(events)} | Critical events: {len(critical_events)}")
    click.echo(f"Threat level: {analysis['threat_level']}")
    for alert in analysis["alerts"]:
        click.echo(f"[{alert['severity']}] {alert['type']}: {alert.get('description', '')}")


@main.command()
def version():
    """Show version"""
    click.echo("SentinelAI CLI v0.1.0")


if __name__ == "__main__":
    main()
