import json
from pathlib import Path
from datetime import datetime


# Project root:
# team-finatics/
BASE_DIR = Path(__file__).resolve().parents[3]

# Local CVE cache directory
CACHE_DIR = BASE_DIR / "reports" / "cve_cache"


def get_cache_file(cve_id):
    """
    Return the cache file path for a CVE.
    """

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    return CACHE_DIR / f"{cve_id}.json"


def get_cached_cve(cve_id):
    """
    Check whether a CVE exists in the local cache.

    Returns:
        dict if cached
        None if not cached
    """

    cache_file = get_cache_file(cve_id)

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"[CACHE] Found {cve_id} in local cache.")
        return data

    except (json.JSONDecodeError, OSError) as e:
        print(f"[CACHE] Error reading cache: {e}")
        return None


def save_cve_to_cache(cve_data):
    """
    Save CVE information to the local cache.
    """

    if not cve_data or "id" not in cve_data:
        return

    cve_id = cve_data["id"]

    cache_file = get_cache_file(cve_id)

    cached_data = {
        **cve_data,
        "cached_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }

    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cached_data, f, indent=4)

        print(f"[CACHE] Saved {cve_id} to local cache.")

    except OSError as e:
        print(f"[CACHE] Error saving cache: {e}")