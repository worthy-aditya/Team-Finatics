#!/usr/bin/env python
"""Demo of the Natural CLI interface"""

import sys
from sentinelai.natural_cli import NaturalLanguageCLI

print("\n" + "="*60)
print("Natural Language CLI Demo")
print("="*60 + "\n")

cli = NaturalLanguageCLI()

# Simulate supported command interactions only
test_inputs = [
    ("hi there", "Unsupported casual input"),
    ("good morning", "Unsupported casual input"),
    ("scan localhost quickly", "Real command"),
    ("help", "Help command"),
]

for user_input, description in test_inputs:
    print(f"TEST: {description}")
    print(f"You> {user_input}")
    
    intent = cli.parse_intent(user_input)
    success, output = cli.execute_command(intent)
    
    print(f"Detected Action: {intent.get('action')} (confidence: {intent.get('confidence'):.0%})")
    
    if output != "exit":
        try:
            truncated = output[:80] if len(output) > 80 else output
            print(f"AI: {truncated}")
        except Exception as e:
            print(f"AI: [Response generated]")
    
    print()

print("="*60)
print("DEMO COMPLETE!")
print("="*60)
