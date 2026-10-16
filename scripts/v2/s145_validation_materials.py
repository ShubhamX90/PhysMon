#!/usr/bin/env python3
"""Stage 14.5: validator-qualification materials (agent-built candidates; human review required).

Builds, from committed data only (CPU):
  1. a stratified genuine pilot sample of DECOY-v1 families chosen by the criteria in v2 B4.1 (p.9): cue types and
     domains, the largest gold-likelihood shifts, base-lowest ("negative score") families, presumed-easy stable
     families, assumption-sensitive isolation families, and the largest structure clusters from Stage 14.4;
  2. a planted-defect bank (v2 B4.4, p.10): each predeclared defect type applied to disjoint base families, plus a
     valid equivalent rewrite as the positive control;
  3. blinded Pass 1 packets (prompts only) and Pass 2 packets (with the encoded equation, parameters, certified
     answer and the authors' proof text), with items shuffled so planted and genuine items are indistinguishable;
  4. the restricted answer key, the physicist-confirmation file for the bank, and a 20-family timing pilot.

Nothing here is a validation. The agent that built the materials cannot be the validator (v2 §9, p.43). The selection
uses model outcomes for some strata (as B4.1 asks); reviewers must never be shown them.

Plan reference: B4.1-B4.5 (p.9-10), P3.1-P3.3 (p.20), §9 human workload (p.43), first sprint item 5 (p.48).
"""

from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import random
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.validation import defect_injection as di  # noqa: E402

OUT_BASE = "docs/validation/v2/materials"
SEED = 42
PER_DEFECT = 3
N_CONTROLS = 6
N_GENUINE = 40
N_TIMING = 20

INPUTS = {
    "rendered": "results/stage6/generated_full_benchmark",
    "templates": "data/raw/templates",
    "clusters": "results/stage14/s144_structure_overlap/attempt_20261016_d637b0e/clusters.csv",
    "x02": "results/stage14/x02_base_rotation/attempt_20261016_2b59e31/base_permutation_audit.csv",
    "per_family": "results/stage6/analysis_d2/stage6_d1_per_family.csv",
}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True,
                          check=False).stdout.strip()


def load_families() -> dict[str, dict]:
    out = {}
    for path in sorted(glob.glob(str(REPO_ROOT / INPUTS["rendered"] / "*.json"))):
        if path.endswith("assembly_summary.json"):
            continue
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        out[data["template_id"]] = data
    return out


def load_templates() -> dict[str, dict]:
    out = {}
    for path in sorted(glob.glob(str(REPO_ROOT / INPUTS["templates"] / "*.yaml"))):
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        out[data["template_id"]] = data
    return out


def read_csv(rel: str) -> list[dict]:
    with (REPO_ROOT / rel).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def variant0_prompt(family: dict) -> str:
    return str(min(family["variants"], key=lambda v: int(v["variant_id"]))["prompt"])


# ---------------------------------------------------------------------------------------------
# Planted bank
# ---------------------------------------------------------------------------------------------


def build_bank(families, templates, rng: random.Random, reserved: set[str]) -> tuple[list[dict], dict[str, Any]]:
    census = {dt: [fid for fid, fam in sorted(families.items())
                   if di.inject(dt, fam, templates.get(fid)).applicable] for dt in di.DEFECT_TYPES}
    used: set[str] = set(reserved)  # families reserved for the genuine sample are never planted
    bank: list[dict] = []
    shortfalls: dict[str, int] = {}
    order = sorted(di.DEFECT_TYPES, key=lambda dt: (len(census[dt]), dt))  # scarcest first
    for defect_type in order:
        want = N_CONTROLS if defect_type == di.CONTROL else PER_DEFECT
        pool = [f for f in census[defect_type] if f not in used]
        rng.shuffle(pool)
        domains_taken: dict[str, int] = {}
        picked: list[str] = []
        while pool and len(picked) < want:
            pool.sort(key=lambda f: domains_taken.get(families[f]["domain"], 0))
            fid = pool.pop(0)
            domains_taken[families[fid]["domain"]] = domains_taken.get(families[fid]["domain"], 0) + 1
            picked.append(fid)
            used.add(fid)
        if len(picked) < want:
            shortfalls[defect_type] = want - len(picked)
        for fid in sorted(picked):
            injection = di.inject(defect_type, families[fid], templates.get(fid))
            bank.append({"family": fid, "defect_type": defect_type, "injection": injection})
    return bank, {"census": {k: len(v) for k, v in census.items()}, "shortfalls": shortfalls}


# ---------------------------------------------------------------------------------------------
# Genuine pilot sample
# ---------------------------------------------------------------------------------------------


def build_sample(families, excluded: set[str], rng: random.Random, reserved: set[str]) -> list[dict]:
    clusters = {r["family"]: r for r in read_csv(INPUTS["clusters"])}
    x02 = {}
    for r in read_csv(INPUTS["x02"]):
        if r["status"] == "EVALUATED":
            x02.setdefault(r["template_id"], {})[r["model"]] = r
    meta = {r["template_id"]: r for r in read_csv(INPUTS["per_family"])}
    candidates = [f for f in sorted(families) if f not in excluded]
    chosen: dict[str, str] = {}

    def take(stratum: str, ordered: list[str], n: int) -> None:
        for fid in ordered:
            if len([s for s in chosen.values() if s == stratum]) >= n:
                break
            if fid in candidates and fid not in chosen:
                chosen[fid] = stratum

    def mean_range(fid: str) -> float:
        rows = x02.get(fid, {}).values()
        values = [float(r["range"]) for r in rows]
        return sum(values) / len(values) if values else -1.0

    def min_base_score(fid: str) -> float:
        rows = x02.get(fid, {}).values()
        values = [float(r["S_plan_b0"]) for r in rows]
        return min(values) if values else 1e9

    # 1. largest structure clusters (Stage 14.4): two families from each of the two largest
    sizes = sorted({(int(r["cluster_size"]), r["cluster_id"]) for r in clusters.values()}, reverse=True)[:2]
    for _, cluster_id in sizes:
        members = [f for f in candidates if clusters.get(f, {}).get("cluster_id") == cluster_id]
        rng.shuffle(members)
        for fid in members[:2]:
            chosen.setdefault(fid, "high_overlap_cluster")
    # 2. largest gold-likelihood shifts
    take("largest_gold_shift", sorted(candidates, key=lambda f: (-mean_range(f), f)), 6)
    # 3. base-lowest ("negative score"): the plan-signed score at base 0 is negative for some model
    take("negative_base_score", sorted(candidates, key=lambda f: (min_base_score(f), f)), 4)
    # 4. presumed easy stable: range < 0.5 nat for both models
    easy = [f for f in candidates if x02.get(f) and all(float(r["range"]) < 0.5 for r in x02[f].values())]
    rng.shuffle(easy)
    take("presumed_easy_stable", easy, 6)
    # 5. assumption-sensitive isolation (proxy for ambiguous coupled systems)
    iso = [f for f in candidates if "isolated" in variant0_prompt(families[f])
           and families[f]["domain"] in ("thermodynamics", "electrostatics_circuits")]
    rng.shuffle(iso)
    take("assumption_sensitive_isolation", iso, 6)
    # 6. frame/unit rendering (Cue C): the families reserved before the bank was built
    for fid in sorted(reserved):
        chosen.setdefault(fid, "cue_c_frame_rendering")
    # 7. coverage of every (cue type, domain) cell, then random fill
    cells = {(families[f]["cue_type"], families[f]["domain"]) for f in candidates}
    covered = {(families[f]["cue_type"], families[f]["domain"]) for f in chosen}
    for cell in sorted(cells - covered):
        pool = [f for f in candidates if (families[f]["cue_type"], families[f]["domain"]) == cell and f not in chosen]
        rng.shuffle(pool)
        if pool:
            chosen[pool[0]] = "cell_coverage"
    rest = [f for f in candidates if f not in chosen]
    rng.shuffle(rest)
    for fid in rest:
        if len(chosen) >= N_GENUINE:
            break
        chosen[fid] = "random_fill"
    sample = []
    for fid, stratum in sorted(chosen.items()):
        sample.append({"family": fid, "stratum": stratum, "cue_type": families[fid]["cue_type"],
                       "domain": families[fid]["domain"], "governing_law": meta[fid]["governing_law"],
                       "cluster_id": clusters[fid]["cluster_id"], "cluster_size": int(clusters[fid]["cluster_size"]),
                       "selection_used_model_outcomes": stratum in (
                           "largest_gold_shift", "negative_base_score", "presumed_easy_stable")})
    return sample[:N_GENUINE] if len(sample) > N_GENUINE else sample


# ---------------------------------------------------------------------------------------------
# Packets
# ---------------------------------------------------------------------------------------------


def parameter_table(template: dict) -> list[dict]:
    return [{"symbol": k, "value": v.get("value"), "units": v.get("units"), "description": v.get("description")}
            for k, v in template["parameters"].items()]


def author_proof(template: dict) -> str:
    slot = template.get("cue_slot", {})
    return str(slot.get("irrelevance_proof") or slot.get("nongoverning_proof") or "")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="v1")
    parser.add_argument("--out-base", default=OUT_BASE)
    args = parser.parse_args()
    out_dir = (REPO_ROOT / args.out_base / args.version).resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"Refusing to reuse non-empty materials directory: {out_dir}", file=sys.stderr)
        return 2

    families, templates = load_families(), load_templates()
    rng = random.Random(SEED)
    cue_c = sorted(f for f, fam in families.items() if fam["cue_type"] == "frame_rendering")
    reserved = set(rng.sample(cue_c, 2))  # Cue C is scarce (5 families); keep two genuine, plant the rest
    bank, bank_info = build_bank(families, templates, rng, reserved)
    planted_families = {b["family"] for b in bank}
    sample = build_sample(families, planted_families, rng, reserved)

    items: list[dict] = []
    for row in sample:
        fid = row["family"]
        items.append({"kind": "genuine", "family": fid, "defect_type": None, "stratum": row["stratum"],
                      "prompts": [v["prompt"] for v in sorted(families[fid]["variants"], key=lambda v: int(v["variant_id"]))],
                      "equation_sympy": templates[fid]["governing_equation_sympy"],
                      "answer_display": families[fid]["correct_answer"], "meta": row, "injection": None})
    for entry in bank:
        fid, inj = entry["family"], entry["injection"]
        items.append({"kind": "planted", "family": fid, "defect_type": entry["defect_type"], "stratum": "planted",
                      "prompts": inj.edited_prompts,
                      "equation_sympy": inj.edited_equation or templates[fid]["governing_equation_sympy"],
                      "answer_display": inj.edited_answer or families[fid]["correct_answer"],
                      "meta": {"cue_type": families[fid]["cue_type"], "domain": families[fid]["domain"]},
                      "injection": inj})
    order = list(range(len(items)))
    random.Random(SEED + 1).shuffle(order)
    for new_index, old_index in enumerate(order, start=1):
        items[old_index]["item_id"] = f"Q{new_index:03d}"
    items.sort(key=lambda it: it["item_id"])

    pass1, pass2, key, bank_rows = [], [], {}, []
    for item in items:
        fid = item["family"]
        template = templates[fid]
        pass1.append({"item_id": item["item_id"], "variants": item["prompts"]})
        pass2.append({
            "item_id": item["item_id"], "variants": item["prompts"],
            "governing_equation_latex": template["governing_equation_latex"],
            "governing_equation_sympy": item["equation_sympy"],
            "parameters": parameter_table(template),
            "target_quantity": template["target_quantity"], "target_units": template["target_units"],
            "certified_answer_display": item["answer_display"],
            "authors_proof_text": author_proof(template),
        })
        inj = item["injection"]
        key[item["item_id"]] = {
            "family": fid, "kind": item["kind"], "stratum": item["stratum"],
            "defect_type": item["defect_type"] or "genuine_v1_family",
            "expected_verdict": inj.expected_verdict if inj else "not_applicable_genuine_family",
            "detectable_in": inj.detectable_in if inj else "not_applicable_genuine_family",
            "description": inj.description if inj else "",
        }
        if inj:
            original = families[fid]
            bank_rows.append({
                "item_id": item["item_id"], "family": fid, "defect_type": item["defect_type"],
                "expected_verdict": inj.expected_verdict, "detectable_in": inj.detectable_in,
                "description": inj.description,
                "original_variant0_prompt": variant0_prompt(original),
                "edited_variant0_prompt": inj.edited_prompts[0],
                "original_equation": template["governing_equation_sympy"],
                "edited_equation": inj.edited_equation,
                "original_answer": original["correct_answer"], "edited_answer": inj.edited_answer,
                "physicist_confirmation": {"is_defective_for_declared_reason": None,
                                           "is_control_actually_valid": None, "confirmed_by": None, "notes": ""},
            })

    genuine_items = [it for it in items if it["kind"] == "genuine"]
    timing_order: list[str] = []
    by_stratum: dict[str, list[str]] = {}
    for it in genuine_items:
        by_stratum.setdefault(it["stratum"], []).append(it["item_id"])
    while len(timing_order) < N_TIMING and any(by_stratum.values()):
        for stratum in sorted(by_stratum):
            if by_stratum[stratum] and len(timing_order) < N_TIMING:
                timing_order.append(by_stratum[stratum].pop(0))

    out_dir.mkdir(parents=True, exist_ok=True)

    def write_jsonl(name: str, rows: list[dict]) -> None:
        (out_dir / name).write_text("".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows),
                                    encoding="utf-8")

    write_jsonl("pass1_packets.jsonl", pass1)
    write_jsonl("pass2_packets.jsonl", pass2)
    write_jsonl("planted_defect_bank_FOR_PHYSICIST_CONFIRMATION.jsonl", bank_rows)
    (out_dir / "packet_key_RESTRICTED.json").write_text(json.dumps(key, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (out_dir / "genuine_pilot_sample.csv").open("w", newline="", encoding="utf-8") as handle:
        columns = ["item_id", "family", "stratum", "cue_type", "domain", "governing_law", "cluster_id", "cluster_size",
                   "selection_used_model_outcomes", "in_timing_pilot_20"]
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for it in genuine_items:
            writer.writerow({"item_id": it["item_id"], **{k: it["meta"][k] for k in columns[1:-1] if k != "family"},
                             "family": it["family"], "in_timing_pilot_20": int(it["item_id"] in timing_order)})
    strata_counts: dict[str, int] = {}
    for it in genuine_items:
        strata_counts[it["stratum"]] = strata_counts.get(it["stratum"], 0) + 1
    defect_counts: dict[str, int] = {}
    for entry in bank:
        defect_counts[entry["defect_type"]] = defect_counts.get(entry["defect_type"], 0) + 1
    summary = {
        "stage": "14.5", "materials_version": args.version, "seed": SEED, "source_commit": git("rev-parse", "HEAD"),
        "git_status_short": git("status", "--short").splitlines(),
        "command": " ".join(sys.argv),
        "status": "CANDIDATE: requires physicist confirmation of the bank and independent reviewers; the agent is not a validator",
        "n_items": len(items), "n_genuine": len(genuine_items), "n_planted": len(bank),
        "genuine_by_stratum": dict(sorted(strata_counts.items())),
        "planted_by_defect_type": dict(sorted(defect_counts.items())),
        "bank_applicability_census": bank_info["census"], "bank_shortfalls": bank_info["shortfalls"],
        "families_disjoint_between_planted_and_genuine": not (planted_families & {it["family"] for it in genuine_items}),
        "timing_pilot_item_ids": timing_order,
        "inputs": {k: v for k, v in INPUTS.items()},
        "file_sha256": {p.name: sha(p.read_text(encoding="utf-8")) for p in sorted(out_dir.iterdir()) if p.is_file()},
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "README.md").write_text(_readme(summary), encoding="utf-8")
    print(json.dumps({"out_dir": str(out_dir.relative_to(REPO_ROOT)) if out_dir.is_relative_to(REPO_ROOT) else str(out_dir),
                      "n_items": len(items), "n_planted": len(bank), "n_genuine": len(genuine_items),
                      "genuine_by_stratum": summary["genuine_by_stratum"],
                      "planted_by_defect_type": summary["planted_by_defect_type"],
                      "shortfalls": bank_info["shortfalls"]}, indent=2))
    return 0


def _readme(summary: dict) -> str:
    return f"""# Validator qualification materials {summary['materials_version']} (Stage 14.5)

Status: **candidate materials built by an agent.** Nothing here is a validation. A physicist must confirm the planted
bank (`planted_defect_bank_FOR_PHYSICIST_CONFIRMATION.jsonl`) before use, and independent reviewers must do the
reviews. Plan reference: v2 B4 (p.9-10), P3.1-P3.3 (p.20).

## What to give reviewers

- Pass 1: `pass1_packets.jsonl` only. Reviewers must not see the equation, answers, model outputs, sensitivity labels,
  probe scores, or the research hypothesis.
- Pass 2: `pass2_packets.jsonl`, after Pass 1 is complete and locked.
- Review records follow the contract in `src/physmon/governance/review.py` (see the v2 handbook).

## What to keep from reviewers

`packet_key_RESTRICTED.json` (which items are planted and why), `planted_defect_bank_FOR_PHYSICIST_CONFIRMATION.jsonl`,
`genuine_pilot_sample.csv` (its strata use model outcomes) and `summary.json`. The key is committed here for
provenance; if this repository is visible to reviewers, move the restricted files out of the copy you share.

## Contents

- {summary['n_items']} items: {summary['n_genuine']} genuine DECOY-v1 families and {summary['n_planted']} planted items,
  shuffled so they cannot be told apart. Base families of planted items are disjoint from the genuine sample.
- Planted types: {', '.join(f'{k} ({v})' for k, v in summary['planted_by_defect_type'].items())}.
- Genuine strata: {', '.join(f'{k} ({v})' for k, v in summary['genuine_by_stratum'].items())}.
- A 20-family timing pilot (`in_timing_pilot_20` in the sample file) measures adjudication time before the full audit
  is budgeted (v2 p.43).
"""


if __name__ == "__main__":
    raise SystemExit(main())
