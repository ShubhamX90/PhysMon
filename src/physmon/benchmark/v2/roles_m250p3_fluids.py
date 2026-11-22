"""M250 phase 3, batch fluids: v2.1 role-by-value specifications for the new structures S311 to S320 (plan revision v2.2, section G, the
wording rules 1-8 of the M0 v2.1/v2.2 panel review and the lessons of the M250 two-judge review; admission standard 3.2, 6.1, 6.2, 6.3).

Every spec follows `roles_m0v21` (the v2.1 design) on instance 0 of the new structure:

* one R/D quantity with three study values and two held-out values; a co-present D (pair 0, `other_object_same_scene`) whose object is
  introduced by a number-free scene clause in the base context of every cell and is of another type than the target, and a same-object
  D (pair 1, `same_object_other_event`: an earlier experiment, "for one experiment only" wherever the event adds or replaces something,
  never a change applied and then reversed), the same frame, numeral and unit within a pair, an attachment-only difference, word counts
  within three, marker- and consequence-free wording, value hygiene;
* every R sentence reads as a further change of the stated value ("is raised by", "is topped up by", "a further"), with the change
  before the asked moment, and no R, D or N sentence contradicts the base text or the scene clause;
* a C quantity where the physics supports a real cancellation (S311, S312, S313, S314, S316, S317, S320); the familiarity of each is tagged;
* a K quantity where a genuine regime condition of the physics itself exists (S314 turbulence, S315 Stokes drag, S316 free floating,
  S318 cavitation); the kind of regime is recorded in `K_KINDS`. K_out is infeasible in every case (the premise is contradicted).

`INFEASIBLE` holds the structures that cannot honestly carry the design (none in this batch); `NO_C` and `NO_K` hold the reason a
structure has no C or K quantity, so that an absence is a judgement on record and not an omission.
"""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_m250p3_fluids as lf
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2

CERT_VERSION = "v2.1"
P = rv.Phrasing
Pair = r2.PhrasePair
CO = r2.D_KIND_CO_PRESENT
EVENT = r2.D_KIND_OTHER_EVENT
V21 = r2.VERSION_V21


def _spec(sid: str, **fields) -> r2.RoleSpecV2:
    return r2.RoleSpecV2(structure_id=sid, version=V21, author="agent (M250 phase 3, fluids)", **fields)


def _ko(reason: str) -> r2.KOut:
    return r2.KOut(False, reason)


# --- S311 --------------------------------------------------------------------------------------------------------------------------

S311_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the atmospheric pressure", "pressure", "kPa", (92.0, 94.0, 96.0), "The atmospheric pressure {relation} {value} {unit}.",
        (P("c0", "is"), P("c1", "at the site is")),
        "(rho*g*w*(d*H**2/2 + H**3/3) + q*w*H**2/2 - q*w*H**2/2)/H",
        ("absolute pressure on the wet face of the gate p = q + rho g z", "torque of the wet face about the hinge, the integral of p w s ds, "
         "which contains q w H^2/2", "torque of the air on the dry face about the hinge, q w H^2/2",
         "net torque = torque of the wet face minus torque of the dry face"),
        "(rho*g*w*(d*H**2/2 + H**3/3) + q*w*H**2/2)/H", nonnumeric_fill="a known value"),
    "standard", "That the atmosphere pushes equally on both faces of a gate and so does not change the holding force is true, but it is "
                "usually left to the reader to see and is not stated as a fact.", (93.0, 97.0))

S311 = _spec(
    "S311", quantity_phrase="a further depth of water", quantity_type="length", unit="m", values=(0.35, 0.65, 1.4),
    heldout_values=(0.45, 0.85),
    relevant=rv.RelevantWiring("d", "add", "Water added to the reservoir before the force is applied raises the level above the hinge, so d "
                                           "becomes d + q."),
    cancelling=S311_C,
    scene_clause="A stock tank for cattle stands beside the reservoir, with no channel between them.",
    scene_object_rationale="A stock tank for cattle is a vessel outside the reservoir; water added to it does not reach the gate, so the "
                           "level of the water above the hinge is the stated one.",
    scene_refs=("stock tank",), target_terms=("reservoir", "gate", "hinge"),
    pairs=(
        Pair("p0", "Before the force is applied, the water level in {relation} is raised by {value} {unit}.", "the reservoir",
             "the stock tank", CO,
             "Water added to the stock tank stays in the tank; the reservoir keeps its stated water level, and the gate, the hinge and "
             "the holding force are as stated.", ("hinged along its top edge", "The water is at rest"), "a modest height",
             before_context_reason="The R sentence refers to 'the reservoir' before the context introduces it."),
        Pair("p1", "{relation} raised by {value} {unit}.",
             "Before the force is applied, the water level in the reservoir has been",
             "For an earlier experiment only, the water level in the reservoir had been", EVENT,
             "The water level of the reservoir had been raised in an earlier experiment only; in the stated run the level is the stated one.",
             ("hinged along its top edge", "The water is at rest"), "a modest height"),
    ),
    notes="M250 phase 3: C is the atmospheric pressure (it acts on both faces of the gate); no K (see NO_K).")

# --- S312 --------------------------------------------------------------------------------------------------------------------------

S312_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the density of the water", "density", "kg/m^3", (1020.0, 1040.0, 1060.0), "The density of the water {relation} {value} {unit}.",
        (P("c0", "is"), P("c1", "is measured as")),
        "(q*pi*(4*R*h0**(3/2)/3 - 2*h0**(5/2)/5))/(q*a*sqrt(2*g))",
        ("mass of the water in the bowl at depth h, dm = q A(h) dh", "mass outflow rate through the hole = q a sqrt(2 g h)",
         "time = the integral of dm over the mass outflow rate"),
        "pi*h0**2*(R - h0/3)/(a*sqrt(2*g*h0))", nonnumeric_fill="a known density"),
    "standard", "That the time to drain does not depend on the density of the liquid follows from the mass in the bowl and the mass "
                "outflow rate both being proportional to it, but it is not stated as a fact in a first treatment.", (1030.0, 1050.0))

S312 = _spec(
    "S312", quantity_phrase="a further depth of water", quantity_type="length", unit="cm", values=(4.2, 7.3, 11.0),
    heldout_values=(5.6, 9.1),
    relevant=rv.RelevantWiring("h0", "add", "Water topped up in the bowl before the hole is made adds to the initial depth, so h0 becomes "
                                            "h0 + q."),
    cancelling=S312_C,
    scene_clause="A watering can stands on the bench beside the bowl.",
    scene_object_rationale="A watering can is a separate vessel; water poured into it does not enter the bowl, so the initial depth of "
                           "the water in the bowl is the stated one.",
    scene_refs=("watering can",), target_terms=("bowl", "hole", "hemisphere"),
    pairs=(
        Pair("p0", "Before the hole is made, the water in {relation} is topped up by {value} {unit}.", "the bowl", "the watering can",
             CO,
             "Water topped up in the watering can stays in the can; the bowl keeps its stated initial depth and the hole and the flow "
             "law are as stated.", ("rim horizontal and open to the air", "the speed of the water surface is negligible"), "a modest depth",
             before_context_reason="The R sentence refers to 'the bowl' and 'the hole' before the context introduces them."),
        Pair("p1", "{relation} topped up by {value} {unit}.",
             "Before the hole is made, the water in the bowl has been",
             "For an earlier experiment only, the water in the bowl had been", EVENT,
             "The water in the bowl had been topped up in an earlier experiment only; in the stated run the bowl starts at its stated depth.",
             ("rim horizontal and open to the air", "the speed of the water surface is negligible"), "a modest depth"),
    ),
    notes="M250 phase 3: C is the density of the water (Torricelli draining does not depend on it); no K (see NO_K).")

# --- S313 --------------------------------------------------------------------------------------------------------------------------

S313_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the atmospheric pressure", "pressure", "kPa", (91.0, 92.0, 94.0), "The air outside the tubes {relation} {value} {unit}.",
        (P("c0", "is at a pressure of"), P("c1", "stays at a pressure of")),
        "(q + ((q + p) - q)*frac) - q",
        ("absolute pressure at the inlet of the first tube = q + p", "absolute pressure at the joint = q + (absolute inlet pressure - q) "
         "times the fraction that remains at the joint", "gauge pressure at the joint = absolute pressure at the joint - q"),
        "q + p*frac", nonnumeric_fill="a known pressure"),
    "standard", "That the gauge pressure at the joint does not depend on the pressure of the surrounding air follows from measuring "
                "every pressure above the air, but it is not stated as a fact in a first treatment.", (97.0, 99.0))

S313 = _spec(
    "S313", quantity_phrase="a further length of tube", quantity_type="length", unit="m", values=(0.7, 1.7, 3.1),
    heldout_values=(0.9, 2.4),
    relevant=rv.RelevantWiring("L2", "add", "Tube added to the second tube before the oil is forced through lengthens it, so L2 becomes "
                                            "L2 + q."),
    cancelling=S313_C,
    scene_clause="A garden hose lies coiled on the bench beside the tubes.",
    scene_object_rationale="A garden hose on the bench is a separate length of hose outside the tubes; lengthening it does not change "
                           "the second tube, so the length of the second tube is the stated one.",
    scene_refs=("garden hose",), target_terms=("tube", "joint", "oil"),
    pairs=(
        Pair("p0", "Before the oil is forced through, {relation} is lengthened by {value} {unit}.", "the second tube",
             "the garden hose", CO,
             "Lengthening the garden hose changes nothing in the tubes; the second tube keeps its stated length and radius, and the "
             "flow of the oil is as stated.", ("joined end to end", "steady, laminar and fully developed"), "a modest length",
             before_context_reason="The R sentence refers to 'the second tube' before the context introduces it."),
        Pair("p1", "{relation} lengthened by {value} {unit}.",
             "Before the oil is forced through, the second tube has been",
             "For an earlier experiment only, the second tube had been", EVENT,
             "The second tube had been lengthened in an earlier experiment only; in the stated run it has its stated length.",
             ("joined end to end", "steady, laminar and fully developed"), "a modest length"),
    ),
    notes="M250 phase 3: C is the atmospheric pressure (gauge against absolute); no K (see NO_K).")

# --- S314 --------------------------------------------------------------------------------------------------------------------------

S314_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the pressure at the downstream tapping", "pressure", "kPa", (173.0, 181.0, 205.0),
        "The pressure at the downstream tapping {relation} {value} {unit}.", (P("c0", "is"), P("c1", "is measured as")),
        "((q + dp) - q)",
        ("absolute pressure at the upstream tapping = pressure at the downstream tapping q + the pressure drop dp",
         "pressure drop = pressure at the upstream tapping - q"),
        "q + dp", nonnumeric_fill="a known pressure"),
    "uncommon", "That the pressure drop between two tappings does not depend on the level of the pressure in the pipe follows from the "
                "definition of a drop, but it is not stated as a fact when a pressure at one tapping is quoted.", (157.0, 194.0))

S314_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the Reynolds number above which the flow is turbulent", "reynolds_number", "1", (2400.0, 2600.0, 3000.0),
        "The flow in a smooth pipe {relation} {value} {unit}.",
        (P("k0", "becomes turbulent above a Reynolds number of"), P("k1", "is turbulent at Reynolds numbers above")),
        "Re > q", "32*eta*L*v/D**2", 900000.0, nonnumeric_fill="a known limit"),
    _ko("A Reynolds number above which the flow is turbulent that lay above the actual Reynolds number would make the flow laminar, "
        "which contradicts the stated condition that the flow is turbulent, so the friction law of the problem would not give the "
        "pressure drop; the premise is contradicted, not merely changed."),
    (2800.0, 3200.0))

S314 = _spec(
    "S314", quantity_phrase="a further distance between the tappings", quantity_type="length", unit="m", values=(9.0, 17.0, 36.0),
    heldout_values=(7.0, 26.0),
    relevant=rv.RelevantWiring("L", "add", "Moving the downstream tapping farther downstream adds to the distance between the tappings, so "
                                           "L becomes L + q."),
    cancelling=S314_C, conditional=S314_K,
    scene_clause="A row of marker posts stands along the lawn beside the pipe.",
    scene_object_rationale="A row of marker posts on the lawn is a line of posts outside the pipe; moving its last post does not change "
                           "the pipe, so the distance between the tappings is the stated one.",
    scene_refs=("marker post",), target_terms=("pipe", "tapping", "tappings", "flow"),
    pairs=(
        Pair("p0", "Before the pressures are read, {relation} is moved {value} {unit} further along.",
             "the downstream tapping of the pipe", "the last marker post", CO,
             "Moving the last marker post along the lawn changes nothing in the pipe; the tappings keep their stated distance, and the "
             "flow and the friction law are as stated.", ("long, straight, smooth, horizontal", "The flow is turbulent"),
             "a modest distance",
             before_context_reason="The R sentence refers to 'the pipe' and its 'tapping' before the context introduces them."),
        Pair("p1", "{relation} moved {value} {unit} further along.",
             "Before the pressures are read, the downstream tapping has been",
             "For an earlier experiment only, the downstream tapping had been", EVENT,
             "The downstream tapping had been moved in an earlier experiment only; in the stated run the tappings have their stated distance.",
             ("long, straight, smooth, horizontal", "The flow is turbulent"), "a modest distance"),
    ),
    notes="M250 phase 3: C is the pressure at the downstream tapping (a drop is a difference), K is the Reynolds number of the onset of "
          "turbulence (laminar flow would give the Poiseuille drop).")

# --- S315 --------------------------------------------------------------------------------------------------------------------------

S315_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the Reynolds number limit of Stokes' law", "reynolds_number", "1", (0.5, 1.6, 2.7),
        "Stokes' law {relation} {value} {unit}.", (P("k0", "holds up to a Reynolds number of"),
                                                   P("k1", "is valid below a Reynolds number of")),
        "rf*(S*n**2*x2)*2*r/eta < q", "t*(1 + 3*q/16)", 1e-8, nonnumeric_fill="a known limit"),
    _ko("A Reynolds number above the limit of Stokes' law would make the drag on the particle something other than the stated Stokes "
        "drag, so the time asked for would belong to a different drag law; the premise is contradicted, not merely changed."),
    (0.7, 1.2))

S315 = _spec(
    "S315", quantity_phrase="a further depth of suspension", quantity_type="length", unit="cm", values=(1.7, 2.6, 4.2),
    heldout_values=(3.0, 3.8),
    relevant=rv.RelevantWiring("x1", "subtract", "Suspension topped up in the tube before the rotor is started moves its surface towards "
                                                 "the axis by the added length, so x1 becomes x1 - q."),
    conditional=S315_K,
    scene_clause="A sample bottle of the suspension stands on the bench beside the centrifuge.",
    scene_object_rationale="A sample bottle is a vessel outside the centrifuge; suspension added to it does not enter the tube, so the "
                           "position of the surface of the suspension in the tube is the stated one.",
    scene_refs=("sample bottle",), target_terms=("tube", "rotor", "particle"),
    pairs=(
        Pair("p0", "Before the rotor is started, the suspension in {relation} is topped up by {value} {unit}.", "the tube",
             "the sample bottle", CO,
             "Suspension topped up in the sample bottle stays in the bottle; the tube keeps its stated surface position, and the "
             "rotation and the drag law are as stated.", ("lies along a radius of a rotor", "the drag on each particle is the Stokes drag"),
             "a modest depth",
             before_context_reason="The R sentence refers to 'the tube' and 'the rotor' before the context introduces them."),
        Pair("p1", "{relation} topped up by {value} {unit}.",
             "Before the rotor is started, the suspension in the tube has been",
             "For an earlier experiment only, the suspension in the tube had been", EVENT,
             "The suspension in the tube had been topped up in an earlier experiment only; in the stated run the surface is at its stated position.",
             ("lies along a radius of a rotor", "the drag on each particle is the Stokes drag"), "a modest depth"),
    ),
    notes="M250 phase 3: K is the Reynolds number limit of Stokes' law (creeping-flow regime); no C (see NO_C).")

# --- S316 --------------------------------------------------------------------------------------------------------------------------

S316_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the depth of the oil above the cube", "length", "cm", (12.0, 17.0, 26.0),
        "The surface of the oil {relation} {value} {unit} above the top face of the cube.", (P("c0", "is"), P("c1", "stands")),
        "(W/a**2 - (ro*g*(q + a) - ro*g*q))/(g*(rw - ro))",
        ("pressure on the top face of the cube p_top = rho_o g q", "pressure on the bottom face of the cube p_bot = rho_o g (q + a - x) + "
         "rho_w g x", "net upward pressure force per unit area = p_bot - p_top, set equal to W/a^2"),
        "(W/a**2 - ro*g*(q + a))/(g*(rw - ro))", nonnumeric_fill="a known depth"),
    "uncommon", "That the depth of a floating body below the interface does not depend on how deep the top of the body lies under the "
                "surface follows from Archimedes' principle, but a pressure at the top face is usually carried into the calculation.",
    (14.0, 21.0))

S316_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the depth of the water layer under the oil", "length", "cm", (14.0, 19.0, 27.0),
        "The layer of water under the oil {relation} {value} {unit} deep.", (P("k0", "is"), P("k1", "is found to be")),
        "q > x", "q", 2.0, nonnumeric_fill="a known depth"),
    _ko("A water layer shallower than the depth that the cube needs would leave the cube resting on the bottom of the tank, which "
        "contradicts the stated condition that it floats freely, so the depth of its bottom face would be the depth of the layer; the "
        "premise is contradicted, not merely changed."),
    (16.0, 23.0))

S316 = _spec(
    "S316", quantity_phrase="a further lead weight", quantity_type="mass", unit="g", values=(12.0, 19.0, 37.0),
    heldout_values=(15.0, 26.0),
    relevant=rv.RelevantWiring("m", "add", "A further lead weight fixed to the top face before the cube is put into the tank adds to the "
                                           "mass of the lead on the cube, so m becomes m + q."),
    cancelling=S316_C, conditional=S316_K,
    scene_clause="A fishing float lies on the bench beside the tank.",
    scene_object_rationale="A fishing float on the bench is a body outside the tank; a lead weight fixed to it does not load the cube, "
                           "so the mass of lead on the cube is the stated one.",
    scene_refs=("fishing float",), target_terms=("cube", "lead weight", "tank"),
    pairs=(
        Pair("p0", "Before the cube is put into the tank, a further {value} {unit} lead weight is fixed to {relation}.",
             "the top face of the cube", "the fishing float", CO,
             "A lead weight fixed to the fishing float stays on the float; the cube keeps its stated load, and the liquids and their "
             "densities are as stated.", ("floats freely and at rest", "do not mix"), "small",
             before_context_reason="The R sentence refers to 'the cube' and 'the tank' before the context introduces them."),
        Pair("p1", "{relation} fitted with a further {value} {unit} lead weight.",
             "Before the cube is put into the tank, it has been",
             "For an earlier experiment only, the cube had been", EVENT,
             "The cube had carried the further lead weight in an earlier experiment only; in the stated run it carries only its stated load.",
             ("floats freely and at rest", "do not mix"), "small"),
    ),
    notes="M250 phase 3: C is the depth of the oil above the cube (pressures at the top and bottom faces), K is the depth of the water "
          "layer (floating freely versus resting on the bottom).")

# --- S317 --------------------------------------------------------------------------------------------------------------------------

S317_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the depth to which the tube is dipped", "length", "mm", (14.0, 16.0, 21.0),
        "The lower end of the tube {relation} {value} {unit} below the level of the water in the dish.", (P("c0", "is"), P("c1", "lies")),
        "rho*pi*r**2*((q + 2*gam*cos(th)/(rho*g*r)) - q)",
        ("height of the water in the tube above its lower end = q + h", "mass of the water above the level in the dish = rho pi r^2 "
         "((q + h) - q)"),
        "rho*pi*r**2*(q + 2*gam*cos(th)/(rho*g*r))", nonnumeric_fill="a known depth"),
    "standard", "That the capillary rise does not depend on how far the tube is dipped follows from measuring the column from the level in "
                "the dish, but a depth that is quoted is easily added to the height.", (18.0, 25.0))

S317 = _spec(
    "S317", quantity_phrase="another tube bore", quantity_type="length", unit="mm", values=(0.9, 1.1, 1.3),
    heldout_values=(0.3, 0.7),
    relevant=rv.RelevantWiring("r", "replace", "Replacing the tube before the dipping gives the water a tube of inner radius q, so r is "
                                               "replaced by q."),
    cancelling=S317_C,
    scene_clause="A rubber-bulb dropper lies on the bench beside the dish.",
    scene_object_rationale="A dropper on the bench is a separate instrument outside the dish; replacing its nozzle does not change the "
                           "tube, so the inner radius of the tube is the stated one.",
    scene_refs=("dropper",), target_terms=("tube", "dish", "meniscus"),
    pairs=(
        Pair("p0", "Before the dipping, {relation} is replaced by one with a {value} {unit} inner radius.", "the glass tube",
             "the nozzle of the dropper", CO,
             "Replacing the nozzle of the dropper changes nothing in the tube or the dish; the tube keeps its stated radius, and the "
             "water and its contact angle are as stated.", ("clean vertical glass tube", "The water is at rest"), "somewhat different",
             before_context_reason="The R sentence refers to 'the glass tube' before the context introduces it."),
        Pair("p1", "{relation} replaced by one with a {value} {unit} inner radius.",
             "Before the dipping, the glass tube has been",
             "For an earlier experiment only, the glass tube had been", EVENT,
             "The tube had been replaced by one of another bore in an earlier experiment only; in the stated run the tube has its stated radius.",
             ("clean vertical glass tube", "The water is at rest"), "different"),
    ),
    notes="M250 phase 3: C is the depth to which the tube is dipped (the column is measured from the level in the dish); no K (see NO_K).")

# --- S318 --------------------------------------------------------------------------------------------------------------------------

S318_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the vapour pressure of the water", "pressure", "kPa", (1.7, 2.3, 3.2),
        "The vapour pressure of the water at its temperature {relation} {value} {unit}.", (P("k0", "is"), P("k1", "is taken as")),
        "p2 > q", "q", 600.0, nonnumeric_fill="a known pressure"),
    _ko("A vapour pressure above the pressure that the throat would reach would make the water boil there, which contradicts the "
        "stated condition that the water stays liquid, so the pressure in the throat would stay at the vapour pressure; the premise is "
        "contradicted, not merely changed."),
    (2.0, 2.8))

S318 = _spec(
    "S318", quantity_phrase="a further flow", quantity_type="volume_flow_rate", unit="L/s", values=(3.5, 6.5, 9.0),
    heldout_values=(4.5, 7.5),
    relevant=rv.RelevantWiring("Q", "add", "Water added to the flow by a booster pump before the pressure is read adds to the volume flow "
                                           "rate through the pipe, so Q becomes Q + q."),
    conditional=S318_K,
    scene_clause="An ornamental fountain with a pump of its own stands in the garden beside the pipe.",
    scene_object_rationale="A fountain with its own pump is a water feature outside the pipe; a booster pump on it does not change the "
                           "flow through the pipe, so the volume flow rate in the pipe is the stated one.",
    scene_refs=("fountain",), target_terms=("pipe", "throat", "regulator"),
    pairs=(
        Pair("p0", "Before the pressure in the throat is read, a booster pump adds {value} {unit} to the flow through {relation}.",
             "the pipe", "the fountain", CO,
             "A booster pump on the fountain adds to the flow of the fountain alone; the pipe keeps its stated flow rate, and the "
             "regulator and the sections are as stated.", ("narrows smoothly", "flows without friction"), "a little water",
             before_context_reason="The R sentence refers to 'the throat' and 'the pipe' before the context introduces them."),
        Pair("p1", "{relation} {value} {unit} to the flow through the pipe.",
             "Before the pressure in the throat is read, a booster pump has added",
             "For an earlier experiment only, a booster pump had added", EVENT,
             "A booster pump had added to the flow through the pipe in an earlier experiment only; in the stated run the pipe carries its stated flow.",
             ("narrows smoothly", "flows without friction"), "a little water"),
    ),
    notes="M250 phase 3: K is the vapour pressure of the water (cavitation limit of the throat pressure); no C (see NO_C).")

# --- S319 --------------------------------------------------------------------------------------------------------------------------

S319 = _spec(
    "S319", quantity_phrase="an additional layer of ice", quantity_type="length", unit="mm", values=(3.0, 6.0, 9.0),
    heldout_values=(4.0, 7.0),
    relevant=rv.RelevantWiring("r", "add", "A further layer of ice grown on the hailstone before the fall adds to its radius, so r becomes "
                                           "r + q."),
    scene_clause="An icicle hangs from the eaves of a shed nearby.",
    scene_object_rationale="An icicle hanging from a shed is a body of ice outside the hailstone; a layer of ice growing on it does not "
                           "change the hailstone, so the radius of the hailstone is the stated one.",
    scene_refs=("icicle",), target_terms=("hailstone", "fall", "air"),
    pairs=(
        Pair("p0", "Before the fall is observed, {relation} grows an additional {value} {unit} of ice on its surface.", "the hailstone",
             "the icicle", CO,
             "Ice grown on the icicle stays on the icicle; the hailstone keeps its stated radius and density, and the drag law and the "
             "air are as stated.", ("still air", "does not melt or change in size"), "modest amount",
             before_context_reason="The R sentence refers to 'the hailstone' and 'the fall' before the context introduces them."),
        Pair("p1", "{relation} an additional {value} {unit} of ice on its surface.",
             "Before the fall is observed, the hailstone has grown",
             "For an earlier experiment only, the hailstone had grown", EVENT,
             "The hailstone had grown the further ice in an earlier experiment only; in the stated run it has its stated radius.",
             ("still air", "does not melt or change in size"), "modest amount"),
    ),
    notes="M250 phase 3: no C and no K (see NO_C, NO_K).")

# --- S320 --------------------------------------------------------------------------------------------------------------------------

S320_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the density of the water", "density", "kg/m^3", (1010.0, 1020.0, 1040.0), "The density of the water {relation} {value} {unit}.",
        (P("c0", "is"), P("c1", "is measured as")),
        "sqrt(2*((q*g*H)/q))*sqrt(2*y/g)",
        ("gauge pressure of the water at the hole p = q g H", "Bernoulli's equation q v^2/2 = p between the free surface and the jet",
         "exit speed v = sqrt(2 p/q), then the range v t"),
        "sqrt(g*H)*sqrt(2*y/g)", nonnumeric_fill="a known density"),
    "famous", "That the speed of efflux does not depend on the density of the liquid is the well-known content of Torricelli's law.",
    (1060.0, 1070.0))

S320 = _spec(
    "S320", quantity_phrase="a further depth of water", quantity_type="length", unit="cm", values=(17.0, 19.0, 34.0),
    heldout_values=(26.0, 31.0),
    relevant=rv.RelevantWiring("H", "add", "Water topped up in the tank before the jet is observed adds to the depth above the hole, so H "
                                           "becomes H + q."),
    cancelling=S320_C,
    scene_clause="A rain barrel stands beside the tank.",
    scene_object_rationale="A rain barrel beside the tank is a separate vessel; water poured into it does not enter the tank, so the "
                           "depth of the water above the hole is the stated one.",
    scene_refs=("rain barrel",), target_terms=("tank", "hole", "jet"),
    pairs=(
        Pair("p0", "Before the jet is observed, the water in {relation} is topped up by {value} {unit}.", "the tank", "the rain barrel",
             CO,
             "Water topped up in the rain barrel stays in the barrel; the tank keeps its stated depth above the hole, and the hole "
             "and the ground are as stated.", ("open tank", "falls to the ground without air resistance"), "a modest depth",
             before_context_reason="The R sentence refers to 'the tank' and 'the jet' before the context introduces them."),
        Pair("p1", "{relation} topped up by {value} {unit}.",
             "Before the jet is observed, the water in the tank has been",
             "For an earlier experiment only, the water in the tank had been", EVENT,
             "The water in the tank had been topped up in an earlier experiment only; in the stated run the depth above the hole is the stated one.",
             ("open tank", "falls to the ground without air resistance"), "a modest depth"),
    ),
    notes="M250 phase 3: C is the density of the water (famous: Torricelli's speed); no K (see NO_K).")


ROLE_SPECS: dict[str, r2.RoleSpecV2] = {s.structure_id: s for s in (S311, S312, S313, S314, S315, S316, S317, S318, S319, S320)}
SPECS = ROLE_SPECS

STRUCTURE_FACTORIES = {f().structure_id: f for f in lf.ALL}

K_KINDS: dict[str, str] = {
    "S314": "laminar versus turbulent flow (Reynolds number above the onset of turbulence)",
    "S315": "creeping-flow regime of the drag law (particle Reynolds number below the limit of Stokes' law)",
    "S316": "free floating versus resting on the bottom (the water layer deeper than the cube needs)",
    "S318": "phase state (vapour pressure below the pressure in the throat, no cavitation)",
}

# Structures that cannot honestly carry the design. None in this batch.
INFEASIBLE: dict[str, str] = {}

NO_C: dict[str, str] = {
    "S315": "The time depends on the radius, the densities and the viscosity through the sedimentation coefficient and on the two "
            "distances and the rotation rate; the number of particles, the diameter of the tube and the volume of suspension appear in "
            "no relation, so nothing enters and cancels.",
    "S318": "Pressure, flow rate, the two diameters and the density all survive in the throat pressure; a free quantity such as the "
            "height of a horizontal pipe appears in no relation of the stated model, so nothing enters and cancels.",
    "S319": "Radius, density of the ice, density of the air and drag coefficient all survive in the terminal speed; a free quantity "
            "such as the temperature of the air appears in no relation, so nothing enters and cancels.",
}
NO_K: dict[str, str] = {
    "S311": "The only regimes of the model (a rigid gate in equilibrium, water at rest) are conditions of the stated situation and "
            "carry no further quantity with a threshold and a definite out-of-regime answer.",
    "S312": "The condition that the surface speed is negligible compared with the speed of the jet changes the draining time "
            "continuously and by less than the grading tolerance over the stated values, so no out-of-regime law separates from "
            "the answer.",
    "S313": "Laminar flow in the two tubes is a stated condition, but a flow that stopped being laminar would obey a friction law "
            "that needs the density and the flow rate, which are not stated, so there is no definite out-of-regime pressure at the joint.",
    "S317": "Jurin's law holds for a tube narrow compared with the capillary length, but the departure grows continuously with the "
            "radius and has no sharp threshold and no definite out-of-regime answer.",
    "S319": "The quadratic drag law holds above a Reynolds number of a few hundred, but the Reynolds number needs the viscosity of "
            "the air, which the problem does not state, so no regime predicate can be evaluated from the stated quantities.",
    "S320": "The condition that the surface speed is negligible compared with the speed of the jet changes the range continuously "
            "and by less than the grading tolerance over the stated values, so no out-of-regime law separates from the answer.",
}


def structure(structure_id: str) -> gr.Structure:
    """The new structure with the spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)


# What the H4 trace extractor (`TraceContext.target_phrases` / `target_symbols`) must read as a statement of the target: a phrase of the
# question, its head noun and the conventional symbols of the target quantity (and the graph's target node name).
TARGET_TERMS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "S311": (("horizontal force must be applied", "force", "bottom edge"), ("Fh", "F_h", "F")),
    "S312": (("long does the bowl take to empty", "take to empty", "how long"), ("t", "t_e", "T")),
    "S313": (("gauge pressure of the oil at the joint", "gauge pressure", "pressure"), ("pj", "p_j", "p")),
    "S314": (("pressure drop between the two tappings", "pressure drop", "drop"), ("dp", "Δp", "p")),
    "S315": (("long does a particle", "take to reach the bottom", "how long"), ("t", "t_s", "T")),
    "S316": (("far below the interface", "bottom face of the cube", "depth"), ("x", "d", "h")),
    "S317": (("mass of the water in the tube", "mass of the water", "mass"), ("m", "M", "m_w")),
    "S318": (("absolute pressure of the water in the throat", "pressure of the water", "pressure"), ("p2", "p_2", "p")),
    "S319": (("terminal speed of the hailstone", "terminal speed", "speed"), ("vt", "v_t", "v")),
    "S320": (("horizontal distance from the tank", "horizontal distance", "distance"), ("x", "R", "d")),
}
