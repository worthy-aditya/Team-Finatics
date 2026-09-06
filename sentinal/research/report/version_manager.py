
import json
from pathlib import Path
from datetime import datetime

REPORT_DIR = Path("reports")
METADATA = REPORT_DIR / "metadata.json"

def initialize():
    REPORT_DIR.mkdir(exist_ok=True)

    for folder in ["docx", "pdf", "md", "json"]:
        (REPORT_DIR / folder).mkdir(exist_ok=True)

    if not METADATA.exists():
        with open(METADATA, "w") as f:
            json.dump({"latest_version": 0, "created_reports": []}, f, indent=4)

def next_version(target_ip="Unknown"):
    initialize()

    with open(METADATA, "r") as f:
        data = json.load(f)

    version = data["latest_version"] + 1
    data["latest_version"] = version

    data["created_reports"].append({
        "version": version,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target": target_ip
    })

    with open(METADATA, "w") as f:
        json.dump(data, f, indent=4)

    return version