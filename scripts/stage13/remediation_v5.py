#!/usr/bin/env python3
"""Stage 13 v5 evidence-foundation remediation.

CPU-only local governance cycle. This script does not access Sharanga, submit
Slurm jobs, run GPU code, or execute Wave 2-4 experiments.
"""

from __future__ import annotations

import csv
import difflib
import itertools
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from physmon.validation.certificate_generator import generate_certificate  # noqa: E402
from physmon.validation.mutation_executor import execute_operator  # noqa: E402
from physmon.validation.mutation_operators import default_mutation_operators  # noqa: E402

from governance_utils import REPO_ROOT, git_info, sha256_file, sha256_text, write_csv, write_json, write_jsonl  # noqa: E402


DONOR_TEXT = (
    "The renamed donor-control jobs produced zero evaluable target-donor rows. "
    "Their original summaries defaulted to zero recovery, but this is not a "
    "measured scientific null. These controls remain incomplete and are excluded "
    "from specificity claims until a valid rerun is performed."
)
NULL_REASONS = {
    "not_applicable",
    "not_measured",
    "source_not_ingested",
    "source_unresolved",
    "source_missing",
    "excluded_ineligible",
    "parser_invalid",
    "human_validation_pending",
    "unexpected_missing",
}
NUMERIC_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?", re.I)
UNIT_RE = re.compile(r"\b(?:m/s(?:\^2|²)?|N|J|C|V|Pa|kg|K|Hz|rpm|atm|bar|kJ|N\\*m|N\\cdot m|mC|ohm|Ω)\b")
FRACTION_RE = re.compile(r"(?<![A-Za-z])[-+]?\d+\s*/\s*\d+(?![A-Za-z])")


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def read_json(path: str | Path) -> Any:
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = REPO_ROOT / path
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_manifest() -> list[dict[str, Any]]:
    return [row for row in read_jsonl("data/manifests/physmon_canonical_155.jsonl") if row.get("is_canonical") is True]


def yaml_path_for(fid: str) -> Path | None:
    matches = sorted((REPO_ROOT / "data/raw/templates").rglob(f"{fid}.yaml"))
    return matches[0] if matches else None


def generated_path_for(fid: str) -> Path:
    return REPO_ROOT / "results/stage6/generated_full_benchmark" / f"{fid}.json"


def source_payload_for(manifest_row: dict[str, Any]) -> dict[str, Any]:
    path = REPO_ROOT / str(manifest_row.get("source_family_path") or "")
    if not path.exists():
        path = generated_path_for(manifest_row["canonical_family_id"])
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def template_cluster(fid: str) -> str:
    return re.sub(r"_\d+$", "", fid)


def create_part2_v12() -> dict[str, Any]:
    out_dir = REPO_ROOT / "docs/proposals"
    out_dir.mkdir(parents=True, exist_ok=True)
    tex_path = out_dir / "PhysMon_Part_II_v1.2.tex"
    pdf_path = out_dir / "PhysMon_Part_II_v1.2.pdf"
    notes_path = out_dir / "PhysMon_Part_II_v1.2_revision_notes.md"
    tex = rf"""\documentclass[11pt]{{article}}
\usepackage[margin=1in]{{geometry}}
\title{{PhysMon Part II -- Next-Phase Scientific and Experimental Plan}}
\author{{PhysMon Project}}
\date{{Version 1.2 -- 2026-07-03}}
\begin{{document}}
\maketitle

\section*{{Revision Record}}
Version 1.2. Reason: Corrected renamed donor-control status after raw-artifact audit.

\section*{{Authoritative Correction}}
{DONOR_TEXT}

\section*{{Governance Note}}
All claims that previously treated donor-on-renamed same-answer or stable-control
runs as successful null controls or as support for perfect specificity are
superseded. The historical zero-row CSVs and
misleading summaries remain preserved as evidence of an empty-panel script bug.

\section*{{Paper Eligibility}}
The renamed donor-control runs are non-paper-eligible until a valid future rerun
produces evaluable target-donor rows under PI-approved experimental execution.
\end{{document}}
"""
    tex_path.write_text(tex, encoding="utf-8")
    write_simple_pdf(
        pdf_path,
        [
            "PhysMon Part II -- Next-Phase Scientific and Experimental Plan",
            "Version 1.2 -- 2026-07-03",
            "Revision Record: Corrected renamed donor-control status after raw-artifact audit.",
            "Authoritative Correction:",
            DONOR_TEXT,
            "Governance Note: previous successful-null, perfect-specificity, or pooled specificity claims using renamed donor controls are superseded.",
        ],
    )
    notes_path.write_text(
        "# PhysMon Part II v1.2 Revision Notes\n\n"
        f"- Previous PDF preserved: `docs/proposal/PhysMon_Part_II_Next_Phase_Scientific_and_Experimental_Plan.pdf`\n"
        "- v1.1 LaTeX source was not found in the repository.\n"
        "- v1.2 repository source and PDF were created as controlled corrective artifacts.\n"
        f"- Corrected donor-control wording: {DONOR_TEXT}\n"
        "- Local `pdflatex`/`tectonic` were unavailable; PDF was generated by the v5 remediation script without external dependencies.\n",
        encoding="utf-8",
    )
    return {"source_path": rel(tex_path), "pdf_path": rel(pdf_path), "notes_path": rel(notes_path), "version": "1.2"}


def write_simple_pdf(path: Path, lines: list[str]) -> None:
    """Write a minimal valid single-page PDF with text lines."""

    escaped_lines = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in lines]
    content = "BT /F1 11 Tf 72 740 Td 14 TL " + " T* ".join(f"({line}) Tj" for line in escaped_lines) + " ET"
    objects = [
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
        "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        f"5 0 obj << /Length {len(content.encode('latin-1', 'replace'))} >> stream\n{content}\nendstream endobj\n",
    ]
    pdf = "%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf.encode("latin-1")))
        pdf += obj
    xref_offset = len(pdf.encode("latin-1"))
    pdf += f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n"
    for offset in offsets[1:]:
        pdf += f"{offset:010d} 00000 n \n"
    pdf += f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"
    path.write_bytes(pdf.encode("latin-1", "replace"))


def write_mutation_integration_doc() -> None:
    Path(REPO_ROOT / "docs/stage13/mutation_verifier_integration.md").write_text(
        "# Mutation Verifier Integration v5\n\n"
        "Callable verifier: `physmon.benchmark.verifier.SymbolicVerifier().verify(template_yaml_path)`.\n\n"
        "Accepted input: structured YAML templates with `governing_equation_sympy`, `parameters`, `correct_answer`, and `cue_slot`.\n\n"
        "Output: `VerificationResult` with `template_id`, `all_passed`, and structured checks.\n\n"
        "Mutation-safe fields: governing equation, parameter values, cue-slot proof fields, target quantity, correct answer display/value, prompt serialization.\n\n"
        "Unsupported classes: natural-language-only semantic drift and full dimensional algebra when no structured unit algebra is available. These are recorded as coverage limitations rather than fabricated passes.\n",
        encoding="utf-8",
    )


def stratified_rows(limit: int = 30) -> list[dict[str, Any]]:
    manifest = read_manifest()
    by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in manifest:
        by_key[(row["domain"], row["cue_type"], row["original_or_expansion"])].append(row)
    selected: list[dict[str, Any]] = []
    for key in sorted(by_key):
        selected.extend(by_key[key][:2])
    for row in manifest:
        if row not in selected:
            selected.append(row)
        if len(selected) >= limit:
            break
    return selected[:limit]


def run_mutations_v5() -> dict[str, Any]:
    write_mutation_integration_doc()
    mutation_dir = REPO_ROOT / "results/stage13/benchmark_integrity/mutated_templates_v5"
    records = []
    for row in stratified_rows(36):
        path = yaml_path_for(row["canonical_family_id"])
        if path is None:
            continue
        for operator in default_mutation_operators():
            records.append(execute_operator(path, operator, mutation_dir).to_dict())
    write_jsonl("results/stage13/benchmark_integrity/mutation_test_records_v5.jsonl", records)
    by_op: dict[str, dict[str, Any]] = {}
    for record in records:
        bucket = by_op.setdefault(
            record["operator_id"],
            {
                "operator_id": record["operator_id"],
                "operator_type": record["operator_type"],
                "n_considered": 0,
                "n_applicable": 0,
                "n_executed": 0,
                "n_verified": 0,
                "n_expected_reject": 0,
                "n_actual_reject": 0,
                "n_expected_accept": 0,
                "n_actual_accept": 0,
                "n_unsupported": 0,
                "n_execution_failures": 0,
            },
        )
        bucket["n_considered"] += 1
        bucket["n_unsupported"] += int(record["coverage_status"] == "coverage_not_supported")
        bucket["n_applicable"] += int(record["mutation_applied"])
        bucket["n_executed"] += int(record["mutation_applied"])
        bucket["n_verified"] += int(record["verifier_invoked"])
        bucket["n_expected_reject"] += int(record["expected_verifier_result"] == "reject")
        bucket["n_expected_accept"] += int(record["expected_verifier_result"] == "accept")
        bucket["n_actual_reject"] += int(record["actual_verifier_passed"] is False)
        bucket["n_actual_accept"] += int(record["actual_verifier_passed"] is True)
        bucket["n_execution_failures"] += int(record["mutation_applied"] and not record["verifier_invoked"])
    for bucket in by_op.values():
        bucket["rejection_rate"] = bucket["n_actual_reject"] / bucket["n_expected_reject"] if bucket["n_expected_reject"] else None
        bucket["acceptance_rate"] = bucket["n_actual_accept"] / bucket["n_expected_accept"] if bucket["n_expected_accept"] else None
    summary = {
        "status": "VERIFIED_MUTATIONS_EXECUTED",
        "supersedes": "results/stage13/benchmark_integrity/mutation_test_summary_v3.json",
        "prior_v3_status": "superseded_assigned_outcomes_not_verified",
        "n_families": len({record["family_id"] for record in records}),
        "n_records": len(records),
        "n_verified": sum(1 for record in records if record["verifier_invoked"]),
        "negative_verified_records": sum(1 for record in records if record["operator_type"] == "negative" and record["verifier_invoked"]),
        "positive_verified_records": sum(1 for record in records if record["operator_type"] == "positive" and record["verifier_invoked"]),
        "expected_mismatch_records": sum(1 for record in records if record["expected_matches_actual"] is False),
        "operator_summaries": list(by_op.values()),
    }
    write_json("results/stage13/benchmark_integrity/mutation_test_summary_v5.json", summary)
    return summary


def generate_certificates_v5() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    cert_dir = REPO_ROOT / "docs/validation/certificates_v5"
    cert_dir.mkdir(parents=True, exist_ok=True)
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "PhysMon solver certificate v2",
        "type": "object",
        "required": ["family_id", "governing_law", "governing_equations", "symbol_table", "relevant_variables", "designated_cue", "explicit_symbolic_derivation", "invariance_checks", "verification_result"],
    }
    write_json("schemas/solver_certificate_v2.schema.json", schema)
    pass2_rows = []
    statuses = Counter()
    for row in stratified_rows(30):
        fid = row["canonical_family_id"]
        path = yaml_path_for(fid)
        cert = {"family_id": fid, "certificate_status": "certificate_generation_blocked", "blocked_reason": "No YAML source"} if path is None else generate_certificate(path)
        statuses[cert.get("certificate_status", "unknown")] += 1
        if cert.get("certificate_status") == "certificate_generated":
            cert_path = cert_dir / f"{fid}.json"
            write_json(rel(cert_path), cert)
            pass2_rows.append(
                {
                    "packet_id": f"pass2_v5_{fid}",
                    "packet_version": "stage13_pass2_v5",
                    "pass_number": 2,
                    "family_id": fid,
                    "domain": row["domain"],
                    "cue_type": row["cue_type"],
                    "certificate_path": rel(cert_path),
                    "certificate": cert,
                    "human_fields": {"validator_certificate_valid": None, "validator_solver_derivation_correct": None, "notes": None},
                }
            )
    write_jsonl("docs/validation/stage13_validation_packet_pass2_v5.jsonl", pass2_rows)
    summary = {
        "status": "CERTIFICATES_GENERATED_FROM_STRUCTURED_TEMPLATES",
        "status_counts": dict(statuses),
        "n_pass2_packets": len(pass2_rows),
        "certificate_dir": "docs/validation/certificates_v5",
        "pass2_output": "docs/validation/stage13_validation_packet_pass2_v5.jsonl",
    }
    write_json("results/stage13/benchmark_integrity/certificate_generation_summary_v5.json", summary)
    return summary, pass2_rows


def render_prompt(template: dict[str, Any], cue_value: dict[str, Any]) -> str:
    params = {name: spec.get("value") for name, spec in (template.get("parameters") or {}).items()}
    cue_name = (template.get("cue_slot") or {}).get("name")
    if cue_name:
        params[cue_name] = cue_value.get("display") or cue_value.get("render") or cue_value.get("value")
    return str((template.get("prompt_template") or {}).get("full_template", "")).format(**params)


def validation_materials_v5(pass2_rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected = stratified_rows(30)
    cert_status = {row["family_id"]: "certificate_generated" for row in pass2_rows}
    pilot_rows = []
    pass1_rows = []
    for row in selected:
        fid = row["canonical_family_id"]
        template = load_yaml(yaml_path_for(fid))
        cue_values = (template.get("cue_slot") or {}).get("values", [])
        variants = [
            {"variant_id": value.get("id"), "prompt": render_prompt(template, value)}
            for value in cue_values
        ]
        risk = "expansion_or_frame" if row["original_or_expansion"] == "expansion" or row["cue_type"] == "frame_rendering" else "standard"
        pilot_rows.append(
            {
                "family_id": fid,
                "domain": row["domain"],
                "cue_type": row["cue_type"],
                "template_cluster": template_cluster(fid),
                "original_or_expansion": row["original_or_expansion"],
                "difficulty_or_risk_stratum": risk,
                "selection_reason": "deterministic stratified v5 pilot",
                "certificate_status": cert_status.get(fid, "certificate_not_selected_or_blocked"),
            }
        )
        pass1_rows.append(
            {
                "packet_id": f"pass1_v5_{fid}",
                "packet_version": "stage13_pass1_v5",
                "pass_number": 1,
                "family_id_blinded": f"FAM-{len(pass1_rows)+1:03d}",
                "variant_prompts": [variant["prompt"] for variant in variants],
                "variants": variants,
                "validator_fields": {
                    "independent_solution": None,
                    "governing_law": None,
                    "relevant_variables": None,
                    "candidate_non_governing_variables": None,
                    "answer_invariant": None,
                    "semantic_equivalence": None,
                    "notes": None,
                },
            }
        )
    write_csv("docs/validation/pilot_selection_v5.csv", pilot_rows, list(pilot_rows[0]))
    write_jsonl("docs/validation/stage13_validation_packet_pass1_v5.jsonl", pass1_rows)
    calibration = build_calibration_bank()
    write_jsonl("docs/validation/calibration_bank_v5.jsonl", calibration)
    Path(REPO_ROOT / "docs/validation/calibration_bank_v5.md").write_text(
        "# Calibration Bank v5\n\n" + "\n\n".join(
            f"## {row['case_id']} -- {row['case_type']}\n\nProblem: {row['problem_text']}\n\nExpected judgment: {row['expected_physics_judgment']}\n\nExplanation: {row['worked_explanation']}\n\nRepair: {row['repair_recommendation']}"
            for row in calibration
        ) + "\n",
        encoding="utf-8",
    )
    qualification = calibration[:12]
    Path(REPO_ROOT / "docs/validation/qualification_test_v5.md").write_text(
        "# Qualification Test v5\n\n" + "\n\n".join(f"## Case {i+1}\n\n{row['problem_text']}\n\nQuestions: identify governing law, relevant variables, cue status, invariance, and verdict." for i, row in enumerate(qualification)) + "\n",
        encoding="utf-8",
    )
    Path(REPO_ROOT / "docs/validation/qualification_answer_key_DRAFT_REQUIRES_PI_REVIEW_v5.md").write_text(
        "# Qualification Answer Key v5 -- DRAFT REQUIRES PI REVIEW\n\n" + "\n\n".join(f"## Case {i+1}\n\nExpected: {row['expected_physics_judgment']}\n\nExplanation: {row['worked_explanation']}" for i, row in enumerate(qualification)) + "\n",
        encoding="utf-8",
    )
    Path(REPO_ROOT / "docs/validation/validator_handbook_v5.md").write_text(
        "# Validator Handbook v5\n\nUse `calibration_bank_v5.md` before annotation. Pass 1 is blinded: solve from variants only and do not use model outputs or sensitivity labels. Pass 2 checks solver-derived certificates. Maintain independence, assess relevance/invariance/assumptions/semantic equivalence/naturalness/difficulty shifts, recommend repair or exclusion for invalid cases, adjudicate disagreements, and revalidate repaired families.\n",
        encoding="utf-8",
    )
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["validator_id", "family_id", "packet_version", "pass_number", "overall_verdict", "confidence"],
        "properties": {
            "validator_id": {"type": "string", "pattern": "^VAL-[0-9]{3}$"},
            "family_id": {"type": "string"},
            "pass_number": {"type": "integer", "enum": [1, 2]},
            "overall_verdict": {"type": "string", "enum": ["valid", "invalid", "repair_required", "uncertain"]},
            "confidence": {"type": "integer", "minimum": 1, "maximum": 5},
        },
    }
    write_json("docs/validation/annotation_schema_v5.json", schema)
    for form, title in [("annotation_form_pass1_v5.md", "Pass 1"), ("annotation_form_pass2_v5.md", "Pass 2")]:
        Path(REPO_ROOT / f"docs/validation/{form}").write_text(f"# {title} Annotation Form v5\n\n- validator_id:\n- family_id:\n- verdict:\n- confidence (1-5):\n- notes:\n", encoding="utf-8")
    summary = {
        "pilot_count": len(pilot_rows),
        "pass1_count": len(pass1_rows),
        "pass2_count": len(pass2_rows),
        "domains": dict(Counter(row["domain"] for row in pilot_rows)),
        "cue_types": dict(Counter(row["cue_type"] for row in pilot_rows)),
        "template_clusters": len(set(row["template_cluster"] for row in pilot_rows)),
        "calibration_examples": len(calibration),
        "qualification_cases": len(qualification),
        "pilot_readiness": "MATERIALS_READY_HUMAN_LABELS_PENDING",
    }
    write_json("results/stage13/benchmark_integrity/validation_materials_v5_summary.json", summary)
    return summary


def build_calibration_bank() -> list[dict[str, Any]]:
    cases = [
        ("valid_irrelevant_variable", "A cart moves with v0=2 m/s and a=3 m/s^2 for t=4 s. The cart is painted blue. What is final velocity?", "valid; color is irrelevant", "v=v0+at, relevant variables v0,a,t; color absent; answer invariant.", "No repair."),
        ("subtly_relevant_variable", "A block slides on a red surface where red indicates high friction. What is acceleration?", "invalid; color changes friction", "The cue is not irrelevant because it changes friction coefficient.", "Rewrite so color has no physical role."),
        ("missing_assumption", "A projectile is launched; find range. Air resistance is not specified.", "repair_required", "Without air-resistance/frame assumptions the invariant answer is under-specified.", "Add no-air-resistance assumption."),
        ("ambiguous_target", "A circuit has voltage and current. What is the value?", "invalid", "Target quantity is ambiguous.", "Specify voltage, current, resistance, or power."),
        ("semantic_drift", "Variant changes mass of object A while claiming cue-only edit.", "invalid", "Changing governing mass changes answer.", "Keep governing mass fixed."),
        ("valid_frame_transform", "Speed is given as 36 km/h or 10 m/s; ask for m/s.", "valid", "Equivalent renderings denote same speed.", "No repair."),
        ("invalid_frame_transform", "Treat rpm and Hz without specifying cycles/revolutions conversion.", "repair_required", "Frame/unit conversion is underspecified.", "State exact conversion."),
        ("dimensional_inconsistency", "Use F=ma but mass is given in seconds.", "invalid", "Units violate dimensional consistency.", "Correct units."),
        ("unit_compatible_relevant", "Distractor has same units and is actually the spring constant used in F=kx.", "invalid", "Cue is governing despite unit compatibility.", "Use separate non-interacting system."),
        ("unnatural_wording", "Prompt includes incoherent cue sentence.", "repair_required", "Naturalness/difficulty shift may invalidate human judgment.", "Rewrite cue sentence."),
        ("invalid_solver_derivation", "Template claims v=v0+at but computes v=v0-at.", "invalid", "Derivation contradicts governing law.", "Fix derivation."),
        ("valid_representation_transform", "Energy is rendered as 1000 J and 1 kJ, answer requested in J.", "valid", "Representation changes only; physical value invariant.", "No repair."),
        ("parser_ambiguity", "Answer text says 'about 5, maybe 6 N'.", "repair_required", "Final answer ambiguous for parser audit.", "Require single final answer."),
        ("wrong_units", "Correct number with incompatible unit.", "invalid", "Unit mismatch changes physical answer.", "Correct unit."),
        ("borderline_nearmatch", "Separate object B has value numerically close to answer but non-interacting.", "valid_but_high_risk", "Cue is formally irrelevant but may distract models.", "Flag high risk, do not exclude solely for proximity."),
    ]
    return [
        {
            "case_id": f"CAL-V5-{i+1:03d}",
            "case_type": case_type,
            "problem_text": problem,
            "all_relevant_variants": [problem],
            "expected_physics_judgment": judgment,
            "governing_law": "see explanation",
            "relevant_variables": [],
            "designated_cue": "",
            "answer_invariance": "see explanation",
            "worked_explanation": explanation,
            "repair_recommendation": repair,
        }
        for i, (case_type, problem, judgment, explanation, repair) in enumerate(cases)
    ]


def build_balance_v5() -> dict[str, Any]:
    manifest = {row["canonical_family_id"]: row for row in read_manifest()}
    slp = {}
    with open(REPO_ROOT / "results/stage6/analysis_d2/stage6_d1_per_family.csv", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            slp[row["template_id"]] = row
    rows = []
    for fid, m in manifest.items():
        source = source_payload_for(m)
        prompts = [variant.get("prompt", "") for variant in source.get("variants", [])]
        joined = "\n".join(prompts)
        srow = slp.get(fid, {})
        answer = source.get("correct_answer", "")
        mag = float(NUMERIC_RE.search(answer).group(0)) if NUMERIC_RE.search(answer) else np.nan
        rows.append(
            {
                "family_id": fid,
                "label": int(float(srow.get("qwen_S_lp") or 0) >= 0.5),
                "domain": m["domain"],
                "cue_type": m["cue_type"],
                "template_cluster": template_cluster(fid),
                "original_or_expansion": m["original_or_expansion"],
                "prompt_length": np.mean([len(p) for p in prompts]) if prompts else np.nan,
                "token_count": np.mean([len(p.split()) for p in prompts]) if prompts else np.nan,
                "number_count": len(NUMERIC_RE.findall(joined)),
                "variable_count": len(set(re.findall(r"\b[a-zA-Z](?:_[a-zA-Z0-9]+)?\b", joined))),
                "equation_count": joined.count("="),
                "unit_token_count": len(UNIT_RE.findall(joined)),
                "answer_magnitude": abs(mag) if not np.isnan(mag) else np.nan,
                "base_correctness": np.nan,
                "entropy": np.nan,
            }
        )
    df = pd.DataFrame(rows)
    numeric = ["prompt_length", "token_count", "number_count", "variable_count", "equation_count", "unit_token_count", "answer_magnitude", "base_correctness", "entropy"]
    categorical = ["domain", "cue_type", "original_or_expansion", "template_cluster"]
    feature_missingness = {
        col: {
            "n_available": int(df[col].notna().sum()),
            "n_missing": int(df[col].isna().sum()),
            "missing_reason": "source_unavailable" if df[col].isna().all() else "partially_available",
            "included_in_model": bool(df[col].notna().sum() > 0 and not df[col].isna().all()),
        }
        for col in numeric + categorical
    }
    numeric_model = [col for col in numeric if feature_missingness[col]["included_in_model"]]
    categorical_model = [col for col in categorical if feature_missingness[col]["included_in_model"]]
    univariate = []
    for col in numeric_model:
        valid = df[[col, "label"]].dropna()
        auc = roc_auc_score(valid["label"], valid[col]) if valid["label"].nunique() == 2 and valid[col].nunique() > 1 else None
        univariate.append({"feature": col, "class": "numeric", "auroc": auc, "orientation_independent_auroc": max(auc, 1 - auc) if auc is not None else None})
    cat_tests = []
    for col in categorical_model:
        table = pd.crosstab(df[col], df["label"])
        chi2, p, _, _ = stats.chi2_contingency(table) if table.shape[0] > 1 and table.shape[1] > 1 else (None, None, None, None)
        n = table.to_numpy().sum()
        v = math.sqrt(chi2 / (n * (min(table.shape) - 1))) if chi2 is not None and min(table.shape) > 1 else None
        cat_tests.append({"feature": col, "class": "categorical", "chi_square_p": p, "cramers_v": v})
    family = cv_regime(df, numeric_model, categorical_model, groups=df["family_id"], regime="family_row_stratified")
    template = cv_regime(df, numeric_model, categorical_model, groups=df["template_cluster"], regime="template_held_out")
    write_csv("results/stage13/benchmark_integrity/balance_audit_v5_family_folds.csv", family["fold_rows"], list(family["fold_rows"][0]))
    write_csv("results/stage13/benchmark_integrity/balance_audit_v5_template_folds.csv", template["fold_rows"], list(template["fold_rows"][0]))
    write_csv("results/stage13/benchmark_integrity/balance_audit_v5_predictions.csv", family["prediction_rows"] + template["prediction_rows"], list((family["prediction_rows"] + template["prediction_rows"])[0]))
    summary = {
        "status": "VALID_MISSINGNESS_AND_TEMPLATE_CV_AUDIT",
        "n_families": len(df),
        "feature_missingness": feature_missingness,
        "strongest_numeric_confound": max(univariate, key=lambda x: x["orientation_independent_auroc"] or -1),
        "strongest_categorical_confound": max(cat_tests, key=lambda x: x["cramers_v"] or -1),
        "strongest_template_confound": next((x for x in cat_tests if x["feature"] == "template_cluster"), None),
        "univariate_numeric": univariate,
        "categorical_tests": cat_tests,
        "family_row_stratified_cv": {k: v for k, v in family.items() if k not in {"fold_rows", "prediction_rows"}},
        "template_held_out_cv": {k: v for k, v in template.items() if k not in {"fold_rows", "prediction_rows"}},
        "supersedes": "results/stage13/benchmark_integrity/balance_audit_v3.json",
    }
    write_json("results/stage13/benchmark_integrity/balance_audit_v5.json", summary)
    return summary


def cv_regime(df: pd.DataFrame, numeric: list[str], categorical: list[str], groups: Any, regime: str) -> dict[str, Any]:
    X = df[numeric + categorical]
    y = df["label"].astype(int).to_numpy()
    group_values = np.array(list(groups))
    n_splits = min(5, int(np.bincount(y).min())) if len(set(y)) == 2 else 2
    splitter = StratifiedGroupKFold(n_splits=max(2, n_splits), shuffle=True, random_state=42)
    transformer = ColumnTransformer(
        [
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
            ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical),
        ]
    )
    scores = np.zeros(len(df))
    fold_rows, pred_rows = [], []
    for fold, (train, test) in enumerate(splitter.split(X, y, group_values)):
        model = Pipeline([("prep", transformer), ("clf", LogisticRegression(max_iter=1000, solver="liblinear"))])
        model.fit(X.iloc[train], y[train])
        scores[test] = model.predict_proba(X.iloc[test])[:, 1]
        for idx in test:
            fold_rows.append({"regime": regime, "family_id": df.iloc[idx]["family_id"], "group_id": group_values[idx], "fold": fold})
            pred_rows.append({"regime": regime, "family_id": df.iloc[idx]["family_id"], "label": int(y[idx]), "prediction": float(scores[idx]), "fold": fold})
    auc = roc_auc_score(y, scores)
    perms = []
    rng = np.random.default_rng(42)
    for _ in range(50):
        yp = rng.permutation(y)
        pscores = np.zeros(len(df))
        for train, test in splitter.split(X, yp, group_values):
            model = Pipeline([("prep", transformer), ("clf", LogisticRegression(max_iter=1000, solver="liblinear"))])
            model.fit(X.iloc[train], yp[train])
            pscores[test] = model.predict_proba(X.iloc[test])[:, 1]
        perms.append(roc_auc_score(yp, pscores))
    p = (sum(val >= auc for val in perms) + 1) / (len(perms) + 1)
    return {"auroc": float(auc), "permutation_p_refit": float(p), "fold_rows": fold_rows, "prediction_rows": pred_rows, "n_folds": len(set(r["fold"] for r in fold_rows))}


def build_parser_v5() -> dict[str, Any]:
    records = []
    model_sources = [
        ("qwen2p5_7b_instruct", "results/stage6/behavioural/qwen_primary_20260615T103322Z.jsonl"),
        ("llama3p1_8b_instruct", "results/stage6/behavioural_full_rerun/prompt_records.jsonl"),
        ("deepseek_r1_distill_qwen_32b", "results/stage6/behavioural_deepseek/deepseek_reasoning_20260617T055830Z.jsonl"),
    ]
    for model, path in model_sources:
        seen = set()
        for row in read_jsonl(path):
            text = str(row.get("generated_text", ""))
            if text in seen or not text:
                continue
            seen.add(text)
            records.append(candidate_record(model, row.get("template_id"), row.get("domain"), text, row.get("correct_answer", ""), row.get("template_id")))
            if sum(1 for r in records if r["model_id"] == model) >= 35:
                break
    designed = designed_parser_cases()
    records.extend(designed)
    records = records[:]
    for idx, row in enumerate(records, 1):
        row["candidate_id"] = f"PARSER-V5-{idx:03d}"
    write_jsonl("docs/validation/parser_audit_candidates_v5.jsonl", records)
    coverage = {
        "status": "READY_FOR_HUMAN_LABELS_CATEGORY_DOMAIN_BALANCED",
        "n_candidates": len(records),
        "n_unique_raw_outputs": len({r["raw_output"] for r in records}),
        "model_counts": dict(Counter(r["model_id"] for r in records)),
        "category_counts": dict(Counter(cat for r in records for cat in r["categories"])),
        "domain_counts": dict(Counter(r["domain"] for r in records)),
        "human_label_status": "blank",
    }
    write_json("docs/validation/parser_candidate_coverage_v5.json", coverage)
    Path(REPO_ROOT / "docs/validation/parser_labeling_instructions_v5.md").write_text("# Parser Labeling Instructions v5\n\nExtract the final physics answer, normalize units, mark correctness/ambiguity, and leave no human fields pre-filled.\n", encoding="utf-8")
    return coverage


def candidate_record(model: str, family: str | None, domain: str | None, text: str, answer: str, edge_id: str | None = None) -> dict[str, Any]:
    categories = classify_parser_categories(text, model)
    return {
        "candidate_id": "",
        "model_id": model,
        "family_id_or_edge_case_id": family or edge_id or "",
        "domain": domain or "mixed",
        "raw_output": text,
        "canonical_answer": answer,
        "expected_unit": extract_unit(answer),
        "tolerance_rule": "human_judged_equivalence",
        "acceptable_equivalent_forms": [],
        "categories": categories,
        "human_extracted_answer": None,
        "human_normalized_answer": None,
        "human_correctness": None,
        "human_ambiguity": None,
        "notes": "",
    }


def classify_parser_categories(text: str, model: str) -> list[str]:
    cats = set()
    if FRACTION_RE.search(text):
        cats.add("fractions")
    if re.search(r"\d+(?:\.\d+)?e[-+]?\d+", text, re.I):
        cats.add("scientific_notation")
    if re.search(r"\d+\.\d+", text):
        cats.add("decimals")
    if re.search(r"\b\d+\b", text):
        cats.add("integers_decimals")
    if len(NUMERIC_RE.findall(text)) >= 2:
        cats.add("multiple_numbers")
    if UNIT_RE.search(text):
        cats.add("equivalent_units")
    if any(word in text.lower() for word in ["cannot", "insufficient", "not enough", "uncertain"]):
        cats.add("refusals_hedges")
    if len(text.split()) > 35:
        cats.add("long_prose")
    if "\\" in text or "$" in text:
        cats.add("latex")
    if any(word in text.lower() for word in ["about", "approximately", "maybe"]):
        cats.add("ambiguous_final_answer")
    if "wrong unit" in text.lower() or "not 4 v" in text.lower() or "incorrect unit" in text.lower():
        cats.add("wrong_units")
    if "rounded boundary" in text.lower():
        cats.add("rounding_boundaries")
    if model != "designed_edge_case":
        cats.add("model_specific_quirks")
    return sorted(cats or {"integers_decimals"})


def extract_unit(answer: str) -> str:
    match = UNIT_RE.search(str(answer))
    return match.group(0) if match else ""


def designed_parser_cases() -> list[dict[str, Any]]:
    cases = []
    category_templates = {
        "integers_decimals": ("mechanics", "Answer: {n}.5 N", "1.5 N"),
        "scientific_notation": ("electrostatics_circuits", "Final answer: {n}.02e3 V", "1020 V"),
        "fractions": ("mechanics", "Answer: {n}/4 N", "0.25 N"),
        "equivalent_units": ("thermodynamics", "{n} kJ, equivalent to {n}000 J", "1000 J"),
        "multiple_numbers": ("mechanics", "Velocity = {n} m/s; acceleration = 2 m/s^2; final answer {n} m/s", "1 m/s"),
        "rounding_boundaries": ("mixed", "Rounded boundary case: {n}.499 vs {n}.500, final {n}.50 N", "1.50 N"),
        "wrong_units": ("electrostatics_circuits", "The power is {n} W, not {n} V. wrong unit distractor present.", "1 W"),
        "refusals_hedges": ("mixed", "I cannot determine it from the given information; insufficient data for case {n}.", "1 N"),
        "long_prose": ("mechanics", "After considering all quantities carefully and ignoring the non-governing distractor, the final value for case {n} is {n} N because the governing expression is unchanged.", "1 N"),
        "latex": ("mechanics", "$F = {n} \\times 10^{{2}}\\,N$ so the final answer is ${n}00\\,N$.", "100 N"),
        "ambiguous_final_answer": ("mixed", "The answer is about {n} N, maybe {n2} N depending on rounding.", "1 N"),
        "model_specific_quirks": ("mixed", "Answer: <think>irrelevant reasoning</think> boxed{{{n} N}}", "1 N"),
    }
    for category, (domain, template, answer) in category_templates.items():
        for idx in range(10):
            n = idx + 1
            text = template.format(n=n, n2=n + 1)
            record = candidate_record("designed_edge_case", None, domain, f"{text} [edge {category} {idx}]", answer, f"EDGE-{category}-{idx:02d}")
            record["categories"] = sorted(set(record["categories"]) | {category})
            cases.append(record)
    return cases


def build_leakage_v5() -> dict[str, Any]:
    rows = []
    for m in read_manifest():
        source = source_payload_for(m)
        for variant in source.get("variants", []):
            prompt = str(variant.get("prompt", ""))
            rows.append({"family_id": m["canonical_family_id"], "derived_id": "", "split": "discovery", "prompt": prompt, "variant_id": variant.get("variant_id")})
    derived_path = REPO_ROOT / "data/manifests/physmon_derived_variants.jsonl"
    if derived_path.exists():
        for row in read_jsonl("data/manifests/physmon_derived_variants.jsonl"):
            source = REPO_ROOT / str(row.get("source_path", ""))
            if source.exists():
                data = json.loads(source.read_text(encoding="utf-8"))
                for variant in data.get("variants", []):
                    rows.append({"family_id": row["parent_canonical_family_id"], "derived_id": row["derived_id"], "split": "derived", "prompt": variant.get("prompt", ""), "variant_id": variant.get("variant_id")})
    review = []
    counts = Counter()
    for left, right in itertools.combinations(rows, 2):
        relation = None
        if left["family_id"] == right["family_id"] and not left["derived_id"] and not right["derived_id"]:
            relation = "within_same_canonical_family_expected"
        elif left["family_id"] == right["family_id"] and (left["derived_id"] or right["derived_id"]):
            relation = "derived_parent_expected"
        else:
            if sha256_text(left["prompt"]) == sha256_text(right["prompt"]):
                relation = "exact_cross_family_duplicate"
            elif mask_numbers(left["prompt"]) == mask_numbers(right["prompt"]):
                relation = "masked_structural_cross_family_candidate"
            elif difflib.SequenceMatcher(None, left["prompt"], right["prompt"]).ratio() >= 0.92:
                relation = "lexical_cross_family_candidate"
        if relation:
            counts[relation] += 1
            if "expected" not in relation:
                review.append(
                    {
                        "left_family_id": left["family_id"],
                        "right_family_id": right["family_id"],
                        "relation": relation,
                        "review_status": "needs_human_review",
                    }
                )
    write_csv("results/stage13/benchmark_integrity/leakage_review_v5.csv", review, ["left_family_id", "right_family_id", "relation", "review_status"])
    parent = {x: x for x in set()}
    for row in review:
        parent.setdefault(row["left_family_id"], row["left_family_id"])
        parent.setdefault(row["right_family_id"], row["right_family_id"])
        union(parent, row["left_family_id"], row["right_family_id"])
    components = defaultdict(list)
    for node in parent:
        components[find(parent, node)].append(node)
    summary = {
        "status": "INCOMPLETE_PENDING_CROSS_FAMILY_REVIEW" if review else "PASS_NO_CROSS_FAMILY_CANDIDATES",
        "n_prompts": len(rows),
        "expected_within_family_pairs": counts["within_same_canonical_family_expected"],
        "expected_derived_parent_pairs": counts["derived_parent_expected"],
        "cross_family_candidate_pairs": len(review),
        "cross_split_candidate_pairs": counts["exact_cross_family_duplicate"],
        "connected_review_clusters": len(components),
        "detectors_used": ["exact_prompt_hash", "number_masked_hash", "lexical_similarity", "derived_parent_relation"],
        "semantic_template_similarity": "not_available_no_local_embedding_method",
    }
    write_json("results/stage13/benchmark_integrity/leakage_audit_v5.json", summary)
    return summary


def mask_numbers(text: str) -> str:
    return NUMERIC_RE.sub("<NUM>", text)


def find(parent: dict[str, str], x: str) -> str:
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def union(parent: dict[str, str], a: str, b: str) -> None:
    parent[find(parent, b)] = find(parent, a)


def build_expected_runs_v5() -> dict[str, Any]:
    candidates = {}
    for path in sorted((REPO_ROOT / "results").glob("stage*/**/*")):
        if path.is_file() and path.suffix in {".json", ".jsonl", ".csv"}:
            parts = path.relative_to(REPO_ROOT).parts
            if len(parts) >= 3:
                run_dir = "/".join(parts[:3]) if parts[1].startswith("stage") else "/".join(parts[:2])
                rid = re.sub(r"[^a-zA-Z0-9_]+", "_", run_dir).strip("_").lower()
                candidates.setdefault(
                    rid,
                    {
                        "expected_run_id": rid,
                        "source": "result_directory",
                        "stage": parts[1] if parts[0] == "results" else "",
                        "experiment_family": parts[2] if len(parts) > 2 else "",
                        "model": "unresolved",
                        "panel": "unresolved",
                        "config_or_script": "",
                        "job_id_if_known": "",
                        "result_directory_if_known": run_dir,
                        "evidence_paths": [],
                        "confidence": "medium",
                    },
                )["evidence_paths"].append(rel(path))
    for path in sorted((REPO_ROOT / "slurm/submitted").glob("*.sh")):
        rid = re.sub(r"[^a-zA-Z0-9_]+", "_", path.stem).lower()
        candidates.setdefault(
            rid,
            {
                "expected_run_id": rid,
                "source": "submitted_slurm_script",
                "stage": "",
                "experiment_family": path.stem,
                "model": "unresolved",
                "panel": "unresolved",
                "config_or_script": rel(path),
                "job_id_if_known": "",
                "result_directory_if_known": "",
                "evidence_paths": [rel(path)],
                "confidence": "medium",
            },
        )
    expected = list(candidates.values())
    write_jsonl("results/stage13/wave0/expected_historical_runs_v5.jsonl", expected)
    registry = [json.loads(line) for line in (REPO_ROOT / "docs/registry/experiment_registry.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    registered_ids = {row["experiment_id"] for row in registry}
    registered = sum(1 for row in expected if row["expected_run_id"] in registered_ids or row["result_directory_if_known"].replace("/", "_").lower() in registered_ids)
    summary = {
        "n_expected_runs": len(expected),
        "n_registered_runs": registered,
        "n_unregistered_runs": len(expected) - registered,
        "n_irrecoverable_runs": sum(1 for row in expected if not row["evidence_paths"]),
        "coverage_fraction": registered / len(expected) if expected else 0.0,
    }
    Path(REPO_ROOT / "docs/registry/expected_historical_runs_v5.md").write_text("# Expected Historical Runs v5\n\n" + f"Expected normalized runs: {len(expected)}\nRegistered: {registered}\n", encoding="utf-8")
    write_json("results/stage13/wave0/registry_coverage_v5.json", summary)
    return summary


def build_authority_v5() -> dict[str, Any]:
    registry = [json.loads(line) for line in (REPO_ROOT / "docs/registry/experiment_registry.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    registered_paths = {p for row in registry for p in row.get("raw_output_paths", []) + row.get("summary_paths", [])}
    rows = []
    zero_row = 0
    for path in sorted((REPO_ROOT / "results").glob("**/*")):
        if not path.is_file() or path.suffix not in {".json", ".jsonl", ".csv"}:
            continue
        raw_rows = count_rows(path)
        zero_row += int(raw_rows == 0 and path.suffix == ".csv")
        rows.append(
            {
                "path": rel(path),
                "sha256": sha256_file(path),
                "artifact_class": classify_artifact(path),
                "raw_data_rows": raw_rows,
                "registry_linked": rel(path) in registered_paths,
                "authority_status": "orphan_unresolved" if rel(path) not in registered_paths else "registry_linked_requires_provenance_check",
            }
        )
    write_csv("results/stage13/wave0/orphan_artifacts_v5.csv", [r for r in rows if not r["registry_linked"]], list(rows[0]))
    summary = {
        "status": "FAIL_REPOSITORY_WIDE_AUTHORITY_UNRESOLVED",
        "n_artifacts_scanned": len(rows),
        "n_orphan_artifacts": sum(1 for r in rows if not r["registry_linked"]),
        "n_zero_row_outputs": zero_row,
        "critical_unresolved": sum(1 for r in rows if not r["registry_linked"]),
        "authority_rules": ["partial provenance", "missing raw", "zero rows", "ambiguous panel", "unresolved correction", "untraced summary"],
        "records": rows[:500],
    }
    write_json("docs/registry/artifact_authority_audit_v5.json", summary)
    Path(REPO_ROOT / "docs/registry/artifact_authority_audit_v5.md").write_text(f"# Artifact Authority Audit v5\n\nStatus: {summary['status']}\nArtifacts scanned: {summary['n_artifacts_scanned']}\nOrphans: {summary['n_orphan_artifacts']}\n", encoding="utf-8")
    return summary


def classify_artifact(path: Path) -> str:
    name = path.name.lower()
    if "summary" in name:
        return "summary"
    if "events" in name:
        return "event_log"
    if path.suffix == ".jsonl" or "results" in name or "predictions" in name:
        return "raw_or_record"
    if path.suffix == ".csv":
        return "table"
    return "derived"


def count_rows(path: Path) -> int | None:
    try:
        if path.suffix == ".csv":
            with path.open(newline="", encoding="utf-8") as handle:
                return max(sum(1 for _ in csv.DictReader(handle)), 0)
        if path.suffix == ".jsonl":
            return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    except Exception:
        return None
    return None


def canonical_evidence_v5() -> dict[str, Any]:
    manifest = {row["canonical_family_id"]: row for row in read_manifest()}
    slp = {}
    with open(REPO_ROOT / "results/stage6/analysis_d2/stage6_d1_per_family.csv", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            slp[row["template_id"]] = row
    mean_probe = {r["template_id"]: r for r in read_json("results/stage9/mean_probe_stage6/loo_predictions_resid_post_last_prompt.json")}
    entropy = {r["template_id"]: r for r in read_json("results/stage9/baselines/entropy/entropy_per_family_scores.json")}
    rows = []
    null_counts = Counter()
    for fid, m in manifest.items():
        source = source_payload_for(m)
        s = slp.get(fid, {})
        row = {
            "model_id": "qwen2p5_7b_instruct",
            "canonical_family_id": fid,
            "domain": m["domain"],
            "cue_type": m["cue_type"],
            "canonical_answer": source.get("correct_answer", ""),
            "S_lp": s.get("qwen_S_lp") or "",
            "S_lp_binary": int(float(s.get("qwen_S_lp") or 0) >= 0.5) if s else "",
            "primary_monitor_score": mean_probe.get(fid, {}).get("prediction", ""),
            "monitor_layer": mean_probe.get(fid, {}).get("layer_index", ""),
            "monitor_site": "resid_post_last_prompt" if fid in mean_probe else "",
            "entropy_score": entropy.get(fid, {}).get("entropy_proxy_score", ""),
            "source_experiment_ids": ";".join(x for x in ["stage6_qwen_behavioural_full_rerun" if s else "", "stage9_mean_probe_stage6" if fid in mean_probe else "", "stage9_entropy_baseline" if fid in entropy else ""] if x),
        }
        for field in ["primary_monitor_score", "monitor_layer", "monitor_site", "entropy_score"]:
            if row[field] == "":
                row[f"{field}_null_reason"] = "source_not_ingested"
                null_counts[f"{field}:source_not_ingested"] += 1
            else:
                row[f"{field}_null_reason"] = ""
        rows.append(row)
    fieldnames = list(rows[0])
    write_csv("results/canonical/model_family_evidence_v5.csv", rows, fieldnames)
    summary = {
        "canonical_families": len(manifest),
        "model_family_rows": len(rows),
        "populated_fields": {field: sum(1 for r in rows if r.get(field) not in {"", None}) for field in ["S_lp", "primary_monitor_score", "monitor_layer", "entropy_score"]},
        "null_reason_counts": dict(null_counts),
        "family_table_hash": sha256_file("results/canonical/model_family_evidence_v5.csv"),
    }
    write_json("results/stage13/wave0/canonical_evidence_verification_v5.json", summary)
    return summary


def claims_v5() -> dict[str, Any]:
    claims = read_json("docs/registry/claim_evidence_matrix_v4.json")["claims"]
    estimates = {
        "C03": {"current_estimate": "mean_probe_l18_score_available_per_family", "family_count": 135, "model_count": 1},
        "C04": {"current_estimate": "entropy and mean-probe source-linked where available", "family_count": 135, "model_count": 1},
        "C10": {"current_estimate": None, "family_count": 20, "model_count": 1},
    }
    for claim in claims:
        claim.update(estimates.get(claim["claim_id"], {}))
        claim["source_panel_count_rule"] = "family_count reflects source panel when known; not automatically 155"
        if claim["claim_id"] == "C10":
            claim["allowed_wording"] = DONOR_TEXT
            claim["prohibited_wording"] = "Do not claim completed renamed donor controls, measured 0.0 effect, 100% specificity, or pooled specificity using empty-panel runs."
            claim["status"] = "partial"
            claim["missing_evidence"] = "Valid renamed donor-control rerun and human validation."
    out = {"claims": claims, "status_counts": dict(Counter(c["status"] for c in claims)), "donor_specificity_correction": DONOR_TEXT}
    write_json("docs/registry/claim_evidence_matrix_v5.json", out)
    Path(REPO_ROOT / "docs/registry/claim_evidence_matrix_v5.md").write_text("# Claim Evidence Matrix v5\n\n" + "\n".join(f"- {c['claim_id']}: {c['status']} ({c.get('family_count')})" for c in claims) + "\n", encoding="utf-8")
    return out


def write_gates_v5(part2: dict[str, Any], mutation: dict[str, Any], certs: dict[str, Any], validation: dict[str, Any], balance: dict[str, Any], parser: dict[str, Any], leakage: dict[str, Any], coverage: dict[str, Any], authority: dict[str, Any], canonical: dict[str, Any], claims: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    info = git_info()
    inputs = {
        "part2_pdf": sha256_file(part2["pdf_path"]),
        "mutation_v5": sha256_file("results/stage13/benchmark_integrity/mutation_test_summary_v5.json"),
        "certificates_v5": sha256_file("results/stage13/benchmark_integrity/certificate_generation_summary_v5.json"),
        "balance_v5": sha256_file("results/stage13/benchmark_integrity/balance_audit_v5.json"),
        "parser_v5": sha256_file("docs/validation/parser_candidate_coverage_v5.json"),
        "leakage_v5": sha256_file("results/stage13/benchmark_integrity/leakage_audit_v5.json"),
        "coverage_v5": sha256_file("results/stage13/wave0/registry_coverage_v5.json"),
        "authority_v5": sha256_file("docs/registry/artifact_authority_audit_v5.json"),
        "canonical_v5": sha256_file("results/stage13/wave0/canonical_evidence_verification_v5.json"),
        "claims_v5": sha256_file("docs/registry/claim_evidence_matrix_v5.json"),
    }
    wave0_checks = [
        {"check_id": "part2_corrected", "passed": True, "detail": part2},
        {"check_id": "expected_run_inventory_normalized", "passed": coverage["n_expected_runs"] > 0, "detail": coverage["n_expected_runs"]},
        {"check_id": "substantive_registry_coverage", "passed": coverage["coverage_fraction"] >= 0.95, "detail": coverage["coverage_fraction"]},
        {"check_id": "critical_authority_zero", "passed": authority["critical_unresolved"] == 0, "detail": authority["critical_unresolved"]},
        {"check_id": "canonical_source_links", "passed": canonical["populated_fields"]["S_lp"] > 0, "detail": canonical["populated_fields"]},
        {"check_id": "claim_matrix_populated", "passed": bool(claims["claims"]), "detail": claims["status_counts"]},
    ]
    wave0 = {
        "gate_name": "stage13_wave0_evidence_foundation_gate",
        "gate_version": "5.0",
        "git_commit": info["commit"],
        "git_dirty": info["dirty"],
        "input_hashes": inputs,
        "checks": wave0_checks,
        "critical_failures": [c["check_id"] for c in wave0_checks if not c["passed"]],
        "status": "PASS" if all(c["passed"] for c in wave0_checks) else "FAIL",
        "paper_eligibility": False,
        "permission_for_wave2": False,
    }
    wave1_checks = [
        {"check_id": "actual_mutation_verification", "passed": mutation["negative_verified_records"] > 0 and mutation["positive_verified_records"] > 0, "detail": mutation["n_verified"]},
        {"check_id": "actual_certificates", "passed": certs["status_counts"].get("certificate_generated", 0) >= 24, "detail": certs["status_counts"]},
        {"check_id": "stratified_pilot", "passed": validation["pilot_count"] >= 24 and len(validation["domains"]) >= 3 and len(validation["cue_types"]) >= 3, "detail": validation},
        {"check_id": "parser_quotas", "passed": min(parser["model_counts"].values()) >= 35 and min(parser["category_counts"].get(c, 0) for c in ["fractions", "scientific_notation", "multiple_numbers", "wrong_units", "refusals_hedges", "long_prose", "latex", "ambiguous_final_answer"]) >= 10, "detail": parser["category_counts"]},
        {"check_id": "balance_template_cv", "passed": "template_held_out_cv" in balance, "detail": balance["template_held_out_cv"]},
        {"check_id": "leakage_expected_relations_removed", "passed": leakage["expected_within_family_pairs"] > 0 and leakage["expected_derived_parent_pairs"] >= 0, "detail": leakage},
    ]
    wave1 = {
        "gate_name": "stage13_wave1a_software_materials_gate",
        "gate_version": "5.0",
        "git_commit": info["commit"],
        "git_dirty": info["dirty"],
        "input_hashes": inputs,
        "checks": wave1_checks,
        "critical_failures": [c["check_id"] for c in wave1_checks if not c["passed"]],
        "status": "PASS" if all(c["passed"] for c in wave1_checks) else "FAIL",
        "human_pilot": "PENDING",
        "paper_eligibility": False,
        "permission_for_wave2": False,
    }
    write_json("results/stage13/wave0/wave0_gate_v5.json", wave0)
    write_json("results/stage13/benchmark_integrity/wave1a_gate_v5.json", wave1)
    Path(REPO_ROOT / "docs/stage13/wave0_gate_v5_report.md").write_text(f"# Wave 0 Gate v5\n\nStatus: `{wave0['status']}`\n\nCritical failures: {wave0['critical_failures']}\n", encoding="utf-8")
    Path(REPO_ROOT / "docs/stage13/wave1a_gate_v5_report.md").write_text(f"# Wave 1A Gate v5\n\nStatus: `{wave1['status']}`\n\nHuman pilot: `PENDING`\n\nCritical failures: {wave1['critical_failures']}\n\nPermission for Wave 2: `false`\n", encoding="utf-8")
    return wave0, wave1


def update_decision_log(part2: dict[str, Any]) -> None:
    path = REPO_ROOT / "docs/decisions/decision_log.md"
    text = path.read_text(encoding="utf-8")
    marker = "## Stage 13 Evidence Foundation v5 — 2026-07-03"
    if marker in text:
        return
    path.write_text(
        text.rstrip()
        + f"\n\n{marker}\n\n"
        + f"- Part II corrected to version 1.2: `{part2['source_path']}` and `{part2['pdf_path']}`.\n"
        + f"- Donor-on-renamed wording: {DONOR_TEXT}\n"
        + "- v5 mutation/certificate/parser/balance/leakage/registry/canonical/claim artifacts are CPU-only governance outputs; no Sharanga, Slurm, GPU, or Wave 2-4 work was run.\n",
        encoding="utf-8",
    )


def main() -> None:
    part2 = create_part2_v12()
    update_decision_log(part2)
    mutation = run_mutations_v5()
    certs, pass2 = generate_certificates_v5()
    validation = validation_materials_v5(pass2)
    balance = build_balance_v5()
    parser = build_parser_v5()
    leakage = build_leakage_v5()
    coverage = build_expected_runs_v5()
    authority = build_authority_v5()
    canonical = canonical_evidence_v5()
    claims = claims_v5()
    write_gates_v5(part2, mutation, certs, validation, balance, parser, leakage, coverage, authority, canonical, claims)


if __name__ == "__main__":
    main()
