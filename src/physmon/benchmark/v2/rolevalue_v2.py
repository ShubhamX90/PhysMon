"""Role-by-value cells, revision 2 (M0 v2; plan revision v2.2, amendments A2, A3, A4, A5, A9).

This module sits beside `rolevalue.py` (which is unchanged, so the sealed `m0_pilot` can still be rebuilt byte for byte by
`scripts/v2/s177_build_m0_pilot.py`) and reuses its numerical machinery: the graph and independent-solver certification, the
misuse foils, the placebo and the separation checks. What changes is the wording design and the hygiene around it.

* Each R/D quantity has exactly two phrasing pairs `p0` and `p1` (`PhrasePair`). Within a pair the R and D sentences use one
  frame, one numeral and one unit and differ only in a short attachment phrase (the token difference is recorded; the word
  counts differ by at most `MAX_WORD_DIFF`). The D attachment of `p0` puts the quantity on another object in the same scene
  (`other_object_same_scene`); the D attachment of `p1` puts it on the target object in another event
  (`same_object_other_event`, or `same_object_undone_event` when the event adds a change and then removes it). One non-numeric control N per pair is the D sentence without the numeral.
* No sentence of any role may explain its own consequence (`consequence_hits`), and none may carry a marker word
  (`MARKER_WORDS_V2`, the October lexicon plus further giveaway words).
* The D rationale (why there is no physical path) is part of the spec; the stated conditions of the base problem that the D
  event must leave intact are listed and checked to occur in the base text.
* Study values are checked against the displayed inputs and the golds (`value_hygiene`).
* C quantities carry a textbook-familiarity tag; K quantities carry an out-of-regime judgement (`KOut`).
"""

from __future__ import annotations

import dataclasses
import difflib
import math
import re
from dataclasses import dataclass, field
from typing import Any

from physmon.benchmark.v2 import design as dg
from physmon.benchmark.v2 import dimensions as dm
from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue as rv

MAX_WORD_DIFF = 3  # R and D sentences of a pair: word counts differ by at most this
D_KIND_CO_PRESENT = "other_object_same_scene"
D_KINDS_SAME_OBJECT = ("same_object_other_event", "same_object_undone_event")
D_KINDS = (D_KIND_CO_PRESENT, *D_KINDS_SAME_OBJECT)
PAIR_IDS = ("p0", "p1")
FAMILIARITY = ("famous", "standard", "uncommon")
COPY_FOILS = ("copy", "digit_copy")
MAX_DIGIT_OVERLAP = 1  # leading significant digits (of three) a study value may share with an input or a gold
INSTRUCTION_RELEVANCE = ("Some of the information given may not be needed. Identify which quantities matter before you "
                         "solve.")
MIN_RATIONALE = 40  # characters

# Words and phrases that explain what a sentence does to the answer (a consequence), matched as whole words, case-blind.
CONSEQUENCE_TERMS = (
    "so", "so that", "so as to", "therefore", "thus", "hence", "because", "since", "which means", "meaning that", "meaning",
    "as a result", "already moving", "this means", "consequently", "thereby", "in order to", "which makes", "which adds",
    "which raises", "which lowers", "causing", "causes", "leading to", "leads to", "resulting in", "results in",
    "adding to", "adds to", "aiding", "opposing", "increasing", "decreasing", "raising", "raises", "lowering", "lowers",
    "effectively", "in effect", "it follows", "now hangs", "making it", "makes it", "enough to",
    "accordingly", "due to", "owing to", "ensuring", "ensures", "such that", "in turn", "for this reason", "which is why",
    "that is why", "as such", "with the result", "to the effect", "contributing", "contributes", "affecting", "affects",
    "without affecting", "has no bearing",
)
# October marker lexicon plus giveaway words found in the M0 wording review.
MARKER_WORDS_V2 = (*rv.MARKER_WORDS, "unconnected", "disconnected", "unused", "idle", "spare", "elsewhere", "not used",
                   "not needed", "no part", "plays no", "has no", "does not affect", "unaffected", "not involved",
                   "not related", "not relevant", "no link", "on its own", "by itself", "does not matter", "ignore",
                   "stand-alone", "standalone", "not linked", "does not interact", "never touches", "not touching",
                   "independently")
# Place or time remoteness used as the only signal of irrelevance in the M0 wording.
REMOTENESS_TERMS = ("next room", "another room", "other room", "different room", "another building", "another kitchen",
                    "yesterday", "far wall", "far end", "drawer", "elsewhere", "across the floor", "next building")


def consequence_hits(text: str) -> list[str]:
    lowered = text.lower()
    return [t for t in CONSEQUENCE_TERMS if re.search(rf"(?<![\w'-]){re.escape(t)}(?![\w'-])", lowered)]


def marker_hits(text: str) -> list[str]:
    lowered = text.lower()
    return [w for w in MARKER_WORDS_V2 if w in lowered]


def remoteness_hits(text: str) -> list[str]:
    lowered = text.lower()
    return [w for w in REMOTENESS_TERMS if w in lowered]


# --- specification -----------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class PhrasePair:
    pair_id: str  # p0 | p1
    frame: str  # one sentence with {value} {unit} {relation}; the relation slot holds the attachment phrase
    r_attach: str
    d_attach: str
    d_kind: str  # co-present for p0; one of the two same-object kinds for p1
    d_rationale: str  # why the D quantity has no physical path to the target
    conditions_preserved: tuple[str, ...]  # stated conditions of the base text that the D event leaves true (substrings)
    nonnumeric_fill: str  # replaces "{value} {unit}" in the non-numeric control N
    d_frame: str | None = None  # a different D frame, only when the pair cannot honestly share one frame
    frame_mismatch_reason: str = ""
    before_context_ok: bool = False  # the pair-0 sentences read correctly placed before the context
    before_context_reason: str = ""

    @property
    def frame_matched(self) -> bool:
        return self.d_frame is None

    def frame_for(self, role: str) -> str:
        return self.frame if role == "R" or self.d_frame is None else self.d_frame


@dataclass(frozen=True)
class CancellingV2:
    spec: rv.CancellingSpec
    familiarity: str  # famous | standard | uncommon
    familiarity_reason: str
    heldout_values: tuple[float, ...] = ()  # display unit of q; certified like the study values, never emitted


@dataclass(frozen=True)
class KOut:
    feasible: bool
    reason: str  # why the question stays (or does not stay) well posed when the regime fails
    values: tuple[float, ...] = ()  # display unit of the K quantity; the regime predicate must be false at every one


@dataclass(frozen=True)
class ConditionalV2:
    spec: rv.ConditionalSpec
    k_out: KOut
    heldout_values: tuple[float, ...] = ()  # display unit of q; the predicate must hold at each; never emitted


@dataclass(frozen=True)
class RoleSpecV2:
    structure_id: str
    quantity_phrase: str
    quantity_type: str
    unit: str
    values: tuple[float, ...]
    heldout_values: tuple[float, ...]
    relevant: rv.RelevantWiring
    pairs: tuple[PhrasePair, ...]
    cancelling: CancellingV2 | None = None
    conditional: ConditionalV2 | None = None
    author: str = "agent"
    notes: str = ""


def to_legacy(spec: RoleSpecV2) -> rv.RoleSpec:
    """A `rolevalue.RoleSpec` carrying the same wiring, values and attachments, so the numerical certification is shared."""

    return rv.RoleSpec(
        structure_id=spec.structure_id, quantity_phrase=spec.quantity_phrase, quantity_type=spec.quantity_type,
        unit=spec.unit, values=spec.values, heldout_values=spec.heldout_values, frame="{value} {unit} {relation}",
        relevant=spec.relevant,
        phrasings_r=tuple(rv.Phrasing(f"r{i}", p.r_attach) for i, p in enumerate(spec.pairs)),
        phrasings_d=tuple(rv.Phrasing(f"d{i}", p.d_attach) for i, p in enumerate(spec.pairs)),
        nonnumeric_fill=spec.pairs[0].nonnumeric_fill,
        cancelling=None if spec.cancelling is None else spec.cancelling.spec,
        conditional=None if spec.conditional is None else spec.conditional.spec, author=spec.author, notes=spec.notes)


# --- sentences and hygiene ----------------------------------------------------------------------------------------------------

def pair_sentence(pair: PhrasePair, role: str, value: float | None, unit: str) -> str:
    attach = pair.r_attach if role == "R" else pair.d_attach
    return rv._sentence(pair.frame_for(role), value, unit, attach, pair.nonnumeric_fill)


def words(text: str) -> list[str]:
    return re.findall(r"[^\s]+", text)


def token_difference(a: str, b: str) -> dict[str, list[str]]:
    """Word-level difference of two sentences: what was removed from `a` and what was added in `b`."""

    wa, wb = words(a), words(b)
    removed: list[str] = []
    added: list[str] = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=wa, b=wb, autojunk=False).get_opcodes():
        if tag != "equal":
            removed += wa[i1:i2]
            added += wb[j1:j2]
    return {"removed": removed, "added": added}


def displayed_inputs(structure: gr.Structure, instance: int) -> dict[str, float]:
    """The input numerals as the prompt prints them."""

    display = dict(structure.instances[instance])
    return {n.name: float(dg.input_text(structure, n.name, display[n.name])) for n in structure.inputs}


def digit_overlap(a: float, b: float) -> int:
    """Leading significant digits (of three, magnitude ignored) that two numbers share: 0.4 and 40 share three."""

    if a == 0 or b == 0:
        return 0
    return dg.common_leading_digits(a, b)


def value_hygiene(structure: gr.Structure, instance: int, value: float, golds: list[float]) -> dict[str, Any]:
    shown = displayed_inputs(structure, instance)
    equals = sorted(n for n, x in shown.items() if math.isclose(float(rv._fmt(value)), x, rel_tol=1e-9))
    overlap_inputs = max(digit_overlap(value, x) for x in shown.values())
    overlap_gold = max(digit_overlap(value, g) for g in golds)
    return {"value": value, "equals_input": equals, "digit_overlap_with_inputs": overlap_inputs,
            "digit_overlap_with_gold": overlap_gold,
            "ok": not equals and overlap_inputs <= MAX_DIGIT_OVERLAP and overlap_gold <= MAX_DIGIT_OVERLAP}


# --- cells -----------------------------------------------------------------------------------------------------------------------

@dataclass
class Cell:
    structure_id: str
    instance: int
    cell_id: str
    family: str  # role_by_value
    stratum: str  # none | N | R | D | C | K | K_out
    value_index: int | None
    value: float | None
    unit: str | None
    phrasing_id: str | None
    pair_id: str | None
    d_kind: str | None
    position: str
    instruction: str | None
    sentence: str  # the added sentence ("" for no cue)
    prompt: str
    gold_value: float
    gold_unit: str
    foils: dict[str, float] = field(default_factory=dict)
    placebo: float | None = None
    confounded: list[str] = field(default_factory=list)
    consequence_free: bool | None = None
    marker_free: bool | None = None
    digit_overlap_with_inputs: int | None = None
    digit_overlap_with_gold: int | None = None
    heldout: bool = False

    @property
    def source_ambiguous(self) -> bool:
        """The sentence's own numeral, copied or read in the target unit, lands within the loosest tolerance of the cell's
        gold, so a correct answer could come from the sentence. (Misuse foils computed from the graph that coincide with the
        gold are recorded in `confounded` but do not make the source ambiguous.)"""

        return any(name in COPY_FOILS for pair in self.confounded for name in pair.split("~"))


def _flags(sentence: str) -> tuple[bool, bool]:
    return (not consequence_hits(sentence), not marker_hits(sentence))


def _overlaps(structure: gr.Structure, instance: int, value: float | None, golds: list[float]) -> tuple[int | None, int | None]:
    if value is None:
        return None, None
    shown = displayed_inputs(structure, instance)
    return (max(digit_overlap(value, x) for x in shown.values()), max(digit_overlap(value, g) for g in golds))


def role_cells_v2(structure: gr.Structure, spec: RoleSpecV2, instance: int, *, include_heldout: bool = False) -> list[Cell]:
    """All role-by-value cells of one instance at the after-context position: no cue, N per pair, R and D at every value and
    pair, and the C, K and K_out cells the spec defines. Positions and instruction variants are made by `variants`."""

    legacy = to_legacy(spec)
    si = rv.display_inputs_si(structure, instance)
    target_unit = structure.render.target_unit
    y_d = dg.gold_for(structure, dict(structure.instances[instance]))
    sign_definite = all(dg.gold_for(structure, dict(i)) > 0 for i in structure.instances) or all(
        dg.gold_for(structure, dict(i)) < 0 for i in structure.instances)
    cells = [Cell(structure.structure_id, instance, "no_cue", "role_by_value", "none", None, None, None, None, None, None,
                  "after_context", None, "", rv._assemble(structure, instance, "", "after_context"), y_d, target_unit)]
    for index, pair in enumerate(spec.pairs):
        sentence = pair_sentence(pair, "D", None, spec.unit)
        c, m = _flags(sentence)
        cells.append(Cell(structure.structure_id, instance, f"N:d{index}:after_context", "role_by_value", "N", None, None,
                          None, f"d{index}", pair.pair_id, pair.d_kind, "after_context", None, sentence,
                          rv._assemble(structure, instance, sentence, "after_context"), y_d, target_unit,
                          consequence_free=c, marker_free=m))
    values = list(spec.values) + (list(spec.heldout_values) if include_heldout else [])
    for z, value in enumerate(values):
        heldout = z >= len(spec.values)
        y_r, _ = rv.gold_r(structure, si, legacy, value)
        foils = rv.misuse_foils(structure, si, legacy, value)
        placebo, _kind = rv.placebo_value(y_r, y_d, sign_definite)
        cell_foils_base = {k: v for k, v in foils.items() if k != f"{spec.relevant.op}:{spec.relevant.input_name}"}
        for role in ("R", "D"):
            for index, pair in enumerate(spec.pairs):
                sentence = pair_sentence(pair, role, value, spec.unit)
                phrasing = f"{role.lower()}{index}"
                gold = y_r if role == "R" else y_d
                cell_foils = dict(cell_foils_base)
                if role == "D":
                    cell_foils["relevant_twin"] = y_r
                else:
                    cell_foils["neglect"] = y_d
                named = {"gold": gold, **cell_foils}
                confounded = [f"{a}~{b}" for a, b in rv._not_separated(named) if "gold" in (a, b)]
                c, m = _flags(sentence)
                o_in, o_gold = _overlaps(structure, instance, value, [gold])
                cells.append(Cell(structure.structure_id, instance, f"{role}:z{z}:{phrasing}:after_context", "role_by_value",
                                  role, z, value, spec.unit, phrasing, pair.pair_id, pair.d_kind if role == "D" else None,
                                  "after_context", None, sentence, rv._assemble(structure, instance, sentence, "after_context"),
                                  gold, target_unit, cell_foils, placebo if role == "R" else None, confounded, c, m, o_in,
                                  o_gold, heldout))
    values_all = rv.all_node_values(structure, si)
    for stratum, wrapped in (("C", spec.cancelling), ("K", spec.conditional)):
        if wrapped is None:
            continue
        sub = wrapped.spec
        for z, value in enumerate(sub.values):
            q_si = dm.to_si(value, sub.unit)
            law = sub.wrong_law if stratum == "C" else sub.out_of_regime_law
            foils = {"wrong_law" if stratum == "C" else "out_of_regime": dm.from_si(
                rv._eval_expr(law, structure, values_all, q_si), target_unit)}
            foils.update(rv.copy_foils(value, sub.unit, target_unit))
            for j, phrasing in enumerate(sub.phrasings):
                sentence = rv._sentence(sub.frame, value, sub.unit, phrasing.relation, sub.nonnumeric_fill)
                confounded = [f"{a}~{b}" for a, b in rv._not_separated({"gold": y_d, **foils}) if "gold" in (a, b)]
                c, m = _flags(sentence)
                o_in, o_gold = _overlaps(structure, instance, value, [y_d])
                tag = stratum.lower()
                cells.append(Cell(structure.structure_id, instance, f"{stratum}:z{z}:{tag}{j}:after_context", "role_by_value",
                                  stratum, z, value, sub.unit, f"{tag}{j}", f"{tag}{j}", None, "after_context", None, sentence,
                                  rv._assemble(structure, instance, sentence, "after_context"), y_d, target_unit, dict(foils),
                                  None, confounded, c, m, o_in, o_gold))
    if spec.conditional is not None and spec.conditional.k_out.feasible:
        sub = spec.conditional.spec
        for z, value in enumerate(spec.conditional.k_out.values):
            q_si = dm.to_si(value, sub.unit)
            gold = dm.from_si(rv._eval_expr(sub.out_of_regime_law, structure, values_all, q_si), target_unit)
            foils = {"regime_ignored": y_d, **rv.copy_foils(value, sub.unit, target_unit)}
            for j, phrasing in enumerate(sub.phrasings):
                sentence = rv._sentence(sub.frame, value, sub.unit, phrasing.relation, sub.nonnumeric_fill)
                confounded = [f"{a}~{b}" for a, b in rv._not_separated({"gold": gold, **foils}) if "gold" in (a, b)]
                c, m = _flags(sentence)
                o_in, o_gold = _overlaps(structure, instance, value, [gold, y_d])
                cells.append(Cell(structure.structure_id, instance, f"K_out:z{z}:k{j}:after_context", "role_by_value", "K_out",
                                  z, value, sub.unit, f"k{j}", f"k{j}", None, "after_context", None, sentence,
                                  rv._assemble(structure, instance, sentence, "after_context"), gold, target_unit, foils, None,
                                  confounded, c, m, o_in, o_gold))
    return cells


def variants(structure: gr.Structure, spec: RoleSpecV2, instance: int, base: list[Cell]) -> tuple[list[Cell], list[dict[str, Any]]]:
    """Supporting variants of role cells: the relevance instruction (no cue, R and D at the middle value, both pairs) and the
    sentence placed before the context (R and D at the middle value, pair 0, only where the pair says it reads correctly).
    Returns (cells, infeasibility records)."""

    middle = len(spec.values) // 2
    by_id = {c.cell_id: c for c in base}
    out: list[Cell] = []
    infeasible: list[dict[str, Any]] = []
    wanted = ["no_cue"] + [f"{role}:z{middle}:{role.lower()}{i}:after_context" for role in ("R", "D") for i in range(len(spec.pairs))]
    for cid in wanted:
        cell = by_id[cid]
        prompt = f"{cell.prompt} {INSTRUCTION_RELEVANCE}"
        out.append(Cell(**{**cell.__dict__, "cell_id": f"{cid}:instr_relevance", "family": "supporting", "instruction": "relevance",
                           "prompt": prompt, "foils": dict(cell.foils), "confounded": list(cell.confounded)}))
    pair = spec.pairs[0]
    for role in ("R", "D"):
        cid = f"{role}:z{middle}:{role.lower()}0:after_context"
        cell = by_id[cid]
        if not pair.before_context_ok:
            infeasible.append({"cell_id": cid.replace("after_context", "before_context"), "condition": "before_context",
                               "feasible": False,
                               "reason": pair.before_context_reason if role == "R" else
                               "The matched R sentence cannot be placed before the context, so its D twin is not built either: "
                               + pair.before_context_reason})
            continue
        prompt = rv._assemble(structure, instance, cell.sentence, "before_context")
        out.append(Cell(**{**cell.__dict__, "cell_id": cid.replace("after_context", "before_context"), "family": "supporting",
                           "position": "before_context", "prompt": prompt, "foils": dict(cell.foils),
                           "confounded": list(cell.confounded)}))
    return out, infeasible


# --- certification ----------------------------------------------------------------------------------------------------------------

def _within(a: float, b: float, tol: float) -> bool:
    scale = max(abs(a), abs(b))
    return scale == 0 or abs(a - b) <= tol * scale


def certify_v2(structure: gr.Structure, spec: RoleSpecV2) -> dict[str, Any]:
    """All checks of one spec: the shared numerical certificate plus the wording, hygiene, familiarity and K_out rules."""

    checks: dict[str, Any] = {}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        checks[name] = {"ok": bool(ok), "detail": detail}

    legacy = to_legacy(spec)
    numeric = rv.certify_role_spec(structure, legacy) if len(spec.pairs) >= 2 else {"passed": False, "failed": ["pairs"],
                                                                                    "strata_failed": [], "checks": {}}
    check("numeric_certificate", numeric["passed"] and not numeric["strata_failed"],
          {"failed": numeric["failed"], "strata_failed": numeric["strata_failed"]})
    check("exactly_two_pairs", [p.pair_id for p in spec.pairs] == list(PAIR_IDS), [p.pair_id for p in spec.pairs])
    if len(spec.pairs) != 2 or "per_instance" not in numeric["checks"]:
        return {"passed": False, "failed": [k for k, v in checks.items() if not v["ok"]], "checks": checks, "numeric": numeric}
    check("d_kinds", spec.pairs[0].d_kind == D_KIND_CO_PRESENT and spec.pairs[1].d_kind in D_KINDS_SAME_OBJECT,
          [p.d_kind for p in spec.pairs])
    context = dg.context_text(structure, dict(structure.instances[0]))
    pair_records = []
    for pair in spec.pairs:
        value0, unit = spec.values[0], spec.unit
        r_sentence = pair_sentence(pair, "R", value0, unit)
        d_sentence = pair_sentence(pair, "D", value0, unit)
        n_sentence = pair_sentence(pair, "D", None, unit)
        record: dict[str, Any] = {"pair_id": pair.pair_id, "d_kind": pair.d_kind, "r_sentence": r_sentence,
                                  "d_sentence": d_sentence, "n_sentence": n_sentence, "d_rationale": pair.d_rationale,
                                  "conditions_preserved": list(pair.conditions_preserved)}
        record["token_difference"] = token_difference(r_sentence, d_sentence)
        record["word_counts"] = [len(words(r_sentence)), len(words(d_sentence))]
        record["word_count_ok"] = abs(record["word_counts"][0] - record["word_counts"][1]) <= MAX_WORD_DIFF
        shared = (r_sentence.replace(pair.r_attach, "@") == d_sentence.replace(pair.d_attach, "@")) if pair.frame_matched else False
        record["same_frame_numeral_unit"] = shared
        record["pair_frame_matched"] = pair.frame_matched
        record["frame_mismatch_reason"] = pair.frame_mismatch_reason
        record["frame_mismatch_reason_ok"] = pair.frame_matched or len(pair.frame_mismatch_reason) >= MIN_RATIONALE
        sentences = {"R": [pair_sentence(pair, "R", v, unit) for v in spec.values],
                     "D": [pair_sentence(pair, "D", v, unit) for v in spec.values], "N": [n_sentence]}
        record["consequence_free"] = {k: not any(consequence_hits(s) for s in v) for k, v in sentences.items()}
        record["marker_free"] = {k: not any(marker_hits(s) for s in v) for k, v in sentences.items()}
        record["remoteness_free_d"] = not any(remoteness_hits(s) for s in sentences["D"])
        record["attach_has_no_digit"] = not any(re.search(r"\d", a) for a in (pair.r_attach, pair.d_attach))
        record["d_rationale_ok"] = len(pair.d_rationale.strip()) >= MIN_RATIONALE
        missing = [c for c in pair.conditions_preserved if c not in context]
        record["conditions_listed"] = bool(pair.conditions_preserved)
        record["conditions_in_base_text"] = not missing
        record["conditions_missing"] = missing
        record["numerals_ok"] = all(_prompt_numerals_ok(structure, 0, s, v) for s, v in zip(
            [rv._assemble(structure, 0, x, "after_context") for x in sentences["R"]], spec.values, strict=True)) and all(
            _prompt_numerals_ok(structure, 0, s, v) for s, v in zip(
                [rv._assemble(structure, 0, x, "after_context") for x in sentences["D"]], spec.values, strict=True))
        pair_records.append(record)
    for key in ("word_count_ok", "attach_has_no_digit", "d_rationale_ok", "conditions_listed", "conditions_in_base_text",
                "numerals_ok", "remoteness_free_d", "frame_mismatch_reason_ok"):
        check(key, all(p[key] for p in pair_records), [p[key] for p in pair_records])
    check("same_frame_numeral_unit_or_declared_unmatched",
          all(p["same_frame_numeral_unit"] or not p["pair_frame_matched"] for p in pair_records),
          [p["same_frame_numeral_unit"] for p in pair_records])
    check("consequence_free", all(all(p["consequence_free"].values()) for p in pair_records),
          [p["consequence_free"] for p in pair_records])
    check("marker_free", all(all(p["marker_free"].values()) for p in pair_records), [p["marker_free"] for p in pair_records])
    check("before_context_judged", all(bool(p.before_context_reason) for p in spec.pairs[:1]), spec.pairs[0].before_context_reason)
    # C and K sentences
    for name, wrapped in (("cancelling", spec.cancelling), ("conditional", spec.conditional)):
        if wrapped is None:
            continue
        sub = wrapped.spec
        sentences = [rv._sentence(sub.frame, v, sub.unit, p.relation, sub.nonnumeric_fill) for v in sub.values for p in sub.phrasings]
        check(f"{name}_consequence_free", not any(consequence_hits(s) for s in sentences), sentences[:2])
        check(f"{name}_marker_free", not any(marker_hits(s) for s in sentences), sentences[:2])
        check(f"{name}_numerals_ok", all(_prompt_numerals_ok(structure, 0, rv._assemble(structure, 0, s, "after_context"), v)
                                          for s, v in zip(sentences, [v for v in sub.values for _ in sub.phrasings], strict=True)))
    if spec.cancelling is not None:
        check("c_familiarity_tag", spec.cancelling.familiarity in FAMILIARITY and len(spec.cancelling.familiarity_reason) >= 20,
              [spec.cancelling.familiarity, spec.cancelling.familiarity_reason])
        held = dataclasses.replace(spec.cancelling.spec, values=spec.cancelling.heldout_values)
        held_cert = rv.certify_cancelling(structure, held)
        check("c_heldout_two_certified", len(spec.cancelling.heldout_values) == 2 and all(
            held_cert.get(k) is True for k in ("q_present_unsimplified", "derivative_zero", "numeric_invariance",
                                               "wrong_law_separated_at_2_of_3")),
              {"values": list(spec.cancelling.heldout_values), "certificate": held_cert})
    if spec.conditional is not None:
        held_k = dataclasses.replace(spec.conditional.spec, values=spec.conditional.heldout_values)
        held_k_cert = rv.certify_conditional(structure, held_k)
        check("k_heldout_two_certified", len(spec.conditional.heldout_values) == 2 and all(
            held_k_cert.get(k) is True for k in ("predicate_holds_at_all_values", "out_of_regime_law_separated")),
              {"values": list(spec.conditional.heldout_values), "certificate": held_k_cert})
        ko = spec.conditional.k_out
        check("k_out_judged", len(ko.reason) >= MIN_RATIONALE, ko.reason)
        if ko.feasible:
            sub = spec.conditional.spec
            broken = True
            answers = []
            for instance in range(len(structure.instances)):
                values_all = rv.all_node_values(structure, rv.display_inputs_si(structure, instance))
                gold = dm.from_si(values_all[structure.target], structure.render.target_unit)
                for v in ko.values:
                    q_si = dm.to_si(v, sub.unit)
                    broken &= not bool(rv._eval_expr(sub.predicate, structure, values_all, q_si))
                    alt = dm.from_si(rv._eval_expr(sub.out_of_regime_law, structure, values_all, q_si), structure.render.target_unit)
                    answers.append(abs(alt - gold) > rv.LOOSEST_REL_TOL * max(abs(alt), abs(gold)))
            check("k_out_predicate_false_and_answer_moves", broken and all(answers) and len(ko.values) >= 2,
                  {"values": list(ko.values), "predicate_false": broken, "answers_separated": all(answers)})
        else:
            check("k_out_infeasible_has_no_values", not ko.values)
    # hygiene and cross-cell separation on the emitted instance
    cells = role_cells_v2(structure, spec, 0)
    golds = sorted({round(c.gold_value, 12) for c in cells})
    hygiene = {}
    for name, quantity_values, unit in (("R_D", spec.values, spec.unit),
                                        *([("C", spec.cancelling.spec.values, spec.cancelling.spec.unit)] if spec.cancelling else []),
                                        *([("K", spec.conditional.spec.values, spec.conditional.spec.unit)] if spec.conditional else []),
                                        *([("K_out", spec.conditional.k_out.values, spec.conditional.spec.unit)]
                                          if spec.conditional and spec.conditional.k_out.feasible else [])):
        hygiene[name] = [value_hygiene(structure, 0, v, golds) for v in quantity_values]
    hygiene["R_D_heldout"] = [value_hygiene(structure, 0, v, golds) for v in spec.heldout_values]
    if spec.cancelling:
        hygiene["C_heldout"] = [value_hygiene(structure, 0, v, golds) for v in spec.cancelling.heldout_values]
    if spec.conditional:
        hygiene["K_heldout"] = [value_hygiene(structure, 0, v, golds) for v in spec.conditional.heldout_values]
    check("value_hygiene", all(h["ok"] for k, v in hygiene.items() if "heldout" not in k for h in v), hygiene)
    check("heldout_value_hygiene", all(h["ok"] for k, v in hygiene.items() if "heldout" in k for h in v),
          {k: v for k, v in hygiene.items() if "heldout" in k})
    # misuse foils that equal the base answer at every study value (adding eV to a keV rest energy) carry no information;
    # they are recorded, not blocking
    d_cells = [c for c in cells if c.stratum == "D"]
    degenerate = sorted({n for n in (d_cells[0].foils if d_cells else {})
                         if all(_within(c.foils[n], c.gold_value, rv.LOOSEST_REL_TOL) for c in d_cells if n in c.foils)})
    confounded = {c.cell_id: c.confounded for c in cells if c.confounded}
    blocking_confounds = {cid: [p for p in pairs if not all(n in degenerate or n == "gold" for n in p.split("~"))]
                          for cid, pairs in confounded.items()}
    blocking_confounds = {k: v for k, v in blocking_confounds.items() if v}
    check("no_confounded_foils_except_degenerate", not blocking_confounds, blocking_confounds)
    checks["degenerate_misuse_foils"] = {"ok": True, "detail": {"names": degenerate, "all_confounded_pairs": confounded}}
    skip = {"relevant_twin", "neglect", "regime_ignored", *degenerate}
    collisions = []
    for cell in cells:
        for name, foil in cell.foils.items():
            if name in skip:
                continue
            for gold in golds:
                if _within(foil, gold, rv.LOOSEST_REL_TOL) and not math.isclose(gold, round(cell.gold_value, 12), rel_tol=1e-9):
                    collisions.append({"cell": cell.cell_id, "foil": name, "foil_value": foil, "other_gold": gold})
    check("foils_not_equal_to_other_cells_golds", not collisions, collisions)
    failed = [k for k, v in checks.items() if not v["ok"]]
    return {"passed": not failed, "failed": failed, "checks": checks, "pairs": pair_records, "hygiene": hygiene,
            "numeric": numeric}


def _prompt_numerals_ok(structure: gr.Structure, instance: int, prompt: str, value: float | None) -> bool:
    """Every numeral in the prompt is a displayed input or the single role value."""

    expected = sorted([*displayed_inputs(structure, instance).values()] + ([float(rv._fmt(value))] if value is not None else []))
    found = dg.prompt_numbers(prompt)
    return found == expected


def complete(spec: RoleSpecV2, certificate: dict[str, Any]) -> bool:
    return bool(certificate["passed"]) and len(spec.values) >= 3 and len(spec.pairs) == 2
