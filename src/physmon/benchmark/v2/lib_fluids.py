"""Fluids and continuum mechanics: five new DECOY-v2 structures, S91 to S95, and gold solution plans (Stage 14.19).

Same pattern as `library_c.py`: a typed graph, an independently coded numeric solver (a quadrature with a root finder, a pressure
integral over the faces of a body, an ODE with an event, a velocity-profile integral with a root finder, a linear system), at least
four numeric instantiations and a relevant edit that moves the answer.

The module also carries the gold solution plans (`trace.Plan`) of the five new structures and of the existing structure S27.

Admission status: agent-verified, not expert-reviewed. The structures are solver-certified by `certify.py`, their plans are checked
by `trace.validate_plan` and re-derived blind by a separate verifier agent; no human physicist has reviewed them.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import quad, solve_ivp
from scipy.optimize import brentq

from physmon.benchmark.v2.graph import Assumption, Structure
from physmon.benchmark.v2.library import A_G, _co, _g, _in, _spec
from physmon.benchmark.v2.trace import Plan, Step

# --- solvers (independent routes; SI inputs in node order) -----------------------------------------


def _solve_venturi(d1, d2, rho, rho_m, g, dh):
    # The manometer reading as a hydrostatic integral, then the speed in the wide section as the root of the Bernoulli
    # balance 0.5 rho (v2^2 - v1^2) = dp with v2 taken from the equal-flux condition v1 A1 = v2 A2.
    a1, a2 = math.pi * d1 ** 2 / 4.0, math.pi * d2 ** 2 / 4.0
    dp, _ = quad(lambda z: (rho_m - rho) * g, 0.0, dh, epsabs=1e-12, epsrel=1e-13)

    def mismatch(v1):
        v2 = v1 * a1 / a2
        return 0.5 * rho * (v2 ** 2 - v1 ** 2) - dp

    v1 = brentq(mismatch, 0.0, 1.0e3, xtol=1e-14, rtol=1e-14)
    return float(a1 * v1)


def _solve_submerged_tension(a, rho_s, rho_l, g):
    # Net vertical force of the liquid on the cube from the pressures on its top and bottom faces (the side faces cancel),
    # at an arbitrary depth, then the string tension from the vertical force balance.
    p_surface, z_top = 101325.0, 0.37

    def pressure(z):
        return p_surface + rho_l * g * z

    upward = (pressure(z_top + a) - pressure(z_top)) * a * a
    weight = rho_s * a ** 3 * g
    return float(upward - weight)


def _solve_drain_time(big_d, small_d, h0, h1, g):
    # Integrate the level equation A dh/dt = -a sqrt(2 g h) from h0 until the level reaches h1 (an event).
    ratio = (small_d / big_d) ** 2  # a / A

    def reached(t, y):
        return y[0] - h1

    reached.terminal = True
    solution = solve_ivp(lambda t, y: [-ratio * math.sqrt(2.0 * g * y[0])], (0.0, 1.0e6), [h0], events=reached,
                         rtol=1e-12, atol=1e-14)
    return float(solution.t_events[0][0])


def _solve_pipe_power(d, length, eta, v):
    # The pressure gradient G for which the parabolic profile u(r) = G (R^2 - r^2) / (4 eta) carries the given volume flow
    # (the profile integrated over the cross-section), found with a root finder; then power = (G L) times the flow.
    radius = d / 2.0
    flow = math.pi * radius ** 2 * v

    def carried(gradient):
        integral, _ = quad(lambda r: gradient * (radius ** 2 - r ** 2) / (4.0 * eta) * 2.0 * math.pi * r, 0.0, radius,
                           epsabs=0.0, epsrel=1e-13)
        return integral - flow

    gradient = brentq(carried, 1e-9, 1.0e12, xtol=1e-12, rtol=1e-14)
    return float(gradient * length * flow)


def _solve_hydraulic_force(m, a_large, a_small, rho, g, h):
    # Gauge pressures as the unknowns of a linear system: the load's equilibrium on the large piston, the hydrostatic step
    # between the two piston faces, and the force on the small piston from the pressure there.
    matrix = np.array([[a_large, 0.0, 0.0], [-1.0, 1.0, 0.0], [0.0, -a_small, 1.0]])
    rhs = np.array([m * g, rho * g * h, 0.0])
    return float(np.linalg.solve(matrix, rhs)[2])


# --- structures ---------------------------------------------------------------------------------------


def s91_venturi_flow_rate() -> Structure:
    return Structure(
        "S91", "Flow rate through a Venturi meter read with a U-tube manometer", "fluids", "venturi_meter_manometer_flow_rate",
        (_in("d1", "length", "cm", "diameter of the wide section of the pipe", 10.0, (8.0, 14.0)),
         _in("d2", "length", "cm", "diameter of the narrow throat", 5.0, (3.0, 6.0)),
         _in("rho", "density", "kg/m^3", "density of the flowing liquid", 1000.0, (800.0, 1100.0)),
         _in("rho_m", "density", "kg/m^3", "density of the liquid in the U-tube", 13600.0, (12000.0, 14000.0)),
         _g(),
         _in("dh", "length", "cm", "difference between the liquid levels in the two arms of the U-tube", 12.0, (4.0, 25.0)),
         _co("dp", "pressure", "kPa", "pressure difference between the wide section and the throat",
             "(rho_m - rho)*g*dh"),
         _co("v1", "speed", "m/s", "speed of the liquid in the wide section",
             "sqrt(2*dp/(rho*((d1/d2)**4 - 1)))"),
         _co("Q", "volume_flow_rate", "L/s", "volume flow rate through the pipe", "pi*d1**2*v1/4")),
        "Q",
        (A_G,
         Assumption("A-ideal", "The liquid is incompressible and flows steadily without friction, and its speed is uniform across each section.",
                    "modelling", ("rho", "d1", "d2")),
         Assumption("A-level", "The pipe is horizontal and the tubing of the manometer above the U-tube liquid is filled with the flowing liquid.",
                    "boundary_condition", ("rho_m", "dh"))),
        _spec("A liquid of density {rho} kg/m³ flows steadily through a horizontal Venturi meter. The wide section of the pipe has a "
              "diameter of {d1} cm and the narrow throat has a diameter of {d2} cm. A U-tube manometer joins a tapping in the wide "
              "section to a tapping in the throat. The U-tube contains a liquid of density {rho_m} kg/m³, the rest of the tubing is "
              "filled with the flowing liquid, and the liquid levels in the two arms of the U-tube differ by {dh} cm. The liquid is "
              "incompressible and frictionless and its speed is uniform across each section. Take g = {g} m/s².",
              "What is the volume flow rate through the pipe?", "volume flow rate through the pipe", "L/s",
              "A separate pump B in another building delivers {v} {u}, but it is unrelated to this pipe.",
              "A reference pipe B carries a flow of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the flow.", "W", equivalent="m^3/s"),
        ("dh", 1.5), _solve_venturi, 6,
        "the manometer reading as a hydrostatic integral, then the speed as the root of the Bernoulli pressure balance with the speed in the throat from the equal-flux condition",
        solver_rel_tol=1e-9,
        instances=({"d1": 10.0, "d2": 5.0, "rho": 1000.0, "rho_m": 13600.0, "g": 9.8, "dh": 12.0},
                   {"d1": 12.0, "d2": 6.0, "rho": 1000.0, "rho_m": 13600.0, "g": 9.8, "dh": 8.0},
                   {"d1": 8.0, "d2": 4.0, "rho": 900.0, "rho_m": 13500.0, "g": 9.8, "dh": 15.0},
                   {"d1": 14.0, "d2": 5.0, "rho": 1000.0, "rho_m": 13600.0, "g": 9.8, "dh": 6.0}))


def s92_cube_held_under_liquid() -> Structure:
    return Structure(
        "S92", "String tension holding a cube under a liquid", "fluids", "submerged_cube_string_tension",
        (_in("a", "length", "cm", "side of the cube", 10.0, (5.0, 20.0)),
         _in("rho_s", "density", "kg/m^3", "density of the cube", 600.0, (300.0, 800.0)),
         _in("rho_l", "density", "kg/m^3", "density of the liquid", 1000.0, (900.0, 1300.0)),
         _g(),
         _co("V", "volume", "cm^3", "volume of the cube", "a**3"),
         _co("m", "mass", "kg", "mass of the cube", "rho_s*V"),
         _co("Fb", "force", "N", "buoyant force on the cube", "rho_l*g*V"),
         _co("T", "force", "N", "tension in the string", "Fb - m*g")),
        "T",
        (A_G,
         Assumption("A-static", "The cube is at rest and completely under the surface, and the string is light, vertical and taut.",
                    "boundary_condition", ("a", "rho_s")),
         Assumption("A-liquid", "The liquid is incompressible and of uniform density.", "modelling", ("rho_l",))),
        _spec("A uniform cube of side {a} cm and density {rho_s} kg/m³ is held at rest completely under the surface of a liquid of "
              "density {rho_l} kg/m³ by a light vertical string that is tied to the bottom of the tank. Take g = {g} m/s².",
              "What is the tension in the string?", "tension in the string", "N",
              "A separate cube B in another tank hangs from a string with a tension of {v} {u}, but it is unrelated to this cube.",
              "A reference string B has a tension of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the holding.", "W", equivalent="mN"),
        ("rho_l", 1.25), _solve_submerged_tension, 4,
        "the net vertical pressure force on the top and bottom faces of the cube at an arbitrary depth, then the vertical force balance for the tension",
        solver_rel_tol=1e-9,
        instances=({"a": 10.0, "rho_s": 600.0, "rho_l": 1000.0, "g": 9.8},
                   {"a": 15.0, "rho_s": 450.0, "rho_l": 1100.0, "g": 9.8},
                   {"a": 8.0, "rho_s": 700.0, "rho_l": 1200.0, "g": 9.8},
                   {"a": 12.0, "rho_s": 500.0, "rho_l": 900.0, "g": 9.8}))


def s93_tank_drain_time() -> Structure:
    return Structure(
        "S93", "Time for a tank to drain through a hole in its bottom", "fluids", "torricelli_tank_drain_time",
        (_in("D", "length", "cm", "inner diameter of the tank", 40.0, (30.0, 80.0)),
         _in("d", "length", "mm", "diameter of the hole in the bottom", 10.0, (5.0, 20.0)),
         _in("h0", "length", "m", "initial height of the water above the hole", 0.8, (0.6, 1.5)),
         _in("h1", "length", "m", "final height of the water above the hole", 0.2, (0.1, 0.5)),
         _g(),
         _co("A", "area", "m^2", "cross-section area of the tank", "pi*D**2/4"),
         _co("a", "area", "mm^2", "area of the hole", "pi*d**2/4"),
         _co("t", "time", "s", "time for the level to fall from the initial to the final height",
             "(A/a)*sqrt(2/g)*(sqrt(h0) - sqrt(h1))")),
        "t",
        (A_G,
         Assumption("A-torricelli", "The water is ideal and the hole is so small that the speed of the surface is negligible compared with the speed of the outflow; the jet area equals the hole area.",
                    "modelling", ("D", "d")),
         Assumption("A-open", "The top of the tank and the jet are both at atmospheric pressure, and the flow is quasi-steady at every instant.",
                    "boundary_condition", ("h0", "h1"))),
        _spec("A cylindrical open tank of inner diameter {D} cm stands upright and contains water. A small circular hole of diameter "
              "{d} mm is opened in the middle of the bottom of the tank and the water drains out through it. Treat the water as ideal, "
              "with the speed of the surface negligible compared with the speed of the outflow, and take the area of the jet equal to "
              "the area of the hole. Take g = {g} m/s².",
              "How long does the water level take to fall from a height of {h0} m to a height of {h1} m above the hole?",
              "time for the level to fall", "s",
              "A separate tank B in another laboratory needs {v} {u} to empty, but it is unrelated to this tank.",
              "A reference tank B takes {v} {u} for the same fall.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the draining.", "W", equivalent="min"),
        ("h0", 1.5), _solve_drain_time, 5,
        "the level equation A dh/dt = -a sqrt(2 g h) integrated as an ODE from the initial height until an event at the final height",
        solver_rel_tol=1e-7,
        instances=({"D": 40.0, "d": 10.0, "h0": 0.8, "h1": 0.2, "g": 9.8},
                   {"D": 50.0, "d": 12.0, "h0": 1.0, "h1": 0.25, "g": 9.8},
                   {"D": 30.0, "d": 8.0, "h0": 0.9, "h1": 0.3, "g": 9.8},
                   {"D": 60.0, "d": 15.0, "h0": 1.2, "h1": 0.4, "g": 9.8}))


def s94_poiseuille_pump_power() -> Structure:
    return Structure(
        "S94", "Pump power for laminar flow of a viscous liquid in a pipe", "fluids", "poiseuille_pumping_power",
        (_in("d", "length", "mm", "inner diameter of the pipe", 4.0, (2.0, 6.0)),
         _in("L", "length", "m", "length of the pipe", 2.0, (0.5, 5.0)),
         _in("eta", "viscosity", "Pa*s", "dynamic viscosity of the liquid", 0.004, (0.003, 0.02)),
         _in("v", "speed", "cm/s", "average speed of the liquid in the pipe", 20.0, (5.0, 30.0)),
         _co("Q", "volume_flow_rate", "m^3/s", "volume flow rate", "pi*d**2*v/4"),
         _co("dp", "pressure", "kPa", "pressure drop along the pipe", "128*eta*L*Q/(pi*d**4)"),
         _co("P", "power", "mW", "power needed to drive the flow", "dp*Q")),
        "P",
        (Assumption("A-laminar", "The flow is steady, laminar and fully developed, the liquid is Newtonian and incompressible, and entrance effects are neglected.",
                    "modelling", ("eta", "d")),
         Assumption("A-horizontal", "The pipe is straight and horizontal, so the pressure drop only drives the viscous flow.",
                    "boundary_condition", ("L",))),
        _spec("A viscous liquid of dynamic viscosity {eta} Pa·s flows through a straight horizontal circular pipe of inner diameter "
              "{d} mm and length {L} m. The flow is steady, laminar and fully developed, and the average speed of the liquid over "
              "the cross-section is {v} cm/s. Neglect entrance effects.",
              "What power is needed to drive the flow through the pipe, that is, the pressure drop along the pipe times the volume flow rate?",
              "power needed to drive the flow", "mW",
              "A separate heater B in another room dissipates {v} {u}, but it is unrelated to this pipe.",
              "A reference pump B delivers {v} {u}.",
              "A separate sensor B reads {v} {u}, but it plays no part in the flow.", "Hz", equivalent="W"),
        ("v", 1.5), _solve_pipe_power, 4,
        "the pressure gradient as the root that makes the integrated parabolic velocity profile carry the given flow, then power as the pressure drop times the flow",
        solver_rel_tol=1e-9,
        instances=({"d": 4.0, "L": 2.0, "eta": 0.004, "v": 20.0},
                   {"d": 3.0, "L": 1.5, "eta": 0.005, "v": 10.0},
                   {"d": 5.0, "L": 3.0, "eta": 0.01, "v": 25.0},
                   {"d": 2.5, "L": 0.8, "eta": 0.006, "v": 15.0}))


def s95_hydraulic_lift_force() -> Structure:
    return Structure(
        "S95", "Force needed on the small piston of a hydraulic lift", "fluids", "hydraulic_lift_height_offset_force",
        (_in("m", "mass", "kg", "mass of the load on the large piston", 1200.0, (500.0, 2500.0)),
         _in("A2", "area", "cm^2", "area of the large piston", 800.0, (400.0, 1500.0)),
         _in("A1", "area", "cm^2", "area of the small piston", 20.0, (10.0, 50.0)),
         _in("rho", "density", "kg/m^3", "density of the oil", 850.0, (750.0, 950.0)),
         _g(),
         _in("h", "length", "m", "height of the large piston face above the small piston face", 1.5, (0.3, 2.5)),
         _co("pL", "pressure", "kPa", "gauge pressure of the oil at the large piston", "m*g/A2"),
         _co("pS", "pressure", "kPa", "gauge pressure of the oil at the small piston", "pL + rho*g*h"),
         _co("F", "force", "N", "force on the small piston", "pS*A1")),
        "F",
        (A_G,
         Assumption("A-static", "The oil is incompressible, of uniform density and at rest, and the pistons are in equilibrium.",
                    "modelling", ("rho",)),
         Assumption("A-ideal", "The pistons are light and move without friction; the atmosphere acts on the outer face of each piston, so only gauge pressures matter.",
                    "boundary_condition", ("m", "A2", "A1", "h"))),
        _spec("A hydraulic lift is filled with oil of density {rho} kg/m³. A load of mass {m} kg rests on the large piston, which has "
              "an area of {A2} cm². A force is applied to the small piston, which has an area of {A1} cm². The face of the large "
              "piston is {h} m above the face of the small piston. The pistons are light, move without friction and are in "
              "equilibrium, and the atmosphere acts on the outer face of each piston. Take g = {g} m/s².",
              "What force must be applied to the small piston?", "force on the small piston", "N",
              "A separate jack B in another garage is pushed with a force of {v} {u}, but it is unrelated to this lift.",
              "A reference lift B needs a force of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the lifting.", "W", equivalent="kN"),
        ("m", 1.25), _solve_hydraulic_force, 6,
        "the gauge pressures as the unknowns of a 3x3 linear system: load equilibrium, the hydrostatic step between the piston faces, and the force from the pressure at the small piston",
        solver_rel_tol=1e-9,
        instances=({"m": 1200.0, "A2": 800.0, "A1": 20.0, "rho": 850.0, "g": 9.8, "h": 1.5},
                   {"m": 1500.0, "A2": 1000.0, "A1": 25.0, "rho": 800.0, "g": 9.8, "h": 1.0},
                   {"m": 900.0, "A2": 600.0, "A1": 15.0, "rho": 900.0, "g": 9.8, "h": 2.0},
                   {"m": 2000.0, "A2": 1200.0, "A1": 40.0, "rho": 870.0, "g": 9.8, "h": 0.5}))


ALL = (s91_venturi_flow_rate, s92_cube_held_under_liquid, s93_tank_drain_time, s94_poiseuille_pump_power, s95_hydraulic_lift_force)


def all_structures() -> list[Structure]:
    return [factory() for factory in ALL]


# --- gold solution plans -----------------------------------------------------------------------------

PLANS: dict[str, Plan] = {
    "S27": Plan(
        approach="We want the absolute pressure at a given depth in a liquid at rest. The pressure at the free surface is known, and the "
                 "pressure grows with depth because of the weight of the liquid above, so we add that increase to the surface value.",
        steps=(
            Step("p",
                 "Hydrostatic pressure law: in a liquid at rest with uniform density the pressure increases linearly with depth, "
                 "p = p0 + rho g h",
                 "The liquid is at rest and its density is uniform, so the extra pressure at depth h is the weight of a column of "
                 "liquid of unit cross-section and height h, rho g h; adding the pressure p0 at the free surface gives the absolute "
                 "pressure at that depth."),
        ),
        check="Limiting case: at zero depth the formula returns the surface pressure. The units are consistent, since kg/m^3 times m/s^2 "
              "times m is Pa. For water a depth of about ten metres adds roughly one atmosphere, which matches the familiar rule of thumb."),
    "S91": Plan(
        approach="The Venturi meter converts a flow rate into a pressure difference between the wide section and the throat, and the "
                 "U-tube measures that difference. Work backwards: first get the pressure difference from the manometer reading, then "
                 "use continuity and Bernoulli's equation to find the speed in the wide section, then multiply by the area for the flow rate.",
        steps=(
            Step("dp",
                 "Hydrostatic pressure law applied to the U-tube: the pressure difference between two tappings equals the weight per "
                 "unit area of the excess column of denser liquid, p1 - p2 = (rho_m - rho) g dh",
                 "The leads of the manometer are filled with the flowing liquid, so the U-tube measures the difference of p + rho g z "
                 "between the two tappings. The pipe axis is horizontal, so this is the pressure difference p1 - p2 that enters "
                 "Bernoulli's equation. In the manometer the column of U-tube liquid of height dh replaces an equal column of the "
                 "flowing liquid, so the pressure difference is the difference in their weights per area. This gives the pressure "
                 "drop without knowing either pressure."),
            Step("v1",
                 "Continuity equation A1 v1 = A2 v2 together with Bernoulli's equation for ideal flow at constant height, "
                 "p1 + (1/2) rho v1^2 = p2 + (1/2) rho v2^2, with the areas proportional to the squared diameters",
                 "The liquid is incompressible and frictionless, so the same flow passes both sections and it speeds up in the "
                 "throat to v2 = v1 (d1/d2)^2. The pressure drop is exactly what supplies the extra kinetic energy, "
                 "dp = (1/2) rho v1^2 ((d1/d2)^4 - 1). Solving this for v1 turns the measured pressure drop into the speed in the "
                 "wide section."),
            Step("Q",
                 "Definition of the volume flow rate for a uniform speed: Q = A v, with the circular area A = pi d^2 / 4",
                 "With a uniform speed across the section, the volume that passes the wide section per second is its area times the "
                 "speed. By continuity the same flow passes the throat, so this is the flow rate through the pipe, which is what the "
                 "question asks."),
        ),
        check="Dimensional check: sqrt(Pa / (kg/m^3)) is a speed in m/s and area times speed is m^3/s. Limiting case: a zero "
              "reading means no flow, and for a given flow the reading grows as the throat is made narrower, so for a given reading "
              "a narrower throat means a smaller flow. Order of magnitude: about 1 "
              "m/s in a pipe of ten centimetres diameter is about ten litres per second, as obtained."),
    "S92": Plan(
        approach="The cube is at rest, so the forces on it balance: the buoyant force of the liquid pushes up, while its weight and the "
                 "string tension pull down. Find the volume of the cube, then the buoyant force and the mass of the cube, and finally solve "
                 "the force balance for the tension.",
        steps=(
            Step("V",
                 "Volume of a cube, V = a^3",
                 "The cube is completely under the surface, so it displaces exactly its own volume of liquid. Both its weight and the "
                 "buoyant force are proportional to this volume, so we need it first."),
            Step("Fb",
                 "Archimedes' principle: the buoyant force equals the weight of the displaced liquid, Fb = rho_l g V",
                 "The cube is fully submerged, so the displaced liquid has the volume of the cube and the density of the liquid. "
                 "This is the upward force the liquid exerts on the cube; it needs the volume but not the mass."),
            Step("m",
                 "Definition of density, rho = m / V, so m = rho_s V",
                 "The weight of the cube is its mass times g, and the problem gives its density instead of its mass; the density "
                 "times the volume gives the mass."),
            Step("T",
                 "Newton's first law for a body in equilibrium: the net vertical force is zero, Fb = m g + T",
                 "The cube is at rest, and the string is tied to the bottom of the tank, so it pulls the cube down along with its "
                 "weight. The upward buoyant force must balance both, so the tension is the buoyant force minus the weight."),
        ),
        check="Limiting case: if the density of the cube equalled that of the liquid, the buoyant force would equal the weight and "
              "the tension would be zero; the tension is positive only when the cube is less dense than the liquid, as it must be "
              "for a cube that needs to be held down. The result scales with the cube volume and with the density difference."),
    "S93": Plan(
        approach="The level falls because water leaves through the hole, so mass conservation links the rate of fall of the level to the "
                 "outflow speed, and Torricelli's law gives that speed as a function of the present height. Since the speed changes "
                 "as the level falls, the separable equation must be integrated between the two heights.",
        steps=(
            Step("A",
                 "Area of a circle, A = pi D^2 / 4",
                 "The cross-section area of the tank decides how much the level drops for a given volume that leaves, so it enters "
                 "the level equation as the area ratio of tank to hole."),
            Step("a",
                 "Area of a circle, a = pi d^2 / 4",
                 "The area of the hole, which equals the area of the jet by assumption, fixes the volume flow out of the tank for a "
                 "given outflow speed."),
            Step("t",
                 "Torricelli's law v = sqrt(2 g h), from Bernoulli's equation between the free surface and the jet, together with "
                 "conservation of volume, A dh/dt = - a sqrt(2 g h); integrating gives t = (A/a) sqrt(2/g) (sqrt(h0) - sqrt(h1))",
                 "The outflow speed depends on the current height of the water above the hole, so the level does not fall at a "
                 "constant rate. Separating the variables gives the integral of dh / sqrt(h) between the initial and the final "
                 "height, which is 2 (sqrt(h0) - sqrt(h1)); this is the time asked for."),
        ),
        check="Bounds: the outflow speed lies between sqrt(2 g h1) and sqrt(2 g h0) during the fall, so the time must lie between "
              "A (h0 - h1) / (a sqrt(2 g h0)) and A (h0 - h1) / (a sqrt(2 g h1)). Limiting case: draining all the way (h1 = 0) takes "
              "twice the time that the initial outflow rate would need to empty the same volume. Narrower holes take longer."),
    "S94": Plan(
        approach="The pump power is the pressure drop along the pipe times the volume flow rate. The flow rate follows from the average "
                 "speed and the area, and the pressure drop needed to drive that flow of a viscous liquid through the pipe follows "
                 "from the Hagen-Poiseuille law; then multiply the two.",
        steps=(
            Step("Q",
                 "Definition of the volume flow rate in terms of the average speed, Q = A v, with the circular area A = pi d^2 / 4",
                 "The Poiseuille law is written for the volume flow rate, but the problem gives the average speed over the "
                 "cross-section, so the flow rate is the area of the cross-section times that average speed."),
            Step("dp",
                 "Hagen-Poiseuille law for steady laminar flow of a Newtonian liquid in a circular pipe, Q = pi R^4 dp / (8 eta L), "
                 "that is dp = 8 eta L Q / (pi R^4) = 128 eta L Q / (pi d^4)",
                 "In laminar flow the viscous shear stress balances the pressure force, which gives a parabolic velocity profile "
                 "and a flow rate proportional to the pressure drop and to the fourth power of the radius. Inverting the law gives "
                 "the pressure drop that drives the given flow rate through the stated length."),
            Step("P",
                 "Power as the rate of work done by the pressure force, P = dp Q",
                 "The pump does work dp on every unit volume of liquid that it pushes through the pipe, so the power is the pressure "
                 "drop times the volume per second. In steady flow this equals the rate at which viscous friction dissipates energy."),
        ),
        check="Dimensional check: Pa s times m times m^3/s divided by m^4 is Pa, and Pa times m^3/s is W. Scaling: at a fixed flow rate "
              "the pressure drop goes as 1/d^4, so halving the diameter multiplies it by sixteen; at a fixed pipe the pressure drop "
              "is proportional to the speed, so doubling the speed makes the power four times larger."),
    "S95": Plan(
        approach="Use the weight of the load to find the gauge pressure of the oil at the large piston, step down to the small piston "
                 "through the hydrostatic pressure change between the two piston faces, and multiply the pressure there by the area "
                 "of the small piston.",
        steps=(
            Step("pL",
                 "Definition of pressure, p = F / A, with Newton's first law for the load: the oil force on the large piston "
                 "balances the weight, so the gauge pressure is m g / A2",
                 "The atmosphere pushes on the outer face of each piston, so only the excess (gauge) pressure of the oil "
                 "has to carry the load. The piston is light and at rest, so the oil pressure times "
                 "its area equals the weight of the load."),
            Step("pS",
                 "Hydrostatic pressure law for a liquid at rest: the pressure is larger by rho g h at a point lower by h, "
                 "pS = pL + rho g h",
                 "The oil is at rest and connected from the large piston face to the small piston face, but the small piston is "
                 "lower by h. The pressures at the two faces are therefore not equal, as they would be at equal heights; the "
                 "pressure at the small piston is larger by the weight per area of an oil column of height h."),
            Step("F",
                 "Newton's first law for the light small piston together with the definition of pressure: the oil pushes up on the "
                 "small piston with the gauge pressure at its face times A1, and the applied force balances this once the atmosphere "
                 "on both sides cancels, F = pS A1",
                 "The small piston is in equilibrium, so the force that has to be applied on it equals the gauge pressure of the oil "
                 "at its face times its area; this is the force asked for. The pressure at this face is pS from the hydrostatic step, "
                 "not pL."),
        ),
        check="Limiting case: for equal heights (h = 0) the result reduces to the ideal hydraulic-lift force m g (A1 / A2), the usual "
              "force multiplication by the area ratio; here the result is slightly larger because the oil column of height h must "
              "also be supported. A small piston with a small area needs a force much smaller than the weight of the load."),
}

LEVELS: dict[str, str] = {
    "S27": "high_school",
    "S91": "intro_university",
    "S92": "high_school",
    "S93": "intro_university",
    "S94": "upper_university",
    "S95": "high_school",
}

TOPICS: dict[str, str] = {
    "S27": "pressure at depth in a liquid",
    "S91": "continuity, Bernoulli and a manometer in a Venturi meter",
    "S92": "Archimedes' principle and a submerged body held by a string",
    "S93": "Torricelli's law and the draining time of a tank",
    "S94": "Poiseuille flow and the pumping power",
    "S95": "hydraulic lift with a height offset between the pistons",
}
