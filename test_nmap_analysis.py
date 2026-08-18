import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Load Affan's real scan output
with open("scan_results.json") as f:
    scan_data = json.load(f)

NMAP_ANALYSIS_PROMPT = """
You are a cybersecurity analyst assistant helping a student understand
the security implications of a network scan.

Below is structured Nmap scan output (JSON) for a target host:

{scan_data}

Please provide:
1. A plain-English summary of what was found (open ports, services, versions)
2. Which findings represent the highest security risk, and why
3. What an attacker could potentially do with this information

Keep the explanation clear enough for someone learning cybersecurity,
but technically accurate.
"""

prompt = NMAP_ANALYSIS_PROMPT.format(scan_data=json.dumps(scan_data, indent=2))

response = client.models.generate_content(
    model="gemini-flash-latest",
    contents=prompt
)

print(response.text)