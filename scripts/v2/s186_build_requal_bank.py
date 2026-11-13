#!/usr/bin/env python3
"""Stage 15 (G1, LLM review panel): build the requalification bank v4 for judge prompt v2.

The protocol requalifies a changed judge or prompt only on items no judge has seen. Bank v4 has two parts:
* fresh legacy-style items: the Stage 14.5 injection rules (`physmon.validation.defect_injection`) applied to DECOY-v1
  families used neither in the 14.5 planted bank nor in its genuine sample: three each of the types both judges failed
  in q1/gpt_q1 (`missing_assumption`, `insufficient_boundary_condition`, `contradictory_distractor_statement`,
  `invalid_numerical_precision`), one each of the other five legacy types (to show v2 did not break them), and six fresh
  valid controls (`valid_equivalent_rewrite`);
* the ten held-out role items of bank v3 (one per role defect type, four valid), unseen by any judge, regenerated with
  the bank-v4 claim wording of `physmon.validation.rolevalue_bank`.
Split "requal" for every item; thresholds are in `qualification_protocol_v2.md`. Outputs as bank v3 (pass1/pass2 packets,
key_RESTRICTED.json, manifest.json); refuses to overwrite; every packet is scanned for key fields.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import random
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.validation import defect_injection as di  # noqa: E402
from physmon.validation import rolevalue_bank as rb  # noqa: E402


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s145 = _load("s145", "scripts/v2/s145_validation_materials.py")
s178 = _load("s178", "scripts/v2/s178_build_judge_bank.py")

SEED = 4242
WANT = {"contradictory_distractor_statement": 3,
        "invalid_numerical_precision": 3, "hidden_coupling": 1, "relevant_variable_removed_from_equation": 1,
        "failed_transformation_identity": 1, "inconsistent_units": 1, "invalid_parameter_domain": 1,
        "valid_equivalent_rewrite": 6}
# Legacy-style injections: the single changed number of a failed-transformation edit reads equally as a rendering or unit
# defect; a hidden-coupling edit says "coupled" against an "isolated" claim (the physics may survive), as in bank v3.
LEGACY_ACCEPTED = {**s178.ACCEPTED_TERMS,
                   "failed_transformation_identity": ["failed_transformation_identity", "rendering_not_minimal",
                                                      "inconsistent_units"],
                   "hidden_coupling": ["hidden_coupling", "contradictory_distractor_statement",
                                       "relevant_variable_removed_from_equation"]}
# The injection rules for the two under-specification types apply only to templates already used in the 14.5 bank, and
# no unused v1 family carries a deletable condition that decides its answer (checked 2026-11-13: the six "frictionless"
# families give acceleration or net force directly; "dropped" already implies rest). These items therefore delete a
# stated, answer-deciding condition from an M0 problem text (role format, all sentences kept; the authors' claims, which
# still list the assumption, show the defect in pass 2). Each edit's phrase must occur exactly once.
ROLE_CONDITION_EDITS = {
    "S07": ("A capacitor of 20 μF, initially uncharged, is connected", "A capacitor of 20 μF is connected",
            "insufficient_boundary_condition", "'initially uncharged' deleted: the capacitor's initial charge is unknown"),
    "S72": ("An electron starts from rest and is accelerated until", "An electron is accelerated until",
            "insufficient_boundary_condition", "'starts from rest' deleted: the final kinetic energy is unknown"),
    "S02": ("A block is released from rest on a rough incline", "A block moves down a rough incline",
            "insufficient_boundary_condition", "release from rest replaced by 'moves down': the initial speed is unknown"),
    "S55": ("A sample of an ideal gas is", "A sample of gas is", "missing_assumption",
            "'ideal' deleted: the governing model of the gas is not stated (as the legacy ideal-gas items)"),
    "S13": (" and swings with a small amplitude.", " and swings.", "missing_assumption",
            "'small amplitude' deleted: the period of a large swing differs"),
    "S01": (" The string does not slip on the pulley.", "", "missing_assumption",
            "no-slip condition deleted: a slipping string would not turn the massive pulley, changing the answer"),
}
V2_MATERIALS = REPO_ROOT / "docs/validation/v2/materials/v2"
BANK_V3 = REPO_ROOT / "docs/validation/v2/llm_panel/bank_v3"


def excluded_families() -> set[str]:
    used = {json.loads(x)["family"] for x in (V2_MATERIALS / "planted_defect_bank_FOR_PHYSICIST_CONFIRMATION.jsonl")
            .read_text().splitlines() if x.strip()}
    with (V2_MATERIALS / "genuine_pilot_sample.csv").open(newline="", encoding="utf-8") as handle:
        used |= {row["family"] for row in csv.DictReader(handle)}
    return used


def fresh_items(rng: random.Random) -> tuple[list[dict], dict]:
    families, templates = s145.load_families(), s145.load_templates()
    excluded = excluded_families()
    used: set[str] = set(excluded)
    items, shortfalls = [], {}
    order = sorted(WANT, key=lambda dt: (sum(1 for f in families if f not in excluded
                                             and di.inject(dt, families[f], templates.get(f)).applicable), dt))
    for defect_type in order:  # scarcest type first, so it gets its families
        pool = [f for f in sorted(families) if f not in used
                and di.inject(defect_type, families[f], templates.get(f)).applicable]
        rng.shuffle(pool)
        domains: Counter = Counter()
        picked = []
        while pool and len(picked) < WANT[defect_type]:
            pool.sort(key=lambda f: domains[families[f]["domain"]])  # spread over domains
            fid = pool.pop(0)
            domains[families[fid]["domain"]] += 1
            picked.append(fid)
            used.add(fid)
        if len(picked) < WANT[defect_type]:
            shortfalls[defect_type] = WANT[defect_type] - len(picked)
        for fid in picked:
            template = templates[fid]
            inj = di.inject(defect_type, families[fid], template)
            pass2 = {"variants": inj.edited_prompts, "governing_equation_latex": template["governing_equation_latex"],
                     "governing_equation_sympy": inj.edited_equation or template["governing_equation_sympy"],
                     "parameters": s145.parameter_table(template), "target_quantity": template["target_quantity"],
                     "target_units": template["target_units"],
                     "certified_answer_display": inj.edited_answer or families[fid]["correct_answer"],
                     "authors_proof_text": s145.author_proof(template)}
            items.append({"family": fid, "defect_type": defect_type, "expected_verdict": inj.expected_verdict,
                          "detectable_in": inj.detectable_in, "description": inj.description,
                          "pass1": {"variants": inj.edited_prompts}, "pass2": pass2})
    return items, {"excluded_families": len(excluded), "shortfalls": shortfalls}


def condition_deleted_items() -> list[dict]:
    out = []
    for sid, (old, new, defect, description) in sorted(ROLE_CONDITION_EDITS.items()):
        item = rb.base_item(sid, f"tmp-{sid}")
        if item["problem"].count(old) != 1:
            raise SystemExit(f"{sid}: the phrase to delete occurs {item['problem'].count(old)} times")
        item = {**item, "problem": item["problem"].replace(old, new), "defect_type": defect, "expected_verdict": "invalid",
                "detectable_in": "pass1", "description": description}
        out.append(item)
    return out


def heldout_role_items() -> list[dict]:
    key = json.loads((BANK_V3 / "key_RESTRICTED.json").read_text(encoding="utf-8"))
    out = []
    for item_id, k in sorted(key.items()):
        if k["split"] != "heldout":
            continue
        base = rb.base_item(k["structure_id"], item_id)
        item = base if k["defect_type"] == "valid" else rb.plant(base, k["defect_type"])
        out.append(item)
    return out


def build(out: Path) -> dict:
    rng = random.Random(SEED)
    fresh, info = fresh_items(rng)
    ids = rng.sample(range(100, 1000), len(fresh))
    p1, p2, key = [], [], {}
    for item, n in zip(fresh, ids, strict=True):
        item_id = f"F-{n}"
        p1.append({"item_id": item_id, "kind": "legacy", **item["pass1"]})
        p2.append({"item_id": item_id, "kind": "legacy", **item["pass2"]})
        key[item_id] = {"defect_type": item["defect_type"], "expected_verdict": item["expected_verdict"],
                        "detectable_in": item["detectable_in"], "description": item["description"],
                        "source": "fresh_v1_inject", "structure_id": item["family"], "split": "requal",
                        "accepted_terms": LEGACY_ACCEPTED.get(item["defect_type"], []), "contested": None}
    v3_ids = set(json.loads((BANK_V3 / "key_RESTRICTED.json").read_text(encoding="utf-8")))
    deleted = condition_deleted_items()
    free = [n for n in range(100, 1000) if f"R-{n}" not in v3_ids and f"F-{n}" not in key]
    for item, n in zip(deleted, rng.sample(free, len(deleted)), strict=True):
        item["item_id"] = f"R-{n}"
    for item in heldout_role_items() + deleted:
        a, b = rb.packets(item, s178.SEED)
        p1.append({**a, "kind": "role"})
        p2.append({**b, "kind": "role"})
        key[item["item_id"]] = {"defect_type": item["defect_type"], "expected_verdict": item["expected_verdict"],
                                "detectable_in": item["detectable_in"], "description": item["description"],
                                "source": ("role_m0_condition_deleted" if item in deleted
                                           else "role_m0_heldout_v4_wording"), "structure_id": item["structure_id"],
                                "split": "requal", "accepted_terms": s178.ACCEPTED_TERMS.get(item["defect_type"], []),
                                "contested": None}
    for packet in p1 + p2:
        leaked = [f for f in s178.LEAK_FIELDS if f in packet]
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
    manifest = {"n_items": len(key), "by_type": dict(Counter(k["defect_type"] for k in key.values())),
                "expected": dict(Counter(k["expected_verdict"] for k in key.values())),
                "by_source": dict(Counter(k["source"] for k in key.values())), **info, "seed": SEED,
                "sha256": {n: hashlib.sha256(t.encode()).hexdigest() for n, t in files.items()}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="docs/validation/v2/llm_panel/bank_v4")
    args = parser.parse_args(argv)
    out = REPO_ROOT / args.out if not Path(args.out).is_absolute() else Path(args.out)
    if out.exists():
        print(f"Refusing to overwrite {out}", file=sys.stderr)
        return 2
    print(json.dumps(build(out), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
