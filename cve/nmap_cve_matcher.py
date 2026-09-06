from cve_search import search_cves

sample_scan = {
    "host": "192.168.1.10",
    "services": [
        "Apache",
        "OpenSSH",
        "MySQL"
    ]
}

for service in sample_scan["services"]:

    print("=" * 60)
    print(f"Searching CVEs for: {service}")

    results = search_cves(service)

    if results:
     for cve in results:
        print("-" * 50)
        print("CVE ID:", cve["id"])
        print("Severity:", cve["severity"])
        print("CVSS Score:", cve["cvss_score"])
        print("Description:", cve["description"])