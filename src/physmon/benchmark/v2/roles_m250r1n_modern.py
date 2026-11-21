"""M250 repair round 1 (journal J15.1-059) of `roles_m250n_modern`: the specs the two-judge panel rejected (any high flag) or whose sentences the
blind naturalness rater rated artificial, repaired; every other spec is the `roles_m250n_modern` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r1/briefs/roles_m250n_modern.md` (built by `scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250/runs/score_two_judges/`). No model output exists on any of these structures, so they may
still be edited (dataset admission standard, preamble). Wording rules 1-8 of `roles_m250n_modern` apply to every changed sentence.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired
(they move to `INFEASIBLE` with the reason and are replaced in a later batch).
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250n_modern as SRC

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

def _pair(sid: str, i: int, **kw):
    return dataclasses.replace(OLD[sid].pairs[i], **kw)


def _fix(sid: str, pairs: dict[int, dict] | None = None, note: str = "", **kw) -> r2.RoleSpecV2:
    old = OLD[sid]
    ps = list(old.pairs)
    for i, fields in (pairs or {}).items():
        ps[i] = dataclasses.replace(ps[i], **fields)
    return dataclasses.replace(old, pairs=tuple(ps), notes=f"{old.notes} M250 r1: {note}", **kw)


# --- S241: the further lamp has the wavelength of the beam; the D0 object is a lit wall chart -------------------------------------
_S241_BOTH = ("every released electron is collected", "falls on the cathode")
FIXED["S241"] = _fix(
    "S241", note="the further lamp has the wavelength of the beam (so the stated release probability applies); D0 object is a wall chart.",
    scene_clause="A wall chart beside the cell is lit by a lamp of its own, and the window of the cell is shielded from that lamp.",
    scene_object_rationale="A wall chart beside the cell is lit by a lamp of its own; light that falls on the chart does not reach the "
                           "cathode, which is behind a shielded window, so the power on the cathode and the current are those of the stated beam.",
    scene_refs=("wall chart",),
    pairs={
        0: dict(frame="A further lamp of the same wavelength as the light supplies {value} {unit} more light power to {relation}.",
                d_attach="the wall chart", conditions_preserved=_S241_BOTH),
        1: dict(frame="{relation} {value} {unit} extra light of the same wavelength onto the cathode.",
                d_attach="During an earlier measurement, a second lamp put"),
    })
CHANGES["S241"] = (
    ("claude+gpt high missing_assumption: R0/R1 second lamp has no stated wavelength or release probability",
     "Both frames now say the added light has the wavelength of the beam: 'A further lamp of the same wavelength as the light supplies "
     "{v} more light power to the cathode.' / 'During this measurement, a second lamp puts {v} extra light of the same wavelength onto "
     "the cathode.' The stated release probability is per photon at 400 nm, so it applies."),
    ("claude medium invalid_numerical_precision (e stated vs CODATA in certified answers)",
     "Not changed: library solver is out of scope; the difference is 0.011 percent, inside the 0.1 percent grading tolerance."),
    ("rating D0 artificial: 'A further lamp supplies 3.4 mW more light power to the dial of the meter.'",
     "Scene clause now has a wall chart lit by its own lamp (shielded from the cell window); D0 'A further lamp of the same wavelength as "
     "the light supplies 3.4 mW more light power to the wall chart.'; N0 follows."),
    ("ratings N0/D1/N1 slightly artificial", "D1/N1 drop 'only': 'During an earlier measurement, a second lamp put ...'."),
)

# --- S242: the further batch is added at the moment of preparation ----------------------------------------------------------------
FIXED["S242"] = _fix(
    "S242", note="R0/D0 state the time of the addition (the moment of preparation), so the certified wiring A2 + q is the only reading.",
    pairs={0: dict(frame="At the moment of preparation, a further {value} {unit} batch of the longer-lived isotope is added to {relation}.",
                   nonnumeric_fill="small")})
CHANGES["S242"] = (
    ("claude+gpt high insufficient_boundary_condition: T45EB[R0] gives no time of the addition",
     "Frame is now 'At the moment of preparation, a further 170 Bq batch of the longer-lived isotope is added to the sample.' (D0: "
     "'... to the waste drum.'; N0: 'a further small batch'), the moment at which the stated activities are given."),
    ("ratings D0/N0/R0 slightly artificial ('Another ... batch' had no antecedent)", "'another' became 'a further', with the time stated."),
)

# --- S243: K sentence says nuclear radius (not an rms charge radius); pair 1 in one tense -------------------------------------------
_s243_k = OLD["S243"].conditional
FIXED["S243"] = _fix(
    "S243", note="K1 'nuclear radius' instead of 'charge radius' (an rms charge radius does not bound the nuclear surface); pair-1 sentences "
                 "end 'on its way to the foil' (one tense).",
    conditional=dataclasses.replace(
        _s243_k, spec=dataclasses.replace(_s243_k.spec, phrasings=(rv.Phrasing("k0", "have a radius of"),
                                                                   rv.Phrasing("k1", "have a nuclear radius of")))),
    pairs={1: dict(frame="{relation} {value} {unit} more kinetic energy to each alpha particle on its way to the foil.",
                   d_attach="For an earlier scattering, an extra accelerating stage gave")})
CHANGES["S243"] = (
    ("gpt high invalid_parameter_domain: K1 'charge radius' (conventionally rms) with regime d > q is not sufficient for the trajectory to be "
     "outside the charge distribution",
     "K1 now reads 'The nuclei of the foil have a nuclear radius of 7.3 fm.' (K0 'have a radius of'): q is the radius of the nucleus, "
     "and d > q means the trajectory stays outside it."),
    ("claude low invalid_numerical_precision", "Not changed (0.011 percent, library solver out of scope)."),
    ("ratings D1/N1 slightly artificial (mixed tenses, 'for an earlier scattering only')",
     "Pair 1 now: 'For this scattering, an extra accelerating stage gives 3.6 MeV more kinetic energy to each alpha particle on its way to "
     "the foil.' / 'For an earlier scattering, ... gave ... on its way to the foil.'"),
)

# --- S245: D0 object is a second beam of molecules; pair-1 sentences in one tense -------------------------------------------------
FIXED["S245"] = _fix(
    "S245", note="D0 object is a second beam of molecules from its own nozzle (the helium-jet D0 was rated artificial); pair 1 ends 'on its "
                 "way to the laser light' (one tense).",
    scene_clause="A second oven beside the first makes a second beam of molecules that passes through a nozzle of its own into another chamber.",
    scene_object_rationale="The molecules of a second oven beside the first pass through their own nozzle into another chamber; a faster "
                           "nozzle there does not change the kinetic energy of the atoms of the beam that meets the laser light.",
    scene_refs=("second beam",),
    pairs={0: dict(r_attach="the atoms of the beam", d_attach="the molecules of the second beam"),
           1: dict(frame="{relation} {value} {unit} more kinetic energy to each atom on its way to the laser light.")})
CHANGES["S245"] = (
    ("rating D0 artificial: 'A faster nozzle adds 0.011 eV to the kinetic energy of the helium jet.'",
     "Scene clause: 'A second oven beside the first makes a second beam of molecules that passes through a nozzle of its own into another "
     "chamber.' D0: 'A faster nozzle adds 0.011 eV to the kinetic energy of the molecules of the second beam.'; N0 follows."),
    ("claude low other: R0 leaves open whether 0.0763 eV includes the increment", "Not changed (the K + q reading is the natural one; low)."),
    ("ratings D1/N1/R1 slightly artificial (mixed tenses)", "Pair 1 ends 'on its way to the laser light' in all four sentences."),
)

# --- S246: pair 1 without the garbled 'for an earlier shield only ... against the wall' ----------------------------------------------
FIXED["S246"] = _fix(
    "S246", note="pair 1 'against its wall' (the wall of the shield named in the attachment) and D1 without 'only'.",
    pairs={1: dict(frame="{relation} {value} {unit} more concrete against its wall.", d_attach="For an earlier shield, the builders laid")})
CHANGES["S246"] = (
    ("rating N1 artificial: 'For an earlier shield only, the builders laid a little more concrete against the wall.'",
     "'For an earlier shield, the builders laid a little more concrete against its wall.' ('its' is that earlier shield's wall); R1 "
     "'For this shield, the builders lay 7.7 cm more concrete against its wall.'; D1 follows."),
)

# --- S247: the added light travels along the beam and is measured like it; pair 1 adds to the intensity of the beam ----------------
FIXED["S247"] = _fix(
    "S247", note="scene clause fixes the direction and the intensity convention of light that a second lamp adds to the beam; R1/D1 add to "
                 "the intensity of the beam.",
    scene_clause="A projection screen hangs on a wall of the laboratory, lit by lamps that do not shine on the mirror. Light that a second "
                 "lamp puts into the beam travels along the beam, and its intensity is measured perpendicular to the beam like that of the "
                 "beam itself.",
    pairs={1: dict(frame="{relation} {value} {unit} to the intensity of the beam.",
                   r_attach="During this exposure, a second lamp adds", d_attach="During an earlier exposure, a second lamp added")})
CHANGES["S247"] = (
    ("gpt high missing_assumption + relevant_variable_removed: R0/R1 give no incidence angle or intensity convention for the second lamp",
     "Scene clause (base context of every cell): 'Light that a second lamp puts into the beam travels along the beam, and its intensity "
     "is measured perpendicular to the beam like that of the beam itself.' R1 now 'During this exposure, a second lamp adds 470 W/m² to "
     "the intensity of the beam.'; R0 unchanged: 'A second lamp adds 470 W/m² to the intensity of the light that reaches the mirror.'"),
    ("claude medium missing_assumption", "Same fix."),
    ("ratings R1/D1/N1 slightly artificial ('illumination onto the mirror' after 'lamps that do not shine on the mirror')",
     "R1/D1/N1 no longer say 'illumination onto the mirror'."),
)

# --- S248: the base problem no longer says that no other field acts at the sample ------------------------------------------------------
_S248_BASE = ("The spin of a free proton precesses about the magnetic field at the sample. That field is uniform, constant and points along the "
              "axis of the magnet, and any field that a coil adds to it points the same way. The magnet gives a field of {B} mT at the sample, "
              "and stray fields are negligible. The magnetic moment of the proton is g e divided by twice m, times its spin angular momentum, "
              "where m is its mass and e is the elementary charge. Take g = {gp}, e = {e} C and m = {mp} kg.")


def _s248_structure() -> gr.Structure:
    base = SRC.STRUCTURE_FACTORIES["S248"]()
    return dataclasses.replace(base, render=dataclasses.replace(base.render, context=_S248_BASE))


STRUCTURE_OVERRIDES["S248"] = _s248_structure
FIXED["S248"] = _fix(
    "S248", pairs={0: dict(conditions_preserved=("free proton", "uniform, constant")),
                   1: dict(conditions_preserved=("free proton", "uniform, constant"))},
    note="the base text no longer says 'no other magnetic field acts there' (it contradicted the R sentences); it says the field is "
                 "uniform, constant and along the magnet axis, that a coil's field points the same way, and that stray fields are negligible. "
                 "Base gold unchanged.")
CHANGES["S248"] = (
    ("claude+gpt high contradictory_distractor_statement: base says 350 mT is the field at the sample and no other field acts there, "
     "R0/R1 add 52 mT there",
     "Base problem replaced (STRUCTURE_OVERRIDES): 'The magnet gives a field of 350 mT at the sample' (no 'no other field acts there'); "
     "'any field that a coil adds to it points the same way' fixes the direction of the added field; 'stray fields are negligible'. "
     "Same gold 14.8979 MHz."),
    ("rating R1 artificial: 'adding 52 mT at the sample contradicts the earlier statement that no other magnetic field acts there'",
     "Statement removed, so R1 'During this measurement, a second coil gives 52 mT more field at the sample.' no longer contradicts the base."),
)

# --- S249: the protons leave the source with the stated energy; the gap acts between source and magnet --------------------------------
_S249_BASE = ("Protons leave an ion source with a kinetic energy of {K} MeV and are injected, perpendicular to a uniform, constant magnetic field "
              "of {B} T, into a magnet, and then move on circular orbits; no electric field acts on them after injection. Use relativistic "
              "mechanics, with momentum γ m v, and neglect radiation. Take m = {m} kg, e = {e} C and c = {c} km/s.")


def _s249_structure() -> gr.Structure:
    base = SRC.STRUCTURE_FACTORIES["S249"]()
    return dataclasses.replace(base, render=dataclasses.replace(base.render, context=_S249_BASE))


STRUCTURE_OVERRIDES["S249"] = _s249_structure
FIXED["S249"] = _fix(
    "S249", note="the base text says the protons LEAVE the source with the stated energy and are then injected, so a gap between source and "
                 "magnet gives K + q at injection with one reading; pair sentences end 'before they are injected' / 'on its way into the field'.",
    pairs={0: dict(frame="A further accelerating gap adds {value} {unit} to the kinetic energy of {relation} before they are injected.",
                   r_attach="the protons from the source", d_attach="the deuterons from the second ion source"),
           1: dict(frame="{relation} {value} {unit} more kinetic energy to each proton on its way into the field.")})
CHANGES["S249"] = (
    ("gpt high missing_assumption: K -> K + q needs the stated 100 MeV to be the energy before the gap, but the base says energy at injection",
     "Base problem replaced (STRUCTURE_OVERRIDES): 'Protons leave an ion source with a kinetic energy of 100 MeV and are injected ... into a "
     "magnet'. R0 'A further accelerating gap adds 75 MeV to the kinetic energy of the protons from the source before they are injected.'; "
     "R1 '... gives 75 MeV more kinetic energy to each proton on its way into the field.' Same gold 16.5271 MHz."),
    ("ratings D1/N1/R0 slightly artificial (mixed tenses, 'for an earlier injection only')",
     "Pair 1 in one tense ('on its way into the field'), D1 'For an earlier injection only, ...' kept as the earlier-run anchor."),
)

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 1: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
