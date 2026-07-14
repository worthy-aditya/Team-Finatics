import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

DOMAINS = {
    "enterprise": DATA_DIR / "enterprise-attack.json",
    "mobile": DATA_DIR / "mobile-attack.json",
    "ics": DATA_DIR / "ics-attack.json"
}

def load_attack_data():
    """Load all MITRE ATT&CK STIX datasets into a dict keyed by domain."""
    datasets = {}
    for name, path in DOMAINS.items():
        with open(path) as f:
            datasets[name] = json.load(f)
    return datasets

def count_techniques_by_domain(datasets):
    """Return a dict of domain -> technique count."""
    counts = {}
    for name, data in datasets.items():
        techniques = [o for o in data["objects"] if o.get("type") == "attack-pattern"]
        counts[name] = len(techniques)
    return counts

def get_all_techniques(datasets):
    """Flatten techniques across all domains, tagged with their domain."""
    techniques = []
    for name, data in datasets.items():
        for obj in data["objects"]:
            if obj.get("type") == "attack-pattern":
                obj["_domain"] = name
                techniques.append(obj)
    return techniques

if __name__ == "__main__":
    datasets = load_attack_data()

    for name, data in datasets.items():
        print(name, "-> total objects:", len(data["objects"]))

    counts = count_techniques_by_domain(datasets)
    for name, count in counts.items():
        print(f"{name}: {count} techniques")

    techniques = get_all_techniques(datasets)
    print("Total techniques across all domains:", len(techniques))
