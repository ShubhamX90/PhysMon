"""M250 phase 3, fluids batch: ten new DECOY-v2 structures S311 to S320 (hydrostatics, Torricelli flow, viscous and turbulent pipe flow,
Stokes settling in a centrifuge, layered liquids, capillarity, cavitation, quadratic drag, a side jet), with gold solution plans.

Written for the M250 exploration pool (plan of record v2.2). Same pattern as `lib_m250_extra.py`: a typed graph of input and computed
nodes, an independently coded numeric solver (quadrature of a pressure moment, a linear system, an ODE with an event, a root finder
on a force balance), four numeric instantiations and a relevant edit that moves the answer. Every stated physical constant is an input
node with provenance "assumed". Every answer-deciding condition (initial state, governing model, boundary condition) is stated in the
base context; the role quantities of the v2.1 specs are in `roles_m250p3_fluids.py`. No numeral appears in a context except as an input
node (laws with fractional powers are written in words).

Level: S311 to S315 upper-university; S316 to S320 introductory. Relations (computed nodes): S311 3, S312 3, S313 3, S314 3, S315 3,
S316 3, S317 3, S318 3, S319 4, S320 3.

Admission status: agent-authored and machine-certified only. No human physicist and no LLM panel has reviewed these problems or plans.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import quad, solve_ivp
from scipy.optimize import brentq

from physmon.benchmark.v2.graph import Assumption, Structure
from physmon.benchmark.v2.library import _co, _in, _spec
from physmon.benchmark.v2.trace import Plan, Step


def _g9() -> object:
    return _in("g", "acceleration", "m/s^2", "gravitational acceleration, a stated constant", 9.81, (9.7, 9.9), provenance="assumed")


A_G = Assumption("A-g", "g is a uniform constant of the stated value.", "modelling", ("g",))

# --- solvers (independent routes; SI inputs in node order) -----------------------------------------


def _solve_gate_force(h, w, d, rho, g):
    # The torque of the water pressure about the hinge as a quadrature of (pressure x width x lever arm) down the gate, then the
    # horizontal force at the lower edge from the balance of torques about the hinge.
    torque, _ = quad(lambda s: rho * g * (d + s) * w * s, 0.0, h, epsabs=0.0, epsrel=1e-13)
    return float(torque / h)


def _solve_bowl_drain(radius, h0, d, g):
    # The draining time as the quadrature of dt = A(h) dh / (a sqrt(2 g h)) over the depth, with the surface area A(h) = pi (2 R h - h^2)
    # of a hemispherical bowl.
    hole = math.pi * d * d / 4.0
    seconds, _ = quad(lambda h: math.pi * (2.0 * radius * h - h * h) / (hole * math.sqrt(2.0 * g * h)), 0.0, h0, epsabs=0.0,
                      epsrel=1e-13)
    return float(seconds)


def _solve_tube_junction(p, l1, r1, l2, r2):
    # Pressure at the joint from the continuity of the flow through two Poiseuille resistances in series, as a linear system in
    # (flow rate, junction pressure): p - pj = R1 Q and pj = R2 Q with R = 8 eta L / (pi r^4), for a reference viscosity (it cancels).
    eta = 0.05
    res1 = 8.0 * eta * l1 / (math.pi * r1 ** 4)
    res2 = 8.0 * eta * l2 / (math.pi * r2 ** 4)
    matrix = np.array([[res1, 1.0], [res2, -1.0]])
    rhs = np.array([p, 0.0])
    return float(np.linalg.solve(matrix, rhs)[1])


def _solve_blasius_drop(d, length, v, rho, eta, cf):
    # The wall shear stress tau = f rho v^2 / 8 with f from the Blasius law, then the force balance on the water in the length of pipe:
    # dp (pi d^2 / 4) = tau (pi d length).
    reynolds = rho * v * d / eta
    friction = cf * reynolds ** (-0.25)
    tau = friction * rho * v * v / 8.0
    return float(tau * math.pi * d * length / (math.pi * d * d / 4.0))


def _solve_settling_time(r, rho_s, rho_f, eta, omega, x1, x2):
    # The radial position of a particle integrated as an ODE, dx/dt = (2 r^2 (rho_s - rho_f) / (9 eta)) omega^2 x (Stokes drag balancing the
    # centrifugal force less the buoyancy), until an event at the bottom of the tube.
    rate = 2.0 * r * r * (rho_s - rho_f) * omega * omega / (9.0 * eta)

    def bottom(t, y):
        return y[0] - x2

    bottom.terminal = True
    solution = solve_ivp(lambda t, y: [rate * y[0]], (0.0, 60.0 * math.log(x2 / x1 + 1.0) / rate + 60.0 / rate), [x1],
                         events=bottom, rtol=1e-12, atol=1e-16)
    return float(solution.t_events[0][0])


def _solve_interface_depth(a, rho_c, m_load, rho_o, rho_w, g):
    # Equilibrium of the cube as the root of the net vertical force from the pressures on its top and bottom faces, with the lower
    # part (depth x) in the water and the rest in the oil, found with a bracketing root finder.
    weight = (rho_c * a ** 3 + m_load) * g

    def net(x):
        return rho_o * g * (a - x) * a * a + rho_w * g * x * a * a - weight

    return float(brentq(net, -1.0e6 * a, 1.0e6 * a, xtol=1e-15, rtol=1e-14))


def _solve_capillary_mass(r, gamma, theta, rho, g):
    # The rise from the balance of the Laplace pressure drop 2 gamma cos(theta) / r across the meniscus against the hydrostatic pressure of
    # the raised column (root finder), then the mass of the cylinder of water of that height.
    laplace = 2.0 * gamma * math.cos(theta) / r
    height = brentq(lambda h: rho * g * h - laplace, -1.0e6, 1.0e6, xtol=1e-15, rtol=1e-14)
    return float(rho * math.pi * r * r * height)


def _solve_throat_pressure(p1, flow, d1, d2, rho):
    # Continuity for the two speeds, then the pressure in the throat as the root of the Bernoulli balance between the two sections.
    v1, v2 = flow / (math.pi * d1 * d1 / 4.0), flow / (math.pi * d2 * d2 / 4.0)

    def imbalance(p2):
        return (p1 + 0.5 * rho * v1 * v1) - (p2 + 0.5 * rho * v2 * v2)

    return float(brentq(imbalance, -1.0e10, 1.0e10, xtol=1e-9, rtol=1e-15))


def _solve_hail_speed(r, rho_s, rho_a, cd, g):
    # The terminal speed as the positive root of the force balance weight = quadratic drag.
    mass = rho_s * 4.0 * math.pi * r ** 3 / 3.0
    area = math.pi * r * r
    return float(brentq(lambda v: mass * g - 0.5 * cd * rho_a * area * v * v, 0.0, 1.0e4, xtol=1e-13, rtol=1e-15))


def _solve_jet_range(depth, height, g):
    # Bernoulli between the free surface and the jet, both at atmospheric pressure, gives the exit speed from the gauge pressure at the hole
    # (a reference density that cancels); the jet is then a projectile launched horizontally, integrated as an ODE until an event at the ground.
    rho = 1000.0
    speed = math.sqrt(2.0 * rho * g * depth / rho)

    def ground(t, y):
        return y[1]

    ground.terminal = True
    solution = solve_ivp(lambda t, y: [speed, y[2], -g], (0.0, 100.0), [0.0, height, 0.0], events=ground, rtol=1e-12, atol=1e-14)
    return float(solution.y_events[0][0][0])


# --- structures ---------------------------------------------------------------------------------------


def s311_hinged_gate_force() -> Structure:
    return Structure(
        "S311", "Force at the foot of a hinged gate that holds back water", "fluids", "hydrostatic_torque_hinged_rectangular_gate_foot_force",
        (_in("H", "length", "m", "height of the gate", 1.5, (1.0, 3.0)),
         _in("w", "length", "m", "width of the gate", 2.0, (1.0, 4.0)),
         _in("d", "length", "m", "initial height of the water level above the hinge", 1.2, (0.5, 3.0)),
         _in("rho", "density", "kg/m^3", "density of the water", 1000.0, (990.0, 1040.0)),
         _g9(),
         _co("Fr", "force", "kN", "resultant force of the water on the gate", "rho*g*w*H*(d + H/2)"),
         _co("zc", "length", "m", "distance of the line of action of the resultant force below the hinge",
             "(d*H**2/2 + H**3/3)/(H*(d + H/2))"),
         _co("Fh", "force", "kN", "horizontal force at the bottom edge of the gate", "Fr*zc/H")),
        "Fh",
        (A_G,
         Assumption("A-water", "The water is at rest and incompressible and of uniform density, so that its pressure increases linearly with depth; the air on both sides of the gate is at the same pressure.",
                    "modelling", ("rho",)),
         Assumption("A-gate", "The gate is rigid and in equilibrium, its weight and the friction at the hinge are neglected, and the holding force is horizontal and acts at the bottom edge.",
                    "boundary_condition", ("H", "w", "d"))),
        _spec("A vertical rectangular gate of height {H} m and width {w} m closes an outlet of a reservoir and is hinged along its top "
              "edge. The reservoir holds water of density {rho} kg/m³, with the water level {d} m above the hinge, and the "
              "other side of the gate is dry. The water is at rest, and the air on both sides of the gate is at the same atmospheric "
              "pressure. A horizontal force applied at the bottom edge of the gate holds it shut. The gate is rigid, and its weight "
              "and the friction at the hinge are neglected. Take g = {g} m/s².",
              "What horizontal force must be applied at the bottom edge of the gate?", "horizontal force at the bottom edge of the gate",
              "kN",
              "A separate gate B in another dam is held shut by a force of {v} {u}, but it is unrelated to this gate.",
              "A reference gate B needs a holding force of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the holding.", "W", equivalent="N"),
        ("d", 1.5), _solve_gate_force, 5,
        "the torque of the water pressure about the hinge as a quadrature of pressure times width times lever arm down the gate, then the torque balance for the force at the bottom edge",
        solver_rel_tol=1e-9,
        instances=({"H": 1.5, "w": 2.0, "d": 1.2, "rho": 1000.0, "g": 9.81},
                   {"H": 2.0, "w": 1.5, "d": 0.8, "rho": 1000.0, "g": 9.81},
                   {"H": 1.2, "w": 3.0, "d": 2.0, "rho": 1025.0, "g": 9.8},
                   {"H": 1.8, "w": 2.5, "d": 0.6, "rho": 998.0, "g": 9.81}))


def s312_hemispherical_bowl_drain() -> Structure:
    return Structure(
        "S312", "Time for a hemispherical bowl to drain through a hole in its lowest point", "fluids",
        "torricelli_drain_time_hemispherical_bowl",
        (_in("R", "length", "cm", "inner radius of the bowl", 30.0, (20.0, 50.0)),
         _in("h0", "length", "cm", "initial depth of the water in the bowl", 15.0, (10.0, 30.0)),
         _in("d", "length", "mm", "diameter of the hole", 8.0, (5.0, 12.0)),
         _g9(),
         _co("a", "area", "mm^2", "area of the hole", "pi*d**2/4"),
         _co("Ae", "area", "cm^2", "effective area of the water surface, the surface area weighted by the inverse square root of the depth and averaged over the depth",
             "pi*h0*(2*R/3 - h0/5)"),
         _co("t", "time", "min", "time for the bowl to empty", "Ae/a*sqrt(2*h0/g)")),
        "t",
        (A_G,
         Assumption("A-torricelli", "The water is ideal and incompressible, the speed of its surface is negligible compared with the speed of the outflow, and the area of the jet equals the area of the hole.",
                    "modelling", ("R", "d")),
         Assumption("A-bowl", "The bowl is a hollow hemisphere held with its rim horizontal and open to the air, the hole is at its lowest point, and the flow is quasi-steady at every depth.",
                    "boundary_condition", ("h0",))),
        _spec("A hollow hemispherical bowl of inner radius {R} cm is held with its rim horizontal and open to the air. It "
              "holds water to a depth of {h0} cm, measured from the lowest point of the bowl. A small round hole of diameter {d} mm "
              "is then made at the lowest point of the bowl, and the water runs out through it. The water is ideal, the jet has the "
              "same area as the hole, and the speed of the water surface is negligible next to the speed of the jet. "
              "Take g = {g} m/s².",
              "How long does the bowl take to empty completely?", "time for the bowl to empty", "min",
              "A separate basin B in another laboratory empties in {v} {u}, but it is unrelated to this bowl.",
              "A reference bowl B empties in {v} {u}.",
              "A separate gauge B reads {v} {u}, but it plays no part in the draining.", "W", equivalent="s"),
        ("h0", 1.3), _solve_bowl_drain, 4,
        "the time as the quadrature of the surface area of the spherical cap times dh over the outflow rate at each depth, instead of the effective-area closed form",
        solver_rel_tol=1e-8,
        instances=({"R": 30.0, "h0": 15.0, "d": 8.0, "g": 9.81},
                   {"R": 25.0, "h0": 20.0, "d": 6.0, "g": 9.81},
                   {"R": 40.0, "h0": 25.0, "d": 10.0, "g": 9.8},
                   {"R": 35.0, "h0": 12.0, "d": 5.0, "g": 9.81}))


def s313_two_tubes_junction_pressure() -> Structure:
    return Structure(
        "S313", "Pressure at the joint between two tubes carrying a viscous liquid in series", "fluids",
        "poiseuille_resistances_in_series_junction_pressure",
        (_in("p", "pressure", "kPa", "gauge pressure of the oil at the inlet of the first tube", 60.0, (30.0, 120.0)),
         _in("L1", "length", "m", "length of the first tube", 1.2, (0.5, 2.0)),
         _in("r1", "length", "mm", "inner radius of the first tube", 3.0, (2.5, 4.0)),
         _in("L2", "length", "m", "length of the second tube", 0.8, (0.4, 1.5)),
         _in("r2", "length", "mm", "inner radius of the second tube", 2.0, (1.5, 3.0)),
         _co("ratio", "ratio", "1", "ratio of the flow resistance of the second tube to that of the first", "(L2/L1)*(r1/r2)**4"),
         _co("frac", "ratio", "1", "fraction of the inlet gauge pressure that remains at the joint", "ratio/(1 + ratio)"),
         _co("pj", "pressure", "kPa", "gauge pressure of the oil at the joint", "p*frac")),
        "pj",
        (Assumption("A-poiseuille", "The flow is steady, laminar and fully developed in both tubes, the oil is Newtonian and incompressible and has the same constant viscosity in both tubes, and entrance effects and the losses at the joint are neglected.",
                    "modelling", ("r1", "r2")),
         Assumption("A-horizontal", "Both tubes are straight and horizontal and are joined end to end with a common axis, and the oil leaves the second tube into the open air.",
                    "boundary_condition", ("p", "L1", "L2"))),
        _spec("A viscous oil is forced steadily through two straight horizontal circular tubes joined end to end, and its viscosity is the "
              "same in both tubes. The first tube has a length of {L1} m and an inner radius of {r1} mm, and the second tube has a "
              "length of {L2} m and an inner radius of {r2} mm. The gauge pressure of the oil at the inlet of the first tube is {p} kPa, "
              "and the oil leaves the second tube into the open air. The flow is steady, laminar and fully developed in both tubes, "
              "and entrance effects and the losses at the joint are neglected.",
              "What is the gauge pressure of the oil at the joint between the tubes?", "gauge pressure of the oil at the joint", "kPa",
              "A separate pipe B in another plant holds oil at a gauge pressure of {v} {u}, but it is unrelated to these tubes.",
              "A reference joint B stands at a gauge pressure of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the flow.", "W", equivalent="Pa"),
        ("L2", 1.5), _solve_tube_junction, 5,
        "the continuity of the flow through two Poiseuille resistances in series, written as a linear system in the flow rate and the junction pressure, instead of the pressure divider",
        solver_rel_tol=1e-9,
        instances=({"p": 60.0, "L1": 1.2, "r1": 3.0, "L2": 0.8, "r2": 2.0},
                   {"p": 45.0, "L1": 1.0, "r1": 2.5, "L2": 1.2, "r2": 2.0},
                   {"p": 80.0, "L1": 1.5, "r1": 3.5, "L2": 0.6, "r2": 2.5},
                   {"p": 50.0, "L1": 0.9, "r1": 3.0, "L2": 1.1, "r2": 1.8}))


def s314_turbulent_pipe_pressure_drop() -> Structure:
    return Structure(
        "S314", "Pressure drop of turbulent water flow along a smooth pipe", "fluids", "blasius_friction_turbulent_smooth_pipe_pressure_drop",
        (_in("D", "length", "cm", "inner diameter of the pipe", 5.0, (2.0, 10.0)),
         _in("L", "length", "m", "distance between the two pressure tappings", 40.0, (10.0, 100.0)),
         _in("v", "speed", "m/s", "mean speed of the water", 1.2, (0.5, 3.0)),
         _in("rho", "density", "kg/m^3", "density of the water", 998.0, (990.0, 1010.0)),
         _in("eta", "viscosity", "Pa*s", "viscosity of the water", 0.001, (0.0008, 0.0013)),
         _in("cf", "ratio", "1", "coefficient of the friction law, a stated constant", 0.316, (0.30, 0.33), provenance="assumed"),
         _co("Re", "reynolds_number", "1", "Reynolds number of the flow", "rho*v*D/eta"),
         _co("f", "ratio", "1", "friction factor of the pipe", "cf/sqrt(sqrt(Abs(Re)))"),
         _co("dp", "pressure", "kPa", "pressure drop between the tappings", "f*(L/D)*rho*v**2/2")),
        "dp",
        (Assumption("A-blasius", "The flow is steady, turbulent and fully developed in a hydraulically smooth pipe, and the friction factor follows the stated law, which is valid for the Reynolds numbers of this problem.",
                    "modelling", ("cf", "rho", "eta")),
         Assumption("A-pipe", "The pipe is straight and horizontal, so the pressure drop only overcomes the friction at the wall, and the water is incompressible and of uniform temperature.",
                    "boundary_condition", ("D", "L", "v"))),
        _spec("Water of density {rho} kg/m³ and viscosity {eta} Pa·s flows steadily at a mean speed of {v} m/s through a long, straight, "
              "smooth, horizontal circular pipe of inner diameter {D} cm. The flow is turbulent and fully developed. The pressure "
              "drop between two tappings in the wall of the pipe, {L} m apart, equals the friction factor times the ratio of that "
              "distance to the diameter of the pipe times the dynamic pressure of the flow, which is one half of the density times "
              "the square of the mean speed. The friction factor is {cf} divided by the fourth root of the Reynolds number, "
              "where the Reynolds number is the density times the mean speed times the diameter divided by the viscosity.",
              "What is the pressure drop between the two tappings?", "pressure drop between the two tappings", "kPa",
              "A separate pump B in another building raises the pressure by {v} {u}, but it is unrelated to this pipe.",
              "A reference pipe B shows a pressure drop of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the flow.", "W", equivalent="Pa"),
        ("L", 1.5), _solve_blasius_drop, 6,
        "the wall shear stress from the friction law and the force balance on the water between the tappings, instead of the Darcy form of the pressure drop",
        solver_rel_tol=1e-9,
        instances=({"D": 5.0, "L": 40.0, "v": 1.2, "rho": 998.0, "eta": 0.001, "cf": 0.316},
                   {"D": 3.0, "L": 25.0, "v": 2.0, "rho": 998.0, "eta": 0.00105, "cf": 0.316},
                   {"D": 8.0, "L": 60.0, "v": 0.9, "rho": 1000.0, "eta": 0.0011, "cf": 0.316},
                   {"D": 4.0, "L": 30.0, "v": 1.5, "rho": 997.0, "eta": 0.00095, "cf": 0.316}))


def s315_centrifuge_settling_time() -> Structure:
    return Structure(
        "S315", "Time for a particle to sediment along a spinning centrifuge tube", "fluids", "stokes_sedimentation_time_in_centrifuge_tube",
        (_in("r", "length", "μm", "radius of a particle", 0.4, (0.2, 1.0)),
         _in("rs", "density", "kg/m^3", "density of the particles", 1900.0, (1500.0, 2500.0)),
         _in("rf", "density", "kg/m^3", "density of the liquid", 1000.0, (990.0, 1100.0)),
         _in("eta", "viscosity", "Pa*s", "viscosity of the liquid", 0.001, (0.0008, 0.0013)),
         _in("n", "angular_speed", "rpm", "rotation rate of the rotor", 2000.0, (1000.0, 4000.0)),
         _in("x1", "length", "cm", "distance of the surface of the suspension from the axis", 8.0, (5.0, 9.0)),
         _in("x2", "length", "cm", "distance of the bottom of the tube from the axis", 14.0, (10.0, 18.0)),
         _co("S", "time", "ns", "sedimentation coefficient of a particle, its speed divided by the product of the squared angular speed and the distance from the axis",
             "2*r**2*(rs - rf)/(9*eta)"),
         _co("lr", "ratio", "1", "natural logarithm of the ratio of the final to the initial distance from the axis", "log(x2/x1)"),
         _co("t", "time", "min", "time for a particle to reach the bottom of the tube", "lr/(S*n**2)")),
        "t",
        (Assumption("A-stokes", "The particles are far apart, spherical and small enough that the drag on each is the Stokes drag, and the liquid is Newtonian and at rest in the rotating frame; the buoyancy of the liquid acts as in a gravitational field of strength equal to the centripetal acceleration.",
                    "modelling", ("r", "rs", "rf", "eta")),
         Assumption("A-spin", "The rotor has been spinning at its constant rate from the start, gravity is neglected, the tube lies along a radius, and the particle moves along the tube without touching its wall.",
                    "boundary_condition", ("n", "x1", "x2"))),
        _spec("A centrifuge tube lies along a radius of a rotor, with its closed bottom {x2} cm from the axis. The tube holds a dilute "
              "suspension of small spherical particles of radius {r} μm and density {rs} kg/m³ in a liquid of density {rf} kg/m³ "
              "and viscosity {eta} Pa·s, and the surface of the suspension is {x1} cm from the axis. The rotor spins in a "
              "horizontal plane at a constant {n} rpm from the start, and gravity is neglected. The particles are far apart, and the "
              "drag on each particle is the Stokes drag.",
              "How long does a particle that starts at the surface of the suspension take to reach the bottom of the tube?",
              "time for a particle to reach the bottom of the tube", "min",
              "A separate sample B in another centrifuge clears in {v} {u}, but it is unrelated to this tube.",
              "A reference particle B takes {v} {u} to settle.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the settling.", "W", equivalent="s"),
        ("n", 1.3), _solve_settling_time, 7,
        "the radial position integrated as an ODE with an event at the bottom of the tube, instead of the logarithm of the distance ratio over the sedimentation coefficient",
        solver_rel_tol=1e-8,
        instances=({"r": 0.4, "rs": 1900.0, "rf": 1000.0, "eta": 0.001, "n": 2000.0, "x1": 8.0, "x2": 14.0},
                   {"r": 0.5, "rs": 1800.0, "rf": 1000.0, "eta": 0.0011, "n": 1500.0, "x1": 7.0, "x2": 13.0},
                   {"r": 0.3, "rs": 2200.0, "rf": 1000.0, "eta": 0.001, "n": 3000.0, "x1": 6.5, "x2": 12.0},
                   {"r": 0.6, "rs": 1500.0, "rf": 1020.0, "eta": 0.0012, "n": 1200.0, "x1": 8.0, "x2": 15.0}))


def s316_cube_at_the_oil_water_interface() -> Structure:
    return Structure(
        "S316", "Depth of a loaded cube below the interface between oil and water", "fluids", "buoyancy_cube_straddling_two_liquid_layers",
        (_in("a", "length", "cm", "side of the cube", 10.0, (6.0, 15.0)),
         _in("rc", "density", "kg/m^3", "density of the cube", 880.0, (700.0, 950.0)),
         _in("m", "mass", "g", "mass of the lead weight on the cube", 30.0, (10.0, 80.0)),
         _in("ro", "density", "kg/m^3", "density of the oil", 800.0, (700.0, 850.0)),
         _in("rw", "density", "kg/m^3", "density of the water", 1000.0, (980.0, 1100.0)),
         _g9(),
         _co("W", "force", "N", "total weight of the cube and the lead weight", "(rc*a**3 + m)*g"),
         _co("Vw", "volume", "cm^3", "volume of the cube below the interface", "(W/g - ro*a**3)/(rw - ro)"),
         _co("x", "length", "cm", "depth of the bottom face of the cube below the interface", "Vw/a**2")),
        "x",
        (A_G,
         Assumption("A-float", "The cube floats freely and at rest with its axis vertical, clear of the walls and the bottom of the tank, with its lower part in the water and its upper part in the oil, and its top face under the surface of the oil.",
                    "boundary_condition", ("a", "rc", "m")),
         Assumption("A-liquids", "The two liquids are incompressible, do not mix and have uniform densities, the tank is wide, and surface tension is neglected.",
                    "modelling", ("ro", "rw"))),
        _spec("A wide tank holds a layer of oil of density {ro} kg/m³ that floats on water of density {rw} kg/m³, and the two liquids do "
              "not mix. A uniform cube of side {a} cm and density {rc} kg/m³ floats freely and at rest with its axis vertical, its "
              "lower part in the water and its upper part in the oil, so that its top face is under the surface of the oil. A small "
              "lead weight of mass {m} g and negligible volume is fixed to the middle of the top face of the cube. Take g = {g} m/s².",
              "How far below the interface between the oil and the water is the bottom face of the cube?",
              "depth of the bottom face of the cube below the interface", "cm",
              "A separate cube B in another tank sits {v} {u} below its interface, but it is unrelated to this cube.",
              "A reference cube B lies {v} {u} below its interface.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the floating.", "W", equivalent="mm"),
        ("m", 1.5), _solve_interface_depth, 6,
        "the vertical force balance from the pressures on the top and bottom faces of the cube, solved as the root of the net force on the cube, instead of the displaced-volume formula",
        solver_rel_tol=1e-9,
        instances=({"a": 10.0, "rc": 880.0, "m": 30.0, "ro": 800.0, "rw": 1000.0, "g": 9.81},
                   {"a": 12.0, "rc": 850.0, "m": 45.0, "ro": 780.0, "rw": 1020.0, "g": 9.81},
                   {"a": 8.0, "rc": 900.0, "m": 20.0, "ro": 820.0, "rw": 1000.0, "g": 9.8},
                   {"a": 15.0, "rc": 840.0, "m": 80.0, "ro": 760.0, "rw": 1050.0, "g": 9.81}))


def s317_capillary_column_mass() -> Structure:
    return Structure(
        "S317", "Mass of the water column held in a narrow glass tube by surface tension", "fluids", "jurin_capillary_rise_column_mass",
        (_in("r", "length", "mm", "inner radius of the tube", 0.6, (0.2, 1.5)),
         _in("gam", "surface_tension", "N/m", "surface tension of the water", 0.0728, (0.06, 0.08)),
         _in("th", "angle", "deg", "contact angle between the water and the glass", 20.0, (0.0, 60.0)),
         _in("rho", "density", "kg/m^3", "density of the water", 1000.0, (990.0, 1010.0)),
         _g9(),
         _co("h", "length", "mm", "height of the water in the tube above the level in the dish", "2*gam*cos(th)/(rho*g*r)"),
         _co("V", "volume", "cm^3", "volume of the water raised above the level in the dish", "pi*r**2*h"),
         _co("m", "mass", "g", "mass of the water raised above the level in the dish", "rho*V")),
        "m",
        (A_G,
         Assumption("A-meniscus", "The meniscus is part of a sphere, the volume of water in the meniscus is neglected so that the raised water is a cylinder of the radius of the tube, and the tube is narrow compared with the capillary length of the water.",
                    "modelling", ("r", "gam", "th")),
         Assumption("A-static", "The water in the tube is at rest, the dish is wide so that its level does not change, and the air above the water in the tube and in the dish is at the same pressure; the water is incompressible.",
                    "boundary_condition", ("rho",))),
        _spec("A clean vertical glass tube of inner radius {r} mm is dipped a short way into a wide dish of water. The water has a "
              "density of {rho} kg/m³ and a surface tension of {gam} N/m, and it meets the glass at a contact angle of {th} degrees. "
              "The meniscus in the tube is part of a sphere and its volume is neglected, the tube is narrow compared with the "
              "capillary length of the water, and the air above the water in the tube and in the dish is at the same pressure. The "
              "water is at rest. Take g = {g} m/s².",
              "What is the mass of the water in the tube that stands above the level of the water in the dish?",
              "mass of the water above the level in the dish", "g",
              "A separate burette B in another laboratory holds {v} {u} of water, but it is unrelated to this tube.",
              "A reference tube B holds {v} {u} of water above the level in its dish.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the capillary rise.", "W", equivalent="kg"),
        ("r", 1.5), _solve_capillary_mass, 5,
        "the balance of the Laplace pressure across the meniscus and the hydrostatic pressure of the column as a root find for the height, then the mass of the cylinder of water",
        solver_rel_tol=1e-9,
        instances=({"r": 0.6, "gam": 0.0728, "th": 20.0, "rho": 1000.0, "g": 9.81},
                   {"r": 0.4, "gam": 0.0725, "th": 15.0, "rho": 998.0, "g": 9.81},
                   {"r": 0.8, "gam": 0.073, "th": 25.0, "rho": 1000.0, "g": 9.8},
                   {"r": 0.5, "gam": 0.072, "th": 30.0, "rho": 997.0, "g": 9.81}))


def s318_throat_pressure_of_a_constriction() -> Structure:
    return Structure(
        "S318", "Absolute pressure of water in the throat of a pipe constriction", "fluids", "bernoulli_throat_pressure_cavitation_limit",
        (_in("p1", "pressure", "kPa", "absolute pressure of the water in the wide section", 300.0, (150.0, 500.0)),
         _in("Q", "volume_flow_rate", "L/s", "volume flow rate of the water", 12.0, (5.0, 25.0)),
         _in("d1", "length", "cm", "inner diameter of the wide section", 10.0, (8.0, 15.0)),
         _in("d2", "length", "cm", "inner diameter of the throat", 4.0, (3.0, 6.0)),
         _in("rho", "density", "kg/m^3", "density of the water", 998.0, (990.0, 1010.0)),
         _co("v1", "speed", "m/s", "speed of the water in the wide section", "4*Q/(pi*d1**2)"),
         _co("v2", "speed", "m/s", "speed of the water in the throat", "4*Q/(pi*d2**2)"),
         _co("p2", "pressure", "kPa", "absolute pressure of the water in the throat", "p1 - rho*(v2**2 - v1**2)/2")),
        "p2",
        (Assumption("A-bernoulli", "The water is incompressible, flows steadily and without friction along a horizontal pipe, its speed is uniform across each section, and it stays liquid throughout.",
                    "modelling", ("rho", "Q")),
         Assumption("A-sections", "The pipe narrows smoothly from the wide section to the throat, both sections are circular and horizontal at the same height, and the pressure in the wide section is held at the stated value.",
                    "boundary_condition", ("p1", "d1", "d2"))),
        _spec("Water of density {rho} kg/m³ is pumped steadily at a volume flow rate of {Q} L/s through a horizontal pipe that narrows "
              "smoothly from an inner diameter of {d1} cm to a throat of inner diameter {d2} cm. A pressure regulator keeps the "
              "absolute pressure of the water in the wide section at {p1} kPa. The water is incompressible and flows without friction, "
              "its speed is uniform across each section, and it stays liquid throughout.",
              "What is the absolute pressure of the water in the throat?", "absolute pressure of the water in the throat", "kPa",
              "A separate boiler B in another plant holds steam at an absolute pressure of {v} {u}, but it is unrelated to this pipe.",
              "A reference throat B stands at an absolute pressure of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the flow.", "W", equivalent="Pa"),
        ("Q", 1.25), _solve_throat_pressure, 5,
        "continuity for the two speeds and the Bernoulli balance between the sections solved as a root find for the throat pressure, instead of the pressure-difference formula",
        solver_rel_tol=1e-9,
        instances=({"p1": 300.0, "Q": 12.0, "d1": 10.0, "d2": 4.0, "rho": 998.0},
                   {"p1": 250.0, "Q": 9.0, "d1": 8.0, "d2": 3.5, "rho": 1000.0},
                   {"p1": 400.0, "Q": 18.0, "d1": 12.0, "d2": 4.5, "rho": 998.0},
                   {"p1": 180.0, "Q": 15.0, "d1": 10.0, "d2": 5.0, "rho": 997.0}))


def s319_hailstone_terminal_speed() -> Structure:
    return Structure(
        "S319", "Terminal speed of a falling hailstone with quadratic drag", "fluids", "quadratic_drag_terminal_speed_hailstone",
        (_in("r", "length", "cm", "radius of the hailstone", 1.5, (0.5, 3.0)),
         _in("rs", "density", "kg/m^3", "density of the ice", 917.0, (850.0, 930.0)),
         _in("ra", "density", "kg/m^3", "density of the air", 1.2, (1.0, 1.3)),
         _in("cd", "ratio", "1", "drag coefficient of the hailstone, a stated constant", 0.47, (0.4, 0.5), provenance="assumed"),
         _g9(),
         _co("V", "volume", "cm^3", "volume of the hailstone", "4*pi*r**3/3"),
         _co("m", "mass", "g", "mass of the hailstone", "rs*V"),
         _co("A", "area", "cm^2", "cross-sectional area of the hailstone", "pi*r**2"),
         _co("vt", "speed", "m/s", "terminal speed of the hailstone", "sqrt(2*m*g/(cd*ra*A))")),
        "vt",
        (A_G,
         Assumption("A-drag", "The drag on the hailstone is the quadratic drag law with the stated constant drag coefficient, the air is still, and the buoyant force of the air is neglected.",
                    "modelling", ("cd", "ra")),
         Assumption("A-hail", "The hailstone is a uniform ice sphere that does not melt or change in size while it falls, and it has reached its terminal speed.",
                    "boundary_condition", ("r", "rs"))),
        _spec("A spherical hailstone of radius {r} cm and density {rs} kg/m³ is released in still air of density {ra} kg/m³ and falls "
              "until it reaches its terminal speed. The drag force on the hailstone is the drag coefficient, {cd}, times one half of "
              "the density of the air times the square of the speed of the hailstone times its cross-sectional area. The hailstone "
              "does not melt or change in size while it falls, and the buoyant force of the air on it is neglected. "
              "Take g = {g} m/s².",
              "What is the terminal speed of the hailstone?", "terminal speed of the hailstone", "m/s",
              "A separate raindrop B in another storm falls at {v} {u}, but it is unrelated to this hailstone.",
              "A reference hailstone B falls at {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the fall.", "W", equivalent="km/h"),
        ("r", 1.3), _solve_hail_speed, 5,
        "the positive root of the force balance weight minus quadratic drag equal to zero, found by bracketing, instead of the closed-form square root",
        solver_rel_tol=1e-9,
        instances=({"r": 1.5, "rs": 917.0, "ra": 1.2, "cd": 0.47, "g": 9.81},
                   {"r": 2.0, "rs": 900.0, "ra": 1.15, "cd": 0.45, "g": 9.81},
                   {"r": 1.0, "rs": 910.0, "ra": 1.25, "cd": 0.5, "g": 9.8},
                   {"r": 2.5, "rs": 917.0, "ra": 1.1, "cd": 0.47, "g": 9.81}))


def s320_side_jet_range() -> Structure:
    return Structure(
        "S320", "Landing distance of the jet from a hole in the side of a tank", "fluids", "torricelli_jet_horizontal_range_on_ground",
        (_in("H", "length", "cm", "depth of the water above the hole", 50.0, (20.0, 120.0)),
         _in("y", "length", "cm", "height of the hole above the ground", 80.0, (40.0, 150.0)),
         _g9(),
         _co("v", "speed", "m/s", "speed of the jet as it leaves the hole", "sqrt(2*g*H)"),
         _co("t", "time", "s", "time of flight of the jet", "sqrt(2*y/g)"),
         _co("x", "length", "m", "horizontal distance from the tank at which the jet lands", "v*t")),
        "x",
        (A_G,
         Assumption("A-torricelli", "The water is ideal and incompressible, the speed of its surface is negligible compared with the speed of the jet, and the free surface and the jet are at atmospheric pressure.",
                    "modelling", ("H",)),
         Assumption("A-jet", "The jet leaves the small hole horizontally, the depth of the water above the hole changes so little during the flight that it is constant, and air resistance on the jet is neglected.",
                    "boundary_condition", ("H", "y"))),
        _spec("An open tank stands on level ground and has a small circular hole in its vertical side, at a height of {y} cm above the "
              "ground. The water in the tank stands {H} cm above the hole, and the depth changes so little while the jet is in the "
              "air that it is taken as constant. The water is ideal, with the speed of its surface negligible compared with the speed "
              "of the jet, and the jet leaves the hole horizontally and falls to the ground without air resistance. "
              "Take g = {g} m/s².",
              "At what horizontal distance from the tank does the jet land on the ground?",
              "horizontal distance at which the jet lands", "m",
              "A separate fountain B in another park throws a jet to {v} {u}, but it is unrelated to this tank.",
              "A reference jet B lands at {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the jet.", "W", equivalent="cm"),
        ("H", 1.5), _solve_jet_range, 3,
        "the exit speed from Bernoulli's equation and the projectile motion of the jet integrated as an ODE with an event at the ground, instead of the closed form 2 sqrt(H y)",
        solver_rel_tol=1e-8,
        instances=({"H": 50.0, "y": 80.0, "g": 9.81},
                   {"H": 40.0, "y": 60.0, "g": 9.81},
                   {"H": 70.0, "y": 100.0, "g": 9.8},
                   {"H": 30.0, "y": 90.0, "g": 9.81}))


ALL = (s311_hinged_gate_force, s312_hemispherical_bowl_drain, s313_two_tubes_junction_pressure, s314_turbulent_pipe_pressure_drop,
       s315_centrifuge_settling_time, s316_cube_at_the_oil_water_interface, s317_capillary_column_mass,
       s318_throat_pressure_of_a_constriction, s319_hailstone_terminal_speed, s320_side_jet_range)


def all_structures() -> list[Structure]:
    return [factory() for factory in ALL]


STRUCTURES: dict[str, Structure] = {s.structure_id: s for s in all_structures()}

LEVELS: dict[str, str] = {
    "S311": "upper-university", "S312": "upper-university", "S313": "upper-university", "S314": "upper-university",
    "S315": "upper-university", "S316": "introductory", "S317": "introductory", "S318": "introductory", "S319": "introductory",
    "S320": "introductory",
}

# --- gold solution plans ---------------------------------------------------------------------------------


def _plan(sid: str, approach: str, steps: dict[str, tuple[str, str]], check: str) -> Plan:
    from physmon.benchmark.v2 import graph as gr  # local import: ordering follows the graph's dependency order

    structure = STRUCTURES[sid]
    order = [n.name for n in gr.topological_order(structure) if n.kind == "computed"]
    return Plan(approach=approach, steps=tuple(Step(name, *steps[name]) for name in order), check=check)


PLANS: dict[str, Plan] = {
    "S311": _plan(
        "S311",
        "The water pressure grows linearly with depth, so the force on the gate is not at its middle. Find the resultant force, the distance "
        "of its line of action below the hinge, and then balance the torques about the hinge to get the force at the bottom edge.",
        {"Fr": ("Hydrostatic pressure p = rho g z gauge, integrated over the gate: F = rho g w H (d + H/2), the pressure at the middle of the gate times its area",
                "The air pressure acts on both faces and cancels, so only the gauge pressure of the water matters, and the average gauge pressure is the value at the middle of the gate."),
         "zc": ("Centre of pressure, the first moment of the pressure about the hinge divided by the resultant force, z = (d H^2/2 + H^3/3)/(H (d + H/2))",
                "The pressure is larger near the bottom of the gate, so the resultant acts below the middle of the gate; the distance is the torque of the pressure about the hinge divided by the force."),
         "Fh": ("Torque balance about the hinge, F_h H = F_r z, so F_h = F_r z/H",
                "The gate is in equilibrium, and the hinge force and the weight have no torque about the hinge, so the torque of the holding force at the bottom edge balances the torque of the water.")},
        "The force at the bottom edge is smaller than the resultant force of the water, since the resultant acts closer to the hinge than the "
        "bottom edge does, and it grows linearly with the width and with the depth of the water above the hinge."),
    "S312": _plan(
        "S312",
        "The outflow speed is Torricelli's speed at every depth, and the surface area of the water changes with depth in a spherical bowl. "
        "Find the area of the hole, an effective area of the surface, and then the time as the ratio of areas times the time to fall freely "
        "through the depth.",
        {"a": ("Area of a circle, a = pi d^2/4", "The outflow rate is the speed of the jet times the area of the hole."),
         "Ae": ("Level equation A(h) dh/dt = -a sqrt(2 g h) with A(h) = pi (2 R h - h^2) for a spherical cap, integrated from the depth to zero, gives the effective area A_e = pi h0 (2R/3 - h0/5) in t = (A_e/a) sqrt(2 h0/g)",
                "The surface area shrinks as the bowl empties, so the time is the integral of A(h) dh over the outflow speed; carrying out the integral of the cap area gives an effective area that replaces the constant area of a cylinder."),
         "t": ("Torricelli's law with the effective area, t = (A_e/a) sqrt(2 h0/g), the time to empty a cylinder of cross-section A_e",
               "With the effective area the bowl empties in the same time as a cylindrical tank of that cross-section and of depth h0.")},
        "The time is shorter than for a cylinder of the area of the rim, since the water surface is smaller at lower levels, and it grows as "
        "the inverse square of the diameter of the hole."),
    "S313": _plan(
        "S313",
        "The same flow passes through both tubes, and in Poiseuille flow the pressure drop along a tube is proportional to the flow rate and "
        "to a hydraulic resistance, which is proportional to the length and to the inverse fourth power of the radius. Find the ratio of the "
        "two resistances, the fraction of the inlet pressure that remains at the joint, and then the pressure at the joint.",
        {"ratio": ("Poiseuille resistance R = 8 eta L/(pi r^4), so the ratio of the resistances of the two tubes is (L2/L1)(r1/r2)^4, since the viscosity is the same",
                   "The viscosity is the same in both tubes and cancels in the ratio, so only the lengths and the radii are needed."),
         "frac": ("Series resistances carry the same flow, so the pressure above the outlet at the joint is the fraction R2/(R1 + R2) = ratio/(1 + ratio) of the inlet pressure",
                  "The oil leaves into the open air, so the gauge pressure at the inlet is shared between the two tubes in proportion to their resistances, and the second tube takes the part nearest the outlet."),
         "pj": ("Gauge pressure at the joint, p_j = p times the fraction",
                "The joint lies between the tubes, so its gauge pressure is the pressure drop along the second tube, the fraction of the inlet pressure found above.")},
        "The pressure at the joint lies between zero and the inlet gauge pressure, tends to the inlet pressure when the second tube is much "
        "more resistive, and does not depend on the viscosity, since the viscosity multiplies both resistances."),
    "S314": _plan(
        "S314",
        "In turbulent flow in a smooth pipe the pressure drop follows from the friction factor, which depends on the Reynolds number. Find "
        "the Reynolds number, the friction factor, and then the pressure drop from the friction law.",
        {"Re": ("Definition of the Reynolds number, Re = rho v D/eta", "The friction law of the pipe is written in terms of the Reynolds number, and its large value confirms that the flow is turbulent."),
         "f": ("Blasius friction law for a smooth pipe, f = c/Re^(1/4) with the stated constant c", "The friction factor is the stated constant divided by the fourth root of the Reynolds number."),
         "dp": ("Darcy-Weisbach relation, dp = f (L/D) (rho v^2/2), the friction factor times the length over the diameter times the dynamic pressure",
                "The pressure drop between the tappings equals the friction factor times the ratio of the distance to the diameter times the dynamic pressure of the flow.")},
        "The pressure drop grows linearly with the distance between the tappings and as the power seven quarters of the speed, which is steeper "
        "than the linear growth of laminar flow and less steep than the square of the speed for a rough pipe."),
    "S315": _plan(
        "S315",
        "The Stokes drag balances the centrifugal force on the particle less the buoyancy, so the particle moves outwards at a speed "
        "proportional to its distance from the axis. Find the sedimentation coefficient, the logarithm of the ratio of the distances, and "
        "the time from the exponential growth of the distance.",
        {"S": ("Stokes drag balanced against the apparent weight in the rotating frame, 6 pi eta r v = (4 pi r^3/3)(rho_s - rho_f) omega^2 x, so v = S omega^2 x with S = 2 r^2 (rho_s - rho_f)/(9 eta)",
               "The centrifugal acceleration omega^2 x takes the place of g, and the liquid displaced by the particle gives the buoyancy; the sedimentation coefficient collects the properties of the particle and the liquid."),
         "lr": ("Natural logarithm of the ratio of the final to the initial distance from the axis", "Since the speed is proportional to the distance, the distance grows exponentially and the time depends on the logarithm of the ratio of the distances."),
         "t": ("Integration of dx/dt = S omega^2 x, so x = x1 exp(S omega^2 t) and t = ln(x2/x1)/(S omega^2)",
               "Inverting the exponential growth of the distance gives the time to travel from the surface to the bottom of the tube.")},
        "The time is independent of the length of the tube except through the logarithm, and it falls as the square of the rotation rate; the "
        "speed of the particle at the bottom of the tube is so small that the Stokes drag law is justified."),
    "S316": _plan(
        "S316",
        "The cube floats, so the upward force from the liquids on it equals its total weight. Find the total weight, the volume of the cube "
        "that must be in the water, and then the depth below the interface.",
        {"W": ("Weight of the cube plus the weight of the lead weight, W = (rho_c a^3 + m) g", "The lead weight is fixed to the cube and adds its weight to the load that the liquids must support."),
         "Vw": ("Archimedes' principle for the two layers, the buoyant force is rho_o g (a^3 - V_w) + rho_w g V_w, set equal to W; so V_w = (W/g - rho_o a^3)/(rho_w - rho_o)",
                "The cube displaces oil with the part above the interface and water with the part below it, and the lead weight has negligible volume; the force balance fixes the volume in the water."),
         "x": ("Geometry of a cube, the volume below the interface divided by the area of its bottom face, x = V_w/a^2", "The cube has vertical sides and a horizontal base, so the volume in the water is the base area times the depth.")},
        "The depth lies between zero and the side of the cube, and it grows linearly with the mass of the lead weight; it does not depend on the "
        "depth of the oil above the cube."),
    "S317": _plan(
        "S317",
        "The curved meniscus lowers the pressure just under it by an amount that the weight of the raised water balances. Find the height of "
        "the water, the volume of the cylinder of water above the level in the dish, and then its mass.",
        {"h": ("Jurin's law, the Laplace pressure 2 gamma cos(theta)/r equals rho g h, so h = 2 gamma cos(theta)/(rho g r)", "The pressure under the spherical meniscus is lower than the pressure of the air by 2 gamma cos(theta)/r, and the hydrostatic pressure of the raised column makes up the difference."),
         "V": ("Volume of a cylinder, V = pi r^2 h", "The water above the level in the dish is a cylinder with the radius of the tube, since the meniscus volume is neglected."),
         "m": ("Definition of density, m = rho V", "The mass of the raised water is its density times its volume.")},
        "The mass equals 2 pi r gamma cos(theta)/g, the vertical component of the surface tension acting round the circumference of the "
        "tube divided by g, and it does not depend on the density of the water."),
    "S318": _plan(
        "S318",
        "The speed of the water rises in the throat, and Bernoulli's equation shows the pressure falls by the same amount of energy per "
        "volume. Find the two speeds from the flow rate and the areas, and then the pressure in the throat.",
        {"v1": ("Continuity for a circular section, v = Q/(pi d^2/4)", "The volume flow rate is the same through every section, so the speed in the wide section is the flow rate divided by its area."),
         "v2": ("Continuity for a circular section, v = Q/(pi d^2/4)", "The speed in the throat follows in the same way from the smaller area."),
         "p2": ("Bernoulli's equation along a horizontal streamline, p1 + rho v1^2/2 = p2 + rho v2^2/2", "The pipe is horizontal and the flow is frictionless, so the pressure falls by the increase of the kinetic energy per unit volume.")},
        "The pressure in the throat is lower than in the wide section and is positive for these values; the liquid stays above its vapour "
        "pressure, which is required for the water to stay liquid."),
    "S319": _plan(
        "S319",
        "At the terminal speed the quadratic drag equals the weight. Find the volume and the mass of the hailstone, its cross-sectional area, "
        "and then the speed from the force balance.",
        {"V": ("Volume of a sphere, V = 4 pi r^3/3", "The mass of the hailstone follows from its volume and the density of ice."),
         "m": ("Definition of density, m = rho_s V", "The weight that the drag must balance is the mass times g."),
         "A": ("Area of a circle, A = pi r^2", "The drag law uses the cross-sectional area of the sphere facing the flow."),
         "vt": ("Force balance m g = cd (rho_a v^2/2) A, so v = sqrt(2 m g/(cd rho_a A))", "At constant speed there is no net force, so the quadratic drag equals the weight.")},
        "The speed grows as the square root of the radius and falls as the square root of the drag coefficient and of the air density; for a "
        "hailstone of a few centimetres it is a few tens of metres per second."),
    "S320": _plan(
        "S320",
        "The water leaves the hole with Torricelli's speed and then moves as a projectile launched horizontally. Find the exit speed, the "
        "time to fall to the ground, and then the horizontal distance.",
        {"v": ("Bernoulli's equation between the free surface and the jet, both at atmospheric pressure, rho g H = rho v^2/2, so v = sqrt(2 g H)", "The speed of the surface is negligible, so the pressure head of the water above the hole becomes the kinetic energy per unit volume of the jet."),
         "t": ("Free fall from rest in the vertical direction, y = g t^2/2, so t = sqrt(2 y/g)", "The jet leaves horizontally, so its vertical motion starts from rest and is a free fall through the height of the hole."),
         "x": ("Uniform horizontal motion at the exit speed, x = v t", "There is no horizontal force on the jet in the air, so the distance is the exit speed times the time of flight.")},
        "The distance equals 2 sqrt(H y), the same when the depth above the hole and the height of the hole are exchanged, and it does not "
        "depend on g or on the density of the liquid."),
}
