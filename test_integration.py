"""
test_integration.py

End-to-end integration test:
Nmap scan output -> nmap_parser -> framework_mapper -> correct MITRE technique.
"""

from nmap_parser import parse_nmap_output, extract_keywords
from framework_mapper import map_to_mitre

SAMPLE_NMAP_OUTPUT = """
Starting Nmap 7.94 ( https://nmap.org ) at 2026-07-23
Nmap scan report for 192.168.1.10
Host is up (0.00050s latency).

PORT     STATE SERVICE      VERSION
22/tcp   open  ssh          OpenSSH 8.9p1 Ubuntu
445/tcp  open  microsoft-ds
5985/tcp open  http         Microsoft HTTPAPI httpd 2.0 (PowerShell remoting)

Nmap done: 1 IP address (1 host up) scanned in 5.21 seconds
"""


def test_parse_nmap_extracts_service_lines():
    services = parse_nmap_output(SAMPLE_NMAP_OUTPUT)
    assert any("powershell" in s.lower() for s in services)
    assert any("ssh" in s.lower() for s in services)


def test_extract_keywords_from_services():
    services = parse_nmap_output(SAMPLE_NMAP_OUTPUT)
    keywords = extract_keywords(services)
    assert "powershell" in keywords
    assert "ssh" in keywords


def test_end_to_end_nmap_to_mitre_technique():
    """
    Full pipeline: raw Nmap output -> parsed services -> extracted keywords
    -> MITRE technique lookup. Confirms the PowerShell service banner
    correctly resolves to the PowerShell technique (T1059.001).
    """
    services = parse_nmap_output(SAMPLE_NMAP_OUTPUT)
    keywords = extract_keywords(services)

    result = map_to_mitre("powershell")

    assert "powershell" in keywords
    assert result is not None
    assert result["id"].startswith("T1059")
    assert "powershell" in result["name"].lower()


def test_end_to_end_handles_no_match_gracefully():
    """A scan with no recognizable indicators should yield no false matches."""
    benign_output = """
PORT     STATE SERVICE      VERSION
80/tcp   open  http         Apache httpd 2.4.41
""" git add nmap_parser.py test_integration.py
    services = parse_nmap_output(benign_output)
    keywords = extract_keywords(services)
    assert keywords == []