"""Day 57 unit tests for provider health profiles (Week 9).

Offline, pure functions - no LLM or network. Covers save/load round-trips,
listing, deletion, name validation (path-traversal safety), corrupt/missing
profiles, and the --profile flag parity across both analyze entry points.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest

from sentinelai.health_profiles import (
    DEFAULT_PROFILES_DIR,
    delete_profile,
    list_profiles,
    load_profile,
    profile_exists,
    profile_path,
    save_profile,
)


def _tmp_dir():
    import tempfile

    return tempfile.mkdtemp()


def test_save_and_load_round_trip():
    d = _tmp_dir()
    save_profile("baseline", {"gemini": 90.0, "ollama": 80.0}, profiles_dir=d)
    loaded = load_profile("baseline", profiles_dir=d)
    assert loaded == {"gemini": 90.0, "ollama": 80.0}


def test_saved_profile_is_json_document():
    d = _tmp_dir()
    path = save_profile("demo", {"gemini": 75.0}, profiles_dir=d)
    assert path.name == "demo.json"
    import json

    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["name"] == "demo"
    assert doc["scores"] == {"gemini": 75.0}
    assert "saved_at" in doc


def test_list_profiles_sorted():
    d = _tmp_dir()
    save_profile("zeta", {"gemini": 90.0}, profiles_dir=d)
    save_profile("alpha", {"gemini": 80.0}, profiles_dir=d)
    assert list_profiles(profiles_dir=d) == ["alpha", "zeta"]


def test_list_profiles_empty_when_no_dir():
    d = _tmp_dir()
    assert list_profiles(profiles_dir=d) == []


def test_delete_profile():
    d = _tmp_dir()
    save_profile("temp", {"gemini": 90.0}, profiles_dir=d)
    assert delete_profile("temp", profiles_dir=d) is True
    assert delete_profile("temp", profiles_dir=d) is False
    assert profile_exists("temp", profiles_dir=d) is False


def test_profile_exists():
    d = _tmp_dir()
    save_profile("here", {"gemini": 90.0}, profiles_dir=d)
    assert profile_exists("here", profiles_dir=d) is True
    assert profile_exists("missing", profiles_dir=d) is False


def test_load_missing_raises():
    d = _tmp_dir()
    with pytest.raises(FileNotFoundError):
        load_profile("nope", profiles_dir=d)


def test_load_corrupt_raises_value_error():
    d = _tmp_dir()
    Path(d, "bad.json").write_text("{ not valid json", encoding="utf-8")
    with pytest.raises(ValueError):
        load_profile("bad", profiles_dir=d)


def test_save_overwrites_existing():
    d = _tmp_dir()
    save_profile("p", {"gemini": 90.0}, profiles_dir=d)
    save_profile("p", {"gemini": 40.0, "ollama": 50.0}, profiles_dir=d)
    assert load_profile("p", profiles_dir=d) == {"gemini": 40.0, "ollama": 50.0}
    # Still a single profile file, not duplicated.
    assert list_profiles(profiles_dir=d) == ["p"]


def test_invalid_names_rejected():
    d = _tmp_dir()
    for bad in ["", "../evil", "a/b", "with space", ".hidden", "name.json"]:
        with pytest.raises(ValueError):
            save_profile(bad, {"gemini": 90.0}, profiles_dir=d)


def test_valid_name_with_dash_underscore():
    d = _tmp_dir()
    save_profile("known_good-v2", {"gemini": 90.0}, profiles_dir=d)
    assert profile_exists("known_good-v2", profiles_dir=d) is True


def test_save_empty_scores_rejected():
    d = _tmp_dir()
    with pytest.raises(ValueError):
        save_profile("empty", {}, profiles_dir=d)


def test_save_non_numeric_score_rejected():
    d = _tmp_dir()
    with pytest.raises(ValueError):
        save_profile("bad", {"gemini": "not-a-number"}, profiles_dir=d)


def test_profile_path_traversal_blocked():
    # profile_path must never resolve outside the profiles dir.
    with pytest.raises(ValueError):
        profile_path("../../etc/passwd")


def test_default_profiles_dir_constant():
    assert DEFAULT_PROFILES_DIR == "provider_profiles"


def test_profile_flag_on_both_analyze_entry_points():
    # Day 4/57 sync: --profile must exist on both analyze entry points.
    from commands.analyze import analyze as analyze_root
    from sentinelai.cli import analyze as analyze_pkg

    root_opts = {o for p in analyze_root.params for o in p.opts}
    pkg_opts = {o for p in analyze_pkg.params for o in p.opts}
    assert "--profile" in root_opts, "root analyze missing --profile"
    assert "--profile" in pkg_opts, "sentinelai/cli.py analyze missing --profile"


def _main() -> None:
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  PASS  {fn.__name__}")
    print(f"ALL {len(fns)} day57 health-profile TESTS PASSED (offline, pure functions)")


if __name__ == "__main__":
    _main()
