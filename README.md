# Team-Finatics
This repository is made for the codequest project
# Team Finatics

## Description
This project maps common security-related keywords to their corresponding
**OWASP Top 10:2025** categories and cross-references them against the
**MITRE ATT&CK** framework (Enterprise, Mobile, and ICS matrices), to help
identify and classify security risks efficiently.

## Project Structure
```
Team-Finatics/
├── data/
│   ├── owasp_top10.json          # OWASP Top 10:2025 dataset
│   ├── owasp_notes.md            # Notes on the OWASP data structure
│   ├── enterprise-attack.json    # MITRE ATT&CK Enterprise STIX data
│   ├── mobile-attack.json        # MITRE ATT&CK Mobile STIX data
│   └── ics-attack.json           # MITRE ATT&CK ICS STIX data
├── owasp_mapper.py                # Keyword -> OWASP category mapping function
├── test_owasp_mapper.py           # Pytest test cases for the mapping function
├── requirements.txt
└── README.md
```

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/worthy-aditya/Team-Finatics.git
   cd Team-Finatics
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install pytest
   ```

4. **Run the test suite**
   ```bash
   pytest -v
   ```

5. **Try the mapping function directly**
   ```bash
   python owasp_mapper.py
   ```

## Usage Example
```python
from owasp_mapper import map_keyword_to_owasp

result = map_keyword_to_owasp("sql injection")
print(result["rank"], result["name"])
# Output: A05:2025 Injection
```

## Team
| Name | Focus Area |
|---|---|
| Sneha Das | OWASP Mapping, Testing & Documentation |

## Data Sources
- [OWASP Top 10:2025](https://owasp.org/Top10/2025/)
- [MITRE ATT&CK (cti repository)](https://github.com/mitre/cti)
