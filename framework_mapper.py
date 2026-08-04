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

    Args:
        keyword (str): Free-text security term, e.g. "sql injection".

    Returns:
        dict | None: OWASP category dict (rank, name, description, ...),
            or None if no match is found.

    Example:
        >>> map_to_owasp("sql injection")["rank"]
        'A05:2025'
    """
    return map_keyword_to_owasp(keyword)


def map_to_mitre(keyword, domain=None):
    """
    Map a keyword to its MITRE ATT&CK technique.

    Args:
        keyword (str): Search term, e.g. "phishing".
        domain (str, optional): Restrict to "enterprise", "mobile", or
            "ics". Defaults to searching all three matrices.

    Returns:
        dict | None: {"id", "name", "description", "domain"}, or None
            if no technique matches.

    Example:
        >>> map_to_mitre("phishing")["id"]
        'T1566'
    """
    return map_keyword_to_technique(keyword, domain=domain)


def map_keyword(keyword, mitre_domain=None):
    """
    Map a single keyword against BOTH frameworks (OWASP and MITRE) at once.

    Useful for a single "what is this?" lookup that gives both the risk
    category (OWASP) and the real-world attacker technique (MITRE) in
    one call, which is the core purpose of this project.

    Args:
        keyword (str): Search term, e.g. "sql injection".
        mitre_domain (str, optional): Restrict the MITRE side of the
            lookup to one matrix ("enterprise", "mobile", or "ics").

    Returns:
        dict: {
            "keyword": <the original input>,
            "owasp": <OWASP category dict or None>,
            "mitre": <MITRE technique dict or None>
        }

    Example:
        >>> result = map_keyword("phishing")
        >>> result["mitre"]["id"]
        'T1566'
        >>> result["owasp"]  # phishing has no direct OWASP Top 10 category
        None
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