# SentinelAI CLI - Code Explanation & Technical Documentation

## Table of Contents
1. [Code Overview](#code-overview)
2. [Detailed Code Breakdown](#detailed-code-breakdown)
3. [What Was Accomplished](#what-was-accomplished)
4. [How to Use](#how-to-use)
5. [Output Interpretation](#output-interpretation)
6. [Project Architecture](#project-architecture)

---

## Code Overview

The **`scan_localhost.py`** script is a Python wrapper around the Nmap security scanning tool. It allows users to scan any target (IP address, hostname, or domain) and get detailed information about open ports and services running on that target.

### Key Purpose
- Simplifies Nmap execution through Python
- Handles cross-platform compatibility (Windows path management)
- Captures and displays raw Nmap output
- Foundation for future AI-driven analysis and reporting

---

## Detailed Code Breakdown

### **Part 1: Imports (Lines 1-11)**

```python
import subprocess       # Run external programs (Nmap.exe)
import json           # Parse JSON data structures
from pathlib import Path  # Handle file paths elegantly
import os             # File/directory operations (check if Nmap exists)
import re             # Regular expressions for text parsing
import sys            # Read command-line arguments from user
```

| Import | Purpose |
|--------|---------|
| `subprocess` | Executes external programs (Nmap) from Python |
| `json` | Parses structured data (for future enhancements) |
| `pathlib.Path` | Cross-platform file path handling |
| `os` | Operating system operations (file existence checks) |
| `re` | Pattern matching for output parsing |
| `sys` | Access command-line arguments |

---

### **Part 2: Main Function - `scan_target()` (Lines 13-55)**

#### **Function Definition**
```python
def scan_target(target="127.0.0.1"):
    """
    Perform a basic Nmap scan on specified target
    Returns raw scan results
    """
```

**Parameters:**
- `target` (string): IP address, hostname, or domain name to scan
- Default value: `"127.0.0.1"` (localhost)

**Returns:**
- `str` or `None`: Raw Nmap output text, or None if scan fails

---

#### **Step 1: Verify Nmap Installation**

```python
print("[*] Initializing Nmap scanner...")

# Full path to nmap.exe
nmap_exe = r"C:\Program Files (x86)\Nmap\nmap.exe"

if not os.path.exists(nmap_exe):
    print(f"[!] Nmap not found at: {nmap_exe}")
    return None
```

**What it does:**
1. Defines the full path to Nmap executable on Windows
2. Checks if the file exists using `os.path.exists()`
3. If not found, prints error message and exits early

**Why this matters:**
- Different Windows systems might have Nmap in different locations
- Better to check early than wait for subprocess error
- Provides clear error message to user

---

#### **Step 2: Configure Scan Arguments**

```python
scan_args = ["-sV", "-p", "1-1000"]  # Service detection, common ports only

print(f"[*] Starting scan on {target}")
print(f"[*] Scan arguments: {' '.join(scan_args)}")
print("[*] Scanning ports 1-1000...\n")
```

**Nmap Arguments Explained:**

| Argument | Full Name | Purpose |
|----------|-----------|---------|
| `-sV` | Service Version Detection | Identifies what services/applications are running on open ports |
| `-p` | Port specification | Limits scan to specific ports |
| `1-1000` | Port range | Scans only ports 1 through 1000 (out of 65535 total) |

**Why this configuration:**
- `-sV` gives us detailed information about what's running
- Limiting to ports 1-1000 makes scan faster (most common services use these)
- Port 80 (HTTP), 443 (HTTPS), 22 (SSH), 3306 (MySQL) all within this range

---

#### **Step 3: Build and Execute Command**

```python
try:
    # Build command
    cmd = [nmap_exe] + scan_args + [target]
    
    # Run nmap
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
```

**Command Structure:**
```
[nmap_exe] + [scan_args] + [target]
↓
["C:\Program Files (x86)\Nmap\nmap.exe"] + ["-sV", "-p", "1-1000"] + ["google.com"]
↓
Final command:
C:\Program Files (x86)\Nmap\nmap.exe -sV -p 1-1000 google.com
```

**subprocess.run() Parameters:**
- `cmd`: The command to execute (list format)
- `capture_output=True`: Capture stdout and stderr (don't print to console)
- `text=True`: Return output as text strings (not bytes)
- `timeout=120`: Stop scan if it takes longer than 120 seconds

**Return Value:**
- `result.stdout`: The normal output from Nmap
- `result.stderr`: Error messages (if any)
- `result.returncode`: Exit code (0 = success, non-zero = failure)

---

#### **Step 4: Error Handling**

```python
if result.returncode != 0:
    print(f"[!] Nmap returned error code: {result.returncode}")
    if result.stderr:
        print(f"[!] Error: {result.stderr}")
    return result.stdout
```

**What it does:**
- Checks if Nmap executed successfully (`returncode == 0`)
- If not, prints error information
- Still returns stdout in case there's partial data

---

#### **Step 5: Display and Return Results**

```python
print("[+] Scan completed successfully!\n")
print("=" * 60)
print("RAW NMAP OUTPUT")
print("=" * 60)
print(result.stdout)

return result.stdout
```

**Output:**
```
============================================================
RAW NMAP OUTPUT
============================================================
Starting Nmap 7.99 ( https://nmap.org ) at 2026-07-13 12:41 +0530
Nmap scan report for google.com (216.239.38.120)
Host is up (0.017s latency).
...
```

---

#### **Step 6: Exception Handling**

```python
except subprocess.TimeoutExpired:
    print("[!] Nmap scan timed out")
    return None
except Exception as e:
    print(f"[!] Error: {e}")
    return None
```

**Handles two scenarios:**
1. **Timeout:** Scan takes longer than 120 seconds
2. **Other errors:** Any unexpected exceptions (file not found, permission denied, etc.)

---

### **Part 3: Main Execution Block (Lines 59-72)**

```python
if __name__ == "__main__":
    print("=" * 60)
    print("SentinelAI - Network Scan Tool")
    print("=" * 60 + "\n")
    
    # Get target from command line or use localhost as default
    target = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    
    results = scan_target(target)
    
    if results:
        print("\n[+] Scan data successfully captured")
        print("\nScan output has been printed above")
    else:
        print("\n[!] Scan failed")
```

**`if __name__ == "__main__":`**
- This block only runs when script is executed directly
- Does NOT run if script is imported as a module in another file
- Best practice for reusable Python code

**Command-line Argument Handling:**
```python
target = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
```

| Scenario | Value of `target` |
|----------|-------------------|
| `python scan_localhost.py` | `"127.0.0.1"` (default) |
| `python scan_localhost.py google.com` | `"google.com"` |
| `python scan_localhost.py 192.168.1.1` | `"192.168.1.1"` |

---

## What Was Accomplished

### **Day 1: Development Environment Setup**

#### Created Project Structure
```
Team-Finatics/
├── sentinelai/              # Main package
│   ├── __init__.py          # Package initialization
│   ├── cli.py               # CLI interface with Click framework
│   └── scanner.py           # Scanner base classes
├── tests/                   # Test directory
├── venv/                    # Python virtual environment
├── requirements.txt         # Python dependencies
├── setup.py                 # Package setup configuration
└── .gitignore              # Git ignore file
```

#### Installed Python Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| python-nmap | 0.7.1 | Nmap Python wrapper |
| click | 8.1.3 | CLI framework |
| colorama | 0.4.6 | Terminal color output |
| pydantic | 2.0.0 | Data validation |
| python-docx | 0.8.11 | Generate Word documents |
| requests | 2.31.0 | HTTP requests |
| openai | 1.3.0 | OpenAI API |
| google-generativeai | 0.3.0 | Google Gemini API |
| anthropic | 0.7.0 | Claude API |

#### Virtual Environment
```powershell
# Created isolated Python environment
venv/ contains:
  - Python interpreter
  - All installed packages
  - Isolated from system Python
```

**Status:** ✅ Dev environment fully operational

---

### **Day 2: Nmap Installation & System Configuration**

#### Installation Details
```
OS: Windows 10/11
Nmap Version: 7.99
Installation Path: C:\Program Files (x86)\Nmap\nmap.exe
```

#### System Configuration
```powershell
# Added to Windows PATH via:
setx PATH "%PATH%;C:\Program Files (x86)\Nmap"

# Verification command:
& "C:\Program Files (x86)\Nmap\nmap.exe" --version

# Output:
Nmap version 7.99 ( https://nmap.org )
Platform: i686-pc-windows-windows
Compiled with: nmap-liblua-5.4.8 openssl-3.0.16
```

#### Tools Installed with Nmap
- **nmap.exe** - Main scanning engine
- **ncat.exe** - Network utility
- **nping.exe** - ICMP/TCP/UDP ping tool
- NSE scripts - Lua scripting for advanced scanning

**Status:** ✅ Nmap confirmed working on Windows

---

### **Day 3: Python Integration & Basic Scan Script**

#### Script Creation: `scan_localhost.py`

**File:** `c:\Users\malis\OneDrive\Documents\GitHub\Team-Finatics\scan_localhost.py`

**Key Features:**
- ✅ Accepts any target (IP, hostname, domain)
- ✅ Uses subprocess for reliable Nmap execution
- ✅ Full path to Nmap (bypasses PATH issues)
- ✅ 120-second timeout protection
- ✅ Error handling for common scenarios
- ✅ Raw output capture and display

#### Test Results

**Test 1: Localhost Scan (127.0.0.1)**
```
Command: .\venv\Scripts\python scan_localhost.py
Scan Time: 7.95 seconds
Ports Found: 3 open/filtered
Results:
  - Port 135/tcp: OPEN (Microsoft Windows RPC)
  - Port 137/tcp: FILTERED (NetBIOS-NS)
  - Port 445/tcp: OPEN (Microsoft-DS)
Status: ✅ SUCCESS
```

**Test 2: Google.com Scan**
```
Command: .\venv\Scripts\python scan_localhost.py google.com
Scan Time: 87.71 seconds
IP Address: 216.239.38.120
Ports Found: 2 open
Results:
  - Port 80/tcp: OPEN (HTTP - Google Web Server)
  - Port 443/tcp: OPEN (HTTPS/SSL - Google Web Server)
Status: ✅ SUCCESS
```

**Status:** ✅ Python-Nmap integration working successfully

---

## How to Use

### **Basic Usage**

#### Scan Localhost (Default)
```powershell
cd "c:\Users\malis\OneDrive\Documents\GitHub\Team-Finatics"
.\venv\Scripts\python scan_localhost.py
```

#### Scan Any Domain
```powershell
.\venv\Scripts\python scan_localhost.py google.com
.\venv\Scripts\python scan_localhost.py example.com
.\venv\Scripts\python scan_localhost.py microsoft.com
```

#### Scan IP Address
```powershell
.\venv\Scripts\python scan_localhost.py 192.168.1.1
.\venv\Scripts\python scan_localhost.py 8.8.8.8
```

#### Scan with Full Path
```powershell
python "c:\Users\malis\OneDrive\Documents\GitHub\Team-Finatics\scan_localhost.py" google.com
```

---

## Output Interpretation

### **Sample Scan Output**

```
============================================================
SentinelAI - Network Scan Tool
============================================================

[*] Initializing Nmap scanner...
[*] Starting scan on google.com
[*] Scan arguments: -sV -p 1-1000
[*] Scanning ports 1-1000...

[+] Scan completed successfully!

============================================================
RAW NMAP OUTPUT
============================================================
Starting Nmap 7.99 ( https://nmap.org ) at 2026-07-13 12:41 +0530
Nmap scan report for google.com (216.239.38.120)
Host is up (0.017s latency).
Other addresses for google.com (not scanned): [IPv6 addresses]
rDNS record for 216.239.38.120: any-in-2678.1e100.net
Not shown: 998 filtered tcp ports (no-response)
PORT    STATE SERVICE   VERSION
80/tcp  open  http      gws
443/tcp open  ssl/https gws

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 87.71 seconds

[+] Scan data successfully captured

Scan output has been printed above
```

### **Output Fields Explained**

| Field | Example | Meaning |
|-------|---------|---------|
| **Port** | `80/tcp` | Port number and protocol (TCP/UDP) |
| **State** | `open` | Connection state: open, closed, or filtered |
| **Service** | `http` | Service running on that port |
| **Version** | `gws` | Version of the service (Google Web Server) |
| **Latency** | `0.017s` | Network delay to target |
| **Host Status** | `Host is up` | Target is reachable |

### **Port States Explained**

| State | Meaning | Implication |
|-------|---------|------------|
| **open** | Port is accepting connections | Service is running and accessible |
| **closed** | Port rejects all connections | No service running, firewall not blocking |
| **filtered** | Port is not responding | Firewall/filter is blocking connections |
| **unfiltered** | Uncertain state | Port is accessible but state unknown |

---

## Project Architecture

### **Current Architecture (Days 1-3)**

```
┌─────────────────────────────────────────────────────┐
│         SentinelAI CLI - Current State              │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
            ┌──────────────────────────┐
            │   Python Script          │
            │  scan_localhost.py       │
            └──────────────────────────┘
                          │
                          ▼
            ┌──────────────────────────┐
            │   subprocess module      │
            │  (Execute external prog) │
            └──────────────────────────┘
                          │
                          ▼
            ┌──────────────────────────┐
            │   Nmap 7.99              │
            │ (nmap.exe on Windows)    │
            └──────────────────────────┘
                          │
                          ▼
            ┌──────────────────────────┐
            │   Target (IP/Domain)     │
            │  google.com, localhost   │
            └──────────────────────────┘
                          │
                          ▼
            ┌──────────────────────────┐
            │   Raw Text Output        │
            │  (Printed to terminal)   │
            └──────────────────────────┘
```

### **Planned Architecture (Days 4-7)**

```
┌─────────────────────────────────────────────────────┐
│         SentinelAI CLI - Full Vision                │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
            ┌──────────────────────────┐
            │   CLI Interface          │
            │  (Natural Language)      │
            └──────────────────────────┘
                          │
                          ▼
            ┌──────────────────────────┐
            │   Nmap Scanner           │
            │  (Parse output structure)│
            └──────────────────────────┘
                          │
        ┌───────────────────────────────────┐
        │                                   │
        ▼                                   ▼
    ┌─────────────┐              ┌──────────────────┐
    │ MITRE ATT&CK│              │  OWASP Mapping   │
    │  Mapping    │              │   (Day 4)        │
    └─────────────┘              └──────────────────┘
        │                                   │
        └───────────────────────────────────┘
                        │
                        ▼
            ┌──────────────────────────┐
            │   Report Generator       │
            │  DOCX/PDF/Markdown       │
            └──────────────────────────┘
                        │
                        ▼
            ┌──────────────────────────┐
            │   LLM Analysis           │
            │  (OpenAI/Claude/Gemini)  │
            └──────────────────────────┘
                        │
                        ▼
            ┌──────────────────────────┐
            │   Professional Report    │
            │  + Remediation Guidance  │
            └──────────────────────────┘
```

---

## Summary

### **What We Have Now**
✅ Working Nmap integration  
✅ Python wrapper script  
✅ Cross-platform compatibility (Windows)  
✅ Command-line argument handling  
✅ Error handling and timeouts  
✅ Raw output capture  

### **What's Next**
📋 **Day 4:** Parse Nmap output structure  
📋 **Day 5:** Build comprehensive NmapScanner wrapper  
📋 **Day 6:** Test on local network  
📋 **Day 7:** Team sync and GitHub merge  

---

**Document Generated:** 2026-07-13  
**Project:** SentinelAI CLI v0.1.0  
**Developer:** Affan Shaikh  
**Team:** Team Finatics | CodeQuest 4.0
