import json
from pathlib import Path

from framework_mapper import map_keyword


ROOT = Path(__file__).resolve().parents[1]
GROUND_TRUTH_DIR = ROOT / "data" / "ground_truth"
DATASET_FILES = [
    GROUND_TRUTH_DIR / "mitre_ground_truth.json",
    GROUND_TRUTH_DIR / "owasp_ground_truth.json",
    GROUND_TRUTH_DIR / "framework_ground_truth.json",
]


def test_ground_truth_keywords_are_reproducible_by_framework_mapper():
    observed = set()
    for file_path in DATASET_FILES:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        for item in payload:
            keyword = item["keyword"]
            observed.add(keyword)

    assert len(observed) >= 40, f"Ground-truth keyword coverage too low: {len(observed)}"

    for keyword in sorted(observed):
        result = map_keyword(keyword)
        assert result is not None, f"Keyword should map: {keyword}"
        assert result.get("owasp") is not None or result.get("mitre") is not None, (
            f"Keyword produced no framework mapping: {keyword}"
        )


def test_ground_truth_datasets_remain_overlap_aware():
    dataset_map = {}
    for file_path in DATASET_FILES:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        dataset_map[file_path.name] = {item["keyword"] for item in payload}

    union = set().union(*dataset_map.values())
    assert len(union) >= 40

    for file_name, keywords in dataset_map.items():
        for keyword in keywords:
            result = map_keyword(keyword)
            assert result is not None, f"{file_name} contains unmappable keyword: {keyword}"
