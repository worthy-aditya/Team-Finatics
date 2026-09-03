"""
Nmap scanner wrapper for SentinelAI
"""

import nmap
import json
from typing import Dict, List, Optional
from datetime import datetime


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
        self.scan_timeout = 60  # Default timeout in seconds
        self.last_error = None
    
    def set_timeout(self, timeout: int):
        """Set scan timeout in seconds"""
        self.scan_timeout = timeout
    
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
            print(f"[*] Timeout: {self.scan_timeout} seconds")
            
            # Validate target format
            if not self._validate_target(self.target):
                self.last_error = f"Invalid target format: {self.target}"
                print(f"[!] {self.last_error}")
                return False
            
            self.nm.scan(self.target, arguments=arguments, timeout=self.scan_timeout)
            self.raw_output = self.nm.csv()
            self.parse_results()
            return True
            
        except nmap.PortScannerTimeoutExpired:
            self.last_error = f"Scan timeout exceeded ({self.scan_timeout}s) for target {self.target}"
            print(f"[!] {self.last_error}")
            print("[*] Tip: Use --timeout flag to increase scan duration for external targets")
            return False
        except nmap.PortScannerHostDown:
            self.last_error = f"Target host {self.target} is down or unreachable"
            print(f"[!] {self.last_error}")
            print("[*] Tip: Verify target is online and reachable from your network")
            return False
        except nmap.PortScannerError as e:
            self.last_error = f"Nmap error: {e}"
            print(f"[!] {self.last_error}")
            if "Permission denied" in str(e):
                print("[*] Tip: Some Nmap options require elevated privileges")
            return False
        except Exception as e:
            self.last_error = f"Unexpected error: {e}"
            print(f"[!] {self.last_error}")
            return False
    
    def _validate_target(self, target: str) -> bool:
        """
        Validate target format
        
        Args:
            target (str): Target IP or hostname
        
        Returns:
            bool: True if target format is valid
        """
        import re
        
        # Valid formats: IP address, hostname, CIDR notation
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        hostname_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$'
        cidr_pattern = r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$'
        localhost_pattern = r'^localhost$'
        
        patterns = [ip_pattern, hostname_pattern, cidr_pattern, localhost_pattern]
        
        for pattern in patterns:
            if re.match(pattern, target):
                return True
        
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
            # Handle case where no hosts were found
            if not self.nm.all_hosts():
                self.last_error = "No hosts found or target is unreachable"
                print("[!] No hosts were discovered during scan")
                return self.parsed_results
            
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
            self.last_error = f"Error parsing results: {e}"
            print(f"[!] {self.last_error}")
        
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
    
    def get_statistics(self) -> Dict:
        """Get scan statistics and summary metrics"""
        if not self.parsed_results:
            return {}
        
        stats = {
            "scan_timestamp": datetime.now().isoformat(),
            "target": self.target,
            "total_hosts": len(self.parsed_results.get("hosts", [])),
            "hosts_up": 0,
            "total_ports_scanned": 0,
            "open_ports_found": 0,
            "filtered_ports": 0,
            "closed_ports": 0,
            "services_detected": 0,
            "critical_services": []
        }
        
        critical_keywords = ["microsoft-ds", "ssh", "telnet", "ftp", "http", "smtp", "rdp"]
        
        for host in self.parsed_results.get("hosts", []):
            if host["status"] == "up":
                stats["hosts_up"] += 1
            
            for proto, ports in host.get("protocols", {}).items():
                stats["total_ports_scanned"] += len(ports)
                
                for port in ports:
                    if port["state"] == "open":
                        stats["open_ports_found"] += 1
                        if port.get("name"):
                            stats["services_detected"] += 1
                            # Check for critical services
                            service_name = port.get("name", "").lower()
                            if any(kw in service_name for kw in critical_keywords):
                                stats["critical_services"].append({
                                    "host": host["ip"],
                                    "port": port["port"],
                                    "service": port.get("name", "unknown"),
                                    "product": port.get("product", "")
                                })
                    elif port["state"] == "filtered":
                        stats["filtered_ports"] += 1
                    elif port["state"] == "closed":
                        stats["closed_ports"] += 1
        
        return stats
    
    def get_llm_ready_format(self) -> Dict:
        """
        Get structured output optimized for LLM analysis
        
        Returns:
            dict: Formatted data ready for passing to LLM prompt module
        """
        if not self.parsed_results:
            return {"error": "No scan results available"}
        
        # Check if any hosts were found
        hosts = self.parsed_results.get("hosts", [])
        if not hosts:
            return {
                "scan_metadata": {
                    "target": self.target,
                    "scan_time": datetime.now().isoformat(),
                    "summary": f"Target {self.target} is unreachable or offline"
                },
                "scan_statistics": {
                    "hosts_up": 0,
                    "total_ports_scanned": 0,
                    "open_ports": 0,
                    "filtered_ports": 0,
                    "closed_ports": 0,
                    "services_detected": 0
                },
                "error": "No hosts found - target may be offline or unreachable",
                "discovered_services": [],
                "open_ports_detail": [],
                "risk_assessment": {
                    "risk_level": "UNKNOWN",
                    "critical_services": [],
                    "recommendation": "Unable to assess security posture. Verify target is online and reachable."
                }
            }
        
        stats = self.get_statistics()
        
        # Build LLM-friendly format
        llm_format = {
            "scan_metadata": {
                "target": self.target,
                "scan_time": stats.get("scan_timestamp"),
                "summary": f"Scanned {stats.get('target')} | Found {stats.get('open_ports_found')} open ports on {stats.get('hosts_up')} host(s)"
            },
            "scan_statistics": {
                "hosts_up": stats.get("hosts_up"),
                "total_ports_scanned": stats.get("total_ports_scanned"),
                "open_ports": stats.get("open_ports_found"),
                "filtered_ports": stats.get("filtered_ports"),
                "closed_ports": stats.get("closed_ports"),
                "services_detected": stats.get("services_detected")
            },
            "discovered_services": [],
            "open_ports_detail": [],
            "risk_assessment": {
                "risk_level": self._calculate_risk_level(stats),
                "critical_services": stats.get("critical_services", []),
                "recommendation": self._get_recommendation(stats)
            }
        }
        
        # Extract discovered services and open ports
        for host in self.parsed_results.get("hosts", []):
            for proto, ports in host.get("protocols", {}).items():
                for port in ports:
                    if port["state"] == "open":
                        service_entry = {
                            "host": host["ip"],
                            "port": port["port"],
                            "protocol": proto,
                            "service_name": port.get("name", "unknown"),
                            "product": port.get("product", ""),
                            "version": port.get("version", ""),
                            "extra_info": port.get("extrainfo", "")
                        }
                        llm_format["open_ports_detail"].append(service_entry)
                        
                        # Add to discovered services if not already there
                        if port.get("name"):
                            service_dict = {
                                "name": port.get("name"),
                                "product": port.get("product", ""),
                                "version": port.get("version", ""),
                                "count": 1
                            }
                            if service_dict not in llm_format["discovered_services"]:
                                llm_format["discovered_services"].append(service_dict)
        
        return llm_format
    
    def _calculate_risk_level(self, stats: Dict) -> str:
        """Calculate risk level based on scan statistics"""
        critical_count = len(stats.get("critical_services", []))
        open_ports = stats.get("open_ports_found", 0)
        
        if critical_count >= 3 or open_ports >= 10:
            return "CRITICAL"
        elif critical_count >= 2 or open_ports >= 5:
            return "HIGH"
        elif critical_count >= 1 or open_ports >= 1:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_recommendation(self, stats: Dict) -> str:
        """Get security recommendation based on findings"""
        critical_count = len(stats.get("critical_services", []))
        open_ports = stats.get("open_ports_found", 0)
        
        if critical_count >= 2:
            return "URGENT: Multiple critical services exposed. Implement firewall rules immediately."
        elif critical_count >= 1:
            return "WARNING: Critical service detected. Review access controls and consider service hardening."
        elif open_ports >= 5:
            return "CAUTION: Multiple open ports found. Verify all are necessary and properly secured."
        elif open_ports >= 1:
            return "INFO: Open port(s) detected. Ensure services are up-to-date and properly configured."
        else:
            return "GOOD: No open ports detected on scanned range."
    
    def validate_structure(self) -> bool:
        """
        Validate that parsed results have correct structure
        
        Returns:
            bool: True if structure is valid, False otherwise
        """
        if not self.parsed_results:
            print("[!] No parsed results available")
            return False
        
        # Check required top-level keys
        required_keys = ["target", "scan_status", "hosts"]
        for key in required_keys:
            if key not in self.parsed_results:
                print(f"[!] Missing required key: {key}")
                return False
        
        # Check hosts structure
        hosts = self.parsed_results.get("hosts", [])
        if not isinstance(hosts, list):
            print("[!] 'hosts' must be a list")
            return False
        
        for host in hosts:
            if not isinstance(host, dict):
                print("[!] Each host must be a dictionary")
                return False
            
            required_host_keys = ["ip", "status", "protocols"]
            for key in required_host_keys:
                if key not in host:
                    print(f"[!] Host missing required key: {key}")
                    return False
        
        print("[+] Structure validation passed")
        return True
