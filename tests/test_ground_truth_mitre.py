import json
from pathlib import Path

from mitre_mapper import map_keyword


def test_ground_truth_dataset_contains_expected_mitre_labels():
    dataset_path = Path(__file__).resolve().parents[1] / "data" / "ground_truth" / "mitre_ground_truth.json"
    assert dataset_path.exists(), "Ground-truth MITRE dataset is missing"

    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) >= 20

    first_case = data[0]
    assert "keyword" in first_case
    assert "expected" in first_case
    assert "context" in first_case


def test_ground_truth_mitre_accuracy_is_measured_for_common_keywords():
    dataset_path = Path(__file__).resolve().parents[1] / "data" / "ground_truth" / "mitre_ground_truth.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))

    correct = 0
    total = 0

    for item in dataset:
        total += 1
        keyword = item["keyword"]
        expected = item["expected"]
        result = map_keyword(keyword)
        mapped = result.get("mitre")

        if mapped is None:
            actual = None
        else:
            actual = mapped.get("id")

        if actual == expected:
            correct += 1

    accuracy = correct / total if total else 0.0
    assert accuracy >= 0.6, f"MITRE mapping accuracy too low: {accuracy:.2%}"


def test_ground_truth_mitre_keeps_known_aliases_and_variants():
    dataset_path = Path(__file__).resolve().parents[1] / "data" / "ground_truth" / "mitre_ground_truth.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))

    aliases = {
        item["keyword"]: item["expected"] for item in dataset if item.get("expected")
    }

    for keyword, expected in aliases.items():
        result = map_keyword(keyword)
        if result.get("mitre") is None:
            continue
        assert result["mitre"]["id"] == expected, f"{keyword} should map to {expected}"
