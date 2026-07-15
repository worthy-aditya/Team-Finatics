import requests # type: ignore
#This library lets Python communicate with web APIs.

cve_id = "CVE-2021-44228"
# CVE ID to search

url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"
# NVD API endpoint

response = requests.get(url)
# Send GET request

if response.status_code == 200:

    data = response.json()

    cve = data["vulnerabilities"][0]["cve"]

    print("=" * 50)
    print("CVE ID:", cve["id"])
    print("Published:", cve["published"])
    print("Last Modified:", cve["lastModified"])
    print()
    print("Description:")
    print(cve["descriptions"][0]["value"])
    print("=" * 50)

else:
    print("Error:", response.status_code)



"""
===============================================================================
                          SentinelAI - Developer Notes
===============================================================================

1. What is an API?
------------------
API (Application Programming Interface) is a communication interface that allows
one software application to interact with another. In this project, our Python
program communicates with the National Vulnerability Database (NVD) API to
retrieve vulnerability information.

2. What is a REST API?
----------------------
REST (Representational State Transfer) is a web service architecture that uses
HTTP methods such as GET, POST, PUT, and DELETE for communication.

HTTP Methods:
- GET    : Retrieve data
- POST   : Create new data
- PUT    : Update existing data
- DELETE : Remove data

Since we only need to retrieve vulnerability information, we use the GET method.

3. How does requests.get() work?
--------------------------------
The requests library sends an HTTP GET request to the specified URL.

Example:
    response = requests.get(url)

If the request is successful, the server returns:
- Status Code (e.g., 200)
- Response Body (JSON data)

Common Status Codes:
200 -> Success
400 -> Bad Request
401 -> Unauthorized
404 -> Resource Not Found
500 -> Internal Server Error

4. What is JSON?
----------------
JSON (JavaScript Object Notation) is a lightweight data format used for
storing and exchanging structured information.

Example:
{
    "id": "CVE-2021-44228",
    "published": "...",
    "descriptions": [
        {
            "value": "Remote Code Execution vulnerability..."
        }
    ]
}

Python automatically converts JSON into dictionaries and lists using:

    data = response.json()

5. How do we extract data from JSON?
------------------------------------
The NVD API returns nested JSON objects.

Hierarchy:

data
 └── vulnerabilities (list)
      └── [0]
           └── cve
                ├── id
                ├── published
                ├── lastModified
                └── descriptions
                     └── [0]
                          └── value

Accessing values:

cve = data["vulnerabilities"][0]["cve"]

cve["id"]
cve["published"]
cve["lastModified"]
cve["descriptions"][0]["value"]

6. How does the NVD API return data?
------------------------------------
The API returns a JSON response containing details about the requested CVE,
including:

- CVE ID
- Publication Date
- Last Modified Date
- Description
- Severity Metrics (CVSS)
- References
- Weaknesses (CWE)
- Configurations
- Vendor Information

For Day 3, we only extracted the basic fields required for the project
deliverable.

7. Why are we implementing this?
--------------------------------
This module is the foundation of SentinelAI's CVE Lookup feature.

Future workflow:

User Scan
    ↓
Identify Vulnerable Software
    ↓
Extract CVE ID
    ↓
Query NVD API
    ↓
Retrieve Vulnerability Details
    ↓
Calculate Severity
    ↓
Generate Security Report

In later phases, this module will be integrated with:
- Nmap Scan Results
- Severity Scoring
- Report Generation (DOCX/PDF/Markdown)
- AI Explanation Module

===============================================================================
Day 3 Deliverable:
✓ Successfully queried CVE-2021-44228 (Log4Shell) using the NVD API.
✓ Parsed the JSON response.
✓ Displayed vulnerability details in a readable format.
===============================================================================
"""