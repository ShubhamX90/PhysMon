import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_parser_candidates_v2_are_unique_stratified_and_unlabeled():
    rows = load_jsonl(ROOT / "docs/validation/parser_audit_candidates_v2.jsonl")
    status = json.loads(
        (ROOT / "results/stage13/benchmark_integrity/parser_audit_status_v2.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(rows) >= 100
    assert len({row["generated_text"] for row in rows}) == len(rows)
    assert {"qwen", "llama", "deepseek"} <= set(status["model_family_counts"])
    assert all(row["human_parser_judgment"] == "" for row in rows)
    assert status["final_metric_status"] == "BLOCKED_PENDING_HUMAN_LABELS"


def test_pass1_packets_are_blinded_and_contain_all_variants():
    rows = load_jsonl(ROOT / "docs/validation/stage13_validation_packet_pass1_v2.jsonl")
    assert rows
    for row in rows:
        assert len(row["variants"]) == 4
        forbidden = {
            "proposed_cue",
            "governing_equation",
            "canonical_answer",
            "solver_certificate",
            "model_outputs",
            "sensitivity",
            "probe_results",
            "causal_results",
        }
        assert forbidden.isdisjoint(row)


def test_pass2_packets_include_certificate_fields():
    rows = load_jsonl(ROOT / "docs/validation/stage13_validation_packet_pass2_v2.jsonl")
    assert rows
    for row in rows:
        assert "proposed_cue" in row
        assert "governing_equation" in row
        assert "canonical_answer" in row
        assert "certificate_fields" in row


def test_annotation_schema_and_agreement_remain_human_pending():
    schema = json.loads((ROOT / "docs/validation/annotation_schema_v2.json").read_text(encoding="utf-8"))
    assert "validator_id" in schema["required"]
    assert "overall_verdict" in schema["required"]

    agreement = json.loads(
        (ROOT / "results/stage13/benchmark_integrity/validation_agreement_v2.json").read_text(
            encoding="utf-8"
        )
    )
    assert agreement["status"] == "HUMAN_PILOT_PENDING"
    assert agreement["families_marked_valid"] == 0
