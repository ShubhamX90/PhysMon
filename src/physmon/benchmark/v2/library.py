"""The first ten DECOY-v2 structures (Stage 14.6; v2 B3 deliverable p.9; first sprint item 6, p.49).

Each structure is a typed graph with an independently coded numeric solver (a different route from the graph's closed
form: a linear system, an ODE integration, a root finder, a momentum-and-energy quadratic, a force-picture time step).
The laws and compositions are not among the 34 v1 clusters; `scripts/v2/s146_generate_structures.py` checks that no
canonical program hash collides with any v1 template.

These are agent-authored candidates. They are solver-certified but UNREVIEWED: independent expert review of the English
text and the physics is required before any use (v2 B4, p.9-10). The prompt grammar avoids incidental numerals so that
every numeral in a prompt can be tied to a graph node.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

from physmon.benchmark.v2 import dimensions as dm
from physmon.benchmark.v2.graph import Assumption, Node, RenderSpec, Structure

GEN_METADATA = ("The laboratory temperature is {v} {u}.", "°C")
GEN_NONNUMERIC = "The apparatus was assembled on a sturdy wooden bench near the window."


def _in(name, qtype, unit, desc, value, domain, provenance="measured", sign="magnitudes are positive"):
    return Node(name, "input", qtype, unit, desc, value=value, provenance=provenance, domain=domain,
                sign_convention=sign)


def _co(name, qtype, unit, desc, expr):
    return Node(name, "computed", qtype, unit, desc, expr=expr, provenance="computed")


def _g():
    return _in("g", "acceleration", "m/s^2", "gravitational acceleration, a stated constant", 9.8, (9.7, 9.9),
               provenance="assumed")


A_G = Assumption("A-g", "g is a uniform constant of the stated value.", "modelling", ("g",))


# --- solvers (independent routes) -----------------------------------------------------------------


def _solve_atwood(m1, m2, mp, g):
    # Newton's second law for each block and the pulley's rotational equation as a linear system in (a, T1, T2).
    matrix = np.array([[-m1, 1.0, 0.0], [m2, 0.0, 1.0], [-mp / 2.0, -1.0, 1.0]])
    rhs = np.array([m1 * g, m2 * g, 0.0])
    # unknowns: a, T1, T2 with T1 - m1 a = m1 g ; m2 a + T2 = m2 g ; T2 - T1 - (mp/2) a = 0
    return float(np.linalg.solve(matrix, rhs)[0])


def _solve_incline(theta, mu, d, g):
    # Force picture per unit mass (driving component minus kinetic friction), integrated from rest until the block
    # has slid the distance d; the speed at that event is returned.
    drive = g * math.sin(theta) - mu * g * math.cos(theta)

    def arrived(t, y):
        return y[0] - d

    arrived.terminal = True
    solution = solve_ivp(lambda t, y: [y[1], drive], (0.0, 100.0), [0.0, 0.0], events=arrived, rtol=1e-11,
                         atol=1e-13)
    return float(solution.y_events[0][0][1])


def _solve_elastic(m1, v1, m2, v2):
    # Conservation of momentum and kinetic energy; the non-trivial root of the resulting quadratic.
    p = m1 * v1 + m2 * v2
    e = 0.5 * m1 * v1 ** 2 + 0.5 * m2 * v2 ** 2
    a = 0.5 * m1 + 0.5 * m1 ** 2 / m2
    b = -m1 * p / m2
    c = 0.5 * p ** 2 / m2 - e
    roots = np.roots([a, b, c])
    return float(max(roots, key=lambda r: abs(r - v1)).real)


def _solve_spring(k, x0, m):
    # Integrate the oscillator from rest at displacement x0 and take the largest speed reached.
    omega2 = k / m
    quarter = 0.5 * math.pi / math.sqrt(omega2)
    solution = solve_ivp(lambda t, y: [y[1], -omega2 * y[0]], (0.0, quarter), [x0, 0.0], rtol=1e-11, atol=1e-13,
                         dense_output=True)
    times = np.linspace(0.0, quarter, 4001)
    return float(np.max(np.abs(solution.sol(times)[1])))


def _solve_disc(tau, tau_f, m, r):
    # Spin up from rest through one radian and recover alpha from omega^2 = 2 alpha phi (an energy observable).
    inertia = 0.5 * m * r ** 2
    solution = solve_ivp(lambda t, y: [y[1], (tau - tau_f) / inertia], (0.0, 50.0), [0.0, 0.0], rtol=1e-11,
                         atol=1e-13, dense_output=True,
                         events=lambda t, y: y[0] - 1.0)
    omega_at_one_radian = float(solution.y_events[0][0][1])
    return omega_at_one_radian ** 2 / 2.0


def _solve_network(volt, r1, r2, r3):
    # Nodal analysis for the voltage at the junction, then the current through the third resistor.
    junction = (volt / r1) / (1.0 / r1 + 1.0 / r2 + 1.0 / r3)
    return float(junction / r3)


def _solve_rc(v0, r, c, t):
    solution = solve_ivp(lambda s, y: [(v0 - y[0]) / (r * c)], (0.0, t), [0.0], rtol=1e-11, atol=1e-13)
    return float(solution.y[0][-1])


def _solve_series_caps(c1, c2, volt):
    # Equal charge on series capacitors and the loop law give the two voltages; sum the stored energies.
    v1, v2 = np.linalg.solve(np.array([[1.0, 1.0], [c1, -c2]]), np.array([volt, 0.0]))
    return float(0.5 * c1 * v1 ** 2 + 0.5 * c2 * v2 ** 2)


def _solve_calorimetry(m1, c1, t1, m2, c2, t2):
    # Energy balance solved for the final temperature with a bracketing root finder; return the water's rise.
    final = brentq(lambda t: m1 * c1 * (t - t1) + m2 * c2 * (t - t2), 0.0, 2000.0, xtol=1e-12, rtol=1e-14)
    return float(final - t2)


def _solve_projectile(v, theta, h0, g):
    # Integrate the vertical motion and stop at the apex (vertical velocity zero).
    def apex(t, y):
        return y[1]

    apex.terminal = True
    solution = solve_ivp(lambda t, y: [y[1], -g], (0.0, 100.0), [h0, v * math.sin(theta)], events=apex,
                         rtol=1e-11, atol=1e-13)
    return float(solution.y_events[0][0][0])


# --- structures -----------------------------------------------------------------------------------


def _spec(context, question, phrase, unit, isolated, comparison, incompatible, incompatible_unit,
          equivalent=None, formats=None):
    return RenderSpec(
        context=context, question=question, quantity_phrase=phrase, target_unit=unit,
        isolated_sentence=isolated, incompatible_sentence=incompatible, incompatible_unit=incompatible_unit,
        metadata_sentence=GEN_METADATA[0], metadata_unit=GEN_METADATA[1], nonnumeric_sentence=GEN_NONNUMERIC,
        comparison_sentence=comparison, equivalent_unit=equivalent, formats=formats or {})


def s01_atwood_massive_pulley() -> Structure:
    return Structure(
        "S01", "Atwood machine with a massive disc pulley", "mechanics", "atwood_massive_pulley",
        (_in("m1", "mass", "kg", "mass of the left block", 3.0, (2.0, 4.0)),
         _in("m2", "mass", "kg", "mass of the right block", 5.0, (4.5, 7.0)),
         _in("M", "mass", "kg", "mass of the uniform disc pulley", 2.0, (1.0, 4.0)),
         _g(),
         _co("m_eff", "mass", "kg", "effective inertial mass of the system", "m1 + m2 + M/2"),
         _co("a", "acceleration", "m/s^2", "acceleration of the blocks", "(m2 - m1)*g/m_eff")),
        "a",
        (A_G, Assumption("A-string", "The string is light and inextensible and does not slip on the pulley.",
                         "modelling", ("m1", "m2")),
         Assumption("A-pulley", "The pulley is a uniform solid disc turning without axle friction.", "modelling",
                    ("M",))),
        _spec("Two blocks hang from a light string that passes over a pulley, which is a uniform solid disc of mass "
              "{M} kg. The string does not slip on the pulley. The left block has mass {m1} kg and the right block "
              "has mass {m2} kg. Take g = {g} m/s².",
              "What is the magnitude of the acceleration of the blocks?", "acceleration of the blocks", "m/s^2",
              "In a separate experiment, a different pulley system B accelerates at {v} {u}, but it is mechanically "
              "isolated from the two blocks.",
              "A reference pulley system B has an acceleration of {v} {u}.",
              "A separate sensor B reports a reading of {v} {u}, but it is not connected to the blocks.", "W",
              equivalent="cm/s^2"),
        ("m2", 1.2), _solve_atwood, 4,
        "Newton's laws for each block and the pulley's rotational equation solved as a 3x3 linear system",
        instances=({"m1": 3.0, "m2": 5.0, "M": 2.0, "g": 9.8}, {"m1": 2.4, "m2": 5.6, "M": 3.0, "g": 9.8}))


def s02_rough_incline_speed() -> Structure:
    return Structure(
        "S02", "Block sliding down a rough incline", "mechanics", "rough_incline_speed",
        (_in("theta", "angle", "deg", "incline angle", 30.0, (25.0, 50.0)),
         _in("mu", "coefficient", "1", "coefficient of kinetic friction", 0.15, (0.05, 0.2)),
         _in("d", "length", "m", "distance slid along the incline", 4.0, (2.0, 6.0)),
         _g(),
         _co("a", "acceleration", "m/s^2", "acceleration down the incline", "g*(sin(theta) - mu*cos(theta))"),
         _co("v", "speed", "m/s", "speed after sliding the distance", "sqrt(2*a*d)")),
        "v",
        (A_G, Assumption("A-rest", "The block starts from rest.", "boundary_condition", ("d",)),
         Assumption("A-friction", "The coefficient of kinetic friction is constant along the incline.", "modelling",
                    ("mu",))),
        _spec("A block is released from rest on a rough incline that makes an angle of {theta} degrees with the "
              "horizontal. The coefficient of kinetic friction between the block and the incline is {mu}. Take "
              "g = {g} m/s². The block slides {d} m down the incline.",
              "What is the speed of the block after it has slid that distance?", "speed of the block", "m/s",
              "A separate cart B on another track is moving at {v} {u}, but it never interacts with the block.",
              "A reference cart B moves at {v} {u}.",
              "A separate heater B is rated at {v} {u}, but it is not connected to the block.", "W",
              equivalent="km/h"),
        ("d", 1.5), _solve_incline, 4,
        "force picture per unit mass integrated with an adaptive ODE solver from rest until the block has slid "
        "the distance",
        solver_rel_tol=1e-6,
        instances=({"theta": 30.0, "mu": 0.15, "d": 4.0, "g": 9.8}, {"theta": 40.0, "mu": 0.1, "d": 5.0, "g": 9.8}))


def s03_elastic_collision() -> Structure:
    return Structure(
        "S03", "One-dimensional perfectly elastic collision", "mechanics", "elastic_collision_1d",
        (_in("m1", "mass", "kg", "mass of the first cart", 3.0, (2.5, 5.0)),
         _in("v1", "velocity", "m/s", "velocity of the first cart before the collision", 6.0, (4.0, 8.0),
             sign="positive along the first cart's original direction of motion"),
         _in("m2", "mass", "kg", "mass of the second cart", 2.0, (1.0, 2.4)),
         _in("v2", "velocity", "m/s", "velocity of the second cart before the collision", 1.0, (0.2, 2.0),
             sign="positive along the first cart's original direction of motion"),
         _co("v1f", "velocity", "m/s", "velocity of the first cart after the collision",
             "((m1 - m2)*v1 + 2*m2*v2)/(m1 + m2)")),
        "v1f",
        (Assumption("A-elastic", "The collision is perfectly elastic and the track is frictionless.", "modelling",
                    ("m1", "m2")),
         Assumption("A-1d", "Both carts move along one straight line and the first cart overtakes the second.",
                    "boundary_condition", ("v1", "v2"))),
        _spec("A cart of mass {m1} kg moves at {v1} m/s along a straight frictionless track and collides head-on "
              "with a second cart of mass {m2} kg that is moving ahead of it at {v2} m/s in the same direction. The "
              "collision is perfectly elastic.",
              "What is the velocity of the first cart immediately after the collision, taking its original "
              "direction of motion as positive?", "velocity of the first cart", "m/s",
              "A third cart B on a different track moves at {v} {u} but takes no part in the collision.",
              "A reference cart B has a velocity of {v} {u}.",
              "A separate lamp B is rated at {v} {u} and takes no part in the collision.", "W", equivalent="km/h"),
        ("m1", 1.25), _solve_elastic, 4,
        "conservation of momentum and kinetic energy combined into a quadratic whose non-trivial root is taken",
        instances=({"m1": 3.0, "v1": 6.0, "m2": 2.0, "v2": 1.0}, {"m1": 4.0, "v1": 5.0, "m2": 1.5, "v2": 0.5}))


def s04_spring_max_speed() -> Structure:
    return Structure(
        "S04", "Maximum speed of a block released from a stretched spring", "mechanics", "spring_release_speed",
        (_in("k", "spring_constant", "N/m", "spring constant", 200.0, (100.0, 400.0)),
         _in("x", "length", "m", "initial displacement from equilibrium", 0.15, (0.05, 0.3)),
         _in("m", "mass", "kg", "mass of the block", 0.5, (0.3, 1.0)),
         _co("omega", "angular_frequency", "rad/s", "angular frequency", "sqrt(k/m)"),
         _co("v", "speed", "m/s", "maximum speed", "omega*x")),
        "v",
        (Assumption("A-hooke", "The spring is ideal and massless and obeys Hooke's law.", "modelling", ("k",)),
         Assumption("A-table", "The table is horizontal and frictionless.", "modelling", ("m",)),
         Assumption("A-release", "The block is released from rest at the stated displacement.",
                    "boundary_condition", ("x",))),
        _spec("A block of mass {m} kg rests on a horizontal frictionless table and is attached to a horizontal "
              "spring of spring constant {k} N/m. The block is pulled {x} m from its equilibrium position and "
              "released from rest.",
              "What is the maximum speed of the block?", "maximum speed of the block", "m/s",
              "A second block-and-spring system on another table reaches a maximum speed of {v} {u}, but it is not "
              "connected to this one.",
              "A reference block-and-spring system B reaches a maximum speed of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it is not connected to the spring.", "W",
              equivalent="km/h"),
        ("k", 1.5), _solve_spring, 3,
        "the oscillator equation integrated from rest with an adaptive ODE solver; the largest speed reached is taken",
        solver_rel_tol=1e-6,
        instances=({"k": 200.0, "x": 0.15, "m": 0.5}, {"k": 150.0, "x": 0.2, "m": 0.8}))


def s05_disc_angular_acceleration() -> Structure:
    return Structure(
        "S05", "Angular acceleration of a disc under a driving and a friction torque", "mechanics",
        "rotational_second_law_friction",
        (_in("tau", "torque", "N*m", "driving torque", 6.0, (4.0, 8.0)),
         _in("tau_f", "torque", "N*m", "friction torque", 1.5, (0.5, 2.5)),
         _in("m", "mass", "kg", "mass of the disc", 4.0, (2.0, 6.0)),
         _in("r", "length", "m", "radius of the disc", 0.25, (0.15, 0.4)),
         _co("Inertia", "moment_of_inertia", "kg*m^2", "moment of inertia of a uniform solid disc", "m*r**2/2"),
         _co("alpha", "angular_acceleration", "rad/s^2", "angular acceleration", "(tau - tau_f)/Inertia")),
        "alpha",
        (Assumption("A-disc", "The disc is uniform and solid and turns about its central axis.", "modelling",
                    ("m", "r")),
         Assumption("A-torques", "Both torques are constant and the driving torque exceeds the friction torque.",
                    "boundary_condition", ("tau", "tau_f"))),
        _spec("A uniform solid disc of mass {m} kg and radius {r} m rotates about its central axis. A constant "
              "driving torque of {tau} N*m acts on the disc while a constant friction torque of {tau_f} N*m opposes "
              "the motion.",
              "What is the magnitude of the angular acceleration of the disc?", "angular acceleration of the disc",
              "rad/s^2",
              "A different flywheel B in the next laboratory has an angular acceleration of {v} {u}, but it is not "
              "coupled to the disc.",
              "A reference flywheel B has an angular acceleration of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it is not coupled to the disc.", "W", equivalent=None),
        ("tau", 1.25), _solve_disc, 4,
        "the equation of motion integrated from rest through one radian; alpha recovered from omega squared over "
        "twice the angle",
        solver_rel_tol=1e-6,
        instances=({"tau": 6.0, "tau_f": 1.5, "m": 4.0, "r": 0.25}, {"tau": 7.5, "tau_f": 2.0, "m": 3.0, "r": 0.3}))


def s06_resistor_network() -> Structure:
    return Structure(
        "S06", "Current through one resistor of a series-parallel network", "circuits", "series_parallel_current",
        (_in("V", "voltage", "V", "battery emf", 12.0, (6.0, 24.0)),
         _in("R1", "resistance", "Ω", "series resistor", 4.0, (2.0, 8.0)),
         _in("R2", "resistance", "Ω", "first resistor of the parallel pair", 6.0, (3.0, 12.0)),
         _in("R3", "resistance", "Ω", "second resistor of the parallel pair", 12.0, (8.0, 24.0)),
         _co("R23", "resistance", "Ω", "equivalent resistance of the parallel pair", "R2*R3/(R2 + R3)"),
         _co("Req", "resistance", "Ω", "total resistance", "R1 + R23"),
         _co("Itot", "current", "A", "total current", "V/Req"),
         _co("V23", "voltage", "V", "voltage across the parallel pair", "Itot*R23"),
         _co("I3", "current", "A", "current through the second resistor of the pair", "V23/R3")),
        "I3",
        (Assumption("A-battery", "The battery has negligible internal resistance.", "modelling", ("V",)),
         Assumption("A-ohmic", "All resistors are ohmic and the wires have negligible resistance.", "modelling",
                    ("R1", "R2", "R3"))),
        _spec("A battery of emf {V} V and negligible internal resistance is connected in series with a {R1} Ω "
              "resistor and then with a parallel pair made of a first resistor of {R2} Ω and a second resistor of "
              "{R3} Ω.",
              "What current flows through the second resistor of the parallel pair?",
              "current through the second resistor of the parallel pair", "A",
              "A separate circuit B on another board carries a current of {v} {u}, but it shares no connection with "
              "this circuit.",
              "A reference circuit B carries a current of {v} {u}.",
              "A separate oscillator B runs at {v} {u}, but it is not part of this circuit.", "Hz", equivalent="mA"),
        ("V", 1.5), _solve_network, 4,
        "nodal analysis for the junction voltage, then the current through the second resistor",
        instances=({"V": 12.0, "R1": 4.0, "R2": 6.0, "R3": 12.0}, {"V": 18.0, "R1": 3.0, "R2": 9.0, "R3": 15.0}))


def s07_rc_charging() -> Structure:
    return Structure(
        "S07", "Capacitor voltage during charging through a resistor", "circuits", "rc_charging_voltage",
        (_in("V0", "voltage", "V", "battery emf", 12.0, (6.0, 24.0)),
         _in("R", "resistance", "kΩ", "series resistance", 5.0, (2.0, 10.0)),
         _in("C", "capacitance", "μF", "capacitance", 20.0, (10.0, 40.0)),
         _in("t", "time", "ms", "time after the connection", 80.0, (40.0, 200.0)),
         _co("tau", "time", "s", "time constant", "R*C"),
         _co("x", "dimensionless", "1", "elapsed time in units of the time constant", "t/tau"),
         _co("VC", "voltage", "V", "capacitor voltage", "V0*(1 - exp(-x))")),
        "VC",
        (Assumption("A-uncharged", "The capacitor is initially uncharged.", "boundary_condition", ("C",)),
         Assumption("A-ideal", "The battery and wires are ideal and the capacitor does not leak.", "modelling",
                    ("V0", "R"))),
        _spec("A capacitor of {C} μF, initially uncharged, is connected in series with a {R} kΩ resistor to a "
              "battery of emf {V0} V. The connection is made at the start of the experiment.",
              "What is the voltage across the capacitor {t} ms after the connection is made?",
              "voltage across the capacitor", "V",
              "Another capacitor circuit on a different board has {v} {u} across its capacitor, but it is not "
              "connected to this circuit.",
              "A reference capacitor circuit B has {v} {u} across its capacitor.",
              "A separate heater B is rated at {v} {u}, but it is not connected to this circuit.", "W",
              equivalent="mV"),
        ("t", 1.5), _solve_rc, 4,
        "the charging equation dV/dt = (V0 - V)/(R C) integrated with an adaptive ODE solver",
        solver_rel_tol=1e-6,
        instances=({"V0": 12.0, "R": 5.0, "C": 20.0, "t": 80.0}, {"V0": 9.0, "R": 8.0, "C": 15.0, "t": 150.0}))


def s08_series_capacitor_energy() -> Structure:
    return Structure(
        "S08", "Energy stored in two capacitors in series", "circuits", "series_capacitor_energy",
        (_in("C1", "capacitance", "μF", "first capacitor", 4.0, (2.0, 8.0)),
         _in("C2", "capacitance", "μF", "second capacitor", 12.0, (8.0, 20.0)),
         _in("V", "voltage", "V", "battery emf", 100.0, (50.0, 200.0)),
         _co("Ceq", "capacitance", "F", "equivalent series capacitance", "C1*C2/(C1 + C2)"),
         _co("Estore", "energy", "mJ", "total stored energy", "Ceq*V**2/2")),
        "Estore",
        (Assumption("A-charged", "The capacitors are fully charged and were initially uncharged.",
                    "boundary_condition", ("C1", "C2")),
         Assumption("A-source", "The battery is ideal with negligible internal resistance.", "modelling", ("V",))),
        _spec("Two capacitors of {C1} μF and {C2} μF are connected in series across a battery of emf {V} V and are "
              "fully charged.",
              "How much energy is stored in the two capacitors together?", "energy stored in the capacitors", "mJ",
              "A separate capacitor bank on another bench stores {v} {u}, but it is not connected to this circuit.",
              "A reference capacitor bank B stores {v} {u}.",
              "A separate oscillator B runs at {v} {u}, but it is not connected to this circuit.", "Hz",
              equivalent="J"),
        ("V", 1.25), _solve_series_caps, 3,
        "equal charge on series capacitors and the loop law solved as a linear system, then the energies summed",
        instances=({"C1": 4.0, "C2": 12.0, "V": 100.0}, {"C1": 6.0, "C2": 10.0, "V": 150.0}))


def s09_calorimetry() -> Structure:
    return Structure(
        "S09", "Temperature rise of water when a hot block is placed in it", "thermodynamics", "calorimetry_mixing_temperature",
        (_in("m1", "mass", "kg", "mass of the block", 0.5, (0.3, 0.8)),
         _in("c1", "specific_heat", "J/(kg*K)", "specific heat of the block", 385.0, (380.0, 390.0),
             provenance="assumed"),
         _in("T1", "temperature", "K", "initial temperature of the block", 373.0, (350.0, 400.0)),
         _in("m2", "mass", "kg", "mass of the water", 0.4, (0.3, 0.6)),
         _in("c2", "specific_heat", "J/(kg*K)", "specific heat of the water", 4186.0, (4100.0, 4250.0),
             provenance="assumed"),
         _in("T2", "temperature", "K", "initial temperature of the water", 293.0, (280.0, 300.0)),
         _co("Tf", "temperature", "K", "final equilibrium temperature",
             "(m1*c1*T1 + m2*c2*T2)/(m1*c1 + m2*c2)"),
         _co("dT", "temperature_change", "K", "temperature rise of the water", "Tf - T2")),
        "dT",
        (Assumption("A-heat", "No heat is exchanged with the surroundings and no phase change occurs.", "modelling",
                    ("T1", "T2")),
         Assumption("A-c", "The specific heats are constant over the temperature range.", "modelling",
                    ("c1", "c2"))),
        _spec("A {m1} kg block of copper with specific heat {c1} J/(kg*K) at {T1} K is placed in {m2} kg of water "
              "with specific heat {c2} J/(kg*K) at {T2} K inside a perfectly insulated container.",
              "By how many kelvin does the temperature of the water rise?",
              "temperature rise of the water", "K",
              "A separate beaker of oil in the next room has warmed by {v} {u}, but it is not in contact with the "
              "container.",
              "A reference container B has a water temperature rise of {v} {u}.",
              "A separate cart B moves at {v} {u}, but it has nothing to do with the container.", "m/s",
              equivalent=None),
        ("m1", 1.5), _solve_calorimetry, 6,
        "the energy balance m1 c1 (T - T1) + m2 c2 (T - T2) = 0 solved for T with a bracketing root finder",
        solver_rel_tol=1e-9,
        instances=({"m1": 0.5, "c1": 385.0, "T1": 373.0, "m2": 0.4, "c2": 4186.0, "T2": 293.0},
                   {"m1": 0.7, "c1": 385.0, "T1": 390.0, "m2": 0.35, "c2": 4186.0, "T2": 288.0}))


def s10_projectile_max_height() -> Structure:
    return Structure(
        "S10", "Maximum height of a ball launched from a platform", "mechanics", "projectile_apex_from_platform",
        (_in("v", "speed", "m/s", "launch speed", 20.0, (12.0, 30.0)),
         _in("theta", "angle", "deg", "launch angle above the horizontal", 40.0, (30.0, 70.0)),
         _in("h0", "length", "m", "height of the platform above the ground", 5.0, (1.0, 10.0)),
         _g(),
         _co("vy", "speed", "m/s", "initial vertical speed", "v*sin(theta)"),
         _co("H", "length", "m", "maximum height above the ground", "h0 + vy**2/(2*g)")),
        "H",
        (A_G, Assumption("A-drag", "Air resistance is neglected.", "modelling", ("v", "theta")),
         Assumption("A-ground", "The ground is level and the platform height is measured from it.",
                    "boundary_condition", ("h0",))),
        _spec("A ball is launched with speed {v} m/s at {theta} degrees above the horizontal from a platform {h0} m "
              "above level ground. Neglect air resistance and take g = {g} m/s².",
              "What is the maximum height of the ball above the ground?", "maximum height of the ball", "m",
              "A separate drone B hovers at a height of {v} {u} nearby, but it plays no part in the ball's motion.",
              "A reference drone B hovers at a height of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the ball's motion.", "W",
              equivalent="cm"),
        ("v", 1.25), _solve_projectile, 4,
        "the vertical motion integrated with an adaptive ODE solver until the apex (vertical velocity zero)",
        solver_rel_tol=1e-6,
        instances=({"v": 20.0, "theta": 40.0, "h0": 5.0, "g": 9.8}, {"v": 15.0, "theta": 55.0, "h0": 8.0, "g": 9.8}))


ALL = (s01_atwood_massive_pulley, s02_rough_incline_speed, s03_elastic_collision, s04_spring_max_speed,
       s05_disc_angular_acceleration, s06_resistor_network, s07_rc_charging, s08_series_capacitor_energy,
       s09_calorimetry, s10_projectile_max_height)


def all_structures() -> list[Structure]:
    return [factory() for factory in ALL]


assert dm.unit("rad/s").dim.exps  # the unit registry is loaded at import
