"""
framework_mapper.py

Single entry point that combines OWASP Top 10:2025 mapping and
MITRE ATT&CK technique mapping into one module.

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


def map_to_mitre(keyword):
    """
    Map a keyword to its MITRE ATT&CK technique.
    Returns a dict (id, name, description) or None.
    """
    return map_keyword_to_technique(keyword)


def map_keyword(keyword):
    """
    Map a single keyword against BOTH frameworks at once.

    Returns a dict:
    {
        "keyword": "sql injection",
        "owasp": { ... } or None,
        "mitre": { ... } or None
    }
    """
    return {
        "keyword": keyword,
        "owasp": map_to_owasp(keyword),
        "mitre": map_to_mitre(keyword),
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
            print(f"  MITRE -> {result['mitre']['id']} {result['mitre']['name']}")
        else:
            print("  MITRE -> No match")