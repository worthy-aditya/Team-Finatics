"""
framework_mapper.py

Single entry point that combines OWASP Top 10:2025 mapping and
MITRE ATT&CK technique mapping (Enterprise, Mobile, ICS) into one module.

Wraps owasp_mapper.map_keyword_to_owasp() and
mitre_mapper.map_keyword_to_technique() so callers only need to
import from one place.
"""

from owasp_mapper import map_keyword_to_owasp
from mitre_mapper import map_keyword_to_technique


def map_to_owasp(keyword):
    """
    Map a keyword to its OWASP Top 10:2025 category.
    Returns a dict (rank, name, description, ...) or None.
    """
    return map_keyword_to_owasp(keyword)


def map_to_mitre(keyword, domain=None):
    """
    Map a keyword to its MITRE ATT&CK technique.

    Args:
        keyword: search term, e.g. "phishing"
        domain: optionally restrict to "enterprise", "mobile", or "ics".
                Defaults to searching all three.

    Returns a dict (id, name, description, domain) or None.
    """
    return map_keyword_to_technique(keyword, domain=domain)


def map_keyword(keyword, mitre_domain=None):
    """
    Map a single keyword against BOTH frameworks at once.

    Args:
        keyword: search term, e.g. "sql injection"
        mitre_domain: optionally restrict the MITRE side of the lookup
                      to one matrix ("enterprise", "mobile", or "ics").

    Returns a dict:
    {
        "keyword": "sql injection",
        "owasp": { ... } or None,
        "mitre": { ... } or None   # includes "domain" field when matched
    }
    """
    return {
        "keyword": keyword,
        "owasp": map_to_owasp(keyword),
        "mitre": map_to_mitre(keyword, domain=mitre_domain),
    }


if __name__ == "__main__":
    test_keywords = ["sql injection", "phishing", "misconfiguration", "powershell"]

    for kw in test_keywords:
        result = map_keyword(kw)
        print(f"\nKeyword: '{kw}'")

        if result["owasp"]:
            print(f"  OWASP -> {result['owasp']['rank']} {result['owasp']['name']}")
        else:
            print("  OWASP -> No match")

        if result["mitre"]:
            m = result["mitre"]
            print(f"  MITRE -> {m['id']} {m['name']} [{m['domain']}]")
        else:
            print("  MITRE -> No match")