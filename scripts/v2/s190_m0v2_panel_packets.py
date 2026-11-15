#!/usr/bin/env python3
"""G1: judge-panel packets for the committed M0 v2 dataset (admission standard sections 5 and 6).

Reads `data/v2/dataset/m0_v2/` (read-only) and the M0 v2 specs, and writes, deterministically and without overwriting:

* admission packets, one item per structure (`M0V2-<structure_id>`, 12 items): pass 1 (problem and role sentences under
  neutral ids in a seeded shuffled order) and pass 2 (the same plus the authors' claims, in the field style of
  `physmon.validation.rolevalue_bank.packets`), plus a key and a manifest, so that `s183_make_judge_kit.build` can make a
  GPT kit from the folder (split name "admission"; the s183 command line accepts only its three older split names, so the
  kit is made by calling `build()` directly, see the folder README text printed at the end);
* naturalness packets (admission standard 6.1), one per role sentence at the middle value: the problem with that one
  sentence inserted, and nothing about its role (`naturalness_prompt_v1.md` is the frozen instruction);
* batch directories on scratch for Claude judge instances and the two assignment files.

The restricted files (`key_RESTRICTED.json`, `naturalness_key_RESTRICTED.json`) hold roles and never go to a judge.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "v2"))

from physmon.benchmark.v2 import roles_m0v2  # noqa: E402
from physmon.benchmark.v2 import rolevalue as rv  # noqa: E402
from s178_build_judge_bank import LEAK_FIELDS  # noqa: E402

SEED = 190
MIDDLE = 1  # index of the middle study value (the value shown in the sentences)
ADMISSION_BATCH = 2
NATURALNESS_BATCH = 12
NATURALNESS_PER_STRUCTURE = 2
CELLS = "data/v2/dataset/m0_v2/cells.jsonl"
CERTIFICATES = "data/v2/dataset/m0_v2/certificates.json"
JUDGE_PROMPT = "docs/validation/v2/llm_panel/judge_prompt_v3.md"
NATURALNESS_PROMPT = "docs/validation/v2/llm_panel/naturalness_prompt_v1.md"
OUT_DIR = "docs/validation/v2/llm_panel/admission_m0v2"
SCRATCH = "/scratch/pabitra/physmon/judge"
INSTRUCTIONS = "Each sentence is added, on its own, to the end of the problem's description, before the question."
# keys that may legitimately appear below the top level of a packet although the name is on the leak list
NESTED_OK = {"description"}  # `inputs[].description`, the description of an input quantity
STRATA = ("R", "D", "N", "C", "K", "K_out")


def r6(x: float) -> float:
    return float(f"{x:.6g}")


def fmt(v: float) -> str:
    return rv._fmt(v)


def shown(value: float, unit: str) -> str:
    """A value with its unit as the sentences write it (bare for dimensionless, glued for degrees)."""

    if unit in rv.UNITLESS:
        return fmt(value)
    return fmt(value) + rv.GLUED_UNITS[unit] if unit in rv.GLUED_UNITS else f"{fmt(value)} {unit}"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def neutral_id(prefix: str, item_id: str, label: str, length: int) -> str:
    return prefix + hashlib.sha256(f"{SEED}:{item_id}:{label}".encode()).hexdigest()[:length].upper()


def load_cells(root: Path = REPO_ROOT) -> list[dict[str, Any]]:
    return [json.loads(x) for x in (root / CELLS).read_text(encoding="utf-8").splitlines() if x.strip()]


def leak_scan(packet: dict[str, Any]) -> list[str]:
    """Key-only field names in a packet: anywhere in the tree, except an input's own `description`."""

    found: list[str] = []

    def walk(node: Any, top: bool) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if k in LEAK_FIELDS and (top or k not in NESTED_OK):
                    found.append(k)
                walk(v, False)
        elif isinstance(node, list):
            for v in node:
                walk(v, False)

    walk(packet, True)
    return found


# --- items ---------------------------------------------------------------------------------------------------------------

def _pick(cells: list[dict[str, Any]], structure_id: str, stratum: str, phrasing: str | None, index: int | None) -> dict[str, Any]:
    hits = [c for c in cells if c["structure_id"] == structure_id and c["family"] == "role_by_value"
            and c["stratum"] == stratum and c["phrasing_id"] == phrasing and c["value_index"] == index
            and not c["heldout"]]
    if len(hits) != 1:
        raise SystemExit(f"expected one cell for {structure_id} {stratum} {phrasing} {index}, got {len(hits)}")
    return hits[0]


def _series(cells: list[dict[str, Any]], structure_id: str, stratum: str, phrasing: str) -> list[dict[str, Any]]:
    rows = [c for c in cells if c["structure_id"] == structure_id and c["family"] == "role_by_value"
            and c["stratum"] == stratum and c["phrasing_id"] == phrasing and not c["heldout"]]
    return sorted(rows, key=lambda c: c["value_index"])


def build_item(structure_id: str, cells: list[dict[str, Any]]) -> dict[str, Any]:
    """One structure: base problem, role sentences with their claims (internal labels), relations and inputs."""

    structure, spec = roles_m0v2.structure(structure_id), roles_m0v2.ROLE_SPECS[structure_id]
    base = next(c for c in cells if c["structure_id"] == structure_id and c["stratum"] == "none")
    base_answer = r6(base["gold_value"])
    sentences: list[dict[str, Any]] = []  # label, stratum, text, cell_id, claim
    for i, pair in enumerate(spec.pairs):
        for role in ("R", "D"):
            series = _series(cells, structure_id, role, f"{role.lower()}{i}")
            cell = _pick(cells, structure_id, role, f"{role.lower()}{i}", MIDDLE)
            claim: dict[str, Any] = {
                "stratum": role, "quantity": spec.quantity_phrase, "values": [fmt(c["value"]) for c in series],
                "value_shown": fmt(cell["value"]), "unit": spec.unit,
                "certified_answers": {fmt(c["value"]): r6(c["gold_value"]) for c in series}}
            if role == "R":
                claim["wiring"] = (f"q {spec.relevant.op} -> input {spec.relevant.input_name}: "
                                   f"{spec.relevant.rationale}")
            else:
                claim["invariance"] = "the answer does not depend on q (no causal path from q to the target)"
                claim["d_rationale"] = cell["d_rationale"]
                claim["minimal_pair_with"] = f"R{i}"
            if not pair.frame_matched:
                claim["pair_note"] = ("the R and D sentences of this pair do not share one frame (they carry the same "
                                      "number and unit); reason: " + pair.frame_mismatch_reason)
            sentences.append({"label": f"{role}{i}", "stratum": role, "gold_full": {fmt(c["value"]): c["gold_value"] for c in series}, "text": cell["sentence"], "cell_id": cell["cell_id"],
                              "claim": claim, "group": f"pair{i}"})
        n_cell = _pick(cells, structure_id, "N", f"d{i}", None)
        d_cell = _pick(cells, structure_id, "D", f"d{i}", MIDDLE)
        sentences.append({
            "label": f"N{i}", "stratum": "N", "gold_full": {"no number": n_cell["gold_value"]}, "text": n_cell["sentence"], "cell_id": n_cell["cell_id"], "group": f"pair{i}",
            "claim": {"stratum": "D", "numeral_free": True, "quantity": spec.quantity_phrase, "values": [], "value_shown": "no number",
                      "unit": None, "certified_answers": {"no number": r6(n_cell["gold_value"])},
                      "invariance": "the answer does not depend on the sentence (no causal path to the target)",
                      "d_rationale": n_cell["d_rationale"], "numeral_free_twin_of": f"D{i}",
                      "twin_note": "the same wording as its D twin with its number and unit replaced by a non-numeric phrase"}})
        assert d_cell["sentence"] != n_cell["sentence"]
    if spec.cancelling is not None:
        sub = spec.cancelling.spec
        for j, _ in enumerate(sub.phrasings):
            series = _series(cells, structure_id, "C", f"c{j}")
            cell = _pick(cells, structure_id, "C", f"c{j}", MIDDLE)
            sentences.append({
                "label": f"C{j}", "stratum": "C", "gold_full": {fmt(c["value"]): c["gold_value"] for c in series}, "text": cell["sentence"], "cell_id": cell["cell_id"], "group": "C",
                "claim": {"stratum": "C", "quantity": sub.quantity_phrase, "values": [fmt(c["value"]) for c in series],
                          "value_shown": fmt(cell["value"]), "unit": sub.unit,
                          "certified_answers": {fmt(c["value"]): r6(c["gold_value"]) for c in series},
                          "cancellation": {"relations": list(sub.intermediate_relations),
                                           "expression_with_q": sub.expr_with_q}}})
    if spec.conditional is not None:
        sub = spec.conditional.spec
        note = ("q in this expression is the value in SI base units and the other symbols are the problem's inputs "
                "and computed quantities in SI units")
        for j, _ in enumerate(sub.phrasings):
            series = _series(cells, structure_id, "K", f"k{j}")
            cell = _pick(cells, structure_id, "K", f"k{j}", MIDDLE)
            sentences.append({
                "label": f"K{j}", "stratum": "K", "gold_full": {fmt(c["value"]): c["gold_value"] for c in series}, "text": cell["sentence"], "cell_id": cell["cell_id"], "group": "K",
                "claim": {"stratum": "K", "quantity": sub.quantity_phrase, "values": [fmt(c["value"]) for c in series],
                          "value_shown": fmt(cell["value"]), "unit": sub.unit,
                          "certified_answers": {fmt(c["value"]): r6(c["gold_value"]) for c in series},
                          "regime": {"the_quantity_is_irrelevant_while": sub.predicate, "predicate_note": note,
                                     "every_listed_value_lies_inside_this_regime": True,
                                     "counter_regime": (f"the predicate is false, for example, at q = "
                                                        f"{shown(sub.counter_regime_value, sub.unit)}"),
                                     "for_reference_only_outside_the_regime": (
                                         "the physics would change (reference expression: %s); this is not part of the "
                                         "certified in-regime claim" % sub.out_of_regime_law)}}})
        if spec.conditional.k_out.feasible:
            for j, _ in enumerate(sub.phrasings):
                series = _series(cells, structure_id, "K_out", f"k{j}")
                cell = _pick(cells, structure_id, "K_out", f"k{j}", MIDDLE)
                sentences.append({
                    "label": f"KO{j}", "stratum": "K_out", "gold_full": {fmt(c["value"]): c["gold_value"] for c in series}, "text": cell["sentence"], "cell_id": cell["cell_id"],
                    "group": "KO",
                    "claim": {"stratum": "R", "outside_regime_of": f"K{j}", "quantity": sub.quantity_phrase,
                              "values": [fmt(c["value"]) for c in series], "value_shown": fmt(cell["value"]),
                              "unit": sub.unit,
                              "certified_answers": {fmt(c["value"]): r6(c["gold_value"]) for c in series},
                              "regime_note": ("the stated value lies outside the regime in which this quantity is irrelevant, so "
                                              "the answer changes as certified here; the sentence outside_regime_of "
                                              "is the same quantity inside the regime"),
                              "regime": {"the_quantity_is_irrelevant_only_while": sub.predicate, "predicate_note": note,
                                         "every_listed_value_lies_outside_this_regime": True,
                                         "out_of_regime_law": sub.out_of_regime_law,
                                         "why_the_question_stays_well_posed": spec.conditional.k_out.reason}}})
    return {"item_id": f"M0V2-{structure_id}", "structure_id": structure_id, "problem": base["prompt"],
            "sentences": sentences, "target_unit": structure.render.target_unit, "base_answer": base_answer,
            "relations": [f"{n.name} = {n.expr}" for n in structure.computed],
            "assumptions": [a.text for a in structure.assumptions],
            "inputs": [{"name": n.name, "unit": n.unit, "description": n.description} for n in structure.inputs]}


def build_items(cells: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    cells = load_cells() if cells is None else cells
    return [build_item(sid, cells) for sid in sorted(roles_m0v2.ROLE_SPECS)]


# --- admission packets -----------------------------------------------------------------------------------------------------

def sentence_ids(item: dict[str, Any]) -> dict[str, str]:
    for length in (4, 5, 6):
        ids = {s["label"]: neutral_id("T", item["item_id"], s["label"], length) for s in item["sentences"]}
        if len(set(ids.values())) == len(ids):
            return ids
    raise SystemExit("sentence id collision in " + item["item_id"])


def admission_packets(item: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    rng = random.Random(f"{SEED}:{item['item_id']}")
    order = sorted(item["sentences"], key=lambda s: s["label"])
    rng.shuffle(order)
    ids = sentence_ids(item)
    pass1 = {"item_id": item["item_id"], "kind": "role", "problem": item["problem"],
             "sentences": [{"sentence_id": ids[s["label"]], "text": s["text"]} for s in order],
             "instructions": INSTRUCTIONS}
    claims = []
    for s in item["sentences"]:
        claim = dict(s["claim"])
        claim["sentence_id"] = ids[s["label"]]
        for key in ("minimal_pair_with", "numeral_free_twin_of", "outside_regime_of"):
            if key in claim:
                claim[key] = ids[claim[key]]
        claims.append(claim)
    claims.sort(key=lambda c: c["sentence_id"])
    pass2 = {**pass1, "authors_claims": claims, "target_unit": item["target_unit"], "base_answer": item["base_answer"],
             "relations": item["relations"], "assumptions": item["assumptions"], "inputs": item["inputs"]}
    for packet in (pass1, pass2):
        leaked = leak_scan(packet)
        if leaked:
            raise SystemExit(f"key field(s) {leaked} in packet {packet['item_id']}")
    return pass1, pass2, ids


# --- naturalness packets ---------------------------------------------------------------------------------------------------

def naturalness_packets(items: list[dict[str, Any]], cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One record per role sentence: `packet` (judge-facing) and `key` (restricted)."""

    by_cell = {c["cell_id"] + "|" + c["structure_id"]: c for c in cells}
    records = []
    for item in items:
        for s in item["sentences"]:
            cell = by_cell[s["cell_id"] + "|" + item["structure_id"]]
            nat_id = neutral_id("NAT-", item["item_id"], "nat:" + s["label"], 8)
            packet = {"item_id": nat_id, "problem": cell["prompt"], "inserted_sentence": s["text"]}
            assert s["text"] in cell["prompt"]
            leaked = leak_scan(packet)
            if leaked:
                raise SystemExit(f"key field(s) {leaked} in packet {nat_id}")
            records.append({"packet": packet,
                            "key": {"item_id": nat_id, "structure_id": item["structure_id"], "label": s["label"],
                                    "stratum": s["stratum"], "cell_id": s["cell_id"], "group": s["group"]}})
    ids = [r["packet"]["item_id"] for r in records]
    if len(set(ids)) != len(ids):
        raise SystemExit("naturalness id collision")
    return sorted(records, key=lambda r: r["packet"]["item_id"])


# --- batches -----------------------------------------------------------------------------------------------------------------

def admission_batches(item_ids: list[str]) -> list[list[str]]:
    order = sorted(item_ids)
    random.Random(f"{SEED}:admission").shuffle(order)
    return [order[i:i + ADMISSION_BATCH] for i in range(0, len(order), ADMISSION_BATCH)]


def naturalness_batches(keys: list[dict[str, Any]]) -> list[list[str]]:
    """Greedy first fit over a seeded shuffle: at most 12 sentences per batch, at most 2 of any structure, and never two
    sentences of the same quantity in one structure (so never an R, its D twin and its N twin together, nor two phrasings
    of one C or K quantity)."""

    order = sorted(keys, key=lambda k: k["item_id"])
    random.Random(f"{SEED}:naturalness").shuffle(order)
    batches: list[list[dict[str, Any]]] = []
    for k in order:
        for batch in batches:
            same = [b for b in batch if b["structure_id"] == k["structure_id"]]
            if (len(batch) < NATURALNESS_BATCH and len(same) < NATURALNESS_PER_STRUCTURE
                    and all(b["group"] != k["group"] for b in same)):
                batch.append(k)
                break
        else:
            batches.append([k])
    return [[k["item_id"] for k in b] for b in batches]


# --- writing -------------------------------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=OUT_DIR)
    parser.add_argument("--scratch", default=SCRATCH)
    args = parser.parse_args(argv)
    out = Path(args.out) if Path(args.out).is_absolute() else REPO_ROOT / args.out
    scratch = Path(args.scratch)
    admission_root, natural_root = scratch / "m0v2_admission", scratch / "m0v2_naturalness"
    for p in (out, admission_root, natural_root):
        if p.exists():
            print(f"Refusing to overwrite {p}", file=sys.stderr)
            return 2
    prompt_path = REPO_ROOT / NATURALNESS_PROMPT
    if not prompt_path.exists():
        print(f"Missing frozen prompt {NATURALNESS_PROMPT}", file=sys.stderr)
        return 2

    cells = load_cells()
    items = build_items(cells)
    adm = {}
    for item in items:
        p1, p2, ids = admission_packets(item)
        adm[item["item_id"]] = (p1, p2, ids, item)
    item_order = sorted(adm, key=lambda i: sha256_text(f"{SEED}:{i}"))
    nat = naturalness_packets(items, cells)
    nat_by_id = {r["packet"]["item_id"]: r for r in nat}
    a_batches = admission_batches(list(adm))
    n_batches = naturalness_batches([r["key"] for r in nat])

    out.mkdir(parents=True)
    files = {
        "pass1_packets.jsonl": "".join(dumps(adm[i][0]) + "\n" for i in item_order),
        "pass2_packets.jsonl": "".join(dumps(adm[i][1]) + "\n" for i in item_order),
        "naturalness_packets.jsonl": "".join(dumps(r["packet"]) + "\n" for r in nat)}
    key = {i: {"split": "admission", "expected_verdict": "valid", "defect_type": "valid",
               "structure_id": adm[i][3]["structure_id"],
               "sentence_strata": {adm[i][2][s["label"]]: s["stratum"] for s in adm[i][3]["sentences"]},
               "sentence_labels": {adm[i][2][s["label"]]: s["label"] for s in adm[i][3]["sentences"]},
               "full_precision_golds": {adm[i][2][s["label"]]: s["gold_full"] for s in adm[i][3]["sentences"]}}
           for i in adm}
    files["key_RESTRICTED.json"] = json.dumps(key, indent=2, sort_keys=True) + "\n"
    files["naturalness_key_RESTRICTED.json"] = json.dumps({r["key"]["item_id"]: r["key"] for r in nat}, indent=2,
                                                          sort_keys=True) + "\n"
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")

    def assignment(run_id: str, batches: list[list[str]], root: Path, prompt: str) -> dict[str, Any]:
        return {"run_id": run_id, "seed": SEED, "prompt": prompt, "prompt_sha256": sha256_file(REPO_ROOT / prompt),
                "batches": [{"batch": f"batch{n:02d}", "dir": str(root / f"batch{n:02d}"), "items": b,
                             "reviewer_id": f"claude-opus-5-5:{run_id}:batch{n:02d}"}
                            for n, b in enumerate(batches, 1)]}

    a_assign = assignment("m0v2_admission", a_batches, admission_root, JUDGE_PROMPT)
    n_assign = assignment("m0v2_naturalness", n_batches, natural_root, NATURALNESS_PROMPT)
    (out / "assignment_admission.json").write_text(json.dumps(a_assign, indent=2) + "\n", encoding="utf-8")
    (out / "assignment_naturalness.json").write_text(json.dumps(n_assign, indent=2) + "\n", encoding="utf-8")

    for n, batch in enumerate(a_batches, 1):
        d = admission_root / f"batch{n:02d}"
        (d / "out").mkdir(parents=True)
        for i in batch:
            (d / f"{i}_pass1_packet.json").write_text(json.dumps(adm[i][0], indent=2, ensure_ascii=False), encoding="utf-8")
            (d / f"{i}_pass2_packet.json").write_text(json.dumps(adm[i][1], indent=2, ensure_ascii=False), encoding="utf-8")
    for n, batch in enumerate(n_batches, 1):
        d = natural_root / f"batch{n:02d}"
        (d / "out").mkdir(parents=True)
        for i in batch:
            (d / f"{i}_packet.json").write_text(json.dumps(nat_by_id[i]["packet"], indent=2, ensure_ascii=False),
                                                encoding="utf-8")

    manifest = {"seed": SEED, "n_admission_items": len(adm), "n_naturalness_sentences": len(nat),
                "n_admission_batches": len(a_batches), "n_naturalness_batches": len(n_batches),
                "naturalness_batch_sizes": [len(b) for b in n_batches],
                "sentences_per_stratum": {s: sum(1 for r in nat if r["key"]["stratum"] == s) for s in STRATA},
                "inputs": {CELLS: sha256_file(REPO_ROOT / CELLS), CERTIFICATES: sha256_file(REPO_ROOT / CERTIFICATES),
                           JUDGE_PROMPT: sha256_file(REPO_ROOT / JUDGE_PROMPT),
                           NATURALNESS_PROMPT: sha256_file(prompt_path)},
                "outputs": {name: sha256_text(text) for name, text in sorted(files.items())},
                "split": "admission", "claim_answer_rounding": "6 significant figures (as in the role bank)"}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in manifest if k.startswith("n_") or k.endswith("sizes")}, indent=2))
    print("GPT kit (after `codex login`; s183's command line does not accept the split name 'admission'):\n"
          "  python -c \"import sys; sys.path.insert(0,'scripts/v2'); from pathlib import Path; "
          "import s183_make_judge_kit as k; k.build(Path('<kit dir>'), Path('%s'), 'admission', "
          "Path('%s'), 'gpt-6.1-sol', 'gpt_m0v2_admission')\"" % (OUT_DIR, JUDGE_PROMPT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
