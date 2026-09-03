#!/usr/bin/env python
"""
Day 12 Edge Case Testing Script
Tests SentinelAI error handling and edge cases
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class EdgeCaseTestRunner:
    def __init__(self):
        self.results = []
        self.script_dir = Path(__file__).parent
        self.results_file = self.script_dir / "test_results_day12_edgecases.json"
    
    def run_test(self, test_name, target, extra_args="", should_fail=False):
        """Run an edge case test"""
        print(f"\n{'='*70}")
        print(f"TEST: {test_name}")
        print(f"{'='*70}")
        print(f"Target: {target}")
        print(f"Extra Args: {extra_args if extra_args else 'None'}")
        print(f"Expected: {'FAIL (Error Handling)' if should_fail else 'SUCCESS'}")
        print(f"Time: {datetime.now().isoformat()}")
        print(f"{'='*70}\n")
        
        # Build command
        cmd = [
            sys.executable,
            "-m", "sentinelai.cli",
            "scan",
            "--target", target
        ]
        
        if extra_args:
            cmd.extend(extra_args.split())
        
        try:
            # Run scan
            result = subprocess.run(
                cmd,
                cwd=str(self.script_dir),
                capture_output=True,
                text=True,
                timeout=90
            )
            
            output = result.stdout + result.stderr
            
            # Determine test status
            if should_fail:
                # We expect an error
                if result.returncode != 0 or "[!]" in output:
                    status = "PASS"
                    details = "Correctly handled edge case with error"
                else:
                    status = "FAIL"
                    details = "Should have failed but succeeded"
            else:
                # We expect success
                if result.returncode == 0 and "[+]" in output:
                    status = "PASS"
                    details = "Scan completed successfully"
                else:
                    status = "FAIL"
                    details = f"Scan failed (exit code: {result.returncode})"
            
            test_result = {
                "test_name": test_name,
                "target": target,
                "extra_args": extra_args,
                "status": status,
                "details": details,
                "exit_code": result.returncode,
                "timestamp": datetime.now().isoformat()
            }
            
            self.results.append(test_result)
            
            # Print result
            result_color = "[✓]" if status == "PASS" else "[✗]"
            print(f"{result_color} {test_name}: {status}")
            print(f"   Details: {details}")
            
            # Show errors if any
            if "[!]" in output:
                error_lines = [line for line in output.split('\n') if "[!]" in line]
                for error_line in error_lines[:3]:  # Show first 3 errors
                    print(f"   Error: {error_line}")
            
            # Show tips if provided
            if "Tips:" in output:
                print(f"   Tips provided by CLI")
            
            return status == "PASS"
            
        except subprocess.TimeoutExpired:
            print(f"[✗] Test timeout (90s exceeded)")
            self.results.append({
                "test_name": test_name,
                "target": target,
                "status": "TIMEOUT",
                "details": "Test execution timeout",
                "timestamp": datetime.now().isoformat()
            })
            return False
        except Exception as e:
            print(f"[✗] Test failed: {e}")
            self.results.append({
                "test_name": test_name,
                "target": target,
                "status": "ERROR",
                "details": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    def save_results(self):
        """Save test results to JSON file"""
        summary = {
            "test_suite": "Day 12 - Edge Case Handling",
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r.get("status") == "PASS"),
            "failed": sum(1 for r in self.results if r.get("status") != "PASS"),
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
        print("EDGE CASE TEST SUMMARY")
        print(f"{'='*70}")
        
        passed = sum(1 for r in self.results if r.get("status") == "PASS")
        failed = sum(1 for r in self.results if r.get("status") != "PASS")
        
        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        
        if failed == 0:
            print("\n✓ ALL EDGE CASES HANDLED CORRECTLY!")
        else:
            print(f"\n✗ {failed} test(s) need attention")
        
        print(f"{'='*70}\n")


def main():
    runner = EdgeCaseTestRunner()
    
    print("\n" + "="*70)
    print("WEEK 2 DAY 12: EDGE CASE HANDLING TEST SUITE")
    print("="*70)
    
    # Test 1: Normal successful scan (baseline)
    runner.run_test(
        "Test 1: Normal Scan (Baseline)",
        "127.0.0.1",
        should_fail=False
    )
    
    # Test 2: No open ports scenario
    print("\nNote: Test 2 will scan a host expected to have no open ports in range")
    runner.run_test(
        "Test 2: Host with No Open Ports",
        "127.0.0.1",
        "--aggressive",
        should_fail=False
    )
    
    # Test 3: Timeout handling
    print("\nNote: Test 3 will test timeout handling with very short timeout")
    runner.run_test(
        "Test 3: Short Timeout (Edge Case)",
        "127.0.0.1",
        "--timeout 2",
        should_fail=True  # Short timeout should cause error
    )
    
    # Test 4: Invalid target format
    runner.run_test(
        "Test 4: Invalid IP Address",
        "999.999.999.999",
        should_fail=True  # Invalid IP should error or warn
    )
    
    # Test 5: Invalid target - bad format
    runner.run_test(
        "Test 5: Invalid Target Format",
        "not-a-valid-target!!!",
        should_fail=True
    )
    
    # Test 6: Localhost variations
    runner.run_test(
        "Test 6: Localhost by Name",
        "localhost",
        should_fail=False
    )
    
    # Test 7: Aggressive mode
    runner.run_test(
        "Test 7: Aggressive Scan",
        "127.0.0.1",
        "--aggressive",
        should_fail=False
    )
    
    # Test 8: JSON output
    runner.run_test(
        "Test 8: JSON Output",
        "127.0.0.1",
        "--json",
        should_fail=False
    )
    
    # Test 9: LLM Format output
    runner.run_test(
        "Test 9: LLM Format Output",
        "127.0.0.1",
        "--llm-format",
        should_fail=False
    )
    
    # Test 10: Analysis mode
    runner.run_test(
        "Test 10: Analysis Mode",
        "127.0.0.1",
        "--analyze",
        should_fail=False
    )
    
    # Save and print results
    summary = runner.save_results()
    runner.print_summary()
    
    return 0 if summary.get("failed") == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
