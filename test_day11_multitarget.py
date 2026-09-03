#!/usr/bin/env python
"""
Day 11 Testing Script - Multi-target scanning and analysis
Tests SentinelAI on 3 different target types
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class TestRunner:
    def __init__(self):
        self.results = []
        self.script_dir = Path(__file__).parent
        self.results_file = self.script_dir / "test_results_day11.json"
    
    def run_scan(self, target, name, aggressive=False):
        """Run a scan and capture results"""
        print(f"\n{'='*70}")
        print(f"TEST {len(self.results) + 1}: {name}")
        print(f"{'='*70}")
        print(f"Target: {target}")
        print(f"Aggressive: {aggressive}")
        print(f"Time: {datetime.now().isoformat()}")
        print(f"{'='*70}\n")
        
        # Build command
        cmd = [
            sys.executable,
            "-m", "sentinelai.cli",
            "scan",
            "--target", target,
            "--llm-format"
        ]
        
        if aggressive:
            cmd.append("--aggressive")
        
        try:
            # Run scan
            result = subprocess.run(
                cmd,
                cwd=str(self.script_dir),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Parse output
            output_lines = result.stdout.split('\n')
            json_start = None
            
            for i, line in enumerate(output_lines):
                if line.strip().startswith('{'):
                    json_start = i
                    break
            
            if json_start is not None:
                json_str = '\n'.join(output_lines[json_start:])
                scan_data = json.loads(json_str)
                
                test_result = {
                    "test_number": len(self.results) + 1,
                    "target": target,
                    "test_name": name,
                    "aggressive": aggressive,
                    "timestamp": datetime.now().isoformat(),
                    "status": "PASS",
                    "scan_data": scan_data
                }
                
                self.results.append(test_result)
                
                # Print summary
                stats = scan_data.get("scan_statistics", {})
                print(f"[✓] Scan successful!")
                print(f"    Open Ports: {stats.get('open_ports')}")
                print(f"    Hosts Up: {stats.get('hosts_up')}")
                print(f"    Services Detected: {stats.get('services_detected')}")
                print(f"    Risk Level: {scan_data.get('risk_assessment', {}).get('risk_level')}")
                
                return True
            else:
                print(f"[✗] Failed to parse scan output")
                self.results.append({
                    "test_number": len(self.results) + 1,
                    "target": target,
                    "test_name": name,
                    "aggressive": aggressive,
                    "status": "FAIL",
                    "error": "Could not parse JSON output"
                })
                return False
                
        except subprocess.TimeoutExpired:
            print(f"[✗] Scan timeout (60s exceeded)")
            self.results.append({
                "test_number": len(self.results) + 1,
                "target": target,
                "test_name": name,
                "status": "FAIL",
                "error": "Scan timeout"
            })
            return False
        except Exception as e:
            print(f"[✗] Scan failed: {e}")
            self.results.append({
                "test_number": len(self.results) + 1,
                "target": target,
                "test_name": name,
                "status": "FAIL",
                "error": str(e)
            })
            return False
    
    def save_results(self):
        """Save test results to JSON file"""
        summary = {
            "test_suite": "Day 11 - Multi-target Testing",
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r.get("status") == "PASS"),
            "failed": sum(1 for r in self.results if r.get("status") == "FAIL"),
            "results": self.results
        }
        
        with open(self.results_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n{'='*70}")
        print(f"Results saved to: {self.results_file}")
        print(f"{'='*70}")
        
        return summary
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*70}")
        print("TEST SUMMARY")
        print(f"{'='*70}")
        
        passed = sum(1 for r in self.results if r.get("status") == "PASS")
        failed = sum(1 for r in self.results if r.get("status") == "FAIL")
        
        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        
        if passed == len(self.results):
            print("\n✓ ALL TESTS PASSED!")
        else:
            print(f"\n✗ {failed} test(s) failed")
        
        print(f"{'='*70}\n")


def main():
    runner = TestRunner()
    
    print("\n" + "="*70)
    print("WEEK 2 DAY 11: MULTI-TARGET SCANNING TEST SUITE")
    print("="*70)
    
    # Test 1: Localhost (127.0.0.1) - Standard scan
    print("\nStarting Test 1...")
    runner.run_scan("127.0.0.1", "Localhost - Standard Scan", aggressive=False)
    
    # Test 2: Localhost - Aggressive scan
    print("\nStarting Test 2...")
    runner.run_scan("127.0.0.1", "Localhost - Aggressive Scan", aggressive=True)
    
    # Test 3: Google DNS (8.8.8.8) - External public IP
    print("\nStarting Test 3...")
    runner.run_scan("8.8.8.8", "Public DNS Server (8.8.8.8)", aggressive=False)
    
    # Save and print results
    summary = runner.save_results()
    runner.print_summary()
    
    return 0 if summary.get("failed") == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
