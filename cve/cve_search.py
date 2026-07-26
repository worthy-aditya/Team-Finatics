import requests

def search_cves(keyword):

    url = (
        "https://services.nvd.nist.gov/rest/json/cves/2.0"
        f"?keywordSearch={keyword}&resultsPerPage=5"
    )

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:

            data = response.json()

            results = []

            for vulnerability in data["vulnerabilities"]:

                cve = vulnerability["cve"]

                metrics = cve.get("metrics", {})

                score = "N/A"
                severity = "UNKNOWN"

                if "cvssMetricV31" in metrics:
                    cvss = metrics["cvssMetricV31"][0]["cvssData"]
                elif "cvssMetricV30" in metrics:
                    cvss = metrics["cvssMetricV30"][0]["cvssData"]
                elif "cvssMetricV2" in metrics:
                    cvss = metrics["cvssMetricV2"][0]["cvssData"]
                else:
                    cvss = None

                if cvss:
                    print(cvss)
                    score = cvss.get("baseScore", "N/A")
                    severity = cvss.get("baseSeverity", "UNKNOWN")

                results.append({
                    "id": cve["id"],
                    "description": cve["descriptions"][0]["value"],
                    "cvss_score": score,
                    "severity": severity
                })

            return results

        else:
            print("Error:", response.status_code)

    except requests.exceptions.RequestException as e:
        print(f"Network Error: {e}")

    

if __name__ == "__main__":

    results = search_cves("Windows")

    if results:
        for cve in results:
            print("-" * 60)
            print("CVE ID:", cve["id"])
            print("Severity:", cve["severity"])
            print("CVSS Score:", cve["cvss_score"])
            print("Description:", cve["description"])