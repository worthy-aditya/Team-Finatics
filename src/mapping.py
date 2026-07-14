import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
OWASP_FILE = DATA_DIR / "owasp_top10.json"

# Common security terms that don't literally appear in OWASP's wording,
# mapped to a term that DOES appear in the relevant category.
SYNONYMS = {
    "sql injection": "injection",
    "sqli": "injection",
    "xss": "injection",
    "cross-site scripting": "injection",
    "encryption": "cryptographic",
    "encrypt": "cryptographic",
    "hashing": "cryptographic",
    "weak password": "authentication",
    "session hijacking": "authentication",
    "misconfigured": "misconfiguration",
    "outdated library": "supply chain",
    "outdated dependency": "supply chain",
    "csrf": "access control",
}


def load_owasp_data():
    """Load OWASP Top 10 data (dict with 'metadata' and 'categories')."""
    with open(OWASP_FILE) as f:
        return json.load(f)


def _normalize(keyword):
    """Lowercase, strip, and apply synonym substitution."""
    keyword_lower = keyword.lower().strip()
    return SYNONYMS.get(keyword_lower, keyword_lower)


def map_keyword_to_owasp(keyword, owasp_data=None):
    """
    Given a keyword, search OWASP Top 10 category names and descriptions
    for a match, and return the matching category name.
    Returns None if no match is found.
    """
    if owasp_data is None:
        owasp_data = load_owasp_data()

    search_term = _normalize(keyword)
    categories = owasp_data.get("categories", [])

    # Pass 1: exact/substring match against category name
    for category in categories:
        name = category.get("name", "")
        if search_term in name.lower():
            return name

    # Pass 2: substring match against full description
    for category in categories:
        description = (category.get("description") or "").lower()
        if search_term in description:
            return category.get("name")

    # Pass 3: word-level match — any single word from the keyword
    # appears in the name or description (catches multi-word inputs
    # like "sql injection" when only "injection" is present)
    words = search_term.split()
    for word in words:
        if len(word) < 4:  # skip tiny/common words
            continue
        for category in categories:
            name = category.get("name", "").lower()
            description = (category.get("description") or "").lower()
            if word in name or word in description:
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
        "ssrf",
        "authentication",
        "nonsense keyword"
    ]

    for kw in test_inputs:
        result = map_keyword_to_owasp(kw, owasp_data)
        print(f"'{kw}' -> {result}")