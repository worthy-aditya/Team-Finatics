import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GROUND_TRUTH_DIR = ROOT / "data" / "ground_truth"
DATASET_FILES = [
    GROUND_TRUTH_DIR / "mitre_ground_truth.json",
    GROUND_TRUTH_DIR / "owasp_ground_truth.json",
    GROUND_TRUTH_DIR / "framework_ground_truth.json",
]


def test_ground_truth_datasets_exist_and_share_valid_schema():
    assert GROUND_TRUTH_DIR.exists(), "Ground-truth directory is missing"

    for file_path in DATASET_FILES:
        assert file_path.exists(), f"Missing dataset: {file_path.name}"
        data = json.loads(file_path.read_text(encoding="utf-8"))
        assert isinstance(data, list)
        assert len(data) >= 10

        for item in data:
            assert isinstance(item, dict)
            assert "keyword" in item
            assert isinstance(item["keyword"], str) and item["keyword"].strip()

            if "expected" in item:
                assert item["expected"] is not None
                assert "context" in item and isinstance(item["context"], str)

            if "expected_owasp" in item or "expected_mitre" in item:
                assert "expected_owasp" in item or "expected_mitre" in item


def test_ground_truth_dataset_coverage_stays_above_threshold():
    total_items = 0
    for file_path in DATASET_FILES:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        total_items += len(data)

    assert total_items >= 40, f"Ground-truth dataset coverage too low: {total_items}"
