#!/usr/bin/env python3
"""Check text about authorship and validation against the provenance fields (G0 item f).

Provenance facts are read from the records, not assumed:

* legacy Phase-I templates, `data/raw/templates/**/*.yaml`: `created_by`, and under
  `validation`: `pi_validated`, `v2_validated`, `verifier_certified`;
* the v2 gold dataset, `data/v2/dataset/v1/dataset.jsonl`: `admission_category` (UNREVIEWED means
  no human expert reviewed the item), `agent_verification`, `level_judged_by`.

Statements in the scanned text are classified as claims of human or expert authorship, human
validation, expert or physicist review, or independent (or multi-rater) validation. A claim is a
CONFLICT when no record supports it (for example "validated by physicists" when every dataset item
is UNREVIEWED and no template field records an expert), and UNSUPPORTED_BY_FIELDS when the fields
are silent or ambiguous (`pi_validated: true` does not record who validated: the decision log
shows PI self-validation for some families and an agent review delegated by the PI for others).
A claim in a negated sentence ("no human expert has reviewed ...") is a NEGATED_MENTION and one in
a sentence about plans ("a planned human validation will ...") a PLANNED_MENTION; both are
consistent with the records. A sentence denying that models or agents authored the items
("language models could not write physics") is checked against `created_by` and conflicts with
any agent-authored record. Exit 1 on any CONFLICT.

Usage:
    python3 scripts/check_provenance_consistency.py paper.txt README.md [--json report.json]

CPU only, read only (except `--json`). It does not decide what the text should say.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATES = REPO_ROOT / "data" / "raw" / "templates"
DEFAULT_DATASET = REPO_ROOT / "data" / "v2" / "dataset" / "v1" / "dataset.jsonl"

ITEM = r"(?:problems?|famil(?:y|ies)|items?|templates?|benchmark|dataset|structures?|questions?|samples?)"
HUMAN = r"(?:humans?|people|annotators?|raters?|reviewers?|the authors|authors|researchers?|students?)"
EXPERT = r"(?:experts?|physicists?|domain experts?|specialists?|professors?|phd)"

# kind -> regular expressions (case-insensitive) that state the kind of claim.
CLAIM_PATTERNS: dict[str, list[str]] = {
    "HUMAN_AUTHORSHIP": [
        rf"\b(?:written|authored|created|constructed|designed|composed|curated) (?:by hand|manually|by {HUMAN}|by {EXPERT})\b",
        r"\b(?:hand|human|expert|manually)[- ](?:written|authored|crafted|curated|constructed|designed)\b",
    ],
    "HUMAN_VALIDATION": [
        rf"\b(?:validated|verified|checked|reviewed|vetted|audited|annotated) (?:by|with) (?:a |two |several |multiple )?{HUMAN}\b",
        r"\b(?:human|manual(?:ly)?)[- ](?:validat\w+|verif\w+|review\w*|check\w*|vetted|audit\w*)\b",
        r"\bhuman validation\b",
    ],
    "EXPERT_REVIEW": [
        rf"\b(?:validated|verified|checked|reviewed|vetted|audited|confirmed|certified) (?:by|with) (?:a |two |several |multiple |independent )?{EXPERT}\b",
        rf"\b{EXPERT}[- ](?:validated|verified|checked|reviewed|vetted|confirmed|certified|review)\b",
    ],
    "INDEPENDENT_VALIDATION": [
        r"\bindependent(?:ly)? (?:human |expert |external )?(?:validat\w+|verif\w+|review\w*|check\w*|annotat\w*|audit\w*)\b",
        r"\b(?:inter-annotator|inter-rater|dual|double|two-rater|multi-rater)[- ]?(?:agreement|validation|review|annotation)\b",
        r"\bcohen'?s kappa\b",
    ],
    # A statement that models or agents did NOT author the items: it is itself negative, so
    # negation does not exempt it; it conflicts with any `created_by: agent` record.
    "MODEL_AUTHORSHIP_DENIED": [
        r"\b(?:language models?|llms?|agents?|ai (?:systems?|assistants?|models?))\b[^.]{0,300}?\b(?:could not|did not|"
        r"cannot|can not|never|were not (?:allowed|permitted) to|was not (?:allowed|permitted) to)\b[^.]{0,40}?\b"
        r"(?:write|author|create|generate|construct|determine|define)\b",
    ],
}
NEGATIVE_KINDS = {"MODEL_AUTHORSHIP_DENIED"}
PLANNED = re.compile(r"\b(?:planned|plans?|will|would|shall|to be|specif(?:y|ies|ied)|proposed|future|until|pending|"
                     r"intend\w*|scheduled)\b", re.IGNORECASE)
NEGATION = re.compile(r"\b(?:not|no|never|none|nor|without|neither|cannot|unreviewed|lack\w*|absen\w+|instead of|"
                      r"replac\w+|pending)\b", re.IGNORECASE)


def collect_facts(templates_dir: Path, dataset_path: Path) -> dict[str, Any]:
    """Counts of the provenance fields, and booleans each claim kind is judged against."""

    template_paths = sorted(templates_dir.rglob("*.yaml")) if templates_dir.is_dir() else []
    created_by: Counter = Counter()
    pi_validated: Counter = Counter()
    v2_validated: Counter = Counter()
    verifier_certified: Counter = Counter()
    for path in template_paths:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        created_by[str(payload.get("created_by"))] += 1
        validation = payload.get("validation") or {}
        pi_validated[str(validation.get("pi_validated"))] += 1
        v2_validated[str(validation.get("v2_validated"))] += 1
        verifier_certified[str(validation.get("verifier_certified"))] += 1
    rows = []
    if dataset_path.is_file():
        rows = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    admission = Counter(str(row.get("admission_category")) for row in rows)
    agent_status = Counter(str((row.get("agent_verification") or {}).get("status")) for row in rows)
    level_judged_by = Counter(str(row.get("level_judged_by")) for row in rows)

    human_created = sum(n for who, n in created_by.items() if who.lower() not in ("agent", "none", ""))
    human_reviewed_dataset = sum(n for category, n in admission.items() if category != "UNREVIEWED")
    return {
        "templates": {"n": len(template_paths), "created_by": dict(created_by),
                      "pi_validated": dict(pi_validated), "v2_validated": dict(v2_validated),
                      "verifier_certified": dict(verifier_certified)},
        "dataset": {"n": len(rows), "admission_category": dict(admission),
                    "agent_verification_status": dict(agent_status), "level_judged_by": dict(level_judged_by)},
        "supports": {
            # A field records human or expert authorship.
            "HUMAN_AUTHORSHIP": human_created > 0,
            # Some record says a human validated (pi_validated true; dataset items not UNREVIEWED).
            "HUMAN_VALIDATION": pi_validated.get("True", 0) > 0 or human_reviewed_dataset > 0,
            # No field records an expert or a physicist; the dataset's UNREVIEWED says none.
            "EXPERT_REVIEW": False,
            # v2_validated is the only multi-rater field; it is never true.
            "INDEPENDENT_VALIDATION": v2_validated.get("True", 0) > 0,
            # Supported only if no record names an agent as author.
            "MODEL_AUTHORSHIP_DENIED": created_by.get("agent", 0) == 0
            and not any("agent" in str(who).lower() for who in level_judged_by),
        },
        "ambiguous": {
            "HUMAN_VALIDATION": "pi_validated does not record who validated; the decision log (2026-06-15) shows "
                                "PI self-validation for some families and a review delegated by the PI to an agent "
                                "for others, and every v2 dataset item is UNREVIEWED",
        },
    }


def classify(supported: bool, ambiguous: bool, negated: bool, planned: bool = False) -> str:
    if negated:
        return "NEGATED_MENTION"
    if planned:
        return "PLANNED_MENTION"
    if not supported:
        return "CONFLICT"
    return "UNSUPPORTED_BY_FIELDS" if ambiguous else "CONSISTENT"


def _sentences(text: str) -> list[tuple[int, str]]:
    out = []
    for block in re.finditer(r"(?:[^\n]|\n(?!\s*\n))+", text):
        for piece in re.finditer(r"[^.!?]+(?:[.!?]+(?=\s|$)|$)", block.group(0)):
            if piece.group(0).strip():
                offset = block.start() + piece.start() + (len(piece.group(0)) - len(piece.group(0).lstrip()))
                out.append((text.count("\n", 0, offset) + 1, " ".join(piece.group(0).split())))
    return out


def scan_text(text: str, facts: dict[str, Any]) -> list[dict[str, Any]]:
    hits = []
    compiled = [(kind, re.compile(pattern, re.IGNORECASE)) for kind, patterns in CLAIM_PATTERNS.items()
                for pattern in patterns]
    # NFKC folds PDF ligatures ("speciﬁed" -> "specified") so patterns match extracted text.
    for line, sentence in _sentences(unicodedata.normalize("NFKC", text)):
        seen: set[str] = set()
        for kind, pattern in compiled:
            match = pattern.search(sentence)
            if not match or kind in seen:
                continue
            seen.add(kind)
            negative_kind = kind in NEGATIVE_KINDS
            negated = not negative_kind and bool(NEGATION.search(sentence[: match.end()]))
            planned = not negative_kind and bool(PLANNED.search(sentence))
            status = classify(facts["supports"][kind], kind in facts["ambiguous"], negated, planned)
            hits.append({"line": line, "kind": kind, "status": status, "match": match.group(0),
                         "mentions_items": bool(re.search(ITEM, sentence, re.IGNORECASE)),
                         "sentence": sentence[:400]})
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--templates", type=Path, default=DEFAULT_TEMPLATES)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)

    facts = collect_facts(args.templates, args.dataset)
    if facts["templates"]["n"] == 0 and facts["dataset"]["n"] == 0:
        print("no provenance records found; nothing can be checked (NOT_EVALUATED)", file=sys.stderr)
        return 2
    report: dict[str, Any] = {"facts": facts, "files": {}}
    for path in args.files:
        if not path.is_file():
            print(f"not a file: {path}", file=sys.stderr)
            return 2
        hits = scan_text(path.read_text(encoding="utf-8", errors="replace"), facts)
        report["files"][str(path)] = hits
        for hit in hits:
            if hit["status"] != "CONSISTENT":
                print(f"{path}:{hit['line']}: {hit['status']} {hit['kind']} '{hit['match']}' :: {hit['sentence'][:160]}")
    statuses = Counter(hit["status"] for hits in report["files"].values() for hit in hits)
    report["status_counts"] = dict(statuses)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"templates {facts['templates']['n']} (created_by {facts['templates']['created_by']}), dataset "
          f"{facts['dataset']['n']} (admission {facts['dataset']['admission_category']}); statuses {dict(statuses)}")
    return 1 if statuses.get("CONFLICT") else 0


if __name__ == "__main__":
    raise SystemExit(main())
