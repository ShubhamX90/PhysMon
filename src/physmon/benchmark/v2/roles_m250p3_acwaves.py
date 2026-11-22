"""M250 phase 3, batch acwaves: v2.1 role-by-value specifications for the new structures S321 to S330 (acoustics and mechanical waves).

Every spec follows `roles_m0v21` (the v2.1 design) and the wording rules 1 to 8 of the earlier waves and the lessons of the two-judge
review (BRIEF_3): one R/D quantity with three study values and two held-out values; a co-present D (pair 0, `other_object_same_scene`)
whose object is introduced by a number-free scene clause in the base context of every cell, is of another type than the target object and
receives an ordinary, purposeful action, and a same-object D (pair 1, `same_object_other_event`: history in an earlier experiment, with
`for one run only` where something is attached) whose R twin names the moment of the question; the same frame, numeral and unit within a
pair, an attachment-only difference, word counts within three, marker- and consequence-free wording, value hygiene.

* C quantity where the physics supports a real cancellation (S322, S324, S325, S326, S327);
* K quantity where a genuine regime condition of the physics itself exists (S321 listener inside or outside the circle, S327 deep or
  shallow water, S328 cube fully or partly immersed); the kind of regime is recorded in `K_KINDS`. K_out is recorded as infeasible with
  the reason in every case.

`INFEASIBLE` holds the structures that cannot honestly carry the design (none in this batch); `NO_C` and `NO_K` hold the reason a
structure has no C or K quantity.
"""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_m250p3_acwaves as lw
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2

P = rv.Phrasing
Pair = r2.PhrasePair
CO = r2.D_KIND_CO_PRESENT
EVENT = r2.D_KIND_OTHER_EVENT
V21 = r2.VERSION_V21
CERT_VERSION = "v2.1"


def _spec(sid: str, **fields) -> r2.RoleSpecV2:
    return r2.RoleSpecV2(structure_id=sid, version=V21, author="agent (M250 phase 3, acwaves)", **fields)


def _ko(reason: str) -> r2.KOut:
    return r2.KOut(False, reason)


# --- S321 --------------------------------------------------------------------------------------------------------------------------

S321_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the distance of the microphone from the axis of the arm", "length", "m", (2.6, 4.1, 6.4),
        "The microphone {relation} {value} {unit} from the axis of the arm.", (P("k0", "stands"), P("k1", "is placed")),
        "q > r", "f*c/(c - v*q/r) - f*c/(c + v*q/r)", 0.2, nonnumeric_fill="a known distance"),
    _ko("The problem states that the microphone is outside the circle; a microphone inside the circle never has the buzzer moving "
        "straight at it, so the extreme shifts would be those of the component v q / r, and the stated question would be a different one."),
    (3.3, 5.2))

S321 = _spec(
    "S321", quantity_phrase="a further turning rate", quantity_type="angular_frequency", unit="rpm", values=(30.0, 55.0, 90.0),
    heldout_values=(40.0, 70.0),
    relevant=rv.RelevantWiring("rot", "add", "A further turning rate q of the arm makes its rate rot + q, which changes the speed of the "
                                             "buzzer and so the spread of the recorded frequencies."),
    conditional=S321_K,
    scene_clause="A potter's wheel turns in a corner of the room.",
    scene_object_rationale="A potter's wheel in a corner of the room is a machine of its own; its turning rate changes that wheel only, "
                           "so the arm, the buzzer and the recorded frequencies keep their stated values.",
    scene_refs=("potter's wheel",), target_terms=("the arm", "buzzer", "microphone"),
    pairs=(
        Pair("p0", "Before the recording is made, the turning rate of {relation} is raised by a further {value} {unit}.", "the arm",
             "the potter's wheel", CO,
             "Raising the turning rate of a potter's wheel changes that wheel only; the arm that carries the buzzer keeps its stated "
             "turning rate, so the recorded frequencies are the stated ones.", ("the air is still", "outside the circle"),
             "small amount",
             before_context_reason="The R sentence refers to 'the arm' and to the recording before the context introduces either."),
        Pair("p1", "{relation} turned faster by a further {value} {unit}.", "Before the recording is made, the arm is",
             "In an earlier experiment, the arm was", EVENT,
             "The arm was turned faster by the further amount in an earlier experiment, which is over; in the stated experiment it "
             "turns at the stated rate.", ("the air is still", "outside the circle"), "small amount"),
    ),
    notes="M250 phase 3: R is a further turning rate of the arm; K is the distance of the microphone from the axis (outside the circle, "
          "there is a tangent point towards and away); no C (see NO_C).")

# --- S322 --------------------------------------------------------------------------------------------------------------------------


def _arrival(n: int) -> str:
    return f"((q + (c + w - vs)*{n}/f)/(c + w - vo))"


S322_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the distance between the car and the cyclist when the horn starts to sound", "length", "m", (50.0, 130.0, 240.0),
        "The car {relation} {value} {unit} behind the cyclist when the horn starts to sound.", (P("c0", "is"), P("c1", "lies")),
        f"1/({_arrival(4)} - {_arrival(3)}) - f",
        ("crest n leaves the car at t = n / f and meets the cyclist at t = (q + (c + w - vs) n / f) / (c + w - vo)",
         "the heard frequency is the inverse of the spacing of two successive arrivals"),
        "f*(c + w - vo)/(c + w - vs)*(1 + q*f/(60*c)) - f", nonnumeric_fill="a known distance"),
    "uncommon", "That the frequency heard from a source and an observer in uniform motion does not depend on how far apart they are when "
                "the sound starts is true but is not a stated textbook fact.", (85.0, 180.0))

S322 = _spec(
    "S322", quantity_phrase="a further speed", quantity_type="speed", unit="m/s", values=(3.5, 14.0, 20.0), heldout_values=(2.8, 16.5),
    relevant=rv.RelevantWiring("vs", "add", "A further speed q of the car makes its speed vs + q relative to the road, which changes the "
                                            "speed of the car relative to the air and so the heard frequency."),
    cancelling=S322_C,
    scene_clause="A lorry drives along the other carriageway of the road.",
    scene_object_rationale="A lorry on the other carriageway is a vehicle of its own; its speed changes that lorry only, so the speeds of "
                           "the car and the cyclist and the frequency that the cyclist hears keep their stated values.",
    scene_refs=("lorry",), target_terms=("the car", "horn", "cyclist"),
    pairs=(
        Pair("p0", "Before the horn is heard, {relation} speeds up by a further {value} {unit}.", "the car", "the lorry", CO,
             "A lorry that speeds up on the other carriageway changes that lorry only; the car keeps its stated speed relative to the "
             "road, so the heard frequency is the stated one.", ("steady wind", "behind a cyclist"), "small amount",
             before_context_reason="The R sentence refers to 'the car' and to the horn before the context introduces either."),
        Pair("p1", "{relation} sped up by a further {value} {unit}.", "Before the horn sounded, the car had", "In an earlier experiment, the car had",
             EVENT,
             "The car sped up by the further amount in an earlier experiment, which is over; in the stated experiment it travels at the "
             "stated speed.", ("steady wind", "behind a cyclist"), "small amount"),
    ),
    notes="M250 phase 3: R is a further speed of the car; C is the distance between the car and the cyclist when the horn starts (it drops "
          "out of the spacing of two arrivals); no K (see NO_K).")

# --- S323 --------------------------------------------------------------------------------------------------------------------------

S323 = _spec(
    "S323", quantity_phrase="a further mass", quantity_type="mass", unit="kg", values=(0.7, 1.4, 2.6), heldout_values=(1.0, 2.3),
    relevant=rv.RelevantWiring("M", "add", "A further mass q on the block makes it M + q, which raises the tension along the whole rope and "
                                           "so the speed of the pulse."),
    scene_clause="A bucket of sand stands on the floor beside the rope.",
    scene_object_rationale="A bucket of sand on the floor is a body of its own, not attached to the rope; making it heavier changes the "
                           "bucket only, so the tension of the rope and the travel time of the pulse keep their stated values.",
    scene_refs=("bucket of sand",), target_terms=("the block", "rope", "pulse"),
    pairs=(
        Pair("p0", "Before the pulse is sent, {relation} is made heavier by a further {value} {unit}.", "the block", "the bucket of sand", CO,
             "Making a bucket of sand on the floor heavier changes the bucket only; the block at the lower end of the rope keeps its "
             "stated mass, so the tension and the travel time are the stated ones.", ("hangs at rest", "inextensible"), "small amount",
             before_context_reason="The R sentence refers to 'the block' and to the pulse before the context introduces either."),
        Pair("p1", "{relation} a further {value} {unit} of lead tied to it.",
             "Before the pulse is sent, the block gets", "For an earlier run only, the block got", EVENT,
             "The block got the further lead for an earlier run only, which is over; in the stated run it carries nothing beyond its "
             "stated mass.", ("hangs at rest", "inextensible"), "small amount"),
    ),
    notes="M250 phase 3: R is a further mass on the block; no C and no K (see NO_C, NO_K).")

# --- S324 --------------------------------------------------------------------------------------------------------------------------

_K2 = "omega*sqrt(rho*pi*d2**2/(4*T))*q"
S324_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the distance from the knot at which the power is read", "length", "m", (0.35, 0.80, 1.45),
        "The power is read {relation} {value} {unit} along the thick string from the knot.",
        (P("c0", "at a point"), P("c1", "at a position")),
        f"P0*4*Z1*Z2/((Z1 + Z2)**2 + Xm**2)*(cos({_K2})**2 + sin({_K2})**2)",
        ("the wave on the thick string is a travelling wave of unchanged amplitude with phase k q",
         "the power it carries is proportional to the square of its amplitude, cos^2(k q) + sin^2(k q) times the transmitted power"),
        f"Pt*cos({_K2})**2", nonnumeric_fill="a known distance"),
    "uncommon", "That a steady travelling wave on a lossless string carries the same power at every point is true, but it is rarely "
                "stated as a result of the junction problem.", (0.55, 1.5))

S324 = _spec(
    "S324", quantity_phrase="a further mass", quantity_type="mass", unit="g", values=(0.4, 0.7, 1.9), heldout_values=(0.6, 1.45),
    relevant=rv.RelevantWiring("m", "add", "A further mass q on the bead makes it m + q, which raises the impedance m omega of the bead and "
                                           "so lowers the power carried on."),
    cancelling=S324_C,
    scene_clause="A kitchen scale stands on the bench beside the strings.",
    scene_object_rationale="A kitchen scale on the bench is an instrument of its own, not touching the strings; adding mass to its pan "
                           "changes the scale only, so the bead at the knot and the power carried on keep their stated values.",
    scene_refs=("kitchen scale",), target_terms=("the bead", "knot", "strings", "wave"),
    pairs=(
        Pair("p0", "Before the wave is sent, a further {value} {unit} is added to {relation}.", "the bead at the knot",
             "the pan of the kitchen scale", CO,
             "Mass added to the pan of a kitchen scale changes the scale only; the bead at the knot keeps its stated mass, so the power "
             "carried on is the stated one.", ("acts as a point mass", "nothing returns"), "small amount",
             before_context_reason="The R sentence refers to 'the bead at the knot' and to the wave before the context introduces them."),
        Pair("p1", "{relation} a further {value} {unit} of solder stuck on it.",
             "Before the wave is sent, the bead gets", "For an earlier run only, the bead got", EVENT,
             "The bead got the further solder for an earlier run only, which is over; in the stated run it has only its stated mass.",
             ("acts as a point mass", "nothing returns"), "small amount"),
    ),
    notes="M250 phase 3: R is a further mass on the bead; C is the point on the thick string at which the power is read (a travelling "
          "wave carries the same power everywhere); no K (see NO_K).")

# --- S325 --------------------------------------------------------------------------------------------------------------------------

S325_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the cross-section area of the rail", "area", "cm^2", (55.0, 70.0, 85.0), "The rail {relation} {value} {unit}.",
        (P("c0", "has a cross-sectional area of"), P("c1", "has a cross-section of")),
        "d/c - d/sqrt((E*q)/(rho*q))",
        ("the stiffness of a piece of rail of length l is E q / l", "the mass of that piece is rho q l",
         "the pulse speed is sqrt(stiffness x length / mass)"),
        "d/c - d/sqrt(E*q/rho)", nonnumeric_fill="a known area"),
    "standard", "That the speed of a longitudinal pulse in a rod does not depend on its cross-section follows from stiffness and mass "
                "both being proportional to it; it is taught but not a headline fact.", (62.0, 74.0))

S325 = _spec(
    "S325", quantity_phrase="a further distance", quantity_type="length", unit="m", values=(140.0, 260.0, 450.0),
    heldout_values=(190.0, 310.0),
    relevant=rv.RelevantWiring("d", "add", "A further distance q along the track makes the distance of the listener from the struck end "
                                           "d + q, which lengthens both travel times and so the gap."),
    cancelling=S325_C,
    scene_clause="A cyclist rides along the road beside the track.",
    scene_object_rationale="A cyclist on the road beside the track is a person of another kind than the listener at the rail; where the "
                           "cyclist goes changes nothing about the rail, so the distance of the listener and the gap keep their stated "
                           "values.",
    scene_refs=("cyclist",), target_terms=("the listener", "rail", "hammer"),
    pairs=(
        Pair("p0", "Before the blow is struck, {relation} goes a further {value} {unit} along the track away from the hammer.", "the listener", "the cyclist", CO,
             "A cyclist who rides on along the road changes the cyclist's own position only; the listener at the rail keeps the stated "
             "distance from the struck end, so the gap is the stated one.", ("still air", "much thinner than the pulse"), "small amount",
             before_context_reason="The R sentence refers to 'the listener' and to the blow before the context introduces either."),
        Pair("p1", "{relation} gone a further {value} {unit} along the track away from the hammer.", "Before the blow is struck, the listener has",
             "In an earlier experiment, the listener had", EVENT,
             "The listener had gone the further distance along the track in an earlier experiment, which is over; in the stated "
             "experiment the listener is at the stated distance.", ("still air", "much thinner than the pulse"), "small amount"),
    ),
    notes="M250 phase 3: R is a further distance of the listener along the track; C is the cross-section of the rail (stiffness and mass "
          "scale together); no K (see NO_K).")

# --- S326 --------------------------------------------------------------------------------------------------------------------------

S326_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the area of the diaphragm of the microphone", "area", "cm^2", (1.8, 2.8, 4.4), "The diaphragm of the microphone {relation} {value} {unit}.",
        (P("c0", "has an area of"), P("c1", "covers")),
        "((eta*p1/(2*pi*r1**2) + eta*p2/(2*pi*r2**2))*q)/q",
        ("the sound power that falls on the diaphragm is the intensity times its area q",
         "the intensity is the power received divided by the area q"),
        "(eta*p1/(2*pi*r1**2) + eta*p2/(2*pi*r2**2))*q", nonnumeric_fill="a known area"),
    "standard", "That the intensity is the same however large the receiving area is follows from its definition as power per area; it "
                "is taught but not a headline fact.", (2.3, 3.6))

S326 = _spec(
    "S326", quantity_phrase="a further distance", quantity_type="length", unit="m", values=(4.5, 9.0, 14.0), heldout_values=(6.0, 11.0),
    relevant=rv.RelevantWiring("r2", "add", "A further distance q makes the distance of the second loudspeaker from the microphone r2 + q, "
                                            "which weakens its intensity as the inverse square of the distance."),
    cancelling=S326_C,
    scene_clause="A photographer has set a camera on a tripod in the field beside the loudspeakers.",
    scene_object_rationale="A camera on a tripod is a piece of equipment of its own and gives off no sound; where the photographer puts it changes "
                           "nothing about the loudspeakers or the microphone, so the intensity keeps its stated value.",
    scene_refs=("tripod",), target_terms=("loudspeaker", "microphone"),
    pairs=(
        Pair("p0", "Before the reading is taken, {relation} is moved a further {value} {unit} away from the microphone.", "the second loudspeaker",
             "the photographer's tripod", CO,
             "A tripod that is moved farther away changes the tripod's own position only; the second loudspeaker stays at the stated "
             "distance from the microphone, so the intensity is the stated one.", ("hard ground", "does not absorb"), "small amount",
             before_context_reason="The R sentence refers to 'the second loudspeaker' and to the reading before the context introduces them."),
        Pair("p1", "{relation} moved a further {value} {unit} away from the microphone.", "Before the reading is taken, the second loudspeaker has been",
             "In an earlier experiment, the second loudspeaker had been", EVENT,
             "The second loudspeaker had been moved the further distance in an earlier experiment, which is over; in the stated "
             "experiment it stands at the stated distance.", ("hard ground", "does not absorb"), "small amount"),
    ),
    notes="M250 phase 3: R is a further distance of the second loudspeaker; C is the area of the diaphragm of the microphone (intensity "
          "is power per area); no K (see NO_K).")

# --- S327 --------------------------------------------------------------------------------------------------------------------------

S327_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the density of the sea water", "density", "kg/m^3", (1018.0, 1024.0, 1029.0), "The sea water {relation} {value} {unit}.",
        (P("c0", "has a density of"), P("c1", "has a mean density of")),
        "D/(sqrt(q*g*k/q)/(2*k))",
        ("the restoring force per unit area of a surface displacement y is q g y, and the inertia per unit area is q y / k",
         "omega^2 = (q g) / (q / k) = g k, and the group speed is omega / (2 k)"),
        "D/(sqrt(g*k*q)/(2*k))", nonnumeric_fill="a known density"),
    "standard", "That the speed of deep-water gravity waves does not depend on the density of the water is classical; it is stated in "
                "many texts but is not the first result a solver recalls.", (1021.0, 1026.0))

S327_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the depth of the ocean", "length", "m", (2800.0, 4200.0, 5500.0), "The depth of the ocean {relation} {value} {unit}.",
        (P("k0", "is"), P("k1", "has been measured as")),
        "q > lam/2", "D/sqrt(g*q)", 30.0, nonnumeric_fill="a known depth"),
    _ko("The problem states that the ocean is much deeper than the wavelength; a depth comparable with the wavelength would contradict "
        "that statement, and the deep-water dispersion relation on which the question rests would no longer apply."),
    (3300.0, 4900.0))

S327 = _spec(
    "S327", quantity_phrase="a further distance", quantity_type="length", unit="km", values=(240.0, 520.0, 900.0),
    heldout_values=(360.0, 700.0),
    relevant=rv.RelevantWiring("D", "add", "A further distance q makes the distance of the storm centre D + q, which lengthens the "
                                           "travel time in proportion."),
    cancelling=S327_C, conditional=S327_K,
    scene_clause="A weather ship steams over the ocean beside the path of the swell.",
    scene_object_rationale="A weather ship steaming over the ocean is a vessel of its own, small against the swell; where it steams changes "
                           "nothing about the storm or the swell, so the travel time keeps its stated value.",
    scene_refs=("weather ship",), target_terms=("storm", "swell", "coast"),
    pairs=(
        Pair("p0", "Before the swell sets out, {relation} a further {value} {unit} out to sea.", "the storm centre drifts",
             "the weather ship steams", CO,
             "A weather ship that steams farther out changes the ship's own position only; the storm that raised the swell stays "
             "where it is stated, so the travel time is the stated one.", ("much deeper than the wavelength", "negligible"), "small amount",
             before_context_reason="The R sentence refers to 'the storm centre' and to the swell before the context introduces them."),
        Pair("p1", "{relation} a further {value} {unit} out to sea.", "Before the swell sets out, the storm centre has drifted",
             "In an earlier case, the storm centre had drifted", EVENT,
             "The storm centre had drifted the further distance farther out in an earlier case, which is over; in the stated case the "
             "storm is centred at the stated distance.", ("much deeper than the wavelength", "negligible"), "small amount"),
    ),
    notes="M250 phase 3: R is a further drift of the storm centre outwards; C is the density of the sea water (it cancels from omega^2); "
          "K is the depth of the ocean (deep-water regime).")

# --- S328 --------------------------------------------------------------------------------------------------------------------------

S328_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the depth of the lower face of the immersed cube below the water surface", "length", "cm", (9.0, 14.0, 19.0),
        "The lower face of the immersed cube {relation} {value} {unit} below the water surface.", (P("k0", "is"), P("k1", "lies")),
        "q > a", "f1 - sqrt((W - rw*a**2*q*g)/(ms*L))/2", 2.0, nonnumeric_fill="a known depth"),
    _ko("The problem states that the cube is completely immersed; a lower face less than one edge below the surface would leave the "
        "cube partly out of the water and contradict that statement, so the buoyant force would no longer be that of the whole cube."),
    (11.0, 16.0))

S328 = _spec(
    "S328", quantity_phrase="a further density", quantity_type="density", unit="kg/m^3", values=(22.0, 38.0, 55.0),
    heldout_values=(30.0, 46.0),
    relevant=rv.RelevantWiring("rw", "add", "A further density q makes the density of the water rw + q, which raises the buoyant force on "
                                            "the immersed cube and so lowers the tension of its string."),
    conditional=S328_K,
    scene_clause="A beaker of brine stands on the bench beside the tank, and no tube joins them.",
    scene_object_rationale="A beaker of brine on the bench is a vessel of its own; salt dissolved in it changes the brine in the beaker "
                           "only, so the water in the tank, the buoyant force and the beat keep their stated values.",
    scene_refs=("beaker", "brine"), target_terms=("the water in the tank", "tank", "cube", "strings"),
    pairs=(
        Pair("p0", "Before the strings are sounded, the density of {relation} is brought up by a further {value} {unit} with dissolved salt.",
             "the water in the tank", "the brine in the beaker", CO,
             "Salt dissolved in the brine of the beaker changes that brine only; the water in the tank keeps its stated density, so the "
             "buoyant force and the beat are the stated ones.", ("completely immersed", "in its fundamental"), "small amount",
             before_context_reason="The R sentence refers to 'the water in the tank' and to the strings before the context introduces them."),
        Pair("p1", "{relation} brought up by a further {value} {unit} with dissolved salt.",
             "Before the strings are sounded, the density of the water has been", "For an earlier experiment only, the density of the water had been",
             EVENT,
             "The density of the water had been brought up by the further amount with dissolved salt for an earlier experiment only, "
             "which is over; in the stated experiment the water has the stated density.",
             ("completely immersed", "in its fundamental"), "small amount"),
    ),
    notes="M250 phase 3: R is a further density of the water (dissolved salt); K is the depth of the lower face of the immersed cube "
          "(completely immersed regime); no C (see NO_C).")

# --- S330 --------------------------------------------------------------------------------------------------------------------------

S330 = _spec(
    "S330", quantity_phrase="a further distance", quantity_type="length", unit="km", values=(1.4, 3.5, 4.6), heldout_values=(2.0, 3.6),
    relevant=rv.RelevantWiring("s", "add", "A further distance q along the road makes the distance of the listener from the post s + q, "
                                           "which delays the boom by q / v."),
    scene_clause="A tractor drives along the road beside the listener.",
    scene_object_rationale="A tractor driving along the road is a farm machine of its own; how far it is driven changes nothing about the "
                           "aircraft, the post or the listener, so the time of the boom keeps its stated value.",
    scene_refs=("tractor",), target_terms=("the listener", "aircraft", "observation post"),
    pairs=(
        Pair("p0", "Before the aircraft arrives, {relation} goes a further {value} {unit} along the road in the direction of flight.",
             "the listener", "the tractor", CO,
             "A tractor driven on along the road changes the tractor's own position only; the listener keeps the stated distance from "
             "the post, so the time of the boom is the stated one.", ("still", "faster than sound"), "small amount",
             before_context_reason="The R sentence refers to 'the listener' and to the aircraft before the context introduces them."),
        Pair("p1", "{relation} gone a further {value} {unit} along the road in the direction of flight.",
             "Before the aircraft arrives, the listener has", "In an earlier experiment, the listener had", EVENT,
             "The listener had gone the further distance along the road in an earlier experiment, which is over; in the stated "
             "experiment the listener is at the stated distance from the post.", ("still", "faster than sound"), "small amount"),
    ),
    notes="M250 phase 3: R is a further distance of the listener along the road; no C and no K (see NO_C, NO_K).")

# --- tables ------------------------------------------------------------------------------------------------------------------------

SPECS: dict[str, r2.RoleSpecV2] = {s.structure_id: s for s in (S321, S322, S323, S324, S325, S326, S327, S328, S330)}
ROLE_SPECS = SPECS

STRUCTURE_FACTORIES = {f().structure_id: f for f in lw.ALL}

INFEASIBLE: dict[str, str] = {
    "S329": "No natural R quantity: the fork frequency cannot be raised (a fork is replaced, not retuned) and any change of it or of the "
            "lengths contradicts the two stated resonance lengths; the lengths and the frequency are all stated measurements. The structure "
            "and its solver stay in lib_m250p3_acwaves.",
}

NO_C: dict[str, str] = {
    "S321": "The spread depends only on f, r, rot and c; no further quantity enters a relation of the graph and leaves it, and the only "
            "other stated quantity of the situation, the place of the microphone, fixes a regime and does not cancel.",
    "S323": "The travel time depends on the block, the mass and the length of the rope and g; a quantity such as the thickness of the rope "
            "does not enter any relation, so nothing enters a relation and cancels.",
    "S328": "The beat depends on the cubes, the water, the strings and g; the quantities that could drop out (the pulley size, the "
            "tank size) never enter a relation, so no stated quantity enters the derivation and cancels.",
    "S330": "The delay depends on h, s, v and c; no further quantity enters a relation and leaves it, and the flight line carries no "
            "stated quantity whose effect cancels.",
}

NO_K: dict[str, str] = {
    "S322": "The Doppler law with a wind holds for any source speed relative to the air below the speed of sound; that is a property "
            "of two inputs, not of a further quantity with a threshold, and no other regime changes the answer at the stated precision.",
    "S323": "The local-tension law holds for every block and rope of the stated kind; no further quantity switches the law, and a pulse "
            "that is not small would need a different, non-linear treatment that has no closed form.",
    "S324": "The point-mass treatment of the bead is stated; the length of the bead would be a regime quantity, but at any length for "
            "which the answer still equals the point-mass value the exact law differs from it by less than the stated precision, so "
            "no value of it separates the two laws honestly.",
    "S325": "The thin-rod speed holds for the stated rail; the regime quantity (the width of the rail against the length of the pulse) "
            "would need the length of the pulse, which is not part of this problem.",
    "S326": "The half-space intensity holds at every distance for a small source on hard ground; no further quantity with a threshold "
            "changes the law at the stated precision.",
    "S330": "The Mach cone exists because the speed exceeds the speed of sound, which is stated and fixed by two inputs; no further "
            "quantity can place the situation outside that regime without contradicting the base problem.",
}

# The kind of regime that each K quantity expresses (a condition of the physics itself, not an equipment rating).
K_KINDS: dict[str, str] = {
    "S321": "geometry of the line of sight (listener outside the circle: a point where the source moves straight at the listener)",
    "S327": "deep-water regime (depth greater than half the wavelength; otherwise the long-wave speed sqrt(g h) takes over)",
    "S328": "complete immersion (the lower face is more than one edge below the surface; otherwise the buoyant force is that of the "
            "submerged part)",
}


def structure(structure_id: str) -> gr.Structure:
    """The new structure with the spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), SPECS[structure_id].scene_clause)


# What the H4 trace extractor (`TraceContext.target_phrases` / `target_symbols`) must read as a statement of the target.
TARGET_TERMS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "S321": (("highest frequency", "exceed the lowest"), ("df", "Δf")),
    "S322": (("frequency of the horn that the cyclist hears exceed", "exceed the frequency"), ("df", "Δf")),
    "S323": (("how long does the pulse take", "pulse take to travel"), ("t", "T")),
    "S324": (("power is carried on along the thick string", "power is carried"), ("Pt", "P_t", "P")),
    "S325": (("after the pulse in the rail", "sound through the air arrive"), ("gap", "Δt", "t")),
    "S326": (("total sound intensity", "intensity at the microphone"), ("i", "I", "I_tot")),
    "S327": (("energy of the swell take to reach", "how long"), ("t", "T")),
    "S328": (("beat frequency",), ("beat", "f_beat", "Δf")),
    "S330": (("how long after the aircraft passes", "sonic boom"), ("t", "T")),
}
