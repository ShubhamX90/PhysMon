"""M250 repair round 1 (journal J15.1-059) of `roles_m250n_thermo`: the specs the two-judge panel rejected (any high flag) or whose sentences the
blind naturalness rater rated artificial, repaired; every other spec is the `roles_m250n_thermo` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r1/briefs/roles_m250n_thermo.md` (built by `scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250/runs/score_two_judges/`). No model output exists on any of these structures, so they may
still be edited (dataset admission standard, preamble). Wording rules 1-8 of `roles_m250n_thermo` apply to every changed sentence.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired
(they move to `INFEASIBLE` with the reason and are replaced in a later batch).
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250n_thermo as SRC

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

# structure id -> reason the structure could not be repaired (it is removed from the specs and recorded as infeasible)
DROPPED: dict[str, str] = {}

def _fix(sid: str, pairs: dict[int, dict] | None = None, note: str = "", **fields) -> r2.RoleSpecV2:
    old = OLD[sid]
    new_pairs = tuple(dataclasses.replace(p, **(pairs or {}).get(i, {})) for i, p in enumerate(old.pairs))
    return dataclasses.replace(old, pairs=new_pairs, notes=f"{old.notes} M250 r1: {note}".strip(), **fields)


# --- S221: R1 contradicted the 2 mol (judge), K reference expression wrong (GPT) -------------------------------------------------------
FIXED["S221"] = _fix(
    "S221",
    pairs={1: dict(frame="{relation} a further {value} {unit} of nitrogen at the same temperature.",
                   r_attach="Just before the heating begins, the cylinder takes in",
                   d_attach="In an earlier run, the cylinder took in")},
    conditional=None,
    note="pair-1 R/D reworded: 'When the heating begins, the cylinder also holds a further 1.3 mol' read as contradicting the stated "
         "2 mol, now 'Just before the heating begins, the cylinder takes in a further 1.3 mol' (D: 'In an earlier run, the cylinder "
         "took in ...'); K quantity removed because the outside-regime reference (fully excited vibration, 9nR dT/2) is not what a "
         "characteristic temperature below 5 T2 gives.")
NO_K["S221"] = ("Where 5 T2 is not below the characteristic temperature of the vibration the mode is partly excited, so no definite "
                "heat follows from the stated relations (the fully excited value is not the right out-of-regime answer); "
                "the regime has no sharp threshold with a definite out-of-regime answer.")
K_KINDS.pop("S221", None)
CHANGES["S221"] = (
    ("gpt high: K annotations give 9nR(T2-T1)/2 as the outside-regime reference although failure of 5T2 < theta does not imply fully "
     "excited vibration",
     "K quantity removed (conditional=None); NO_K['S221'] records why no definite out-of-regime answer exists."),
    ("R1 rated artificial: 'When the heating begins, the cylinder also holds a further 1.3 mol of nitrogen at the same temperature.' "
     "contradicts the stated 2 mol",
     "R1 now 'Just before the heating begins, the cylinder takes in a further 1.3 mol of nitrogen at the same temperature.'; the "
     "twin D1 is 'In an earlier run, the cylinder took in a further 1.3 mol of nitrogen at the same temperature.' (also replaces "
     "'For an earlier run only, the cylinder also held ...', rated slightly artificial); N1 follows the D1 frame."),
)

# --- S222: GPT's only high flag is the 5.3b judge error (N sentences are numeral-free by design); nothing to change -----------------------

# --- S223: R1 artificial, D0 artificial --------------------------------------------------------------------------------------------
FIXED["S223"] = _fix(
    "S223",
    pairs={0: dict(d_attach="loaded into the dispenser's ice hopper"),
           1: dict(frame="{relation} a further {value} {unit} of ice at its melting point.",
                   r_attach="Just before the heating begins, the block gains",
                   d_attach="In an earlier run, the block gained")},
    scene_clause="A water dispenser with an ice hopper stands in the corridor outside the laboratory, with no pipe to the block. "
                 "No water evaporates from the block.",
    note="D0/N0 now load the ice into the ice hopper of the dispenser (a purposeful action; the scene clause gives the dispenser an "
         "ice hopper); pair-1 R/D reworded so that the further ice is gained before the heating, not 'also included' in the 0.2 kg.")
CHANGES["S223"] = (
    ("R1 rated artificial: 'When the heating begins, the block also includes a further 0.13 kg of ice at its melting point.' "
     "conflicts with the stated mass",
     "R1 now 'Just before the heating begins, the block gains a further 0.13 kg of ice at its melting point.'; D1 'In an earlier run, "
     "the block gained a further 0.13 kg of ice at its melting point.' (was 'For an earlier run only, the block also included ...')."),
    ("D0 rated artificial: 'put into the dispenser' (pointless action)",
     "D0/N0 now '... is loaded into the dispenser's ice hopper.' with the scene clause 'A water dispenser with an ice hopper stands in "
     "the corridor ...'."),
)

# --- S224: GPT high (temperature of the added helium unstated) ---------------------------------------------------------------------
FIXED["S224"] = _fix(
    "S224",
    pairs={0: dict(frame="Before the gases are allowed to mix, a further {value} {unit} of helium at the temperature of the gases is "
                         "{relation}."),
           1: dict(frame="{relation} a further {value} {unit} of helium at the temperature of the gases.",
                   r_attach="Before the gases are allowed to mix, the helium compartment takes in",
                   d_attach="In an earlier run, the helium compartment took in")},
    note="the added helium is stated to be at the temperature of the gases (R and D, both pairs), so that the common temperature of "
         "the two gases is explicit; pair-1 R/D reworded ('takes in' for 'also holds a further ...' that read as contradicting 1.5 mol).")
CHANGES["S224"] = (
    ("gpt high: T6DA3[R0] admits helium without specifying that the compartments regain a common temperature",
     "R0 now 'Before the gases are allowed to mix, a further 1.3 mol of helium at the temperature of the gases is let into the "
     "helium compartment.' (same frame for D0 and N0 with the balloon)."),
    ("claude low: R sentences do not state that the added helium is at the common temperature",
     "pair-1 R now 'Before the gases are allowed to mix, the helium compartment takes in a further 1.3 mol of helium at the "
     "temperature of the gases.'"),
    ("R1 slightly artificial: 'the helium compartment also holds a further 1.3 mol' borders on contradicting 1.5 mol",
     "reworded as above; D1 'In an earlier run, the helium compartment took in a further 1.3 mol of helium at the temperature of "
     "the gases.' (was 'For an earlier run only, ... also held ...')."),
)

# --- S225: GPT high + Claude medium (which surface is held at the outer temperature once more insulation is added) --------------------


def _s225_factory() -> gr.Structure:
    base = SRC.STRUCTURE_FACTORIES["S225"]()
    old = "and the outer surface of the insulation is held at {Tout} K."
    assert old in base.render.context
    context = base.render.context.replace(old, "and the outermost surface of the insulation is held at {Tout} K.")
    return dataclasses.replace(base, render=dataclasses.replace(base.render, context=context))


STRUCTURE_OVERRIDES["S225"] = _s225_factory
FIXED["S225"] = _fix(
    "S225",
    pairs={0: dict(frame="A further {value} {unit} of the same insulation is wrapped {relation}."),
           1: dict(frame="{relation} a further {value} {unit} of the same insulation.",
                   r_attach="Before the heat flow becomes steady, the layer is wrapped in",
                   d_attach="In an earlier survey, the layer was wrapped in")},
    note="base context now says the OUTERMOST surface of the insulation is held at the stated temperature (base answer unchanged), "
         "so after a further wrapping it is the new outermost surface that is held there and the old outer radius is not clamped; "
         "the tail 'with its outer surface held at the same temperature' is dropped from every frame; pair-1 R/D reworded.")
CHANGES["S225"] = (
    ("gpt high: T21B1[R1] and T15F5[R0] do not replace the maintained 300 K condition at 9 cm by a condition at the new outer surface",
     "base context (STRUCTURE_OVERRIDES) now reads '... and the outermost surface of the insulation is held at 300 K'; R0 is "
     "'A further 1.8 cm of the same insulation is wrapped round the layer on the pipe.' (the old tail 'with its outer surface held "
     "at the same temperature' is removed, which was ambiguous); the base answer 55.7968 K is unchanged."),
    ("claude medium: a reader could keep the 9 cm surface clamped and get 55.80 K",
     "same change: the clamp is stated on the outermost surface, which is the new one after the wrapping."),
    ("N1 rated artificial: 'For an earlier survey only, the layer was wrapped in a further small thickness ...'",
     "D1/N1 now 'In an earlier survey, the layer was wrapped in a further 1.8 cm / small thickness of the same insulation.'"),
    ("R1 slightly artificial: 'While the heat flows steadily, the layer is wrapped in ...'",
     "R1 now 'Before the heat flow becomes steady, the layer is wrapped in a further 1.8 cm of the same insulation.'"),
)

# --- S226: GPT high (timing of the warming; does the hot plate stay at the new temperature), N0 artificial ---------------------------
FIXED["S226"] = _fix(
    "S226",
    pairs={0: dict(frame="Before the shields settle, a heater warms and then keeps {relation} {value} {unit} above its initial "
                         "temperature.", nonnumeric_fill="a few kelvin"),
           1: dict(frame="{relation} {value} {unit} above its initial temperature.",
                   r_attach="Before the shields reach steady temperatures, a heater warms and then keeps the hot plate",
                   d_attach="In an earlier run, a heater warmed and then kept the hot plate", nonnumeric_fill="a few kelvin")},
    note="R/D/N reworded ('warms and then keeps ... {v} above its initial temperature') so that the warming happens before the shields "
         "settle and the plate stays at the raised temperature: exactly one reading, the certified one (the stated 800 K is the "
         "initial temperature of the plate).")
CHANGES["S226"] = (
    ("gpt high: T7BAD[R0] describes ongoing warming without the observation time or that the plate then remains at the new "
     "temperature",
     "R0 now 'Before the shields settle, a heater warms and then keeps the hot plate 70 K above its initial temperature.' ; "
     "R1 'Before the shields reach steady temperatures, a heater warms and then keeps the hot plate 70 K above its initial "
     "temperature.'"),
    ("claude low: progressive 'is then warming ... by a further 70 K' awkward",
     "removed with the rewording above; D0 'Before the shields settle, a heater warms and then keeps the water in the kettle 70 K "
     "above its initial temperature.'"),
    ("N0 rated artificial: 'A heater is then warming the water in the kettle by a further few kelvin.'",
     "N0 now '... keeps the water in the kettle a few kelvin above its initial temperature.' ; N1 '... kept the hot plate a few "
     "kelvin above its initial temperature.'"),
)

# --- S227: Claude high (R1 contradicts stated equilibrium 300 K) + GPT high (R0 timing), N0/D0 awkward ------------------------------
FIXED["S227"] = _fix(
    "S227",
    pairs={0: dict(frame="Before the energy is evaluated, a heater warms {relation} and lets it equilibrate {value} {unit} above its "
                         "starting temperature.", nonnumeric_fill="a few kelvin"),
           1: dict(frame="{relation} {value} {unit} above its starting temperature.",
                   r_attach="Before the molecules are examined, a heater warms the gas and lets it equilibrate",
                   d_attach="In an earlier run, a heater warmed the gas and let it equilibrate", nonnumeric_fill="a few kelvin")},
    note="R/D/N reworded: the stated 300 K is the starting temperature, the heater warms the gas before the energy is evaluated and "
         "the gas equilibrates at the raised temperature (one reading, the certified one: the gas at 338 K for the 38 K value).")
CHANGES["S227"] = (
    ("claude high: T5974[R1] 'Before the molecules equilibrate, a heater has warmed the gas by a further 38 K' contradicts the "
     "stated equilibrium at 300 K",
     "R1 now 'Before the molecules are examined, a heater warms the gas and lets it equilibrate 38 K above its starting "
     "temperature.' (the 300 K is the starting temperature; equilibrium holds at the raised temperature)."),
    ("gpt high: T4CBB[R0] ongoing heating without saying the energy is evaluated after the whole increase and equilibration",
     "R0 now 'Before the energy is evaluated, a heater warms the gas and lets it equilibrate 38 K above its starting "
     "temperature.'; D0 '... warms the water bath and lets it equilibrate 38 K above its starting temperature.'"),
    ("D0/N0/R0 slightly artificial: 'is then warming ... by a further 38 K'",
     "replaced as above; N0 '... a few kelvin above ...', N1 'In an earlier run, a heater warmed the gas and let it equilibrate a "
     "few kelvin above its starting temperature.'"),
)

# --- S230: D0 / N0 / R1 artificial ----------------------------------------------------------------------------------------------------
FIXED["S230"] = _fix(
    "S230",
    pairs={0: dict(frame="Before the blocks touch, a further {value} {unit} of the same metal, at the temperature of the hotter block, "
                         "is {relation}.",
                   r_attach="joined to the hotter block", d_attach="placed in the warming cabinet"),
           1: dict(frame="{relation} a further {value} {unit} of the same metal at the same temperature.",
                   r_attach="Just before the blocks touch, the hotter block takes on",
                   d_attach="In an earlier run, the hotter block took on")},
    scene_clause="A warming cabinet stands beside the enclosure, and no heat passes between the cabinet and the enclosure.",
    scene_object_rationale="A warming cabinet is a vessel for keeping metal warm outside the enclosure; metal placed in it is not part "
                           "of either block, so the masses and temperatures of the two blocks are the stated ones.",
    scene_refs=("warming cabinet",),
    note="the co-present object is a warming cabinet (metal at the hotter block's temperature is plausibly kept there; the casting "
         "mould made D0 implausible); R0 states the timing ('Before the blocks touch'); pair-1 R/D reworded ('takes on').")
CHANGES["S230"] = (
    ("D0/N0 rated artificial: 'poured into the mould' (metal at 360 K is solid)",
     "scene clause now 'A warming cabinet stands beside the enclosure ...'; D0 '... is placed in the warming cabinet.'"),
    ("R1 rated artificial: 'Before the blocks touch, the hotter block also includes a further 1.1 kg of the same metal.' "
     "contradicts the stated 2 kg",
     "R1 now 'Just before the blocks touch, the hotter block takes on a further 1.1 kg of the same metal at the same temperature.'; "
     "D1 'In an earlier run, the hotter block took on ...' (was 'For an earlier run only, ... also included ...')."),
    ("claude low: T8625[R0] does not say when the further metal is added",
     "R0 now 'Before the blocks touch, a further 1.1 kg of the same metal, at the temperature of the hotter block, is joined to "
     "the hotter block.'"),
)

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 1: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
