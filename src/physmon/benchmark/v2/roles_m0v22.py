"""M0 v2.2 role specs: M0 v2.1 revised after its LLM panel review (journal J15.1-038, 2026-11-16).

The Claude judge (prompt v3) and blind naturalness raters (prompt v2) reviewed M0 v2.1 on 2026-11-16
(`docs/validation/v2/llm_panel/admission_m0v21/runs/claude/score/admission_report.md`): 10 ADMIT, 2 REJECT (S02, S92), and
rewrites required for S20 D0/N0 and S26 D0 (rated artificial: a pointless action on an unrelated object). No model output exists
on M0 v2.1, so rewriting is allowed (admission standard, opening paragraph). Changes:

* S02 is REJECTED and REPLACED (dropped from M0): its R quantity (an extra release distance) cannot be worded so that the base
  ("released from rest", "slides 4 m", "after it has slid that distance") and the R sentence fix one reading; both of its R
  phrasings were read two ways by the judge. It returns to the M250 pool only with a new design and a fresh review.
* S92 pair 1: the R sentence now states the change of liquid as an event before the measurement, in the same tank with the same
  string (the judge's high flag: "Afterwards, the cube was held ..." left open which state the question asks about).
* S20 pair 0: the co-present object is a lamp that lights the object (adjusting a lamp is an ordinary action); the stool is gone.
* S26 pair 0: the co-present object is a camera that films the interface (re-aiming a camera is an ordinary action).

Every other structure keeps its M0 v2.1 spec unchanged (it was admitted as is).
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m0v21

V22 = "v2.2"
Pair = r2.PhrasePair
CO = r2.D_KIND_CO_PRESENT
EVENT = r2.D_KIND_OTHER_EVENT

OLD = roles_m0v21.ROLE_SPECS
TARGET_TERMS = roles_m0v21.TARGET_TERMS
RELATION_NOTES = roles_m0v21.RELATION_NOTES

# Structures rejected by the panel and replaced (not carried into M0 v2.2), with the reason.
REJECTED: dict[str, str] = {
    "S02": "panel REJECT (ANSWER_AMBIGUOUS, high flag) on M0 v2.1: an extra release distance cannot be stated without "
           "contradicting 'released from rest ... slides 4 m ... after it has slid that distance'; replaced, not rewritten.",
}


def _spec(sid: str, **changes) -> r2.RoleSpecV2:
    return dataclasses.replace(OLD[sid], version=V22, **changes)


S20 = _spec(
    "S20",
    scene_clause="A lamp that stands beside the bench lights the object from one side.",
    scene_object_rationale="A lamp off the axis only illuminates the object; it is not between the object and the lens and does "
                           "not move the object, so the object distance and the image distance are unchanged.",
    scene_refs=("lamp",), target_terms=("object", "lens", "axis"),
    pairs=(
        Pair("p0", "The {relation} is then pushed {value} {unit} farther from the lens.", "stand that holds the object on the axis",
             "lamp that stands beside the bench", CO,
             "Moving the lamp changes only how brightly the object is lit; the object stays on its stand at its stated distance, "
             "and a thin lens images it at the distance fixed by the object distance and the focal length.",
             ("thin converging lens", "placed on the axis"), "a little",
             before_context_reason="The R sentence refers to 'the stand that holds the object on the axis' and says it is 'then' "
                                   "pushed; the object and the lens are introduced only in the context."),
        OLD["S20"].pairs[1],
    ),
    notes="M0 v2.2: the stool (rated artificial) is replaced by a lamp that lights the object; pair 1 unchanged.")

S26_P0 = dataclasses.replace(
    OLD["S26"].pairs[0],
    d_attach="the vertical",
    d_rationale="A camera that films the interface turns no ray in the experiment; the ray meets the interface at the stated angle "
                "of incidence whatever way the camera points.",
    d_frame="The camera that films the interface is then tilted {value} {unit} farther from {relation}.",
    frame_mismatch_reason="The R quantity tilts the ray itself, so the subject is the ray and the reference is the normal; a "
                          "co-present D needs another object with its own reference direction, so the subject and the reference "
                          "(the camera, the vertical) differ as well as the attachment. A ray tilted 'from the vertical' would not "
                          "be the stated angle of incidence.",
)

S26 = _spec(
    "S26",
    scene_clause="A camera on a tripod films the interface.",
    scene_object_rationale="A camera only records the light that reaches it; it emits no ray and does not touch the media, so the "
                           "ray, its angle of incidence and the indices at the interface are unchanged.",
    scene_refs=("camera",), target_terms=("ray", "normal", "incidence", "laser"),
    pairs=(S26_P0, OLD["S26"].pairs[1]),
    notes="M0 v2.2: the desk lamp (rated artificial when tilted) is replaced by a camera that films the interface; pair 1 unchanged.")

S92_P1 = Pair(
    "p1",
    "{relation}, the liquid in the tank was replaced by one whose density is {value} {unit}, with the string still holding the "
    "cube under it.",
    "Before the tension was measured", "In an earlier experiment", EVENT,
    "The liquid was replaced in an earlier experiment, which is over; in the stated experiment the cube is held under the stated "
    "liquid, which alone sets the buoyant force and the tension.",
    ("held at rest completely under the surface", "light vertical string"), "different from the original's")

S92 = _spec(
    "S92",
    pairs=(OLD["S92"].pairs[0], S92_P1),
    notes="M0 v2.2: R1 states the replacement as an event in this tank, with the same string, before the measurement (panel high "
          "flag on M0 v2.1).")

CHANGED = ("S20", "S26", "S92")
ROLE_SPECS: dict[str, r2.RoleSpecV2] = {
    sid: ({"S20": S20, "S26": S26, "S92": S92}.get(sid) or OLD[sid]) for sid in sorted(OLD) if sid not in REJECTED
}
STRUCTURE_FACTORIES = roles_m0v21.STRUCTURE_FACTORIES


def structure(structure_id: str) -> gr.Structure:
    """The M0 v2 structure with the v2.2 spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
