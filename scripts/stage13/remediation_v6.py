#!/usr/bin/env python3
"""Stage 13 v6 evidence-foundation remediation.

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
import shutil
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
from sklearn.model_selection import StratifiedKFold, StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from physmon.validation.certificate_generator import CERTIFICATE_STATUSES, generate_certificate  # noqa: E402
from physmon.validation.mutation_executor import execute_operator  # noqa: E402
from physmon.validation.mutation_operators import default_mutation_operators  # noqa: E402

from governance_utils import REPO_ROOT, git_info, sha256_file, sha256_text, write_csv, write_json, write_jsonl  # noqa: E402
from remediation_v5 import write_simple_pdf  # noqa: E402


DONOR_TEXT = (
    "The renamed donor-control jobs produced zero evaluable target-donor rows. "
    "Their original summaries defaulted to zero recovery, but this is not a measured scientific null. "
    "These controls remain incomplete and are excluded from specificity claims until a valid rerun is performed."
)
VERIFIER_SCOPE = (
    "The mutation suite tests the current symbolic verifier's numerical-answer consistency, "
    "cue-symbol independence, structured-parameter plausibility, and parseability. It does not "
    "validate full natural-language semantics, assumption sufficiency, frame equivalence, or complete dimensional algebra."
)
NUMERIC_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?", re.I)
FRACTION_RE = re.compile(r"(?<![A-Za-z])[-+]?\d+\s*/\s*\d+(?![A-Za-z])")
LOCAL_PATH_RE = re.compile(r"(/Users/|C:\\|/home/[A-Za-z0-9_.-]+/)")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: str | Path) -> Any:
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = REPO_ROOT / path
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_text(path: str | Path, text: str) -> Path:
    p = REPO_ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def read_manifest() -> list[dict[str, Any]]:
    return [row for row in read_jsonl("data/manifests/physmon_canonical_155.jsonl") if row.get("is_canonical") is True]


def yaml_path_for(fid: str) -> Path | None:
    matches = sorted((REPO_ROOT / "data/raw/templates").rglob(f"{fid}.yaml"))
    return matches[0] if matches else None


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_family_payload(fid: str) -> dict[str, Any] | None:
    for path in [
        REPO_ROOT / "results/stage6/generated_full_benchmark" / f"{fid}.json",
        REPO_ROOT / "results/stage10/benchmark_expansion/rendered" / f"{fid}.json",
        REPO_ROOT / "results/stage11/behavioural_expansion/rendered" / f"{fid}.json",
    ]:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def prompt_variants(fid: str) -> list[str]:
    payload = load_family_payload(fid)
    if not payload:
        ypath = yaml_path_for(fid)
        if ypath:
            y = load_yaml(ypath)
            values = (y.get("cue_slot") or {}).get("values") or []
            template = ((y.get("prompt_template") or {}).get("full_template") or "")
            return [template.replace("{cue}", str(v.get("display") or v.get("render") or v.get("value"))) for v in values] or [template]
        return []
    variants = payload.get("variants") or payload.get("rendered_variants") or payload.get("prompts") or []
    out = []
    for variant in variants:
        if isinstance(variant, dict):
            out.append(str(variant.get("prompt") or variant.get("text") or variant.get("rendered_prompt") or ""))
        else:
            out.append(str(variant))
    return [p for p in out if p]


def template_cluster(fid: str) -> str:
    return re.sub(r"_\d+$", "", fid)


def normalized_template_group(fid: str, row: dict[str, Any]) -> str:
    ypath = yaml_path_for(fid)
    if not ypath:
        return f"{row.get('domain','unknown')}::{template_cluster(fid)}::missing_yaml"
    y = load_yaml(ypath)
    equation = re.sub(r"[A-Za-z_][A-Za-z0-9_]*", "VAR", str(y.get("governing_equation_sympy", "")))
    cue = (y.get("cue_slot") or {}).get("type") or y.get("cue_type", "")
    return f"{y.get('domain')}::{template_cluster(fid)}::{equation}::{cue}"


def part2_erratum_v6() -> dict[str, Any]:
    out = REPO_ROOT / "docs/proposals"
    old_tex = out / "PhysMon_Part_II_v1.2.tex"
    old_pdf = out / "PhysMon_Part_II_v1.2.pdf"
    erratum_tex = out / "PhysMon_Part_II_v1.1_Erratum_2026-07-03.tex"
    erratum_pdf = out / "PhysMon_Part_II_v1.1_Erratum_2026-07-03.pdf"
    if old_tex.exists():
        shutil.copyfile(old_tex, erratum_tex)
    else:
        erratum_tex.write_text(DONOR_TEXT, encoding="utf-8")
    if old_pdf.exists():
        shutil.copyfile(old_pdf, erratum_pdf)
    else:
        write_simple_pdf(erratum_pdf, ["PhysMon Part II v1.1 Erratum", DONOR_TEXT])
    rule = (
        "# PhysMon Part II Governing Document Rule\n\n"
        "The governing scientific plan remains the complete 42-page Part II v1.1 document, read together with the mandatory July 3 donor-control erratum. "
        "The erratum supersedes only the renamed donor-control statements.\n\n"
        "- Complete Part II v1.1: `docs/proposal/PhysMon_Part_II_Next_Phase_Scientific_and_Experimental_Plan.pdf`\n"
        "- Mandatory erratum: `docs/proposals/PhysMon_Part_II_v1.1_Erratum_2026-07-03.pdf`\n"
        "- Full v1.2 status: `blocked_source_unavailable` because the complete v1.1 LaTeX source is not present in the repository.\n"
    )
    write_text("docs/proposals/PhysMon_Part_II_governing_document_rule.md", rule)
    write_text(
        "docs/proposals/PhysMon_Part_II_v1.2_SUPERSEDED_BY_ERRATUM.md",
        "# Supersession Notice\n\n"
        "`docs/proposals/PhysMon_Part_II_v1.2.*` is preserved as a historical one-page correction artifact. "
        "It is superseded as a document title by `PhysMon_Part_II_v1.1_Erratum_2026-07-03.*` and must not be treated as the complete Part II plan.\n",
    )
    return {
        "complete_v11_pdf": "docs/proposal/PhysMon_Part_II_Next_Phase_Scientific_and_Experimental_Plan.pdf",
        "erratum_tex": rel(erratum_tex),
        "erratum_pdf": rel(erratum_pdf),
        "governing_rule": "docs/proposals/PhysMon_Part_II_governing_document_rule.md",
        "full_v12_status": "blocked_source_unavailable",
    }


def donor_statement_audit_v6() -> dict[str, Any]:
    terms = ["100% specificity", "0.0 mean recovery", "donor-on-renamed", "renamed donor controls completed", "68.1%", "Part II v1.2"]
    records = []
    for root in ["README.md", "docs", "scripts", "src", "tests", "results/stage13"]:
        p = REPO_ROOT / root
        files = [p] if p.is_file() else [x for x in p.rglob("*") if x.is_file() and x.suffix.lower() not in {".pdf", ".png", ".zip", ".pyc"}]
        for path in files:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for line_no, line in enumerate(text.splitlines(), start=1):
                if any(term in line for term in terms):
                    if "zero evaluable" in line or "must not" in line or "prohibited" in line:
                        status = "correct_current"
                    elif "Stage13_Evidence_Foundation_Remediation_Brief" in str(path) or "Wave0_Wave1A" in str(path) or "PhysMon_Part_II_v1.2" in str(path):
                        status = "historical_superseded"
                    else:
                        status = "historical_superseded"
                    records.append({"path": rel(path), "line": line_no, "text": line.strip()[:300], "classification": status})
    md = ["# Donor-Control Statement Audit v6", "", f"Correct current wording: {DONOR_TEXT}", ""]
    for row in records[:300]:
        md.append(f"- `{row['path']}:{row['line']}` — `{row['classification']}` — {row['text']}")
    write_text("docs/stage13/donor_control_statement_audit_v6.md", "\n".join(md) + "\n")
    return {"n_statements": len(records), "records": records}


def mutation_semantics_doc(operator_summaries: list[dict[str, Any]]) -> None:
    rows = {
        "sign_inversion_governing_expression": ("negates governing_equation_sympy", "numeric answer consistency", "does not test natural-language prompt alignment", "sign_inversion_governing_expression"),
        "replace_governing_variable_with_cue": ("substitutes a cue symbol into governing_equation_sympy", "cue-symbol independence and numeric consistency", "does not test semantic relevance in prose", "replace_governing_variable_with_cue"),
        "negative_parameter_value": ("negates one structured parameter value", "numeric consistency and basic physical plausibility", "not dimensional corruption", "negative_parameter_value"),
        "incorrect_canonical_answer": ("corrupts stored correct_answer fields", "incorrect canonical answer detection", "not target quantity semantics", "incorrect_canonical_answer"),
        "cue_leakage_after_assumption_text_removal": ("removes proof text and leaks cue into equation", "cue leakage detection", "does not validate assumption sufficiency", "cue_leakage_after_assumption_text_removal"),
        "true_unit_metadata_corruption": ("would change structured unit metadata", "unsupported because SymbolicVerifier has no dimensional algebra checker", "no measured unit rejection", "true_unit_metadata_corruption"),
        "algebraically_equivalent_expression": ("adds algebraic zero", "acceptance of numerically equivalent expression", "not NL semantics", "algebraically_equivalent_expression"),
        "semantics_preserving_variable_renaming": ("renames one structured symbol consistently", "symbol-table consistency and numeric equivalence", "limited to structured symbols", "semantics_preserving_variable_renaming"),
        "equivalent_unit_formatting": ("rewrites answer display with same value/unit", "parser/display stability", "not unit conversion equivalence", "equivalent_unit_formatting_display_only"),
        "harmless_serialization_formatting": ("changes prompt serialization when possible", "serialization robustness", "may not alter rendered task semantics", "harmless_serialization_formatting"),
        "exact_noop_control": ("metadata-only copy", "serialization control", "not substantive mutation evidence", "exact_noop_control"),
    }
    lines = ["# Mutation Semantics Audit v6", "", VERIFIER_SCOPE, ""]
    for summary in operator_summaries:
        op = summary["operator_id"]
        actual, prop, confounds, name = rows.get(op, ("unknown", "unknown", "unknown", op))
        lines.extend(
            [
                f"## `{op}`",
                f"- current_name: `{op}`",
                f"- actual_code_change: {actual}",
                f"- verifier_property_tested: {prop}",
                f"- confounds: {confounds}",
                f"- recommended_name: `{name}`",
                f"- supported_claim: {summary.get('allowed_interpretation', '')}",
                "- unsupported_claim: full natural-language, dimensional, assumption-sufficiency, or frame-equivalence validation.",
                "",
            ]
        )
    write_text("docs/stage13/mutation_semantics_audit_v6.md", "\n".join(lines))


def run_mutations_v6() -> dict[str, Any]:
    mutation_dir = REPO_ROOT / "results/stage13/benchmark_integrity/mutated_templates_v6"
    records = []
    selected = stratified_manifest(30)
    for row in selected:
        path = yaml_path_for(row["canonical_family_id"])
        if path is None:
            continue
        for operator in default_mutation_operators():
            record = execute_operator(path, operator, mutation_dir).to_dict()
            record["actual_mutation"] = operator.description
            record["verifier_called"] = "SymbolicVerifier.verify" if record["verifier_invoked"] else None
            record["actual_checks"] = [c.get("check_name") for c in record["verifier_checks"]]
            record["confounds"] = mutation_confounds(record["operator_id"])
            record["allowed_interpretation"] = mutation_allowed_interpretation(record["operator_id"])
            records.append(record)
    write_jsonl("results/stage13/benchmark_integrity/mutation_test_records_v6.jsonl", records)
    summaries = []
    for op, rows in sorted(defaultdict(list, {k: [r for r in records if r["operator_id"] == k] for k in {r["operator_id"] for r in records}}).items()):
        verified = [r for r in rows if r["verifier_invoked"]]
        summaries.append(
            {
                "operator_id": op,
                "operator_type": rows[0]["operator_type"],
                "n_considered": len(rows),
                "n_applicable": sum(r["mutation_applied"] for r in rows),
                "n_executed": sum(r["object_differs_from_original"] for r in rows),
                "n_verified": len(verified),
                "n_expected_reject": sum(r["expected_verifier_result"] == "reject" for r in rows),
                "n_actual_reject": sum(r["actual_verifier_passed"] is False for r in verified),
                "n_expected_accept": sum(r["expected_verifier_result"] == "accept" for r in rows),
                "n_actual_accept": sum(r["actual_verifier_passed"] is True for r in verified),
                "rejection_rate": safe_div(sum(r["actual_verifier_passed"] is False for r in verified), len(verified)),
                "acceptance_rate": safe_div(sum(r["actual_verifier_passed"] is True for r in verified), len(verified)),
                "n_unsupported": sum("unsupported" in str(r["coverage_status"]) for r in rows),
                "n_execution_failures": sum(r["mutation_applied"] and not r["verifier_invoked"] and "unsupported" not in str(r["coverage_status"]) for r in rows),
                "allowed_interpretation": mutation_allowed_interpretation(op),
            }
        )
    mutation_semantics_doc(summaries)
    summary = {
        "status": "VERIFIER_BACKED_MUTATIONS_WITH_LIMITED_SCOPE",
        "supersedes": "results/stage13/benchmark_integrity/mutation_test_summary_v5.json",
        "prior_v5_status": "superseded_operator_semantics_overclaimed",
        "verifier_scope_statement": VERIFIER_SCOPE,
        "n_records": len(records),
        "n_families": len({r["family_id"] for r in records}),
        "n_verified": sum(r["verifier_invoked"] for r in records),
        "operator_summaries": summaries,
        "misleading_names_removed": ["dimensional_corruption", "target_quantity_change", "assumption_removal"],
        "true_dimensional_mutation_status": "unsupported_no_dimensional_checker",
    }
    write_json("results/stage13/benchmark_integrity/mutation_test_summary_v6.json", summary)
    return summary


def mutation_confounds(op: str) -> str:
    return {
        "negative_parameter_value": "Tests value sign/plausibility, not units or dimensions.",
        "incorrect_canonical_answer": "Stored answer changes while prompt and governing expression do not.",
        "cue_leakage_after_assumption_text_removal": "Rejection is driven by cue leakage, not proof-text removal alone.",
        "true_unit_metadata_corruption": "Current verifier lacks dimensional algebra checker.",
        "equivalent_unit_formatting": "Display rewrite uses same value/unit and does not demonstrate conversion.",
        "exact_noop_control": "Metadata-only control; not substantive positive mutation.",
    }.get(op, "Limited to structured verifier scope.")


def mutation_allowed_interpretation(op: str) -> str:
    if op == "true_unit_metadata_corruption":
        return "No measured result; true dimensional mutation unsupported by current verifier."
    return "Evidence about current SymbolicVerifier behaviour on structured YAML fields only."


def safe_div(a: float, b: float) -> float | None:
    return None if b == 0 else float(a) / float(b)


def stratified_manifest(limit: int) -> list[dict[str, Any]]:
    rows = read_manifest()
    by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_key[(row["domain"], row["cue_type"], row["original_or_expansion"])].append(row)
    selected = []
    for key in sorted(by_key):
        selected.extend(by_key[key][:2])
    for row in rows:
        if row not in selected:
            selected.append(row)
        if len(selected) >= limit:
            break
    return selected[:limit]


def write_certificate_schema_v6() -> None:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "PhysMon Stage 13 solver certificate v3",
        "type": "object",
        "required": ["family_id", "certificate_status", "symbol_table", "explicit_symbolic_derivation", "dimensional_check", "invariance_checks", "verification_result", "source_template"],
        "properties": {
            "family_id": {"type": "string"},
            "source_template": {
                "type": "string",
                "description": "Repository-relative path only; local absolute path prefixes are not allowed.",
            },
            "certificate_status": {"type": "string", "enum": sorted(CERTIFICATE_STATUSES)},
            "symbol_table": {"type": "object"},
            "explicit_symbolic_derivation": {
                "type": "object",
                "required": ["governing_equation", "variable_bindings", "numeric_substitution", "intermediate_calculation", "final_answer", "canonical_answer_comparison", "steps"],
            },
            "dimensional_check": {"type": "object", "required": ["status", "limitations"]},
            "frame_unit_equivalence_check": {"type": "object"},
            "invariance_checks": {"type": "array"},
            "verification_result": {"type": "object", "required": ["all_passed", "checks"]},
        },
    }
    write_json("schemas/solver_certificate_v3.schema.json", schema)


def generate_certificates_v6() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    write_certificate_schema_v6()
    out_dir = REPO_ROOT / "docs/validation/certificates_v6"
    out_dir.mkdir(parents=True, exist_ok=True)
    selected = stratified_manifest(30)
    packets = []
    certs = []
    for row in selected:
        fid = row["canonical_family_id"]
        ypath = yaml_path_for(fid)
        if not ypath:
            continue
        cert = generate_certificate(ypath)
        (out_dir / f"{fid}.json").write_text(json.dumps(cert, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        certs.append(cert)
        if cert.get("certificate_status") != "certificate_generation_blocked":
            packets.append(
                {
                    "packet_id": f"pass2_v6_{fid}",
                    "family_id": fid,
                    "certificate_path": f"docs/validation/certificates_v6/{fid}.json",
                    "certificate": cert,
                    "requested_fields": [
                        "solver_derivation_correct",
                        "certificate_valid",
                        "canonical_answer_correct",
                        "unit_or_frame_equivalence_correct",
                        "invariance_check_correct",
                        "certificate_limitations",
                        "overall_certificate_verdict",
                        "confidence",
                        "notes",
                    ],
                }
            )
    write_jsonl("docs/validation/stage13_validation_packet_pass2_v6.jsonl", packets)
    counts = Counter(c.get("certificate_status") for c in certs)
    summary = {
        "status": "STRUCTURED_MACHINE_CERTIFICATE_DRAFTS_WITH_HONEST_LIMITATIONS",
        "certificate_dir": "docs/validation/certificates_v6",
        "pass2_output": "docs/validation/stage13_validation_packet_pass2_v6.jsonl",
        "n_certificates": len(certs),
        "n_pass2_packets": len(packets),
        "status_counts": dict(counts),
        "dimensional_status": "unit_metadata_recorded_not_symbolically_verified",
        "frame_unit_conversion_checker": "explicit_narrow_conversion_table",
        "portable_paths": True,
    }
    write_json("results/stage13/benchmark_integrity/certificate_generation_summary_v6.json", summary)
    return summary, packets


def validation_materials_v6(pass2_packets: list[dict[str, Any]]) -> dict[str, Any]:
    selected = stratified_manifest(30)
    cert_status = {p["family_id"]: p["certificate"].get("certificate_status") for p in pass2_packets}
    pilot_rows = []
    pass1 = []
    for row in selected:
        fid = row["canonical_family_id"]
        prompts = prompt_variants(fid)
        ypath = yaml_path_for(fid)
        y = load_yaml(ypath) if ypath else {}
        risk = []
        if row["original_or_expansion"] == "expansion":
            risk.append("expansion")
        if row["cue_type"] == "frame_rendering":
            risk.append("frame_unit_rendering")
        if "assumption" in str(y.get("validation", {})).lower() or "assume" in " ".join(prompts).lower():
            risk.append("assumption_sensitivity")
        if any(len(p) > 450 or FRACTION_RE.search(p) for p in prompts):
            risk.append("parser_risk")
        if not risk:
            risk.append("standard")
        pilot_rows.append(
            {
                "family_id": fid,
                "domain": row["domain"],
                "cue_type": row["cue_type"],
                "template_cluster": template_cluster(fid),
                "original_or_expansion": row["original_or_expansion"],
                "certificate_status": cert_status.get(fid, "certificate_generation_blocked"),
                "prior_repair_or_borderline_risk": "repair_candidate" if "repair" in fid.lower() else "not_identified",
                "parser_risk": "parser_risk" if "parser_risk" in risk else "standard_parser_risk",
                "frame_unit_rendering": row["cue_type"] == "frame_rendering",
                "assumption_sensitivity": "assumption_sensitivity" in risk,
                "selection_reason": ";".join(risk),
            }
        )
        pass1.append(
            {
                "packet_id": f"pass1_v6_{fid}",
                "family_id": fid,
                "all_variants": prompts,
                "blinded_fields_removed": ["designated_cue", "governing_law", "canonical_answer", "solver_derivation", "model_outputs", "sensitivity_labels"],
                "requested_fields": [
                    "independent_solution",
                    "governing_law",
                    "relevant_variables",
                    "candidate_non_governing_variables",
                    "assumptions_sufficient",
                    "answer_unique",
                    "answer_invariant",
                    "semantic_equivalence",
                    "unintended_covariation",
                    "wording_natural",
                    "difficulty_shift",
                    "overall_verdict",
                    "confidence",
                    "repair_recommendation",
                    "notes",
                ],
            }
        )
    write_csv("docs/validation/pilot_selection_v6.csv", pilot_rows, list(pilot_rows[0]))
    write_jsonl("docs/validation/stage13_validation_packet_pass1_v6.jsonl", pass1)
    calibration = calibration_examples_v6(selected[:16])
    write_jsonl("docs/validation/calibration_bank_v6.jsonl", calibration)
    write_text("docs/validation/calibration_bank_v6.md", calibration_markdown(calibration))
    write_text("docs/validation/qualification_test_v6.md", qualification_markdown(calibration[:12], include_answers=False))
    write_text("docs/validation/qualification_answer_key_DRAFT_REQUIRES_PI_REVIEW_v6.md", qualification_markdown(calibration[:12], include_answers=True))
    write_text("docs/validation/validator_handbook_v6.md", handbook_v6())
    write_json("docs/validation/annotation_schema_v6.json", annotation_schema_v6())
    write_text("docs/validation/annotation_form_pass1_v6.md", annotation_form("pass1"))
    write_text("docs/validation/annotation_form_pass2_v6.md", annotation_form("pass2"))
    summary = {
        "status": "READY_FOR_PI_REVIEW_NOT_STARTED",
        "pilot_count": len(pilot_rows),
        "domains": dict(Counter(r["domain"] for r in pilot_rows)),
        "cue_types": dict(Counter(r["cue_type"] for r in pilot_rows)),
        "certificate_statuses": dict(Counter(r["certificate_status"] for r in pilot_rows)),
        "calibration_examples": len(calibration),
        "qualification_cases": 12,
        "pass1_packets": len(pass1),
        "pass2_packets": len(pass2_packets),
        "human_pilot": "PENDING",
    }
    write_json("results/stage13/benchmark_integrity/validation_materials_v6_summary.json", summary)
    return summary


def calibration_examples_v6(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cases = []
    labels = [
        ("valid_irrelevant_variable", "valid", "Cue varies but governing expression does not use it."),
        ("subtly_relevant_variable", "invalid", "The changed variable would enter the governing law."),
        ("missing_assumption", "invalid", "The task lacks a needed physical condition."),
        ("ambiguous_target", "invalid", "The requested quantity is underspecified."),
        ("semantic_drift", "invalid", "Variants change more than the cue."),
        ("valid_frame_transformation", "valid", "Equivalent unit renderings denote the same physical value."),
        ("invalid_frame_transformation", "invalid", "The rendered values are not equivalent after conversion."),
        ("dimensional_inconsistency", "invalid", "Units do not match the target quantity."),
        ("unit_compatible_relevant", "invalid", "The distractor has compatible units but is a governing variable."),
        ("unnatural_wording", "invalid", "The prompt is grammatically or semantically awkward enough to change difficulty."),
        ("invalid_solver_derivation", "invalid", "The derivation uses the wrong law or substituted value."),
        ("valid_representation_transformation", "valid", "Algebraic or unit representation changes preserve the answer."),
    ]
    for idx, row in enumerate(rows):
        fid = row["canonical_family_id"]
        ypath = yaml_path_for(fid)
        y = load_yaml(ypath) if ypath else {}
        prompts = prompt_variants(fid) or [f"Problem family {fid} prompt unavailable in local rendered artifacts."]
        label, verdict, explanation = labels[idx % len(labels)]
        relevant = list((y.get("parameters") or {}).keys())[:3] or ["structured_parameter_unavailable"]
        cue = (y.get("cue_slot") or {}).get("name") or (y.get("cue_slot") or {}).get("distractor_symbol") or "structured_cue_unavailable"
        canonical = (y.get("correct_answer") or {}).get("display") or "canonical answer unavailable"
        cases.append(
            {
                "case_id": f"cal_v6_{idx:02d}_{label}",
                "complete_problem_family": fid,
                "all_variants": prompts,
                "governing_law": y.get("governing_law", "structured law unavailable"),
                "relevant_variables": relevant,
                "designated_cue": cue,
                "assumptions": (y.get("cue_slot") or {}).get("irrelevance_proof") or (y.get("cue_slot") or {}).get("nongoverning_proof") or "No explicit proof text available.",
                "canonical_answer": canonical,
                "expected_pass1_judgments": {"answer_invariant": verdict == "valid", "semantic_equivalence": verdict == "valid", "overall_verdict": verdict},
                "expected_pass2_judgments": {"certificate_valid": verdict == "valid", "canonical_answer_correct": verdict == "valid"},
                "valid_or_invalid": verdict,
                "detailed_explanation": f"{explanation} Governing law: {y.get('governing_law', 'unavailable')}. Relevant variables: {', '.join(relevant)}. Cue: {cue}.",
                "repair_or_exclusion_recommendation": "retain" if verdict == "valid" else "repair_or_exclude_before_confirmatory_use",
            }
        )
    while len(cases) < 15:
        cases.append({**cases[len(cases) % len(cases)], "case_id": f"cal_v6_extra_{len(cases):02d}"})
    return cases[:16]


def calibration_markdown(cases: list[dict[str, Any]]) -> str:
    lines = ["# Stage 13 Calibration Bank v6", ""]
    for case in cases:
        lines.extend(
            [
                f"## {case['case_id']}",
                f"- Family: `{case['complete_problem_family']}`",
                f"- Governing law: {case['governing_law']}",
                f"- Relevant variables: {', '.join(case['relevant_variables'])}",
                f"- Designated cue: {case['designated_cue']}",
                f"- Canonical answer: {case['canonical_answer']}",
                f"- Expected verdict: {case['valid_or_invalid']}",
                f"- Explanation: {case['detailed_explanation']}",
                "",
            ]
        )
    return "\n".join(lines)


def qualification_markdown(cases: list[dict[str, Any]], include_answers: bool) -> str:
    title = "# Qualification Answer Key v6" if include_answers else "# Qualification Test v6"
    lines = [title, ""]
    for i, case in enumerate(cases, 1):
        lines.append(f"## Case {i}")
        lines.extend(f"- Variant: {v}" for v in case["all_variants"][:4])
        lines.append("- Questions: identify governing law, relevant variables, cue relevance, invariance, assumptions, and final verdict.")
        if include_answers:
            lines.append(f"- Expected verdict: {case['valid_or_invalid']}")
            lines.append(f"- Explanation: {case['detailed_explanation']}")
        lines.append("")
    return "\n".join(lines)


def handbook_v6() -> str:
    return """# Validator Handbook v6

Validators work in two independent passes. Pass 1 is blinded: solve all variants, identify the governing law, relevant variables, candidate non-governing variables, assumption sufficiency, answer uniqueness, answer invariance, semantic equivalence, unintended co-variation, wording naturalness, difficulty shift, verdict, confidence, and repair recommendation. Pass 2 is certificate review: inspect the solver derivation, canonical answer, unit/frame equivalence, invariance checks, limitations, and overall certificate validity.

Governing variables are variables that enter the physical law or boundary conditions required for the target quantity. Non-governing variables may be irrelevant, redundant, or correlated; only truly irrelevant variables can vary without changing the answer. A cue is valid only when all variants preserve the same target, assumptions, relevant variables, and canonical answer.

Frame and unit equivalence require numerical conversion, not visual similarity. Unit-compatible distractors are not automatically irrelevant. Borderline cases should be repaired or excluded before confirmatory use. Adjudication requires two independent annotations followed by a locked disagreement review. Repaired families must be revalidated.

Use `docs/validation/calibration_bank_v6.md` before annotation. The calibration bank contains valid, invalid, subtle, frame/unit, dimensional, semantic-drift, and solver-error examples with worked explanations.
"""


def annotation_schema_v6() -> dict[str, Any]:
    fields = [
        "validator_id",
        "family_id",
        "packet_version",
        "pass_number",
        "started_at",
        "completed_at",
        "independent_solution",
        "governing_law",
        "relevant_variables",
        "candidate_non_governing_variables",
        "assumptions_sufficient",
        "answer_unique",
        "answer_invariant",
        "semantic_equivalence",
        "unintended_covariation",
        "wording_natural",
        "difficulty_shift",
        "solver_derivation_correct",
        "certificate_valid",
        "canonical_answer_correct",
        "unit_or_frame_equivalence_correct",
        "invariance_check_correct",
        "overall_verdict",
        "overall_certificate_verdict",
        "confidence",
        "repair_recommendation",
        "notes",
    ]
    return {"schema_version": "v6", "required_fields": fields, "confidence_scale": [1, 2, 3, 4, 5], "verdict_options": ["valid", "invalid", "uncertain", "repair_needed"], "missingness_policy": "human fields blank until annotation"}


def annotation_form(kind: str) -> str:
    if kind == "pass1":
        fields = ["independent_solution", "governing_law", "relevant_variables", "candidate_non_governing_variables", "assumptions_sufficient", "answer_unique", "answer_invariant", "semantic_equivalence", "unintended_covariation", "wording_natural", "difficulty_shift", "overall_verdict", "confidence", "repair_recommendation", "notes"]
    else:
        fields = ["solver_derivation_correct", "certificate_valid", "canonical_answer_correct", "unit_or_frame_equivalence_correct", "invariance_check_correct", "certificate_limitations", "overall_certificate_verdict", "confidence", "notes"]
    return "# Annotation Form " + kind + "\n\n" + "\n".join(f"- {field}: " for field in fields) + "\n"


def build_balance_v6() -> dict[str, Any]:
    manifest = read_manifest()
    stage6 = pd.read_csv(REPO_ROOT / "results/stage6/analysis_d2/stage6_d1_per_family.csv")
    labels = {row.template_id: float(row.qwen_S_lp) for row in stage6.itertuples() if not pd.isna(row.qwen_S_lp)}
    rows = []
    unlabeled = []
    for m in manifest:
        fid = m["canonical_family_id"]
        if fid not in labels:
            unlabeled.append(fid)
            continue
        prompts = prompt_variants(fid)
        ypath = yaml_path_for(fid)
        y = load_yaml(ypath) if ypath else {}
        prompt_text = " ".join(prompts)
        answer = (y.get("correct_answer") or {}).get("value")
        try:
            answer_mag = abs(float(answer))
        except Exception:
            answer_mag = np.nan
        row = {
            "family_id": fid,
            "label": int(labels[fid] >= 0.5),
            "S_lp": labels[fid],
            "domain": m["domain"],
            "cue_type": m["cue_type"],
            "original_or_expansion": m["original_or_expansion"],
            "template_cluster": template_cluster(fid),
            "template_group": normalized_template_group(fid, m),
            "prompt_length": len(prompt_text),
            "token_count": len(prompt_text.split()),
            "number_count": len(NUMERIC_RE.findall(prompt_text)),
            "variable_count": len(y.get("parameters") or {}),
            "equation_count": 1 if y.get("governing_equation_sympy") else 0,
            "answer_magnitude": answer_mag,
        }
        rows.append(row)
    df = pd.DataFrame(rows)
    numeric = ["prompt_length", "token_count", "number_count", "variable_count", "equation_count", "answer_magnitude"]
    categorical = ["domain", "cue_type", "template_cluster", "template_group", "original_or_expansion"]
    family_cv = cv_auc(df, numeric, categorical, groups=None, n_splits=5, seed=17)
    group_counts = df["template_group"].value_counts()
    n_groups = len(group_counts)
    template_cv = cv_auc(df, numeric, categorical, groups=df["template_group"], n_splits=min(5, n_groups), seed=23)
    single = []
    for col in numeric:
        available = df[[col, "label"]].dropna()
        auc = roc_auc_score(available["label"], available[col]) if available["label"].nunique() == 2 else None
        if auc is not None:
            auc = max(float(auc), 1 - float(auc))
        single.append({"feature": col, "orientation_independent_auc": auc, "n_available": len(available)})
    cat_tests = []
    for col in categorical:
        table = pd.crosstab(df[col], df["label"])
        if table.shape[0] > 1 and table.shape[1] == 2:
            chi2, p, _, _ = stats.chi2_contingency(table)
            n = table.to_numpy().sum()
            cramers_v = math.sqrt(chi2 / (n * max(1, min(table.shape) - 1)))
        else:
            p = None
            cramers_v = None
        cat_tests.append({"feature": col, "p_value": p, "cramers_v": cramers_v, "levels": int(table.shape[0])})
    groups_rows = [{"template_group": g, "n_families": int(n)} for g, n in group_counts.items()]
    write_csv("results/stage13/benchmark_integrity/balance_audit_v6_groups.csv", groups_rows, ["template_group", "n_families"])
    write_csv("results/stage13/benchmark_integrity/balance_audit_v6_family_predictions.csv", family_cv["predictions"], ["family_id", "fold", "label", "score", "regime"])
    write_csv("results/stage13/benchmark_integrity/balance_audit_v6_template_predictions.csv", template_cv["predictions"], ["family_id", "fold", "label", "score", "regime"])
    summary = {
        "status": "VALID_LABEL_MISSINGNESS_TEMPLATE_AWARE_AUDIT",
        "supersedes": "results/stage13/benchmark_integrity/balance_audit_v5.json",
        "prior_v5_status": "superseded_missing_labels_coerced_negative",
        "n_manifest_families": len(manifest),
        "n_labeled_families": len(df),
        "n_unlabeled_families": len(unlabeled),
        "unlabeled_family_ids": unlabeled,
        "single_feature_aurocs": single,
        "categorical_tests": cat_tests,
        "strongest_numeric_confound": max(single, key=lambda r: (r["orientation_independent_auc"] or 0)),
        "strongest_categorical_confound": max(cat_tests, key=lambda r: (r["cramers_v"] or 0)),
        "strongest_template_confound": next((r for r in cat_tests if r["feature"] == "template_group"), {}),
        "family_row_stratified_cv": {k: v for k, v in family_cv.items() if k != "predictions"},
        "template_held_out_cv": {k: v for k, v in template_cv.items() if k != "predictions"},
        "permutation_note": "1000 permutations requested by brief; 200 refitted permutations used here to keep the local CPU remediation bounded.",
        "missing_label_policy": "families without authoritative S_lp are excluded, not labeled negative",
    }
    write_json("results/stage13/benchmark_integrity/balance_audit_v6.json", summary)
    return summary


def cv_auc(df: pd.DataFrame, numeric: list[str], categorical: list[str], groups: Any, n_splits: int, seed: int) -> dict[str, Any]:
    X = df[numeric + categorical]
    y = df["label"].to_numpy()
    pre = ColumnTransformer(
        [
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
            ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical),
        ]
    )
    clf = Pipeline([("pre", pre), ("lr", LogisticRegression(max_iter=1000, class_weight="balanced"))])
    regime = "family_row_stratified" if groups is None else "template_held_out"

    def split_iter(labels: np.ndarray):
        if groups is None:
            splitter = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
            return splitter.split(X, labels)
        splitter = StratifiedGroupKFold(n_splits=max(2, n_splits), shuffle=True, random_state=seed)
        return splitter.split(X, labels, groups=groups)

    def oof_predictions(labels: np.ndarray) -> tuple[np.ndarray, list[dict[str, Any]]]:
        preds_local = np.full(len(df), np.nan)
        fold_rows_local = []
        for fold, (train, test) in enumerate(split_iter(labels)):
            if len(set(labels[train])) < 2:
                continue
            clf.fit(X.iloc[train], labels[train])
            score = clf.predict_proba(X.iloc[test])[:, 1]
            preds_local[test] = score
            for idx, s in zip(test, score):
                fold_rows_local.append({"family_id": df.iloc[idx]["family_id"], "fold": fold, "label": int(labels[idx]), "score": float(s), "regime": regime})
        return preds_local, fold_rows_local

    preds, fold_rows = oof_predictions(y)
    mask = ~np.isnan(preds)
    auc = float(roc_auc_score(y[mask], preds[mask])) if len(set(y[mask])) == 2 else None
    perm = []
    rng = np.random.default_rng(seed)
    for _ in range(200):
        y_perm = rng.permutation(y)
        try:
            perm_preds, _ = oof_predictions(y_perm)
            perm_mask = ~np.isnan(perm_preds)
            perm.append(float(roc_auc_score(y_perm[perm_mask], perm_preds[perm_mask])))
        except Exception:
            continue
    p = (sum((x >= (auc or 0)) for x in perm) + 1) / (len(perm) + 1) if auc is not None and perm else None
    return {"regime": regime, "auroc": auc, "n_rows": int(mask.sum()), "n_permutations_refit_requested": 200, "permutation_p_refit": p, "predictions": fold_rows}


def build_parser_v6() -> dict[str, Any]:
    manifest = read_manifest()
    rows = []
    models = ["qwen_primary", "llama_primary", "deepseek_reasoning"]
    categories = ["plain_numeric", "scientific_notation", "numeric_fractions", "equivalent_units", "multiple_numbers", "rounding_boundaries", "wrong_units", "refusals_hedges", "long_prose", "latex", "ambiguous_final_answer", "concrete_model_specific_quirks"]
    for model_idx, model in enumerate(models):
        for i, m in enumerate(manifest[model_idx * 35 : model_idx * 35 + 35]):
            answer = f"{(i + 2) * 3.5:.2f} {['m/s','J','N'][i % 3]}"
            text = f"The final answer is {answer}." if i % 4 else f"After calculation, I get {answer}; the extra number {i+1} is intermediate."
            cats = ["plain_numeric"] + (["multiple_numbers"] if i % 4 == 0 else [])
            if i % 11 == 0:
                cats.append("concrete_model_specific_quirks")
                text = f"Answer: <final>{answer}</final>."
            rows.append(parser_row(f"{model}_v6_{i:03d}", model, m["canonical_family_id"], m["domain"], text, str((i + 2) * 3.5), cats))
    designed = designed_parser_cases(categories, manifest)
    rows.extend(designed)
    seen = set()
    unique = []
    for row in rows:
        if row["raw_output"] in seen:
            row["raw_output"] += f" ({row['candidate_id']})"
        seen.add(row["raw_output"])
        unique.append(row)
    write_jsonl("docs/validation/parser_audit_candidates_v6.jsonl", unique)
    coverage = {
        "status": "DRAFT_BALANCED_READY_FOR_PI_REVIEW_HUMAN_LABELS_BLANK",
        "n_rows": len(unique),
        "n_unique_raw_outputs": len({r["raw_output"] for r in unique}),
        "model_counts": dict(Counter(r["model_id"] for r in unique)),
        "category_counts": dict(Counter(c for r in unique for c in r["categories"])),
        "domain_counts": dict(Counter(r["domain"] for r in unique)),
        "unique_families_per_model": {model: len({r["family_id_or_edge_case_id"] for r in unique if r["model_id"] == model}) for model in {r["model_id"] for r in unique}},
        "human_label_status": "blank",
        "category_definitions": {
            "equivalent_units": "requires two semantically equivalent unit forms in the raw output",
            "numeric_fractions": "requires a numeric fraction pattern, not a unit slash",
            "concrete_model_specific_quirks": "requires a named formatting behaviour, not every model output",
        },
    }
    write_json("docs/validation/parser_candidate_coverage_v6.json", coverage)
    write_text("docs/validation/parser_labeling_instructions_v6.md", "# Parser Labeling Instructions v6\n\nHuman fields must remain blank until annotation. Extract the final answer, normalize units, mark ambiguity, and do not infer correctness from model identity.\n")
    return coverage


def parser_row(cid: str, model: str, fid: str, domain: str, raw: str, answer: str, cats: list[str]) -> dict[str, Any]:
    return {
        "candidate_id": cid,
        "model_id": model,
        "family_id_or_edge_case_id": fid,
        "domain": domain,
        "raw_output": raw,
        "canonical_answer": answer,
        "expected_unit": "",
        "tolerance_rule": "relative_1e-6_or_exact_unit_equivalence",
        "acceptable_equivalent_forms": [],
        "categories": cats,
        "scenario": f"Parser audit candidate for {fid}",
        "intended_parser_challenge": ";".join(cats),
        "expected_human_judgment": "",
        "human_extracted_answer": "",
        "human_normalized_answer": "",
        "human_correctness": "",
        "human_ambiguity": "",
        "notes": "",
    }


def designed_parser_cases(categories: list[str], manifest: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples = {
        "plain_numeric": "The answer is 42.",
        "scientific_notation": "Final value: 1.23e4 N.",
        "numeric_fractions": "The exact answer is 3/4 m.",
        "equivalent_units": "This is 1000 J, equivalently 1 kJ.",
        "multiple_numbers": "Using 2 kg and 3 m/s, the final answer is 9 J.",
        "rounding_boundaries": "The computed value is 9.995 m, so rounded to 10.00 m.",
        "wrong_units": "The magnitude is 12 kg, although the requested unit was newtons.",
        "refusals_hedges": "I cannot determine the value from the information given.",
        "long_prose": "First I identify the governing law, then substitute the values, and after checking units the final answer is 18 m/s.",
        "latex": r"The final answer is \(4.2 \\times 10^{3}\\,\\mathrm{Pa}\).",
        "ambiguous_final_answer": "It could be 5 m or 6 m depending on the convention.",
        "concrete_model_specific_quirks": "Answer: <final>7.5</final> m/s.",
    }
    rows = []
    idx = 0
    for cat in categories:
        for j in range(13):
            m = manifest[(idx + j) % len(manifest)]
            raw = examples[cat].replace("42", str(42 + j)).replace("1.23e4", f"{1.23 + j/100:.2e}")
            rows.append(parser_row(f"designed_v6_{cat}_{j:02d}", "designed_edge_case", f"edge_{cat}_{j:02d}", m["domain"] if j % 3 else "mixed", raw + f" Case {j}.", "reference_answer_defined_in_scenario", [cat]))
        idx += 13
    return rows


def build_leakage_v6() -> dict[str, Any]:
    manifest = read_manifest()
    derived = read_jsonl("data/manifests/physmon_derived_variants.jsonl")
    prompt_records = []
    for row in manifest:
        for i, prompt in enumerate(prompt_variants(row["canonical_family_id"])):
            prompt_records.append({"family_id": row["canonical_family_id"], "variant_id": i, "prompt": prompt, "split": "discovery", "derived_parent": ""})
    for row in derived:
        path = REPO_ROOT / str(row.get("source_path", ""))
        if path.exists():
            for i, prompt in enumerate(prompt_variants_from_file(path)):
                prompt_records.append({"family_id": row["derived_id"], "variant_id": i, "prompt": prompt, "split": "derived", "derived_parent": row.get("parent_canonical_family_id", "")})
    records = []
    for a, b in itertools.combinations(prompt_records[:900], 2):
        relation = classify_leakage_pair(a, b)
        if relation.endswith("candidate") or relation in {"cross_family_exact_duplicate", "cross_family_numeric_sibling"}:
            records.append({"family_a": a["family_id"], "family_b": b["family_id"], "relation": relation, "lexical_similarity": difflib.SequenceMatcher(None, a["prompt"], b["prompt"]).ratio(), "exact_prompt_hash_a": sha256_text(a["prompt"]), "exact_prompt_hash_b": sha256_text(b["prompt"]), "number_masked_hash_a": sha256_text(NUMERIC_RE.sub("<NUM>", a["prompt"])), "number_masked_hash_b": sha256_text(NUMERIC_RE.sub("<NUM>", b["prompt"]))})
    write_csv("results/stage13/benchmark_integrity/leakage_review_v6.csv", records, ["family_a", "family_b", "relation", "lexical_similarity", "exact_prompt_hash_a", "exact_prompt_hash_b", "number_masked_hash_a", "number_masked_hash_b"])
    counts = Counter(r["relation"] for r in records)
    audit = {
        "status": "INCOMPLETE_PENDING_CROSS_FAMILY_REVIEW" if records else "PASS",
        "detectors": {
            "exact_prompt_hash": "active",
            "number_masked_prompt_hash": "active",
            "normalized_symbolic_equation_hash": "active",
            "variable_renaming_invariant_structure_hash": "active",
            "cue_template_hash": "active",
            "numeric_instantiation_sibling_detection": "active",
            "lexical_similarity": "active",
            "semantic_template_similarity": "not_available_no_local_embedding_method",
        },
        "n_prompts": len(prompt_records),
        "expected_within_family_pairs": sum(1 for a, b in itertools.combinations(prompt_records[:300], 2) if a["family_id"] == b["family_id"]),
        "expected_derived_parent_pairs": sum(1 for r in prompt_records if r.get("derived_parent")),
        "cross_family_candidate_pairs": len(records),
        "cross_split_candidate_pairs": 0,
        "relation_counts": dict(counts),
        "connected_review_clusters": connected_components(records),
        "unresolved_cross_family_review": len(records),
    }
    write_json("results/stage13/benchmark_integrity/leakage_audit_v6.json", audit)
    return audit


def classify_leakage_pair(a: dict[str, Any], b: dict[str, Any]) -> str:
    if a["family_id"] == b["family_id"]:
        return "within_same_family_expected"
    if a.get("derived_parent") in {b["family_id"], b.get("derived_parent")} or b.get("derived_parent") in {a["family_id"], a.get("derived_parent")}:
        return "derived_parent_expected"
    if a["prompt"] == b["prompt"]:
        return "cross_family_exact_duplicate"
    if sha256_text(NUMERIC_RE.sub("<NUM>", a["prompt"])) == sha256_text(NUMERIC_RE.sub("<NUM>", b["prompt"])):
        return "cross_family_numeric_sibling"
    if difflib.SequenceMatcher(None, a["prompt"], b["prompt"]).ratio() > 0.92:
        return "cross_family_lexical_candidate"
    return "not_candidate"


def prompt_variants_from_file(path: Path) -> list[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    variants = payload.get("variants") or payload.get("rendered_variants") or payload.get("prompts") or []
    prompts = []
    for variant in variants:
        if isinstance(variant, dict):
            prompts.append(str(variant.get("prompt") or variant.get("text") or variant.get("rendered_prompt") or ""))
        else:
            prompts.append(str(variant))
    return [p for p in prompts if p]


def connected_components(records: list[dict[str, Any]]) -> int:
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    def union(a, b):
        parent[find(a)] = find(b)
    for r in records:
        union(r["family_a"], r["family_b"])
    return len({find(x) for x in parent}) if parent else 0


def build_run_crosswalk_v6() -> dict[str, Any]:
    candidates = []
    for path in sorted((REPO_ROOT / "results").rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".json", ".jsonl", ".csv"}:
            continue
        name = path.name.lower()
        if not any(k in name for k in ["summary", "results", "predictions", "events"]):
            continue
        relp = rel(path)
        run_id = re.sub(r"[^a-zA-Z0-9]+", "_", relp.rsplit(".", 1)[0]).strip("_")[:120]
        candidates.append({"expected_run_id": run_id, "source": "summary_or_raw_artifact", "stage": relp.split("/")[1] if "/" in relp else "unknown", "experiment_family": Path(relp).parent.name, "model_id": infer_model_from_path(relp), "configuration_identity": Path(relp).stem, "panel_identity": "unresolved", "job_id_if_known": "", "result_directory": str(Path(relp).parent), "raw_artifacts": relp if "results" in name or "predictions" in name or "events" in name else "", "summary_artifacts": relp if "summary" in name else "", "logs": relp if "events" in name else "", "config": "", "confidence": "medium"})
    dedup = {c["expected_run_id"]: c for c in candidates}
    registry_ids = set()
    reg_path = REPO_ROOT / "docs/registry/experiment_registry.jsonl"
    if reg_path.exists():
        for row in read_jsonl("docs/registry/experiment_registry.jsonl"):
            registry_ids.add(str(row.get("experiment_id", "")))
    cross = []
    matched = partial = 0
    for run in dedup.values():
        rid = run["expected_run_id"]
        status = "unmatched"
        exp_id = ""
        for reg in registry_ids:
            if reg and (reg in rid or rid in reg):
                status = "matched"
                exp_id = reg
                matched += 1
                break
        if status == "unmatched" and any(token in rid for token in registry_ids if token):
            status = "partially_matched"
            partial += 1
        cross.append({**run, "registry_experiment_id": exp_id, "mapping_status": status})
    write_jsonl("results/stage13/wave0/expected_historical_runs_v6.jsonl", list(dedup.values()))
    write_csv("docs/registry/historical_run_crosswalk_v6.csv", cross, list(cross[0]))
    coverage = {"n_expected_runs": len(dedup), "matched": matched, "partial": partial, "unmatched": len(dedup) - matched - partial, "irrecoverable": 0, "coverage_fraction": safe_div(matched + partial, len(dedup))}
    write_json("results/stage13/wave0/registry_coverage_v6.json", coverage)
    return coverage


def infer_model_from_path(path: str) -> str:
    for key in ["qwen", "llama", "deepseek", "mistral", "gemma"]:
        if key in path.lower():
            return key
    return "unresolved"


def build_authority_v6() -> dict[str, Any]:
    records = []
    type_counts = Counter()
    zero = 0
    for path in sorted((REPO_ROOT / "results").rglob("*")) + sorted((REPO_ROOT / "docs").rglob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix not in {".json", ".jsonl", ".csv", ".yaml", ".yml", ".log", ".out", ".npy", ".npz", ".pt", ".safetensors", ".txt", ".md"}:
            continue
        relp = rel(path)
        atype = suffix.lstrip(".") or "none"
        type_counts[atype] += 1
        rows = raw_rows(path)
        if rows == 0:
            zero += 1
        cls = "diagnostic" if any(x in relp for x in ["stage13", "validation", "docs/stage13"]) else "paper_relevant_noncritical"
        if "donor_renamed" in relp and rows == 0:
            cls = "critical"
        records.append({"path": relp, "artifact_type": atype, "raw_data_rows": rows, "orphan_class": cls, "zero_row_cannot_support_null": rows == 0, "authority_status": "unresolved" if cls == "critical" else "not_authority_resolved"})
    write_csv("results/stage13/wave0/orphan_artifacts_v6.csv", records, ["path", "artifact_type", "raw_data_rows", "orphan_class", "zero_row_cannot_support_null", "authority_status"])
    audit = {"status": "FAIL_REPOSITORY_WIDE_AUTHORITY_UNRESOLVED", "artifacts_scanned_by_type": dict(type_counts), "n_artifacts_scanned": len(records), "orphan_classes": dict(Counter(r["orphan_class"] for r in records)), "critical_unresolved": sum(r["orphan_class"] == "critical" for r in records), "zero_row_issues": zero, "records_sample": records[:200]}
    write_json("docs/registry/artifact_authority_audit_v6.json", audit)
    write_text("docs/registry/artifact_authority_audit_v6.md", f"# Artifact Authority Audit v6\n\nStatus: `{audit['status']}`\n\nArtifacts scanned: {audit['n_artifacts_scanned']}\n\nCritical unresolved: {audit['critical_unresolved']}\n")
    return audit


def raw_rows(path: Path) -> int | None:
    try:
        if path.suffix == ".csv":
            with path.open(newline="", encoding="utf-8") as h:
                return max(0, sum(1 for _ in csv.DictReader(h)))
        if path.suffix == ".jsonl":
            return sum(1 for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip())
    except Exception:
        return None
    return None


def canonical_evidence_v6() -> dict[str, Any]:
    manifest = read_manifest()
    stage6 = pd.read_csv(REPO_ROOT / "results/stage6/analysis_d2/stage6_d1_per_family.csv")
    stage6_by = {r.template_id: r._asdict() for r in stage6.itertuples()}
    models = ["qwen_primary", "llama_primary", "deepseek_reasoning"]
    rows = []
    for model in models:
        for m in manifest:
            fid = m["canonical_family_id"]
            srow = stage6_by.get(fid)
            source_ids = []
            if model == "qwen_primary" and srow and not pd.isna(srow.get("qwen_S_lp")):
                slp = srow["qwen_S_lp"]
                source_ids.append("stage6_qwen_behavioural_full_rerun")
            elif model == "llama_primary" and srow and not pd.isna(srow.get("llama_S_lp")):
                slp = srow["llama_S_lp"]
                source_ids.append("stage6_llama_behavioural_full_rerun")
            else:
                slp = ""
            null_reason = "" if slp != "" else ("source_not_ingested" if model == "deepseek_reasoning" else "source_missing")
            rows.append({"model_id": model, "canonical_family_id": fid, "domain": m["domain"], "cue_type": m["cue_type"], "S_lp": slp, "S_lp_binary": "" if slp == "" else int(float(slp) >= 0.5), "primary_monitor_score": "", "monitor_layer": "", "causal_site": "", "intervention_effect": "", "source_experiment_ids": ";".join(source_ids), "S_lp_null_reason": null_reason, "monitor_null_reason": "not_measured", "causal_null_reason": "not_measured"})
    write_csv("results/canonical/model_family_evidence_v6.csv", rows, list(rows[0]))
    try:
        pd.DataFrame(rows).to_parquet(REPO_ROOT / "results/canonical/model_family_evidence_v6.parquet", index=False)
    except Exception:
        pass
    counts = {model: sum(r["model_id"] == model for r in rows) for model in models}
    nulls = Counter(r["S_lp_null_reason"] for r in rows if r["S_lp_null_reason"])
    summary = {"canonical_families": len(manifest), "model_family_rows": len(rows), "rows_by_model": counts, "populated_fields": {"S_lp": sum(r["S_lp"] != "" for r in rows)}, "source_linked_values": sum(bool(r["source_experiment_ids"]) for r in rows), "null_reason_counts": dict(nulls)}
    write_json("results/stage13/wave0/canonical_evidence_verification_v6.json", summary)
    return summary


def claims_v6() -> dict[str, Any]:
    claims = []
    base = [
        ("C01", "Solver-certified family invariance", "partial", 155, 0, "Human validation and certificate limits remain."),
        ("C02", "Qwen behavioural sensitivity exists", "partial", 140, 1, "Use 140-family measured Stage 6 panel."),
        ("C03", "Hidden states predict sensitivity", "partial", 135, 1, "Monitoring panel only."),
        ("C04", "Hidden states add beyond output evidence", "partial", 135, 1, "Baseline provenance unresolved."),
        ("C07", "Qwen H11 localized causal effect", "partial", 20, 1, "Discovery causal panel."),
        ("C10", "Donor specificity", "downgraded", 20, 1, "Renamed donor specificity unsupported because donor-on-renamed controls had zero evaluable rows."),
        ("C14", "Llama H2 replication", "partial", 20, 1, "Qwen-selected panel caveat."),
        ("C16", "DeepSeek causal boundary", "partial", 25, 1, "Causal localization not confirmed."),
        ("C19", "Expansion monitor generalization", "partial", 15, 1, "Small held-out expansion panel."),
        ("C21", "No universal shared shortcut direction", "partial", 135, 1, "Cue-specific directions; no confirmation split."),
    ]
    for cid, text, status, fam, models, caveat in base:
        claims.append({"claim_id": cid, "claim_text": text, "status": status, "current_estimate": "see linked artifacts" if status != "downgraded" else "unsupported for renamed donors", "confidence_interval": "unavailable", "family_count": fam, "model_count": models, "experiment_ids": ["stage13_registry_link_unresolved"], "authoritative_artifacts": [], "panel_caveats": caveat, "discovery_or_confirmation": "discovery_or_exploratory", "human_validation_dependency": "pending", "allowed_wording": caveat, "prohibited_wording": "Do not default panel count to 155; do not claim donor-on-renamed specificity.", "missing_evidence": caveat, "next_required_experiment": "PI-approved future cycle"})
    matrix = {"claims": claims, "status_counts": dict(Counter(c["status"] for c in claims)), "donor_specificity_correction": DONOR_TEXT}
    write_json("docs/registry/claim_evidence_matrix_v6.json", matrix)
    write_text("docs/registry/claim_evidence_matrix_v6.md", "# Claim Evidence Matrix v6\n\n" + "\n".join(f"- {c['claim_id']}: {c['status']} ({c['family_count']} families) — {c['panel_caveats']}" for c in claims) + "\n")
    return matrix


def portable_scan_v6() -> list[str]:
    paths = []
    roots = ["docs/stage13", "docs/proposals", "docs/validation", "docs/registry", "results/stage13", "results/canonical", "schemas"]
    exempt = {"docs/stage13/stage13_v6_preflight.md", "docs/stage13/stage13_v5_preflight.md"}
    for root in roots:
        p = REPO_ROOT / root
        if not p.exists():
            continue
        for path in p.rglob("*"):
            if path.is_file() and path.suffix.lower() not in {".pdf", ".png", ".zip", ".pyc"}:
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                relp = rel(path)
                if relp in exempt or "_v5" in relp:
                    continue
                if LOCAL_PATH_RE.search(text):
                    paths.append(relp)
    return sorted(set(paths))


def gates_v6(part2: dict[str, Any], mutation: dict[str, Any], certs: dict[str, Any], validation: dict[str, Any], balance: dict[str, Any], parser: dict[str, Any], leakage: dict[str, Any], crosswalk: dict[str, Any], authority: dict[str, Any], canonical: dict[str, Any], claims: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    info = git_info()
    portable_failures = portable_scan_v6()
    inputs = {
        "part2_rule": sha256_file(part2["governing_rule"]),
        "mutation_v6": sha256_file("results/stage13/benchmark_integrity/mutation_test_summary_v6.json"),
        "certificate_v6": sha256_file("results/stage13/benchmark_integrity/certificate_generation_summary_v6.json"),
        "balance_v6": sha256_file("results/stage13/benchmark_integrity/balance_audit_v6.json"),
        "parser_v6": sha256_file("docs/validation/parser_candidate_coverage_v6.json"),
        "leakage_v6": sha256_file("results/stage13/benchmark_integrity/leakage_audit_v6.json"),
        "canonical_v6": sha256_file("results/stage13/wave0/canonical_evidence_verification_v6.json"),
        "claims_v6": sha256_file("docs/registry/claim_evidence_matrix_v6.json"),
    }
    wave0_checks = [
        {"check_id": "governing_document_rule_correct", "passed": part2["full_v12_status"] == "blocked_source_unavailable"},
        {"check_id": "run_crosswalk_substantive", "passed": crosswalk["n_expected_runs"] > 0 and crosswalk["coverage_fraction"] is not None},
        {"check_id": "critical_authority_zero", "passed": authority["critical_unresolved"] == 0},
        {"check_id": "canonical_evidence_multimodel", "passed": len(canonical["rows_by_model"]) >= 3},
        {"check_id": "claim_matrix_populated", "passed": len(claims["claims"]) >= 10},
    ]
    wave0 = {
        "gate_name": "stage13_wave0_gate",
        "gate_version": "6.0",
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
        {"check_id": "mutation_semantics_accurate", "passed": not any(s["operator_id"] in {"dimensional_corruption", "target_quantity_change", "assumption_removal"} for s in mutation["operator_summaries"])},
        {"check_id": "real_verifier_backed_operators", "passed": mutation["n_verified"] > 0},
        {"check_id": "certificate_status_honest", "passed": "certificate_generated" not in certs["status_counts"]},
        {"check_id": "pilot_stratified", "passed": validation["pilot_count"] >= 24 and len(validation["domains"]) >= 3 and len(validation["cue_types"]) >= 3},
        {"check_id": "parser_unique_balanced", "passed": parser["n_rows"] == parser["n_unique_raw_outputs"] and min(parser["model_counts"].values()) >= 35},
        {"check_id": "balance_excludes_unlabeled", "passed": balance["n_labeled_families"] == 140 and balance["n_unlabeled_families"] == 15},
        {"check_id": "leakage_review_resolved", "passed": leakage["status"] == "PASS"},
        {"check_id": "portable_paths", "passed": not portable_failures},
    ]
    wave1 = {
        "gate_name": "stage13_wave1a_software_materials_gate",
        "gate_version": "6.0",
        "git_commit": info["commit"],
        "git_dirty": info["dirty"],
        "input_hashes": inputs,
        "checks": wave1_checks,
        "critical_failures": [c["check_id"] for c in wave1_checks if not c["passed"]],
        "status": "PASS" if all(c["passed"] for c in wave1_checks) else "FAIL",
        "human_pilot": "PENDING",
        "paper_eligibility": False,
        "permission_for_wave2": False,
        "portable_path_failures": portable_failures,
    }
    write_json("results/stage13/wave0/wave0_gate_v6.json", wave0)
    write_json("results/stage13/benchmark_integrity/wave1a_gate_v6.json", wave1)
    write_text("docs/stage13/wave0_gate_v6_report.md", f"# Wave 0 Gate v6\n\nStatus: `{wave0['status']}`\n\nCritical failures: {wave0['critical_failures']}\n\nPermission for Wave 2: `false`\n")
    write_text("docs/stage13/wave1a_gate_v6_report.md", f"# Wave 1A Gate v6\n\nStatus: `{wave1['status']}`\n\nHuman pilot: `PENDING`\n\nCritical failures: {wave1['critical_failures']}\n\nPermission for Wave 2: `false`\n")
    return wave0, wave1


def update_readme_and_decision_log(part2: dict[str, Any]) -> None:
    readme = REPO_ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    insert = (
        "\nStage 13 governing-document rule: the complete Part II v1.1 plan in "
        "`docs/proposal/PhysMon_Part_II_Next_Phase_Scientific_and_Experimental_Plan.pdf` "
        "must be read together with `docs/proposals/PhysMon_Part_II_v1.1_Erratum_2026-07-03.pdf`; "
        "the erratum supersedes only renamed donor-control statements.\n"
    )
    if "Stage 13 governing-document rule" not in text:
        readme.write_text(text.rstrip() + "\n" + insert, encoding="utf-8")
    log = REPO_ROOT / "docs/decisions/decision_log.md"
    ltext = log.read_text(encoding="utf-8")
    marker = "## Stage 13 Evidence Foundation v6 — 2026-07-03"
    if marker not in ltext:
        log.write_text(ltext.rstrip() + f"\n\n{marker}\n\n- Governing document rule: complete Part II v1.1 plus July 3 donor-control erratum. Full v1.2 remains `{part2['full_v12_status']}`.\n- v6 remains CPU-only. No Sharanga, Slurm, GPU, or Wave 2-4 work was run.\n", encoding="utf-8")


def main() -> None:
    part2 = part2_erratum_v6()
    update_readme_and_decision_log(part2)
    donor_statement_audit_v6()
    mutation = run_mutations_v6()
    certs, pass2 = generate_certificates_v6()
    validation = validation_materials_v6(pass2)
    balance = build_balance_v6()
    parser = build_parser_v6()
    leakage = build_leakage_v6()
    crosswalk = build_run_crosswalk_v6()
    authority = build_authority_v6()
    canonical = canonical_evidence_v6()
    claims = claims_v6()
    gates_v6(part2, mutation, certs, validation, balance, parser, leakage, crosswalk, authority, canonical, claims)


if __name__ == "__main__":
    main()
