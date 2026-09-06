"""
Nmap scanner wrapper for SentinelAI
"""

import nmap
import json
import re
import logging
from typing import Dict, List, Optional
from datetime import datetime

from sentinelai.ui import error, info, success

# Configure logging (INFO: DEBUG made nmap/python-nmap spam stdout)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Scanner:
    """Base scanner class"""
    
    def __init__(self, target):
        self.target = target
        self.results = None
    
    @staticmethod
    def validate_target(target: str) -> bool:
        """Validate target format (IP, hostname, or domain)"""
        # IP address validation (IPv4)
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        # Hostname/domain validation
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        # localhost
        localhost_pattern = r'^(localhost|127\.0\.0\.1)$'
        
        return bool(re.match(ipv4_pattern, target) or 
                   re.match(domain_pattern, target) or 
                   re.match(localhost_pattern, target))
    
    def scan(self):
        """Execute scan"""
        raise NotImplementedError
    
    def get_results(self):
        """Return scan results"""
        return self.results


class NmapScanner(Scanner):
    """Nmap-based security scanner using python-nmap library"""
    
    def __init__(self, target, quiet: bool = False):
        super().__init__(target)
        # Day 24: quiet=True suppresses human status lines so machine-readable
        # paths (scan --output-json) keep stdout JSON-pure. Failures still land
        # in the logger and self.scan_errors.
        self.quiet = quiet
        
        # Validate target format
        if not self.validate_target(target):
            logger.warning(f"Target '{target}' may not be valid. Proceeding anyway...")
        
        self.nm = nmap.PortScanner()
        self.raw_output = None
        self.parsed_results = None
        self.scan_errors = []
    
    def scan(self, arguments="-sV -p 1-1000"):
        """
        Execute Nmap scan on target
        
        Args:
            arguments (str): Nmap command-line arguments
                            Default: "-sV -p 1-1000" (Service detection on common ports)
        
        Returns:
            bool: True if scan successful, False otherwise
        """
        try:
            logger.info("Scanning target: %s", self.target)
            logger.info("Using arguments: %s", arguments)
            # The CLI already announces the target; only add the arguments here.
            if not self.quiet:
                info(f"Using arguments: {arguments}")
            
            self.nm.scan(self.target, arguments=arguments)
            
            # Check if scan found any hosts
            if not self.nm.all_hosts():
                error_msg = f"No hosts found for target: {self.target}"
                logger.warning(error_msg)
                if not self.quiet:
                    error(error_msg)
                self.scan_errors.append("No hosts found")
                return False
            
            self.raw_output = self.nm.csv()
            self.parse_results()
            logger.info("[+] Scan completed successfully")
            return True
            
        except nmap.PortScannerError as e:
            logger.error("Nmap error: %s", e)
            if not self.quiet:
                error(f"Nmap error: {e}")
            self.scan_errors.append(str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error: %s", e)
            if not self.quiet:
                error(f"Unexpected error: {e}")
            self.scan_errors.append(str(e))
            return False
    
    def parse_results(self) -> Dict:
        """
        Parse Nmap results into comprehensive structured format
        LLM-ready output with detailed host, ports, and services information
        
        Returns:
            dict: Structured scan results with metadata and detailed port/service info
        """
        scan_start_time = datetime.now().isoformat()
        
        self.parsed_results = {
            "metadata": {
                "target": self.target,
                "scan_timestamp": scan_start_time,
                "scan_type": "nmap_security_scan"
            },
            "summary": {
                "total_hosts_scanned": 0,
                "total_hosts_up": 0,
                "total_ports_scanned": 0,
                "total_open_ports": 0,
                "total_closed_ports": 0,
                "total_filtered_ports": 0
            },
            "hosts": []
        }
        
        try:
            hosts_list = self.nm.all_hosts()
            self.parsed_results["summary"]["total_hosts_scanned"] = len(hosts_list)
            
            for host in hosts_list:
                host_state = self.nm[host].state()
                if host_state == "up":
                    self.parsed_results["summary"]["total_hosts_up"] += 1
                
                host_info = {
                    "address": host,
                    "status": host_state,
                    "hostnames": [],
                    "ports": [],
                    "services": {},
                    "protocol_summary": {}
                }
                
                # Collect hostnames if available
                try:
                    if self.nm[host].hostnames():
                        host_info["hostnames"] = [h for h in self.nm[host].hostnames() if h]
                except:
                    pass
                
                # Process all protocols (tcp, udp, etc.)
                for proto in self.nm[host].all_protocols():
                    proto_ports = []
                    open_count = 0
                    closed_count = 0
                    filtered_count = 0
                    
                    ports = self.nm[host][proto].keys()
                    for port in sorted(ports):
                        port_data = self.nm[host][proto][port]
                        state = port_data["state"]
                        
                        # Update port state counters
                        if state == "open":
                            open_count += 1
                            self.parsed_results["summary"]["total_open_ports"] += 1
                        elif state == "closed":
                            closed_count += 1
                            self.parsed_results["summary"]["total_closed_ports"] += 1
                        elif state == "filtered":
                            filtered_count += 1
                            self.parsed_results["summary"]["total_filtered_ports"] += 1
                        
                        self.parsed_results["summary"]["total_ports_scanned"] += 1
                        
                        port_info = {
                            "port": int(port),
                            "protocol": proto,
                            "state": state,
                            "service": {
                                "name": port_data.get("name", "unknown"),
                                "product": port_data.get("product", ""),
                                "version": port_data.get("version", ""),
                                "extrainfo": port_data.get("extrainfo", "")
                            }
                        }
                        
                        # Build full service string for easy consumption
                        service_str = port_data.get("name", "unknown")
                        if port_data.get("product"):
                            service_str += f" ({port_data['product']}"
                            if port_data.get("version"):
                                service_str += f" {port_data['version']}"
                            service_str += ")"
                        if port_data.get("extrainfo"):
                            service_str += f" - {port_data['extrainfo']}"
                        
                        port_info["service_string"] = service_str
                        
                        # Add to ports list
                        host_info["ports"].append(port_info)
                        
                        # Build services dict organized by port
                        host_info["services"][f"{port}/{proto}"] = {
                            "state": state,
                            "name": port_data.get("name", "unknown"),
                            "full_info": service_str
                        }
                        
                        proto_ports.append(port_info)
                    
                    # Protocol summary
                    host_info["protocol_summary"][proto] = {
                        "open": open_count,
                        "closed": closed_count,
                        "filtered": filtered_count,
                        "total_scanned": len(ports)
                    }
                
                self.parsed_results["hosts"].append(host_info)
                
        except Exception as e:
            if not self.quiet:
                error(f"Error parsing results: {e}")
            logger.error(f"Parse error: {str(e)}")
        
        return self.parsed_results
    
    def get_results(self) -> Dict:
        """Return parsed scan results"""
        return self.parsed_results
    
    def get_open_ports(self) -> List[Dict]:
        """Get list of all open ports found in a structured format"""
        open_ports = []
        if not self.parsed_results:
            return open_ports
            
        for host in self.parsed_results.get("hosts", []):
            for port_info in host.get("ports", []):
                if port_info["state"] == "open":
                    open_ports.append({
                        "host": host["address"],
                        "port": port_info["port"],
                        "protocol": port_info["protocol"],
                        "service": port_info["service"]["name"],
                        "product": port_info["service"]["product"],
                        "version": port_info["service"]["version"],
                        "service_string": port_info.get("service_string", "")
                    })
        return open_ports
    
    def get_summary(self) -> str:
        """Get human-readable summary of scan with detailed statistics"""
        if not self.parsed_results:
            return "[!] No scan results available. Scan may have failed or no hosts were found."
        
        if not self.parsed_results.get("hosts"):
            return f"[!] No hosts found for target: {self.target}"
        
        summary = []
        
        # Add header with metadata
        summary.append(f"Scan Target: {self.target}")
        summary.append(f"Scan Time: {self.parsed_results['metadata']['scan_timestamp']}")
        summary.append("")
        
        # Add scan summary statistics
        stats = self.parsed_results["summary"]
        summary.append("SCAN STATISTICS")
        summary.append("=" * 60)
        summary.append(f"Total Hosts Scanned: {stats['total_hosts_scanned']}")
        summary.append(f"Total Hosts Up: {stats['total_hosts_up']}")
        summary.append(f"Total Ports Scanned: {stats['total_ports_scanned']}")
        summary.append(f"Open Ports: {stats['total_open_ports']} | Closed: {stats['total_closed_ports']} | Filtered: {stats['total_filtered_ports']}")
        summary.append("")
        
        # Add host details
        summary.append("HOST DETAILS")
        summary.append("=" * 60)
        
        for host in self.parsed_results.get("hosts", []):
            summary.append(f"\nHost: {host['address']} ({host['status']})")
            
            if host.get("hostnames"):
                summary.append(f"  Hostnames: {', '.join(host['hostnames'])}")
            
            # Protocol summary
            for proto, proto_stats in host.get("protocol_summary", {}).items():
                summary.append(f"\n  {proto.upper()} Protocol:")
                summary.append(f"    Open: {proto_stats['open']} | Closed: {proto_stats['closed']} | Filtered: {proto_stats['filtered']}")
            
            # List open ports with service details
            open_ports = [p for p in host.get("ports", []) if p["state"] == "open"]
            if open_ports:
                summary.append("  Open Ports:")
                for port in open_ports:
                    summary.append(f"    {port['port']}/{port['protocol']}: {port['service_string']}")
            else:
                summary.append("  No open ports found")
        
        return "\n".join(summary) if summary else "[!] No scan information available"
    
    def export_json(self, filepath: str) -> bool:
        """Export results to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.parsed_results, f, indent=2)
            success(f"Results exported to: {filepath}")
            logger.info(f"Results exported to {filepath}")
            return True
        except Exception as e:
            error(f"Error exporting to JSON: {e}")
            logger.error(f"JSON export failed: {str(e)}")
            return False
    
    def to_json_string(self) -> str:
        """Get results as JSON string"""
        if not self.parsed_results:
            return json.dumps({"error": "No scan results available"}, indent=2)
        return json.dumps(self.parsed_results, indent=2)
    
    def get_json_dict(self) -> Dict:
        """Get results as dictionary for programmatic use"""
        return self.parsed_results if self.parsed_results else {}
