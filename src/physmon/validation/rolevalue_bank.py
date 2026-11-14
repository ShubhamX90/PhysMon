"""Judge-qualification items for role-by-value structures (Stage 15, G1 "LLM review panel": extend the planted-defect bank
with fresh valid items and new planted defects, with a held-out portion; plan of record sec:llmpanel and B4.4).

Each item is built from a certified M0 role spec on one instance (instance 0 unless stated) and shown to a judge in two passes:
* Pass 1 (blind): the base problem and every role sentence (R, D and, where present, C and K, both phrasings, at the
  middle study value), in a shuffled order under neutral ids. The judge solves the problem, assigns each sentence's
  stratum, states the answer when the sentence is added, and flags defects.
* Pass 2: adds the authors' claims for each sentence (stratum, certified answers at every value, wiring or relations,
  regime), the governing relations, assumptions and the claimed target unit.

Valid items are the unmodified M0 specs. Planted defects (one declared type each; all detectable in pass 2, where the
claims appear):
* hidden_coupling: one D phrasing is replaced by a relation that couples the quantity, while the claim says D.
* failed_transformation_identity: the claimed R answers use the wrong operation (subtract for add, etc.).
* relevant_variable_removed_from_equation: the claimed R answers ignore the quantity (all equal the base answer).
* invalid_parameter_domain: the K values are moved outside the regime while the claim says K (irrelevant).
* inconsistent_units: the claimed target unit is replaced by a unit of another dimension (values unchanged).
* rendering_not_minimal: a D sentence carries a different numeral from its R twin while the claim says they
  form a minimal pair at the same value.
"""

from __future__ import annotations

import dataclasses
import hashlib
import random
from typing import Any

from physmon.benchmark.v2 import design as dg
from physmon.benchmark.v2 import dimensions as dm
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import roles_m0

ROLE_DEFECT_TYPES = ("hidden_coupling", "failed_transformation_identity", "relevant_variable_removed_from_equation",
                     "invalid_parameter_domain", "inconsistent_units", "rendering_not_minimal")
# Every role defect is a mismatch between a sentence and the authors' claim, and claims appear only in pass 2, so all
# are pass-2 detectable; pass-1 stratum assignments are scored separately as blind stratum agreement.
DETECTABLE_IN = {t: "pass2" for t in ("hidden_coupling", "failed_transformation_identity",
                                      "relevant_variable_removed_from_equation", "invalid_parameter_domain",
                                      "inconsistent_units", "rendering_not_minimal", "valid")}
FLIP_OP = {"add": "subtract", "subtract": "add", "scale": "add", "replace": "add"}
WRONG_UNIT = {"m/s^2": "m/s", "m/s": "m", "s": "Hz", "Pa": "N", "kPa": "N", "N": "Pa", "V": "A", "W": "J", "cm": "s",
              "deg": "rad/s", "pm": "eV", "nm": "eV", "m": "s", "J": "W", "K": "J"}
DISPLAY_INDEX = 1  # the middle study value is shown in the role sentences


def _sid(item_id: str, label: str) -> str:
    return "T" + hashlib.sha256(f"{item_id}:{label}".encode()).hexdigest()[:4].upper()


def _r_answers(structure, spec: rv.RoleSpec, op: str | None = None, instance: int = 0) -> dict[str, float]:
    si = rv.display_inputs_si(structure, instance)
    wiring = spec.relevant if op is None else dataclasses.replace(spec.relevant, op=op)
    use = dataclasses.replace(spec, relevant=wiring)
    return {rv._fmt(v): float(f"{rv.gold_r(structure, si, use, v)[0]:.6g}") for v in spec.values}


def base_item(structure_id: str, item_id: str, instance: int = 0) -> dict[str, Any]:
    """An unmodified (valid) item: pass-1 packet, pass-2 packet and the internal key. `instance` selects the certified
    instance of the structure (every role spec is certified on every instance); banks v3 and v4 use instance 0."""

    structure, spec = roles_m0.structure(structure_id), roles_m0.ROLE_SPECS[structure_id]
    problem = rv._assemble(structure, instance, "", "after_context")
    y_d = float(f"{dg.gold_for(structure, dict(structure.instances[instance])):.6g}")
    z = spec.values[DISPLAY_INDEX]
    sentences, claims = [], []
    for role, phrasings in (("R", spec.phrasings_r), ("D", spec.phrasings_d)):
        for i, p in enumerate(phrasings):
            label = f"{role}{i}"
            sentences.append({"label": label, "text": rv._sentence(spec.frame, z, spec.unit, p.relation, "")})
            claim: dict[str, Any] = {"label": label, "stratum": role, "quantity": spec.quantity_phrase,
                                     "values": [rv._fmt(v) for v in spec.values], "value_shown": rv._fmt(z),
                                     "unit": spec.unit}
            if role == "R":
                claim["certified_answers"] = _r_answers(structure, spec, instance=instance)
                claim["wiring"] = f"q {spec.relevant.op} -> input {spec.relevant.input_name}: {spec.relevant.rationale}"
            else:
                claim["certified_answers"] = {rv._fmt(v): y_d for v in spec.values}
                claim["invariance"] = "the answer does not depend on q (no causal path from q to the target)"
                claim["minimal_pair_with"] = f"R{i}"
            claims.append(claim)
    for role, sub in (("C", spec.cancelling), ("K", spec.conditional)):
        if sub is None:
            continue
        for i, p in enumerate(sub.phrasings):
            label = f"{role}{i}"
            value = sub.values[DISPLAY_INDEX]
            sentences.append({"label": label, "text": rv._sentence(sub.frame, value, sub.unit, p.relation, "")})
            claim = {"label": label, "stratum": role, "quantity": sub.quantity_phrase,
                     "values": [rv._fmt(v) for v in sub.values], "value_shown": rv._fmt(value), "unit": sub.unit,
                     "certified_answers": {rv._fmt(v): y_d for v in sub.values}}
            if role == "C":
                claim["cancellation"] = {"relations": list(sub.intermediate_relations),
                                         "expression_with_q": sub.expr_with_q}
            else:
                # bank v4 wording (after the GPT judge's objections in gpt_q1): only the in-regime answer is certified;
                # the out-of-regime expression is context, and no listed value is at or beyond the boundary
                claim["regime"] = {"the_quantity_is_irrelevant_while": sub.predicate,
                                   "every_listed_value_lies_inside_this_regime": True,
                                   "for_reference_only_outside_the_regime": (
                                       "the physics would change (reference expression: %s); this is not part of the "
                                       "certified claim" % sub.out_of_regime_law)}
            claims.append(claim)
    relations = [f"{n.name} = {n.expr}" for n in structure.computed]
    item = {"item_id": item_id, "structure_id": structure_id, "problem": problem, "sentences": sentences,
            "claims": claims, "target_unit": structure.render.target_unit, "base_answer": y_d,
            "relations": relations, "assumptions": [a.text for a in structure.assumptions],
            "inputs": [{"name": n.name, "unit": n.unit, "description": n.description} for n in structure.inputs],
            "defect_type": "valid", "expected_verdict": "valid", "detectable_in": DETECTABLE_IN["valid"],
            "description": "unmodified certified M0 item", "instance": instance}
    return item


def plant(item: dict[str, Any], defect_type: str) -> dict[str, Any]:
    """Apply one declared defect to a valid item (returns a new item)."""

    structure, spec = roles_m0.structure(item["structure_id"]), roles_m0.ROLE_SPECS[item["structure_id"]]
    out = {**item, "sentences": [dict(s) for s in item["sentences"]], "claims": [dict(c) for c in item["claims"]],
           "defect_type": defect_type, "expected_verdict": "invalid", "detectable_in": DETECTABLE_IN[defect_type]}
    z = spec.values[DISPLAY_INDEX]
    if defect_type == "hidden_coupling":
        # D1 takes the R1 relation (q enters the target) and R1 is removed, so no two sentences are identical
        coupled = rv._sentence(spec.frame, z, spec.unit, spec.phrasings_r[1].relation, "")
        out["sentences"] = [s for s in out["sentences"] if s["label"] != "R1"]
        out["claims"] = [c for c in out["claims"] if c["label"] != "R1"]
        next(s for s in out["sentences"] if s["label"] == "D1")["text"] = coupled
        next(c for c in out["claims"] if c["label"] == "D1")["minimal_pair_with"] = "R0"  # every D claim names a twin
        out["description"] = "D1 states a relation through which q enters the target but is claimed structurally disconnected"
    elif defect_type == "failed_transformation_identity":
        wrong = _r_answers(structure, spec, FLIP_OP[spec.relevant.op], item.get("instance", 0))
        for c in out["claims"]:
            if c["stratum"] == "R":
                c["certified_answers"] = wrong
        out["description"] = f"R answers computed with q {FLIP_OP[spec.relevant.op]} instead of {spec.relevant.op}"
    elif defect_type == "relevant_variable_removed_from_equation":
        for c in out["claims"]:
            if c["stratum"] == "R":
                c["certified_answers"] = {k: item["base_answer"] for k in c["certified_answers"]}
        out["description"] = "R answers ignore q (all equal the base answer)"
    elif defect_type == "invalid_parameter_domain":
        if spec.conditional is None:
            raise ValueError("needs a K stratum")
        k = spec.conditional
        bad = k.counter_regime_value
        for s in out["sentences"]:
            if s["label"].startswith("K"):
                rel = k.phrasings[int(s["label"][1])].relation
                s["text"] = rv._sentence(k.frame, bad, k.unit, rel, "")
        for c in out["claims"]:
            if c["stratum"] == "K":  # the claim is made consistent with the shown value: q = bad, still "irrelevant"
                c["value_shown"] = rv._fmt(bad)
                c["values"] = [rv._fmt(bad)]
                c["certified_answers"] = {rv._fmt(bad): item["base_answer"]}
        out["description"] = f"K value {rv._fmt(bad)} lies outside the regime ({k.predicate}) but is claimed irrelevant"
    elif defect_type == "inconsistent_units":
        out["target_unit"] = WRONG_UNIT[item["target_unit"]]
        out["description"] = f"claimed target unit {out['target_unit']} has the wrong dimension (values unchanged)"
    elif defect_type == "rendering_not_minimal":
        other = spec.values[DISPLAY_INDEX + 1]
        target = next(s for s in out["sentences"] if s["label"] == "D0")
        target["text"] = rv._sentence(spec.frame, other, spec.unit, spec.phrasings_d[0].relation, "")
        out["description"] = (f"D0 shows {rv._fmt(other)} while its claimed R0 twin shows {rv._fmt(z)} "
                              "(not a minimal pair at the same value)")
    else:
        raise ValueError(defect_type)
    return out


def packets(item: dict[str, Any], seed: int = 42) -> tuple[dict[str, Any], dict[str, Any]]:
    """The judge-facing pass-1 and pass-2 packets: neutral sentence ids, shuffled order, no labels, no key fields."""

    rng = random.Random(f"{seed}:{item['item_id']}")
    order = list(item["sentences"])
    rng.shuffle(order)
    ids = {s["label"]: _sid(item["item_id"], s["label"]) for s in item["sentences"]}
    pass1 = {"item_id": item["item_id"], "problem": item["problem"],
             "sentences": [{"sentence_id": ids[s["label"]], "text": s["text"]} for s in order],
             "instructions": "Each sentence is added, on its own, to the end of the problem's description, before the "
                             "question."}
    claims = []
    for c in item["claims"]:
        cc = {k: v for k, v in c.items() if k != "label"}
        cc["sentence_id"] = ids[c["label"]]
        if "minimal_pair_with" in cc:
            cc["minimal_pair_with"] = ids[cc["minimal_pair_with"]]
        claims.append(cc)
    claims.sort(key=lambda c: c["sentence_id"])
    pass2 = {**pass1, "authors_claims": claims, "target_unit": item["target_unit"],
             "base_answer": item["base_answer"], "relations": item["relations"], "assumptions": item["assumptions"],
             "inputs": item["inputs"]}
    return pass1, pass2


def unit_dimension_differs(a: str, b: str) -> bool:
    return dm.UNITS[a].dim != dm.UNITS[b].dim
