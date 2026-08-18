import click
import json
import os
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

@click.command()
@click.option("--input", "-i", required=False, help="Input JSON scan file")
@click.option("--output", "-o", default="scan_report", help="Output report filename (without extension)")
@click.option("--format", "-f", type=click.Choice(["text", "json", "csv"]), default="text", help="Output format")
def report(input, output, format):
    """Generate security scan reports from saved Nmap scans."""
    
    # If no input provided, try to find most recent scan file
    if not input:
        json_files = [f for f in os.listdir(".") if f.startswith("scan_") and f.endswith(".json")]
        if not json_files:
            click.echo(f"{Fore.RED}[!] No scan JSON files found. Run 'sentinelai scan --target <IP>' first.{Style.RESET_ALL}")
            return
        input = sorted(json_files)[-1]  # Get most recent
        click.echo(f"{Fore.CYAN}[*] Using most recent scan file: {input}{Style.RESET_ALL}")
    
    # Load scan data
    try:
        with open(input, 'r') as f:
            scan_data = json.load(f)
        click.echo(f"{Fore.GREEN}[+] Loaded scan data from {input}{Style.RESET_ALL}")
    except FileNotFoundError:
        click.echo(f"{Fore.RED}[!] File not found: {input}{Style.RESET_ALL}")
        return
    except json.JSONDecodeError:
        click.echo(f"{Fore.RED}[!] Invalid JSON file: {input}{Style.RESET_ALL}")
        return
    
    # Generate report based on format
    if format == "text":
        _generate_text_report(scan_data, output)
    elif format == "json":
        _generate_json_report(scan_data, output)
    elif format == "csv":
        _generate_csv_report(scan_data, output)
    
    click.echo(f"{Fore.GREEN}[+] Report generated successfully!{Style.RESET_ALL}")


def _generate_text_report(scan_data, output_base):
    """Generate text format report"""
    filename = f"{output_base}.txt"
    
    with open(filename, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("SENTINELAI NETWORK SCAN REPORT\n")
        f.write("=" * 70 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Target: {scan_data.get('target', 'Unknown')}\n")
        f.write("=" * 70 + "\n\n")
        
        hosts = scan_data.get('hosts', [])
        if not hosts:
            f.write("[!] No hosts found in scan data\n")
            return
        
        for host in hosts:
            f.write(f"Host: {host['ip']} ({host['status']})\n")
            f.write("-" * 70 + "\n")
            
            protocols = host.get('protocols', {})
            for proto, ports in protocols.items():
                open_ports = [p for p in ports if p['state'] == 'open']
                if open_ports:
                    f.write(f"\n{proto.upper()} Protocol:\n")
                    for port in open_ports:
                        f.write(f"  Port {port['port']}: {port['state'].upper()}\n")
                        f.write(f"    Service: {port['name']}\n")
                        if port.get('product'):
                            f.write(f"    Product: {port['product']}\n")
                        if port.get('version'):
                            f.write(f"    Version: {port['version']}\n")
                        f.write("\n")
            f.write("\n")
        
        f.write("=" * 70 + "\n")
        f.write("End of Report\n")
    
    click.echo(f"  Saved to: {filename}")


def _generate_json_report(scan_data, output_base):
    """Generate JSON format report"""
    filename = f"{output_base}.json"
    
    report = {
        "generated": datetime.now().isoformat(),
        "target": scan_data.get('target'),
        "scan_summary": {},
        "details": scan_data
    }
    
    # Add summary
    for host in scan_data.get('hosts', []):
        total_open = 0
        for proto, ports in host.get('protocols', {}).items():
            total_open += sum(1 for p in ports if p['state'] == 'open')
        report['scan_summary'][host['ip']] = {'status': host['status'], 'open_ports': total_open}
    
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    click.echo(f"  Saved to: {filename}")


def _generate_csv_report(scan_data, output_base):
    """Generate CSV format report"""
    filename = f"{output_base}.csv"
    
    with open(filename, 'w') as f:
        f.write("IP,Status,Protocol,Port,State,Service,Product,Version\n")
        
        for host in scan_data.get('hosts', []):
            ip = host['ip']
            status = host['status']
            
            for proto, ports in host.get('protocols', {}).items():
                for port in ports:
                    f.write(f'{ip},{status},{proto},{port["port"]},{port["state"]},{port["name"]},{port.get("product", "")},{port.get("version", "")}\n')
    
    click.echo(f"  Saved to: {filename}")
