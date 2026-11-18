"""M0 v2.3 role specs: M0 v2.2 revised for the legitimate flags of the second judge (GPT-6.1 Sol; journal J15.1-046, 2026-11-18).

GPT reviewed the 11 structures of M0 v2.2 (reports `docs/validation/v2/llm_panel/admission_{m0v21,m0v22,m0v22b}/runs/
score_two_judges/admission_report.md`) and admitted only S01, S15 and S20. No model output exists on M0 v2.2, so the structures
are fixed before any run (admission standard, opening paragraph). S02 stays rejected (it is not in M0). Every change below follows
the eight wording rules (rules 1-5 of J15.1-038, rules 6-8 of J15.1-046); each is also recorded in the spec's `notes`.

Changes (old -> new wording is in `CHANGES`; the tests check each):

* Rule 7 (a pair-1 D event that attaches or adds something to the target in an earlier experiment must say it was there for that
  experiment only): the pair-1 D attachment of S01 (block hung), S07 (resistor connected), S13 (cord tied) and S15 (cell connected)
  is now "for an earlier experiment only" ("For an earlier experiment only" where the frame opens with it). S92 pair 1 (the liquid
  of the tank replaced) gets the same phrase: a replaced liquid that is not stated to have been put back leaves the current liquid
  in doubt (Claude's low flag on M0 v2.2: "leave implicit that the original liquid was restored"). Checked and left as they are,
  because they attach nothing: S20 (object moved), S26 (laser tilted), S55 (sample warmed), S27 (a pump raised the pressure; the
  attachment would also lengthen the D side by more than the three-word limit against "Afterwards"), S30 (a jug emptied after the
  heating) and S72 (pair 1 is a co-present alpha particle).
* S07: the K_out rationale falsely said the in-regime answer does not need a non-leaking capacitor (GPT, high flag on T3314/T7A5D);
  leakage lowers the voltage before a break as well, so the rationale now says the answer needs it throughout, and the scene clause
  states (rule 6) that the capacitor does not leak and that the batteries and wires are ideal.
* S26 (GPT high flag, Claude medium flag: "40 degrees before or after the tilt"): both R sentences say the tilt starts from the
  stated angle of incidence (the ray is tilted farther from the normal "than the stated angle of incidence"; no numeral other than
  the cue); the D sentences of the pair carry the same words ("than before" for the camera of pair 0).
* S27 (GPT high flags): the scene clause states the liquid in both tanks is at rest at the start, both tanks are open to the same air
  above (so the second free surface is at the same pressure), and the depth is measured in the first tank (judgement
  call: the flag also said the question does not identify the tank); the C sentences name "the first tank" and c1 states "vertical
  sides and a flat base with an area", so the column relation m = rho A h has one cross-section (the flat-base-only wording was
  the flagged T2AA8).
* S27 held-out value 8 kPa -> 9 kPa: "a 8 kPa" has the wrong article; held-out values are certified, never emitted, so no cell
  changes (the tests scan every study and held-out value of every frame for "a" before a vowel-sound number).
* S30 (GPT high flag): the scene clause states that no heat is lost to the surroundings and that the water does not boil.
* S55 (GPT high flags): the scene clause states the two flasks are thermally insulated from each other; the pair-1 R sentence now
  says the heater warmed the sample from the stated temperature before the molecular speeds are measured ("From the stated
  temperature, a heater warmed this gas sample by 50 K before the molecular speeds are measured."), so the stated 300 K is the start
  and the speeds are those after the warming (rules 1 and 5).
* S92 (GPT high flag, rule 8): the second tank stays "empty" in the scene clause; D0 and N0 pour liquid into it ("is poured into
  the second tank beside this one"), not "now fills" it.
* S72: no sentence changed; GPT's flag (the numeral-free N sentences "omit the 90 eV") was a misreading and is answered in the
  panel packets (`scripts/v2/s201_m0v23_panel_packets.py`: every N claim states the numeral-free control by design).
* S20: no sentence changed (admitted by both judges, no flag).

Certificate note (a finding): `rolevalue_v2.certify_v2` applies its stricter rule set (reversal patterns, co-present D not naming the
target, time-anchored same-object D, scene-clause checks) only when `spec.version == "v2.1"`; the M0 v2.2 specs of S20, S26 and S92
had version "v2.2" and so were certified without those checks. The v2.3 specs keep the `version` field at "v2.1" (the certificate
generation the checks key on) so that every structure is certified under the full rule set; the dataset is identified as M0 v2.3 by
`VERSION` and by the builder's `m0_version` field.
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m0v21, roles_m0v22

VERSION = "v2.3"
CERT_VERSION = r2.VERSION_V21  # the value of `RoleSpecV2.version` under which `certify_v2` applies the full rule set
P = rv.Phrasing
Pair = r2.PhrasePair

OLD = roles_m0v22.ROLE_SPECS
TARGET_TERMS = roles_m0v22.TARGET_TERMS
RELATION_NOTES = roles_m0v22.RELATION_NOTES
REJECTED = roles_m0v22.REJECTED

ONLY_EARLIER = "for an earlier experiment only"  # rule 7
ONLY_EARLIER_CAP = "For an earlier experiment only"

# structure id -> (old wording, new wording) of every changed sentence template or clause, as the tests and the report cite them
CHANGES: dict[str, tuple[tuple[str, str], ...]] = {
    "S01": (("A {v} kg block was hung from the left block in an earlier experiment.",
             "A {v} kg block was hung from the left block for an earlier experiment only."),),
    "S07": (("A {v} kOhm resistor was connected in series with the capacitor in an earlier experiment.",
             "A {v} kOhm resistor was connected in series with the capacitor for an earlier experiment only."),
            ("Beside the circuit, a small lamp is connected to a second battery.",
             "Beside the circuit, a small lamp is connected to a second battery. The batteries and the wires are ideal, and the "
             "capacitor does not leak."),
            ("K_out reason: ... Assumes an ideal, non-leaking capacitor, which the in-regime answer does not need.",
             "K_out reason: ... Assumes an ideal, non-leaking capacitor, which the stated answer needs before the break as well.")),
    "S13": (("A {v} m light cord was tied between the string and the bob in an earlier experiment.",
             "A {v} m light cord was tied between the string and the bob for an earlier experiment only."),),
    "S15": (("In an earlier experiment, a {v} V cell ... was connected in series with the first battery, facing the same way.",
             "For an earlier experiment only, a {v} V cell ... was connected in series with the first battery, facing the same "
             "way."),),
    "S26": (("The ray is then tilted {v} farther from the normal in the plane of incidence.",
             "The ray is then tilted {v} farther from the normal than the stated angle of incidence."),
            ("The laser that produces the ray was tilted {v} farther from the normal in the plane of incidence before the "
             "refraction was observed.",
             "The laser that produces the ray was tilted {v} farther from the normal than the stated angle of incidence before "
             "the refraction was observed."),
            ("The camera that films the interface is then tilted {v} farther from the vertical.",
             "The camera that films the interface is then tilted {v} farther from the vertical than before."),
            ("The laser ... was tilted {v} farther from the normal in the plane of incidence in an earlier experiment.",
             "The laser ... was tilted {v} farther from the normal than the stated angle of incidence in an earlier experiment.")),
    "S27": (("A second tank, filled with the same liquid, stands beside it.",
             "A second tank, filled with the same liquid, stands beside it. At the start the liquid in both tanks is at rest and "
             "both tanks are open to the same air above; the depth is measured in the first tank."),
            ("The tank has a flat base with an area of {v} m2.",
             "The first tank has vertical sides and a flat base with an area of {v} m2."),
            ("The tank has a uniform horizontal cross-sectional area of {v} m2.",
             "The first tank has a uniform horizontal cross-sectional area of {v} m2.")),
    "S30": (("A jug stands on the bench beside the heater.",
             "A jug stands on the bench beside the heater. No heat is lost to the surroundings, and the water does not boil."),),
    "S55": (("The sample is in a flask, and a sample of a different gas is in another flask beside it.",
             "The sample is in a flask, and a sample of a different gas is in another flask beside it. The two flasks are "
             "thermally insulated from each other."),
            ("A heater warmed this gas sample by {v} K before its molecular speeds were measured.",
             "From the stated temperature, a heater warmed this gas sample by {v} K before the molecular speeds are measured."),
            ("A heater warmed this gas sample by {v} K in an earlier experiment.",
             "From the stated temperature, a heater warmed this gas sample by {v} K in an earlier experiment.")),
    "S92": (("A liquid whose density is {v} kg/m3 now fills the second tank beside this one.",
             "A liquid whose density is {v} kg/m3 is poured into the second tank beside this one."),
            ("In an earlier experiment, the liquid in the tank was replaced by one whose density is {v} kg/m3, with the string "
             "still holding the cube under it.",
             "For an earlier experiment only, the liquid in the tank was replaced by one whose density is {v} kg/m3, with the "
             "string still holding the cube under it.")),
}


def _spec(sid: str, **changes) -> r2.RoleSpecV2:
    return dataclasses.replace(OLD[sid], version=CERT_VERSION, **changes)


def _p1(sid: str, **changes) -> Pair:
    return dataclasses.replace(OLD[sid].pairs[1], **changes)


def _note(sid: str, text: str) -> str:
    return f"{OLD[sid].notes} M0 v2.3: {text}".strip()


S01 = _spec(
    "S01",
    pairs=(OLD["S01"].pairs[0], _p1("S01", d_attach=ONLY_EARLIER)),
    notes=_note("S01", "pair-1 D says the block was hung 'for an earlier experiment only' (rule 7); nothing else changed."))

_S07_K_OUT = dataclasses.replace(
    OLD["S07"].conditional.k_out,
    reason="The question asks for the capacitor voltage at a stated time after the connection, so it stays well posed when the "
           "circuit is opened earlier than that time: an ideal capacitor with no discharge path keeps the charge it had at the "
           "break, V0 (1 - exp(-t_break / RC)). Assumes an ideal, non-leaking capacitor, which the stated answer needs before the "
           "break as well as after it (leakage would lower the charging voltage throughout); the scene clause states it.")

S07 = _spec(
    "S07",
    conditional=dataclasses.replace(OLD["S07"].conditional, k_out=_S07_K_OUT),
    scene_clause="Beside the circuit, a small lamp is connected to a second battery. The batteries and the wires are ideal, and "
                 "the capacitor does not leak.",
    pairs=(OLD["S07"].pairs[0], _p1("S07", d_attach="connected in series with the capacitor " + ONLY_EARLIER)),
    notes=_note("S07", "pair-1 D 'for an earlier experiment only' (rule 7); the K_out rationale no longer claims the in-regime "
                       "answer is independent of leakage, and the scene clause states ideal batteries and wires and a capacitor "
                       "that does not leak (rule 6; GPT high flag)."))

S13 = _spec(
    "S13",
    pairs=(OLD["S13"].pairs[0], _p1("S13", d_attach=ONLY_EARLIER)),
    notes=_note("S13", "pair-1 D says the cord was tied 'for an earlier experiment only' (rule 7; GPT hidden-coupling flag)."))

S15 = _spec(
    "S15",
    pairs=(OLD["S15"].pairs[0], _p1("S15", d_attach=ONLY_EARLIER_CAP)),
    notes=_note("S15", "pair-1 D 'For an earlier experiment only' (rule 7); nothing else changed."))

S20 = _spec("S20", notes=_note("S20", "no sentence changed (admitted by both judges); certified under the full rule set."))

S26_P0 = dataclasses.replace(
    OLD["S26"].pairs[0],
    frame="The ray is then tilted {value} {unit} farther from {relation}.",
    r_attach="the normal than the stated angle of incidence",
    d_frame="The camera that films the interface is then tilted {value} {unit} farther from {relation} than before.",
    d_attach="the vertical")
S26_P1 = dataclasses.replace(
    OLD["S26"].pairs[1],
    frame="The laser that produces the ray was tilted {value} {unit} farther from the normal than the stated angle of incidence "
          "{relation}.")

S26 = _spec(
    "S26",
    pairs=(S26_P0, S26_P1),
    notes=_note("S26", "both R sentences state that the tilt starts from the stated angle of incidence ('farther from the normal "
                       "than the stated angle of incidence'), so '40 degrees before or after the tilt' has one reading (GPT high "
                       "flag, Claude medium flag); the D twins carry the same words."))

_S27_CANCELLING_SPEC = dataclasses.replace(
    OLD["S27"].cancelling.spec,
    frame="The first tank {relation} {value} {unit}.",
    phrasings=(P("c0", "has a uniform horizontal cross-sectional area of"),
               P("c1", "has vertical sides and a flat base with an area of")))

S27 = _spec(
    "S27",
    heldout_values=(9.0, 20.0),  # 8.0 rendered "A 8 kPa" (wrong article); 9 reads with "a" and certifies
    cancelling=dataclasses.replace(OLD["S27"].cancelling, spec=_S27_CANCELLING_SPEC),
    scene_clause="A second tank, filled with the same liquid, stands beside it. At the start the liquid in both tanks is at rest "
                 "and both tanks are open to the same air above; the depth is measured in the first tank.",
    notes=_note("S27", "the scene clause states the liquid at rest, both tanks open to the same air at the start, and the tank the "
                       "question refers to; the C sentences say 'The first tank' and c1 says 'vertical sides and a flat base' (GPT "
                       "high flags: rest, which tank, the second tank's surface pressure, constant cross-section). The held-out "
                       "value 8 kPa is replaced by 9 kPa: 'A 8 kPa' has the wrong article (held-out values are certified, never "
                       "emitted)."))

S30 = _spec(
    "S30",
    scene_clause="A jug stands on the bench beside the heater. No heat is lost to the surroundings, and the water does not boil.",
    notes=_note("S30", "the scene clause states no heat loss and no boiling (rule 6; GPT high flag)."))

S55_P1 = _p1(
    "S55",
    frame="From the stated temperature, a heater warmed this gas sample by {value} {unit} {relation}.",
    r_attach="before the molecular speeds are measured",
    d_attach="in an earlier experiment")

S55 = _spec(
    "S55",
    scene_clause="The sample is in a flask, and a sample of a different gas is in another flask beside it. The two flasks are "
                 "thermally insulated from each other.",
    pairs=(OLD["S55"].pairs[0], S55_P1),
    notes=_note("S55", "the scene clause states the two flasks are thermally insulated from each other (rule 6); pair-1 R/D now "
                       "start 'From the stated temperature' and R ties the warming to the moment the speeds are measured (rules "
                       "1 and 5; Claude medium flag and GPT high flag on the tense)."))

S72 = _spec("S72", notes=_note("S72", "no sentence changed; the numeral-free N sentences are explained as controls in the panel "
                                      "packets (GPT misreading, J15.1-046)."))

S92_P0 = dataclasses.replace(OLD["S92"].pairs[0], d_attach="is poured into the second tank beside this one")
S92_P1 = _p1("S92", d_attach=ONLY_EARLIER_CAP)

S92 = _spec(
    "S92",
    pairs=(S92_P0, S92_P1),
    notes=_note("S92", "the second tank stays empty in the scene clause; D0 and N0 pour liquid into it instead of 'now fills' "
                       "(rule 8; GPT high flag); pair-1 D 'For an earlier experiment only' (rule 7)."))

CHANGED = ("S01", "S07", "S13", "S15", "S26", "S27", "S30", "S55", "S92")
UNCHANGED_SENTENCES = ("S20", "S72")
ROLE_SPECS: dict[str, r2.RoleSpecV2] = {
    s.structure_id: s for s in (S01, S07, S13, S15, S20, S26, S27, S30, S55, S72, S92)}
STRUCTURE_FACTORIES = roles_m0v21.STRUCTURE_FACTORIES


def structure(structure_id: str) -> gr.Structure:
    """The M0 v2 structure with the v2.3 spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
