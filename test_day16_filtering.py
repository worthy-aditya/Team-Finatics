#!/usr/bin/env python3
"""
Day 16: Critical Event Filtering & Threat Detection
Test EventFilter class with realistic security scenarios

This script will:
1. Test critical event filtering
2. Detect brute force attacks
3. Detect unusual account changes
4. Detect suspicious network access
5. Generate comprehensive threat analysis
"""

import json
from datetime import datetime, timedelta
from sentinelai.event_logs import EventFilter


def create_test_scenario_brute_force():
    """Create a brute force attack scenario"""
    base_time = datetime.now()
    events = []
    
    # Create 7 failed login attempts (4625) within 30 minutes
    for i in range(7):
        events.append({
            "log": "Security",
            "event_id": 4625,
            "event_type": 1,
            "source": "Microsoft-Windows-Security-Auditing",
            "computer": "DESKTOP-USER",
            "timestamp": (base_time - timedelta(minutes=5-i)).strftime("%Y-%m-%d %H:%M:%S"),
            "message": "TestUser | Failed Logon | Bad Password",
            "category": 0,
            "record_number": 1000 + i,
            "data": ""
        })
    
    # Add a few successful logins to mix in
    for i in range(2):
        events.append({
            "log": "Security",
            "event_id": 4624,
            "event_type": 0,
            "source": "Microsoft-Windows-Security-Auditing",
            "computer": "DESKTOP-USER",
            "timestamp": (base_time - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
            "message": "Administrator | Successful Logon | Network",
            "category": 0,
            "record_number": 2000 + i,
            "data": ""
        })
    
    return events


def create_test_scenario_account_changes():
    """Create suspicious account change scenario"""
    base_time = datetime.now()
    events = []
    
    # Create 4 new user accounts within 1 hour
    for i in range(4):
        events.append({
            "log": "Security",
            "event_id": 4720,
            "event_type": 0,
            "source": "Microsoft-Windows-Security-Auditing",
            "computer": "DESKTOP-USER",
            "timestamp": (base_time - timedelta(minutes=50-i*10)).strftime("%Y-%m-%d %H:%M:%S"),
            "message": f"NewUser{i} | Account Created | Domain",
            "category": 0,
            "record_number": 3000 + i,
            "data": ""
        })
    
    # Delete 2 user accounts
    for i in range(2):
        events.append({
            "log": "Security",
            "event_id": 4726,
            "event_type": 0,
            "source": "Microsoft-Windows-Security-Auditing",
            "computer": "DESKTOP-USER",
            "timestamp": (base_time - timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S"),
            "message": f"DeletedUser{i} | Account Deleted",
            "category": 0,
            "record_number": 3100 + i,
            "data": ""
        })
    
    return events


def create_test_scenario_after_hours_access():
    """Create after-hours network access scenario"""
    # Create midnight timestamp (00:30)
    base_time = datetime.now().replace(hour=0, minute=30, second=0)
    events = []
    
    # Create 3 network share access events at midnight
    for i in range(3):
        events.append({
            "log": "Security",
            "event_id": 5140,
            "event_type": 0,
            "source": "Microsoft-Windows-Security-Auditing",
            "computer": "DESKTOP-USER",
            "timestamp": (base_time + timedelta(minutes=i*5)).strftime("%Y-%m-%d %H:%M:%S"),
            "message": f"\\\\SERVER\\Share{i} | Accessed",
            "category": 0,
            "record_number": 4000 + i,
            "data": ""
        })
    
    # Add some daytime access (business hours)
    daytime = datetime.now().replace(hour=14, minute=0, second=0)
    for i in range(2):
        events.append({
            "log": "Security",
            "event_id": 5140,
            "event_type": 0,
            "source": "Microsoft-Windows-Security-Auditing",
            "computer": "DESKTOP-USER",
            "timestamp": (daytime + timedelta(minutes=i*10)).strftime("%Y-%m-%d %H:%M:%S"),
            "message": f"\\\\SERVER\\Files | Accessed",
            "category": 0,
            "record_number": 4100 + i,
            "data": ""
        })
    
    return events


def create_normal_scenario():
    """Create normal, non-threatening scenario"""
    base_time = datetime.now()
    events = []
    
    # Normal successful logins
    for i in range(5):
        events.append({
            "log": "Security",
            "event_id": 4624,
            "event_type": 0,
            "source": "Microsoft-Windows-Security-Auditing",
            "computer": "DESKTOP-USER",
            "timestamp": (base_time - timedelta(hours=i)).strftime("%Y-%m-%d %H:%M:%S"),
            "message": "Administrator | Successful Logon | Interactive",
            "category": 0,
            "record_number": 5000 + i,
            "data": ""
        })
    
    # One normal failed login
    events.append({
        "log": "Security",
        "event_id": 4625,
        "event_type": 1,
        "source": "Microsoft-Windows-Security-Auditing",
        "computer": "DESKTOP-USER",
        "timestamp": base_time.strftime("%Y-%m-%d %H:%M:%S"),
        "message": "User | Failed Logon | Typo Password",
        "category": 0,
        "record_number": 5100,
        "data": ""
    })
    
    return events


def run_test(name, events, expected_threat_level):
    """Run a test scenario"""
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print(f"{'='*70}")
    
    filter = EventFilter()
    analysis = filter.analyze_events(events)
    
    # Display results
    print(f"\n[*] Event Analysis:")
    print(f"    Events Analyzed: {analysis['events_analyzed']}")
    print(f"    Critical Events Found: {analysis['critical_events_found']}")
    print(f"    Threat Level: {analysis['threat_level']}")
    print(f"    Total Alerts: {analysis['total_alerts']}")
    
    # Display alerts
    if analysis['alerts']:
        print(f"\n[!] ALERTS DETECTED:")
        for alert in analysis['alerts']:
            print(f"    - [{alert['severity']}] {alert['type']}")
            if 'description' in alert:
                print(f"      Description: {alert['description']}")
            if 'user' in alert:
                print(f"      User: {alert['user']}")
            if 'attempts' in alert:
                print(f"      Attempts: {alert['attempts']}")
    else:
        print(f"\n[✓] No alerts detected")
    
    # Display analysis details
    if analysis['brute_force_analysis']['total_failed_logins'] > 0:
        print(f"\n[*] Brute Force Analysis:")
        print(f"    Total Failed Logins: {analysis['brute_force_analysis']['total_failed_logins']}")
        print(f"    By User: {analysis['brute_force_analysis']['by_user']}")
    
    if analysis['account_changes_analysis']['created_accounts']:
        print(f"\n[*] Account Changes:")
        print(f"    Created: {len(analysis['account_changes_analysis']['created_accounts'])}")
        print(f"    Deleted: {len(analysis['account_changes_analysis']['deleted_accounts'])}")
    
    if analysis['unusual_access_analysis']['after_hours_access']:
        print(f"\n[*] Unusual Access:")
        print(f"    After-Hours Access: {len(analysis['unusual_access_analysis']['after_hours_access'])}")
    
    # Display recommendations
    if analysis['recommendations']:
        print(f"\n[→] RECOMMENDATIONS:")
        for rec in analysis['recommendations']:
            print(f"    - {rec}")
    
    # Verify expected threat level
    status = "✓ PASS" if analysis['threat_level'] == expected_threat_level else "✗ FAIL"
    print(f"\n{status}: Expected {expected_threat_level}, Got {analysis['threat_level']}")
    
    return analysis


def main():
    """Run all Day 16 tests"""
    
    print("\n" + "="*70)
    print("DAY 16: CRITICAL EVENT FILTERING & THREAT DETECTION")
    print("="*70)
    
    results = []
    
    # Test 1: Brute Force Detection
    print("\n[TEST 1/4] BRUTE FORCE ATTACK SCENARIO")
    events = create_test_scenario_brute_force()
    result = run_test("Brute Force Attack (7 failed logins)", events, "HIGH")
    results.append(("Brute Force Attack", result))
    
    # Test 2: Account Changes
    print("\n[TEST 2/4] SUSPICIOUS ACCOUNT CHANGES SCENARIO")
    events = create_test_scenario_account_changes()
    result = run_test("Suspicious Account Changes (4 created, 2 deleted)", events, "HIGH")
    results.append(("Suspicious Account Changes", result))
    
    # Test 3: After-Hours Access
    print("\n[TEST 3/4] AFTER-HOURS NETWORK ACCESS SCENARIO")
    events = create_test_scenario_after_hours_access()
    result = run_test("After-Hours Network Access", events, "MEDIUM")
    results.append(("After-Hours Access", result))
    
    # Test 4: Normal Scenario
    print("\n[TEST 4/4] NORMAL SCENARIO (NO THREATS)")
    events = create_normal_scenario()
    result = run_test("Normal Activity (1 failed, 5 successful logins)", events, "LOW")
    results.append(("Normal Activity", result))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, r in results if r['threat_level'] in ["HIGH", "MEDIUM", "LOW"])
    
    print(f"\n[*] Results:")
    for name, result in results:
        threat = result['threat_level']
        alerts = result['total_alerts']
        print(f"  - {name}: {threat} threat ({alerts} alerts)")
    
    print(f"\n[✓] Test Execution: {passed_tests}/{total_tests} scenarios validated")
    
    # Save detailed results
    print(f"\n[*] Saving results to file...")
    detailed_results = {
        "test_date": datetime.now().isoformat(),
        "test_count": total_tests,
        "scenarios": [
            {
                "name": name,
                "threat_level": result['threat_level'],
                "critical_events": result['critical_events_found'],
                "total_alerts": result['total_alerts'],
                "brute_force_detected": result['brute_force_analysis']['detected'],
                "account_changes": len(result['account_changes_analysis']['created_accounts']),
                "alerts": result['alerts']
            }
            for name, result in results
        ]
    }
    
    with open("test_results_day16.json", "w") as f:
        json.dump(detailed_results, f, indent=2, default=str)
    print(f"    ✓ Results saved to test_results_day16.json")
    
    print("\n" + "="*70)
    print("✓ DAY 16 TESTING COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
