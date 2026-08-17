"""
Nmap scanner wrapper for SentinelAI
"""

import nmap
import json
from typing import Dict, List, Optional


class Scanner:
    """Base scanner class"""
    
    def __init__(self, target):
        self.target = target
        self.results = None
    
    def scan(self):
        """Execute scan"""
        raise NotImplementedError
    
    def get_results(self):
        """Return scan results"""
        return self.results


class NmapScanner(Scanner):
    """Nmap-based security scanner using python-nmap library"""
    
    def __init__(self, target):
        super().__init__(target)
        self.nm = nmap.PortScanner()
        self.raw_output = None
        self.parsed_results = None
    
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
            print(f"[*] Scanning target: {self.target}")
            print(f"[*] Using arguments: {arguments}")
            
            self.nm.scan(self.target, arguments=arguments)
            self.raw_output = self.nm.csv()
            self.parse_results()
            return True
            
        except nmap.PortScannerError as e:
            print(f"[!] Nmap error: {e}")
            return False
        except Exception as e:
            print(f"[!] Unexpected error: {e}")
            return False
    
    def parse_results(self) -> Dict:
        """
        Parse Nmap results into structured format
        
        Returns:
            dict: Structured scan results with hosts, ports, and services
        """
        self.parsed_results = {
            "target": self.target,
            "scan_status": {},
            "hosts": []
        }
        
        try:
            for host in self.nm.all_hosts():
                host_info = {
                    "ip": host,
                    "status": self.nm[host].state(),
                    "protocols": {}
                }
                
                for proto in self.nm[host].all_protocols():
                    host_info["protocols"][proto] = []
                    
                    ports = self.nm[host][proto].keys()
                    for port in sorted(ports):
                        port_info = {
                            "port": port,
                            "state": self.nm[host][proto][port]["state"],
                            "name": self.nm[host][proto][port].get("name", ""),
                            "product": self.nm[host][proto][port].get("product", ""),
                            "version": self.nm[host][proto][port].get("version", ""),
                            "extrainfo": self.nm[host][proto][port].get("extrainfo", "")
                        }
                        host_info["protocols"][proto].append(port_info)
                
                self.parsed_results["hosts"].append(host_info)
                
        except Exception as e:
            print(f"[!] Error parsing results: {e}")
        
        return self.parsed_results
    
    def get_results(self) -> Dict:
        """Return parsed scan results"""
        return self.parsed_results
    
    def get_open_ports(self) -> List[Dict]:
        """Get list of all open ports found"""
        open_ports = []
        if not self.parsed_results:
            return open_ports
            
        for host in self.parsed_results.get("hosts", []):
            for proto, ports in host.get("protocols", {}).items():
                for port in ports:
                    if port["state"] == "open":
                        open_ports.append({
                            "host": host["ip"],
                            "port": port["port"],
                            "protocol": proto,
                            "service": port["name"],
                            "product": port["product"],
                            "version": port["version"]
                        })
        return open_ports
    
    def get_summary(self) -> str:
        """Get human-readable summary of scan"""
        if not self.parsed_results:
            return "No scan results available"
        
        summary = []
        summary.append(f"Target: {self.target}")
        
        for host in self.parsed_results.get("hosts", []):
            summary.append(f"Host: {host['ip']} ({host['status']})")
            
            for proto, ports in host.get("protocols", {}).items():
                open_count = sum(1 for p in ports if p["state"] == "open")
                filtered_count = sum(1 for p in ports if p["state"] == "filtered")
                closed_count = sum(1 for p in ports if p["state"] == "closed")
                
                summary.append(f"  {proto.upper()}: {open_count} open, {filtered_count} filtered, {closed_count} closed")
                
                # List open ports
                for port in ports:
                    if port["state"] == "open":
                        service_info = f"{port['name']}"
                        if port['product']:
                            service_info += f" ({port['product']}"
                            if port['version']:
                                service_info += f" {port['version']}"
                            service_info += ")"
                        summary.append(f"    Port {port['port']}/{proto}: {port['state'].upper()} - {service_info}")
        
        return "\n".join(summary)
    
    def export_json(self, filepath: str) -> bool:
        """Export results to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.parsed_results, f, indent=2)
            print(f"[+] Results exported to: {filepath}")
            return True
        except Exception as e:
            print(f"[!] Error exporting to JSON: {e}")
            return False
