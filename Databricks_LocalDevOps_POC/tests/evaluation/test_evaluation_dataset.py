import json
from pathlib import Path


def test_evaluation_dataset_covers_answers_refusals_and_followups() -> None:
    path = Path(__file__).with_name("questions.jsonl")
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    assert len(cases) >= 5
    assert {"answer", "answer_or_clarify", "refuse_or_clarify", "refuse"}.issubset(
        {case["expected_behavior"] for case in cases}
    )
    for case in cases:
        assert case["id"] and case["question"] and case["answer_criteria"]
        assert "expected_sources" in case and "sql_characteristics" in case
