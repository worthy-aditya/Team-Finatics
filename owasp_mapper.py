"""
owasp_mapper.py

Maps a security-related keyword (e.g. "sql injection", "misconfiguration")
to its corresponding OWASP Top 10:2025 category, using data/owasp_top10.json.
"""

import json
import os

DEFAULT_DATA_PATH = os.path.join("data", "owasp_top10.json")

# Keyword -> OWASP 2025 rank lookup table
KEYWORD_MAP = {
    "access control": "A01:2025",
    "bola": "A01:2025",
    "bfla": "A01:2025",
    "ssrf": "A01:2025",
    "unauthorized": "A01:2025",

    "misconfiguration": "A02:2025",
    "default credentials": "A02:2025",
    "default password": "A02:2025",
    "open bucket": "A02:2025",

    "supply chain": "A03:2025",
    "dependency": "A03:2025",
    "third-party": "A03:2025",
    "third party": "A03:2025",
    "outdated component": "A03:2025",

    "crypto": "A04:2025",
    "encryption": "A04:2025",
    "weak hash": "A04:2025",
    "cleartext": "A04:2025",

    "injection": "A05:2025",
    "sql injection": "A05:2025",
    "xss": "A05:2025",
    "command injection": "A05:2025",

    "insecure design": "A06:2025",
    "threat modeling": "A06:2025",

    "authentication": "A07:2025",
    "login": "A07:2025",
    "password": "A07:2025",
    "session": "A07:2025",
    "brute force": "A07:2025",

    "integrity": "A08:2025",
    "ci/cd": "A08:2025",
    "unsigned": "A08:2025",
    "deserialization": "A08:2025",

    "logging": "A09:2025",
    "monitoring": "A09:2025",
    "alerting": "A09:2025",

    "exception": "A10:2025",
    "error handling": "A10:2025",
    "crash": "A10:2025",
    "fail open": "A10:2025",
}


def load_owasp_data(path=DEFAULT_DATA_PATH):
    """
    Load the OWASP Top 10:2025 dataset from disk.

    Args:
        path (str): Path to the OWASP Top 10 JSON file.
                     Defaults to "data/owasp_top10.json".

    Returns:
        dict: Parsed JSON with keys "metadata", "categories", "consolidations".

    Raises:
        FileNotFoundError: If the file does not exist at the given path.
        json.JSONDecodeError: If the file is not valid JSON.

    Example:
        >>> data = load_owasp_data()
        >>> len(data["categories"])
        10
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def map_keyword_to_owasp(keyword, owasp_data=None):
    """
    Map a free-text keyword to its matching OWASP Top 10:2025 category.

    Matching is case-insensitive and checks whether any known indicator
    phrase (from KEYWORD_MAP) appears as a substring of the input keyword.
    Longer, more specific phrases are checked before shorter ones, so
    "sql injection" matches before the more general "injection".

    Args:
        keyword (str): Free-text security term, e.g. "sql injection".
        owasp_data (dict, optional): Pre-loaded OWASP dataset (as returned
            by load_owasp_data()). If not provided, it is loaded automatically
            from DEFAULT_DATA_PATH.

    Returns:
        dict | None: The matching category dict (rank, name, description, ...)
            from owasp_top10.json, or None if no keyword match is found.

    Example:
        >>> result = map_keyword_to_owasp("sql injection")
        >>> result["rank"], result["name"]
        ('A05:2025', 'Injection')

        >>> map_keyword_to_owasp("banana smoothie")  # no match
        None
    """
    if not keyword or not isinstance(keyword, str):
        return None

    if owasp_data is None:
        owasp_data = load_owasp_data()

    keyword_lower = keyword.strip().lower()

    matched_rank = None
    # Sort by length descending so more specific phrases match before
    # shorter, more general ones (e.g. "sql injection" before "injection")
    for key in sorted(KEYWORD_MAP, key=len, reverse=True):
        if key in keyword_lower:
            matched_rank = KEYWORD_MAP[key]
            break

    if not matched_rank:
        return None

    for category in owasp_data["categories"]:
        if category["rank"] == matched_rank:
            return category

    return None


if __name__ == "__main__":
    # Quick manual check
    test_keywords = ["sql injection", "misconfiguration", "banana smoothie"]
    for kw in test_keywords:
        result = map_keyword_to_owasp(kw)
        if result:
            print(f"'{kw}' -> {result['rank']} {result['name']}")
        else:
            print(f"'{kw}' -> No match found")