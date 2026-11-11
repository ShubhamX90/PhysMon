#!/usr/bin/env python3
"""Check a manuscript or summary against the claim registry's prohibited wording (G0 item e).

The claim registry (`docs/registry/claim_evidence_matrix_v7.json`, with its Markdown twin
`claim_evidence_matrix_v7.md`) states, per claim, a prohibited wording in prose ("Do not claim
necessity, nor a complete circuit, from this panel."). Prose cannot be matched mechanically, so
this script keeps, per claim, a small table of regular expressions that implement that
prohibition, and it refuses to run if the registry and the table drift apart:

* every registry claim with a prohibited wording must have rules here, and the registry text
  must equal the text the rules were written for (`RULES[claim]["prohibited"]`); otherwise the
  script exits 2 and asks for the rules to be reviewed;
* the JSON and Markdown registries must state the same prohibitions.

Each scanned file is split into sentences. A rule hit in a sentence is a VIOLATION unless the
sentence negates it before the match (for example "we do not claim necessity"), in which case it
is reported as NEGATED_MENTION for a human to read; negated mentions never fail the check.
Patterns marked `source: review` implement wording the ICLR 2027 review (issue 7, analysis.md
section 5 point 2(e)) showed to carry the same prohibited meaning (for example "cancels the
sensitivity" for a knockout that inverts it).

Usage:
    python3 scripts/check_claim_wording.py draft.tex summary.md [--json report.json]

Exit status: 0 no violation, 1 violations found, 2 registry and rules out of step or bad input.
CPU only, stdlib only, read only (except `--json`).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_JSON = REPO_ROOT / "docs" / "registry" / "claim_evidence_matrix_v7.json"
DEFAULT_REGISTRY_MD = REPO_ROOT / "docs" / "registry" / "claim_evidence_matrix_v7.md"

COMPONENT_CONTEXT = r"\b(?:heads?|components?|circuits?|knock-?outs?|ablat\w+|lesions?|L\d+H?\d*|sites?)\b"

# claim_id -> prohibited wording the rules implement, and the rules: (pattern, context, source).
# `context`, when set, must also match somewhere in the same sentence.
RULES: dict[str, dict[str, Any]] = {
    "C01": {"prohibited": "Do not describe this as shortcut reliance; it is Level-2 behaviour only.",
            "rules": [(r"\bshortcut[- ]reliance\b", None, "registry"),
                      (r"\brel(?:y|ies|ied|ying|iance) on (?:a |the |physics )?shortcuts?\b", None, "registry"),
                      (r"\bshortcut[- ](?:use|exploitation)\b", None, "registry")]},
    "C02": {"prohibited": "Do not claim superiority over all baselines from this number alone.",
            "rules": [(r"\bsuperior(?:ity)? (?:to|over) (?:all|every) (?:\w+ )?baselines?\b", None, "registry"),
                      (r"\b(?:outperform|beat|surpass)(?:s|ed|ing)? (?:all|every) (?:\w+ )?baselines?\b", None, "registry"),
                      (r"\bbetter than (?:all|every) (?:\w+ )?baselines?\b", None, "registry")]},
    "C03": {"prohibited": "Do not claim independence from correctness; shared variance remains.",
            "rules": [(r"\bindependen(?:t|ce) (?:of|from) (?:answer )?correctness\b", None, "registry"),
                      (r"\borthogonal to (?:answer )?correctness\b", None, "registry")]},
    "C04": {"prohibited": "Do not present this as the monitor's ceiling without a paired test.",
            "rules": [(r"\b(?:monitor|probe)(?:'s)? (?:performance )?(?:ceiling|upper bound)\b", None, "registry"),
                      (r"\b(?:ceiling|upper bound) (?:on|for) (?:the )?(?:monitor|probe)\b", None, "registry")]},
    "C05": {"prohibited": "Do not treat the monitor's margin over entropy as established.",
            "rules": [(r"\b(?:outperform|beat|surpass)(?:s|ed|ing)? (?:the )?(?:\w+ )?entropy\b", None, "registry"),
                      (r"\b(?:significant|clear|robust|established|reliable) (?:margin|advantage|gain|improvement)"
                       r" over (?:the )?(?:\w+ )?entropy\b", None, "registry"),
                      (r"\bmargin over (?:the )?(?:\w+ )?entropy\b[^.]{0,60}\b(?:established|significant|robust)\b",
                       None, "registry")]},
    "C06": {"prohibited": "Do not describe this as equivalent to activation access.",
            "rules": [(r"\b(?:equivalent|equal) to (?:having )?activation access\b", None, "registry"),
                      (r"\b(?:replaces?|substitutes? for) activation access\b", None, "registry")]},
    "C07": {"prohibited": "Do not claim cross-model transfer from this within-model number.",
            "rules": [(r"\bcross-model transfer\b", None, "registry"),
                      (r"\btransfers? (?:across|between) (?:models|architectures|model families)\b", None, "registry"),
                      (r"\bgenerali[sz]es? (?:across|to other) models\b", None, "registry")]},
    "C08": {"prohibited": "Do not claim necessity, nor a complete circuit, from this panel.",
            "rules": [(r"\bnecessary\b", COMPONENT_CONTEXT, "registry"),
                      (r"\bnecessity\b", COMPONENT_CONTEXT, "registry"),
                      (r"\bcomplete circuit\b", None, "registry"),
                      (r"\b(?:full|whole|entire) circuit\b", None, "registry"),
                      (r"\bcancel(?:s|led|ling)? (?:the |its )?(?:\w+ )?sensitivity\b", None, "review")]},
    "C09": {"prohibited": "Do not claim a shared mechanism across architectures.",
            "rules": [(r"\bshared (?:circuit|mechanism)\b", None, "registry"),
                      (r"\bsame (?:circuit|mechanism) (?:across|in both|in all)\b", None, "registry"),
                      (r"\bmechanism (?:is )?(?:shared|common) (?:across|between)\b", None, "registry")]},
    "C10": {"prohibited": "Do not claim 100% specificity, 0.0 mean recovery, or completed renamed donor controls.",
            "rules": [(r"\b100\s?% specific(?:ity)?\b", None, "registry"),
                      (r"\b0\.0 mean recovery\b", None, "registry"),
                      (r"\bmean recovery (?:of )?0\.0\b", None, "registry"),
                      (r"\bcompleted? (?:the )?renamed[- ]donor controls?\b", None, "registry"),
                      (r"\brenamed[- ]donor controls? (?:establish|show|confirm|demonstrate)\w*\b", None, "registry")]},
}

NEGATION = re.compile(r"\b(?:not|no|never|cannot|can't|nor|without|neither|avoid\w*|prohibit\w*|forbid\w*|"
                      r"refrain\w*|unsupported|withdrawn?|retracted?)\b", re.IGNORECASE)


class RegistryMismatch(RuntimeError):
    """The registry's prohibited wording and the rule table are out of step."""


def load_registry(json_path: Path | None, md_path: Path | None) -> dict[str, str]:
    """Prohibited wording per claim from the JSON registry and/or its Markdown twin."""

    from_json: dict[str, str] = {}
    from_md: dict[str, str] = {}
    if json_path is not None and json_path.is_file():
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        for claim in payload.get("claims", []):
            text = str(claim.get("prohibited_wording") or "").strip()
            if text:
                from_json[str(claim["claim_id"])] = text
    if md_path is not None and md_path.is_file():
        current = None
        for line in md_path.read_text(encoding="utf-8").splitlines():
            heading = re.match(r"^###\s+(C\d+)\s*$", line.strip())
            if heading:
                current = heading.group(1)
                continue
            match = re.match(r"^-\s*Prohibited:\s*(.+)$", line.strip())
            if match and current:
                from_md[current] = match.group(1).strip()
    if not from_json and not from_md:
        raise RegistryMismatch("no prohibited wording found in the registry files given")
    if from_json and from_md and from_json != from_md:
        differing = sorted(k for k in set(from_json) | set(from_md) if from_json.get(k) != from_md.get(k))
        raise RegistryMismatch(f"JSON and Markdown registries disagree on {differing}")
    return from_json or from_md


def check_rules_cover(registry: dict[str, str], rules: dict[str, dict[str, Any]] = RULES) -> None:
    problems = []
    for claim, text in sorted(registry.items()):
        if claim not in rules:
            problems.append(f"{claim}: prohibited wording has no mechanical rule: {text!r}")
        elif rules[claim]["prohibited"] != text:
            problems.append(f"{claim}: registry text changed to {text!r}; review the rules written for "
                            f"{rules[claim]['prohibited']!r}")
    if problems:
        raise RegistryMismatch("; ".join(problems))


def sentences(text: str) -> list[tuple[int, str]]:
    """(first line number, sentence text) pairs; sentences may span line breaks."""

    out = []
    for block_match in re.finditer(r"(?:[^\n]|\n(?!\s*\n))+", text):
        block = block_match.group(0)
        block_start = block_match.start()
        for sentence_match in re.finditer(r"[^.!?]+(?:[.!?]+(?=\s|$)|$)", block):
            piece = sentence_match.group(0)
            if not piece.strip():
                continue
            offset = block_start + sentence_match.start() + (len(piece) - len(piece.lstrip()))
            out.append((text.count("\n", 0, offset) + 1, " ".join(piece.split())))
    return out


def scan_text(text: str, rules: dict[str, dict[str, Any]] = RULES) -> list[dict[str, Any]]:
    hits = []
    compiled = [(claim, re.compile(pattern, re.IGNORECASE), re.compile(context, re.IGNORECASE) if context else None,
                 source) for claim, spec in rules.items() for pattern, context, source in spec["rules"]]
    # NFKC folds PDF ligatures ("sufﬁcient" -> "sufficient") so patterns match extracted text.
    for line, sentence in sentences(unicodedata.normalize("NFKC", text)):
        for claim, pattern, context, source in compiled:
            match = pattern.search(sentence)
            if not match or (context is not None and not context.search(sentence)):
                continue
            negated = bool(NEGATION.search(sentence[: match.start()]))
            hits.append({"line": line, "claim": claim, "pattern": pattern.pattern, "rule_source": source,
                         "match": match.group(0), "kind": "NEGATED_MENTION" if negated else "VIOLATION",
                         "sentence": sentence[:400]})
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--registry-json", type=Path, default=DEFAULT_REGISTRY_JSON)
    parser.add_argument("--registry-md", type=Path, default=DEFAULT_REGISTRY_MD)
    parser.add_argument("--json", type=Path, default=None, help="Write the full report here.")
    args = parser.parse_args(argv)

    try:
        registry = load_registry(args.registry_json, args.registry_md)
        check_rules_cover(registry)
    except RegistryMismatch as error:
        print(f"REGISTRY/RULES MISMATCH: {error}", file=sys.stderr)
        return 2
    report: dict[str, Any] = {"registry_claims": sorted(registry), "files": {}}
    n_violations = 0
    for path in args.files:
        if not path.is_file():
            print(f"not a file: {path}", file=sys.stderr)
            return 2
        hits = scan_text(path.read_text(encoding="utf-8", errors="replace"))
        report["files"][str(path)] = hits
        for hit in hits:
            n_violations += hit["kind"] == "VIOLATION"
            print(f"{path}:{hit['line']}: {hit['kind']} {hit['claim']} ({hit['rule_source']}) "
                  f"'{hit['match']}' :: {hit['sentence'][:160]}")
    report["n_violations"] = n_violations
    report["n_negated_mentions"] = sum(h["kind"] == "NEGATED_MENTION" for hits in report["files"].values()
                                       for h in hits)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{n_violations} violation(s), {report['n_negated_mentions']} negated mention(s) in "
          f"{len(args.files)} file(s)")
    return 1 if n_violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
