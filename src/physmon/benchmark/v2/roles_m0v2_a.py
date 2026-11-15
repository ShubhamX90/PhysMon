"""Role-by-value specifications for M0 v2, batch a (S01, S02, S13, S27, S92, S20). See `rolevalue_v2` for the rules.

The M0 specs (`roles_m0.py`, `roles_m0_a.py`, `roles_m0_b.py`) stay as they were; they built the sealed `m0_pilot`. These
specs keep the same structures, wirings and cancelling and conditional quantities, and replace the wording (two phrasing
pairs with a co-present D and a same-object-other-event D, no consequence clauses, no marker words) and the study values
(no value equals a displayed input or shares two leading digits with an input or an answer).
"""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_fluids, library, library_b, library_c
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2

P = rv.Phrasing
Pair = r2.PhrasePair

S01 = r2.RoleSpecV2(
    structure_id="S01", quantity_phrase="a small block", quantity_type="mass", unit="kg", values=(0.6, 0.9, 1.3),
    heldout_values=(0.7, 1.1),
    relevant=rv.RelevantWiring("m1", "add", "A block hung from the left block moves with it, so the left mass in the "
                                            "equation of motion becomes m1 + q."),
    pairs=(
        Pair("p0", "A {value} {unit} block is {relation}.", "tied to the underside of the left block",
             "resting on the bench beside the apparatus", "other_object_same_scene",
             "A block resting on the bench is not tied to the blocks, the string or the pulley and exerts no force on any "
             "of them; the blocks' acceleration is fixed by the two hanging masses, the pulley mass and g.",
             ("light string", "does not slip"), "small",
             before_context_reason="The R sentence names 'the left block' before the context introduces any block; a "
                                   "definite reference to an entity not yet mentioned does not read correctly."),
        Pair("p1", "Before the blocks were let go, a {value} {unit} block was hung from the left block and {relation}.",
             "left there", "taken down again", "same_object_undone_event",
             "The block was hung from the left block and taken down again before the blocks were let go, so the left "
             "block carries only its own stated mass when the motion starts.",
             ("light string", "does not slip"), "small"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the pulley radius", "length", "cm", (8.0, 12.0, 16.0), "The pulley {relation} {value} {unit}.",
            (P("c0", "has a radius of"), P("c1", "measures, from its axle to its rim,")),
            "(m2 - m1)*g/(m1 + m2 + (M*q**2/2)/q**2)", ("I = M r^2 / 2", "a = (m2 - m1) g / (m1 + m2 + I / r^2)"),
            "(m2 - m1)*g/(m1 + m2 + M/2)/q"),
        "uncommon",
        "The radius cancels only after writing I = M r^2 / 2 and a = alpha r; textbook results usually quote just the "
        "effective mass m1 + m2 + M/2, so the cancellation is rarely stated as a fact.", (9.0, 13.0)),
    conditional=r2.ConditionalV2(
        rv.ConditionalSpec(
            "the string's breaking strength", "force", "N", (150.0, 250.0, 350.0), "The string {relation} {value} {unit}.",
            (P("k0", "can withstand a tension of up to"), P("k1", "is rated to break only above")),
            "Max(m1*(g + a), m2*(g - a)) < q", "g", 20.0),
        r2.KOut(False, "If the string broke, the question 'the magnitude of the acceleration of the blocks' would have no "
                       "single answer: it breaks at the first instant of motion, so the acceleration is g afterwards but "
                       "no steady acceleration is ever reached, and the question does not say which time is meant."),
        (180.0, 320.0)),
    notes="R values (0.6, 0.9, 1.3) kg replace (0.4, 0.8, 1.2): 1.2 kg (digit copy) equalled the 1.2 m/s2 R answer at 0.8 kg. K values (150, 250, 350) N replace (120, 200, 300): 200 N shared its digits with the 2 kg pulley input.",
)

S02 = r2.RoleSpecV2(
    structure_id="S02", quantity_phrase="an earlier stretch of sliding", quantity_type="length", unit="m",
    values=(1.2, 2.6, 3.4), heldout_values=(1.8, 3.1),
    relevant=rv.RelevantWiring("d", "add", "The block starts from rest q further up the same incline, so the distance slid "
                                           "from rest at the constant acceleration g (sin theta - mu cos theta) is d + q."),
    pairs=(
        Pair("p0", "The release point lies {value} {unit} up {relation}.",
             "this incline from where the stated distance begins",
             "the neighbouring incline from its foot", "other_object_same_scene",
             "A second block released on a neighbouring incline moves under its own gravity and friction; nothing links "
             "its release point to this block's incline, so this block's distance from rest is the stated one.",
             ("released from rest", "kinetic friction"), "a short way",
             d_frame="A second block's release point lies {value} {unit} up {relation}.",
             frame_mismatch_reason="The R quantity is a stretch of the target block's own path, so the subject is the "
                                   "block's release point; a co-present D needs a second block and a second incline, so the "
                                   "subject noun phrase has to change as well as the attachment, and one frame would "
                                   "either read as a contradiction or leave the R reading ambiguous.",
             before_context_reason="The R sentence refers to 'the release point' and 'the stated distance', which the "
                                   "context introduces later, and its order relation ('up this incline from where the "
                                   "stated distance begins') presupposes the described slide."),
        Pair("p1", "The block slid {value} {unit} {relation}.", "down this incline before the stated distance began",
             "along a lab bench before being placed on this incline", "same_object_other_event",
             "The slide on the bench ended before the block was placed on the incline and released from rest, so it "
             "adds nothing to the distance the block slides on the incline.",
             ("released from rest", "kinetic friction"), "a short way"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the block's mass", "mass", "kg", (0.6, 2.5, 6.5), "The block {relation} {value} {unit}.",
            (P("c0", "has a mass of"), P("c1", "is a solid wooden block with a mass of")),
            "sqrt(2*d*(q*g*sin(theta) - mu*q*g*cos(theta))/q)",
            ("N = m g cos(theta)", "f = mu N", "m a = m g sin(theta) - f", "(1/2) m v^2 = (m g sin(theta) - f) d"),
            "sqrt(2*q*g*d*(sin(theta) - mu*cos(theta)))", nonnumeric_fill="a known mass"),
        "famous", "Mass independence of the acceleration on an incline (Galileo) is a headline classroom fact.", (1.8, 3.2)),
    conditional=r2.ConditionalV2(
        rv.ConditionalSpec(
            "the coefficient of static friction", "coefficient", "1", (0.25, 0.35, 0.45),
            "The coefficient of static friction between the block and the incline {relation} {value}.",
            (P("k0", "is"), P("k1", "has been measured as")), "q < tan(theta)", "0", 0.9),
        r2.KOut(False, "With a static coefficient above tan(theta) the block never slides, so 'the speed of the block after "
                       "it has slid that distance' has no answer (the block stays at rest and slides nowhere); the question "
                       "is ill posed, not merely changed."), (0.28, 0.42)),
    notes="R values (1.2, 2.6, 3.4) m replace (1, 2, 3) m: 3 m shared its digits with the 30 degree angle and none was clear "
          "of the 4 m input's neighbourhood; C masses avoid the displayed 4.",
)

S13 = r2.RoleSpecV2(
    structure_id="S13", quantity_phrase="a light cord", quantity_type="length", unit="m", values=(0.3, 0.5, 0.7),
    heldout_values=(0.4, 0.6),
    relevant=rv.RelevantWiring("L", "add", "A cord between the string and the bob puts the bob q further from the pivot, so "
                                           "the pendulum length becomes L + q."),
    pairs=(
        Pair("p0", "A {value} {unit} cord is {relation}.", "tied between the string and the bob",
             "hanging from a nail on the nearby wall", "other_object_same_scene",
             "A cord hanging from a nail on a nearby wall touches neither the string, the bob nor the stand, so the "
             "pendulum's length is still the stated string length.",
             ("light string", "small amplitude"), "short",
             before_context_reason="The R sentence refers to 'the string and the bob' before the context mentions them, and "
                                   "the context then introduces 'A small bob' with an indefinite article, which would read "
                                   "as a second bob."),
        Pair("p1", "Before the swing began, a {value} {unit} cord was knotted into the string just above the bob and "
                   "{relation}.", "left there", "cut out again", "same_object_undone_event",
             "The cord was knotted in and cut out again before the swing began, so the string that swings has only its "
             "stated length.", ("light string", "small amplitude"), "short"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the bob's mass", "mass", "kg", (0.2, 0.5, 2.0), "The bob {relation} {value} {unit}.",
            (P("c0", "has a mass of"), P("c1", "is a brass sphere with a mass of")),
            "2*pi*sqrt((q*L**2)/(q*g*L))", ("I = m L^2", "restoring torque = m g L theta", "omega^2 = m g L / I"),
            "2*pi*sqrt(L/(q*g))", nonnumeric_fill="a known mass"),
        "famous", "Mass independence of the pendulum period is a headline classroom fact.", (0.4, 1.0)),
    notes="R values (0.3, 0.5, 0.7) m replace (0.2, 0.4, 0.6) m: 0.2 m gave an R answer of 2.007 s sharing its leading digits "
          "with the value. No K (see roles_m0_a).",
)

S27 = r2.RoleSpecV2(
    structure_id="S27", quantity_phrase="a pressure rise", quantity_type="pressure", unit="kPa", values=(7.5, 15.0, 35.0),
    heldout_values=(8.0, 20.0),
    relevant=rv.RelevantWiring("p0", "add", "A pressure added at the free surface of a liquid at rest is transmitted "
                                            "undiminished (Pascal), so the surface pressure becomes p0 + q."),
    pairs=(
        Pair("p0", "A {value} {unit} pressure rise is then applied {relation}.",
             "to the liquid in this tank by a piston resting on its free surface",
             "to the liquid in a second tank by a piston resting on its free surface", "other_object_same_scene",
             "The piston presses on the liquid of a second tank; liquids in separate tanks share no pressure, so the "
             "pressure at the free surface of this tank stays as stated.",
             ("free surface", "filled with a liquid"), "small",
             before_context_reason="The sentence says the rise is 'then' applied to 'this tank', which presupposes the state "
                                   "described in the context; placed first it would be read as the final state and the "
                                   "stated surface pressure would no longer be a starting value."),
        Pair("p1", "A pump adds a {value} {unit} pressure rise to the air above this liquid and {relation}.",
             "holds it there", "then lets it out again", "same_object_undone_event",
             "The pump's pressure rise is let out of the air above the liquid again, so the pressure at the free surface is "
             "back at its stated value when the depth is considered.", ("free surface", "filled with a liquid"), "small"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the tank's cross-sectional area", "area", "m^2", (0.5, 2.0, 3.0), "The tank {relation} {value} {unit}.",
            (P("c0", "has a uniform horizontal cross-sectional area of"), P("c1", "has a flat base with an area of")),
            "p0 + rho*q*h*g/q", ("mass of the liquid column above the point: m = rho A h", "p = p0 + m g / A"),
            "(p0 + rho*g*h)*q", nonnumeric_fill="a known area"),
        "standard", "Pressure depends on depth and density, not on container shape or area, is taught with Pascal's vases "
                    "but is not a slogan like mass independence.", (0.8, 1.5)),
    notes="R values (7.5, 15, 35) kPa replace (10, 20, 40) kPa: 10 kPa has the digits of the 1000 kg/m3 input and of 101 kPa. "
          "No K (see roles_m0_a).",
)

S92 = r2.RoleSpecV2(
    structure_id="S92", quantity_phrase="a replacement liquid", quantity_type="density", unit="kg/m^3",
    values=(1150.0, 1250.0, 1350.0), heldout_values=(1300.0, 1400.0),
    relevant=rv.RelevantWiring("rho_l", "replace", "The tank's liquid is replaced and the string still holds the cube fully "
                                                   "submerged, so the buoyant force is q g a^3 and the tension (q - rho_s) g a^3."),
    pairs=(
        Pair("p0", "A liquid whose density is {value} {unit} {relation}.", "now replaces the original liquid in this tank",
             "now fills a second tank on the same bench", "other_object_same_scene",
             "A liquid in a second tank exerts no force on this cube; the buoyant force on this cube comes only from the "
             "liquid in its own tank, which is unchanged.", ("held at rest completely under the surface", "light vertical string"),
             "unknown",
             before_context_reason="The R sentence refers to 'the original liquid in this tank', which the context has not yet "
                                   "introduced, and 'now' presupposes the earlier state."),
        Pair("p1", "The tank {relation} a liquid whose density is {value} {unit}.", "is then drained and refilled with",
             "was earlier rinsed out with", "same_object_other_event",
             "The rinse liquid was drained out before the tank was filled with its stated liquid, so it plays no part in "
             "the force balance on the cube.", ("held at rest completely under the surface", "light vertical string"),
             "unknown"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the depth of the cube's top face", "length", "cm", (20.0, 50.0, 80.0),
            "The top face of the cube {relation} {value} {unit}.",
            (P("c0", "is at a depth of"), P("c1", "lies below the free surface of the liquid by")),
            "(rho_l*g*(q + a) - rho_l*g*q)*a**2 - rho_s*a**3*g",
            ("pressure on the top face: p_top = p_surface + rho_l g q",
             "pressure on the bottom face: p_bottom = p_surface + rho_l g (q + a)",
             "buoyant force: Fb = (p_bottom - p_top) a^2"),
            "rho_l*g*(q + a)*a**2 - rho_s*a**3*g", nonnumeric_fill="some depth"),
        "standard", "That the buoyant force on a fully submerged body does not depend on depth is standard in "
                    "treatments of Archimedes' principle but is not a headline fact.", (30.0, 65.0)),
    conditional=r2.ConditionalV2(
        rv.ConditionalSpec(
            "the string's breaking strength", "force", "N", (30.0, 50.0, 80.0), "The string {relation} {value} {unit}.",
            (P("k0", "can withstand a tension of up to"), P("k1", "is rated to break only above")),
            "T < q", "0", 2.0),
        r2.KOut(False, "With a breaking strength below the tension (3.92 N) the string would break, but the problem says the "
                       "cube 'is held at rest completely under the surface' by that string, so the premise is contradicted; "
                       "'the tension in the string' would be zero for a string that was never holding the cube."),
        (40.0, 65.0)),
    notes="R uses replace for the density as in M0. K as in M0.",
)

S20 = r2.RoleSpecV2(
    structure_id="S20", quantity_phrase="a shift of a stand", quantity_type="length", unit="cm", values=(6.0, 18.0, 30.0),
    heldout_values=(9.0, 22.0),
    relevant=rv.RelevantWiring("do", "add", "Moving the object q farther from the lens along the axis raises the object "
                                            "distance to do + q."),
    pairs=(
        Pair("p0", "The stand {relation} is then pushed {value} {unit} farther from the lens.",
             "that holds the object on the axis", "that holds a microphone on the bench", "other_object_same_scene",
             "A microphone stand moves a microphone on the bench; the object that the lens images is on its own stand and "
             "stays where the problem put it.", ("thin converging lens", "placed on the axis"), "a little",
             before_context_reason="The R sentence refers to 'the stand that holds the object on the axis' and says it is "
                                   "'then' pushed; the object and the lens are introduced only in the context."),
        Pair("p1", "The object was slid {value} {unit} {relation}.", "directly away from the lens after being placed on the axis",
             "along the bench before being placed on the axis", "same_object_other_event",
             "The slide along the bench ended before the object was placed on the axis at its stated distance, so it does "
             "not change that distance.", ("thin converging lens", "placed on the axis"), "a little"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the object's height", "length", "cm", (2.5, 3.5, 4.5), "The object {relation} {value} {unit}.",
            (P("c0", "is an upright arrow of height"), P("c1", "stands perpendicular to the axis with a height of")),
            "do*(q*f/(do - f))/q",
            ("ray parallel to the axis then through the focus: h_i / h_o = f / (do - f)",
             "ray through the centre of the lens: h_i / h_o = di / do"),
            "q*f/(do - f)", nonnumeric_fill="a known height"),
        "standard", "The lens equation has no object height in it, so the cancellation is visible in the formula; it is "
                    "taught with the magnification relations.", (3.0, 5.5)),
    notes="R values (6, 18, 30) cm replace (5, 15, 25) cm: 15 cm shared two digits with the 15.35 cm R answer. No K.",
)

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {"S01": S01, "S02": S02, "S13": S13, "S27": S27, "S92": S92, "S20": S20}

STRUCTURE_FACTORIES = {
    "S01": library.s01_atwood_massive_pulley,
    "S02": library.s02_rough_incline_speed,
    "S13": library_b.s13_pendulum_period,
    "S27": library_c.s27_hydrostatic_pressure,
    "S92": lib_fluids.s92_cube_held_under_liquid,
    "S20": library_b.s20_thin_lens_image,
}


def structure(structure_id: str) -> gr.Structure:
    return STRUCTURE_FACTORIES[structure_id]()
