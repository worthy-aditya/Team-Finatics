"""
mitre_mapper.py

Maps a threat-related keyword (e.g. "phishing", "powershell") to the
matching MITRE ATT&CK technique — returning its T-number ID and name,
using data/enterprise-attack.json (STIX 2.x bundle).
"""

import json
import os

DEFAULT_DATA_PATH = os.path.join("data", "enterprise-attack.json")

# Cache so we don't reload/reparse the (large) STIX file on every call
_TECHNIQUE_CACHE = None


def load_mitre_data(path=DEFAULT_DATA_PATH):
    """Load the raw MITRE ATT&CK STIX bundle from disk."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_technique_id(stix_object):
    """
    Extract the T-number (e.g. 'T1059') from a STIX attack-pattern object's
    external_references. Returns None if not found.
    """
    for ref in stix_object.get("external_references", []):
        if ref.get("source_name") == "mitre-attack":
            return ref.get("external_id")
    return None


def _build_technique_index(mitre_data):
    """
    Build a flat list of techniques from the STIX bundle, each as:
    {"id": "T1059", "name": "...", "description": "..."}

    Skips deprecated/revoked techniques and sub-techniques' parent
    duplicates are kept (sub-techniques have their own T-number, e.g. T1059.001).
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
        })
    return techniques


def _get_technique_index(mitre_data=None, path=DEFAULT_DATA_PATH, force_reload=False):
    """Return the cached technique index, building it if needed."""
    global _TECHNIQUE_CACHE
    if _TECHNIQUE_CACHE is None or force_reload:
        if mitre_data is None:
            mitre_data = load_mitre_data(path)
        _TECHNIQUE_CACHE = _build_technique_index(mitre_data)
    return _TECHNIQUE_CACHE


def map_keyword_to_technique(keyword, mitre_data=None, path=DEFAULT_DATA_PATH):
    """
    Take a threat-related keyword and return the best-matching MITRE ATT&CK
    technique as a dict: {"id": "T1059", "name": "...", "description": "..."}

    Returns None if no match is found.

    Matching strategy:
      1. Exact (case-insensitive) match against technique name.
      2. Keyword found as a substring within the technique name.
      3. Keyword found within the technique description (weaker match,
         used only if nothing matched on the name).
    """
    if not keyword or not isinstance(keyword, str):
        return None

    keyword_lower = keyword.strip().lower()
    if not keyword_lower:
        return None

    techniques = _get_technique_index(mitre_data, path)

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
            print(f"'{kw}' -> {result['id']} {result['name']}")
        else:
            print(f"'{kw}' -> No match found")