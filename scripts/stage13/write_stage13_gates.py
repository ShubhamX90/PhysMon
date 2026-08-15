#!/usr/bin/env python3
"""Write Wave 0 and Wave 1A gate reports from generated artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from governance_utils import GateCheck, gate_json, read_json, repo_path, write_json


def exists(path: str) -> bool:
    return repo_path(path).exists()


def load_status(path: str) -> str:
    if not exists(path):
        return "MISSING"
    data = read_json(path)
    return str(data.get("status", data.get("overall_status", "UNKNOWN")))


def write_md(path: str, title: str, payload: dict[str, object]) -> None:
    lines = [f"# {title}", "", f"Overall status: **{payload['overall_status']}**", ""]
    lines.append(f"Paper-eligible evidence allowed: **{payload['paper_eligible_evidence_allowed']}**")
    lines.extend(["", "## Checks", ""])
    for check in payload["checks"]:
        mark = "PASS" if check["passed"] else "FAIL"
        lines.append(f"- {mark} `{check['name']}` ({check['severity']}): {check['detail']}")
    Path(repo_path(path)).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave0-json", default="results/stage13/wave0/wave0_gate.json")
    parser.add_argument("--wave1a-json", default="results/stage13/benchmark_integrity/wave1a_gate.json")
    args = parser.parse_args()

    registry_status = load_status("results/stage13/wave0/registry_verification.json")
    canonical_status = load_status("results/stage13/wave0/canonical_evidence_verification.json")
    audit_exists = exists("docs/registry/artifact_authority_audit.json")
    partition_exists = exists("docs/registry/partition_freeze.json")
    claims_exists = exists("docs/registry/claim_evidence_matrix.json")
    cards_status = load_status("results/stage13/wave0/experiment_card_validation.json")
    wave0_checks = [
        GateCheck("registry_verification", registry_status == "PASS", "blocker", registry_status),
        GateCheck("canonical_evidence_verification", canonical_status == "PASS", "blocker", canonical_status),
        GateCheck("artifact_authority_audit_exists", audit_exists, "blocker", str(audit_exists)),
        GateCheck("partition_freeze_exists", partition_exists, "blocker", str(partition_exists)),
        GateCheck("claim_evidence_matrix_exists", claims_exists, "blocker", str(claims_exists)),
        GateCheck("experiment_card_validation", cards_status == "PASS", "blocker", cards_status),
    ]
    wave0 = gate_json("Wave 0", wave0_checks)
    wave0["paper_eligible_evidence_allowed"] = False
    wave0["next_step_allowed"] = "Wave 1A software/human-validation completion only"
    wave0["paper_eligibility_note"] = (
        "Wave 0 passing stabilizes registry/canonical artifacts but does not by itself "
        "make historical scientific claims paper-eligible."
    )
    write_json(args.wave0_json, wave0)
    write_md("docs/stage13/wave0_gate_report.md", "Stage 13 Wave 0 Gate Report", wave0)

    mutation_status = load_status("results/stage13/benchmark_integrity/mutation_test_summary.json")
    parser_status = load_status("results/stage13/benchmark_integrity/parser_audit_status.json")
    leakage_status = load_status("results/stage13/benchmark_integrity/leakage_audit.json")
    balance_status = load_status("results/stage13/benchmark_integrity/balance_audit.json")
    validation_status = load_status("results/stage13/benchmark_integrity/validation_packet_summary.json")
    agreement_status = load_status("results/stage13/benchmark_integrity/validation_agreement.json")
    wave1a_checks = [
        GateCheck("mutation_harness", mutation_status != "MISSING", "warning", mutation_status),
        GateCheck("parser_audit_candidates", parser_status == "PASS", "blocker", parser_status),
        GateCheck("leakage_audit", leakage_status == "PASS", "blocker", leakage_status),
        GateCheck("balance_audit", balance_status != "MISSING", "blocker", balance_status),
        GateCheck("validation_packets", validation_status != "MISSING", "blocker", validation_status),
        GateCheck("human_agreement", agreement_status == "PASS", "blocker", agreement_status),
    ]
    wave1a = gate_json("Wave 1A", wave1a_checks)
    write_json(args.wave1a_json, wave1a)
    write_md("docs/stage13/wave1a_gate_report.md", "Stage 13 Wave 1A Gate Report", wave1a)


if __name__ == "__main__":
    main()
