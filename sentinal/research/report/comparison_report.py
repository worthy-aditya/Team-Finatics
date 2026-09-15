import json
import os
from pathlib import Path
from collections import Counter


BASE_DIR = Path(__file__).resolve().parents[3]
SNAPSHOT_DIR = BASE_DIR / "reports" / "snapshots"
COMPARISON_DIR = BASE_DIR / "reports" / "comparisons"


def load_version(version):
    """Load a saved report snapshot."""

    file_path = SNAPSHOT_DIR / f"version_{version}.json"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Version {version} does not exist."
        )

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_severity_counts(findings):
    """Count findings by severity."""

    counts = Counter()

    for finding in findings:
        severity = finding.get("severity", "Unknown").lower()
        counts[severity] += 1

    return counts

def finding_key(finding):
    """
    Create a unique identifier for a security finding.
    """

    return (
        str(finding.get("service", "")).lower(),
        str(finding.get("port", "")).lower(),
        str(finding.get("cve_id", "")).lower()
    )

def detect_finding_changes(old_findings, new_findings):
    """
    Detect new, removed and unchanged findings.
    """

    old_map = {
        finding_key(f): f
        for f in old_findings
    }

    new_map = {
        finding_key(f): f
        for f in new_findings
    }

    old_keys = set(old_map.keys())
    new_keys = set(new_map.keys())

    new_keys_only = new_keys - old_keys
    removed_keys = old_keys - new_keys
    unchanged_keys = old_keys & new_keys

    return {
        "new": [
            new_map[key]
            for key in new_keys_only
        ],
        "removed": [
            old_map[key]
            for key in removed_keys
        ],
        "unchanged": [
            new_map[key]
            for key in unchanged_keys
        ]
    }


def compare_versions(version1, version2):
    """Compare two SentinelAI report versions."""

    old_report = load_version(version1)
    new_report = load_version(version2)

    old_findings = old_report.get("findings", [])
    new_findings = new_report.get("findings", [])

    old_counts = get_severity_counts(old_findings)
    new_counts = get_severity_counts(new_findings)

    changes = detect_finding_changes(
    old_findings,
    new_findings
)

    comparison = {
    "version_1": version1,
    "version_2": version2,
    "old_total": len(old_findings),
    "new_total": len(new_findings),
    "severity_changes": {},
    "new_findings": changes["new"],
    "removed_findings": changes["removed"],
    "unchanged_findings": changes["unchanged"]
}

    severities = [
        "critical",
        "high",
        "medium",
        "low"
    ]

    for severity in severities:

        old_count = old_counts.get(severity, 0)
        new_count = new_counts.get(severity, 0)

        comparison["severity_changes"][severity] = {
            "old": old_count,
            "new": new_count,
            "difference": new_count - old_count
        }

    return comparison

def generate_comparison_report(version1, version2):

    comparison = compare_versions(version1, version2)

    COMPARISON_DIR.mkdir(exist_ok=True)

    output_file = (
        COMPARISON_DIR /
        f"compare_v{version1}_v{version2}.md"
    )

    old_total = comparison["old_total"]
    new_total = comparison["new_total"]

    if new_total > old_total:
        risk_status = "INCREASED"
    elif new_total < old_total:
        risk_status = "DECREASED"
    else:
        risk_status = "UNCHANGED"

    with open(output_file, "w", encoding="utf-8") as f:

        f.write("# SentinelAI Report Comparison\n\n")

        f.write(
            f"**Version {version1} → Version {version2}**\n\n"
        )

        f.write("## Finding Summary\n\n")

        f.write(
            f"- Version {version1}: **{old_total} findings**\n"
        )

        f.write(
            f"- Version {version2}: **{new_total} findings**\n\n"
        )

        f.write("## Severity Changes\n\n")

        f.write(
            "| Severity | Old | New | Difference |\n"
        )

        f.write(
            "|---|---:|---:|---:|\n"
        )

        for severity, values in comparison[
            "severity_changes"
        ].items():

            f.write(
                f"| {severity.capitalize()} "
                f"| {values['old']} "
                f"| {values['new']} "
                f"| {values['difference']:+} |\n"
            )

        f.write("\n## New Findings\n\n")

        if comparison["new_findings"]:
            for finding in comparison["new_findings"]:
                service = finding.get("service", "Unknown")
                port = finding.get("port", "Unknown")
                severity = finding.get("severity", "Unknown")
                cve = finding.get("cve_id", "")

                if cve:
                    f.write(
                        f"- **{service}** (Port {port}) "
                        f"- {severity} - {cve}\n"
                    )
                else:
                    f.write(
                        f"- **{service}** (Port {port}) "
                        f"- {severity}\n"
                    )
        else:
            f.write("No new findings.\n")

        f.write("\n## Removed Findings\n\n")

        if comparison["removed_findings"]:
            for finding in comparison["removed_findings"]:
                service = finding.get("service", "Unknown")
                port = finding.get("port", "Unknown")
                severity = finding.get("severity", "Unknown")
                cve = finding.get("cve_id", "")

                if cve:
                    f.write(
                        f"- **{service}** (Port {port}) "
                        f"- {severity} - {cve}\n"
                    )
                else:
                    f.write(
                        f"- **{service}** (Port {port}) "
                        f"- {severity}\n"
                    )
        else:
            f.write("No removed findings.\n")

        f.write("\n## Unchanged Findings\n\n")

        if comparison["unchanged_findings"]:
            for finding in comparison["unchanged_findings"]:
                service = finding.get("service", "Unknown")
                port = finding.get("port", "Unknown")
                severity = finding.get("severity", "Unknown")

                f.write(
                    f"- **{service}** (Port {port}) - {severity}\n"
                )
        else:
            f.write("No unchanged findings.\n")

        f.write("\n## Overall Risk\n\n")
        f.write(f"**{risk_status}**\n")

    print("Comparison report generated successfully!")
    print(f"Saved at: {output_file}")

    return output_file