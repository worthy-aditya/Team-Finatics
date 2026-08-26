# SentinelAI — Team Finatics

Maps security-related keywords, Nmap scan output, and security event logs to
standardized **OWASP Top 10:2025** categories and **MITRE ATT&CK** techniques
(Enterprise, Mobile, and ICS matrices), generates AI-powered analysis, and
provides concrete remediation guidance — built for students, bug bounty
hunters, red/blue teams, and enterprise security teams.

## Features

- **OWASP Mapper** — maps a keyword (e.g. `"sql injection"`) to its OWASP Top 10:2025 category
- **MITRE ATT&CK Mapper** — maps a keyword (e.g. `"phishing"`) to its MITRE technique (T-number), across Enterprise, Mobile, and ICS
- **Framework Mapper** — one call returns both OWASP and MITRE results at once
- **Nmap Integration** — parses raw Nmap scan output and maps discovered services to OWASP/MITRE
- **Event Log Integration** — parses security event logs, including pattern-based inference (e.g. repeated failed logons inferred as brute force)
- **AI-Powered Analysis** — Google Gemini generates natural-language security analysis, with automatic offline rule-based fallback if the API is unavailable
- **Remediation Mapper** — returns concrete, actionable fix steps for any OWASP or MITRE finding
- **Multi-format Reports** — text, JSON, or Markdown output
- Fully tested with `pytest` (56+ passing tests, including full end-to-end pipeline integration tests, confirmed passing on both Windows and Linux)

## Project Structure

```
Team-Finatics/
├── data/
│   ├── owasp_top10.json              # OWASP Top 10:2025 dataset
│   ├── owasp_notes.md                # Notes on the OWASP data structure
│   ├── enterprise-attack.json        # MITRE ATT&CK Enterprise STIX data
│   ├── mobile-attack.json            # MITRE ATT&CK Mobile STIX data
│   └── ics-attack.json               # MITRE ATT&CK ICS STIX data
├── owasp_mapper.py                    # Keyword -> OWASP category mapping
├── mitre_mapper.py                    # Keyword -> MITRE technique mapping
├── framework_mapper.py                # Combined OWASP + MITRE mapper
├── nmap_parser.py                     # Nmap output parsing + keyword extraction
├── event_log_parser.py                # Event log parsing + keyword extraction/inference
├── llm_analyzer.py                    # Gemini-powered analysis, with offline fallback
├── report_generator.py                # Formats findings as text/JSON/Markdown
├── remediation_mapper.py              # OWASP/MITRE -> concrete remediation steps
├── nmap_report_pipeline.py            # Full pipeline: Nmap -> mapping -> analysis -> report
├── event_log_report_pipeline.py       # Full pipeline: Event Log -> mapping -> analysis -> report
├── test_owasp_mapper.py
├── test_mitre_mapper.py
├── test_integration.py                # Nmap -> MITRE end-to-end test
├── test_day15_integration.py          # Nmap -> LLM -> report end-to-end test
├── test_day16_integration.py          # Event Log -> LLM -> report end-to-end test
├── test_remediation_mapper.py
├── requirements.txt
├── README.md
├── USAGE.md                           # Install, configure, and first-scan guide
├── ARCHITECTURE.md                    # System overview and data flow
└── CONTRIBUTING.md                    # Guide for contributors
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

4. **(Optional) Enable AI-powered analysis**

   By default, SentinelAI uses a fast, deterministic rule-based analyzer — no setup needed. To enable real AI-generated analysis via Gemini:
   ```powershell
   [System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "your-key-here", "User")
   ```
   Get a key at https://aistudio.google.com/apikey. See **USAGE.md** for full details.

## Quick Start — First Command

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

Keyword: 'powershell'
  OWASP -> No match
  MITRE -> T1059.001 PowerShell [enterprise]
```

## Usage Examples

### Map a single keyword against both frameworks

```python
from framework_mapper import map_keyword

result = map_keyword("sql injection")
print(result["owasp"]["rank"], result["owasp"]["name"])
# A05:2025 Injection
```

### Full pipeline: Nmap scan -> mapping -> AI analysis -> report

```python
from nmap_report_pipeline import run_nmap_to_report

with open("scan_output.txt") as f:
    nmap_output = f.read()

result = run_nmap_to_report(nmap_output, report_format="markdown")
print(result["report"])
```

### Full pipeline: Event log -> mapping -> AI analysis -> report

```python
from event_log_report_pipeline import run_event_log_to_report

result = run_event_log_to_report(log_text, audience="enterprise")
print(result["report"])
```

### Get remediation steps for findings

```python
from remediation_mapper import get_remediation_for_findings

remediations = get_remediation_for_findings(result["findings"])
```

For the complete usage guide — including audience modes (student, enterprise, red team, blue team, bug bounty), report format options, and troubleshooting — see **[USAGE.md](USAGE.md)**.

## Running Tests

```bash
pytest -v
```

Expected: **56 tests passing**, covering OWASP mapping, MITRE mapping, the full Nmap and Event Log LLM pipelines, remediation lookups, and end-to-end integration — confirmed passing on both Windows and Linux.

## Documentation

- **[USAGE.md](USAGE.md)** — installation, configuration, and first-scan walkthrough
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — system overview and data flow
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — guide for adding new mappings or features

## Data Sources

- [OWASP Top 10:2025](https://owasp.org/Top10/2025/)
- [MITRE ATT&CK (cti repository)](https://github.com/mitre/cti)

## Team

| Name | Focus Area |
|---|---|
| Sneha Das | OWASP Mapping, MITRE Mapping, LLM Integration, Remediation Mapping, Testing & Documentation |