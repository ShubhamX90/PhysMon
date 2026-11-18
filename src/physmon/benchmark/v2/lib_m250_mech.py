"""M250 phase 2, batch mech: ten NEW classical-mechanics structures, S201 to S210 (exploration pool).

Authority: plan of record v2.2 (`docs/proposals/PhysMon_Research_v2.tex`, "Dataset plan"), the dataset admission standard
(`docs/registry/v2/g1/dataset_admission_standard.md`) and plan revision v2.2 section G. Each structure is a typed graph with an
independently coded numeric solver (a linear system, an ODE with an event, an orbit integration, a quadrature with a root finder,
the impulse equations of each body, a reduced-mass route), four numeric instantiations and a relevant edit that moves the answer.

The situations are new against dataset v1 (S01-S95), every `library*` / `lib_*` structure and the October templates: a driven damped
oscillator, the final speed of a rocket (variable mass), a bead on a rotating hoop (Lagrangian level), a right-angle collision of two
skaters, a turntable that is spun up, a spun-up tank of liquid (non-inertial frame), a double Atwood machine, a spinning disc dropped
onto a stationary one, a free rod struck by a lump of clay, and the decay time of a damped oscillator.

Every answer-deciding condition (initial and boundary conditions, the governing model where models compete) is stated in the base
text. `PLANS` holds the gold solving technique for each structure, `LEVELS` and `TOPICS` label them. These are agent-authored
candidates: solver-certified, not expert-reviewed.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import quad, solve_ivp
from scipy.optimize import brentq

from physmon.benchmark.v2.graph import Assumption, Structure
from physmon.benchmark.v2.library import A_G, _co, _g, _in, _spec
from physmon.benchmark.v2.trace import Plan, Step

# --- solvers (independent routes; SI inputs in input-node order) --------------------------------------------------------------------


def _solve_driven_amplitude(m, k, b, f0, w):
    # Steady state x = a cos(w t) + c sin(w t): the cosine and sine coefficients of m x'' + b x' + k x = F0 cos(w t) give a 2x2 linear system.
    stiff = k - m * w * w
    a, c = np.linalg.solve(np.array([[stiff, b * w], [-b * w, stiff]]), np.array([f0, 0.0]))
    return float(math.hypot(a, c))


def _solve_rocket_speed(md, mf, u):
    # Integrate the rocket equation dv/dt = u r / m with a steady burn of r = 5 kg/s (the rate does not enter the answer) until the fuel is gone.
    rate = 5.0

    def burnt_out(t, y):
        return y[1] - md

    burnt_out.terminal = True
    solution = solve_ivp(lambda t, y: [u * rate / y[1], -rate], (0.0, 10.0 * mf / rate), [0.0, md + mf], events=burnt_out, rtol=1e-12, atol=1e-12)
    return float(solution.y_events[0][0][0])


def _solve_hoop_period(radius, omega, g):
    # The equilibrium angle from a root finder on the radial force balance; then the full nonlinear equation of motion integrated from a tiny
    # displacement at rest; the time between two successive downward crossings of the equilibrium is the period.
    def balance(theta):
        return omega ** 2 * math.cos(theta) - g / radius

    theta0 = brentq(balance, 1e-9, math.pi / 2, xtol=1e-14, rtol=1e-14)

    def crossing(t, y):
        return y[0] - theta0

    crossing.direction = -1
    solution = solve_ivp(lambda t, y: [y[1], math.sin(y[0]) * (omega ** 2 * math.cos(y[0]) - g / radius)], (0.0, 50.0),
                         [theta0 + 1e-4, 0.0], events=crossing, rtol=1e-12, atol=1e-14)
    crossings = solution.t_events[0]
    return float(crossings[1] - crossings[0])


def _solve_skater_loss(m1, v1, m2, v2):
    # The centre-of-mass route: the energy lost in a perfectly inelastic collision is (1/2) mu v_rel^2 with the reduced mass and the relative speed.
    mu = m1 * m2 / (m1 + m2)
    return float(0.5 * mu * (v1 ** 2 + v2 ** 2))


def _solve_turntable_friction(m, r, alpha, t):
    # Integrate the angular speed from rest under the constant angular acceleration, then the two components of the coin's acceleration and the force.
    solution = solve_ivp(lambda s, y: [alpha], (0.0, t), [0.0], rtol=1e-12, atol=1e-14)
    omega = float(solution.y[0][-1])
    return float(m * math.hypot(omega ** 2 * r, alpha * r))


def _solve_tank_axis_depth(h0, radius, omega, g):
    # Volume conservation with the paraboloid z(r) = z0 + omega^2 r^2 / (2 g): quadrature of the volume under the surface, root finder on z0.
    def volume_error(z0):
        volume, _ = quad(lambda r: 2.0 * math.pi * r * (z0 + omega ** 2 * r * r / (2.0 * g)), 0.0, radius, epsabs=1e-14, epsrel=1e-13)
        return volume - math.pi * radius ** 2 * h0

    return float(brentq(volume_error, -10.0, 10.0, xtol=1e-14, rtol=1e-14))


def _solve_double_atwood(m1, m2, m3, g):
    # Newton's second law for each block, the massless-pulley tension relation and the string constraint as a linear system in
    # (a1, a2, a3, T1, T2); downward accelerations positive.
    matrix = np.array([[m1, 0.0, 0.0, 1.0, 0.0],
                       [0.0, 0.0, 0.0, 1.0, -2.0],
                       [0.0, m2, 0.0, 0.0, 1.0],
                       [0.0, 0.0, m3, 0.0, 1.0],
                       [2.0, 1.0, 1.0, 0.0, 0.0]])
    return float(np.linalg.solve(matrix, np.array([m1 * g, 0.0, m2 * g, m3 * g, 0.0]))[0])


def _solve_disc_drop_loss(m1, r1, n1, i2):
    # Integrate the two discs under a constant friction torque of 0.8 N m (it does not enter the answer) until their speeds are equal,
    # accumulating the heat power torque x relative speed; the heat generated up to that event.
    torque = 0.8
    i1 = 0.5 * m1 * r1 ** 2  # the moment of inertia of a uniform solid disc

    def equal(t, y):
        return y[0] - y[1]

    equal.terminal = True
    solution = solve_ivp(lambda t, y: [-torque / i1, torque / i2, torque * (y[0] - y[1])], (0.0, 1.0e4), [n1, 0.0, 0.0], events=equal,
                         rtol=1e-12, atol=1e-12)
    return float(solution.y_events[0][0][2])


def _solve_rod_clay(big_m, length, m, v, d):
    # Impulse equations of each body and the contact condition as a linear system in (J, V, w, u): the rod gets the impulse J at the distance d
    # (M V = J, I w = J d), the clay loses m (v - u) = J, and sticks: u = V + w d.
    inertia = big_m * length ** 2 / 12.0
    matrix = np.array([[1.0, -big_m, 0.0, 0.0],
                       [d, 0.0, -inertia, 0.0],
                       [1.0, 0.0, 0.0, m],
                       [0.0, 1.0, d, -1.0]])
    return float(np.linalg.solve(matrix, np.array([0.0, 0.0, m * v, 0.0]))[2])


def _solve_decay_time(m, b, f):
    # The envelope of the underdamped displacement from the oscillator integrated with a very stiff spring is awkward; instead integrate the
    # energy-like envelope equation dA/dt = -(b / 2m) A from the unit amplitude until it falls to the fraction f.
    def reached(t, y):
        return y[0] - f

    reached.terminal = True
    solution = solve_ivp(lambda t, y: [-b / (2.0 * m) * y[0]], (0.0, 1.0e4), [1.0], events=reached, rtol=1e-12, atol=1e-14)
    return float(solution.t_events[0][0])


# --- structures ---------------------------------------------------------------------------------------------------------------------


def s201_driven_damped_amplitude() -> Structure:
    return Structure(
        "S201", "Steady-state amplitude of a driven damped oscillator", "mechanics", "driven_damped_oscillator_steady_amplitude",
        (_in("m", "mass", "kg", "mass of the block", 0.5, (0.2, 1.5)),
         _in("k", "spring_constant", "N/m", "spring constant", 200.0, (100.0, 400.0)),
         _in("b", "damping_coefficient", "kg/s", "damping coefficient of the damper", 2.0, (0.5, 6.0)),
         _in("F0", "force", "N", "amplitude of the driving force", 6.0, (2.0, 10.0)),
         _in("w", "angular_frequency", "rad/s", "angular frequency of the driving force", 30.0, (10.0, 45.0)),
         _co("w0sq", "squared_angular_frequency", "rad/s^2", "squared natural angular frequency of the undamped oscillator", "k/m"),
         _co("gam", "rate", "1/s", "damping rate of the oscillator", "b/m"),
         _co("den", "squared_angular_frequency", "rad/s^2", "magnitude of the denominator of the response function", "sqrt((w0sq - w**2)**2 + (gam*w)**2)"),
         _co("A", "length", "cm", "amplitude of the steady-state oscillation", "F0/(m*den)")),
        "A",
        (Assumption("A-model", "The spring is ideal and obeys Hooke's law, and the damper exerts a force proportional to the speed of the block "
                               "(viscous damping).", "modelling", ("k", "b")),
         Assumption("A-steady", "The block has been driven for so long that the transient has died out, so only the steady oscillation at the "
                                "driving frequency remains.", "boundary_condition", ("w",))),
        _spec("A block of mass {m} kg is attached to a spring of spring constant {k} N/m and slides on a horizontal frictionless track. A damper "
              "exerts on the block a force proportional to its speed, with damping coefficient {b} kg/s. A horizontal force that varies "
              "sinusoidally in time, with amplitude {F0} N and angular frequency {w} rad/s, is applied to the block along the track. The "
              "block has been driven for a long time, so that the transient motion has died out. The spring is light and obeys Hooke's law for the extensions that occur. Air resistance is negligible, and no object outside the apparatus exerts a force on the block.",
              "What is the amplitude of the steady oscillation of the block?", "amplitude of the steady oscillation of the block", "cm",
              "A separate oscillator B on another track has an amplitude of {v} {u}, but it is unrelated to this block.",
              "A reference oscillator B oscillates with an amplitude of {v} {u}.",
              "A separate motor B is rated at {v} {u}, but it plays no part in the motion of the block.", "W", equivalent="mm"),
        ("F0", 1.5), _solve_driven_amplitude, 5,
        "the cosine and sine coefficients of the steady solution found as a 2x2 linear system, and the amplitude as their root-sum-square",
        solver_rel_tol=1e-9,
        instances=({"m": 0.5, "k": 200.0, "b": 2.0, "F0": 6.0, "w": 30.0}, {"m": 0.4, "k": 250.0, "b": 1.5, "F0": 5.0, "w": 35.0},
                   {"m": 0.8, "k": 150.0, "b": 3.0, "F0": 8.0, "w": 25.0}, {"m": 0.6, "k": 300.0, "b": 2.5, "F0": 7.0, "w": 40.0}))


def s202_rocket_final_speed() -> Structure:
    return Structure(
        "S202", "Final speed of a rocket that burns all its fuel", "mechanics", "tsiolkovsky_rocket_final_speed_empty_mass",
        (_in("md", "mass", "kg", "empty mass of the rocket (body and engine, without fuel or payload)", 800.0, (300.0, 2000.0)),
         _in("mf", "mass", "kg", "mass of the fuel at the start", 2400.0, (500.0, 6000.0)),
         _in("u", "speed", "km/s", "speed of the exhaust relative to the rocket", 3.0, (2.0, 4.5)),
         _co("m0", "mass", "kg", "total mass of the rocket at the start", "md + mf"),
         _co("ratio", "mass_ratio", "1", "ratio of the initial mass to the final mass", "m0/md"),
         _co("vf", "speed", "km/s", "speed of the rocket after all the fuel has been burned", "u*log(ratio)")),
        "vf",
        (Assumption("A-space", "The rocket is in empty space, far from any planet or star, so no gravity and no drag act on it.", "modelling", ("md",)),
         Assumption("A-burn", "The rocket starts at rest and burns all its fuel at a steady rate, ejecting it backwards along the line of motion "
                              "at a constant speed relative to the rocket; the whole fuel is used and the exhaust leaves with no other loss.",
                    "boundary_condition", ("mf", "u"))),
        _spec("A rocket in empty space, far from any planet or star, has an empty mass of {md} kg (its body and engine, without fuel or payload) "
              "and starts at rest with {mf} kg of fuel on board. Its engine burns all this fuel at a steady rate, ejecting it backwards along "
              "the line of motion at a constant speed of {u} km/s relative to the rocket. No object outside the rocket and whatever it carries exerts an appreciable force on it.",
              "What is the speed of the rocket after all the fuel has been burned?", "speed of the rocket after all the fuel has been burned", "km/s",
              "A separate rocket B on another launch pad reaches a speed of {v} {u}, but it is unrelated to this rocket.",
              "A reference rocket B reaches a speed of {v} {u}.",
              "A separate crane B is rated at {v} {u}, but it plays no part in the flight.", "kg", equivalent="m/s"),
        ("mf", 1.25), _solve_rocket_speed, 3,
        "the rocket equation dv/dt = u r / m integrated with an adaptive ODE solver at a steady burn rate until the fuel is gone",
        solver_rel_tol=1e-6,
        instances=({"md": 800.0, "mf": 2400.0, "u": 3.0}, {"md": 500.0, "mf": 1500.0, "u": 2.5}, {"md": 1200.0, "mf": 2000.0, "u": 3.5},
                   {"md": 600.0, "mf": 4200.0, "u": 2.2}))


def s203_bead_on_rotating_hoop() -> Structure:
    return Structure(
        "S203", "Small oscillations of a bead on a rotating hoop", "mechanics", "rotating_hoop_bead_small_oscillation_period",
        (_in("R", "length", "m", "radius of the hoop", 0.4, (0.25, 0.8)),
         _in("Om", "angular_frequency", "rad/s", "angular speed of the rotating hoop", 7.0, (7.0, 15.0)),
         _g(),
         _co("c0", "dimensionless", "1", "cosine of the polar angle of the equilibrium position, measured from the downward vertical",
             "g/(Om**2*R)"),
         _co("s0", "dimensionless", "1", "sine of the polar angle of the equilibrium position", "sqrt(1 - c0**2)"),
         _co("ws", "angular_frequency", "rad/s", "angular frequency of small oscillations about the equilibrium", "Om*s0"),
         _co("T", "time", "s", "period of small oscillations about the equilibrium", "2*pi/ws")),
        "T",
        (A_G, Assumption("A-hoop", "The hoop is thin and rigid, the bead slides on it without friction, and the bead is small enough to be treated "
                                   "as a point mass; the hoop turns at a constant angular speed about its vertical diameter.", "modelling",
                         ("R", "Om")),
         Assumption("A-equilibrium", "The bead rests in equilibrium relative to the hoop at a point away from the axis, the stable point that "
                                     "exists because the hoop turns faster than the critical rate, and the oscillations are small and along the "
                                     "hoop.", "boundary_condition", ("Om",))),
        _spec("A small bead slides without friction on a thin vertical circular hoop of radius {R} m. The hoop is mounted on a platform and turns "
              "at a constant angular speed of {Om} rad/s, kept constant by a motor, about its vertical diameter. Air resistance is negligible. Observed from the hoop, the bead rests in equilibrium at a "
              "point on the hoop away from the axis. Take g = {g} m/s².",
              "What is the period of small oscillations of the bead along the hoop about this equilibrium position, as observed from the hoop?",
              "period of small oscillations of the bead", "s",
              "A separate pendulum B on another stand has a period of {v} {u}, but it is unrelated to this bead.",
              "A reference oscillator B has a period of {v} {u}.",
              "A separate stopwatch B reads {v} {u}, but it plays no part in the motion of the bead.", "m", equivalent="ms"),
        ("Om", 1.3), _solve_hoop_period, 3,
        "the equilibrium angle by a root finder on the radial force balance, then the full nonlinear equation of motion integrated from a tiny "
        "displacement; the time between two successive downward crossings of the equilibrium",
        solver_rel_tol=1e-6,
        instances=({"R": 0.4, "Om": 7.0, "g": 9.8}, {"R": 0.3, "Om": 9.0, "g": 9.8}, {"R": 0.5, "Om": 7.5, "g": 9.8},
                   {"R": 0.25, "Om": 10.0, "g": 9.81}))


def s204_skaters_right_angle_collision() -> Structure:
    return Structure(
        "S204", "Kinetic energy lost when two skaters collide at right angles", "mechanics", "perpendicular_inelastic_collision_energy_loss",
        (_in("m1", "mass", "kg", "mass of the skater moving east", 60.0, (40.0, 90.0)),
         _in("v1", "speed", "m/s", "speed of the skater moving east", 4.0, (2.0, 7.0)),
         _in("m2", "mass", "kg", "mass of the skater moving north", 75.0, (50.0, 100.0)),
         _in("v2", "speed", "m/s", "speed of the skater moving north", 3.0, (2.0, 7.0)),
         _co("px", "momentum", "kg*m/s", "eastward momentum of the system", "m1*v1"),
         _co("py", "momentum", "kg*m/s", "northward momentum of the system", "m2*v2"),
         _co("M", "mass", "kg", "total mass of the two skaters", "m1 + m2"),
         _co("Vf", "speed", "m/s", "speed of the two skaters together after the collision", "sqrt(px**2 + py**2)/M"),
         _co("Ki", "energy", "J", "kinetic energy before the collision", "(m1*v1**2 + m2*v2**2)/2"),
         _co("Kf", "energy", "J", "kinetic energy after the collision", "M*Vf**2/2"),
         _co("dK", "energy", "J", "kinetic energy converted to other forms in the collision", "Ki - Kf")),
        "dK",
        (Assumption("A-ice", "The ice is frictionless and level, and the collision is brief, so only the two skaters exchange momentum.", "modelling",
                    ("m1", "m2")),
         Assumption("A-stick", "The skaters hold on to each other and move off together after the collision, a perfectly inelastic collision, and "
                               "their velocities before it are perpendicular.", "boundary_condition", ("v1", "v2"))),
        _spec("Two ice skaters glide on frictionless ice. A skater of mass {m1} kg moves due east at {v1} m/s and a skater of mass {m2} kg moves "
              "due north at {v2} m/s. They collide and hold on to each other, moving off together. Air resistance is negligible, and the skaters may be treated as particles.",
              "How much kinetic energy is converted to other forms in the collision?", "kinetic energy converted to other forms in the collision",
              "J",
              "A separate skater B on another rink has a kinetic energy of {v} {u}, but she is unrelated to these skaters.",
              "A reference collision B converts {v} {u} of kinetic energy.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the collision.", "W", equivalent="kJ"),
        ("m2", 1.25), _solve_skater_loss, 4,
        "the centre-of-mass route: one half of the reduced mass times the square of the relative speed",
        solver_rel_tol=1e-9,
        instances=({"m1": 60.0, "v1": 4.0, "m2": 75.0, "v2": 3.0}, {"m1": 55.0, "v1": 5.0, "m2": 65.0, "v2": 2.5},
                   {"m1": 70.0, "v1": 3.0, "m2": 80.0, "v2": 4.0}, {"m1": 48.0, "v1": 6.0, "m2": 62.0, "v2": 3.5}))


def s205_turntable_spin_up_friction() -> Structure:
    return Structure(
        "S205", "Friction force on a coin on a turntable that is spun up", "mechanics", "turntable_spin_up_static_friction_force",
        (_in("m", "mass", "g", "mass of the coin", 12.0, (5.0, 30.0)),
         _in("r", "length", "cm", "distance of the coin from the axis of the turntable", 8.0, (5.0, 15.0)),
         _in("alpha", "angular_acceleration", "rad/s^2", "constant angular acceleration of the turntable", 0.9, (0.3, 2.0)),
         _in("t", "time", "s", "time since the turntable started from rest", 4.0, (1.0, 6.0)),
         _co("w", "angular_frequency", "rad/s", "angular speed of the turntable", "alpha*t"),
         _co("ac", "acceleration", "m/s^2", "centripetal acceleration of the coin", "w**2*r"),
         _co("at", "acceleration", "m/s^2", "tangential acceleration of the coin", "alpha*r"),
         _co("f", "force", "mN", "magnitude of the friction force of the turntable on the coin", "m*sqrt(ac**2 + at**2)")),
        "f",
        (Assumption("A-turntable", "The turntable is horizontal and rigid and turns about its vertical axis with a constant angular acceleration "
                                   "from rest.", "modelling", ("alpha",)),
         Assumption("A-noslip", "The coin does not slip: it stays at the same place on the turntable, so its acceleration is that of the point "
                                "of the turntable under it, and the friction force is the force that gives it this acceleration.",
                    "boundary_condition", ("m", "r", "t"))),
        _spec("A coin of mass {m} g rests on a horizontal turntable, at a distance of {r} cm from its axis. The turntable starts from rest at "
              "time zero and is spun up with a constant angular acceleration of {alpha} rad/s². At a time {t} s after it started, the coin has "
              "not slipped and is still at the same place on the turntable. The turntable turns about a fixed vertical axis through its centre, the coin is small compared with its distance from the axis, and air resistance is negligible.",
              "What is the magnitude of the friction force that the turntable exerts on the coin at that time?",
              "friction force of the turntable on the coin", "mN",
              "A separate block B on another turntable feels a friction force of {v} {u}, but it is unrelated to this coin.",
              "A reference coin B feels a friction force of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the motion of the coin.", "W", equivalent="N"),
        ("m", 1.5), _solve_turntable_friction, 4,
        "the angular speed integrated from rest under the constant angular acceleration, then the vector sum of the centripetal and tangential "
        "accelerations times the mass",
        solver_rel_tol=1e-9,
        instances=({"m": 12.0, "r": 8.0, "alpha": 0.9, "t": 4.0}, {"m": 20.0, "r": 10.0, "alpha": 0.8, "t": 6.0},
                   {"m": 8.0, "r": 6.0, "alpha": 1.2, "t": 5.0}, {"m": 25.0, "r": 12.0, "alpha": 0.7, "t": 5.0}))


def s206_spun_up_tank_axis_depth() -> Structure:
    return Structure(
        "S206", "Depth of liquid at the axis of a spun-up tank", "mechanics", "rotating_tank_free_surface_axis_depth",
        (_in("h0", "length", "cm", "depth of the liquid in the tank at rest", 30.0, (28.0, 40.0)),
         _in("R", "length", "cm", "inner radius of the tank", 15.0, (10.0, 18.0)),
         _in("Om", "angular_frequency", "rad/s", "angular speed of the tank", 10.0, (6.0, 12.0)),
         _g(),
         _co("dh", "length", "cm", "height of the liquid surface at the wall above its height at the axis", "Om**2*R**2/(2*g)"),
         _co("hw", "length", "cm", "depth of the liquid at the wall of the tank", "h0 + dh/2"),
         _co("ha", "length", "cm", "depth of the liquid at the axis of the tank", "hw - dh")),
        "ha",
        (A_G, Assumption("A-solid", "The liquid has reached a steady state in which it turns with the tank as a solid body at the stated angular "
                                    "speed; the tank is a vertical cylinder turning about its axis and open at the top, and it is tall enough "
                                    "that no liquid spills.", "boundary_condition", ("Om",)),
         Assumption("A-surface", "The pressure at the free surface is atmospheric, and surface tension and the viscosity of the liquid do not "
                                 "matter in the steady state.", "modelling", ("h0",))),
        _spec("An open cylindrical tank of inner radius {R} cm stands on a platform and contains a liquid to a depth of {h0} cm when it is at "
              "rest. The tank is tall enough that no liquid spills. The tank is then spun at a constant angular speed of {Om} rad/s about its "
              "vertical axis, until the liquid turns with the tank as a solid body. The liquid is incompressible and its evaporation is negligible. Take g = {g} m/s².",
              "What is the depth of the liquid at the axis of the tank?", "depth of the liquid at the axis of the tank", "cm",
              "A separate pond B has a depth of {v} {u}, but it is unrelated to this tank.",
              "A reference tank B has a liquid depth of {v} {u} at its axis.",
              "A separate pump B is rated at {v} {u}, but it plays no part in the spinning of the tank.", "W", equivalent="mm"),
        ("Om", 1.15), _solve_tank_axis_depth, 4,
        "the paraboloid of the free surface with the volume of the liquid conserved: a quadrature of the volume under the surface and a root "
        "finder on the height of its lowest point",
        solver_rel_tol=1e-8,
        instances=({"h0": 30.0, "R": 15.0, "Om": 10.0, "g": 9.8}, {"h0": 32.0, "R": 14.0, "Om": 11.0, "g": 9.8},
                   {"h0": 31.0, "R": 16.0, "Om": 9.5, "g": 9.81}, {"h0": 30.0, "R": 13.0, "Om": 12.0, "g": 9.8}))


def s207_double_atwood_machine() -> Structure:
    return Structure(
        "S207", "Acceleration of the single block of a double Atwood machine", "mechanics", "double_atwood_movable_pulley_acceleration",
        (_in("m1", "mass", "kg", "mass of the single block on the first string", 8.0, (6.0, 10.0)),
         _in("m2", "mass", "kg", "mass of the first block on the second string", 1.0, (0.5, 1.5)),
         _in("m3", "mass", "kg", "mass of the second block on the second string", 1.5, (0.5, 2.0)),
         _g(),
         _co("S", "mass", "kg", "sum of the two masses on the movable pulley", "m2 + m3"),
         _co("mr", "mass", "kg", "effective mass of the movable pulley and its two blocks as seen by the first string", "4*m2*m3/S"),
         _co("a1", "acceleration", "m/s^2", "downward acceleration of the single block", "g*(m1 - mr)/(m1 + mr)")),
        "a1",
        (A_G, Assumption("A-light", "Both strings are light and inextensible and stay taut, and both pulleys are light and turn without friction, "
                                    "so the tension is the same on both sides of each pulley.", "modelling", ("m1", "m2", "m3")),
         Assumption("A-release", "The blocks are released from rest and the first string is long enough that no block reaches a pulley or the "
                                 "floor while the acceleration is measured.", "boundary_condition", ("m1",))),
        _spec("A light string passes over a fixed pulley. A single block of mass {m1} kg hangs from one end of it. From the other end hangs a "
              "movable pulley, over which a second light string passes, carrying a block of mass {m2} kg on one side and a block of mass "
              "{m3} kg on the other. Both pulleys are light and turn without friction, and both strings stay taut. The blocks move only vertically and air resistance is negligible. The blocks are released from "
              "rest. Take g = {g} m/s².",
              "What is the downward acceleration of the single block at the moment of release?", "downward acceleration of the single block",
              "m/s^2",
              "A separate lift B on another rig accelerates at {v} {u}, but it is unrelated to these blocks.",
              "A reference block B has a downward acceleration of {v} {u}.",
              "A separate stopwatch B reads {v} {u}, but it plays no part in the motion of the blocks.", "s", equivalent="cm/s^2"),
        ("m1", 1.25), _solve_double_atwood, 4,
        "Newton's second law for each block, the tension relation of the massless movable pulley and the string constraint solved as a 5x5 linear system",
        solver_rel_tol=1e-9,
        instances=({"m1": 8.0, "m2": 1.0, "m3": 1.5, "g": 9.8}, {"m1": 7.0, "m2": 0.8, "m3": 1.2, "g": 9.8},
                   {"m1": 9.0, "m2": 1.4, "m3": 1.8, "g": 9.81}, {"m1": 6.5, "m2": 0.9, "m3": 1.0, "g": 9.8}))


def s208_disc_dropped_on_disc() -> Structure:
    return Structure(
        "S208", "Energy dissipated when a spinning disc is dropped onto a stationary disc", "mechanics",
        "coaxial_disc_coupling_energy_dissipated",
        (_in("m1", "mass", "kg", "mass of the spinning disc, a uniform solid disc", 2.0, (1.0, 5.0)),
         _in("r1", "length", "cm", "radius of the spinning disc", 20.0, (10.0, 30.0)),
         _in("n1", "angular_frequency", "rpm", "angular speed of the spinning disc before the contact", 600.0, (300.0, 1500.0)),
         _in("I2", "moment_of_inertia", "kg*m^2", "moment of inertia of the stationary disc about the axle", 0.03, (0.02, 0.2)),
         _co("I1", "moment_of_inertia", "kg*m^2", "moment of inertia of the spinning disc about the axle", "m1*r1**2/2"),
         _co("wf", "angular_frequency", "rad/s", "common angular speed of the two discs after the coupling", "I1*n1/(I1 + I2)"),
         _co("Ki", "energy", "J", "rotational kinetic energy before the coupling", "I1*n1**2/2"),
         _co("Kf", "energy", "J", "rotational kinetic energy after the coupling", "(I1 + I2)*wf**2/2"),
         _co("dE", "energy", "J", "mechanical energy dissipated as heat in the coupling", "Ki - Kf")),
        "dE",
        (Assumption("A-axle", "The two discs are coaxial on a frictionless axle, so no external torque acts on the pair about the axle.", "modelling",
                    ("m1", "I2")),
         Assumption("A-grip", "The faces grip each other and slip against each other until the two discs turn together at one angular speed; "
                              "the energy that is not kept as rotational kinetic energy is dissipated as heat.", "boundary_condition", ("n1",))),
        _spec("A uniform solid disc of mass {m1} kg and radius {r1} cm spins at {n1} rpm on a frictionless axle through its centre. It is lowered onto a "
              "second disc, with a moment of inertia of {I2} kg*m² about the same axle, that is at rest on the same axle. The faces of the "
              "discs grip each other and slip against each other until the two discs turn together. The discs are rigid, air resistance is negligible, and the energy that is not kept as rotational kinetic energy is dissipated as heat in the coupling.",
              "How much mechanical energy is dissipated as heat when the discs reach a common angular speed?",
              "mechanical energy dissipated as heat", "J",
              "A separate flywheel B in another machine stores {v} {u}, but it is unrelated to these discs.",
              "A reference coupling B dissipates {v} {u} as heat.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the coupling.", "W", equivalent="kJ"),
        ("I2", 1.5), _solve_disc_drop_loss, 4,
        "the two discs integrated under a constant friction torque until their speeds are equal, with the heat power torque times relative speed accumulated (I1 = m r^2 / 2 for the uniform solid disc)",
        solver_rel_tol=1e-6,
        instances=({"m1": 2.0, "r1": 20.0, "n1": 600.0, "I2": 0.03}, {"m1": 3.0, "r1": 25.0, "n1": 900.0, "I2": 0.06},
                   {"m1": 1.5, "r1": 15.0, "n1": 1200.0, "I2": 0.05}, {"m1": 4.0, "r1": 20.0, "n1": 450.0, "I2": 0.04}))


def s209_rod_struck_by_clay() -> Structure:
    return Structure(
        "S209", "Angular speed of a rod struck by a lump of clay", "mechanics", "free_rod_clay_collision_angular_speed",
        (_in("M", "mass", "kg", "mass of the rod", 2.0, (1.0, 3.0)),
         _in("L", "length", "m", "length of the rod", 1.2, (0.8, 1.6)),
         _in("m", "mass", "kg", "mass of the lump of clay", 0.3, (0.1, 0.5)),
         _in("v", "speed", "m/s", "speed of the clay just before the collision", 6.0, (3.0, 12.0)),
         _in("d", "length", "m", "distance of the point of impact from the centre of the rod", 0.4, (0.1, 0.4)),
         _co("mt", "mass", "kg", "total mass of the rod and the clay", "M + m"),
         _co("yc", "length", "m", "distance of the centre of mass of the combined body from the centre of the rod", "m*d/mt"),
         _co("Ic", "moment_of_inertia", "kg*m^2", "moment of inertia of the combined body about its centre of mass",
             "M*L**2/12 + M*yc**2 + m*(d - yc)**2"),
         _co("w", "angular_frequency", "rad/s", "angular speed of the combined body just after the collision", "m*v*(d - yc)/Ic")),
        "w",
        (Assumption("A-rod", "The rod is thin and uniform, and the clay is small enough to be treated as a point mass; the table is smooth, so "
                             "no horizontal force other than the collision acts on the rod and the clay.", "modelling", ("M", "L", "m")),
         Assumption("A-collision", "The clay moves perpendicular to the rod, hits it at the stated point and sticks to it, and the collision is "
                                   "brief; the rod is free to move and turn on the table.", "boundary_condition", ("v", "d"))),
        _spec("A thin uniform rod of mass {M} kg and length {L} m lies on a smooth horizontal table and is free to move. A lump of clay of mass "
              "{m} kg slides across the table at {v} m/s, perpendicular to the rod, and hits the rod at a point {d} m from its centre. The clay "
              "sticks to the rod. The clay is small enough to be treated as a point, and air resistance is negligible.",
              "What is the angular speed of the rod and clay together about their common centre of mass just after the collision?",
              "angular speed of the rod and clay together just after the collision", "rad/s",
              "A separate wheel B on another table turns at {v} {u}, but it is unrelated to this rod.",
              "A reference rod B turns at {v} {u} after its own collision.",
              "A separate stopwatch B reads {v} {u}, but it plays no part in the collision.", "s", equivalent="rpm"),
        ("v", 1.5), _solve_rod_clay, 5,
        "the impulse equations of the rod and of the clay with the contact condition, solved as a 4x4 linear system",
        solver_rel_tol=1e-9,
        instances=({"M": 2.0, "L": 1.2, "m": 0.3, "v": 6.0, "d": 0.4}, {"M": 1.5, "L": 1.0, "m": 0.25, "v": 8.0, "d": 0.3},
                   {"M": 2.5, "L": 1.5, "m": 0.4, "v": 5.0, "d": 0.4}, {"M": 1.8, "L": 0.9, "m": 0.2, "v": 10.0, "d": 0.35}))


def s210_damped_amplitude_decay_time() -> Structure:
    return Structure(
        "S210", "Time for the amplitude of a damped oscillator to fall", "mechanics", "underdamped_envelope_decay_time_to_fraction",
        (_in("m", "mass", "kg", "mass of the block", 0.5, (0.3, 1.5)),
         _in("b", "damping_coefficient", "kg/s", "damping coefficient of the damper", 0.2, (0.1, 0.6)),
         _in("f", "fraction", "1", "fraction of the initial amplitude that the amplitude falls to", 0.2, (0.05, 0.5)),
         _co("tau", "time", "s", "time for the amplitude to fall by the factor e", "2*m/b"),
         _co("Lf", "dimensionless", "1", "natural logarithm of the ratio of the initial amplitude to the final amplitude", "log(1/f)"),
         _co("t", "time", "s", "time for the amplitude to fall to the fraction", "tau*Lf")),
        "t",
        (Assumption("A-damper", "The damper exerts a force proportional to the speed of the block, and the spring is ideal.", "modelling",
                    ("m", "b")),
         Assumption("A-light", "The damping is light, so the block oscillates many times; the amplitude is the height of the envelope of the "
                               "displacement, which falls exponentially, and the block is released from rest.", "boundary_condition", ("f",))),
        _spec("A block of mass {m} kg on a horizontal frictionless track is attached to a spring and to a damper that exerts a force proportional "
              "to the speed of the block, with damping coefficient {b} kg/s. The damping is light, so the block oscillates and the amplitude of "
              "the oscillation, the height of the envelope of the displacement, falls with time. The spring is light and ideal, and air resistance is negligible. The block is pulled aside and released from rest.",
              "How long after the release does the amplitude of the oscillation first fall to the fraction {f} of its initial value?",
              "time for the amplitude to fall to the stated fraction", "s",
              "A separate pendulum B on another stand takes {v} {u} to settle, but it is unrelated to this block.",
              "A reference oscillator B takes {v} {u} for its amplitude to fall.",
              "A separate stopwatch B reads {v} {u}, but it plays no part in the decay of the block.", "W", equivalent="ms"),
        ("m", 1.5), _solve_decay_time, 3,
        "the envelope equation integrated from the unit amplitude until the amplitude falls to the stated fraction",
        solver_rel_tol=1e-6,
        instances=({"m": 0.5, "b": 0.2, "f": 0.2}, {"m": 0.4, "b": 0.3, "f": 0.25}, {"m": 0.8, "b": 0.25, "f": 0.1},
                   {"m": 0.6, "b": 0.5, "f": 0.15}))


ALL = (s201_driven_damped_amplitude, s202_rocket_final_speed, s203_bead_on_rotating_hoop, s204_skaters_right_angle_collision,
       s205_turntable_spin_up_friction, s206_spun_up_tank_axis_depth, s207_double_atwood_machine, s208_disc_dropped_on_disc,
       s209_rod_struck_by_clay, s210_damped_amplitude_decay_time)


def all_structures() -> list[Structure]:
    return [factory() for factory in ALL]


STRUCTURES: dict[str, Structure] = {s.structure_id: s for s in all_structures()}

LEVELS: dict[str, str] = {
    "S201": "upper_university", "S202": "intro_university", "S203": "upper_university", "S204": "intro_university",
    "S205": "intro_university", "S206": "upper_university", "S207": "upper_university", "S208": "intro_university",
    "S209": "upper_university", "S210": "intro_university",
}

TOPICS: dict[str, str] = {
    "S201": "driven damped oscillator, resonance curve", "S202": "variable mass, rocket equation", "S203": "Lagrangian mechanics, rotating frame",
    "S204": "two-dimensional inelastic collision", "S205": "circular motion with angular acceleration, friction", "S206": "non-inertial frame, rotating liquid",
    "S207": "Atwood machines, constraints", "S208": "rotational collision, angular momentum and energy", "S209": "rigid-body collision, angular momentum",
    "S210": "damped oscillations, envelope",
}

# --- gold solution plans -------------------------------------------------------------------------------------------------------------

PLANS: dict[str, Plan] = {
    "S201": Plan(
        approach="After the transient has died out the block oscillates at the driving frequency with a constant amplitude. Write the equation of "
                 "motion with the spring, damper and driving force, find the natural frequency and damping rate, and use the magnitude of the "
                 "response function at the driving frequency.",
        steps=(
            Step("w0sq", "Natural angular frequency of the undamped oscillator: omega_0^2 = k / m",
                 "The spring and the mass alone fix the natural frequency; the response is compared with the driving frequency through this "
                 "number."),
            Step("gam", "Damping rate of a block with a viscous damper: gamma = b / m, from m x'' + b x' + k x = F0 cos(w t)",
                 "Dividing the equation of motion by the mass gives the damping term b x' / m, so b / m is the rate that enters the response."),
            Step("den", "Steady-state response of a driven damped oscillator: the denominator is sqrt((omega_0^2 - w^2)^2 + (gamma w)^2)",
                 "Trying x = A cos(w t - delta) in the equation of motion and matching the in-phase and quadrature terms gives the magnitude of "
                 "this denominator; it is smallest near resonance, where the amplitude is largest."),
            Step("A", "Amplitude of the steady state: A = (F0 / m) / sqrt((omega_0^2 - w^2)^2 + (gamma w)^2)",
                 "The force per unit mass divided by the magnitude of the denominator gives the amplitude of the displacement."),
        ),
        check="For a very low driving frequency the amplitude tends to F0 / k, and it is largest near the natural frequency; units: N over "
              "kg times s^-2 give m."),
    "S202": Plan(
        approach="No external force acts, so the momentum of the rocket and its exhaust is conserved. Applying this to the rocket as its mass falls "
                 "gives the rocket equation; the final speed depends on the exhaust speed and on the ratio of the initial to the final mass.",
        steps=(
            Step("m0", "Mass bookkeeping: the initial mass is the empty mass plus the fuel, m0 = md + mf",
                 "The rocket starts with all its fuel on board, so its initial mass is the sum of the empty mass and the fuel mass."),
            Step("ratio", "Mass ratio of the rocket equation: the initial mass divided by the final mass, which is the empty mass once the fuel is burned",
                 "After all the fuel has been burned only the empty mass remains, so the ratio m0 / md measures how much the mass has fallen."),
            Step("vf", "Tsiolkovsky rocket equation: from m dv = -u dm for a constant exhaust speed u relative to the rocket, v = u ln(m0 / mfinal)",
                 "With no external force the rocket gains speed du per unit of mass ejected backwards at speed u relative to it; integrating "
                 "from the start at rest to the final mass gives the logarithm, and the burn rate drops out."),
        ),
        check="With no fuel the speed is zero, and the speed grows only logarithmically with the fuel: doubling the fuel does not double the speed. "
              "Units: km/s times a dimensionless logarithm give km/s."),
    "S203": Plan(
        approach="Work in the frame of the hoop, where the bead feels gravity and the centrifugal force. Find the equilibrium angle from the "
                 "condition that the effective potential is stationary, then expand the Lagrangian to second order in the displacement.",
        steps=(
            Step("c0", "Stationary point of the effective potential from the Lagrangian L = m R^2 (theta'^2 + Om^2 sin^2 theta) / 2 + m g R cos theta: "
                       "cos theta_0 = g / (Om^2 R)",
                 "Setting the generalized force sin theta (Om^2 cos theta - g / R) to zero away from the axis gives this equilibrium; it exists "
                 "only if Om^2 R > g, which holds for the stated rotation."),
            Step("s0", "Trigonometric identity: sin theta_0 = sqrt(1 - cos^2 theta_0)",
                 "The curvature of the effective potential is needed at the equilibrium angle and involves its sine."),
            Step("ws", "Small oscillations: theta'' = -Om^2 sin^2 theta_0 (theta - theta_0), so the angular frequency is Om sin theta_0",
                 "Expanding the equation of motion to first order about the equilibrium gives a harmonic equation whose stiffness per unit "
                 "inertia is Om^2 sin^2 theta_0; the mass of the bead has divided out."),
            Step("T", "Period of a harmonic oscillation, T = 2 pi / omega",
                 "The small oscillations are harmonic, so the period is two pi over their angular frequency."),
        ),
        check="As the rotation rate grows, sin theta_0 tends to one and the period tends to 2 pi / Om; near the critical rate the period grows "
              "without limit, because the restoring force vanishes."),
    "S204": Plan(
        approach="The momentum of the system is conserved in the collision; the two perpendicular components give the velocity after it. The "
                 "kinetic energy converted is the energy before minus the energy after.",
        steps=(
            Step("px", "Momentum of the eastward skater, p = m1 v1", "Only this skater moves east, so it carries all the eastward momentum."),
            Step("py", "Momentum of the northward skater, p = m2 v2", "Only this skater moves north, so it carries all the northward momentum."),
            Step("M", "Total mass of a system that moves as one body after the collision, M = m1 + m2",
                 "The skaters hold on to each other, so the final momentum is carried by the combined mass."),
            Step("Vf", "Conservation of momentum for each perpendicular component: the final speed is the magnitude of the vector sum divided by M",
                 "The two components are perpendicular, so the magnitude of the total momentum is the root of the sum of squares; dividing by "
                 "the total mass gives the final speed."),
            Step("Ki", "Kinetic energy of the system before the collision, the sum of (1/2) m v^2 for each skater",
                 "Kinetic energy is a scalar, so the two skaters' energies add whatever their directions."),
            Step("Kf", "Kinetic energy of the combined body after the collision, (1/2) M Vf^2",
                 "After the collision the two skaters move together at the final speed."),
            Step("dK", "Energy accounting: the kinetic energy converted to other forms is the initial minus the final kinetic energy",
                 "Momentum is conserved but kinetic energy is not in a perfectly inelastic collision; the difference goes into deformation and heat."),
        ),
        check="The result equals one half of the reduced mass times the square of the relative speed, which is independent of the frame of the "
              "observer; it is positive, as it must be for an inelastic collision."),
    "S205": Plan(
        approach="The coin has not slipped, so its acceleration equals that of the point of the turntable under it. That acceleration has a "
                 "centripetal part from the angular speed at the given time and a tangential part from the angular acceleration; the friction "
                 "force is the mass times the vector sum.",
        steps=(
            Step("w", "Rotational kinematics with constant angular acceleration from rest: w = alpha t",
                 "The angular speed at the given time fixes the centripetal acceleration of the coin."),
            Step("ac", "Centripetal acceleration of circular motion, a_c = w^2 r",
                 "The coin moves on a circle of radius r at the angular speed found, so it needs this acceleration toward the axis."),
            Step("at", "Tangential acceleration of a point at radius r with angular acceleration alpha, a_t = alpha r",
                 "The turntable is speeding up, so the coin also needs an acceleration along its path."),
            Step("f", "Newton's second law for the coin: the friction force is m times the vector sum of the two perpendicular accelerations",
                 "The only horizontal force on the coin is static friction, so it must supply both accelerations; the two are perpendicular "
                 "and combine as the root of the sum of squares."),
        ),
        check="With no angular acceleration the result reduces to m w^2 r; units: kg times m/s^2 give N, shown in millinewtons."),
    "S206": Plan(
        approach="In the frame of the rotating tank the liquid is at rest under gravity and the centrifugal force, so its free surface is a "
                 "paraboloid. The volume of the liquid is conserved, which fixes the height of the surface at the axis.",
        steps=(
            Step("dh", "Free surface of a rotating liquid (hydrostatic balance in the rotating frame): z(r) = z0 + w^2 r^2 / (2 g), so the rise "
                       "from axis to wall is w^2 R^2 / (2 g)",
                 "The pressure is constant on the surface, which is perpendicular to the effective gravity; integrating the slope w^2 r / g "
                 "gives the paraboloid and its total rise."),
            Step("hw", "Conservation of the volume of liquid: the mean depth stays h0, and the mean height of a paraboloid above its vertex is "
                       "half of the rise, so the depth at the wall is h0 + dh / 2",
                 "The average of w^2 r^2 / (2 g) weighted by the area is half of its value at the wall, so the surface at the wall is half of "
                 "the rise above the original level."),
            Step("ha", "Depth at the axis from the depth at the wall minus the rise: ha = hw - dh",
                 "The surface is lowest at the axis, below the wall level by the full rise of the paraboloid."),
        ),
        check="With no rotation the result is h0; the liquid is lowered at the axis by half of the rise and raised at the wall by half of it, and "
              "the density of the liquid does not appear."),
    "S207": Plan(
        approach="Treat the movable pulley with its two blocks as one effective mass on the first string. The two blocks on the movable pulley "
                 "give an effective mass 4 m2 m3 / (m2 + m3), and the single block and this effective mass form an ordinary Atwood machine.",
        steps=(
            Step("S", "Sum of the two masses on the second string, m2 + m3", "The reduced-mass type combination of the two blocks needs their sum."),
            Step("mr", "Effective mass of the movable-pulley branch: 4 m2 m3 / (m2 + m3), from the tension relation T1 = 2 T2 of a massless pulley and "
                       "the constraint a_pulley = (a2 + a3) / 2",
                 "The massless movable pulley carries a tension T1 = 2 T2 from the first string, and the blocks on it accelerate relative to it; "
                 "solving the three equations shows the first string sees an inertial mass 4 m2 m3 / (m2 + m3) when the string is taut."),
            Step("a1", "Newton's second law for the Atwood pair: a = g (m1 - mr) / (m1 + mr) for the single block",
                 "The single block and the effective mass hang from one string over the fixed pulley, so the net force over the total mass "
                 "gives the acceleration."),
        ),
        check="If the two blocks are equal, the effective mass is the mass of one of them times two; if the single block has the effective mass "
              "the acceleration is zero, and the answer is below g."),
    "S208": Plan(
        approach="No external torque acts on the two discs about the common axle, so their total angular momentum is conserved while they slip "
                 "and then turn together. The kinetic energy that is lost is the difference between the energy before and after.",
        steps=(
            Step("I1", "Moment of inertia of a uniform solid disc about its axis, I = (1/2) m r^2",
                 "The spinning disc is a uniform solid disc, so its moment of inertia about the axle through its centre follows from its mass "
                 "and radius; this is the number that enters angular momentum and energy."),
            Step("wf", "Conservation of angular momentum about the axle: I1 w1 = (I1 + I2) wf",
                 "The faces exert equal and opposite torques on each other and nothing else exerts a torque, so the sum of the angular "
                 "momenta is unchanged; solving for the common speed gives wf."),
            Step("Ki", "Rotational kinetic energy of a rigid body, K = (1/2) I w^2, for the spinning disc alone",
                 "Before the contact only the first disc turns, so the energy of the system is the energy of that disc."),
            Step("Kf", "Rotational kinetic energy of the two discs turning together, K = (1/2) (I1 + I2) wf^2",
                 "After the coupling the two discs are one rotating body with the combined moment of inertia."),
            Step("dE", "Energy accounting: the mechanical energy that is not kept as rotational kinetic energy is dissipated as heat, dE = Ki - Kf",
                 "Angular momentum is conserved but kinetic energy is not while the faces slip, so the difference is the heat generated."),
        ),
        check="The result equals one half of the reduced moment of inertia I1 I2 / (I1 + I2) times the square of the initial angular speed; it is "
              "positive and does not depend on the friction torque of the faces."),
    "S209": Plan(
        approach="Momentum and angular momentum are conserved in the collision on the smooth table. Find the centre of mass of the combined body, "
                 "its moment of inertia about that point, and the angular momentum about the centre of mass.",
        steps=(
            Step("mt", "Total mass of the combined body, M + m", "The combined body moves as one rigid body after the collision."),
            Step("yc", "Centre of mass of a system of two bodies on a line: the clay sits at distance d from the centre of the rod, so the centre of mass "
                       "is at m d / (M + m) from the centre of the rod",
                 "The rod's centre of mass is at its centre and the clay is a point mass at distance d, so their weighted average sits close "
                 "to the rod's centre."),
            Step("Ic", "Parallel-axis theorem: I = M L^2 / 12 + M yc^2 + m (d - yc)^2 about the centre of mass",
                 "The rod's moment about its own centre is M L^2 / 12, and each body's offset from the combined centre of mass adds its mass "
                 "times the square of the offset."),
            Step("w", "Conservation of angular momentum about the centre of mass: m v (d - yc) = I w",
                 "The clay moves along a line a distance d - yc from the combined centre of mass and the rod is at rest, so this is the "
                 "angular momentum about that point; no external torque acts on the smooth table."),
        ),
        check="If the clay hits the centre of the rod (d = 0) there is no rotation; a faster or heavier lump gives a larger angular speed."),
    "S210": Plan(
        approach="For light damping the displacement is an oscillation inside an envelope that falls exponentially with time constant 2 m / b. "
                 "Find the time constant, and the time at which the envelope has fallen to the stated fraction.",
        steps=(
            Step("tau", "Envelope of a lightly damped oscillator: A(t) = A0 exp(-b t / (2 m)), so the time constant is 2 m / b",
                 "The equation of motion m x'' + b x' + k x = 0 has solutions exp(-b t / 2m) cos(w_d t) when it is underdamped; the spring "
                 "constant sets only the oscillation frequency, not the decay rate."),
            Step("Lf", "Natural logarithm of the ratio of the initial to the final amplitude, ln(1 / f)",
                 "Setting exp(-t / tau) equal to the fraction f and taking logarithms gives t = tau ln(1 / f); this factor is that logarithm."),
            Step("t", "Time for the envelope to reach the fraction: t = tau ln(1 / f)",
                 "The envelope falls to f of its initial value when t / tau equals the logarithm found."),
        ),
        check="The amplitude falls by the factor e after one time constant (f = 1/e gives t = tau); the initial amplitude and the spring "
              "constant do not appear."),
}


def _in_dependency_order() -> None:
    """Arrange each plan's steps in the dependency order that `trace.validate_plan` requires (the graph's topological order)."""

    from physmon.benchmark.v2.graph import topological_order

    for sid, plan in list(PLANS.items()):
        order = [n.name for n in topological_order(STRUCTURES[sid]) if n.kind == "computed"]
        PLANS[sid] = Plan(plan.approach, tuple(sorted(plan.steps, key=lambda step: order.index(step.node))), plan.check)


_in_dependency_order()
