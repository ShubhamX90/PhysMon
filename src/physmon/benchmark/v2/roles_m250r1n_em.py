"""M250 repair round 1 (journal J15.1-059) of `roles_m250n_em`: the specs the two-judge panel rejected (any high flag) or whose sentences the
blind naturalness rater rated artificial, repaired; every other spec is the `roles_m250n_em` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r1/briefs/roles_m250n_em.md` (built by `scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250/runs/score_two_judges/`). No model output exists on any of these structures, so they may
still be edited (dataset admission standard, preamble). Wording rules 1-8 of `roles_m250n_em` apply to every changed sentence.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired
(they move to `INFEASIBLE` with the reason and are replaced in a later batch).
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250n_em as SRC

OLD: dict[str, r2.RoleSpecV2] = dict(getattr(SRC, "ROLE_SPECS", None) or SRC.SPECS)
TARGET_TERMS = SRC.TARGET_TERMS
NO_C: dict[str, str] = dict(SRC.NO_C)
NO_K: dict[str, str] = dict(SRC.NO_K)
K_KINDS = dict(getattr(SRC, "K_KINDS", {}) or {})
if hasattr(SRC, "CERT_VERSION"):
    CERT_VERSION = SRC.CERT_VERSION

# structure id -> tuple of (finding it answers, resolution); one entry per changed structure
CHANGES: dict[str, tuple[tuple[str, str], ...]] = {}

# structure id -> repaired spec (built from OLD[sid] with dataclasses.replace)
FIXED: dict[str, r2.RoleSpecV2] = {}

# structure id -> replacement structure factory (NEW structures only, when the base problem itself must change); default: SRC's
STRUCTURE_OVERRIDES: dict[str, object] = {}

# --- repairs ------------------------------------------------------------------------------------------------------------------------


def _note(sid: str, text: str) -> str:
    return f"{OLD[sid].notes} M250 r1: {text}".strip()


def _p(sid: str, i: int, **kw):
    return dataclasses.replace(OLD[sid].pairs[i], **kw)


# S211: R1 rated artificial (clip stuck on at the instant of release); GPT: cancellation relations applied an interior formula
# of a ball of radius a at a point outside it.
_S211_SPEC = OLD["S211"].cancelling.spec
_S211_EXPR = ("q0*(((((4/3)*pi*q**3*(3*(8854/10**15)*E0/R)))/((4/3)*pi*q**3))*d/(3*(8854/10**15)))/m")
FIXED["S211"] = dataclasses.replace(
    OLD["S211"],
    cancelling=dataclasses.replace(
        OLD["S211"].cancelling,
        spec=dataclasses.replace(
            _S211_SPEC, expr_with_q=_S211_EXPR,
            intermediate_relations=(
                "charge of the removed material Qc = (4/3) pi a^3 rho, with rho = 3 eps0 E0 / R",
                "charge density of the removed material rho = Qc / ((4/3) pi a^3) (a cancels)",
                "field in the cavity = rho d / (3 eps0), by superposition of the whole ball and a ball of opposite charge in the cavity"))),
    pairs=(OLD["S211"].pairs[0],
           _p("S211", 1, frame="An uncharged {value} {unit} plastic clip {relation}.", r_attach="rides on the bead when it is released",
              d_attach="rode on the bead for an earlier trial only")),
    notes=_note("S211", "R1 'is stuck to the bead at the moment it is released' (artificial) -> 'rides on the bead when it is released'; "
                        "D1/N1 -> 'rode on the bead for an earlier trial only'; the C intermediate relations no longer apply the "
                        "interior-sphere formula at a point outside the removed sphere (rho = Qc/((4/3) pi a^3) recovers the density, "
                        "the field is rho d/(3 eps0)); the expression is algebraically unchanged."))
CHANGES["S211"] = (
    ("claude R1 rated artificial: 'An uncharged 0.7 g plastic clip is stuck to the bead at the moment it is released.'",
     "'An uncharged 0.7 g plastic clip rides on the bead when it is released.' (D1/N1: 'rode on the bead for an earlier trial only')"),
    ("gpt high invalid_parameter_domain: the C relations apply Qc d/(4 pi eps0 a^3) where d is outside a small removed sphere",
     "the relations now state rho = Qc/((4/3) pi a^3) and the cavity field rho d/(3 eps0); the expression is rewritten to match "
     "(same value, a still cancels)"),
    ("claude low: the C relations are written loosely", "same rewrite: the superposition is named in the last relation"),
)

# S215: GPT: uniformity not stated; 310 m with the stated totals needs a wavefront faster than light.
_S215_C = OLD["S215"].cancelling
FIXED["S215"] = dataclasses.replace(
    OLD["S215"],
    cancelling=dataclasses.replace(
        _S215_C,
        spec=dataclasses.replace(
            _S215_C.spec, values=(34.0, 67.0, 89.0),
            wrong_law=_S215_C.spec.wrong_law.replace("q/60", "q/4"), frame="The cable {relation} {value} {unit}.",
            phrasings=(rv.Phrasing("c0", "has a length of"), rv.Phrasing("c1", "measures"))),
        heldout_values=(38.0, 76.0)),
    scene_clause="The cable is uniform along its length. A signal lamp, run from a battery of its own, stands beside the apparatus.",
    notes=_note("S215", "scene clause states that the cable is uniform; C lengths 34/67/89 m (heldout 38/76 m) keep the wavefront speed "
                        "L/sqrt(LC) = length / 0.5 microseconds below the speed of light (certified 310 m needed 6.2e8 m/s); C1 'is cut "
                        "to a length of' -> 'measures'."))
CHANGES["S215"] = (
    ("gpt high missing_assumption: uniformity of the cable not stated",
     "scene clause: 'The cable is uniform along its length.'"),
    ("gpt high invalid_parameter_domain: 310 m with L = 0.025 mH, C = 10 nF needs 6.2e8 m/s",
     "C values (45, 120, 310) m -> (34, 67, 89) m (wrong law Z0 ~ length/4 so it separates from the gold), heldout (75, 200) -> (38, 76) m; speed = length/0.5 us <= 1.8e8 m/s; digits chosen to pass value hygiene"),
    ("claude low: 'The cable is cut to a length of 120 m.' could suggest the totals no longer apply",
     "C1 'The cable measures 67 m.'"),
)

# S216: GPT: negative plates not stated joined.


def _s216_factory() -> gr.Structure:
    base = SRC.STRUCTURE_FACTORIES["S216"]()
    old_ctx = "connected, with their positive plates joined, through an ideal inductor and a switch, with no resistance"
    new_ctx = ("connected, with their positive plates joined through an ideal inductor and a switch and their negative plates "
               "joined directly by a wire, with no resistance")
    assert old_ctx in base.render.context
    render = dataclasses.replace(base.render, context=base.render.context.replace(old_ctx, new_ctx))
    assumptions = tuple(
        dataclasses.replace(a, text="The capacitors are joined with their positive plates together through the inductor and the "
                                    "switch and their negative plates together by a wire, so the charges on the joined plates add, "
                                    "and there is no current in the inductor when the switch closes.")
        if a.assumption_id == "A-start" else a for a in base.assumptions)
    return dataclasses.replace(base, render=render, assumptions=assumptions)


STRUCTURE_OVERRIDES["S216"] = _s216_factory
_S216_FRAME_P0 = "A {value} {unit} capacitor, charged to the same voltage as the first one, is connected in parallel with {relation}."
_S216_FRAME_P1 = "A {value} {unit} capacitor, charged to the same voltage as the first one, {relation}."
FIXED["S216"] = dataclasses.replace(
    OLD["S216"],
    pairs=(_p("S216", 0, frame=_S216_FRAME_P0), _p("S216", 1, frame=_S216_FRAME_P1)),
    notes=_note("S216", "base text states that the negative plates are joined directly by a wire (STRUCTURE_OVERRIDES; gold unchanged); "
                        "'charged to the same voltage' now names its referent ('as the first one')."))
CHANGES["S216"] = (
    ("gpt high insufficient_boundary_condition: connection of the negative plates not stated",
     "base text: 'with their positive plates joined through an ideal inductor and a switch and their negative plates joined directly "
     "by a wire'; assumption A-start extended"),
    ("claude low / rater D0, N0, R0: 'charged to the same voltage' has no clear referent",
     "'charged to the same voltage as the first one' in all sentences of both pairs"),
)

# S218 and S220: GPT (and Claude for S220): relative polarity of the series battery not stated; D0/N0 rated artificial.
_ADD = ", their emfs pointing the same way"
FIXED["S218"] = dataclasses.replace(
    OLD["S218"],
    scene_clause="A neon sign, run from a low-voltage supply of its own, hangs on the wall beside the bench.",
    pairs=(_p("S218", 0, frame="A further {value} {unit} battery is connected in series with {relation}" + _ADD + ".",
              r_attach="the capacitor's battery", d_attach="the neon sign's supply"),
           _p("S218", 1, r_attach="is connected in series with the capacitor's battery" + _ADD + ", before the plates are pulled apart",
              d_attach="was connected in series with the capacitor's battery" + _ADD + ", for an earlier run only")),
    notes=_note("S218", "the series battery is connected 'with the two emfs pointing the same way' (one polarity reading); the neon sign runs from a "
                        "low-voltage supply, so raising that supply is an ordinary action; 'the capacitor's battery' replaces "
                        "'the battery'."))
CHANGES["S218"] = (
    ("gpt high insufficient_boundary_condition: relative polarity of the series batteries not stated",
     "R0/R1/D/N: '... in series with the capacitor's battery with the two emfs pointing the same way'"),
    ("rater D0, N0 artificial: 'A further 450 V battery is connected in series with the neon sign's supply.'",
     "scene: sign run from a low-voltage supply; D0/N0 '... in series with the neon sign's supply with the two emfs pointing the same way'"),
)
FIXED["S220"] = dataclasses.replace(
    OLD["S220"],
    scene_clause="A Geiger counter, whose tube voltage is set by a high-voltage supply of its own, stands beside the apparatus.",
    pairs=(_p("S220", 0, frame="A further {value} {unit} battery is connected in series with {relation}" + _ADD + ".",
              r_attach="the capacitor's battery", d_attach="the Geiger counter's supply"),
           _p("S220", 1, r_attach="is connected in series with the capacitor's battery" + _ADD + ", before the slab is inserted",
              d_attach="was connected in series with the capacitor's battery" + _ADD + ", for an earlier run only")),
    notes=_note("S220", "the series battery is connected 'with the two emfs pointing the same way' (one polarity reading); the counter's tube voltage "
                        "is set by its supply, so raising that supply is an ordinary action; 'the capacitor's battery' removes the "
                        "ambiguity with the counter's supply."))
CHANGES["S220"] = (
    ("claude and gpt high: relative polarity of the further battery not stated (V + q assumed, V - q possible)",
     "R0/R1/D/N: '... in series with the capacitor's battery with the two emfs pointing the same way'"),
    ("rater D0, N0 artificial: '... in series with the Geiger counter's supply.'",
     "scene: tube voltage set by the counter's supply; D0/N0 '... in series with the Geiger counter's supply with the two emfs pointing the same way'"),
    ("rater R1 'the battery' ambiguous next to the counter's supply", "'the capacitor's battery'"),
)

# S219: GPT: non-relativistic motion not stated; R1, D1, N1 rated artificial.
FIXED["S219"] = dataclasses.replace(
    OLD["S219"],
    scene_clause="The bead moves slowly compared with light. An electroscope stands on the bench, well clear of the apparatus.",
    pairs=(OLD["S219"].pairs[0],
           _p("S219", 1, r_attach="is placed on the bead just before it enters the field",
              d_attach="was placed on the bead for an earlier run only")),
    notes=_note("S219", "scene clause states that the bead moves slowly compared with light; pair-1 wording 'is placed on the bead just "
                        "before it enters the field' / 'was placed on the bead for an earlier run only'."))
CHANGES["S219"] = (
    ("gpt high missing_assumption: non-relativistic motion not stated",
     "scene clause: 'The bead moves slowly compared with light.'"),
    ("rater R1 artificial: 'A further 3.4 mC of charge sits on the bead as it enters the field.'",
     "'A further 3.4 mC of charge is placed on the bead just before it enters the field.'"),
    ("rater D1/N1 artificial: '... of charge sat on the bead for an earlier run only.'",
     "'... of charge was placed on the bead for an earlier run only.'"),
)


# structure id -> reason the structure could not be repaired (it is removed from the specs and recorded as infeasible)
DROPPED: dict[str, str] = {}

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 1: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
