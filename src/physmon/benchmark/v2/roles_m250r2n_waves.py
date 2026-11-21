"""M250 repair round 2 (journal J15.1-061) of `roles_m250r1n_waves`: the specs the two-judge re-review rejected (any high flag) or whose sentences
the blind naturalness rater rated artificial, repaired again; every other spec is the `roles_m250r1n_waves` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r2/briefs/roles_m250r1n_waves.md` (`scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250r1/runs/score_two_judges/`). No model output exists on any of these structures. The round-1
history of each structure is in `roles_m250r1n_waves.CHANGES`; wording rules 1-8 of the original module apply.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired.
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250r1n_waves as SRC

OLD: dict[str, r2.RoleSpecV2] = dict(SRC.ROLE_SPECS)
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

def _note(sid: str, text: str) -> str:
    return f"{OLD[sid].notes} M250 r2: {text}".strip()


def _pair(sid: str, i: int, **kw):
    return dataclasses.replace(OLD[sid].pairs[i], **kw)


# --- S231 --------------------------------------------------------------------------------------------------------------------------
# Both judges: the trolley's own velocity is not stated, so the 3 m/s relative to the trolley is not an air-frame speed. The scene
# clause now says the trolley stands still unless it is said to move (R says it moves), so the base reading is unique.
FIXED["S231"] = dataclasses.replace(
    OLD["S231"],
    scene_clause="The wall rides on a flat trolley, and the speed given for the wall is the speed it has relative to the trolley, "
                 "which stands still on the floor unless it is said to move. A conveyor belt carries parcels along the floor beside "
                 "the loudspeaker; it stirs no air, which stays still throughout.",
    notes=_note("S231", "scene clause states that the trolley stands still unless it is said to move, so the stated speed is the "
                        "wall's speed in the air in the base problem and the trolley speed of R adds to it."))
CHANGES["S231"] = (
    ("claude high / gpt high insufficient_boundary_condition: the trolley's velocity is never stated, the 3 m/s is relative to it",
     "Scene clause: 'the speed given for the wall is the speed it has relative to the trolley, which stands still on the floor "
     "unless it is said to move' (old: no statement about the trolley's own motion); R0/R1 say it moves at 1.4 m/s."),
    ("gpt high relevant_variable_removed_from_equation: the relations use v as the air-frame speed without the trolley velocity",
     "Same clause: with the trolley at rest in the base problem v is the air-frame speed, and R adds the trolley speed."),
    ("rated slightly_artificial D1/N1 'in an earlier run'", "Kept ('in an earlier run' states the earlier run plainly); wording unchanged."),
)

# --- S232 --------------------------------------------------------------------------------------------------------------------------
# GPT high: R1 does not identify the tank, and the pluperfect allows the stated 0.0728 N/m to include the reduction.
_S232_P1 = _pair("S232", 1, frame="{relation}, detergent reduced the surface tension of the water in the tank by {value} {unit}.",
                 r_attach="Before the ripples were made", d_attach="In an earlier run")
FIXED["S232"] = dataclasses.replace(
    OLD["S232"], pairs=(OLD["S232"].pairs[0], _S232_P1),
    scene_clause="A washing-up bowl of water stands on the bench beside the tank, and no tube or channel joins them. The surface "
                 "tension given is that of the clean water in the tank, before any detergent is added to it.",
    notes=_note("S232", "scene clause: the surface tension given is that of the clean water in the tank; R1/D1 name the tank and "
                        "say 'Before the ripples were made' / 'In an earlier run'."))
CHANGES["S232"] = (
    ("gpt high insufficient_boundary_condition: R1 does not establish that the stated surface tension precedes the reduction, nor "
     "name the tank (claude medium: same)",
     "Scene clause 'The surface tension given is that of the clean water in the tank, before any detergent is added to it.'; R1 "
     "'Before the ripples were made, detergent reduced the surface tension of the water in the tank by 0.015 N/m.' (old: 'Detergent "
     "had reduced the surface tension of the water by 0.015 N/m before the ripples were made.')."),
    ("rated slightly_artificial D1/N1 'for an earlier run only' (which water unclear)",
     "'In an earlier run, detergent reduced the surface tension of the water in the tank by 0.015 N/m.'"),
)

# --- S233 --------------------------------------------------------------------------------------------------------------------------
# GPT high: R0 does not place the amplifier before the first glass surface. N0 rated artificial (pointless action on the second laser).
_S233_P0 = _pair("S233", 0, frame="Before any light reaches the block, an optical amplifier adds {value} {unit} to the power of "
                                  "{relation}.")
FIXED["S233"] = dataclasses.replace(
    OLD["S233"], pairs=(_S233_P0, OLD["S233"].pairs[1]),
    scene_clause="The beam leaves a laser fixed to the bench, and the power given for it is the power at the laser. A second laser "
                 "stands on the bench beside the block, turned away from it, for use in another experiment. The beam is narrow "
                 "and parallel.",
    notes=_note("S233", "R0/D0 start 'Before any light reaches the block' so the amplifier acts before the first surface; the "
                        "second laser is for another experiment (purpose for the D object)."))
CHANGES["S233"] = (
    ("gpt high insufficient_boundary_condition: R0 does not place the amplifier before the first glass surface",
     "R0 'Before any light reaches the block, an optical amplifier adds 3.4 mW to the power of the beam.' (old: 'An optical "
     "amplifier adds 3.4 mW to the power of the beam.')."),
    ("rated artificial N0 / slightly_artificial D0 'An optical amplifier adds ... to the power of the second laser' (pointless)",
     "Scene clause gives the second laser a purpose ('for use in another experiment'); D0/N0 'Before any light reaches the block, an "
     "optical amplifier adds 3.4 mW / a small amount to the power of the second laser.'"),
    ("rated slightly_artificial R0", "Rewritten as above (timing stated, plain wording)."),
)

# --- S234 --------------------------------------------------------------------------------------------------------------------------
# GPT high: C1 'drawn to a diameter' can change the rod length (rephrased as a plain cross-section). R0 rated artificial (extends the
# rod right after its length is fixed): the length given is now the length as first cut.
_S234_C = OLD["S234"].cancelling
S234_C = dataclasses.replace(
    _S234_C, spec=dataclasses.replace(
        _S234_C.spec, phrasings=(rv.Phrasing("c0", "has a diameter of"),
                                 rv.Phrasing("c1", "has a circular cross-section of diameter"))))
_S234_P0 = _pair("S234", 0, frame="The {relation} is lengthened by {value} {unit} of the same glass, joined on in line with it, "
                                  "before the pulse is sent.")
_S234_P1 = _pair("S234", 1, frame="{relation}, the rod was lengthened by {value} {unit} of the same glass, joined on in line with it.",
                 r_attach="Before the pulse was sent", d_attach="For an earlier run only")
FIXED["S234"] = dataclasses.replace(
    OLD["S234"], cancelling=S234_C, pairs=(_S234_P0, _S234_P1),
    scene_clause="A coil of optical cable lies on the bench beside the rod, and no light passes between them. The glass is not "
                 "dispersive. The length given for the rod is its length as first cut.",
    notes=_note("S234", "C1 phrased as a circular cross-section (no change of length); the length given is the length as first cut, "
                        "R/D 'lengthened' and timed before the pulse."))
CHANGES["S234"] = (
    ("gpt high insufficient_boundary_condition / hidden_coupling: C1 'The rod is drawn to a diameter of 2.5 cm' can change the length",
     "C1 now 'The rod has a circular cross-section of diameter 2.5 cm.' (a description that fixes no change of length)."),
    ("rated artificial R0 'The rod is extended by 1.3 m ...' right after fixing its length",
     "Scene clause 'The length given for the rod is its length as first cut.'; R0 'The rod is lengthened by 1.3 m of the same glass, "
     "joined on in line with it, before the pulse is sent.'; R1 'Before the pulse was sent, the rod was lengthened by 1.3 m of the same "
     "glass, joined on in line with it.'"),
    ("rated slightly_artificial D1/N1 'for an earlier run only'", "'In an earlier run, the rod was lengthened by ...'"),
)

# --- S238 --------------------------------------------------------------------------------------------------------------------------
# GPT high: the K outside-regime reference does not describe the power after the onset of secondary flow: K removed.
# GPT medium: 'this rate' is ambiguous after the speed is raised: the question asks for the power at the rotor's final rate.
NO_K["S238"] = ("The power after the onset of vortices is not P (q/rot)^2 or any simple law of the stated rate, so no separated "
                "outside-regime reference exists; the regime is the stated steady laminar purely circular flow.")
K_KINDS.pop("S238", None)


def _s238_base() -> gr.Structure:
    s = SRC.STRUCTURE_FACTORIES["S238"]()
    return dataclasses.replace(s, render=dataclasses.replace(s.render, question="What power is needed to keep the rotor turning at "
                                                                              "its final rate?"))


STRUCTURE_OVERRIDES["S238"] = _s238_base
_S238_P1 = _pair("S238", 1, frame="{relation}, the speed setting of the rotor was raised by {value} {unit}.",
                 r_attach="Before the power was measured", d_attach="In an earlier run")
FIXED["S238"] = dataclasses.replace(
    OLD["S238"], conditional=None, pairs=(OLD["S238"].pairs[0], _S238_P1),
    scene_clause="A magnetic stirrer on the bench beside the cylinder mixes a beaker of water for another experiment. The oil is Newtonian and "
                 "moves only in circles about the axis; it stays at one temperature, and its viscosity stays constant. The rate "
                 "given for the rotor is the rate at which it first runs.",
    notes=_note("S238", "K removed (see NO_K); the question asks for the power at the rotor's final rate; the stirrer mixes a beaker of water"
                        "beaker for another experiment; R1/D1 'Before the power was measured' / 'In an earlier run'."))
CHANGES["S238"] = (
    ("gpt high failed_transformation_identity: the K reference P (q/rot)^2 does not describe the power after the onset of secondary "
     "flow",
     "K removed; NO_K['S238'] gives the reason."),
    ("gpt medium other: 'this rate' can be the original 120 rpm or the raised 195 rpm",
     "Question now 'What power is needed to keep the rotor turning at its final rate?' (old: '... at this rate?')."),
    ("rated slightly_artificial D0/N0 (purposeless stirrer)", "Scene clause: the stirrer 'mixes a beaker of water for another experiment'."),
    ("rated slightly_artificial D1/N1 'for an earlier run only'",
     "'In an earlier run, the speed setting of the rotor was raised by 75 rpm.' / R1 'Before the power was measured, ...'."),
)

# --- S240 --------------------------------------------------------------------------------------------------------------------------
# R0 rated artificial: replacing the siphon liquid alone is incoherent while the reservoir holds the same liquid (claude low as well).
_S240_P0 = _pair("S240", 0, r_attach="the siphon and reservoir",
                 d_rationale="Replacing the liquid in the beaker changes the contents of the beaker only; the liquid in the siphon "
                             "and the reservoir, and so the pressure at the highest point, are those of the stated liquid.")
_S240_P1 = _pair("S240", 1, frame="{relation}, the liquid in the siphon and the reservoir was replaced by one of {value} {unit} "
                                  "density.", r_attach="Before the flow began", d_attach="For an earlier run only")
FIXED["S240"] = dataclasses.replace(
    OLD["S240"], pairs=(_S240_P0, _S240_P1),
    notes=_note("S240", "R replaces the liquid in the siphon and the reservoir together (both held the same liquid); R1/D1 "
                        "'Before the flow began' / 'In an earlier run'."))
CHANGES["S240"] = (
    ("rated artificial R0 'The liquid in the siphon is replaced by one of 1180 kg/m3 density' (siphon alone, reservoir-fed)",
     "R0 'The liquid in the siphon and reservoir is replaced by one of 1180 kg/m3 density.'; also resolves claude low (indirect "
     "wording)."),
    ("rated slightly_artificial R1/D1/N1",
     "R1 'Before the flow began, the liquid in the siphon and the reservoir was replaced by one of 1180 kg/m3 density.'; D1 'In an "
     "earlier run, ...'"),
)


ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 2: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
