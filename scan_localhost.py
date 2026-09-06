#!/usr/bin/env python
"""
Basic Nmap scan script for localhost
Tests python-nmap integration
"""

import subprocess
import json
from pathlib import Path
import os
import re
import sys

def scan_target(target="127.0.0.1"):
    """
    Perform a basic Nmap scan on specified target
    Returns raw scan results
    """
    print("[*] Initializing Nmap scanner...")
    
    # Full path to nmap.exe
    nmap_exe = r"C:\Program Files (x86)\Nmap\nmap.exe"
    
    if not os.path.exists(nmap_exe):
        print(f"[!] Nmap not found at: {nmap_exe}")
        return None
    
    scan_args = ["-sV", "-p", "1-1000"]  # Service detection, common ports only
    
    print(f"[*] Starting scan on {target}")
    print(f"[*] Scan arguments: {' '.join(scan_args)}")
    print("[*] Scanning ports 1-1000...\n")
    
    try:
        # Build command
        cmd = [nmap_exe] + scan_args + [target]
        
        # Run nmap
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            print(f"[!] Nmap returned error code: {result.returncode}")
            if result.stderr:
                print(f"[!] Error: {result.stderr}")
            return result.stdout
        
        print("[+] Scan completed successfully!\n")
        print("=" * 60)
        print("RAW NMAP OUTPUT")
        print("=" * 60)
        print(result.stdout)
        
        return result.stdout
        
    except subprocess.TimeoutExpired:
        print("[!] Nmap scan timed out")
        return None
    except Exception as e:
        print(f"[!] Error: {e}")
        return None


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
