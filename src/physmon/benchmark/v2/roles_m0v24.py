"""M0 v2.4 role specs: M0 v2.3 with the last fixes before the G2 pilot (journal J15.1-048, 2026-11-19).

Both qualified judges reviewed M0 v2.3 (`docs/validation/v2/llm_panel/admission_m0v23/runs/score_two_judges/admission_report.md`):
with the 5.3b guard 10 structures ADMIT and S72 REJECTS; the naturalness raters required rewrites of S26 R1, S55 N1 and S92 N1. No
model output exists on any M0 cell, so the structures are still fixed before any run. Everything else is the M0 v2.3 spec object,
unchanged (S01, S07, S13, S15, S20, S27, S30). Wording rules 1-8 apply; scene clauses are unchanged (physical conditions only), and
no sentence uses meta wording ("given", "stated", "before any ...").

Changes (old -> new wording is in `CHANGES`; the tests check each):

* S72 pair 1 (GPT, correct: an energy gain of the electron after the wavelength determination leaves the determined wavelength
  unchanged, so an honest same-object other event exists): R1 is an extra energy gain of the electron BEFORE the wavelength is
  determined; D1 is the same gain AFTER the wavelength has been determined (`same_object_other_event`, like S30's jug); the pair frame
  is shared and the `d_kind_note` is dropped. Pair 0 (the proton) is unchanged.
* S26 (R1 rated artificial: "than the stated angle of incidence" is meta wording): the order is said in ordinary words, "tilted
  until the angle of incidence had grown by {v}" (R0 the same way: "until its angle of incidence at the interface has grown by {v}");
  no numeral but the cue. "so that" is avoided: the certificate's consequence list rejects it.
* S55 pair 1 (naturalness rewrite of N1; "From the stated temperature" removed): "Once the sample was in equilibrium, a heater warmed it
  by {v} just before the molecular speeds were measured" (R1) / "... in an earlier experiment" (D1, N1), so the order is
  equilibrium, warming, measurement in ordinary words.
* S92 (naturalness rewrite of N1; N0 checked): the numeral-free fill of both pairs is "somewhat greater than the original's"
  ("replaced by one whose density is somewhat greater than the original's"), replacing the vague "different from the original's".

`CERT_VERSION` stays "v2.1": `rolevalue_v2.certify_v2` applies its full rule set only for that `RoleSpecV2.version`.
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m0v21, roles_m0v23

VERSION = "v2.4"
CERT_VERSION = roles_m0v23.CERT_VERSION
Pair = r2.PhrasePair
EVENT = r2.D_KIND_OTHER_EVENT

OLD = roles_m0v23.ROLE_SPECS
TARGET_TERMS = roles_m0v23.TARGET_TERMS
RELATION_NOTES = roles_m0v23.RELATION_NOTES
REJECTED = roles_m0v23.REJECTED

FILL_S92 = "somewhat greater than the original's"

# structure id -> (old wording, new wording) of every changed sentence template, as the tests and the report cite them
CHANGES: dict[str, tuple[tuple[str, str], ...]] = {
    "S26": (("The ray is then tilted {v} farther from the normal than the stated angle of incidence.",
             "The ray is then tilted until its angle of incidence at the interface has grown by {v}."),
            ("The camera that films the interface is then tilted {v} farther from the vertical than before.",
             "The camera on the tripod is then tilted until its angle from the vertical has grown by {v}."),
            ("The laser that produces the ray was tilted {v} farther from the normal than the stated angle of incidence before "
             "the refraction was observed.",
             "Before the refraction was observed, the laser that produces the ray was tilted until the angle of incidence had "
             "grown by {v}."),
            ("The laser ... was tilted {v} farther from the normal than the stated angle of incidence in an earlier experiment.",
             "In an earlier experiment, the laser that produces the ray was tilted until the angle of incidence had grown by "
             "{v}.")),
    "S55": (("From the stated temperature, a heater warmed this gas sample by {v} K before the molecular speeds are measured.",
             "Once the sample was in equilibrium, a heater warmed it by {v} K just before the molecular speeds were measured."),
            ("From the stated temperature, a heater warmed this gas sample by {v} K in an earlier experiment.",
             "Once the sample was in equilibrium, a heater warmed it by {v} K in an earlier experiment.")),
    "S72": (("The electron in this apparatus gains a further {v} eV of kinetic energy in one more accelerating gap. "
             "(D: The alpha particle in the other apparatus gains ...)",
             "R1: The electron in this apparatus gains a further {v} eV of kinetic energy in one more accelerating gap before "
             "the wavelength is determined. D1: the same sentence ending after the wavelength has been determined."),),
    "S92": (("N0: A liquid whose density is different from the original's is poured into the second tank beside this one.",
             "N0: A liquid whose density is somewhat greater than the original's is poured into the second tank beside this one."),
            ("N1: For an earlier experiment only, the liquid in the tank was replaced by one whose density is different from the "
             "original's, with the string still holding the cube under it.",
             "N1: For an earlier experiment only, the liquid in the tank was replaced by one whose density is somewhat greater "
             "than the original's, with the string still holding the cube under it.")),
}


def _spec(sid: str, **changes) -> r2.RoleSpecV2:
    return dataclasses.replace(OLD[sid], **changes)


def _note(sid: str, text: str) -> str:
    return f"{OLD[sid].notes} M0 v2.4: {text}".strip()


S26_P0 = dataclasses.replace(
    OLD["S26"].pairs[0],
    frame="The ray is then tilted until its {relation} has grown by {value} {unit}.",
    r_attach="angle of incidence at the interface",
    d_frame="The camera on the tripod is then tilted until its {relation} has grown by {value} {unit}.",
    d_attach="angle from the vertical",
    frame_mismatch_reason="The R quantity tilts the ray itself, so the subject is the ray and the angle is its angle of incidence; a "
                          "co-present D needs another object with its own reference direction, so the subject and the angle (the "
                          "camera, its angle from the vertical) differ as well as the attachment. A ray tilted 'from the vertical' "
                          "would not be the angle of incidence.")
S26_P1 = dataclasses.replace(
    OLD["S26"].pairs[1],
    frame="{relation}, the laser that produces the ray was tilted until the angle of incidence had grown by {value} {unit}.",
    r_attach="Before the refraction was observed",
    d_attach="In an earlier experiment")

S26 = _spec(
    "S26",
    pairs=(S26_P0, S26_P1),
    notes=_note("S26", "R0 and R1 say the order in ordinary words ('tilted until the angle of incidence has grown by {v}'; R1 "
                       "opens 'Before the refraction was observed'), replacing the meta wording 'than the stated angle of "
                       "incidence' that the naturalness raters rejected; the D twins share the words."))

S55_P1 = dataclasses.replace(
    OLD["S55"].pairs[1],
    frame="Once the sample was in equilibrium, a heater warmed it by {value} {unit} {relation}.",
    r_attach="just before the molecular speeds were measured",
    d_attach="in an earlier experiment")

S55 = _spec(
    "S55",
    pairs=(OLD["S55"].pairs[0], S55_P1),
    notes=_note("S55", "pair-1 R/D/N no longer start 'From the stated temperature'; they start 'Once the sample was in equilibrium' "
                       "and R ties the warming to just before the speeds are measured (rules 1 and 5)."))

S72_P1 = Pair(
    "p1",
    "The electron in this apparatus gains a further {value} {unit} of kinetic energy in one more accelerating gap {relation}.",
    "before the wavelength is determined", "after the wavelength has been determined", EVENT,
    "The electron gains the energy only after its wavelength has been determined, so the energy gain cannot change the wavelength "
    "that the question asks for, which is the one fixed by the kinetic energy gained before the determination.",
    ("starts from rest", "non-relativistically"), "amount")

S72 = _spec(
    "S72",
    pairs=(OLD["S72"].pairs[0], S72_P1),
    notes=_note("S72", "pair 1 is now a same-electron event: R1 an extra gain before the wavelength is determined, D1 the same "
                       "gain after it has been determined (`same_object_other_event`; GPT was right that such an event exists); "
                       "the d_kind_note is dropped; pair 0 (the proton) is unchanged."))

_S92_P0 = dataclasses.replace(OLD["S92"].pairs[0], nonnumeric_fill=FILL_S92)
_S92_P1 = dataclasses.replace(OLD["S92"].pairs[1], nonnumeric_fill=FILL_S92)

S92 = _spec(
    "S92",
    pairs=(_S92_P0, _S92_P1),
    notes=_note("S92", "the numeral-free fill of both pairs is 'somewhat greater than the original's' instead of 'different from "
                       "the original's' (naturalness rewrite of N1; N0 changed with it)."))

CHANGED = ("S26", "S55", "S72", "S92")
ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: {"S26": S26, "S55": S55, "S72": S72, "S92": S92}.get(sid) or OLD[sid] for sid in sorted(OLD)}
STRUCTURE_FACTORIES = roles_m0v21.STRUCTURE_FACTORIES


def structure(structure_id: str) -> gr.Structure:
    """The M0 v2 structure with the v2.4 spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
