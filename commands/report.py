import click
import json
import os
from datetime import datetime

from sentinelai.ui import error, info, success

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
            error("No scan JSON files found. Run 'sentinelai scan --target <IP>' first.")
            return
        input = sorted(json_files)[-1]  # Get most recent
        info(f"Using most recent scan file: {input}")
    
    # Load scan data
    try:
        with open(input, 'r') as f:
            scan_data = json.load(f)
        success(f"Loaded scan data from {input}")
    except FileNotFoundError:
        error(f"File not found: {input}")
        return
    except json.JSONDecodeError:
        error(f"Invalid JSON file: {input}")
        return
    
    # Generate report based on format
    if format == "text":
        _generate_text_report(scan_data, output)
    elif format == "json":
        _generate_json_report(scan_data, output)
    elif format == "csv":
        _generate_csv_report(scan_data, output)
    
    success("Report generated successfully!")


def _normalize_scan(scan_data):
    """Yield (ip, status, rows) for BOTH scan schema generations.

    Week-1 schema:  host = {ip, status, protocols: {tcp: [{port, state, name,
                    product, version, extrainfo}]}}
    Current schema (Week 2+, NmapScanner.parse_results): host = {address,
                    status, hostnames, ports: [{port, protocol, state,
                    service: {name, product, version}, service_string}]}
    Found by the Day 25 E2E test: report.py crashed with KeyError 'ip' on
    current-schema files because it only understood the Week-1 layout.
    """
    for host in scan_data.get("hosts", []):
        ip = host.get("address") or host.get("ip") or "unknown"
        status = host.get("status", "unknown")
        rows = []
        if isinstance(host.get("ports"), list) and host["ports"]:
            for p in host["ports"]:
                svc = p.get("service") if isinstance(p.get("service"), dict) else {}
                rows.append({
                    "proto": p.get("protocol", "tcp"),
                    "port": p.get("port"),
                    "state": p.get("state", "unknown"),
                    "name": svc.get("name", "") or (p.get("service_string") or "").strip(),
                    "product": svc.get("product", ""),
                    "version": svc.get("version", ""),
                })
        else:
            for proto, ports in (host.get("protocols") or {}).items():
                for p in ports or []:
                    rows.append({
                        "proto": proto,
                        "port": p.get("port"),
                        "state": p.get("state", "unknown"),
                        "name": p.get("name", ""),
                        "product": p.get("product", ""),
                        "version": p.get("version", ""),
                    })
        yield ip, status, rows


def _generate_text_report(scan_data, output_base):
    """Generate text format report"""
    filename = f"{output_base}.txt"
    
    with open(filename, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("SENTINELAI NETWORK SCAN REPORT\n")
        f.write("=" * 70 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Target: {scan_data.get('target', scan_data.get('metadata', {}).get('target', 'Unknown'))}\n")
        f.write("=" * 70 + "\n\n")
        
        wrote_any = False
        for ip, status, rows in _normalize_scan(scan_data):
            wrote_any = True
            f.write(f"Host: {ip} ({status})\n")
            f.write("-" * 70 + "\n")
            
            current_proto = None
            for row in rows:
                if row["state"] != "open":
                    continue
                if row["proto"] != current_proto:
                    current_proto = row["proto"]
                    f.write(f"\n{current_proto.upper()} Protocol:\n")
                f.write(f"  Port {row['port']}: {row['state'].upper()}\n")
                f.write(f"    Service: {row['name']}\n")
                if row["product"]:
                    f.write(f"    Product: {row['product']}\n")
                if row["version"]:
                    f.write(f"    Version: {row['version']}\n")
                f.write("\n")
            f.write("\n")
        
        if not wrote_any:
            f.write("[!] No hosts found in scan data\n")
        
        f.write("=" * 70 + "\n")
        f.write("End of Report\n")
    
    success(f"Saved report to {filename}")


def _generate_json_report(scan_data, output_base):
    """Generate JSON format report"""
    filename = f"{output_base}.json"
    
    report = {
        "generated": datetime.now().isoformat(),
        "target": scan_data.get('target', scan_data.get('metadata', {}).get('target')),
        "scan_summary": {},
        "details": scan_data
    }
    
    # Add summary (works for both Week-1 and current scan schemas)
    for ip, status, rows in _normalize_scan(scan_data):
        open_ports = sum(1 for r in rows if r["state"] == "open")
        report['scan_summary'][ip] = {'status': status, 'open_ports': open_ports}
    
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    success(f"Saved report to {filename}")


def _generate_csv_report(scan_data, output_base):
    """Generate CSV format report"""
    filename = f"{output_base}.csv"
    
    with open(filename, 'w') as f:
        f.write("IP,Status,Protocol,Port,State,Service,Product,Version\n")
        
        for ip, status, rows in _normalize_scan(scan_data):
            for r in rows:
                f.write(f'{ip},{status},{r["proto"]},{r["port"]},{r["state"]},'
                        f'{r["name"]},{r["product"]},{r["version"]}\n')
    
    success(f"Saved report to {filename}")
