"""
mitre_mapper.py

Maps a threat-related keyword (e.g. "phishing", "powershell") to the
matching MITRE ATT&CK technique — returning its T-number ID, name, and
which matrix (domain) it came from.

Searches across all three ATT&CK matrices so the mapper is useful for
students, bug bounty hunters, red/blue teams, and enterprises covering
IT, mobile, and industrial/OT environments alike:
  - Enterprise -> data/enterprise-attack.json
  - Mobile     -> data/mobile-attack.json
  - ICS        -> data/ics-attack.json
"""

import json
import os

DATA_SOURCES = {
    "enterprise": os.path.join("data", "enterprise-attack.json"),
    "mobile": os.path.join("data", "mobile-attack.json"),
    "ics": os.path.join("data", "ics-attack.json"),
}

# Cache so we don't reload/reparse the (large) STIX files on every call
_TECHNIQUE_CACHE = None


def load_mitre_data(path):
    """
    Load a raw MITRE ATT&CK STIX 2.x bundle from disk.

    Args:
        path (str): Path to a MITRE ATT&CK JSON file
                     (e.g. "data/enterprise-attack.json").

    Returns:
        dict: The parsed STIX bundle. The techniques live under the
              "objects" key as items with "type": "attack-pattern".

    Example:
        >>> data = load_mitre_data("data/enterprise-attack.json")
        >>> data["objects"][0]["type"]
        'attack-pattern'
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_technique_id(stix_object):
    """
    Extract the T-number (e.g. 'T1059') from a STIX attack-pattern object's
    external_references list.

    Args:
        stix_object (dict): A single STIX object of type "attack-pattern".

    Returns:
        str | None: The MITRE technique ID (e.g. "T1059.001"), or None
            if no mitre-attack reference is present.
    """
    for ref in stix_object.get("external_references", []):
        if ref.get("source_name") == "mitre-attack":
            return ref.get("external_id")
    return None


def _build_technique_index(mitre_data, domain):
    """
    Build a flat list of techniques from a STIX bundle.

    Filters out revoked and deprecated techniques, since those no longer
    represent current, valid ATT&CK techniques.

    Args:
        mitre_data (dict): Parsed STIX bundle (from load_mitre_data()).
        domain (str): Label for which matrix this data came from
                       ("enterprise", "mobile", or "ics").

    Returns:
        list[dict]: Each item is {"id", "name", "description", "domain"}.
    """
    techniques = []
    for obj in mitre_data.get("objects", []):
        if obj.get("type") != "attack-pattern":
            continue
        if obj.get("revoked") or obj.get("x_mitre_deprecated"):
            continue

        tid = _get_technique_id(obj)
        if not tid:
            continue

        techniques.append({
            "id": tid,
            "name": obj.get("name", ""),
            "description": obj.get("description", ""),
            "domain": domain,
        })
    return techniques


def _get_technique_index(sources=None, force_reload=False):
    """
    Return the cached, combined technique index across all matrices,
    building it from disk if it hasn't been built yet.

    Args:
        sources (dict, optional): Custom {domain: path} mapping, used to
            inject test fixtures instead of the real large datasets.
            When provided, results are NOT cached (so tests stay isolated).
        force_reload (bool): If True, rebuild the cache from DATA_SOURCES
            even if it already exists.

    Returns:
        list[dict]: Combined technique list across all requested matrices.
    """
    global _TECHNIQUE_CACHE
    if _TECHNIQUE_CACHE is None or force_reload or sources is not None:
        active_sources = sources if sources is not None else DATA_SOURCES
        combined = []
        for domain, path in active_sources.items():
            if not os.path.exists(path):
                continue  # skip matrices the user hasn't downloaded
            data = load_mitre_data(path)
            combined.extend(_build_technique_index(data, domain))

        if sources is not None:
            return combined  # don't cache custom test sources
        _TECHNIQUE_CACHE = combined
    return _TECHNIQUE_CACHE


def map_keyword_to_technique(keyword, sources=None, domain=None):
    """
    Map a threat-related keyword to the best-matching MITRE ATT&CK technique.

    Matching strategy (first match wins, checked in this order):
      1. Exact (case-insensitive) match against the technique name.
      2. Keyword found as a substring within the technique name.
      3. Keyword found within the technique description (weaker fallback).

    Args:
        keyword (str): Search term, e.g. "phishing" or "powershell".
        sources (dict, optional): Custom {domain: path} override, used
            in tests instead of the real datasets.
        domain (str, optional): Restrict the search to a single matrix
            ("enterprise", "mobile", or "ics"). Defaults to searching
            all three.

    Returns:
        dict | None: {"id": "T1566", "name": "Phishing",
            "description": "...", "domain": "enterprise"}, or None if
            no technique matches.

    Example:
        >>> result = map_keyword_to_technique("phishing")
        >>> result["id"], result["domain"]
        ('T1566', 'enterprise')

        >>> map_keyword_to_technique("nonsense keyword xyz")  # no match
        None

        >>> map_keyword_to_technique("phishing", domain="mobile")
        {'id': 'T1660', 'name': 'Phishing', ...}
    """
    if not keyword or not isinstance(keyword, str):
        return None

    keyword_lower = keyword.strip().lower()
    if not keyword_lower:
        return None

    techniques = _get_technique_index(sources)

    if domain:
        techniques = [t for t in techniques if t["domain"] == domain]

    # Pass 1: exact name match
    for tech in techniques:
        if tech["name"].lower() == keyword_lower:
            return tech

    # Pass 2: keyword is a substring of the technique name
    for tech in techniques:
        if keyword_lower in tech["name"].lower():
            return tech

    # Pass 3: fall back to description match
    for tech in techniques:
        if keyword_lower in tech["description"].lower():
            return tech

    return None


if __name__ == "__main__":
    test_keywords = ["phishing", "powershell", "made up nonsense technique"]
    for kw in test_keywords:
        result = map_keyword_to_technique(kw)
        if result:
            print(f"'{kw}' -> {result['id']} {result['name']} [{result['domain']}]")
        else:
            print(f"'{kw}' -> No match found")