# SentinelAI — Team Finatics

Maps security-related keywords and Nmap scan output to standardized
**OWASP Top 10:2025** categories and **MITRE ATT&CK** techniques
(Enterprise, Mobile, and ICS matrices) — built for students, bug bounty
hunters, red/blue teams, and enterprise security teams.

## Features

- 🔎 **OWASP Mapper** — maps a keyword (e.g. `"sql injection"`) to its OWASP Top 10:2025 category
- 🎯 **MITRE ATT&CK Mapper** — maps a keyword (e.g. `"phishing"`) to its MITRE technique (T-number), across Enterprise, Mobile, and ICS
- 🧩 **Framework Mapper** — one call returns both OWASP and MITRE results at once
- 🛰️ **Nmap Integration** — parses raw Nmap scan output and automatically maps discovered services to likely MITRE techniques
- ✅ Fully tested with `pytest` (23+ passing tests, including a full end-to-end integration test)

## Project Structure

```
Team-Finatics/
├── data/
│   ├── owasp_top10.json          # OWASP Top 10:2025 dataset
│   ├── owasp_notes.md            # Notes on the OWASP data structure
│   ├── enterprise-attack.json    # MITRE ATT&CK Enterprise STIX data
│   ├── mobile-attack.json        # MITRE ATT&CK Mobile STIX data
│   └── ics-attack.json           # MITRE ATT&CK ICS STIX data
├── owasp_mapper.py                # Keyword -> OWASP category mapping
├── mitre_mapper.py                # Keyword -> MITRE technique mapping
├── framework_mapper.py            # Combined OWASP + MITRE mapper
├── nmap_parser.py                 # Nmap output parsing + keyword extraction
├── test_owasp_mapper.py
├── test_mitre_mapper.py
├── test_integration.py            # End-to-end Nmap -> MITRE test
├── requirements.txt
└── README.md
```

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/worthy-aditya/Team-Finatics.git
   cd Team-Finatics
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

   *(If `requirements.txt` isn't present yet, `pip install pytest` covers the current dependency set.)*

## Quick Start — First Command

Once installed, try the combined mapper directly from the command line:

```bash
python framework_mapper.py
```

You should see output like:

```
Keyword: 'sql injection'
  OWASP -> A05:2025 Injection
  MITRE -> No match

Keyword: 'phishing'
  OWASP -> No match
  MITRE -> T1566 Phishing [enterprise]

Keyword: 'misconfiguration'
  OWASP -> A02:2025 Security Misconfiguration
  MITRE -> No match

Keyword: 'powershell'
  OWASP -> No match
  MITRE -> T1059.001 PowerShell [enterprise]
```

## Usage Example (as a library)

```python
from framework_mapper import map_keyword

result = map_keyword("sql injection")
print(result["owasp"]["rank"], result["owasp"]["name"])
# A05:2025 Injection

result = map_keyword("phishing")
print(result["mitre"]["id"], result["mitre"]["name"])
# T1566 Phishing
```

### Nmap Integration Example

```python
from nmap_parser import parse_nmap_output, extract_keywords
from framework_mapper import map_to_mitre

nmap_output = """
PORT     STATE SERVICE      VERSION
22/tcp   open  ssh          OpenSSH 8.9p1 Ubuntu
5985/tcp open  http         Microsoft HTTPAPI httpd 2.0 (PowerShell remoting)
"""

services = parse_nmap_output(nmap_output)
keywords = extract_keywords(services)          # ['ssh', 'powershell']

for kw in keywords:
    technique = map_to_mitre(kw)
    if technique:
        print(f"{kw} -> {technique['id']} {technique['name']}")

# ssh -> T1021.004 Remote Services: SSH
# powershell -> T1059.001 PowerShell
```

## Running Tests

```bash
pytest -v
```

Expected: all tests pass, including OWASP mapper tests, MITRE mapper tests, and the end-to-end Nmap-to-MITRE integration test.

## Data Sources

- [OWASP Top 10:2025](https://owasp.org/Top10/2025/)
- [MITRE ATT&CK (cti repository)](https://github.com/mitre/cti)

## Team

| Name | Focus Area |
|---|---|
| Sneha Das | OWASP Mapping, MITRE Mapping, Testing & Documentation |