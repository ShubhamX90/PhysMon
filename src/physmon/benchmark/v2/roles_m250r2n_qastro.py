"""M250 repair round 2 (journal J15.1-061) of `roles_m250r1n_qastro`: the specs the two-judge re-review rejected (any high flag) or whose sentences
the blind naturalness rater rated artificial, repaired again; every other spec is the `roles_m250r1n_qastro` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r2/briefs/roles_m250r1n_qastro.md` (`scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250r1/runs/score_two_judges/`). No model output exists on any of these structures. The round-1
history of each structure is in `roles_m250r1n_qastro.CHANGES`; wording rules 1-8 of the original module apply.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired.
"""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250r1n_qastro as SRC

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

import dataclasses  # noqa: E402

from physmon.benchmark.v2 import rolevalue as rv  # noqa: E402


def _note(sid: str, text: str) -> str:
    return f"{OLD[sid].notes} M250 r2: {text}".strip()


def _rep(sid: str, pair_index: int, **changes) -> r2.PhrasePair:
    return dataclasses.replace(OLD[sid].pairs[pair_index], **changes)


def _ctx(sid: str, edits: tuple[tuple[str, str], ...]):
    def factory() -> gr.Structure:
        base = SRC.STRUCTURE_FACTORIES[sid]()
        context = base.render.context
        for old, new in edits:
            assert old in context, (sid, old)
            context = context.replace(old, new)
        return dataclasses.replace(base, render=dataclasses.replace(base.render, context=context))

    return factory


# --- S274: GPT high: the certified 27.0031 pm follows from the exact SI elementary charge in the eV conversion, not from e = 1.602e-19 C -----------------------
STRUCTURE_OVERRIDES["S274"] = _ctx("S274", (
    ("One electronvolt is the elementary charge times one volt.", "One electronvolt is the elementary charge times one volt, taking the exact SI value of the elementary charge for this "
     "conversion only."),))
FIXED["S274"] = dataclasses.replace(
    OLD["S274"], notes=_note("S274", "base text: the joule-electronvolt relation now uses the exact SI elementary charge (as the certified answer does); with e = 1.602e-19 C it gave 27.0061 pm."))
CHANGES["S274"] = (
    ("gpt high failed_transformation_identity: base result 27.006092 pm, not the certified 27.0031 pm",
     "the base text said 'One electronvolt is the elementary charge times one volt', which with the stated e = 1.602e-19 C gives 27.0061 pm; "
     "it now says '... taking the exact SI value of the elementary charge for this conversion only' (no numeral; the gold's conversion, 27.0031 pm); gold unchanged"),
)

# --- S275: D0/N0 artificial (the metal strip on an unrelated chip) -> a second probe with a window of its own -------------------------
_S275_P0 = _rep("S275", 0, d_attach="the window of the second probe",
                d_rationale="Moving the edge of the window of the second probe, which reads a neighbouring well, does not change this probe or "
                            "this well; the slice in which the probe responds has the stated edges.")
FIXED["S275"] = dataclasses.replace(
    OLD["S275"], quantity_phrase="a moved edge",
    scene_refs=("second probe",),
    scene_clause="A second probe, mounted on a second chip beside the apparatus, reads a neighbouring well through a window of its own.",
    scene_object_rationale="A second probe on a second chip beside the apparatus reads another well through its own window, so the edges of the "
                           "slice in which the probe responds are the stated ones.",
    pairs=(_S275_P0, OLD["S275"].pairs[1]),
    notes=_note("S275", "scene: a second probe with a window of its own replaces the metal strip; D0/N0 move the right-hand edge of that window."))
CHANGES["S275"] = (
    ("blind rating D0 artificial: 'The right-hand edge of the metal strip on the second chip is moved 0.24 nm farther to the right.'",
     "D0: 'The right-hand edge of the window of the second probe is moved 0.24 nm farther to the right.' (scene: a second probe on the second "
     "chip reads a neighbouring well through a window of its own); same action as R0 on a co-present probe"),
    ("blind rating N0 artificial: '... the metal strip on the second chip is moved a little farther to the right.'",
     "N0: 'The right-hand edge of the window of the second probe is moved a little farther to the right.'"),
)

# --- S279: R0 artificial (restates a radius already given) -> a ring fitted around the disc; GPT precision flag -----------------------
STRUCTURE_OVERRIDES["S279"] = _ctx("S279", (
    ("A source of gamma rays is fixed to the rim of a rotor and moves on a circle of radius {R} cm at a constant rotation frequency of {frot} Hz.",
     "A rotor built on a disc of radius {R} cm turns about its axis at a constant rotation frequency of {frot} Hz. A source of gamma rays is "
     "fixed at the outermost edge of the rotor and moves on a circle about the axis."),))
_S279_P0 = _rep("S279", 0, frame="A ring fitted around {relation} and turning with it adds {value} {unit} to its radius.",
                r_attach="the disc of the rotor", d_attach="the pulley of the vacuum pump", nonnumeric_fill="a little",
                d_rationale="A ring that is fitted around the pulley of the vacuum pump changes the pump and not the rotor; the source moves on a "
                            "circle of the radius of the disc.")
_S279_P1 = _rep("S279", 1, frame="{relation} {value} {unit} to its radius.",
                r_attach="Before the rotor is set turning, a ring fitted around the disc adds",
                d_attach="For an earlier run only, a ring fitted around the disc added", nonnumeric_fill="a little")
FIXED["S279"] = dataclasses.replace(
    OLD["S279"], quantity_phrase="a ring",
    relevant=rv.RelevantWiring("R", "add", "A ring fitted around the disc that adds q to its radius makes the radius of the circle of the source "
                                           "R + q, and the speed of the source and the shift grow in proportion to the radius and to its square."),
    scene_object_rationale="A pulley of a vacuum pump beside the rotor housing is not part of the rotor that carries the source; a ring that is "
                           "fitted around it leaves the radius of the circle on which the source moves as stated.",
    pairs=(_S279_P0, _S279_P1),
    notes=_note("S279", "base text: the stated radius is that of the disc and the source is fixed at the outermost edge of the rotor, so a ring fitted "
                        "around the disc adds to the radius of the circle (no restated value); R sentences 'A ring fitted around the disc of the rotor "
                        "and turning with it adds 3.7 cm to its radius'. The certified 6.7855 MHz is the correct rounding of 6.785498 MHz."))
CHANGES["S279"] = (
    ("blind rating R0 artificial: 'The radius of the circle on which the source moves is made 3.7 cm larger.' (contradicts the stated radius)",
     "base: 12 cm is the radius of the disc and the source sits at the outermost edge of the rotor; R0: 'A ring fitted around the disc of the "
     "rotor and turning with it adds 3.7 cm to its radius.'"),
    ("blind rating D0 artificial: 'The radius of the pulley of the vacuum pump is made 3.7 cm larger.'",
     "D0: 'A ring fitted around the pulley of the vacuum pump and turning with it adds 3.7 cm to its radius.'"),
    ("gpt high invalid_numerical_precision: 6.7855 MHz said to round 6.7855928 MHz",
     "unresolved by wording: 4.1357e-15 eV s, 2.998e8 m/s, 14.4 keV, 600 Hz, R = 15.7 cm give 6.785498 MHz (leading order), which rounds to the "
     "certified 6.7855 MHz; the judge's 6.7855928 could not be reproduced"),
    ("slightly_artificial R1/D1/N1",
     "R1: 'Before the rotor is set turning, a ring fitted around the disc adds 3.7 cm to its radius.'; D1: 'For an earlier run only, a ring fitted "
     "around the disc added 3.7 cm to its radius.'"),
)

# --- S280: R0/R1 artificial -------------------------------------------------------------------------------------------------------
DROPPED["S280"] = ("no honest R quantity: any sentence that adds to the altitude of the initial or final orbit restates or contradicts the stated "
                   "altitude, and a further burn contradicts 'two burns'; no added quantity enters the transfer without changing the premise")

# --- S281: accretion of 310 km is implausible -> a layer of rock covering the body of the planet -----------------------------------
STRUCTURE_OVERRIDES["S281"] = _ctx("S281", (
    ("The planet is a uniform sphere of radius {R} km", "The body of the planet is a uniform sphere of radius {R} km"),))
_S281_P0 = _rep("S281", 0, frame="A layer of rock of the same density covers {relation} and adds {value} {unit} to its radius.",
                r_attach="the body of the planet", d_attach="the moon", nonnumeric_fill="a small amount",
                d_rationale="A layer of rock that covers the moon changes the moon and not the planet; the planet keeps its stated radius and density.")
_S281_P1 = _rep("S281", 1, frame="{relation} {value} {unit} to its radius.",
                r_attach="Before the probe is launched, a layer of rock of the same density covers the body of the planet and adds",
                d_attach="For an earlier simulation only, a layer of rock of the same density covered the body of the planet and added",
                nonnumeric_fill="a small amount")
FIXED["S281"] = dataclasses.replace(
    OLD["S281"], quantity_phrase="a layer of rock",
    relevant=rv.RelevantWiring("R", "add", "A layer of rock of the same density that adds q to the radius of the body of the planet makes the radius "
                                           "R + q with the density unchanged, and the escape speed is proportional to the radius."),
    pairs=(_S281_P0, _S281_P1),
    notes=_note("S281", "base text: 'the body of the planet' is the uniform sphere of the stated radius; R is a layer of rock of the same density "
                        "that covers it (replaces the implausible accretion of 310 km)."))
CHANGES["S281"] = (
    ("blind ratings R0/R1/D0/N0 artificial: accretion of rock gaining 310 km of radius",
     "R0: 'A layer of rock of the same density covers the body of the planet and adds 310 km to its radius.'; R1 'Before the probe is launched, "
     "a layer of rock ... covers the body of the planet and adds 310 km to its radius.'; D0: '... covers the moon and adds 310 km to its radius.'; "
     "base: 'The body of the planet is a uniform sphere of radius 3390 km ...'"),
    ("slightly_artificial D1/N1", "D1: 'For an earlier simulation only, a layer of rock of the same density covered the body of the planet and added 310 km to its radius.'"),
)

# --- S282: R0 high (unstated thermal condition); all R/D/N artificial (a star's radius cannot be 'increased') ------------------------
DROPPED["S282"] = ("a stated added radius needs a thermal condition (peak wavelength unchanged) that makes the star's radius an action nobody performs; "
                   "every wording of an increase of the radius is rated artificial and no added quantity avoids restating the stated 1.71 solar radii")


ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 2: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
