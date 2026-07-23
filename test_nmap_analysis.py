import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Mock Nmap output — standing in for Affan's real scan output until it's ready
sample_scan = """
PORT     STATE SERVICE      VERSION
22/tcp   open  ssh          OpenSSH 7.4
80/tcp   open  http         Apache httpd 2.4.6
445/tcp  open  microsoft-ds Samba smbd 4.6.2
3306/tcp open  mysql        MySQL 5.5.60
"""

NMAP_ANALYSIS_PROMPT = """
You are a cybersecurity analyst assistant helping a student understand
the security implications of a network scan.

Below is raw Nmap scan output for a target host:

{scan_data}

Please provide:
1. A plain-English summary of what was found (open ports, services, versions)
2. Which findings represent the highest security risk, and why
3. What an attacker could potentially do with this information

Keep the explanation clear enough for someone learning cybersecurity,
but technically accurate.
"""

prompt = NMAP_ANALYSIS_PROMPT.format(scan_data=sample_scan)

response = client.models.generate_content(
    model="gemini-flash-latest",
    contents=prompt
)

print(response.text)