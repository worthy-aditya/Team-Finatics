# SentinelAI — Usage Guide

Complete step-by-step guide to install, configure, and run your first security scan with **SentinelAI**.

---

## Prerequisites

- **Python 3.8+** installed on your system
- **Nmap** (optional, required only for network scanning via `nmap_report_pipeline.py`)
- **Git** (to clone the repository)
- **pip** (Python package manager, typically included with Python)

### Check your Python version:
```bash
python --version
```

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/worthy-aditya/Team-Finatics.git
cd Team-Finatics
```

### Step 2: Create a Virtual Environment

A virtual environment keeps your project dependencies isolated.

**Windows (PowerShell):**
```powershell
python -m venv venv
# Activate the virtual environment
venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

> You'll see `(venv)` appear at the start of your terminal prompt when activated.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `google-generativeai` — Gemini API integration
- `requests` — HTTP requests
- `pytest` — Testing framework
- `click` — CLI framework
- `rich` — Formatted console output
- And other security/analysis libraries

---

## Configuration

### Optional: Enable Gemini AI Analysis

SentinelAI can use Google's **Gemini API** to generate natural-language analysis summaries. If you skip this, a deterministic rule-based fallback will be used automatically.

#### To enable Gemini:

1. **Get a free Gemini API key** from [Google AI Studio](https://aistudio.google.com/apikey)
2. **Set the environment variable** (this key is never committed to the repo):

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY = "your-api-key-here"
```

**Windows (Command Prompt):**
```cmd
set GEMINI_API_KEY=your-api-key-here
```

**macOS/Linux:**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

Or, for permanent storage, create a `.env` file in the project root (this file is in `.gitignore`, so it won't be committed):
```
GEMINI_API_KEY=your-api-key-here
```

> **Note:** The API key is optional. If it's not set, SentinelAI will use its built-in rule-based fallback for analysis.

---

## Running Your First Scan

### Option 1: Analyze Nmap Output (Network Scanning)

This is the most common use case — parse a raw Nmap scan and map it to OWASP and MITRE frameworks.

#### Step 1: Run an Nmap scan

First, perform an Nmap scan on a target (or use sample output):

```bash
# Scan a local IP or domain (replace with your target)
nmap -sV 192.168.1.1 > scan_output.txt
```

Or, if you're testing locally, save this sample output to `scan_output.txt`:
```
Nmap scan report for example.com (93.184.216.34)
Host is up (0.050s latency).
Not shown: 997 filtered ports
PORT    STATE SERVICE      VERSION
80/tcp  open  http         Apache httpd 2.4.41
443/tcp open  https        Apache httpd 2.4.41
22/tcp  open  ssh          OpenSSH 7.9p1
```

#### Step 2: Generate the Nmap Report

```bash
python nmap_report_pipeline.py
```

This will:
1. Parse the Nmap output
2. Extract security keywords (e.g., `"ssh"`, `"apache"`, `"http"`)
3. Map each keyword to OWASP Top 10:2025 categories
4. Map each keyword to MITRE ATT&CK techniques
5. Generate a natural-language analysis (via Gemini, or rule-based fallback)
6. Output a formatted security findings report

**Example Output:**
```
============================================================
SENTINELAI SECURITY FINDINGS REPORT
============================================================
Generated: 2026-08-18T09:44:18.996140+00:00
Total findings: 3

--- FINDINGS ---

[1] Keyword: ssh
    OWASP: No match
    MITRE: T1021.004 - SSH [enterprise]

[2] Keyword: apache
    OWASP: A06:2025 - Insecure Design
    MITRE: T1190 - Exploit Public-Facing Application [enterprise]

[3] Keyword: http
    OWASP: No match
    MITRE: T1071.001 - HTTP/HTTPS [enterprise]

--- ANALYSIS ---
Analysis Summary: 3 finding(s) reviewed...
...
```

---

### Option 2: Analyze Event Logs

Process security event logs and extract keywords automatically:

```bash
python event_log_report_pipeline.py
```

This pipeline:
1. Parses security event logs
2. Extracts threat-related keywords
3. Maps them to OWASP and MITRE frameworks
4. Generates an analysis summary
5. Produces a formatted report

---

### Option 3: Interactive CLI

Use the SentinelAI CLI for an interactive experience:

```bash
python sentinelai.py --help
```

Available commands:
- `scan <target>` — Scan a target IP or domain
- `network` — Perform network reconnaissance
- `report` — Generate a security report
- `start` — Enter interactive mode

---

## Generating Reports

### Report Formats

Generate reports in multiple formats using the report generator:

```bash
python main.py
```

This interactive menu allows you to generate:
1. **DOCX** — Microsoft Word format (includes tables, charts)
2. **PDF** — Portable Document Format
3. **Markdown** — For documentation and Git repositories

---

## Running Tests

Verify that everything is working correctly:

```bash
# Run all tests with verbose output
pytest -v

# Run tests with short traceback
pytest -v --tb=short

# Run a specific test file
pytest test_integration.py -v

# Run tests with coverage report
pytest --cov=. --cov-report=html
```

**Expected Result:**
```
============================= 56 passed in 4.75s ==============================
```

> All 56 tests should pass on both Windows and Linux environments.

---

## Common Use Cases

### 1. Quick Security Assessment of a Website

```bash
nmap -sV example.com > output.txt
python nmap_report_pipeline.py
```

Then view the generated report in the terminal or export to PDF/DOCX/Markdown.

### 2. Analyze Multiple Event Logs

Modify `event_log_report_pipeline.py` to point to your log files, then:
```bash
python event_log_report_pipeline.py
```

### 3. Continuous Integration / Automated Scanning

Add to your CI/CD pipeline:
```bash
python -m pytest -v
python event_log_report_pipeline.py > ci_report.txt
```

### 4. Red Team / Penetration Testing

Use the MITRE mapping to see which attack techniques are present:
```bash
# After running a scan, review MITRE technique IDs in the report
# Cross-reference with https://attack.mitre.org to see attack chains
```

### 5. Blue Team / Security Operations

Filter findings by OWASP category to prioritize remediation:
```bash
# Look at A01 (Broken Access Control) findings
# Focus on A07 (Authentication Failures) findings
# etc.
```

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'requests'`

**Solution:**
```bash
pip install -r requirements.txt
```

Ensure your virtual environment is activated (you should see `(venv)` in your terminal prompt).

---

### Issue: Gemini Timeout Error

**This is normal!** Gemini occasionally takes longer than expected. The system automatically falls back to a rule-based summary, so your report will still generate.

**Solution:**
```bash
# The fallback is built in—just re-run the command
python event_log_report_pipeline.py
```

Some runs will use Gemini, others will use the fallback. Either way, you get a complete report.

---

### Issue: Nmap Not Found

If you see "nmap not found", install Nmap:

**Windows:**
Download from [nmap.org](https://nmap.org/download.html) or install via Chocolatey:
```powershell
choco install nmap
```

**macOS:**
```bash
brew install nmap
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install nmap
```

---

### Issue: Tests Failing

**Solution:**
```bash
# Make sure your virtual environment is activated
venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate    # macOS/Linux

# Reinstall dependencies
pip install -r requirements.txt

# Run tests again
pytest -v
```

If tests still fail, check the detailed error:
```bash
pytest -v --tb=long
```

---

## File Structure Reference

```
Team-Finatics/
├── USAGE.md                      # This file
├── requirements.txt              # Python dependencies
├── main.py                       # Report generator (interactive menu)
├── sentinelai.py                 # CLI entry point
├── nmap_report_pipeline.py       # Nmap → OWASP/MITRE pipeline
├── event_log_report_pipeline.py  # Event log analysis pipeline
├── nmap_parser.py                # Parse Nmap output
├── framework_mapper.py           # Map keywords to OWASP + MITRE
├── owasp_mapper.py               # OWASP Top 10:2025 lookup
├── mitre_mapper.py               # MITRE ATT&CK lookup
├── llm_analyzer.py               # Gemini + fallback analysis
├── report_generator.py           # Format final reports
├── data/
│   ├── owasp_top10.json          # OWASP Top 10:2025 dataset
│   ├── enterprise-attack.json    # MITRE Enterprise dataset
│   ├── mobile-attack.json        # MITRE Mobile dataset
│   └── ics-attack.json           # MITRE ICS dataset
├── commands/
│   ├── scan.py                   # CLI scan command
│   ├── network.py                # CLI network command
│   └── report.py                 # CLI report command
├── tests/
│   └── test_*.py                 # 56 unit + integration tests
└── sentinal/
    └── research/report/          # Report generation (DOCX, PDF, Markdown)
```

---

## Next Steps

1. **Run your first scan:**
   ```bash
   python nmap_report_pipeline.py
   ```

2. **Verify everything works:**
   ```bash
   pytest -v
   ```

3. **Generate a report:**
   ```bash
   python main.py
   ```

4. **Explore the CLI:**
   ```bash
   python sentinelai.py --help
   ```

---

## Support & Feedback

For issues, feature requests, or questions:
- Check the [README.md](README.md) for architecture overview
- Review test files (`test_*.py`) for usage examples
- Open an issue on GitHub Discussions

---

**Happy scanning! 🛡️**
