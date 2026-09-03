import json

with open('test_results_day16.json', 'r') as f:
    data = json.load(f)

print(f"Test Results Summary:")
print(f"Total Scenarios: {data['test_count']}")
print()

for scenario in data['scenarios']:
    print(f"  Scenario: {scenario['name']}")
    print(f"    Threat Level: {scenario['threat_level']}")
    print(f"    Total Alerts: {scenario['total_alerts']}")
    print(f"    Brute Force Detected: {scenario['brute_force_detected']}")
    print(f"    Account Changes: {scenario['account_changes']}")
    print()
