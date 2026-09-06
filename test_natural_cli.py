#!/usr/bin/env python
"""Test the natural CLI parsing"""

from sentinelai.natural_cli import NaturalLanguageCLI

cli = NaturalLanguageCLI()

print("=" * 60)
print("Testing Natural CLI Parsing")
print("=" * 60)

# Test 1: unsupported casual conversation
result = cli.parse_intent('hi there')
print(f"\nTest 1 - 'hi there':")
print(f"  Action: {result.get('action')}")
print(f"  Confidence: {result.get('confidence')}")

# Test 2: Command
result = cli.parse_intent('scan localhost quickly')
print(f"\nTest 2 - 'scan localhost quickly':")
print(f"  Action: {result.get('action')}")
print(f"  Target: {result.get('target')}")
print(f"  Scan Type: {result.get('scan_type')}")
print(f"  Confidence: {result.get('confidence')}")

# Test 3: bare target should not trigger a command
result = cli.parse_intent('localhost')
print(f"\nTest 3 - 'localhost':")
print(f"  Action: {result.get('action')}")
print(f"  Confidence: {result.get('confidence')}")

# Test 4: another unsupported greeting
result = cli.parse_intent('good morning')
print(f"\nTest 4 - 'good morning':")
print(f"  Action: {result.get('action')}")
print(f"  Confidence: {result.get('confidence')}")

# Test 5: Help command
result = cli.parse_intent('help')
print(f"\nTest 5 - 'help':")
print(f"  Action: {result.get('action')}")
print(f"  Confidence: {result.get('confidence')}")

# Test 6: Report command
result = cli.parse_intent('generate a json report')
print(f"\nTest 6 - 'generate a json report':")
print(f"  Action: {result.get('action')}")
print(f"  Format: {result.get('format')}")
print(f"  Confidence: {result.get('confidence')}")

print("\n" + "=" * 60)
print("✅ All tests completed!")
print("=" * 60)
