"""M250 repair round 1 (journal J15.1-059) of `roles_m250n_qastro`: the specs the two-judge panel rejected (any high flag) or whose sentences the
blind naturalness rater rated artificial, repaired; every other spec is the `roles_m250n_qastro` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r1/briefs/roles_m250n_qastro.md` (built by `scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250/runs/score_two_judges/`). No model output exists on any of these structures, so they may
still be edited (dataset admission standard, preamble). Wording rules 1-8 of `roles_m250n_qastro` apply to every changed sentence.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired
(they move to `INFEASIBLE` with the reason and are replaced in a later batch).
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250n_qastro as SRC

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

P = rv.Phrasing
Pair = r2.PhrasePair


def _note(sid: str, text: str) -> str:
    return f"{OLD[sid].notes} M250 r1: {text}".strip()


def _rep(structure_id: str, pair_index: int, **changes) -> r2.PhrasePair:
    return dataclasses.replace(OLD[structure_id].pairs[pair_index], **changes)


def _context_override(sid: str, edits: tuple[tuple[str, str], ...], formats: dict[str, str] | None = None):
    def factory() -> gr.Structure:
        base = SRC.STRUCTURE_FACTORIES[sid]()
        context = base.render.context
        for old, new in edits:
            assert old in context, (sid, old)
            context = context.replace(old, new)
        render = dataclasses.replace(base.render, context=context, formats={**base.render.formats, **(formats or {})})
        return dataclasses.replace(base, render=render)

    return factory


# --- S273: N1 (an 'earlier capture' of the single muon is incoherent); GPT: K reference expression unjustified -> K removed -----------

_S273_P0 = _rep("S273", 0, frame="An accelerating gap adds {value} {unit} to the kinetic energy of {relation}.")
_S273_P1 = _rep("S273", 1, frame="{relation} {value} {unit} more kinetic energy before capture.",
                r_attach="In this capture, an accelerating gap gives the muon",
                d_attach="In an earlier capture only, an accelerating gap gave another muon",
                d_rationale="The gap gave another muon its energy in an earlier capture, which is over; in the capture of the question the muon "
                            "has the stated kinetic energy relative to the nucleus.")
FIXED["S273"] = dataclasses.replace(
    OLD["S273"], quantity_phrase="an accelerating gap", pairs=(_S273_P0, _S273_P1), conditional=None,
    notes=_note("S273", "K (radius of the nucleus) removed: its out-of-regime reference replaced the orbit radius by the nuclear radius without "
                        "physical justification (see NO_K); 'a further' dropped from the gap sentences; pair 1 now reads 'In this capture, an "
                        "accelerating gap gives the muon ... more kinetic energy before capture' / 'In an earlier capture only, ... gave another "
                        "muon ...' (the single muon of the question has no earlier capture)."))
NO_K["S273"] = ("The nuclear radius enters only through the point-charge premise; an out-of-regime law for a muon orbit comparable with the nucleus "
                "would need the charge distribution of the nucleus (levels inside the nucleus), and no honest closed-form reference exists.")
K_KINDS.pop("S273", None)
CHANGES["S273"] = (
    ("claude blind rating N1 artificial: 'For an earlier capture only, ... gave a little more kinetic energy to the muon before the capture.' (earlier capture of the single muon incoherent)",
     "pair 1 D/N now give the energy to 'another muon' in 'an earlier capture only'; N1: 'In an earlier capture only, an accelerating gap gave another muon a little more kinetic energy before capture.'; R1: 'In this capture, an accelerating gap gives the muon {v} eV more kinetic energy before capture.'"),
    ("gpt high other: claimed outside-regime reference expression substitutes the nuclear radius for the Bohr orbital radius without justification",
     "K quantity (radius of the nucleus) removed (conditional=None); reason recorded in NO_K['S273']; K_KINDS entry removed"),
    ("gpt high rendering_not_minimal (N sentences omit 116 eV)", "5.3b judge error, N sentences numeral-free by design; kept"),
    ("slightly_artificial R0/D0/N0/R1/D1 ('a further accelerating gap' refers to nothing earlier)",
     "'A further accelerating gap adds ...' -> 'An accelerating gap adds ...'"),
)

# --- S274 ---------------------------------------------------------------------------------------------------------------------------

_S274_SCENE = ("A small compass lies on the bench outside the gap of the magnet, far from the vapour, and a field applied at the compass "
               "does not reach the vapour.")
_S274_P0 = _rep("S274", 0, d_rationale="A second coil that is placed at the compass adds field there; the compass is far from the vapour and "
                                       "no field applied at the compass reaches it, so the field at the vapour is the stated one.")
_S274_P1 = _rep("S274", 1, frame="{relation} {value} {unit} to the magnetic field at the vapour.",
                r_attach="In this measurement, a second coil adds", d_attach="In an earlier measurement only, a second coil added")
FIXED["S274"] = dataclasses.replace(
    OLD["S274"], scene_clause=_S274_SCENE,
    scene_object_rationale="A compass on the bench is far from the vapour and a field applied at the compass does not reach the vapour; a coil "
                           "that acts on the compass changes the field at the compass only, so the field at the vapour is the stated one.",
    pairs=(_S274_P0, _S274_P1),
    notes=_note("S274", "base text: 'longer-wavelength' -> 'shorter-wavelength' (P3/2 to S1/2 is the D2 line) and the joule-electronvolt relation "
                        "stated; scene clause states that a field applied at the compass does not reach the vapour; pair 1 reads 'a second coil "
                        "adds {v} to the magnetic field at the vapour'."))
STRUCTURE_OVERRIDES["S274"] = _context_override(
    "S274",
    (("emits the longer-wavelength line", "emits the shorter-wavelength line"),
     ("Take e = {e} C,", "One electronvolt is the elementary charge times one volt. Take e = {e} C,")))
CHANGES["S274"] = (
    ("gpt high other: the P3/2 to S1/2 transition is the shorter-wavelength member, contradicting 'longer-wavelength'",
     "STRUCTURE_OVERRIDES['S274']: 'emits the longer-wavelength line' -> 'emits the shorter-wavelength line' (gold unchanged)"),
    ("gpt high inconsistent_units: relations give joules but divide by hc in eV nm",
     "base text adds 'One electronvolt is the elementary charge times one volt.' so the conversion between joule and electronvolt is stated"),
    ("gpt high hidden_coupling and missing_assumption: a coil at the compass could also produce a field at the vapour",
     "scene clause: 'A small compass lies on the bench outside the gap of the magnet, far from the vapour, and a field applied at the compass does not reach the vapour.'"),
    ("blind ratings slightly_artificial R1/D1/N1 ('gives 55 mT more field' stilted)",
     "R1: 'In this measurement, a second coil adds 55 mT to the magnetic field at the vapour.'; D1: 'In an earlier measurement only, a second coil added ...'"),
)

# --- S275 ---------------------------------------------------------------------------------------------------------------------------

_S275_P0 = _rep("S275", 0, frame="The right-hand edge of {relation} is moved {value} {unit} farther to the right.",
                r_attach="the slice in which the probe responds", d_attach="the metal strip on the second chip",
                nonnumeric_fill="a little",
                d_rationale="Moving the edge of the metal strip on the second chip does not change the probe or the well; the slice in which the "
                            "probe responds has the stated edges.")
_S275_P1 = _rep("S275", 1, frame="{relation} {value} {unit} farther to the right.",
                r_attach="Before the position is measured, the right-hand edge of the slice in which the probe responds is moved",
                d_attach="In an earlier measurement only, the right-hand edge of the slice in which the probe responded was moved")
FIXED["S275"] = dataclasses.replace(
    OLD["S275"], quantity_phrase="a further strip",
    scene_clause="A second chip, with a thin metal strip on it, lies on a stage beside the apparatus.",
    scene_object_rationale="A metal strip on a second chip beside the apparatus is not part of the well or of the probe, so the edges of the slice in "
                           "which the probe responds are the stated ones.",
    pairs=(_S275_P0, _S275_P1),
    notes=_note("S275", "the edge that moves is stated (the right-hand edge, farther to the right; the left edge stays at the stated place); "
                        "the second chip carries a thin metal strip whose right-hand edge is moved in D0/N0."))
CHANGES["S275"] = (
    ("claude and gpt high insufficient_boundary_condition: T3E63[R0] does not say which edge is widened",
     "R0: 'The slice in which the probe responds is widened by 0.24 nm more.' -> 'The right-hand edge of the slice in which the probe responds is moved 0.24 nm farther to the right.'"),
    ("blind rating N0 artificial: 'The coating on the second chip is widened by a little more.'",
     "scene: 'A second chip, with a thin metal strip on it, ...'; N0: 'The right-hand edge of the metal strip on the second chip is moved a little farther to the right.'"),
    ("slightly_artificial D0/D1/N1/R1 ('widened by 0.24 nm more')",
     "R1: 'Before the position is measured, the right-hand edge of the slice in which the probe responds is moved 0.24 nm farther to the right.'; D1: 'In an earlier measurement only, the right-hand edge of the slice in which the probe responded was moved ...'"),
)

# --- S276 ---------------------------------------------------------------------------------------------------------------------------

_S276_P0 = _rep("S276", 0, frame="A bias lifts the height of {relation} by {value} {unit}.",
                r_attach="the barrier that the beams strike", d_attach="the potential step at the guard electrode",
                nonnumeric_fill="a small amount")
_S276_P1 = _rep("S276", 1, frame="{relation} the height of the barrier by {value} {unit}.",
                r_attach="During this run, a bias lifts", d_attach="During an earlier run only, a bias lifted",
                nonnumeric_fill="a small amount")
FIXED["S276"] = dataclasses.replace(
    OLD["S276"], quantity_phrase="a bias", pairs=(_S276_P0, _S276_P1), conditional=None,
    notes=_note("S276", "K (thermal energy) removed: the thermal sentences did not tie thermal motion to the prescribed kinetic energy and the "
                        "claimed thermal invariance has no basis in the transmission law (see NO_K); bias sentences reworded ('A bias lifts the "
                        "height of ... by {v}')."))
NO_K["S276"] = ("A thermal spread of the incident energies changes the energy-dependent transmissions even when the barrier is far above the mean "
                "energy, and the premise fixes one kinetic energy for each beam; no regime quantity with an exact in-regime invariance exists.")
K_KINDS.pop("S276", None)
CHANGES["S276"] = (
    ("gpt high missing_assumption: thermal sentences do not relate thermal motion to the prescribed kinetic energy",
     "K quantity (mean thermal energy) removed (conditional=None); reason in NO_K['S276']; K_KINDS entry removed"),
    ("gpt high hidden_coupling: thermal invariance under 8*q < V has no basis in the transmission law",
     "same: K removed"),
    ("slightly_artificial D0/N0 'adds 0.15 eV to the height of the step at the guard electrode'",
     "D0: 'A bias lifts the height of the potential step at the guard electrode by 0.15 eV.'; R0: 'A bias lifts the height of the barrier that the beams strike by 0.15 eV.'"),
    ("slightly_artificial D1/N1/R0 ('a further bias' refers to nothing earlier, stilted)",
     "R1: 'During this run, a bias lifts the height of the barrier by 0.15 eV.'; D1: 'During an earlier run only, a bias lifted the height of the barrier by ...'"),
)

# --- S277 ---------------------------------------------------------------------------------------------------------------------------

_S277_P0 = _rep("S277", 0, frame="{relation} is extended by {value} {unit} at its downstream end.", r_attach="The evacuated tube",
                d_attach="The cooling-water line", nonnumeric_fill="a small amount",
                d_rationale="Extending the cooling-water line adds water pipe, not tube that the pions fly through; the tube has the stated length.")
_S277_P1 = _rep("S277", 1, frame="{relation} {value} {unit} at its downstream end.",
                r_attach="Before the pions are sent in, the tube is extended by", d_attach="For an earlier run only, the tube was extended by",
                nonnumeric_fill="a small amount")
FIXED["S277"] = dataclasses.replace(
    OLD["S277"], pairs=(_S277_P0, _S277_P1),
    notes=_note("S277", "wording only: 'gets 34 m more pipe' -> 'is extended by 34 m at its downstream end' (the tube for R, the cooling-water line for D)."))
CHANGES["S277"] = (
    ("blind rating R0 artificial: 'The flight path of the pions gets 34 m more pipe.'",
     "R0: 'The evacuated tube is extended by 34 m at its downstream end.'"),
    ("blind ratings D0/N0 artificial: 'The cooling-water line gets 34 m more pipe.' / '... gets a little more pipe.'",
     "D0: 'The cooling-water line is extended by 34 m at its downstream end.'; N0: '... is extended by a small amount at its downstream end.'"),
    ("slightly_artificial R1/D1/N1 ('lengthened by 34 m more')",
     "R1: 'Before the pions are sent in, the tube is extended by 34 m at its downstream end.'; D1: 'For an earlier run only, the tube was extended by ...'"),
)

# --- S278 ---------------------------------------------------------------------------------------------------------------------------

_S278_REL = rv.RelevantWiring("Q", "add", "One more particle that carries q of rest energy adds q to the excess of the total rest energy produced, which "
                                          "becomes Q + q.")
_S278_P0 = _rep("S278", 0, frame="{relation} also produces one more particle with {value} {unit} of rest energy.",
                r_attach="The reaction", d_attach="The second target station", nonnumeric_fill="a small amount",
                d_rationale="A particle that the second target station produces is not produced by the reaction of the question; the particles of "
                            "that reaction have the stated excess of rest energy.")
_S278_P1 = _rep("S278", 1, frame="{relation} one more particle with {value} {unit} of rest energy.",
                r_attach="In this reaction, the collision also produces", d_attach="In an earlier reaction only, the collision also produced",
                nonnumeric_fill="a small amount",
                d_rationale="The further particle was produced in an earlier reaction, which is over; the particles of the reaction of the question "
                            "have the stated excess of rest energy.")
FIXED["S278"] = dataclasses.replace(
    OLD["S278"], quantity_phrase="one more particle", relevant=_S278_REL, pairs=(_S278_P0, _S278_P1),
    notes=_note("S278", "base text: 'a group of particles' with the excess 134.98 MeV (digits as in the gold) and 'all the particles that it "
                        "produces' move together; R is one more particle of stated rest energy, so the excess is Q + q."))
STRUCTURE_OVERRIDES["S278"] = _context_override(
    "S278",
    (("The reaction produces final particles whose total rest energy", "The reaction produces a group of particles whose total rest energy"),
     ("so that the final particles move together", "so that all the particles that it produces move together")),
    formats={"m1": ".5g", "m2": ".5g", "Q": ".6g"})
CHANGES["S278"] = (
    ("gpt high failed_transformation_identity: certified answers do not follow from the displayed inputs beyond rounding",
     "base text now displays Q = 134.98 MeV and the rest energies 938.27 MeV (formats .6g/.5g), the values that the gold uses; gold unchanged"),
    ("gpt high other and claude medium: 'the final particles carry 104 MeV more rest energy' has no reference for 'more'",
     "R is now one more particle: R1 'In this reaction, the collision also produces one more particle with 104 MeV of rest energy.' (base: 'a group of particles whose total rest energy exceeds ... by 134.98 MeV'); the excess becomes Q + q with one reading"),
    ("blind ratings D0/D1/R0/N0/R1 artificial",
     "D0: 'The second target station also produces one more particle with 104 MeV of rest energy.'; D1: 'In an earlier reaction only, the collision also produced one more particle ...'; R0: 'The reaction also produces one more particle ...'"),
)

# --- S279 ---------------------------------------------------------------------------------------------------------------------------

_S279_P0 = _rep("S279", 0, frame="The radius of {relation} is made {value} {unit} larger.",
                r_attach="the circle on which the source moves", d_attach="the pulley of the vacuum pump", nonnumeric_fill="a little")
_S279_P1 = _rep("S279", 1, frame="{relation} {value} {unit} larger, at the same rotation frequency.",
                r_attach="Before the shift is measured, the radius of the circle on which the source moves is made",
                d_attach="For an earlier run only, the radius of the circle on which the source moved was made", nonnumeric_fill="a little")
FIXED["S279"] = dataclasses.replace(
    OLD["S279"], pairs=(_S279_P0, _S279_P1),
    notes=_note("S279", "wording only: 'gets 3.7 cm more' / 'has grown by 3.7 cm more in rim radius' -> 'is made 3.7 cm larger'."))
CHANGES["S279"] = (
    ("blind ratings R0/D0/N0 artificial: 'The radius of ... gets 3.7 cm more.'",
     "R0: 'The radius of the circle on which the source moves is made 3.7 cm larger.'; D0: 'The radius of the pulley of the vacuum pump is made 3.7 cm larger.'; N0: '... is made a little larger.'"),
    ("blind ratings R1/D1/N1 artificial: 'the rotor ... has grown by 3.7 cm more in rim radius'",
     "R1: 'Before the shift is measured, the radius of the circle on which the source moves is made 3.7 cm larger, at the same rotation frequency.'; D1: 'For an earlier run only, the radius of the circle on which the source moved was made ...'"),
)

# --- S280 ---------------------------------------------------------------------------------------------------------------------------

_S280_C = dataclasses.replace(
    OLD["S280"].cancelling,
    spec=dataclasses.replace(OLD["S280"].cancelling.spec, phrasings=(P("c0", "has a mass of"), P("c1", "has a total mass of"))))
_S280_P0 = _rep("S280", 0, frame="The altitude of {relation} is increased by {value} {unit}.",
                r_attach="the initial circular orbit", d_attach="the orbit of the relay satellite", nonnumeric_fill="a small amount")
_S280_P1 = _rep("S280", 1, frame="{relation} {value} {unit}.",
                r_attach="Before the first burn, the altitude of the initial circular orbit is increased by",
                d_attach="For an earlier flight only, the altitude of the initial circular orbit was increased by", nonnumeric_fill="a small amount")
FIXED["S280"] = dataclasses.replace(
    OLD["S280"], cancelling=_S280_C, conditional=None, pairs=(_S280_P0, _S280_P1),
    notes=_note("S280", "K (burn duration) removed: no universal additive correction dv + g1 t exists for a finite burn (see NO_K); 'gets 470 km "
                        "more' -> 'the altitude of ... is increased by 470 km'; C1 'has a total mass of'."))
NO_K["S280"] = ("A finite burn has no universal correction to the change of speed; its effect depends on the thrust profile and the turning of the "
                "velocity during the burn, so no honest closed-form out-of-regime reference exists for the duration of a burn.")
K_KINDS.pop("S280", None)
CHANGES["S280"] = (
    ("gpt high other: dv + v1**2/r1*q is not a universal correction for a finite burn",
     "K quantity (burn duration) removed (conditional=None); reason in NO_K['S280']; K_KINDS entry removed"),
    ("blind ratings R0/D0/N0 artificial: 'The altitude of ... gets 470 km more.'",
     "R0: 'The altitude of the initial circular orbit is increased by 470 km.'; D0: 'The altitude of the orbit of the relay satellite is increased by 470 km.'; N0: '... is increased by a small amount.'"),
    ("blind rating R1 artificial: 'the initial circular orbit is placed 470 km higher still'",
     "R1: 'Before the first burn, the altitude of the initial circular orbit is increased by 470 km.'; D1: 'For an earlier flight only, the altitude of the initial circular orbit was increased by 470 km.'"),
    ("slightly_artificial C1 'has been weighed at'", "C1: 'The spacecraft has a total mass of 1400 kg.'"),
)

# --- S281 ---------------------------------------------------------------------------------------------------------------------------

_S281_P0 = _rep("S281", 0, frame="{relation} accretes rock of the same density, gaining {value} {unit} of radius.",
                r_attach="The planet", d_attach="The moon", nonnumeric_fill="a small amount",
                d_rationale="Rock that the moon accretes changes the moon and not the planet; the planet keeps its stated radius and density.")
_S281_P1 = _rep("S281", 1, frame="{relation} rock of the same density, gaining {value} {unit} of radius.",
                r_attach="Before the probe is launched, the planet accretes", d_attach="For an earlier simulation only, the planet accreted",
                nonnumeric_fill="a small amount")
FIXED["S281"] = dataclasses.replace(
    OLD["S281"], quantity_phrase="accreted rock", pairs=(_S281_P0, _S281_P1),
    scene_clause="A moon circles the planet.",
    notes=_note("S281", "the added radius is now accreted rock of the same density ('accretes rock of the same density, increasing its radius by "
                        "310 km'), replacing 'a further layer of rock ... adds 310 km to the radius'; the moon accretes in D0/N0."))
CHANGES["S281"] = (
    ("blind ratings R0/R1/D0/N0 artificial: 'A further layer of rock of the same density adds 310 km to the radius of the planet/moon.'",
     "R0: 'The planet accretes rock of the same density, gaining 310 km of radius.'; D0: 'The moon accretes rock of the same density, gaining 310 km of radius.'; R1: 'Before the probe is launched, the planet accretes rock of the same density, gaining 310 km of radius.'"),
    ("slightly_artificial D1/N1 'given 310 km more radius'",
     "D1: 'For an earlier simulation only, the planet accreted rock of the same density, gaining 310 km of radius.'"),
)

# --- S282 ---------------------------------------------------------------------------------------------------------------------------

_S282_P0 = _rep("S282", 0, frame="The radius of {relation} is increased by {value} {unit} of the radius of the Sun.",
                r_attach="the radiating star", d_attach="the dust disc rim", nonnumeric_fill="a small part")
_S282_P1 = _rep("S282", 1, frame="{relation} {value} {unit} of the radius of the Sun, with the peak wavelength unchanged.",
                r_attach="Before the luminosity is evaluated, the radius of the star is increased by",
                d_attach="For an earlier observation only, the radius of the star was increased by", nonnumeric_fill="a small part")
FIXED["S282"] = dataclasses.replace(
    OLD["S282"], quantity_phrase="an increase of the radius", pairs=(_S282_P0, _S282_P1),
    notes=_note("S282", "the unit text 'in solar radii' is no longer a dangling tail: the sentences read 'increased by 0.74 of the radius of the "
                        "Sun' and the N control 'increased by a small part of the radius of the Sun'."))
CHANGES["S282"] = (
    ("gpt high other: the numeral-free twin_note claims state that number and unit were replaced, but the N sentences keep 'in solar radii'",
     "the N sentences keep no stray unit: R0 'The radius of the star is increased by 0.74 of the radius of the Sun.'; N0 'The radius of the dust disc rim is increased by a small part of the radius of the Sun.' (the tail is the rest of the sentence, not a unit)"),
    ("blind ratings R0/D0/N0 artificial 'gets 0.74 more, in solar radii'", "see R0/D0/N0 above"),
    ("blind ratings R1/D1/N1 artificial 'has swollen by 0.74 more, in solar radii'",
     "R1: 'Before the luminosity is evaluated, the radius of the star is increased by 0.74 of the radius of the Sun, with the peak wavelength unchanged.'; D1: 'For an earlier observation only, the radius of the star was increased by ...'"),
)


ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 1: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
