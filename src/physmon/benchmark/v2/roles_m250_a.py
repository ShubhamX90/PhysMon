"""M250 phase 1, batch a: October structures S03-S23 upgraded to the role-by-value design of M0 v2.1.

Seventeen structures (S03 S04 S05 S06 S08 S09 S10 S11 S12 S14 S16 S17 S18 S19 S21 S22 S23), instance 0, specified with the
M0 v2.1 classes (`rolevalue_v2.RoleSpecV2`, `PhrasePair`, `CancellingV2`, `ConditionalV2`, `KOut`) and certified by
`rolevalue_v2.certify_v2` (`version="v2.1"`). The rules are those of plan revision v2.2, section G and the dataset admission
standard 3.1-3.5, 6.2, 6.3:

* one R/D quantity q with three study and two held-out values; two phrasing pairs. Pair 0 puts q on a co-present object that a
  number-free scene clause (the last sentence of the base context of every cell) has introduced; pair 1 is an earlier event of
  the target object that leaves no state behind. No change is applied and then reversed. R and D share frame, numeral and unit.
* C quantities only where q really enters the governing relations and cancels; K quantities only where a genuine regime exists.
  Where the physics does not support one, the stratum is recorded in `NO_C` / `NO_K` with the reason, never forced.

The base problems, wirings' inputs and gold answers are those of the October library (`library.py`, `library_b.py`, `library_c.py`).
"""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import library, library_b, library_c
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2

P = rv.Phrasing
Pair = r2.PhrasePair
CO = r2.D_KIND_CO_PRESENT
EVENT = r2.D_KIND_OTHER_EVENT
V21 = r2.VERSION_V21

STRUCTURE_FACTORIES = {
    "S03": library.s03_elastic_collision,
    "S04": library.s04_spring_max_speed,
    "S05": library.s05_disc_angular_acceleration,
    "S06": library.s06_resistor_network,
    "S08": library.s08_series_capacitor_energy,
    "S09": library.s09_calorimetry,
    "S10": library.s10_projectile_max_height,
    "S11": library_b.s11_braking_distance,
    "S12": library_b.s12_curve_speed,
    "S14": library_b.s14_lift_power,
    "S16": library_b.s16_rl_current,
    "S17": library_b.s17_wall_heat_flow,
    "S18": library_b.s18_isothermal_work,
    "S19": library_b.s19_projectile_range,
    "S21": library_c.s21_doppler_shift,
    "S22": library_c.s22_string_fundamental,
    "S23": library_c.s23_combined_gas_law,
}

# What the H4 trace extractor must read as a statement of the target: the target phrase of the question and its head noun, and
# the conventional symbols of the target quantity (see `roles_m0v2.TARGET_TERMS`).
TARGET_TERMS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "S03": (("velocity of the first cart", "velocity"), ("v_1f", "v1f", "v_1'", "v_1", "v1", "v")),
    "S04": (("maximum speed of the block", "maximum speed", "speed"), ("v_max", "v")),
    "S05": (("angular acceleration of the disc", "angular acceleration"), ("alpha", "α")),
    "S06": (("current through the second resistor", "current"), ("I_3", "I3", "I")),
    "S08": (("energy stored", "energy"), ("E", "U")),
    "S09": (("temperature rise", "rise in the temperature of the water", "temperature of the water"),
            ("ΔT", "dT", "DeltaT", "T")),
    "S10": (("maximum height of the ball", "maximum height", "height"), ("H", "h_max", "h")),
    "S11": (("braking distance", "stopping distance", "distance"), ("d", "s", "x")),
    "S12": (("maximum speed", "speed"), ("v_max", "v")),
    "S14": (("average mechanical power", "power"), ("P",)),
    "S16": (("current in the circuit", "current"), ("I",)),
    "S17": (("rate of heat flow", "heat flow"), ("Q", "q", "P", "Q_dot")),
    "S18": (("work done by the gas", "work"), ("W",)),
    "S19": (("horizontal distance", "range"), ("R", "x", "d")),
    "S21": (("frequency the listener hears", "frequency heard", "frequency"), ("f_o", "f'", "f_obs", "f_L", "f")),
    "S22": (("fundamental frequency", "frequency"), ("f_1", "f1", "f")),
    "S23": (("final pressure", "pressure"), ("p_2", "p2", "P_2", "P2", "p")),
}

BEFORE_NO = ("The pair-0 R sentence refers to entities that the context introduces afterwards (and, for the D twin, to the "
             "scene object), so it does not read correctly placed before the context.")


# --- S03: one-dimensional perfectly elastic collision ----------------------------------------------------------------------------

S03 = r2.RoleSpecV2(
    structure_id="S03", quantity_phrase="an extra block", quantity_type="mass", unit="kg", values=(0.7, 1.3, 2.2),
    heldout_values=(0.8, 1.2),
    relevant=rv.RelevantWiring("m1", "add", "A block loaded onto the first cart moves with it, so the first cart's mass in the "
                                            "collision becomes m1 + q; the collision stays perfectly elastic."),
    pairs=(
        Pair("p0", "A {value} {unit} block is loaded onto {relation} before the collision.", "the first cart", "the third cart", CO,
             "A block loaded onto a cart that waits at rest on a parallel track adds no mass to either colliding cart and takes "
             "no part in the collision, so the first cart's velocity afterwards is fixed by the stated masses and velocities.",
             ("frictionless track", "perfectly elastic"), "small", before_context_reason=BEFORE_NO),
        Pair("p1", "A {value} {unit} block was loaded onto the first cart {relation}.", "just before the collision",
             "in an earlier run", EVENT,
             "The block was loaded onto the first cart in an earlier run, which is over; in the stated run the first cart carries "
             "only its stated mass.", ("frictionless track", "perfectly elastic"), "small"),
    ),
    scene_clause="A third cart waits at rest on a parallel track.",
    scene_object_rationale="A cart waiting at rest on a parallel track is touched by neither colliding cart and exerts no force "
                           "on them, so the collision of the first two carts is unchanged.",
    scene_refs=("third cart",), target_terms=("first cart", "second cart"), version=V21,
    notes="M250 a: R is mass added to the first cart; no C (no honest cancelling quantity) and no K (see NO_C, NO_K).")

# --- S04: block released from a stretched spring -----------------------------------------------------------------------------------

S04 = r2.RoleSpecV2(
    structure_id="S04", quantity_phrase="an extra weight", quantity_type="mass", unit="kg", values=(0.6, 0.8, 1.2),
    heldout_values=(0.9, 1.1),
    relevant=rv.RelevantWiring("m", "add", "A weight stuck on top of the block oscillates with it, so the moving mass becomes "
                                           "m + q and omega = sqrt(k/(m + q))."),
    pairs=(
        Pair("p0", "Before the release, a {value} {unit} weight is stuck on top of {relation}.", "the block", "the trolley", CO,
             "A weight loaded onto a trolley that stands on the floor beside the table is not on the block and exerts no force on "
             "the block or the spring, so the block's maximum speed is fixed by the stated k, x and m.",
             ("horizontal frictionless table", "released from rest"), "small", before_context_reason=BEFORE_NO),
        Pair("p1", "A {value} {unit} weight was stuck on top of the block {relation}.", "before it was released",
             "in an earlier trial", EVENT,
             "The weight was stuck on the block in an earlier trial, which is over; in the stated trial the block carries only "
             "its stated mass.", ("horizontal frictionless table", "released from rest"), "small"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the spring's natural length", "length", "m", (0.25, 0.45, 0.65), "The spring {relation} {value} {unit}.",
            (P("c0", "has a natural length of"), P("c1", "has an unstretched length of")),
            "sqrt(k/m)*((q + x) - q)",
            ("the stretched length of the spring: l = L0 + x", "the extension that Hooke's law uses: l - L0",
             "restoring force: F = k (l - L0)"),
            "sqrt(k/m)*(q + x)", nonnumeric_fill="a known length"),
        "standard", "Hooke's law is written for the extension from the natural length, so the natural length drops out of any "
                    "answer; every textbook states F = -k x for x measured from it, but it is not a headline fact.", (0.35, 0.4)),
    conditional=r2.ConditionalV2(
        rv.ConditionalSpec(
            "the spring's elastic limit", "length", "m", (0.26, 0.34, 0.52),
            "The spring {relation} {value} {unit}.",
            (P("k0", "obeys Hooke's law for extensions of up to"), P("k1", "stays elastic for extensions of up to")),
            "x < q", "q*sqrt(k/m)", 0.1, nonnumeric_fill="a known length"),
        r2.KOut(False, "Beyond its elastic limit the spring's force law is not Hooke's law and is not given, so 'the maximum speed "
                       "of the block' has no certified answer without an added model of permanent deformation (the formula "
                       "q sqrt(k/m) assumes an elastic-perfectly-plastic spring, which the base problem does not state)."),
        (0.4, 0.48)),
    scene_clause="A trolley stands on the floor beside the table.",
    scene_object_rationale="A trolley on the floor beside the table is touched by neither the block nor the spring and exerts no "
                           "force on them, so the block's oscillation is unchanged.",
    scene_refs=("trolley",), target_terms=("the block", "the spring"), version=V21,
    notes="M250 a: R is mass added to the block; C is the natural length (cancels in the extension); K is the elastic limit.")

# --- S05: disc under a driving and a friction torque ---------------------------------------------------------------------------------

S05 = r2.RoleSpecV2(
    structure_id="S05", quantity_phrase="an extra disc", quantity_type="mass", unit="kg",
    values=(1.0, 2.0, 5.5), heldout_values=(4.5, 5.0),
    relevant=rv.RelevantWiring("m", "add", "A uniform disc of the same radius bolted coaxially onto the disc makes a uniform solid disc "
                                           "of mass m + q and radius r, so I = (m + q) r^2 / 2 and the net torque tau - tau_f "
                                           "acts on it."),
    pairs=(
        Pair("p0", "Before the torques are applied, a {value} {unit} disc of the same radius is bolted coaxially onto {relation}.",
             "this disc", "the flywheel", CO,
             "A disc bolted onto a flywheel on a second shaft beside the disc is not on the disc's shaft, so the disc's mass, "
             "moment of inertia and net torque are the stated ones.",
             ("central axis", "friction torque"), "small", before_context_reason=BEFORE_NO),
        Pair("p1", "A {value} {unit} disc of the same radius was bolted coaxially onto this disc {relation}.",
             "before the torques were applied", "in an earlier run", EVENT,
             "The extra disc was bolted onto this disc in an earlier run, which is over; in the stated run the disc has only its "
             "stated mass.", ("central axis", "friction torque"), "small"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the disc's thickness", "length", "cm", (2.0, 3.5, 5.0), "The disc {relation} {value} {unit}.",
            (P("c0", "has a thickness of"), P("c1", "is cut from a plate with a thickness of")),
            "(tau - tau_f)/(((m/(pi*r**2*q))*pi*q*r**4)/2)",
            ("density of the uniform disc: rho = m / (pi r^2 t)", "inertia of a uniform solid disc: I = (1/2) rho pi r^4 t",
             "alpha = (tau - tau_f) / I"),
            "(tau - tau_f)/((m*r**2/2)*(1 + q/r))", nonnumeric_fill="a known thickness"),
        "standard", "That a uniform solid disc's moment of inertia (1/2) M R^2 does not depend on its thickness is taught with "
                    "the derivation of I, but it is not a classroom slogan.", (3.0, 4.5)),
    conditional=r2.ConditionalV2(
        rv.ConditionalSpec(
            "the static friction torque", "torque", "N*m", (2.0, 2.6, 3.4),
            "The static friction torque on the disc {relation} {value} {unit}.",
            (P("k0", "is"), P("k1", "has been measured at")), "q < tau", "0", 9.0, nonnumeric_fill="a known value"),
        r2.KOut(False, "If the static friction torque exceeded the driving torque the disc would not turn, but the problem then "
                       "states a kinetic friction torque that 'opposes the motion' of a disc that does not move; the premise "
                       "would be contradicted, so no certified answer exists for the stated question."),
        (2.3, 2.9)),
    scene_clause="A flywheel is mounted on a second shaft beside the disc.",
    scene_object_rationale="A flywheel on its own second shaft is not coupled to the disc or its shaft, so the torques on the disc "
                           "and its moment of inertia are unchanged.",
    scene_refs=("flywheel",), target_terms=("this disc", "the disc"), version=V21,
    notes="M250 a: R is an extra coaxial disc; C is the thickness (cancels in I); K is the static friction torque.")

# --- S06: series-parallel resistor network ---------------------------------------------------------------------------------------

S06 = r2.RoleSpecV2(
    structure_id="S06", quantity_phrase="an extra series resistor", quantity_type="resistance", unit="Ω", values=(1.5, 3.5, 7.0),
    heldout_values=(2.5, 5.5),
    relevant=rv.RelevantWiring("R1", "add", "A resistor in series with the battery adds to the series resistance, so the series "
                                            "resistor becomes R1 + q and the current through the pair falls."),
    pairs=(
        Pair("p0", "A {value} {unit} resistor is connected in series with {relation}.", "the battery", "the lamp", CO,
             "A resistor in series with the lamp lies in the lamp's own loop and shares no node with the battery's network, so "
             "the network's resistances and the current through the second resistor are the stated ones.",
             ("negligible internal resistance", "in series"), "small", before_context_reason=BEFORE_NO),
        Pair("p1", "A {value} {unit} resistor was connected in series with the battery {relation}.", "in this circuit",
             "in an earlier experiment", EVENT,
             "The resistor was connected in an earlier experiment, which is over; the circuit of the stated experiment has only "
             "its stated resistors.", ("negligible internal resistance", "in series"), "small"),
    ),
    conditional=r2.ConditionalV2(
        rv.ConditionalSpec(
            "the power rating of the second resistor", "power", "W", (11.0, 20.0, 29.0),
            "The second resistor of the parallel pair {relation} {value} {unit}.",
            (P("k0", "is rated for a maximum power of"), P("k1", "can dissipate at most")), "I3**2*R3 < q", "0", 1.5,
            nonnumeric_fill="a known value"),
        r2.KOut(False, "A resistor that is overloaded may burn out (open circuit), change its resistance or survive for a while; "
                       "a rating does not determine which, so the current through it has no certified answer outside the regime "
                       "(0 is the open-circuit case only)."),
        (14.0, 24.0)),
    scene_clause="A small lamp, wired to its own cell, stands beside the circuit.",
    scene_object_rationale="A lamp wired to its own cell closes a loop of its own that shares no node with the battery's network, "
                           "so the battery still drives only the stated resistors.",
    scene_refs=("lamp",), target_terms=("the battery", "parallel pair", "second resistor"), version=V21,
    notes="M250 a: R is an extra resistor in series with the battery; K is the second resistor's power rating; no C.")

# --- S08: two capacitors in series -------------------------------------------------------------------------------------------------

S08 = r2.RoleSpecV2(
    structure_id="S08", quantity_phrase="an extra capacitor", quantity_type="capacitance", unit="μF", values=(5.0, 7.5, 14.0),
    heldout_values=(5.5, 8.5),
    relevant=rv.RelevantWiring("C2", "add", "A capacitor in parallel with the second capacitor adds to its capacitance, so C2 "
                                            "becomes C2 + q and the series equivalent capacitance rises."),
    pairs=(
        Pair("p0", "Before charging begins, a {value} {unit} capacitor is connected in parallel with {relation}.",
             "the second capacitor", "the lamp", CO,
             "A capacitor in parallel with the lamp belongs to the lamp's own loop and shares no node with the series "
             "capacitors, so their equivalent capacitance and stored energy are the stated ones.",
             ("fully charged", "in series"), "small", before_context_reason=BEFORE_NO),
        Pair("p1", "A {value} {unit} capacitor was connected in parallel with the second capacitor {relation}.",
             "before charging began", "in an earlier experiment", EVENT,
             "The capacitor was connected in an earlier experiment, which is over; the stated capacitors are charged alone.",
             ("fully charged", "in series"), "small"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the resistance of the charging circuit", "resistance", "kΩ", (5.0, 6.5, 9.0),
            "The charging circuit {relation} {value} {unit}.",
            (P("c0", "has a total resistance of"), P("c1", "offers a resistance of")),
            "(V*(V/q)*(q*C1*C2/(C1 + C2))) - ((V/q)**2*q*(q*C1*C2/(C1 + C2)/2))",
            ("charging current: I(t) = (V/R) exp(-t/(R Ceq))", "energy drawn from the battery: Wb = V (V/R) (R Ceq)",
             "energy dissipated in the resistance: Wd = (V/R)^2 R (R Ceq / 2)", "stored energy = Wb - Wd"),
            "C1*C2/(C1 + C2)*V**2", nonnumeric_fill="a known resistance"),
        "standard", "That half of the energy drawn from the battery is dissipated, whatever the charging resistance, is a standard "
                    "result of the RC charging analysis but is not stated as a slogan.", (6.0, 7.5)),
    conditional=r2.ConditionalV2(
        rv.ConditionalSpec(
            "the voltage rating of the first capacitor", "voltage", "V", (130.0, 185.0, 250.0),
            "The first capacitor {relation} {value} {unit}.",
            (P("k0", "is rated for a maximum voltage of"), P("k1", "can withstand at most")), "Ceq*V/C1 < q", "C2*V**2/2", 50.0,
            nonnumeric_fill="a known voltage"),
        r2.KOut(False, "A capacitor driven beyond its rating may short, open or survive; the rating does not say which, so the "
                       "stored energy has no certified answer outside the regime (the formula C2 V^2/2 is the shorted-first-"
                       "capacitor case only)."),
        (145.0, 220.0)),
    scene_clause="A small lamp, wired to its own cell, stands beside the circuit.",
    scene_object_rationale="A lamp wired to its own cell closes a loop of its own that shares no node with the capacitors, so the "
                           "capacitors and the battery are unchanged.",
    scene_refs=("lamp",), target_terms=("second capacitor", "first capacitor"), version=V21,
    notes="M250 a: R is a capacitor in parallel with the second capacitor; C is the charging resistance (half the battery energy "
          "is dissipated whatever it is); K is the first capacitor's voltage rating.")

# --- S09: calorimetry ---------------------------------------------------------------------------------------------------------------

S09 = r2.RoleSpecV2(
    structure_id="S09", quantity_phrase="further water", quantity_type="mass", unit="kg", values=(0.2, 0.55, 0.85),
    heldout_values=(0.25, 0.65),
    relevant=rv.RelevantWiring("m2", "add", "Further water at the same temperature poured into the container adds to the water "
                                            "mass, so m2 becomes m2 + q."),
    pairs=(
        Pair("p0", "A further {value} {unit} of water at the same temperature is poured into {relation}.", "this container",
             "the second container", CO,
             "Water poured into a second, separate container takes no heat from the copper block and adds no water to the "
             "first container, so the water's temperature rise there is the stated one.",
             ("perfectly insulated container", "placed in"), "small amount", before_context_reason=BEFORE_NO),
        Pair("p1", "A further {value} {unit} of water at the same temperature was poured into this container {relation}.",
             "before the block was added", "in an earlier experiment", EVENT,
             "The water was poured into this container in an earlier experiment, which is over; in the stated experiment the "
             "container holds only its stated water.", ("perfectly insulated container", "placed in"), "small amount"),
    ),
    scene_clause="A second insulated container with some water stands beside it.",
    scene_object_rationale="A second insulated container with its own water exchanges no heat with the first container or the "
                           "block, so the first container's mixing is unchanged.",
    scene_refs=("second",), target_terms=("this container", "the container"), version=V21,
    notes="M250 a: R is further water in the container; no C (no honest cancelling quantity) and no K (see NO_C, NO_K).")

# --- S10: projectile maximum height ------------------------------------------------------------------------------------------------

S10 = r2.RoleSpecV2(
    structure_id="S10", quantity_phrase="a stand", quantity_type="length", unit="m", values=(1.2, 2.2, 4.3),
    heldout_values=(2.4, 3.9),
    relevant=rv.RelevantWiring("h0", "add", "A stand under the platform raises the launch point by q, so the platform height "
                                            "becomes h0 + q."),
    pairs=(
        Pair("p0", "Before the ball is launched, a {value} {unit} stand is placed under the {relation}.", "platform", "table", CO,
             "A stand under a table beside the platform does not raise the platform, so the launch height is the stated "
             "platform height.", ("platform 5 m above level ground", "Neglect air resistance"), "small",
             before_context_reason=BEFORE_NO),
        Pair("p1", "A {value} {unit} stand was placed under the platform {relation}.", "before the ball was launched",
             "in an earlier experiment", EVENT,
             "The stand was placed under the platform in an earlier experiment, which is over; in the stated experiment the "
             "platform is at its stated height.", ("platform 5 m above level ground", "Neglect air resistance"), "small"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the ball's mass", "mass", "kg", (1.2, 1.8, 3.7), "The ball {relation} {value} {unit}.",
            (P("c0", "has a mass of"), P("c1", "is a solid ball with a mass of")),
            "h0 + (q*(v*sin(theta))**2/2)/(q*g)",
            ("kinetic energy of the vertical motion at launch: (1/2) m vy^2", "potential energy gained at the top: m g (H - h0)"),
            "h0 + q*(v*sin(theta))**2/(2*g)", nonnumeric_fill="a known mass"),
        "famous", "Mass independence of projectile motion is a headline classroom fact.", (2.4, 3.4)),
    conditional=r2.ConditionalV2(
        rv.ConditionalSpec(
            "the height of the hall's ceiling", "length", "m", (18.0, 26.0, 43.0),
            "The platform stands in a hall whose ceiling {relation} {value} {unit} above the ground.",
            (P("k0", "is"), P("k1", "lies")), "H < q", "q", 9.0, nonnumeric_fill="a known height"),
        r2.KOut(False, "Below the maximum height the ball would strike the ceiling and the maximum height would equal the "
                       "ceiling height, which is the stated number: a copy of the stated value would be a correct answer, so the "
                       "cell would be source-ambiguous (and the question would then be about the ceiling, not the trajectory)."),
        (31.0, 34.0)),
    scene_clause="A table stands beside the platform.",
    scene_object_rationale="A table beside the platform is not under it and does not touch the ball, so the launch point and the "
                           "trajectory are unchanged.",
    scene_refs=("table",), target_terms=("platform",), version=V21,
    notes="M250 a: R is a stand under the platform; C is the ball's mass (famous); K is the ceiling height.")

# --- S11: braking distance ---------------------------------------------------------------------------------------------------------

S11 = r2.RoleSpecV2(
    structure_id="S11", quantity_phrase="a speed gain", quantity_type="speed", unit="m/s", values=(3.0, 4.5, 11.0),
    heldout_values=(3.5, 6.0),
    relevant=rv.RelevantWiring("v0", "add", "The car gains a further q before braking starts, so its speed when braking begins is "
                                            "v0 + q."),
    pairs=(
        Pair("p0", "The {relation} gains a further {value} {unit} before braking starts.", "car", "bus", CO,
             "The bus drives on the same road but is another vehicle; its change of speed does not alter the car's speed when "
             "its braking starts.", ("level road", "wheels locked"), "small amount", before_context_reason=BEFORE_NO),
        Pair("p1", "The car gained a further {value} {unit} {relation}.", "before it started braking", "on an earlier run",
             EVENT,
             "The car gained that speed on an earlier run, which is over; on the stated run it brakes from the stated speed.",
             ("level road", "wheels locked"), "small amount"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the car's mass", "mass", "kg", (1000.0, 1350.0, 2200.0), "The car {relation} {value} {unit}.",
            (P("c0", "has a mass of"), P("c1", "is loaded to a total mass of")),
            "v0**2/(2*((q*mu*g)/q))", ("normal force: N = m g", "friction force: f = mu N", "deceleration: a = f / m"),
            "v0**2*q/(2*mu*g)", nonnumeric_fill="a known mass"),
        "famous", "Mass independence of the braking distance is a familiar classroom statement.", (1100.0, 1200.0)),
    scene_clause="A bus drives along the same road.",
    scene_object_rationale="A bus on the road is another vehicle that is not in the car's way and exerts no force on it, so the "
                           "car's braking is unchanged.",
    scene_refs=("bus",), target_terms=("car",), version=V21,
    notes="M250 a: R is a speed gain before braking; C is the car's mass (famous); no K (see NO_K).")

# --- S12: maximum speed on a flat curve ------------------------------------------------------------------------------------------

S12 = r2.RoleSpecV2(
    structure_id="S12", quantity_phrase="an outward shift", quantity_type="length", unit="m", values=(4.0, 7.5, 11.5),
    heldout_values=(8.5, 10.0),
    relevant=rv.RelevantWiring("r", "add", "The car moves q further from the centre of the curve, so the radius of its path becomes "
                                           "r + q."),
    pairs=(
        Pair("p0", "The {relation} moves {value} {unit} further from the centre of the curve.", "car", "cyclist", CO,
             "A cyclist on a path beside the road changes the cyclist's own radius; the car's path and the road under it are "
             "unchanged, so its maximum speed is fixed by the stated radius and coefficient.",
             ("flat circular curve", "static friction"), "a little", before_context_reason=BEFORE_NO),
        Pair("p1", "The car was driven {value} {unit} further from the centre of the curve {relation}.",
             "before it entered the curve", "on an earlier run", EVENT,
             "The car was driven further out on an earlier run, which is over; on the stated run it follows the stated radius.",
             ("flat circular curve", "static friction"), "a little"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the car's mass", "mass", "kg", (1000.0, 1350.0, 2200.0), "The car {relation} {value} {unit}.",
            (P("c0", "has a mass of"), P("c1", "is loaded to a total mass of")),
            "sqrt((q*mu*g*r)/q)", ("maximum friction force: f = mu m g", "centripetal force: m v^2 / r"),
            "sqrt(q*mu*g*r)", nonnumeric_fill="a known mass"),
        "famous", "Mass independence of the maximum cornering speed is a familiar classroom statement.", (1100.0, 1200.0)),
    scene_clause="A cyclist rides along a path beside the road.",
    scene_object_rationale="A cyclist on a path beside the road is another road user that exerts no force on the car and does not "
                           "change the road under it, so the car's curve is unchanged.",
    scene_refs=("cyclist",), target_terms=("car",), version=V21,
    notes="M250 a: R is an outward shift of the car's path; C is the car's mass (famous); no K (see NO_K).")

# --- S14: lifting power --------------------------------------------------------------------------------------------------------------

S14 = r2.RoleSpecV2(
    structure_id="S14", quantity_phrase="an extra box", quantity_type="mass", unit="kg", values=(7.0, 11.0, 28.0),
    heldout_values=(13.0, 24.0),
    relevant=rv.RelevantWiring("m", "add", "A box placed on the load is lifted with it, so the lifted mass becomes m + q."),
    pairs=(
        Pair("p0", "Before the lift begins, a {value} {unit} box is placed on {relation}.", "the load", "the crate", CO,
             "A box placed on a crate that rests on the floor beside the motor is not lifted by the motor, so the lifted "
             "mass is the stated load.", ("constant speed", "load of 80 kg"), "small",
             before_context_reason=BEFORE_NO),
        Pair("p1", "A {value} {unit} box was placed on the load {relation}.", "before the lift began", "in an earlier lift",
             EVENT,
             "The box was placed on the load in an earlier lift, which is over; in the stated lift the motor raises only the "
             "stated load.", ("constant speed", "load of 80 kg"), "small"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the height of the starting level", "length", "m", (1.2, 2.4, 4.2), "The load {relation} {value} {unit} above the ground.",
            (P("c0", "starts"), P("c1", "is first held")),
            "m*g*((q + h) - q)/t", ("potential energy at the start: m g q", "potential energy at the end: m g (q + h)",
                                    "work done on the load: the increase in potential energy"),
            "m*g*(q + h)/t", nonnumeric_fill="a known height"),
        "standard", "That only the change in potential energy matters, not the level it is measured from, is standard but not a "
                    "headline fact.", (1.4, 2.2)),
    conditional=r2.ConditionalV2(
        rv.ConditionalSpec(
            "the motor's maximum power", "power", "W", (680.0, 930.0, 1280.0), "The motor {relation} {value} {unit}.",
            (P("k0", "can deliver at most"), P("k1", "has a maximum power output of")), "P < q", "q", 300.0,
            nonnumeric_fill="a known power"),
        r2.KOut(False, "If the motor's maximum power were below the power the lift needs, the load could not be raised in the stated "
                       "time at constant speed, so the stated process would not occur and 'the average mechanical power "
                       "delivered' has no certified answer for it."),
        (750.0, 840.0)),
    scene_clause="A crate rests on the floor beside the motor.",
    scene_object_rationale="A crate resting on the floor beside the motor is not connected to the motor or the load and is not lifted "
                           "by it, so the motor's work on the load is unchanged.",
    scene_refs=("crate",), target_terms=("the load",), version=V21,
    notes="M250 a: R is a box on the load; C is the starting level (potential energy datum); K is the motor's power limit.")

# --- S16: RL circuit ----------------------------------------------------------------------------------------------------------------

S16 = r2.RoleSpecV2(
    structure_id="S16", quantity_phrase="an extra series resistor", quantity_type="resistance", unit="Ω", values=(4.0, 11.5, 17.0),
    heldout_values=(8.5, 13.5),
    relevant=rv.RelevantWiring("R", "add", "A resistor in series with the coil adds to the series resistance, so R becomes R + q "
                                           "and both the time constant L/R and the final current V/R change."),
    pairs=(
        Pair("p0", "Before the circuit is closed, a {value} {unit} resistor is connected in series with {relation}.",
             "the coil", "the lamp", CO,
             "A resistor in series with the lamp lies in the lamp's own loop and shares no node with the coil's circuit, so the "
             "coil's current is fixed by the stated emf, resistance and inductance.",
             ("negligible resistance", "in series"), "small", before_context_reason=BEFORE_NO),
        Pair("p1", "A {value} {unit} resistor was connected in series with the coil {relation}.", "before the circuit was closed",
             "in an earlier experiment", EVENT,
             "The resistor was connected in an earlier experiment, which is over; the circuit of the stated experiment has only "
             "its stated resistor.", ("negligible resistance", "in series"), "small"),
    ),
    scene_clause="A small lamp, wired to its own cell, stands beside the circuit.",
    scene_object_rationale="A lamp wired to its own cell closes a loop of its own that shares no node with the coil's circuit, so the "
                           "battery still drives only the stated coil and resistor.",
    scene_refs=("lamp",), target_terms=("the coil", "the battery"), version=V21,
    notes="M250 a: R is an extra resistor in series with the coil; no C and no K (see NO_C, NO_K).")

# --- S17: heat flow through a two-layer wall -----------------------------------------------------------------------------------------

S17 = r2.RoleSpecV2(
    structure_id="S17", quantity_phrase="a further warming", quantity_type="temperature difference", unit="K",
    values=(3.5, 6.5, 11.0), heldout_values=(4.0, 6.0),
    relevant=rv.RelevantWiring("dT", "add", "Warming the hotter outer surface by q with the colder one unchanged raises the "
                                            "temperature difference across the layers to dT + q."),
    pairs=(
        Pair("p0", "The hotter surface of {relation} is warmed by {value} {unit}.", "the wall", "the partition", CO,
             "Warming the hotter surface of a partition beside the wall changes the partition's temperatures, not the wall's, so "
             "the wall's temperature difference and heat flow are the stated ones.",
             ("two layers in series", "steady"), "a few kelvin", before_context_reason=BEFORE_NO),
        Pair("p1", "The hotter surface of the wall was warmed by {value} {unit} {relation}.", "before the test began",
             "in an earlier test", EVENT,
             "The hotter surface was warmed in an earlier test, which is over; in the stated test the temperature difference is "
             "the stated one.", ("two layers in series", "steady"), "a few kelvin"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the temperature of the colder surface", "temperature", "K", (257.0, 303.0, 333.0),
            "The colder outer surface {relation} {value} {unit}.", (P("c0", "is at"), P("c1", "is held at")),
            "((q + dT) - q)/(Ra + Rb)",
            ("temperature of the hotter surface: T_hot = T_cold + dT", "temperature difference driving the flow: T_hot - T_cold",
             "heat flow: q = (T_hot - T_cold) / (Ra + Rb)"),
            "(q + dT)/(Ra + Rb)", nonnumeric_fill="a known temperature"),
        "standard", "That conduction depends only on the temperature difference, not on the absolute temperatures, is standard in "
                    "treatments of Fourier's law but is not a headline fact.", (265.0, 275.0)),
    scene_clause="A partition stands beside the wall.",
    scene_object_rationale="A partition beside the wall is not in series with its layers and carries no part of the heat flow, so "
                           "the wall's flow is unchanged.",
    scene_refs=("partition",), target_terms=("the wall",), version=V21,
    notes="M250 a: R is a warming of the hotter surface; C is the colder surface's absolute temperature; no K (see NO_K).")

# --- S18: isothermal work ----------------------------------------------------------------------------------------------------------

S18 = r2.RoleSpecV2(
    structure_id="S18", quantity_phrase="a further expansion", quantity_type="ratio", unit="1", values=(2.6, 3.4, 4.5),
    heldout_values=(3.0, 3.9),
    relevant=rv.RelevantWiring("rho", "replace", "If the expansion continues until the volume is q times the initial volume, the "
                                                 "final volume is q V1, so rho becomes q and the work is p1 V1 ln(q)."),
    pairs=(
        Pair("p0", "The expansion in {relation} then continues until the volume is {value} {unit} times its initial volume.",
             "this cylinder", "the second cylinder", CO,
             "The expansion in a second cylinder with its own gas does not change this cylinder's final volume, so the work done "
             "by this gas is fixed by its stated pressure, initial volume and expansion ratio.",
             ("constant temperature", "slowly"), "several", before_context_reason=BEFORE_NO),
        Pair("p1", "{relation}, the expansion continued until the volume was {value} {unit} times its initial volume.",
             "In this experiment", "In an earlier experiment", EVENT,
             "The expansion of this gas continued further in an earlier experiment, which is over; in the stated experiment the "
             "gas stops at its stated final volume.", ("constant temperature", "slowly"), "several"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the gas temperature", "temperature", "K", (280.0, 385.0, 435.0), "The gas {relation} {value} {unit}.",
            (P("c0", "is at a temperature of"), P("c1", "is held at a temperature of")),
            "(p1*V1/q)*q*log(rho)", ("amount of gas: n R = p1 V1 / T", "isothermal work: W = n R T ln(V2/V1)"),
            "p1*V1*log(rho)*(1 + q/273)", nonnumeric_fill="a known temperature"),
        "standard", "That the isothermal work p1 V1 ln(V2/V1) does not depend on the temperature once pV is known is standard in "
                    "the derivation W = n R T ln(V2/V1) but is not a headline fact.", (315.0, 345.0)),
    scene_clause="A second cylinder, in which a gas also expands slowly, stands beside the first.",
    scene_object_rationale="A second cylinder with its own gas and piston shares no gas with the first cylinder, so the first gas's "
                           "pressure, volume and expansion are unchanged.",
    scene_refs=("second cylinder",), target_terms=("this cylinder", "the cylinder"), version=V21,
    notes="M250 a: R continues the expansion to q times the initial volume (rho becomes q); C is the gas temperature; no K.")

# --- S19: projectile range -----------------------------------------------------------------------------------------------------------

S19 = r2.RoleSpecV2(
    structure_id="S19", quantity_phrase="a lowering of the launch direction", quantity_type="angle", unit="deg",
    values=(7.0, 14.0, 22.0), heldout_values=(16.0, 19.0),
    relevant=rv.RelevantWiring("theta", "subtract", "Lowering the launch direction by q towards the horizontal makes the launch "
                                                    "angle theta - q."),
    pairs=(
        Pair("p0", "The {relation} is lowered by {value} {unit}.", "launch direction", "ramp", CO,
             "A ramp on the field beside the launch point does not change the direction in which the ball is launched, so "
             "the launch angle is the stated one.", ("level ground", "Neglect air resistance"), "a few degrees",
             before_context_reason=BEFORE_NO),
        Pair("p1", "The launch direction was lowered by {value} {unit} {relation}.", "before the ball was launched",
             "in an earlier trial", EVENT,
             "The launch direction was lowered in an earlier trial, which is over; in the stated trial the ball is launched at "
             "the stated angle.", ("level ground", "Neglect air resistance"), "a few degrees"),
    ),
    scene_clause="A ramp stands on the field beside the launch point.",
    scene_object_rationale="A ramp beside the launch point is not in the ball's path and does not touch it, so the trajectory and "
                           "the landing point are unchanged.",
    scene_refs=("ramp",), target_terms=("launch direction", "the ball"), version=V21,
    notes="M250 a: R lowers the launch angle; no C and no K (see NO_C, NO_K).")

# --- S21: Doppler shift ---------------------------------------------------------------------------------------------------------------

S21 = r2.RoleSpecV2(
    structure_id="S21", quantity_phrase="a tuning increase", quantity_type="frequency", unit="Hz", values=(9.0, 16.0, 24.0),
    heldout_values=(18.0, 21.0),
    relevant=rv.RelevantWiring("f", "add", "Tuning the siren up by q raises the frequency it emits to f + q, and the heard frequency "
                                           "is (f + q) c / (c - vs)."),
    pairs=(
        Pair("p0", "The {relation} is tuned up by {value} {unit}.", "siren", "horn", CO,
             "The horn of the van is another sound source; tuning it changes the sound of the horn, not the frequency the siren "
             "emits or the frequency the listener hears from the siren.", ("steady tone", "stationary listener"),
             "a small amount", before_context_reason=BEFORE_NO),
        Pair("p1", "The siren was tuned up by {value} {unit} {relation}.", "before the tone was measured", "on an earlier run",
             EVENT,
             "The siren was tuned up on an earlier run, which is over; on the stated run it emits its stated tone.",
             ("steady tone", "stationary listener"), "a small amount"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the initial distance to the listener", "length", "m", (180.0, 300.0, 950.0),
            "At the start of the observation the siren {relation} {value} {unit} from the listener.",
            (P("c0", "is"), P("c1", "is at a distance of")),
            "1/((1/f + (q - vs/f)/c) - q/c)",
            ("the first wavefront, emitted at distance d, arrives at t1 = d / c",
             "the next wavefront is emitted after Ts = 1/f from distance d - vs Ts and arrives at t2 = Ts + (d - vs Ts)/c",
             "heard period = t2 - t1; heard frequency = 1 / (t2 - t1)"),
            "1/(1/f + (q - vs/f)/c)", nonnumeric_fill="a known distance"),
        "standard", "That the heard frequency does not depend on the distance is part of the standard derivation of the Doppler "
                    "shift from wavefront arrival times, but is rarely stated as a fact.", (240.0, 580.0)),
    scene_clause="A van with a horn stands on a road nearby.",
    scene_object_rationale="A van with a horn on a nearby road is another sound source; it neither changes the siren's tone nor the "
                           "relative motion of the siren and the listener.",
    scene_refs=("horn",), target_terms=("siren",), version=V21,
    notes="M250 a: R is a tuning increase of the siren; C is the initial distance (cancels in the heard period); no K (see NO_K).")

# --- S22: stretched string ----------------------------------------------------------------------------------------------------------

S22 = r2.RoleSpecV2(
    structure_id="S22", quantity_phrase="a tension increase", quantity_type="force", unit="N", values=(9.0, 41.0, 68.0),
    heldout_values=(24.0, 46.0),
    relevant=rv.RelevantWiring("T", "add", "Increasing the tension of the string by q makes the tension T + q while its mass and "
                                           "length are unchanged."),
    pairs=(
        Pair("p0", "The tension in {relation} is increased by {value} {unit}.", "this string", "the second string", CO,
             "Tightening a second string on the frame does not change the tension in this string, so its fundamental frequency "
             "is fixed by its stated tension, mass and length.", ("fixed at both ends", "uniform string"), "a small amount",
             before_context_reason=BEFORE_NO),
        Pair("p1", "The tension in this string was increased by {value} {unit} {relation}.", "before it was set vibrating",
             "in an earlier experiment", EVENT,
             "The tension was increased in an earlier experiment, which is over; in the stated experiment the string is stretched "
             "to its stated tension.", ("fixed at both ends", "uniform string"), "a small amount"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the string's cross-sectional area", "area", "mm^2", (1.2, 2.4, 3.3), "The string {relation} {value} {unit}.",
            (P("c0", "has a cross-sectional area of"), P("c1", "is a wire with a cross-sectional area of")),
            "sqrt(T/((m/(q*L))*q))/(2*L)",
            ("density of the uniform string: rho = m / (A L)", "linear density: mu = rho A", "frequency: f = sqrt(T / mu) / (2 L)"),
            "sqrt(T/(m/(q*L)))/(2*L)", nonnumeric_fill="a known area"),
        "uncommon", "That the cross-section drops out once the mass and length are given needs the step mu = rho A = m / L; it is "
                    "not stated as a fact in the usual presentations.", (1.5, 1.8)),
    conditional=r2.ConditionalV2(
        rv.ConditionalSpec(
            "the string's breaking strength", "force", "N", (160.0, 240.0, 370.0), "The string {relation} {value} {unit}.",
            (P("k0", "can withstand a tension of up to"), P("k1", "is rated to break only above")), "T < q", "0", 60.0,
            nonnumeric_fill="a known force"),
        r2.KOut(False, "If the string broke at a tension below the stretching tension it could not be stretched to it and would "
                       "not vibrate, so 'the fundamental frequency at which the string vibrates' would have no answer."),
        (220.0, 280.0)),
    scene_clause="A second string of the same kind is stretched on the same frame.",
    scene_object_rationale="A second string on the same frame is fixed at its own ends and exerts no force along the first string, so "
                           "the first string's tension and mass per length are unchanged.",
    scene_refs=("second string",), target_terms=("this string",), version=V21,
    notes="M250 a: R is a tension increase; C is the cross-section (cancels in mu); K is the breaking strength.")

# --- S23: combined gas law --------------------------------------------------------------------------------------------------------

S23 = r2.RoleSpecV2(
    structure_id="S23", quantity_phrase="a further warming", quantity_type="temperature", unit="K", values=(17.0, 38.0, 57.0),
    heldout_values=(45.0, 49.0),
    relevant=rv.RelevantWiring("T2", "add", "Warming the gas by a further q at constant volume makes its final temperature T2 + q "
                                            "at the unchanged final volume."),
    pairs=(
        Pair("p0", "The gas in {relation} is then warmed by a further {value} {unit} at constant volume.", "this piston",
             "the second piston", CO,
             "Warming the gas in a second piston does not change the gas in this piston, so its final pressure is fixed by its "
             "stated initial and final volumes and temperatures.", ("ideal gas", "sealed piston"), "small amount",
             before_context_reason=BEFORE_NO),
        Pair("p1", "The gas in this piston was warmed by {value} {unit} at constant volume {relation}.",
             "just before its final pressure was read", "in an earlier experiment", EVENT,
             "The gas was warmed in an earlier experiment, which is over; in the stated experiment it ends at its stated "
             "final state.", ("ideal gas", "sealed piston"), "a small amount"),
    ),
    scene_clause="A second piston, holding a different gas, stands beside it.",
    scene_object_rationale="A second piston with its own gas shares no gas with the first piston, so the first gas's pressure, "
                           "volume and temperature are unchanged.",
    scene_refs=("second piston",), target_terms=("this piston", "sealed piston"), version=V21,
    notes="M250 a: R is a further warming at constant volume; no C and no K (see NO_C, NO_K).")

SPECS: dict[str, r2.RoleSpecV2] = {s.structure_id: s for s in (
    S03, S04, S05, S06, S08, S09, S10, S11, S12, S14, S16, S17, S18, S19, S21, S22, S23)}

# Structures that cannot honestly support the whole design (no natural relevant quantity, no honest D): none in this batch.
INFEASIBLE: dict[str, str] = {}

# Strata not built, with the reason (never imputed; absent cells are "not evaluated", not a measured zero effect).
NO_C: dict[str, str] = {
    "S03": "The collision relations hold only the four inputs. The only further quantities are the contact time and the stiffness of "
           "the bumpers: the time enters only through F = J / dt and dv = F dt / m, which cancels by construction because J is "
           "already the answer, and a stiffness needs a spring model that the problem does not state. A C built on either would be "
           "forced, not physical.",
    "S06": "Every quantity of the network that enters (V, R1, R2, R3) is an input; wire resistance is excluded by statement, and "
           "there is no further quantity in the relations that cancels.",
    "S09": "The heat balance holds only the six inputs. The container, the room and the time are excluded by the perfect insulation "
           "and by the equilibrium reading; a temperature-scale offset is not a quantity of the system.",
    "S16": "The relations hold V, R, L and t. The coil's turns, area and core would only re-express the given inductance (and the coil "
           "resistance is negligible by statement), so none enters and cancels.",
    "S19": "Feasible but not built: the only honest cancelling quantity is the ball's mass (mass independence of projectile motion, a "
           "'famous' result). S10, S11 and S12 already carry mass-independence C quantities; a fourth would add no new mechanism and "
           "would push the batch towards the half-famous limit.",
    "S23": "p2 = p1 V1 T2 / (V2 T1) holds only the five inputs. The amount of gas n would cancel (pV = nRT), but n is fixed by "
           "p1 V1 / (R T1) and is not a free quantity: any stated value other than about 0.24 mol would contradict the inputs.",
}
NO_K: dict[str, str] = {
    "S03": "The stated regime (perfectly elastic, frictionless track) is a condition of the problem, not a quantity with a value; no "
           "quantity has an out-of-regime answer that the base problem would still ask for.",
    "S09": "The only regime is 'no phase change'. Its quantity, the boiling point of water, is fixed by the physics (373 K at the "
           "stated conditions) rather than a free value, and a lower stated value would contradict the 373 K block.",
    "S11": "The regime (level road, constant kinetic friction while the wheels slide) is stated; a regime quantity such as a gradient "
           "would change the question rather than the answer.",
    "S12": "A rollover threshold would change which limit applies, but the question asks for the speed 'without sliding', so the "
           "answer would not change outside the regime and the quantity would not be conditionally relevant.",
    "S16": "A saturation current of the coil is conceivable, but no out-of-regime law (inductance after saturation) is certified, so "
           "no K quantity with a counter-regime answer exists.",
    "S17": "Steady one-dimensional conduction through layers in series has no regime quantity in the problem; the steady state is "
           "stated, and no quantity changes the law.",
    "S18": "Slow isothermal expansion is stated. The regime quantity (the duration of the expansion) has no certified out-of-regime "
           "law without the thermal relaxation time of the gas, which the problem does not give.",
    "S19": "A ceiling or wall near the launch point does not give a K quantity: a ceiling above the maximum height changes nothing, "
           "and below it an elastic bounce leaves the range unchanged by symmetry (the flight time stays 2 vy / g), so the "
           "predicate would never change the answer.",
    "S21": "The regime (source slower than sound) is a condition on the input vs, not on a separate quantity.",
    "S23": "The regime (ideal gas) would need a condensation temperature as the quantity, and no out-of-regime law is certified for "
           "this gas.",
}


def structure(structure_id: str) -> gr.Structure:
    """The October structure with the spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), SPECS[structure_id].scene_clause)
