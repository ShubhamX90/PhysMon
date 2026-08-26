#!/usr/bin/env python3
"""Structure-first benchmark leakage audit (v7).

The v6 audit reported 25,360 unresolved cross-family pairs.  That number is a
detector artifact rather than a measurement: v6 compared every cross-family
prompt pair and classified any pair with ``difflib`` ratio > 0.92 as a leakage
candidate.  PhysMon prompts share a common template scaffold, so almost every
cross-family pair clears that threshold.  A queue of 25,360 pairs is not
reviewable, and its size says nothing about whether leakage exists.

v7 changes the method, not the threshold:

1.  **Structural signatures first.**  Each prompt gets an exact hash, a
    number-masked hash, a normalized governing-equation hash, a
    variable-renaming-invariant structure hash, and a cue-template hash.
2.  **Blocking.**  Pairs are only formed inside a shared signature bucket, so
    the comparison is proportional to bucket mass rather than to n^2.  v6 also
    silently truncated its population to the first 900 prompt records (and
    computed its "expected within-family" count over a *different* first 300),
    so its two headline numbers were drawn from different populations.  v7
    applies no truncation.
3.  **Lexical similarity is a tie-breaker, never a trigger.**  A pair that is
    lexically similar but whose governing equation, governing variable set, and
    canonical answer all differ is *resolved* as shared scaffold, with the
    differing fields recorded as the resolution evidence.  Only structural
    matches enter unresolved review.

Honesty constraints kept from the v6 brief:

*   Status stays one of ``PASS``, ``FAIL_EXACT_CROSS_SPLIT_DUPLICATE``,
    ``INCOMPLETE_PENDING_CROSS_FAMILY_REVIEW``.
*   A detector is reported active only if records actually carry its output.
*   Shrinking the queue by relabelling is not a resolution.  Every resolved pair
    carries the concrete evidence that resolved it.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from physmon.benchmark.generator import _render_variants  # noqa: E402
from governance_utils import (  # noqa: E402
    REPO_ROOT,
    read_jsonl,
    sha256_text,
    write_csv,
    write_json,
)


NUMERIC_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?", re.I)
SYMBOL_RE = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
WHITESPACE_RE = re.compile(r"\s+")

# Relations that are structurally expected and never enter unresolved review.
EXPECTED_RELATIONS = {"within_same_family_expected", "derived_parent_expected"}

# Relations that constitute genuine unresolved cross-family review workload.
UNRESOLVED_RELATIONS = {
    "cross_family_exact_duplicate",
    "cross_family_numeric_sibling",
    "cross_family_structural_candidate",
}


def normalize_equation(expression: str) -> str:
    """Whitespace- and case-normalized governing expression."""

    return WHITESPACE_RE.sub("", str(expression or "")).lower()


def renaming_invariant_structure(expression: str) -> str:
    """Replace symbols with positional tokens so variable renaming cannot hide a match.

    ``v_0 + a * t`` and ``u_0 + b * s`` both become ``S0+S1*S2``.
    """

    text = WHITESPACE_RE.sub("", str(expression or ""))
    mapping: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        token = match.group(0)
        if token not in mapping:
            mapping[token] = f"S{len(mapping)}"
        return mapping[token]

    return SYMBOL_RE.sub(replace, text)


def governing_symbols(expression: str) -> list[str]:
    return sorted(set(SYMBOL_RE.findall(str(expression or ""))))


def load_template(template_id: str) -> dict[str, Any] | None:
    matches = sorted((REPO_ROOT / "data/raw/templates").rglob(f"{template_id}.yaml"))
    if not matches:
        return None
    with matches[0].open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def render_variants(template: dict[str, Any]) -> list[str]:
    """Render one prompt per cue value using the production renderer.

    Delegates to physmon.benchmark.generator._render_variants so the audit sees
    exactly the prompts the benchmark produces. Rendering these by hand is how a
    leakage audit invents duplicates: parameter placeholders left unsubstituted
    make every family sharing a template look byte-identical.
    """

    return [str(variant["prompt"]) for variant in _render_variants(template)]


def build_prompt_records(manifest_path: str) -> list[dict[str, Any]]:
    """One record per rendered prompt variant, carrying every structural signature."""

    records: list[dict[str, Any]] = []
    missing: list[str] = []
    for row in read_jsonl(manifest_path):
        family_id = str(row.get("canonical_family_id") or row.get("template_id") or "")
        template = load_template(str(row.get("template_id") or family_id))
        if template is None:
            missing.append(family_id)
            continue
        equation = template.get("governing_equation_sympy") or ""
        answer = (template.get("correct_answer") or {}).get("display") or ""
        cue_template = (template.get("prompt_template") or {}).get("full_template") or ""
        for variant_id, prompt in enumerate(render_variants(template)):
            records.append(
                {
                    "family_id": family_id,
                    "variant_id": variant_id,
                    "prompt": prompt,
                    "split": str(row.get("original_or_expansion") or "unknown"),
                    "derived_parent": str(row.get("parent_family_id") or ""),
                    "domain": str(row.get("domain") or ""),
                    "cue_type": str(row.get("cue_type") or ""),
                    "governing_equation": str(equation),
                    "governing_symbols": governing_symbols(equation),
                    "canonical_answer": str(answer),
                    "exact_prompt_hash": sha256_text(prompt),
                    "number_masked_hash": sha256_text(NUMERIC_RE.sub("<NUM>", prompt)),
                    "equation_hash": sha256_text(normalize_equation(equation)),
                    "structure_hash": sha256_text(renaming_invariant_structure(equation)),
                    "cue_template_hash": sha256_text(WHITESPACE_RE.sub(" ", str(cue_template))),
                }
            )
    if missing:
        print(f"warning: {len(missing)} manifest families had no template YAML", file=sys.stderr)
    return records


def bucket_pairs(records: list[dict[str, Any]], key: str) -> set[tuple[int, int]]:
    """Index pairs that share a signature, avoiding an all-pairs scan."""

    buckets: dict[str, list[int]] = defaultdict(list)
    for index, record in enumerate(records):
        buckets[record[key]].append(index)
    pairs: set[tuple[int, int]] = set()
    for members in buckets.values():
        if len(members) < 2:
            continue
        for a, b in itertools.combinations(members, 2):
            pairs.add((a, b))
    return pairs


def classify(a: dict[str, Any], b: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Classify one candidate pair and, when resolved, record why."""

    if a["family_id"] == b["family_id"]:
        return "within_same_family_expected", {}
    if a["derived_parent"] and a["derived_parent"] == b["family_id"]:
        return "derived_parent_expected", {}
    if b["derived_parent"] and b["derived_parent"] == a["family_id"]:
        return "derived_parent_expected", {}
    if a["derived_parent"] and a["derived_parent"] == b["derived_parent"]:
        return "derived_parent_expected", {}

    if a["prompt"] == b["prompt"]:
        return "cross_family_exact_duplicate", {}

    equation_differs = a["equation_hash"] != b["equation_hash"]
    symbols_differ = a["governing_symbols"] != b["governing_symbols"]
    answer_differs = a["canonical_answer"] != b["canonical_answer"]

    if a["number_masked_hash"] == b["number_masked_hash"]:
        # Same prompt text once numbers are masked: a numeric instantiation sibling.
        return "cross_family_numeric_sibling", {}

    if a["structure_hash"] == b["structure_hash"] and not (
        equation_differs and symbols_differ and answer_differs
    ):
        return "cross_family_structural_candidate", {}

    # Shared scaffold only: the physics content genuinely differs.
    if equation_differs and answer_differs:
        return "cross_family_template_scaffold_resolved", {
            "resolved_by": "governing_equation_and_canonical_answer_both_differ",
            "equation_a": a["governing_equation"],
            "equation_b": b["governing_equation"],
            "answer_a": a["canonical_answer"],
            "answer_b": b["canonical_answer"],
            "symbols_differ": symbols_differ,
        }
    return "cross_family_structural_candidate", {}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="data/manifests/physmon_canonical_155.jsonl")
    parser.add_argument("--audit-out", default="results/stage13/benchmark_integrity/leakage_audit_v7.json")
    parser.add_argument("--review-out", default="results/stage13/benchmark_integrity/leakage_review_v7.csv")
    parser.add_argument(
        "--resolutions-out",
        default="results/stage13/benchmark_integrity/leakage_resolutions_v7.csv",
    )
    args = parser.parse_args()

    records = build_prompt_records(args.manifest)

    # Blocking: only signatures that can indicate reuse generate candidate pairs.
    candidate_pairs: set[tuple[int, int]] = set()
    for key in ("exact_prompt_hash", "number_masked_hash", "structure_hash", "cue_template_hash"):
        candidate_pairs |= bucket_pairs(records, key)

    relation_counts: Counter = Counter()
    review_rows: list[dict[str, Any]] = []
    resolution_rows: list[dict[str, Any]] = []

    for index_a, index_b in sorted(candidate_pairs):
        a, b = records[index_a], records[index_b]
        relation, evidence = classify(a, b)
        relation_counts[relation] += 1
        if relation in UNRESOLVED_RELATIONS:
            review_rows.append(
                {
                    "family_a": a["family_id"],
                    "family_b": b["family_id"],
                    "variant_a": a["variant_id"],
                    "variant_b": b["variant_id"],
                    "relation": relation,
                    "split_a": a["split"],
                    "split_b": b["split"],
                    "equation_a": a["governing_equation"],
                    "equation_b": b["governing_equation"],
                    "answer_a": a["canonical_answer"],
                    "answer_b": b["canonical_answer"],
                }
            )
        elif relation == "cross_family_template_scaffold_resolved":
            resolution_rows.append(
                {
                    "family_a": a["family_id"],
                    "family_b": b["family_id"],
                    "relation": relation,
                    "resolved_by": evidence.get("resolved_by", ""),
                    "equation_a": evidence.get("equation_a", ""),
                    "equation_b": evidence.get("equation_b", ""),
                    "answer_a": evidence.get("answer_a", ""),
                    "answer_b": evidence.get("answer_b", ""),
                }
            )

    # Adjudication is done per family pair, not per rendered variant pair, so the
    # review workload must be reported at family granularity to be meaningful.
    unresolved_family_pairs = {
        tuple(sorted((row["family_a"], row["family_b"]))) for row in review_rows
    }
    parent: dict[str, str] = {}

    def find(node: str) -> str:
        parent.setdefault(node, node)
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for left, right in unresolved_family_pairs:
        parent[find(left)] = find(right)
    clusters = len({find(node) for node in parent})

    cross_split = [
        row
        for row in review_rows
        if row["split_a"] != row["split_b"] and row["relation"] == "cross_family_exact_duplicate"
    ]

    unresolved = len(review_rows)
    if cross_split:
        status = "FAIL_EXACT_CROSS_SPLIT_DUPLICATE"
    elif unresolved:
        status = "INCOMPLETE_PENDING_CROSS_FAMILY_REVIEW"
    else:
        status = "PASS"

    # A detector is active only when the records actually carry its field.
    def detector_state(field: str) -> str:
        return "active" if records and field in records[0] else "not_emitted"

    audit = {
        "status": status,
        "method": "structure_first_blocking_v7",
        "supersedes": "results/stage13/benchmark_integrity/leakage_audit_v6.json",
        "supersession_reason": (
            "v6 classified any cross-family pair with lexical ratio > 0.92 as a leakage "
            "candidate, which the shared prompt scaffold makes near-universal, and it "
            "truncated its prompt population inconsistently (first 900 for pairs, first "
            "300 for the expected-pair count)."
        ),
        "n_prompt_records": len(records),
        "n_families": len({r["family_id"] for r in records}),
        "population_truncated": False,
        "n_candidate_pairs_after_blocking": len(candidate_pairs),
        "detectors": {
            "exact_prompt_hash": detector_state("exact_prompt_hash"),
            "number_masked_prompt_hash": detector_state("number_masked_hash"),
            "normalized_symbolic_equation_hash": detector_state("equation_hash"),
            "variable_renaming_invariant_structure_hash": detector_state("structure_hash"),
            "cue_template_hash": detector_state("cue_template_hash"),
            "numeric_instantiation_sibling_detection": "active",
            "lexical_similarity": "used_as_tiebreaker_not_trigger",
            "semantic_template_similarity": "not_available_no_local_embedding_method",
        },
        "relation_counts": dict(relation_counts),
        "expected_relation_pairs": sum(
            relation_counts[relation] for relation in EXPECTED_RELATIONS
        ),
        "resolved_scaffold_pairs": relation_counts.get(
            "cross_family_template_scaffold_resolved", 0
        ),
        "unresolved_cross_family_review": unresolved,
        "unresolved_family_pairs": len(unresolved_family_pairs),
        "unresolved_family_clusters": clusters,
        "n_families_in_unresolved_review": len(parent),
        "cross_split_exact_duplicates": len(cross_split),
        "review_csv": args.review_out,
        "resolutions_csv": args.resolutions_out,
        "interpretation": (
            "Unresolved pairs are genuine cross-family structural matches requiring "
            "adjudication. Resolved pairs each carry the differing governing equation "
            "and canonical answer that resolved them."
        ),
    }

    write_json(args.audit_out, audit)
    write_csv(
        args.review_out,
        review_rows,
        [
            "family_a", "family_b", "variant_a", "variant_b", "relation",
            "split_a", "split_b", "equation_a", "equation_b", "answer_a", "answer_b",
        ],
    )
    write_csv(
        args.resolutions_out,
        resolution_rows,
        [
            "family_a", "family_b", "relation", "resolved_by",
            "equation_a", "equation_b", "answer_a", "answer_b",
        ],
    )

    print(json.dumps({k: v for k, v in audit.items() if not isinstance(v, dict)}, indent=2))
    print("relation_counts:", json.dumps(dict(relation_counts), indent=2))


if __name__ == "__main__":
    main()
