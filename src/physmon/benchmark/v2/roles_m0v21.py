"""The M0 v2.1 structures: M0 v2 revised after the LLM panel review (plan revision v2.2, section G; admission standard 3.2, 6.1).

The twelve structures, wirings, study values, cancelling and conditional quantities are those of `roles_m0v2` (imported and reused
with `dataclasses.replace`), so the certified numbers are unchanged. What changes:

* G1: `same_object_undone_event` is withdrawn. Pair 1 of every structure is a genuine other event of the target object that leaves
  no state behind (history in an earlier experiment, or an event after the stated process), or, for S72 only, a second co-present
  object of a different type (`other_object_same_scene` with `d_kind_note`). The certificate rejects reversal patterns and any D
  whose quantity acts on the target.
* G2: the co-present object of d0 is introduced by one number-free clause appended to the base context of EVERY cell of the
  structure (`scene_clause`, `scene_object_rationale`). `structure(sid)` returns the structure with that clause in its context.
* G4: wording fixes (S27 r1 time marker, S07 K, S13 "light cord", S55 relation note) and the naturalness rewrites of the D, N and R
  sentences.

C and K sentences are those of M0 v2 except S07's K (the "broken again" wording).
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m0v2

P = rv.Phrasing
Pair = r2.PhrasePair
CO = r2.D_KIND_CO_PRESENT
EVENT = r2.D_KIND_OTHER_EVENT
V21 = r2.VERSION_V21
OLD = roles_m0v2.ROLE_SPECS

TARGET_TERMS = roles_m0v2.TARGET_TERMS

# Notes appended to the relations listed in the panel packets (admission report, S55 flag: the molar mass is given in g/mol).
RELATION_NOTES: dict[str, dict[str, str]] = {
    "S55": {"vrms": "M is used in kg/mol: M = 4 g/mol = 4e-3 kg/mol (1 g/mol = 1e-3 kg/mol), Ek in J/mol (1 kJ/mol = 1000 J/mol), "
                    "so vrms is in m/s"},
}


def _spec(sid: str, **changes) -> r2.RoleSpecV2:
    return dataclasses.replace(OLD[sid], version=V21, **changes)


S01 = _spec(
    "S01",
    scene_clause="A small cart stands on the floor beside the pulley.",
    scene_object_rationale="A cart on the floor is touched by neither the blocks, the string nor the pulley and exerts no force on "
                           "them, so the acceleration of the blocks is still fixed by the two masses, the pulley and g.",
    scene_refs=("cart",), target_terms=("left block", "right block", "string", "pulley"),
    pairs=(
        Pair("p0", "A {value} {unit} block is {relation}.", "hung from the left block", "loaded onto the small cart", CO,
             "A block loaded onto a cart on the floor is not hung from the blocks, the string or the pulley and exerts no force on "
             "any of them; the blocks' acceleration is fixed by the two hanging masses, the pulley mass and g.",
             ("light string", "does not slip"), "small",
             before_context_reason="The R sentence names 'the left block' before the context introduces any block; a definite "
                                   "reference to an entity not yet mentioned does not read correctly."),
        Pair("p1", "A {value} {unit} block was hung from the left block {relation}.", "before the blocks were released",
             "in an earlier experiment", EVENT,
             "The block was hung from the left block in an earlier experiment, a use of the apparatus that is over; it adds no "
             "mass to the left block in the stated experiment, whose left block carries only its own stated mass.",
             ("light string", "does not slip"), "small"),
    ),
    notes="M0 v2.1: pair 0 puts the extra block on a cart (scene object), pair 1 is history in an earlier experiment.")

S02 = _spec(
    "S02",
    quantity_phrase="an extra distance along the incline",
    scene_clause="A second, identical block rests on a neighbouring incline of the same angle.",
    scene_object_rationale="A block at rest on a neighbouring incline exerts no force on the first block or its incline; the "
                           "first block's speed after its slide depends only on its own incline, friction and g.",
    scene_refs=("second",), target_terms=("the mark", "this incline", "its slide"),
    pairs=(
        Pair("p0", "The block is let go {value} {unit} above {relation}.", "the mark where its slide begins",
             "the foot of its incline", CO,
             "The second block is let go on its own neighbouring incline; nothing links its release point to the first block's "
             "incline, so the first block's distance from rest is the stated one.",
             ("released from rest", "kinetic friction"), "a short way",
             d_frame="The second block is let go {value} {unit} above {relation}.",
             frame_mismatch_reason="The R quantity is the first block's own release point, so the subject is the block itself; a "
                                   "co-present D needs the second block, so the subject noun phrase has to change as well as the "
                                   "attachment, and one frame would either name the wrong block or leave the R reading ambiguous.",
             before_context_reason="The R sentence refers to 'the block' and to the mark where its slide begins, which the context "
                                   "introduces earlier, and presupposes the described slide; placed first it has no referent."),
        Pair("p1", "{relation}, the block slid {value} {unit} down this incline from rest.", "Just before that slide",
             "On an earlier trial", EVENT,
             "The block slid down this incline from rest on an earlier trial, which is over; it adds nothing to the distance the "
             "block slides in the stated trial, which starts from rest at the stated point.",
             ("released from rest", "kinetic friction"), "a short way"),
    ),
    notes="M0 v2.1: R0 reworded without 'the stated distance'; pair 1 is a previous trial instead of a slide on a bench.")

S07_K_SPEC = dataclasses.replace(
    OLD["S07"].conditional.spec, quantity_phrase="the time at which the circuit is broken",
    phrasings=(P("k0", "is broken by opening a switch"), P("k1", "is cut off from the battery")))

S07 = _spec(
    "S07",
    conditional=dataclasses.replace(OLD["S07"].conditional, spec=S07_K_SPEC),
    scene_clause="Beside the circuit, a small lamp is connected to a second battery.",
    scene_object_rationale="A lamp wired to its own second battery closes a loop of its own and shares no node with the capacitor's "
                           "charging loop; an ideal emf is unaffected by what else is connected to a different battery.",
    scene_refs=("second battery",), target_terms=("capacitor", "first battery"),
    pairs=(
        Pair("p0", "A {value} {unit} resistor is {relation}.", "connected in series between the first battery and the capacitor",
             "connected in series with the lamp and the second battery", CO,
             "A resistor in series with the lamp and the second battery closes a complete loop of its own; it shares no node with "
             "the capacitor's charging loop, and an ideal emf is unaffected by whatever else is connected to another battery.",
             ("initially uncharged", "connected in series"), "small",
             before_context_reason="The R sentence refers to 'the first battery and the capacitor' before the context introduces "
                                   "them, and 'first' presupposes the second battery that the scene clause adds."),
        Pair("p1", "A {value} {unit} resistor was {relation}.", "also connected in series with the capacitor in this experiment",
             "connected in series with the capacitor in an earlier experiment", EVENT,
             "The resistor was in the capacitor's circuit in an earlier experiment, which is over; the charging loop of the stated "
             "experiment contains only its stated resistor, and the capacitor is stated to start uncharged.",
             ("initially uncharged", "connected in series"), "small"),
    ),
    notes="M0 v2.1: K quantity phrase and k0 reworded ('broken again' implied an earlier break).")

S13 = _spec(
    "S13",
    scene_clause="A hook is fixed to the wall nearby.",
    scene_object_rationale="A hook on the wall touches neither the string, the bob nor the support of the pendulum, so the "
                           "pendulum's length and period are unchanged.",
    scene_refs=("hook",), target_terms=("string", "bob"),
    pairs=(
        Pair("p0", "A {value} {unit} light cord {relation}.", "is tied between the string and the bob",
             "is hanging from the hook on the wall", CO,
             "A light cord hanging from a hook on the wall touches neither the string, the bob nor the stand, so the pendulum's "
             "length is still the stated string length.",
             ("light string", "small amplitude"), "short",
             before_context_reason="The R sentence refers to 'the string and the bob' before the context mentions them, and the "
                                   "context then introduces 'A small bob' with an indefinite article, which would read as a "
                                   "second bob."),
        Pair("p1", "A {value} {unit} light cord was tied between the string and the bob {relation}.", "before the swing began",
             "in an earlier experiment", EVENT,
             "The cord was tied into the pendulum in an earlier experiment, which is over; the string that swings in the stated "
             "experiment has only its stated length.", ("light string", "small amplitude"), "short"),
    ),
    notes="M0 v2.1: the cord is stated as light in every R and D sentence (panel flag).")

S15 = _spec(
    "S15",
    scene_clause="A small fan, driven by a second battery, stands beside the circuit.",
    scene_object_rationale="A fan driven by its own second battery forms a loop that shares no node with the two resistors, which "
                           "still see only the stated battery.",
    scene_refs=("second battery",), target_terms=("first battery", "resistors"),
    pairs=(
        Pair("p0", "A {value} {unit} cell of negligible internal resistance is {relation}, facing the same way.",
             "connected in series with the first battery", "connected in series with the second battery", CO,
             "A cell in series with the fan's battery forms a loop of its own that shares no node with the two resistors; the "
             "resistors still see only the stated battery.", ("negligible internal resistance", "in parallel"), "small",
             before_context_reason="The R sentence refers to 'the first battery', which the context introduces afterwards, and "
                                   "'facing the same way' has no reference yet."),
        Pair("p1", "{relation}, a {value} {unit} cell of negligible internal resistance was connected in series with the first "
                   "battery, facing the same way.", "In this experiment", "In an earlier experiment", EVENT,
             "The cell was in series with the battery in an earlier experiment, which is over; in the stated experiment the "
             "resistors are across the stated battery alone.", ("negligible internal resistance", "in parallel"), "small"),
    ),
    notes="M0 v2.1: pair 0 differs by one word (first/second battery).")

S20 = _spec(
    "S20",
    scene_clause="A lab stool stands beside the optical bench.",
    scene_object_rationale="A stool beside the bench is not in the path of the light and does not touch the lens or the object, so "
                           "the object distance and the image distance are unchanged.",
    scene_refs=("stool",), target_terms=("object", "lens", "axis"),
    pairs=(
        Pair("p0", "The {relation} is then pushed {value} {unit} farther from the lens.", "stand that holds the object on the axis",
             "stool that stands beside the optical bench", CO,
             "A stool moves on the floor beside the bench; the object that the lens images is on its own stand and stays where the "
             "problem put it.", ("thin converging lens", "placed on the axis"), "a little",
             before_context_reason="The R sentence refers to 'the stand that holds the object on the axis' and says it is 'then' "
                                   "pushed; the object and the lens are introduced only in the context."),
        Pair("p1", "The object was moved {value} {unit} farther from the lens {relation}.", "after it was placed on the axis",
             "in an earlier experiment", EVENT,
             "The object was moved farther from the lens in an earlier experiment, which is over; in the stated experiment it "
             "stands at its stated distance.", ("thin converging lens", "placed on the axis"), "a little"),
    ),
    notes="M0 v2.1: the microphone stand is replaced by a stool; pair 1 is history instead of a slide along the bench.")

S26 = _spec(
    "S26",
    scene_clause="A desk lamp stands near the interface.",
    scene_object_rationale="A desk lamp near the interface is not in the beam, so the ray, its angle of incidence and the media at "
                           "the interface are unchanged by it.",
    scene_refs=("desk lamp",), target_terms=("ray", "normal", "incidence", "laser"),
    pairs=(
        Pair("p0", "The ray is then tilted {value} {unit} farther from {relation}.", "the normal in the plane of incidence",
             "the vertical, away from the interface", CO,
             "A desk lamp near the interface turns no ray in the experiment; the angle of incidence of the ray at the interface is "
             "untouched.", ("flat interface", "angle of incidence"), "a little",
             d_frame="The desk lamp is then tilted {value} {unit} farther from {relation}.",
             frame_mismatch_reason="The R quantity tilts the ray itself, so the subject is the ray and the reference is the normal; a "
                                   "co-present D needs another object with its own reference direction, so the subject and the "
                                   "reference (a desk lamp, the vertical) differ as well as the attachment. A ray tilted 'from the "
                                   "vertical' would not be the stated angle of incidence.",
             before_context_reason="The R sentence refers to 'the ray' and 'the normal' before the context introduces them, and says "
                                   "the tilt is 'then' given, which presupposes the stated angle."),
        Pair("p1", "The laser that produces the ray was tilted {value} {unit} farther from the normal in the plane of incidence "
                   "{relation}.", "after the angle of incidence was set", "in an earlier experiment", EVENT,
             "The laser was tilted in an earlier experiment, which is over; in the stated experiment the ray meets the interface at "
             "the stated angle of incidence.", ("flat interface", "angle of incidence"), "a little"),
    ),
    notes="M0 v2.1: the ceiling lamp and the unmentioned bench are replaced by a desk lamp that the scene clause introduces.")

S27 = _spec(
    "S27",
    scene_clause="A second tank, filled with the same liquid, stands beside it.",
    scene_object_rationale="A second tank with its own liquid shares no liquid, pipe or surface with the first, so the pressure at "
                           "the first tank's free surface and at depth stays as stated.",
    scene_refs=("second tank",), target_terms=("this tank",),
    pairs=(
        Pair("p0", "A {value} {unit} pressure rise is then applied to the liquid in {relation} by a piston resting on its free "
                   "surface.", "this tank", "the second tank", CO,
             "The piston presses on the liquid of the second tank; liquids in separate tanks share no pressure, so the pressure at "
             "the free surface of this tank stays as stated.", ("free surface", "filled with a liquid"), "small",
             before_context_reason="The sentence says the rise is 'then' applied to 'this tank', which presupposes the state "
                                   "described in the context; placed first it would be read as the final state and the stated "
                                   "surface pressure would no longer be a starting value."),
        Pair("p1", "{relation}, a pump added a {value} {unit} pressure rise to the air above this liquid.", "Afterwards",
             "In an earlier experiment", EVENT,
             "The pump raised the pressure above this liquid in an earlier experiment, which is over; in the stated experiment the "
             "pressure at the free surface is the stated value.", ("free surface", "filled with a liquid"), "small"),
    ),
    notes="M0 v2.1: R1 carries a time marker ('Afterwards') so the added rise follows the stated surface pressure (panel flag).")

S30 = _spec(
    "S30",
    scene_clause="A jug stands on the bench beside the heater.",
    scene_object_rationale="A jug standing on the bench is not in the heated water and takes no energy from the heater, which "
                           "delivers its stated power to the stated mass only.",
    scene_refs=("jug",), target_terms=("into the water", "heater delivers"),
    pairs=(
        Pair("p0", "The jug holds {value} {unit} of water at the same starting temperature and is {relation}.",
             "emptied into the water before the heating starts", "left on the bench until the heating is over", CO,
             "A jug left on the bench is not in the heated water and takes no energy from the heater, which delivers its stated "
             "power to the stated mass only.", ("specific heat capacity", "delivers"), "a small amount",
             before_context_reason="The R sentence refers to 'the jug', 'the water' and to 'heating', introduced only in the "
                                   "context and the scene clause, and says 'at the same starting temperature' of a temperature "
                                   "not yet stated."),
        Pair("p1", "A jug holding {value} {unit} of water at the same starting temperature was emptied into the water {relation}.",
             "before the heating started", "after the heating ended", EVENT,
             "The jug was emptied into the water only after the stated heating had ended, so the heater warmed the stated mass "
             "throughout the time the question asks for.", ("specific heat capacity", "delivers"), "a small amount"),
    ),
    notes="M0 v2.1: pair 1 D is an event after the stated process (no effect on a time-to-heat); judged honest, see the report.")

S55 = _spec(
    "S55",
    scene_clause="The sample is in a flask, and a sample of a different gas is in another flask beside it.",
    scene_object_rationale="A sample of a different gas in another flask exchanges no heat with the first and does not change its "
                           "temperature, molar mass or the molar gas constant.",
    scene_refs=("sample",), target_terms=("this gas sample",),
    pairs=(
        Pair("p0", "Before the molecular speeds are measured, a heater warms {relation} by {value} {unit}.", "this gas sample",
             "the other sample", CO,
             "A different gas in another flask exchanges no heat with this sample, which stays at its stated temperature.",
             ("thermal equilibrium", "ideal gas"), "a few kelvin",
             before_context_reason="The R sentence refers to 'this gas sample', which the context introduces afterwards, and "
                                   "'before the molecular speeds are measured' would then precede the stated equilibrium "
                                   "temperature, so the order of warming and the stated 300 K would be reversed."),
        Pair("p1", "A heater warmed this gas sample by {value} {unit} {relation}.", "before its molecular speeds were measured",
             "in an earlier experiment", EVENT,
             "The sample was warmed in an earlier experiment, which is over; in the stated experiment it is in thermal "
             "equilibrium at its stated temperature when the speeds are measured.", ("thermal equilibrium", "ideal gas"),
             "a few kelvin"),
    ),
    notes="M0 v2.1: the heat-and-cool-back D is withdrawn; the molar-mass conversion is stated in the listed relation (RELATION_NOTES).")

S72 = _spec(
    "S72",
    scene_clause="A second apparatus beside this one accelerates protons and alpha particles.",
    scene_object_rationale="Protons and alpha particles accelerated in another apparatus do not interact with the electron or give "
                           "it energy; its kinetic energy and the constants stay as stated.",
    scene_refs=("proton",), target_terms=("electron",),
    pairs=(
        Pair("p0", "Before the wavelength is determined, an extra {value} {unit} of kinetic energy is given to {relation} by "
                   "one more accelerating stage.", "the electron", "the proton", CO,
             "Energy given to a proton by a stage of the other apparatus does not reach the electron; the electron's kinetic "
             "energy is the stated one.", ("starts from rest", "non-relativistically"), "amount",
             before_context_reason="The R sentence refers to 'the electron' and to the wavelength before the context introduces "
                                   "either, and 'an extra' energy presupposes the stated one."),
        Pair("p1", "The {relation} gains a further {value} {unit} of kinetic energy in one more accelerating gap.",
             "electron in this apparatus", "alpha particle in the other apparatus", CO,
             "Energy gained by an alpha particle in the other apparatus does not reach the electron; the electron's kinetic energy "
             "is the stated one.", ("starts from rest", "non-relativistically"), "amount",
             d_kind_note="No honest same-object other event exists for this quantity: any energy gained by the electron itself "
                         "(before or after) acts on its kinetic energy, and a gain in an earlier run belongs to another "
                         "electron. A second co-present object of a different type (the alpha particle, named in the scene clause "
                         "with the proton) is used instead."),
    ),
    notes="M0 v2.1: the gain-and-loss D is withdrawn; both D pairs are co-present (proton, alpha particle), see d_kind_note.")

S92 = _spec(
    "S92",
    scene_clause="A second, empty tank stands beside it.",
    scene_object_rationale="An empty second tank holds no liquid and no part of the cube or the string, so the cube's buoyancy and "
                           "the string tension come only from the first tank's liquid.",
    scene_refs=("second",), target_terms=("this tank", "original liquid", "cube", "string"),
    pairs=(
        Pair("p0", "A liquid whose density is {value} {unit} {relation}.", "now replaces the original liquid in this tank",
             "now fills the second tank beside this one", CO,
             "A liquid in a second tank exerts no force on this cube; the buoyant force on this cube comes only from the liquid in "
             "its own tank, which is unchanged.", ("held at rest completely under the surface", "light vertical string"),
             "different from the original's",
             before_context_reason="The R sentence refers to 'the original liquid in this tank', which the context has not yet "
                                   "introduced, and 'now' presupposes the earlier state."),
        Pair("p1", "{relation}, the cube was held completely under a liquid whose density is {value} {unit}.", "Afterwards",
             "In an earlier experiment", EVENT,
             "The cube was held under that liquid in an earlier experiment, which is over; in the stated experiment it is held "
             "under the stated liquid.", ("held at rest completely under the surface", "light vertical string"),
             "different from the original's"),
    ),
    notes="M0 v2.1: the rinse D is replaced by a use of the cube in an earlier experiment; the second tank is introduced as empty.")

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {s.structure_id: s for s in (S01, S02, S07, S13, S15, S20, S26, S27, S30, S55, S72, S92)}
STRUCTURE_FACTORIES = roles_m0v2.STRUCTURE_FACTORIES


def structure(structure_id: str) -> gr.Structure:
    """The M0 v2 structure with the spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
