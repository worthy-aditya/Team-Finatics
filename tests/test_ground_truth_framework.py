import json
from pathlib import Path

from framework_mapper import map_keyword


def test_ground_truth_framework_dataset_contains_expected_pairs():
    dataset_path = Path(__file__).resolve().parents[1] / "data" / "ground_truth" / "framework_ground_truth.json"
    assert dataset_path.exists(), "Framework ground-truth dataset is missing"

    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) >= 10

    first_case = data[0]
    assert "keyword" in first_case
    assert "expected_owasp" in first_case
    assert "expected_mitre" in first_case


def test_ground_truth_framework_mapping_accuracy_is_measured_for_common_keywords():
    dataset_path = Path(__file__).resolve().parents[1] / "data" / "ground_truth" / "framework_ground_truth.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))

    correct = 0
    total = 0

    for item in dataset:
        total += 1
        keyword = item["keyword"]
        expected_owasp = item["expected_owasp"]
        expected_mitre = item["expected_mitre"]

        result = map_keyword(keyword)
        owasp_rank = result.get("owasp", {}).get("rank") if result.get("owasp") else None
        mitre_id = result.get("mitre", {}).get("id") if result.get("mitre") else None

        if owasp_rank == expected_owasp and mitre_id == expected_mitre:
            correct += 1

    accuracy = correct / total if total else 0.0
    assert accuracy >= 0.6, f"Framework mapping accuracy too low: {accuracy:.2%}"


def test_ground_truth_framework_keeps_aliases_and_variants():
    dataset_path = Path(__file__).resolve().parents[1] / "data" / "ground_truth" / "framework_ground_truth.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))

    for item in dataset:
        result = map_keyword(item["keyword"])
        if result.get("owasp") is not None:
            assert result["owasp"]["rank"] == item["expected_owasp"]
        if result.get("mitre") is not None:
            assert result["mitre"]["id"] == item["expected_mitre"]
