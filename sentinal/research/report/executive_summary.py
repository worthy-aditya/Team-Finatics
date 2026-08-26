
from collections import Counter

def generate_executive_summary(scan_info, findings):
    """
    Generate a short executive summary for reports.
    """

    if not findings:
        return (
            f"SentinelAI analyzed {scan_info['target_ip']} and found no security findings."
        )

    severity_counts = Counter(f["severity"].lower() for f in findings)

    critical = severity_counts.get("critical", 0)
    high = severity_counts.get("high", 0)
    medium = severity_counts.get("medium", 0)
    low = severity_counts.get("low", 0)

    total = len(findings)

    summary = (
        f"SentinelAI analyzed the target system ({scan_info['target_ip']}) and identified "
        f"{total} security findings. "
        f"These include {critical} Critical, {high} High, "
        f"{medium} Medium, and {low} Low severity issues. "
        f"Known vulnerabilities were correlated with the NVD database where applicable. "
        f"Priority remediation is recommended for Critical and High findings."
    )

    return summary