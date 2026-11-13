#!/usr/bin/env python3
"""Stage 15 (G1, LLM review panel): build the extended judge-qualification bank v3.

Contents: the 33 legacy planted-defect items of Stage 14.5 (27 defective, 6 valid; labelled by the user, J14.5-013),
plus role-by-value items built from the twelve M0 specs: the twelve unmodified items (valid) and planted defects of
six types on three structures each (`physmon.validation.rolevalue_bank`). A held-out portion (one item of each new
defect type and four new valid items, seed 42) is never shown to a judge unless a prompt or judge must be requalified.

Outputs under <out> (refusing to overwrite):
  pass1_packets.jsonl, pass2_packets.jsonl  judge-facing; no key fields
  key_RESTRICTED.json                       item -> defect type, expected verdict, detectable pass, split, description
  manifest.json                             counts and file hashes
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import roles_m0  # noqa: E402
from physmon.validation import rolevalue_bank as rb  # noqa: E402

LEGACY = REPO_ROOT / "docs/validation/v2/materials/v2"
SEED = 42
PER_TYPE = 3
# Accepted vocabulary terms per declared type (frozen with the protocol, before any judge sees the bank): a defect is
# detected for the declared reason when the pass-2 flags contain any accepted term. The independent pre-freeze review
# (2026-11-13) found each alternative below to be a defensible description of the planted defect.
ACCEPTED_TERMS = {
    "hidden_coupling": ["hidden_coupling", "relevant_variable_removed_from_equation"],
    "failed_transformation_identity": ["failed_transformation_identity"],
    "relevant_variable_removed_from_equation": ["relevant_variable_removed_from_equation",
                                                "failed_transformation_identity"],
    "invalid_parameter_domain": ["invalid_parameter_domain", "hidden_coupling", "contradictory_distractor_statement"],
    "inconsistent_units": ["inconsistent_units"],
    "rendering_not_minimal": ["rendering_not_minimal"],
    "insufficient_boundary_condition": ["insufficient_boundary_condition", "missing_assumption"],
    "missing_assumption": ["missing_assumption", "insufficient_boundary_condition"],
    "invalid_numerical_precision": ["invalid_numerical_precision"],
    "contradictory_distractor_statement": ["contradictory_distractor_statement"],
}
ITEM_ACCEPTED_TERMS = {  # legacy items whose single changed number reads equally as a rendering or unit defect
    "L-Q017": ["failed_transformation_identity", "rendering_not_minimal", "inconsistent_units"],
    "L-Q057": ["failed_transformation_identity", "rendering_not_minimal", "inconsistent_units"],
    "L-Q069": ["failed_transformation_identity", "rendering_not_minimal", "inconsistent_units"],
    # the physics is unaffected; the defect is text saying "coupled" against an "isolated" claim
    "L-Q043": ["hidden_coupling", "contradictory_distractor_statement"],
    "L-Q048": ["hidden_coupling", "contradictory_distractor_statement"],
}
CONTESTED = {  # kept as labelled by the user (J14.5-013); flagged by the pre-freeze review and reported separately
    "L-Q043": "the coupling does not change the answer (Kirchhoff's current law at the junction)",
    "L-Q048": "Q = m c dT uses A's own stated rise, so the coupling does not change the answer",
    "L-Q024": "'ideal' deleted; at 1 bar and 300 K a careful physicist may assume an ideal gas",
    "L-Q028": "'ideal' deleted; at 1 bar and 300 K a careful physicist may assume an ideal gas",
    "L-Q041": "'ideal' deleted; at 1 bar and 300 K a careful physicist may assume an ideal gas",
}
QUESTION = re.compile(r"What is the ([^?\n]+)\?\s*$")

LEAK_FIELDS = ("defect_type", "expected_verdict", "detectable_in", "description", "structure_id", "split",
               "physicist_confirmation", "edited_answer", "original_answer", "family")


def legacy_items() -> tuple[list[dict], list[dict], dict]:
    bank = {json.loads(line)["item_id"]: json.loads(line)
            for line in (LEGACY / "planted_defect_bank_FOR_PHYSICIST_CONFIRMATION.jsonl").read_text().splitlines()}
    p1 = {json.loads(line)["item_id"]: json.loads(line) for line in (LEGACY / "pass1_packets.jsonl").read_text().splitlines()}
    p2 = {json.loads(line)["item_id"]: json.loads(line) for line in (LEGACY / "pass2_packets.jsonl").read_text().splitlines()}
    pass1, pass2, key = [], [], {}
    for item_id, b in sorted(bank.items()):
        new_id = f"L-{item_id}"
        a1, a2 = dict(p1[item_id]), dict(p2[item_id])
        # every legacy valid control asks "Determine the X." and every defective item "What is ...?": a cue. Every
        # defective item with a "What is the X?" question gets the equivalent "Determine the X." form (13 of 27), so
        # "Determine" no longer marks a valid item (6 of 19 instead of 6 of 6).
        if b["expected_verdict"] == "invalid":
            for packet in (a1, a2):
                packet["variants"] = [QUESTION.sub(lambda m: f"Determine the {m.group(1)}.", v) for v in packet["variants"]]
        pass1.append({**a1, "item_id": new_id, "kind": "legacy"})
        pass2.append({**a2, "item_id": new_id, "kind": "legacy"})
        key[new_id] = {"defect_type": b["defect_type"], "expected_verdict": b["expected_verdict"],
                       "detectable_in": b["detectable_in"], "description": b["description"], "source": "legacy_14.5",
                       "split": "qualification", "structure_id": b["family"],
                       "accepted_terms": ITEM_ACCEPTED_TERMS.get(new_id, ACCEPTED_TERMS.get(b["defect_type"], [])),
                       "contested": CONTESTED.get(new_id)}
    return pass1, pass2, key


def role_items() -> list[dict]:
    rng = random.Random(SEED)
    sids = sorted(roles_m0.ROLE_SPECS)
    items = [rb.base_item(s, f"tmp-valid-{s}") for s in sids]
    k_eligible = [s for s in sids if roles_m0.ROLE_SPECS[s].conditional is not None]
    for defect in rb.ROLE_DEFECT_TYPES:
        pool = k_eligible if defect == "invalid_parameter_domain" else sids
        for s in rng.sample(pool, PER_TYPE):
            items.append(rb.plant(rb.base_item(s, f"tmp-{defect}-{s}"), defect))
    return items


def build(out: Path) -> dict:
    rng = random.Random(SEED)
    l1, l2, key = legacy_items()
    roles = role_items()
    ids = rng.sample(range(100, 1000), len(roles))  # neutral ids: nothing in an id reveals type or structure
    heldout: set[str] = set()
    by_type: dict[str, list[dict]] = {}
    for item, n in zip(roles, ids, strict=True):
        item["item_id"] = f"R-{n}"
        by_type.setdefault(item["defect_type"], []).append(item)
    for defect, members in sorted(by_type.items()):
        chosen = rng.sample(members, 4 if defect == "valid" else 1)
        heldout.update(m["item_id"] for m in chosen)
    p1, p2 = list(l1), list(l2)
    for item in roles:
        a, b = rb.packets(item, SEED)
        p1.append({**a, "kind": "role"})
        p2.append({**b, "kind": "role"})
        key[item["item_id"]] = {"defect_type": item["defect_type"], "expected_verdict": item["expected_verdict"],
                                "detectable_in": item["detectable_in"], "description": item["description"],
                                "source": "role_m0", "structure_id": item["structure_id"],
                                "split": "heldout" if item["item_id"] in heldout else "qualification",
                                "accepted_terms": ACCEPTED_TERMS.get(item["defect_type"], []), "contested": None}
    for packet in p1 + p2:  # leak scan: no key field in any judge-facing packet
        leaked = [f for f in LEAK_FIELDS if f in packet]
        if leaked:
            raise SystemExit(f"key field(s) {leaked} in packet {packet['item_id']}")
    order = sorted(key, key=lambda i: hashlib.sha256(f"{SEED}:{i}".encode()).hexdigest())
    p1.sort(key=lambda p: order.index(p["item_id"]))
    p2.sort(key=lambda p: order.index(p["item_id"]))
    out.mkdir(parents=True, exist_ok=False)
    files = {"pass1_packets.jsonl": "".join(json.dumps(p, ensure_ascii=False, sort_keys=True) + "\n" for p in p1),
             "pass2_packets.jsonl": "".join(json.dumps(p, ensure_ascii=False, sort_keys=True) + "\n" for p in p2),
             "key_RESTRICTED.json": json.dumps(key, indent=2, sort_keys=True) + "\n"}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    manifest = {"n_items": len(key), "by_split": dict(Counter(v["split"] for v in key.values())),
                "by_type_split": dict(Counter(f"{v['defect_type']}|{v['split']}" for v in key.values())),
                "expected": dict(Counter(f"{v['expected_verdict']}|{v['split']}" for v in key.values())),
                "sha256": {n: hashlib.sha256(t.encode()).hexdigest() for n, t in files.items()}, "seed": SEED}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="docs/validation/v2/llm_panel/bank_v3")
    args = parser.parse_args(argv)
    out = REPO_ROOT / args.out if not Path(args.out).is_absolute() else Path(args.out)
    if out.exists():
        print(f"Refusing to overwrite {out}", file=sys.stderr)
        return 2
    print(json.dumps(build(out), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
