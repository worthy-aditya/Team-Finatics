import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
OWASP_FILE = DATA_DIR / "owasp_top10.json"


def load_owasp_data():
    """Load OWASP Top 10 data (dict with 'metadata' and 'categories')."""
    with open(OWASP_FILE) as f:
        return json.load(f)


def map_keyword_to_owasp(keyword, owasp_data=None):
    """
    Given a keyword, search OWASP Top 10 category names and descriptions
    for a match, and return the matching category name.
    Returns None if no match is found.
    """
    if owasp_data is None:
        owasp_data = load_owasp_data()

    keyword_lower = keyword.lower().strip()
    categories = owasp_data.get("categories", [])

    # First pass: match against category name (most reliable)
    for category in categories:
        name = category.get("name", "")
        if keyword_lower in name.lower():
            return name

    # Second pass: fall back to matching inside the description
    for category in categories:
        description = category.get("description", "") or ""
        if keyword_lower in description.lower():
            return category.get("name")

    return None


def get_category_by_rank(rank, owasp_data=None):
    """Bonus helper: look up a category directly by rank, e.g. 'A01:2025'."""
    if owasp_data is None:
        owasp_data = load_owasp_data()

    for category in owasp_data.get("categories", []):
        if category.get("rank") == rank:
            return category
    return None


if __name__ == "__main__":
    owasp_data = load_owasp_data()

    test_inputs = [
        "sql injection",
        "encryption",
        "access control",
        "logging",
        "supply chain",
        "ssrf",              # tests the consolidation note in the description
        "authentication",
        "nonsense keyword"   # should return None
    ]

    for kw in test_inputs:
        result = map_keyword_to_owasp(kw, owasp_data)
        print(f"'{kw}' -> {result}")