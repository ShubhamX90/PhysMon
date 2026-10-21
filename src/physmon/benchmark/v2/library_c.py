"""The third batch of DECOY-v2 structures, S21 to S30 (Stage 14.18; v2 B3 deliverable p.9).

Same pattern as `library.py` and `library_b.py`: a typed graph, an independently coded numeric solver for each structure (a root
finder, an ODE with an event, a linear system, a quadrature), two numeric instantiations and a relevant edit that moves the answer.
The laws are short chains from areas the first two batches do not cover (acoustics, gas laws, heat engines, magnetic energy,
refraction, fluid pressure, kinematic pursuit, vibrating strings, angled-force power, heating time), so that a 7 to 8 B model has a chance of solving
them with reasoning, while `scripts/v2/s146_generate_structures.py` still rejects any program whose renaming-invariant hash equals a
v1 template.

They are agent-authored candidates: solver-certified and UNREVIEWED. Independent expert review of the English text and the physics
is required before any use (v2 B4).
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import quad, solve_ivp
from scipy.optimize import brentq

from physmon.benchmark.v2.graph import Assumption, Structure
from physmon.benchmark.v2.library import A_G, _co, _g, _in, _spec

# --- solvers (independent routes; SI inputs in node order) -----------------------------------------


def _solve_doppler(f, c, vs):
    # The observed frequency is the root of f_obs (c - vs) = f c, found with a bracketing root finder.
    return float(brentq(lambda fo: fo * (c - vs) - f * c, 0.0, 100.0 * f, xtol=1e-12, rtol=1e-14))


def _solve_string(tension, mass, length):
    # The wave speed from v^2 (m / L) = T, then the fundamental frequency as the root of 2 L f = v.
    speed = brentq(lambda v: v * v * mass / length - tension, 1e-6, 1e6, xtol=1e-12, rtol=1e-14)
    return float(brentq(lambda f: 2.0 * length * f - speed, 1e-9, 1e9, xtol=1e-12, rtol=1e-14))


def _solve_gas(p1, v1, t1, v2, t2):
    # The final pressure as the root of p V / T = const, with the constant fixed by the initial state.
    constant = p1 * v1 / t1
    return float(brentq(lambda p: p * v2 / t2 - constant, 0.0, 1000.0 * p1, xtol=1e-9, rtol=1e-14))


def _solve_carnot(qh, th, tc):
    # Entropy balance (Qc / Tc = Qh / Th) together with energy conservation (W + Qc = Qh), as a linear system in (W, Qc).
    matrix = np.array([[1.0, 1.0], [0.0, th / tc]])
    rhs = np.array([qh, qh])
    return float(np.linalg.solve(matrix, rhs)[0])


def _solve_inductor_energy(ind, cur):
    # Work done against the induced emf while the current is raised from zero: the integral of L i di.
    energy, _ = quad(lambda i: ind * i, 0.0, cur, epsabs=1e-14, epsrel=1e-12)
    return float(energy)


def _solve_snell(n1, n2, theta1):
    # The refraction angle as the root of n1 sin(theta1) = n2 sin(theta2) on the first quadrant.
    return float(brentq(lambda th2: n2 * math.sin(th2) - n1 * math.sin(theta1), 0.0, 0.5 * math.pi, xtol=1e-14, rtol=1e-14))


def _solve_hydrostatic(p0, rho, g, h):
    # The pressure at depth as the surface pressure plus the integral of rho g over the depth.
    extra, _ = quad(lambda z: rho * g, 0.0, h, epsabs=1e-9, epsrel=1e-12)
    return float(p0 + extra)


def _solve_catch_up(a, v):
    # The car starts from rest at the same point as the truck; the time at which the gap closes again.
    return float(brentq(lambda t: 0.5 * a * t * t - v * t, v / a, 10.0 * v / a, xtol=1e-12, rtol=1e-14))


def _solve_angled_power(force, v, theta):
    # The dot product of the force vector and the velocity vector, in components along and across the ground.
    fx, fy = force * math.cos(theta), force * math.sin(theta)
    return float(fx * v + fy * 0.0)


def _solve_heating_time(m, c, d_t, power):
    # The heater warms the water until the rise reaches the target; the time at that event.
    def reached(t, y):
        return y[0] - d_t

    reached.terminal = True
    solution = solve_ivp(lambda t, y: [power / (m * c)], (0.0, 1.0e6), [0.0], events=reached, rtol=1e-11, atol=1e-13)
    return float(solution.t_events[0][0])


# --- structures ---------------------------------------------------------------------------------------


def s21_doppler_shift() -> Structure:
    return Structure(
        "S21", "Frequency heard from an approaching source", "acoustics", "doppler_approaching_source",
        (_in("f", "frequency", "Hz", "frequency emitted by the source", 440.0, (200.0, 1000.0)),
         _in("c", "speed", "m/s", "speed of sound in the air, a stated constant", 343.0, (330.0, 350.0), provenance="assumed"),
         _in("vs", "speed", "m/s", "speed of the source toward the listener", 20.0, (5.0, 80.0)),
         _co("fo", "frequency", "Hz", "frequency heard by the listener", "f*c/(c - vs)")),
        "fo",
        (Assumption("A-medium", "The air is still and the listener is at rest; the source moves directly toward the listener.", "modelling", ("vs",)),
         Assumption("A-sound", "The speed of sound is the stated constant.", "modelling", ("c",))),
        _spec("A siren emits a steady tone of {f} Hz while it moves directly toward a stationary listener at {vs} m/s. "
              "The speed of sound in the air is {c} m/s.",
              "What frequency does the listener hear?", "frequency heard by the listener", "Hz",
              "A separate alarm B in another building emits a tone of {v} {u}, but it is unrelated to the siren.",
              "A reference tuning fork B vibrates at {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the sound.", "W", equivalent="kHz"),
        ("vs", 2.0), _solve_doppler, 3,
        "the heard frequency as the root of f_obs (c - vs) = f c, found with a bracketing root finder",
        solver_rel_tol=1e-9,
        instances=({"f": 440.0, "c": 343.0, "vs": 20.0}, {"f": 512.0, "c": 343.0, "vs": 30.0}))


def s22_string_fundamental() -> Structure:
    return Structure(
        "S22", "Fundamental frequency of a stretched string", "acoustics", "stretched_string_fundamental",
        (_in("T", "force", "N", "tension in the string", 100.0, (50.0, 400.0)),
         _in("m", "mass", "kg", "mass of the string", 0.01, (0.005, 0.05)),
         _in("L", "length", "m", "length of the vibrating part of the string", 0.8, (0.5, 1.5)),
         _co("f1", "frequency", "Hz", "fundamental frequency of the string", "sqrt(T/(m*L))/2")),
        "f1",
        (Assumption("A-fixed", "The string is fixed at both ends and vibrates in its fundamental mode.", "modelling", ("L",)),
         Assumption("A-uniform", "The string is uniform, flexible and under constant tension.", "modelling", ("T", "m"))),
        _spec("A uniform string of mass {m} kg and length {L} m is fixed at both ends and stretched to a tension of {T} N.",
              "What is the fundamental frequency at which the string vibrates?", "fundamental frequency of the string", "Hz",
              "A separate guitar B in another room sounds a note of {v} {u}, but it is unrelated to this string.",
              "A reference string B vibrates at {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the vibration.", "W", equivalent="kHz"),
        ("T", 1.5), _solve_string, 3,
        "the wave speed v with v squared times the mass per length equal to the tension, then the frequency as the root of 2 L f = v",
        solver_rel_tol=1e-9,
        instances=({"T": 100.0, "m": 0.01, "L": 0.8}, {"T": 150.0, "m": 0.012, "L": 0.65}))


def s23_combined_gas_law() -> Structure:
    return Structure(
        "S23", "Final pressure of a gas in a piston", "thermodynamics", "combined_gas_law_pressure",
        (_in("p1", "pressure", "kPa", "initial pressure of the gas", 100.0, (80.0, 200.0)),
         _in("V1", "volume", "L", "initial volume of the gas", 6.0, (2.0, 10.0)),
         _in("T1", "temperature", "K", "initial temperature of the gas", 300.0, (280.0, 350.0)),
         _in("V2", "volume", "L", "final volume of the gas", 4.0, (1.0, 8.0)),
         _in("T2", "temperature", "K", "final temperature of the gas", 360.0, (280.0, 500.0)),
         _co("p2", "pressure", "kPa", "final pressure of the gas", "p1*V1*T2/(V2*T1)")),
        "p2",
        (Assumption("A-ideal", "The gas is ideal and the amount of gas does not change.", "modelling", ("p1", "V1", "V2")),
         Assumption("A-equilibrium", "The gas is in equilibrium in both the initial and the final state.", "boundary_condition", ("T1", "T2"))),
        _spec("A sealed piston holds an ideal gas at a pressure of {p1} kPa, a volume of {V1} L and a temperature of {T1} K. The gas is "
              "compressed and heated until its volume is {V2} L and its temperature is {T2} K.",
              "What is the final pressure of the gas?", "final pressure of the gas", "kPa",
              "A separate tank B in another room is at a pressure of {v} {u}, but it is unrelated to the piston.",
              "A reference gas B is at a pressure of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the compression.", "W", equivalent="Pa"),
        ("T2", 1.25), _solve_gas, 5,
        "the final pressure as the root of p V / T = constant, with the constant fixed by the initial state",
        solver_rel_tol=1e-9,
        instances=({"p1": 100.0, "V1": 6.0, "T1": 300.0, "V2": 4.0, "T2": 360.0},
                   {"p1": 150.0, "V1": 8.0, "T1": 320.0, "V2": 5.0, "T2": 400.0}))


def s24_carnot_work() -> Structure:
    return Structure(
        "S24", "Work output of a reversible heat engine", "thermodynamics", "carnot_engine_work",
        (_in("Qh", "energy", "kJ", "heat taken from the hot reservoir", 800.0, (200.0, 2000.0)),
         _in("Th", "temperature", "K", "temperature of the hot reservoir", 600.0, (450.0, 900.0)),
         _in("Tc", "temperature", "K", "temperature of the cold reservoir", 300.0, (250.0, 400.0)),
         _co("W", "energy", "kJ", "net work done by the engine", "Qh*(1 - Tc/Th)")),
        "W",
        (Assumption("A-reversible", "The engine is reversible and operates in a cycle between the two reservoirs.", "modelling", ("Th", "Tc")),
         Assumption("A-cycle", "The heat taken in is the heat taken from the hot reservoir in one cycle.", "boundary_condition", ("Qh",))),
        _spec("A reversible heat engine takes {Qh} kJ of heat from a reservoir at {Th} K in each cycle and rejects heat to a reservoir at "
              "{Tc} K.",
              "How much net work does the engine do in one cycle?", "net work done in one cycle", "kJ",
              "A separate generator B in another plant delivers {v} {u} per cycle, but it is unrelated to the engine.",
              "A reference engine B does {v} {u} of work per cycle.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the cycle.", "W", equivalent="J"),
        ("Qh", 1.25), _solve_carnot, 3,
        "the entropy balance Qc / Tc = Qh / Th together with W + Qc = Qh, solved as a linear system",
        solver_rel_tol=1e-9,
        instances=({"Qh": 800.0, "Th": 600.0, "Tc": 300.0}, {"Qh": 1200.0, "Th": 700.0, "Tc": 350.0}))


def s25_inductor_energy() -> Structure:
    return Structure(
        "S25", "Energy stored in an inductor", "circuits", "inductor_stored_energy",
        (_in("Lind", "inductance", "mH", "inductance of the coil", 250.0, (50.0, 500.0)),
         _in("Icur", "current", "A", "steady current through the coil", 3.0, (1.0, 8.0)),
         _co("Wm", "energy", "mJ", "energy stored in the magnetic field", "Lind*Icur**2/2")),
        "Wm",
        (Assumption("A-ideal", "The coil is ideal: it has no resistance and no core losses.", "modelling", ("Lind",)),
         Assumption("A-steady", "The current has reached its steady value.", "boundary_condition", ("Icur",))),
        _spec("An ideal coil has an inductance of {Lind} mH and carries a steady current of {Icur} A.",
              "How much energy is stored in the magnetic field of the coil?", "energy stored in the coil", "mJ",
              "A separate battery B on another bench stores {v} {u}, but it is unrelated to the coil.",
              "A reference coil B stores {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the field.", "W", equivalent="J"),
        ("Icur", 1.25), _solve_inductor_energy, 2,
        "the work against the induced emf while the current is raised from zero, the integral of L i di",
        solver_rel_tol=1e-9,
        instances=({"Lind": 250.0, "Icur": 3.0}, {"Lind": 120.0, "Icur": 5.0}))


def s26_snell_refraction() -> Structure:
    return Structure(
        "S26", "Angle of refraction at a flat interface", "optics", "snell_refraction_angle",
        (_in("n1", "coefficient", "1", "refractive index of the first medium", 1.0, (1.0, 1.4)),
         _in("n2", "coefficient", "1", "refractive index of the second medium", 1.5, (1.3, 1.9)),
         _in("theta1", "angle", "deg", "angle of incidence from the normal", 40.0, (20.0, 60.0)),
         _co("theta2", "angle", "deg", "angle of refraction from the normal", "asin(n1*sin(theta1)/n2)")),
        "theta2",
        (Assumption("A-flat", "The interface is flat and the light travels from the first medium into the second.", "modelling", ("n1", "n2")),
         Assumption("A-angle", "Angles are measured from the normal to the interface.", "boundary_condition", ("theta1",))),
        _spec("A ray of light in a medium of refractive index {n1} meets a flat interface with a second medium of refractive index "
              "{n2}. The angle of incidence, measured from the normal, is {theta1} degrees.",
              "What is the angle of refraction, measured from the normal?", "angle of refraction", "deg",
              "A separate ray B in another prism leaves at an angle of {v} {u}, but it is unrelated to the interface.",
              "A reference ray B is refracted by {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the refraction.", "W", equivalent="rad"),
        ("theta1", 1.25), _solve_snell, 3,
        "the refraction angle as the root of n1 sin(theta1) = n2 sin(theta2) on the first quadrant",
        solver_rel_tol=1e-9,
        instances=({"n1": 1.0, "n2": 1.5, "theta1": 40.0}, {"n1": 1.2, "n2": 1.7, "theta1": 35.0}))


def s27_hydrostatic_pressure() -> Structure:
    return Structure(
        "S27", "Absolute pressure at depth in a liquid", "fluids", "hydrostatic_pressure_at_depth",
        (_in("p0", "pressure", "kPa", "pressure at the free surface", 101.0, (95.0, 105.0)),
         _in("rho", "density", "kg/m^3", "density of the liquid", 1000.0, (700.0, 1400.0)),
         _g(),
         _in("h", "length", "m", "depth below the surface", 12.0, (2.0, 30.0)),
         _co("p", "pressure", "kPa", "absolute pressure at that depth", "p0 + rho*g*h")),
        "p",
        (A_G, Assumption("A-static", "The liquid is at rest and its density is uniform.", "modelling", ("rho",)),
         Assumption("A-surface", "The pressure at the free surface is the stated value.", "boundary_condition", ("p0",))),
        _spec("A tank is filled with a liquid of density {rho} kg/m³. The pressure at the free surface is {p0} kPa. Take g = {g} m/s².",
              "What is the absolute pressure at a depth of {h} m?", "absolute pressure at that depth", "kPa",
              "A separate gauge B in another tank reads {v} {u}, but it is unrelated to this liquid.",
              "A reference tank B has a pressure of {v} {u} at its bottom.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the pressure.", "W", equivalent="Pa"),
        ("h", 1.5), _solve_hydrostatic, 4,
        "the surface pressure plus the integral of rho g dz over the depth",
        solver_rel_tol=1e-9,
        instances=({"p0": 101.0, "rho": 1000.0, "g": 9.8, "h": 12.0}, {"p0": 100.0, "rho": 850.0, "g": 9.8, "h": 20.0}))


def s28_catch_up_time() -> Structure:
    return Structure(
        "S28", "Time for an accelerating car to overtake a truck", "mechanics", "uniform_acceleration_catch_up",
        (_in("a", "acceleration", "m/s^2", "constant acceleration of the car", 2.0, (0.5, 4.0)),
         _in("v", "speed", "m/s", "constant speed of the truck", 15.0, (5.0, 30.0)),
         _co("t", "time", "s", "time at which the car draws level with the truck", "2*v/a")),
        "t",
        (Assumption("A-start", "The car starts from rest at the moment it passes the truck, which already travels at constant speed.", "boundary_condition", ("a", "v")),
         Assumption("A-const", "The acceleration of the car and the speed of the truck are constant and both move along the same line.", "modelling", ("a", "v"))),
        _spec("A truck travels at a constant {v} m/s along a straight road. At the instant it passes a stationary car, the car starts "
              "from rest and accelerates at a constant {a} m/s² in the same direction.",
              "How long after the truck passes the car does the car draw level with the truck?", "time for the car to draw level", "s",
              "A separate lorry B on another road needs {v} {u} to stop, but it is unrelated to the car.",
              "A reference car B draws level after {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the chase.", "W", equivalent="min"),
        ("a", 1.5), _solve_catch_up, 2,
        "the non-trivial root of the gap function a t squared over two minus v t, found with a bracketing root finder",
        solver_rel_tol=1e-9,
        instances=({"a": 2.0, "v": 15.0}, {"a": 1.5, "v": 12.0}))


def s29_power_of_angled_force() -> Structure:
    return Structure(
        "S29", "Power delivered by a force at an angle to the motion", "mechanics", "angled_force_power",
        (_in("F", "force", "N", "magnitude of the pulling force", 40.0, (10.0, 120.0)),
         _in("v", "speed", "m/s", "speed of the sled", 3.0, (1.0, 8.0)),
         _in("theta", "angle", "deg", "angle of the rope above the horizontal", 30.0, (10.0, 60.0)),
         _co("P", "power", "W", "power delivered to the sled by the rope", "F*v*cos(theta)")),
        "P",
        (Assumption("A-const", "The pulling force and the speed are constant and the rope stays at the stated angle.", "modelling", ("F", "v")),
         Assumption("A-direction", "The sled moves along the ground and the angle is measured from the direction of motion.", "boundary_condition", ("theta",))),
        _spec("A sled is pulled along level ground at a constant speed of {v} m/s by a rope that makes an angle of {theta} degrees above "
              "the horizontal. The tension in the rope is {F} N.",
              "What power does the rope deliver to the sled?", "power delivered to the sled", "W",
              "A separate winch B on another jetty delivers {v} {u}, but it is unrelated to the sled.",
              "A reference rope B delivers {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the pulling.", "Hz", equivalent="kW"),
        ("F", 1.25), _solve_angled_power, 3,
        "the power as the dot product of the force vector and the velocity vector, computed in components",
        solver_rel_tol=1e-9,
        instances=({"F": 40.0, "v": 3.0, "theta": 30.0}, {"F": 60.0, "v": 2.0, "theta": 25.0}))


def s30_heating_time() -> Structure:
    return Structure(
        "S30", "Time for a heater to warm water", "thermodynamics", "electric_heater_water_heating_time",
        (_in("m", "mass", "kg", "mass of the water", 2.0, (0.5, 5.0)),
         _in("c", "specific_heat", "J/(kg*K)", "specific heat capacity of water, a stated constant", 4186.0, (4100.0, 4200.0), provenance="assumed"),
         _in("dT", "temperature", "K", "required rise in temperature", 40.0, (10.0, 70.0)),
         _in("P", "power", "W", "power delivered to the water by the heater", 1500.0, (500.0, 3000.0)),
         _co("t", "time", "s", "time needed for the water to warm by the required amount", "m*c*dT/P")),
        "t",
        (Assumption("A-loss", "All of the heater power goes into the water and no heat is lost to the surroundings.", "modelling", ("P",)),
         Assumption("A-c", "The specific heat capacity is the stated constant over the whole temperature range.", "modelling", ("c",))),
        _spec("An electric heater delivers {P} W to {m} kg of water. The specific heat capacity of water is {c} J/(kg·K).",
              "How long does it take to raise the temperature of the water by {dT} K?", "time to warm the water", "s",
              "A separate kettle B in another kitchen needs {v} {u} to boil, but it is unrelated to this heater.",
              "A reference heater B needs {v} {u} for the same rise.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the heating.", "W", equivalent="min"),
        ("dT", 1.25), _solve_heating_time, 4,
        "the temperature rise integrated at the constant rate P / (m c) until it reaches the required rise",
        solver_rel_tol=1e-6,
        instances=({"m": 2.0, "c": 4186.0, "dT": 40.0, "P": 1500.0}, {"m": 1.5, "c": 4186.0, "dT": 60.0, "P": 2000.0}))


ALL = (s21_doppler_shift, s22_string_fundamental, s23_combined_gas_law, s24_carnot_work, s25_inductor_energy, s26_snell_refraction,
       s27_hydrostatic_pressure, s28_catch_up_time, s29_power_of_angled_force, s30_heating_time)


def all_structures() -> list[Structure]:
    return [factory() for factory in ALL]
