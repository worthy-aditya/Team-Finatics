#!/usr/bin/env python3
"""
Day 15: Windows Event Log Reader Test
Test the EventLogReader class with actual Windows Security events

This script will:
1. Test PyWin32 availability
2. Attempt to read Security log
3. Parse and display events
4. Show statistics
"""

import json
from sentinelai.event_logs import EventLogReader, EventLogAnalyzer


def test_eventlog_reader():
    """Test basic event log reading functionality"""
    
    print("="*70)
    print("DAY 15: WINDOWS EVENT LOG READER TEST")
    print("="*70)
    
    # Initialize reader
    reader = EventLogReader()
    
    # Check if PyWin32 is available
    print("\n[*] Checking PyWin32 availability...")
    if not reader.provider.available:
        print("    ✗ PyWin32 not available - install with: pip install pywin32")
        return False
    print("    ✓ PyWin32 is available")
    
    # Try to open Security log
    print("\n[*] Attempting to open Security log...")
    if not reader.open_log("Security"):
        print(f"    ✗ Error: {reader.last_error}")
        print("    Note: Security log requires administrator privileges")
        print("    Attempting to read Application log instead...")
        if not reader.open_log("Application"):
            print(f"    ✗ Error: {reader.last_error}")
            return False
        log_name = "Application"
    else:
        print("    ✓ Security log opened successfully")
        log_name = "Security"
    
    # Read events
    print(f"\n[*] Reading events from {log_name} log...")
    events = reader.read_events(log_name=log_name, max_events=100)
    
    if not events:
        if reader.last_error:
            print(f"    ✗ Error: {reader.last_error}")
        else:
            print(f"    ✗ No events read from {log_name} log")
        return False
    
    print(f"    ✓ Successfully read {len(events)} events")
    
    # Display first few events
    print(f"\n[*] First 5 events from {log_name} log:")
    print("-" * 70)
    for i, event in enumerate(events[:5], 1):
        print(f"\nEvent {i}:")
        print(f"  Event ID: {event.get('event_id')}")
        print(f"  Type: {event.get('event_type')}")
        print(f"  Timestamp: {event.get('timestamp')}")
        print(f"  Source: {event.get('source')}")
        print(f"  Computer: {event.get('computer')}")
        print(f"  Message: {event.get('message', '')[:100]}...")
    
    # Generate statistics
    print(f"\n[*] Statistics for {len(events)} events:")
    print("-" * 70)
    stats = reader.get_statistics(events)
    print(f"  Total Events: {stats['total_events']}")
    print(f"  Unique Event IDs: {stats['unique_event_ids']}")
    print(f"  Event Type Distribution:")
    for event_type, count in stats['event_type_counts'].items():
        print(f"    - {event_type}: {count}")
    
    if stats['top_events']:
        print(f"\n  Top 5 Event IDs:")
        for event_id, count in stats['top_events']:
            print(f"    - Event {event_id}: {count} occurrences")
    
    # Analyze events (using sample data or actual)
    print(f"\n[*] Running threat analysis on {len(events)} events...")
    print("-" * 70)
    analyzer = EventLogAnalyzer()
    analysis = analyzer.analyze_security_events(events)
    print(f"  Threat Summary: {analysis['threat_summary']}")
    print(f"  Critical Events Found: {len(analysis['critical_events'])}")
    print(f"  Suspicious Patterns: {len(analysis['suspicious_patterns'])}")
    if analysis['recommendations']:
        print(f"  Recommendations:")
        for rec in analysis['recommendations']:
            print(f"    - {rec}")
    
    # Save results to file
    print(f"\n[*] Saving results to file...")
    results = {
        "test_date": events[0].get('timestamp') if events else "N/A",
        "events_read": len(events),
        "sample_events": events[:10],
        "statistics": stats,
        "analysis": analysis
    }
    
    with open("test_results_day15.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("    ✓ Results saved to test_results_day15.json")
    
    print("\n" + "="*70)
    print("✓ DAY 15 TEST COMPLETE")
    print("="*70)
    print("\nSummary:")
    print(f"  - Read {len(events)} events from {log_name} log")
    print(f"  - Successfully parsed all events")
    print(f"  - Generated statistics and threat analysis")
    print(f"  - Results saved to JSON file")
    
    return True


if __name__ == "__main__":
    success = test_eventlog_reader()
    exit(0 if success else 1)
