"""
nmap_parser.py

Parses raw Nmap scan output (default `-sV` service-detection format) and
extracts known threat-relevant keywords (e.g. "powershell", "ssh", "ftp")
that can be fed into framework_mapper for MITRE/OWASP lookups.
"""

import re

# Short, known indicator terms we watch for inside Nmap service banners.
# Kept short/single-concept so they match cleanly against MITRE technique
# names (e.g. "powershell" -> "PowerShell" sub-technique).
KNOWN_INDICATORS = [
    "powershell",
    "remote desktop",
    "rdp",
    "ssh",
    "ftp",
    "smb",
    "telnet",
    "vnc",
    "phishing",
]

_PORT_LINE_RE = re.compile(r'^\d+/(tcp|udp)\s+open\s+\S+\s*(.*)$')


def parse_nmap_output(output_text):
    """
    Extract the service/version description from each open-port line in
    Nmap output.

    Example input line:
        "5985/tcp open  http   Microsoft HTTPAPI httpd 2.0 (PowerShell remoting)"
    Returns:
        ["Microsoft HTTPAPI httpd 2.0 (PowerShell remoting)"]
    """
    services = []
    for line in output_text.splitlines():
        line = line.strip()
        match = _PORT_LINE_RE.match(line)
        if match:
            info = match.group(2).strip()
            if info:
                services.append(info)
    return services


def extract_keywords(service_lines):
    """
    Scan a list of service description strings and return the known
    indicator keywords found within them (deduplicated, order preserved).
    """
    found = []
    for line in service_lines:
        lower = line.lower()
        for indicator in KNOWN_INDICATORS:
            if indicator in lower and indicator not in found:
                found.append(indicator)
    return found


if __name__ == "__main__":
    sample = """
Starting Nmap 7.94 ( https://nmap.org )
Nmap scan report for 192.168.1.10
PORT     STATE SERVICE      VERSION
22/tcp   open  ssh          OpenSSH 8.9p1 Ubuntu
445/tcp  open  microsoft-ds
5985/tcp open  http         Microsoft HTTPAPI httpd 2.0 (PowerShell remoting)
Nmap done: 1 IP address (1 host up) scanned in 5.21 seconds
"""
    services = parse_nmap_output(sample)
    print("Services found:", services)
    print("Keywords extracted:", extract_keywords(services))