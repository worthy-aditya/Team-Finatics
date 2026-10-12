import json
from pathlib import Path

from owasp_mapper import map_keyword


def test_ground_truth_dataset_contains_expected_owasp_labels():
    dataset_path = Path(__file__).resolve().parents[1] / "data" / "ground_truth" / "owasp_ground_truth.json"
    assert dataset_path.exists(), "Ground-truth OWASP dataset is missing"

    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) >= 20

    first_case = data[0]
    assert "keyword" in first_case
    assert "expected" in first_case
    assert "context" in first_case


def test_ground_truth_owasp_accuracy_is_measured_for_common_keywords():
    dataset_path = Path(__file__).resolve().parents[1] / "data" / "ground_truth" / "owasp_ground_truth.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))

    correct = 0
    total = 0

    for item in dataset:
        total += 1
        keyword = item["keyword"]
        expected = item["expected"]
        result = map_keyword(keyword)
        mapped = result.get("owasp") if result else None
        actual = mapped.get("rank") if mapped else None

        if actual == expected:
            correct += 1

    accuracy = correct / total if total else 0.0
    assert accuracy >= 0.6, f"OWASP mapping accuracy too low: {accuracy:.2%}"


def test_ground_truth_owasp_keeps_known_aliases_and_variants():
    dataset_path = Path(__file__).resolve().parents[1] / "data" / "ground_truth" / "owasp_ground_truth.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))

    alias_map = {
        item["keyword"]: item["expected"] for item in dataset if item.get("expected")
    }

    for keyword, expected in alias_map.items():
        result = map_keyword(keyword)
        if result.get("owasp") is None:
            continue
        assert result["owasp"]["rank"] == expected, f"{keyword} should map to {expected}"
