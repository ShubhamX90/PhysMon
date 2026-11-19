"""M0 v2.5 role specs: M0 v2.4 with the two N sentences that the naturalness rater rated artificial rewritten (journal J15.1-051).

Both qualified judges admitted the four changed structures of M0 v2.4 (4/4; committed 396e7b8); the naturalness rater rated two N
sentences artificial, and the D or R twins that share their frames change with them. No model output exists on any M0 cell, so the
structures are still fixed before any run. The other nine specs are the M0 v2.4 spec objects, unchanged. Wording rules 1-8 apply;
scene clauses are unchanged (physical conditions only); no meta wording.

Changes (old -> new wording is in `CHANGES`; the tests check each):

* S26 pair 0 (N0 rated artificial: tilting the filming camera is a pointless action, and "its angle from the vertical has grown by a
  little" is wording no one would use; rule 3, a co-present D needs an ordinary purposeful action): D0 and N0 are "The camera on the
  tripod is then tilted {v} farther from the vertical to keep the ray in view." (N0: "a little"). The R0 sentence and the unmatched D
  frame declaration are unchanged (the R quantity tilts the ray, the D quantity tilts another object).
* S55 pair 1 (N1 rated incoherent: the sample is said to be warmed after reaching equilibrium yet "in an earlier experiment"; the
  reader must infer the sample is back at 300 K): "Once the sample was in equilibrium" is dropped. R1 "Just before the molecular speeds
  are measured, a heater warmed this gas sample by {v}." / D1 and N1 "In an earlier experiment, a heater warmed this gas sample by
  {v}." The frame is shared (R and D differ in the attachment only; word counts differ by at most 3); R1 stays a change applied to
  this sample just before the question's moment (rules 1 and 5). Pair 0 is unchanged.

`CERT_VERSION` stays "v2.1": `rolevalue_v2.certify_v2` applies its full rule set only for that `RoleSpecV2.version`.
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m0v21, roles_m0v24

VERSION = "v2.5"
CERT_VERSION = roles_m0v24.CERT_VERSION

OLD = roles_m0v24.ROLE_SPECS
TARGET_TERMS = roles_m0v24.TARGET_TERMS
RELATION_NOTES = roles_m0v24.RELATION_NOTES
REJECTED = roles_m0v24.REJECTED

# structure id -> (old wording, new wording) of every changed sentence template, as the tests and the report cite them
CHANGES: dict[str, tuple[tuple[str, str], ...]] = {
    "S26": (("D0: The camera on the tripod is then tilted until its angle from the vertical has grown by {v}.",
             "D0: The camera on the tripod is then tilted {v} farther from the vertical to keep the ray in view."),
            ("N0: The camera on the tripod is then tilted until its angle from the vertical has grown by a little.",
             "N0: The camera on the tripod is then tilted a little farther from the vertical to keep the ray in view.")),
    "S55": (("R1: Once the sample was in equilibrium, a heater warmed it by {v} just before the molecular speeds were measured.",
             "R1: Just before the molecular speeds were measured, a heater warmed this gas sample by {v}."),
            ("D1: Once the sample was in equilibrium, a heater warmed it by {v} in an earlier experiment.",
             "D1: In an earlier experiment, a heater warmed this gas sample by {v}."),
            ("N1: Once the sample was in equilibrium, a heater warmed it by a few kelvin in an earlier experiment.",
             "N1: In an earlier experiment, a heater warmed this gas sample by a few kelvin.")),
}


def _spec(sid: str, **changes) -> r2.RoleSpecV2:
    return dataclasses.replace(OLD[sid], **changes)


def _note(sid: str, text: str) -> str:
    return f"{OLD[sid].notes} M0 v2.5: {text}".strip()


S26_P0 = dataclasses.replace(
    OLD["S26"].pairs[0],
    d_frame="The camera on the tripod is then tilted {value} {unit} farther from {relation} to keep the ray in view.",
    d_attach="the vertical")

S26 = _spec(
    "S26",
    pairs=(S26_P0, OLD["S26"].pairs[1]),
    notes=_note("S26", "D0/N0 give the camera an ordinary purpose and plain wording ('tilted {v} farther from the vertical to keep "
                       "the ray in view', rule 3), replacing 'tilted until its angle from the vertical has grown by {v}' that the "
                       "naturalness rater rejected; R0 and pair 1 unchanged."))

S55_P1 = dataclasses.replace(
    OLD["S55"].pairs[1],
    frame="{relation}, a heater warmed this gas sample by {value} {unit}.",
    r_attach="Just before the molecular speeds were measured",
    d_attach="In an earlier experiment")

S55 = _spec(
    "S55",
    pairs=(OLD["S55"].pairs[0], S55_P1),
    notes=_note("S55", "pair-1 R/D/N no longer say 'Once the sample was in equilibrium' (the earlier-experiment reading was "
                       "incoherent with it); R1 'Just before the molecular speeds were measured, a heater warmed this gas sample by "
                       "{v}', D1 'In an earlier experiment, a heater warmed this gas sample by {v}' (rules 1 and 5)."))

CHANGED = ("S26", "S55")
ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: {"S26": S26, "S55": S55}.get(sid) or OLD[sid] for sid in sorted(OLD)}
STRUCTURE_FACTORIES = roles_m0v21.STRUCTURE_FACTORIES


def structure(structure_id: str) -> gr.Structure:
    """The M0 v2 structure with the v2.5 spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
