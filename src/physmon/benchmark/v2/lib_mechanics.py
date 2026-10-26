"""Classical-mechanics batch of DECOY-v2 structures, S31 to S38, and the gold solution plans for the mechanics structures of the
earlier batches (Stage 14.19; v2 B3 deliverable p.9).

Same pattern as `library_c.py`: a typed graph with input and computed nodes, an independently coded numeric solver for each new structure
(a linear system, an ODE with an event, a root finder, a quadrature), four numeric instantiations and a relevant edit that moves the
answer. The topics are spread over the mechanics curriculum: projectile motion from a cliff, work and energy with a spring and friction,
impulse on a bouncing ball, rolling on an incline, the conical pendulum, the physical pendulum, a circular orbit (from the surface
gravity and the radius of the Earth, so that no gravitational constant is needed) and the statics of a ladder.

`PLANS` holds the gold solving technique (a `trace.Plan`) for every new structure and for the existing mechanics structures listed in the
task; `LEVELS` and `TOPICS` label them. These are agent-authored candidates: solver-certified and agent-verified, not expert-reviewed.
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


def _solve_cliff_throw(v, h, g):
    # Integrate the vertical fall from rest at height h until the stone reaches the ground; the horizontal motion is uniform.
    def landed(t, y):
        return y[0]

    landed.terminal = True
    solution = solve_ivp(lambda t, y: [y[1], -g], (0.0, 200.0), [h, 0.0], events=landed, rtol=1e-11, atol=1e-13)
    return float(v * solution.t_events[0][0])


def _solve_spring_slide(k, x, m, mu, g):
    # Integrate the block from rest at compression x: spring force only while compressed, constant kinetic friction throughout;
    # the distance from the release point at the event "speed back to zero".
    def stopped(t, y):
        return y[1]

    stopped.terminal = True
    stopped.direction = -1

    def rhs(t, y):
        spring = max(-k * y[0], 0.0)
        return [y[1], (spring - mu * m * g) / m]

    solution = solve_ivp(rhs, (0.0, 2000.0), [-x, 0.0], events=stopped, rtol=1e-11, atol=1e-13, max_step=0.05)
    return float(solution.y_events[0][0][0] + x)


def _solve_wall_bounce(m, v, e, dt):
    # The constant force F for which the velocity after the contact time is minus e times the incoming velocity (a root finder
    # on the velocity change obtained by integrating the acceleration -F/m over the contact).
    def velocity_after(force):
        change, _ = quad(lambda t: -force / m, 0.0, dt, epsabs=1e-14, epsrel=1e-13)
        return v + change

    return float(brentq(lambda force: velocity_after(force) + e * v, 0.0, 1.0e9, xtol=1e-12, rtol=1e-14))


def _solve_rolling_up(v0, theta, g):
    # Per unit mass and radius: translation a = f - g sin(theta), rolling torque I a = -f R with I = 2/5 (a linear system in a and f);
    # then the motion is integrated until the speed returns to zero.
    inertia = 0.4
    acc, _ = np.linalg.solve(np.array([[1.0, -1.0], [inertia, 1.0]]), np.array([-g * math.sin(theta), 0.0]))

    def stopped(t, y):
        return y[1]

    stopped.terminal = True
    stopped.direction = -1
    solution = solve_ivp(lambda t, y: [y[1], acc], (0.0, 100.0), [0.0, v0], events=stopped, rtol=1e-11, atol=1e-13)
    return float(solution.y_events[0][0][0])


def _solve_conical(length, theta, g):
    # Per unit mass: T sin(theta) = w / r and T cos(theta) = g with w = v^2 (a linear system in T and w); then 2 pi r / v.
    r = length * math.sin(theta)
    tension, w = np.linalg.solve(np.array([[math.sin(theta), -1.0 / r], [math.cos(theta), 0.0]]), np.array([0.0, g]))
    return float(2.0 * math.pi * r / math.sqrt(w))


def _solve_physical_pendulum(length, d, g):
    # The moment of inertia per unit mass by quadrature over the rod (positions measured from the pivot), then the small-angle
    # equation of motion integrated from rest; four times the first zero crossing is the period.
    inertia, _ = quad(lambda s: s * s / length, d - 0.5 * length, d + 0.5 * length, epsabs=1e-14, epsrel=1e-13)
    omega2 = g * d / inertia

    def crossing(t, y):
        return y[0]

    crossing.terminal = True
    solution = solve_ivp(lambda t, y: [y[1], -omega2 * y[0]], (0.0, 200.0), [0.05, 0.0], events=crossing, rtol=1e-12, atol=1e-14)
    return float(4.0 * solution.t_events[0][0])


def _solve_orbit(radius, g, h):
    # The circular speed as the root of v^2 / r = G M / r^2 with G M = g R^2; then the orbit is integrated from (r, 0) with velocity
    # (0, v) and four times the time to the first crossing of the y axis is the period.
    r = radius + h
    gm = g * radius ** 2
    speed = brentq(lambda v: v * v / r - gm / (r * r), 0.0, 1.0e5, xtol=1e-12, rtol=1e-14)

    def axis(t, y):
        return y[0]

    axis.terminal = True
    axis.direction = -1

    def rhs(t, y):
        rr = math.hypot(y[0], y[1])
        return [y[2], y[3], -gm * y[0] / rr ** 3, -gm * y[1] / rr ** 3]

    solution = solve_ivp(rhs, (0.0, 1.0e5), [r, 0.0, 0.0, speed], events=axis, rtol=1e-12, atol=1e-9)
    return float(4.0 * solution.t_events[0][0])


def _solve_ladder(m, big_m, x, theta, g):
    # Equilibrium of the ladder as a linear system in (wall force, floor friction, floor normal force), with unit length:
    # horizontal balance, vertical balance, torques about the foot. The magnitude of the force of the ground on the ladder.
    matrix = np.array([[-1.0, 1.0, 0.0], [0.0, 0.0, 1.0], [math.sin(theta), 0.0, 0.0]])
    rhs = np.array([0.0, (m + big_m) * g, (0.5 * m + big_m * x) * g * math.cos(theta)])
    wall, friction, normal = np.linalg.solve(matrix, rhs)
    return float(math.hypot(friction, normal))


# --- structures ---------------------------------------------------------------------------------------


def s31_cliff_throw_distance() -> Structure:
    return Structure(
        "S31", "Horizontal distance of a stone thrown from a cliff", "mechanics", "horizontal_launch_cliff_distance",
        (_in("v", "speed", "m/s", "horizontal launch speed of the stone", 15.0, (5.0, 25.0)),
         _in("h", "length", "m", "height of the cliff edge above the ground", 20.0, (10.0, 100.0)),
         _g(),
         _co("t", "time", "s", "time the stone takes to fall to the ground", "sqrt(2*h/g)"),
         _co("dx", "length", "m", "horizontal distance travelled before landing", "v*t")),
        "dx",
        (A_G, Assumption("A-drag", "Air resistance is neglected, so the horizontal velocity is constant.", "modelling", ("v",)),
         Assumption("A-ground", "The ground is level and the stone is thrown exactly horizontally from the edge.", "boundary_condition", ("h",))),
        _spec("A stone is thrown horizontally with a speed of {v} m/s from the edge of a cliff that is {h} m above level ground. "
              "Neglect air resistance and take g = {g} m/s².",
              "What horizontal distance does the stone travel before it hits the ground?", "horizontal distance travelled by the stone", "m",
              "A separate stone B thrown from another cliff lands {v} {u} from its base, but it is unrelated to this stone.",
              "A reference stone B lands {v} {u} from the base of its own cliff.",
              "A separate crate B on the cliff has a mass of {v} {u}, but it plays no part in the throw.", "kg", equivalent="cm"),
        ("h", 1.5), _solve_cliff_throw, 3,
        "the vertical fall from rest integrated with an adaptive ODE solver until the stone reaches the ground, times the horizontal speed",
        solver_rel_tol=1e-6,
        instances=({"v": 15.0, "h": 20.0, "g": 9.8}, {"v": 12.0, "h": 45.0, "g": 9.8}, {"v": 20.0, "h": 30.0, "g": 9.81},
                   {"v": 8.0, "h": 60.0, "g": 9.8}))


def s32_spring_launch_slide() -> Structure:
    return Structure(
        "S32", "Distance a block slides after release from a compressed spring", "mechanics", "spring_launch_friction_slide_distance",
        (_in("k", "spring_constant", "N/m", "spring constant", 800.0, (400.0, 1500.0)),
         _in("x", "length", "cm", "compression of the spring before release", 10.0, (5.0, 20.0)),
         _in("m", "mass", "kg", "mass of the block", 0.5, (0.2, 1.5)),
         _in("mu", "coefficient", "1", "coefficient of kinetic friction between the block and the table", 0.25, (0.1, 0.4)),
         _g(),
         _co("E", "energy", "J", "elastic energy stored in the compressed spring", "k*x**2/2"),
         _co("Ff", "force", "N", "kinetic friction force on the block", "mu*m*g"),
         _co("s", "length", "m", "total distance slid from the release point until the block stops", "E/Ff")),
        "s",
        (A_G, Assumption("A-spring", "The spring is ideal and massless and obeys Hooke's law; the block is not attached to it and separates "
                                      "from it at its natural length.", "modelling", ("k",)),
         Assumption("A-friction", "The table is horizontal and the coefficient of kinetic friction is the same over the whole path, "
                                  "including while the block is in contact with the spring.", "modelling", ("mu", "m")),
         Assumption("A-rest", "The block is released from rest at the stated compression.", "boundary_condition", ("x",))),
        _spec("A block of mass {m} kg rests on a horizontal table against a spring of spring constant {k} N/m that is compressed by "
              "{x} cm. The block is not attached to the spring. When the block is released from rest, the spring pushes it along the "
              "table and it later stops. The coefficient of kinetic friction between the block and the table is {mu}. "
              "Take g = {g} m/s².",
              "What total distance does the block slide from its release point before it stops?", "total distance slid by the block", "m",
              "A separate toy B launched by another spring slides {v} {u} before it stops, but it is unrelated to this block.",
              "A reference block B slides {v} {u} before it stops.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the launch.", "W", equivalent="cm"),
        ("k", 1.25), _solve_spring_slide, 5,
        "the block integrated from rest with a spring force while compressed and constant kinetic friction, until its speed returns to zero",
        solver_rel_tol=1e-6,
        instances=({"k": 800.0, "x": 10.0, "m": 0.5, "mu": 0.25, "g": 9.8}, {"k": 600.0, "x": 12.0, "m": 0.4, "mu": 0.2, "g": 9.8},
                   {"k": 1000.0, "x": 8.0, "m": 0.8, "mu": 0.3, "g": 9.8}, {"k": 500.0, "x": 15.0, "m": 0.3, "mu": 0.15, "g": 9.81}))


def s33_wall_bounce_force() -> Structure:
    return Structure(
        "S33", "Average force of a wall on a bouncing ball", "mechanics", "bounce_average_force_restitution",
        (_in("m", "mass", "g", "mass of the ball", 150.0, (50.0, 500.0)),
         _in("v", "speed", "m/s", "speed of the ball just before it hits the wall", 20.0, (10.0, 40.0)),
         _in("e", "coefficient", "1", "coefficient of restitution, rebound speed divided by approach speed", 0.6, (0.3, 0.9)),
         _in("dt", "time", "ms", "time of contact between the ball and the wall", 8.0, (3.0, 20.0)),
         _co("vout", "speed", "m/s", "speed of the ball just after it leaves the wall", "e*v"),
         _co("J", "impulse", "N*s", "magnitude of the impulse given to the ball by the wall", "m*(v + vout)"),
         _co("F", "force", "N", "magnitude of the average force of the wall on the ball", "J/dt")),
        "F",
        (Assumption("A-wall", "The wall is rigid and fixed, and the ball hits it head-on, moving along one line before and after.", "modelling", ("e", "v")),
         Assumption("A-contact", "The weight of the ball is negligible compared with the force during the short contact, and the average "
                                 "force is the impulse divided by the contact time.", "modelling", ("m", "dt"))),
        _spec("A ball of mass {m} g hits a rigid wall head-on at a speed of {v} m/s and rebounds along the same line. The coefficient of "
              "restitution, the ratio of the rebound speed to the approach speed, is {e}. The ball is in contact with the wall for "
              "{dt} ms. Neglect the weight of the ball during the contact.",
              "What is the magnitude of the average force that the wall exerts on the ball during the contact?",
              "average force of the wall on the ball", "N",
              "A separate ball B hitting another wall feels an average force of {v} {u}, but it is unrelated to this ball.",
              "A reference ball B feels an average force of {v} {u} from its own wall.",
              "A separate stopwatch B reads {v} {u}, but it plays no part in the impact.", "s", equivalent="kN"),
        ("v", 1.25), _solve_wall_bounce, 4,
        "the constant force found with a bracketing root finder so that the velocity after the contact equals minus e times the incoming velocity",
        solver_rel_tol=1e-9,
        instances=({"m": 150.0, "v": 20.0, "e": 0.6, "dt": 8.0}, {"m": 200.0, "v": 15.0, "e": 0.5, "dt": 10.0},
                   {"m": 60.0, "v": 30.0, "e": 0.8, "dt": 5.0}, {"m": 400.0, "v": 12.0, "e": 0.4, "dt": 15.0}))


def s34_rolling_sphere_up_incline() -> Structure:
    return Structure(
        "S34", "Distance a rolling sphere climbs an incline", "mechanics", "rolling_sphere_incline_stopping_distance",
        (_in("v0", "speed", "m/s", "speed of the centre of the sphere at the bottom of the incline", 6.0, (3.0, 15.0)),
         _in("theta", "angle", "deg", "angle of the incline above the horizontal", 25.0, (10.0, 40.0)),
         _g(),
         _co("a", "acceleration", "m/s^2", "magnitude of the deceleration of the sphere along the incline", "5*g*sin(theta)/7"),
         _co("d", "length", "m", "distance travelled up the incline before coming to rest", "v0**2/(2*a)")),
        "d",
        (A_G, Assumption("A-roll", "The sphere is uniform and solid, with moment of inertia (2/5) m R squared about its centre, and it "
                                   "rolls without slipping, so static friction does no work.", "modelling", ("v0",)),
         Assumption("A-loss", "Rolling resistance and air resistance are neglected and the incline is long enough for the sphere to stop on it.",
                    "boundary_condition", ("theta",))),
        _spec("A uniform solid sphere rolls without slipping up a fixed incline that makes an angle of {theta} degrees with the "
              "horizontal. At the bottom of the incline the centre of the sphere moves at {v0} m/s along the incline. Take "
              "g = {g} m/s².",
              "How far along the incline does the sphere travel before it momentarily comes to rest?",
              "distance travelled up the incline", "m",
              "A separate cylinder B on another ramp rolls {v} {u} up its incline, but it is unrelated to this sphere.",
              "A reference sphere B rolls {v} {u} up its own incline.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the rolling.", "W", equivalent="cm"),
        ("v0", 1.25), _solve_rolling_up, 3,
        "translation and rolling-torque equations solved as a linear system for the deceleration, then the motion integrated until the speed is zero",
        solver_rel_tol=1e-6,
        instances=({"v0": 6.0, "theta": 25.0, "g": 9.8}, {"v0": 8.0, "theta": 30.0, "g": 9.8}, {"v0": 5.0, "theta": 15.0, "g": 9.81},
                   {"v0": 10.0, "theta": 35.0, "g": 9.8}))


def s35_conical_pendulum_period() -> Structure:
    return Structure(
        "S35", "Period of a conical pendulum", "mechanics", "conical_pendulum_revolution_period",
        (_in("L", "length", "m", "length of the string", 1.2, (0.5, 3.0)),
         _in("theta", "angle", "deg", "angle between the string and the vertical", 30.0, (15.0, 60.0)),
         _g(),
         _co("r", "length", "m", "radius of the horizontal circle", "L*sin(theta)"),
         _co("v", "speed", "m/s", "speed of the bob", "sqrt(g*r*tan(theta))"),
         _co("T", "time", "s", "time for one revolution of the bob", "2*pi*r/v")),
        "T",
        (A_G, Assumption("A-string", "The string is light and inextensible, the bob is small, and air resistance is neglected.", "modelling", ("L",)),
         Assumption("A-steady", "The bob moves at constant speed in a horizontal circle with the string at a constant angle.", "boundary_condition", ("theta",))),
        _spec("A small bob is attached to a light string of length {L} m. The bob moves at constant speed in a horizontal circle, "
              "with the string making a constant angle of {theta} degrees with the vertical, so that the string sweeps out a cone. "
              "Neglect air resistance and take g = {g} m/s².",
              "What is the time for one complete revolution of the bob?", "time for one revolution of the bob", "s",
              "A separate swing B on another rig has a period of {v} {u}, but it is unrelated to this bob.",
              "A reference pendulum B has a period of {v} {u}.",
              "A separate rope B on another rig is {v} {u} long, but it plays no part in the motion.", "m", equivalent="ms"),
        ("L", 1.5), _solve_conical, 3,
        "the force balance on the bob solved as a linear system for the tension and the squared speed, then the period as the circumference over the speed",
        solver_rel_tol=1e-9,
        instances=({"L": 1.2, "theta": 30.0, "g": 9.8}, {"L": 0.8, "theta": 45.0, "g": 9.8}, {"L": 2.0, "theta": 20.0, "g": 9.8},
                   {"L": 1.5, "theta": 55.0, "g": 9.81}))


def s36_rod_physical_pendulum() -> Structure:
    return Structure(
        "S36", "Period of a uniform rod swinging about an off-centre pivot", "mechanics", "physical_pendulum_rod_period",
        (_in("L", "length", "m", "length of the rod", 1.2, (1.0, 2.5)),
         _in("d", "length", "m", "distance from the pivot to the centre of the rod", 0.3, (0.05, 0.45)),
         _g(),
         _co("kk", "moment_of_inertia_per_mass", "m^2", "moment of inertia about the pivot per unit mass of the rod", "L**2/12 + d**2"),
         _co("omega", "angular_frequency", "rad/s", "angular frequency of small oscillations", "sqrt(g*d/kk)"),
         _co("T", "time", "s", "period of small oscillations", "2*pi/omega")),
        "T",
        (A_G, Assumption("A-rod", "The rod is thin and uniform, and the pivot is a fixed horizontal axis perpendicular to the rod.", "modelling", ("L", "d")),
         Assumption("A-small", "The amplitude is small, so that sin(angle) equals the angle, and pivot friction and air resistance are neglected.",
                    "modelling", ("d",))),
        _spec("A thin uniform rod of length {L} m is hung from a fixed horizontal axis that is perpendicular to the rod and passes through a "
              "point on the rod {d} m from its centre. The rod swings in a vertical plane with a small amplitude. The pivot is "
              "frictionless and air resistance is negligible. Take g = {g} m/s².",
              "What is the period of the small oscillations of the rod?", "period of the small oscillations", "s",
              "A separate pendulum clock B has a period of {v} {u}, but it is unrelated to this rod.",
              "A reference rod B has a period of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the swing.", "W", equivalent="ms"),
        ("L", 1.25), _solve_physical_pendulum, 3,
        "the moment of inertia by quadrature over the rod, then the small-angle equation of motion integrated until the first zero crossing",
        solver_rel_tol=1e-6,
        instances=({"L": 1.2, "d": 0.3, "g": 9.8}, {"L": 1.0, "d": 0.25, "g": 9.8}, {"L": 1.5, "d": 0.4, "g": 9.8},
                   {"L": 2.0, "d": 0.45, "g": 9.81}))


def s37_circular_orbit_period() -> Structure:
    return Structure(
        "S37", "Orbital period of a low Earth satellite", "mechanics", "circular_orbit_period_from_surface_gravity",
        (_in("R", "length", "km", "radius of the Earth, a stated constant", 6371.0, (6300.0, 6400.0), provenance="assumed"),
         _in("g", "acceleration", "m/s^2", "gravitational acceleration at the surface of the Earth, a stated constant", 9.8, (9.7, 9.9),
             provenance="assumed"),
         _in("h", "length", "km", "altitude of the orbit above the surface", 400.0, (200.0, 5000.0)),
         _co("r", "length", "km", "radius of the orbit, measured from the centre of the Earth", "R + h"),
         _co("v", "speed", "km/s", "orbital speed of the satellite", "sqrt(g*R**2/r)"),
         _co("T", "time", "min", "orbital period of the satellite", "2*pi*r/v")),
        "T",
        (Assumption("A-earth", "The Earth is a uniform sphere of the stated radius, its rotation is neglected, and g is the stated value at its surface.",
                    "modelling", ("R", "g")),
         Assumption("A-orbit", "The orbit is circular, and only the gravity of the Earth acts on the satellite (no drag, Moon or Sun).",
                    "boundary_condition", ("h",))),
        _spec("A satellite moves in a circular orbit {h} km above the surface of the Earth. Take the Earth to be a uniform sphere of "
              "radius {R} km with a gravitational acceleration of {g} m/s² at its surface, and neglect air drag and the gravity of "
              "other bodies.",
              "What is the orbital period of the satellite, in minutes?", "orbital period of the satellite", "min",
              "A separate satellite B in another orbit has a period of {v} {u}, but it is unrelated to this one.",
              "A reference satellite B has an orbital period of {v} {u}.",
              "A separate telescope B is rated at {v} {u}, but it plays no part in the orbit.", "W", equivalent="s"),
        ("h", 3.0), _solve_orbit, 3,
        "the circular speed from a root finder on v squared over r equal to g R squared over r squared, then the orbit integrated to its first axis crossing",
        solver_rel_tol=1e-6,
        instances=({"R": 6371.0, "g": 9.8, "h": 400.0}, {"R": 6371.0, "g": 9.81, "h": 800.0}, {"R": 6378.0, "g": 9.8, "h": 1500.0},
                   {"R": 6360.0, "g": 9.8, "h": 300.0}))


def s38_ladder_ground_force() -> Structure:
    return Structure(
        "S38", "Force of the ground on a ladder with a person on it", "mechanics", "ladder_equilibrium_ground_force",
        (_in("m", "mass", "kg", "mass of the ladder", 12.0, (8.0, 25.0)),
         _in("M", "mass", "kg", "mass of the person", 70.0, (50.0, 100.0)),
         _in("x", "fraction", "1", "fraction of the ladder length, measured from the foot, at which the person stands", 0.6, (0.2, 0.9)),
         _in("theta", "angle", "deg", "angle between the ladder and the ground", 62.0, (50.0, 75.0)),
         _g(),
         _co("Fwall", "force", "N", "horizontal force of the wall on the ladder", "(m/2 + M*x)*g/tan(theta)"),
         _co("Ngnd", "force", "N", "vertical (normal) force of the ground on the ladder", "(m + M)*g"),
         _co("F", "force", "N", "magnitude of the total force of the ground on the ladder", "sqrt(Fwall**2 + Ngnd**2)")),
        "F",
        (A_G, Assumption("A-ladder", "The ladder is uniform, so its weight acts at its midpoint, and the wall is smooth, so it exerts only a horizontal force.",
                         "modelling", ("m",)),
         Assumption("A-equilibrium", "The ladder and the person are at rest in equilibrium; the person stands at the stated point.",
                    "boundary_condition", ("M", "x", "theta"))),
        _spec("A uniform ladder of mass {m} kg leans against a smooth vertical wall and rests on rough horizontal ground, making an angle "
              "of {theta} degrees with the ground. A person of mass {M} kg stands on the ladder at a fraction {x} of its length, "
              "measured from its foot. The ladder does not slip. Take g = {g} m/s².",
              "What is the magnitude of the total force that the ground exerts on the ladder?", "total force of the ground on the ladder", "N",
              "A separate ladder B in another yard feels a ground force of {v} {u}, but it is unrelated to this ladder.",
              "A reference ladder B feels a ground force of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the equilibrium.", "W", equivalent="kN"),
        ("M", 1.25), _solve_ladder, 5,
        "the force and torque equilibrium conditions solved as a linear system for the wall force, the friction and the normal force",
        solver_rel_tol=1e-9,
        instances=({"m": 12.0, "M": 70.0, "x": 0.6, "theta": 62.0, "g": 9.8}, {"m": 15.0, "M": 60.0, "x": 0.5, "theta": 60.0, "g": 9.8},
                   {"m": 10.0, "M": 80.0, "x": 0.7, "theta": 65.0, "g": 9.81}, {"m": 20.0, "M": 55.0, "x": 0.4, "theta": 55.0, "g": 9.8}))


ALL = (s31_cliff_throw_distance, s32_spring_launch_slide, s33_wall_bounce_force, s34_rolling_sphere_up_incline,
       s35_conical_pendulum_period, s36_rod_physical_pendulum, s37_circular_orbit_period, s38_ladder_ground_force)


def all_structures() -> list[Structure]:
    return [factory() for factory in ALL]


# --- gold solution plans -----------------------------------------------------------------------------
# A plan names the law behind each computed node and why it applies; the numbers are rendered from the graph by `trace.render_trace`.

PLANS: dict[str, Plan] = {
    # ---- new structures ----
    "S31": Plan(
        approach="The stone is a projectile, so its vertical and horizontal motions are independent. The vertical fall from the cliff edge fixes how "
                 "long the stone is in the air; the constant horizontal speed over that time then gives the horizontal distance.",
        steps=(
            Step("t", "Constant-acceleration kinematics for the vertical motion: the fall distance from rest is h = (1/2) g t^2",
                 "The stone is thrown horizontally, so it starts with zero vertical velocity and falls the height h with acceleration g; "
                 "solving h = g t^2 / 2 for t gives the time to reach the ground, which does not depend on the horizontal speed."),
            Step("dx", "Uniform motion in the horizontal direction: with no horizontal force the horizontal velocity is constant, so distance = speed x time",
                 "The time of flight found from the vertical motion is also the time during which the stone moves horizontally at the launch "
                 "speed, so the product of the two is the horizontal distance travelled before landing."),
        ),
        check="The distance grows with the launch speed and with the square root of the height, and it vanishes for a zero height. As a "
              "magnitude check, a fall of about 5 m takes about 1 s, so from such a height the stone lands roughly one second times its launch "
              "speed away; the units m/s times s give m."),
    "S32": Plan(
        approach="Use the work-energy theorem for the whole motion from release to rest: all the energy stored in the compressed spring is "
                 "removed by the work of kinetic friction. So find the stored energy, the friction force, and the path length over which "
                 "friction must act to remove that energy.",
        steps=(
            Step("E", "Elastic potential energy of an ideal spring (Hooke's law): U = (1/2) k x^2 for a compression x",
                 "The block starts at rest, so the only energy at the start is the energy stored in the compressed spring; this is the "
                 "energy that is available to be dissipated by friction."),
            Step("Ff", "Law of kinetic friction: f = mu N, with N = m g for a block on a horizontal surface",
                 "The block slides on a horizontal table, so the normal force balances its weight and the kinetic friction force is "
                 "constant for the whole path, whether or not the block is still touching the spring."),
            Step("s", "Work-energy theorem: change of kinetic energy = net work, here 0 = U - f s for a block that starts and ends at rest",
                 "The kinetic energy is zero at the release and at the stop, so the energy stored in the spring equals the work done by "
                 "the constant friction force over the path length; dividing the stored energy by the friction force gives that length."),
        ),
        check="A stiffer spring or a larger compression gives a longer slide, and a rougher table or a heavier block gives a shorter one; "
              "with no friction the block would never stop in this model. The result must exceed the compression, because the block "
              "has to leave the spring, and joules divided by newtons give metres."),
    "S33": Plan(
        approach="The wall changes the momentum of the ball, so apply the impulse-momentum theorem along the line of motion: first the "
                 "rebound speed from the coefficient of restitution, then the impulse as the change of momentum (the direction reverses), "
                 "and finally the average force as the impulse divided by the contact time.",
        steps=(
            Step("vout", "Definition of the coefficient of restitution for a collision with a fixed wall: e = rebound speed / approach speed",
                 "The wall does not move, so the ratio of the speeds after and before the impact is e; this gives the speed with which "
                 "the ball leaves the wall, which is needed for the change of momentum."),
            Step("J", "Impulse-momentum theorem: the impulse J equals the change of momentum, J = m (v_final - v_initial)",
                 "The ball reverses direction, so the velocity changes from +v to -vout and the magnitude of the change is v + vout, "
                 "not their difference; multiplying by the mass gives the magnitude of the impulse. Gravity is negligible during the contact."),
            Step("F", "Definition of the average force: F_avg = J / (contact time), since the impulse is the time integral of the force",
                 "The impulse is the area under the force-time curve, so dividing the impulse by the contact time gives the constant force "
                 "that would deliver the same impulse, that is, the average force exerted by the wall."),
        ),
        check="The answer must lie between m v / dt (a ball that stops dead, e = 0) and 2 m v / dt (a perfectly elastic bounce, e = 1). "
              "The units N s divided by s give N, and a lighter, slower ball or a longer contact gives a smaller force."),
    "S34": Plan(
        approach="A rolling sphere slows down on the way up because gravity pulls it down the slope while static friction also turns the "
                 "spin down. Find the constant deceleration from the translational and rotational equations of motion with the rolling "
                 "condition, then use constant-acceleration kinematics to find the distance at which the sphere stops.",
        steps=(
            Step("a", "Newton's second law for the centre of mass (m a = m g sin(theta) - f), the rotational law (I alpha = f R with I = (2/5) m R^2) "
                      "and the rolling condition a = alpha R",
                 "Static friction f acts up the slope and the sphere rolls without slipping, so the rotational law gives f = (2/5) m a; "
                 "substituting into the translational equation gives (7/5) a = g sin(theta). The sphere is therefore slowed at 5/7 of "
                 "the rate of a frictionless sliding body."),
            Step("d", "Constant-acceleration kinematics: v_final^2 = v0^2 - 2 a d with v_final = 0",
                 "The deceleration is constant, and at the highest point of the motion the speed of the centre is zero; solving "
                 "0 = v0^2 - 2 a d for d gives the distance travelled along the incline."),
        ),
        check="Energy check: the initial kinetic energy (1/2) m v0^2 (1 + 2/5) equals m g d sin(theta), giving the same d = 7 v0^2 / (10 g sin(theta)). "
              "The answer does not depend on the mass or the radius, and it is 7/5 times the distance that a frictionless sliding block would travel."),
    "S35": Plan(
        approach="The bob moves in a horizontal circle, so the net force on it is horizontal and points to the centre. Resolve the string "
                 "tension into a vertical part that balances the weight and a horizontal part that supplies the centripetal force; that gives "
                 "the speed, and the period follows from the circumference of the circle.",
        steps=(
            Step("r", "Geometry of the cone: a string of length L at angle theta to the vertical sweeps a horizontal circle of radius r = L sin(theta)",
                 "The radius of the circle is needed both in the centripetal condition and in the circumference, and it is the horizontal "
                 "projection of the string."),
            Step("v", "Newton's second law with uniform circular motion: vertically T cos(theta) = m g, horizontally T sin(theta) = m v^2 / r",
                 "The vertical component of the tension balances the weight and the horizontal component is the centripetal force; dividing "
                 "the two equations eliminates the tension and the mass and gives v^2 = g r tan(theta)."),
            Step("T", "Uniform circular motion: period = circumference / speed, T = 2 pi r / v",
                 "The bob covers one circle of length 2 pi r at the constant speed v, so the time for one revolution follows directly "
                 "from the radius and the speed found above."),
        ),
        check="The closed form is T = 2 pi sqrt(L cos(theta) / g): as theta tends to zero it tends to the small-angle pendulum period "
              "2 pi sqrt(L / g), and for larger angles the period is shorter. It does not depend on the mass of the bob."),
    "S36": Plan(
        approach="A rigid body swinging about a fixed pivot obeys the rotational form of Newton's second law. For a small angle the restoring "
                 "torque is proportional to the angle, so the motion is simple harmonic; the period then follows from the moment of inertia "
                 "about the pivot, which comes from the parallel-axis theorem.",
        steps=(
            Step("kk", "Moment of inertia of a thin uniform rod about its centre, I_cm = m L^2 / 12, and the parallel-axis theorem, I = I_cm + m d^2 (per unit mass)",
                 "The rod turns about the pivot, which is a distance d from its centre, not about its centre, so the moment of inertia "
                 "about the pivot is needed. The mass appears in both the inertia and the torque and cancels, so only I / m = L^2/12 + d^2 matters."),
            Step("omega", "Rotational second law for a small angle: I theta'' = -m g d sin(theta) = -m g d theta, so the motion is simple harmonic with omega^2 = m g d / I",
                 "The weight acts at the centre of the rod, a distance d from the pivot, and gives a restoring torque proportional to "
                 "sin(theta), which equals theta for small angles; the equation of motion is then that of a harmonic oscillator, with "
                 "angular frequency sqrt(g d / (I / m))."),
            Step("T", "Relation between the period and the angular frequency of simple harmonic motion: T = 2 pi / omega",
                 "One full oscillation corresponds to a phase advance of 2 pi, so the period is 2 pi divided by the angular frequency of "
                 "the small oscillations just found."),
        ),
        check="Taking L to zero gives the simple-pendulum period 2 pi sqrt(d / g) for a point mass; the extra term L^2 / 12 lengthens the period. "
              "A rod pivoted at its end (d = L/2) gives 2 pi sqrt(2 L / (3 g)), which agrees with the general formula."),
    "S37": Plan(
        approach="Gravity supplies the centripetal force of a circular orbit. The surface gravity and the radius of the Earth give the "
                 "product G M = g R^2, so no value of G is needed; find the orbital radius, then the orbital speed from Newton's second law, "
                 "then the period as the circumference divided by the speed.",
        steps=(
            Step("r", "Geometry: gravity depends on the distance from the centre of the Earth, so the orbital radius is r = R + h",
                 "The altitude h is measured from the surface, while the law of gravitation uses the distance from the centre of the Earth, "
                 "so the radius of the Earth must be added."),
            Step("v", "Newton's law of gravitation with Newton's second law for circular motion: G M m / r^2 = m v^2 / r, with G M = g R^2 from the surface gravity",
                 "At the surface g = G M / R^2, so G M = g R^2 and the product G M is known; setting gravity equal to the centripetal "
                 "force gives v = sqrt(G M / r) = sqrt(g R^2 / r), independent of the mass of the satellite."),
            Step("T", "Uniform circular motion: period = circumference / speed, T = 2 pi r / v (equivalent to Kepler's third law)",
                 "The satellite moves around a circle of length 2 pi r at the constant speed v, so the time for one orbit follows directly; "
                 "the result is converted from seconds to minutes."),
        ),
        check="For h = 0 the period is 2 pi sqrt(R / g), about 84 minutes, the shortest possible period around the Earth; the period grows as "
              "r to the power 3/2 (Kepler's third law). A satellite a few hundred kilometres up has a period of about 90 minutes."),
    "S38": Plan(
        approach="The ladder is in static equilibrium, so the net force and the net torque on it are zero. Take torques about the foot to "
                 "eliminate the unknown ground forces and find the force of the smooth wall; the vertical balance gives the normal force of "
                 "the ground; the horizontal balance makes the friction equal to the wall force; the total ground force combines the two.",
        steps=(
            Step("Fwall", "Condition of rotational equilibrium: the net torque about the foot of the ladder is zero",
                 "The smooth wall pushes horizontally at the top with lever arm L sin(theta), the weight of the ladder acts at L/2 and that of "
                 "the person at x L, with horizontal lever arms L cos(theta)/2 and x L cos(theta); the ground forces act at the foot and give no "
                 "torque. So N_w L sin(theta) = (m/2 + M x) g L cos(theta), which gives N_w."),
            Step("Ngnd", "Condition of translational equilibrium in the vertical direction: the normal force balances the total weight",
                 "A smooth wall can exert no vertical force, so the normal force of the ground alone supports the weights of the ladder "
                 "and the person, N_f = (m + M) g."),
            Step("F", "Translational equilibrium in the horizontal direction (friction f = N_w) and vector addition of the perpendicular components, F = sqrt(f^2 + N_f^2)",
                 "The ground exerts on the foot both the normal force and a horizontal friction force, which must cancel the wall force; "
                 "the question asks for the magnitude of their resultant, found with the Pythagorean theorem."),
        ),
        check="The resultant must exceed the total weight (m + M) g, because friction adds a horizontal part, and it tends to the total "
              "weight as the ladder becomes vertical (the wall force then tends to zero). The wall force rises as the person climbs higher."),
    # ---- existing structures ----
    "S01": Plan(
        approach="Apply Newton's second law to each hanging block and the rotational form of the second law to the pulley, with the string "
                 "not slipping. Combining them gives one equation of motion for the whole system, in which the pulley adds an effective mass.",
        steps=(
            Step("m_eff", "Newton's second law for each block, the rotational law tau = I alpha with I = (1/2) M R^2 for the disc, and the no-slip condition a = alpha R",
                 "The two tensions differ because the pulley has inertia: (T2 - T1) R = (1/2) M R^2 (a / R), so T2 - T1 = (M/2) a. Adding "
                 "the block equations then shows that the whole system accelerates as if it had the inertial mass m1 + m2 + M/2."),
            Step("a", "Newton's second law for the system: net driving force = effective mass x acceleration",
                 "The net force along the string is the difference of the weights, (m2 - m1) g, and it must accelerate the effective "
                 "inertial mass; dividing gives the common acceleration of the blocks."),
        ),
        check="Taking M to zero gives the ideal Atwood result (m2 - m1) g / (m1 + m2), and equal masses give zero acceleration. The acceleration "
              "is always smaller than g, and the units N / kg give m/s^2."),
    "S02": Plan(
        approach="Find the constant acceleration of the block along the incline from the force components and kinetic friction, then use "
                 "constant-acceleration kinematics from rest to get the speed after the stated distance.",
        steps=(
            Step("a", "Newton's second law along the incline with the friction law f = mu N, where N = m g cos(theta)",
                 "Along the slope the weight component m g sin(theta) drives the block down and kinetic friction mu m g cos(theta) opposes "
                 "it; dividing the net force by the mass gives the acceleration, which does not depend on the mass."),
            Step("v", "Constant-acceleration kinematics from rest: v^2 = 2 a d (equivalently the work-energy theorem)",
                 "The acceleration is constant and the block starts from rest, so after sliding the distance d the speed follows from "
                 "v^2 = 2 a d."),
        ),
        check="With mu = 0 the speed is sqrt(2 g d sin(theta)), the frictionless result, and friction lowers it. The block slides only if "
              "tan(theta) exceeds mu, which holds in the stated range; the units sqrt(m/s^2 m) give m/s."),
    "S03": Plan(
        approach="Both the momentum and the kinetic energy of the two carts are conserved in a perfectly elastic collision on a frictionless "
                 "track, which gives two equations for the two final velocities. Solving them gives the velocity of the first cart.",
        steps=(
            Step("v1f", "Conservation of linear momentum, m1 v1 + m2 v2 = m1 v1f + m2 v2f, and conservation of kinetic energy for an elastic collision (equivalently, the relative speed of approach equals the relative speed of separation)",
                 "No external horizontal force acts and no energy is lost, so the two conservation laws hold; using the equal relative speeds "
                 "in place of the energy equation makes the system linear, and eliminating v2f gives v1f = ((m1 - m2) v1 + 2 m2 v2) / (m1 + m2)."),
        ),
        check="For equal masses the carts exchange velocities, and for v2 = 0 the formula gives (m1 - m2) v1 / (m1 + m2). After finding both final "
              "velocities one can verify that the total momentum and the total kinetic energy are unchanged."),
    "S04": Plan(
        approach="The block on an ideal spring moves in simple harmonic motion, so find the angular frequency from the spring constant and "
                 "the mass, and use the fact that the maximum speed occurs at the equilibrium position and equals the angular frequency times "
                 "the amplitude.",
        steps=(
            Step("omega", "Hooke's law F = -k x with Newton's second law, m x'' = -k x, which is simple harmonic motion with omega = sqrt(k / m)",
                 "The spring is the only horizontal force on the block on the frictionless table, so the equation of motion is that of a "
                 "harmonic oscillator, and the angular frequency depends only on k and m."),
            Step("v", "Simple harmonic motion: x = A cos(omega t), so the maximum speed is omega A (at the equilibrium position)",
                 "The block is released from rest at the displacement x, so x is the amplitude; the speed is greatest when the block passes "
                 "the equilibrium point, where all the elastic energy has become kinetic energy."),
        ),
        check="Energy check: (1/2) m v^2 = (1/2) k x^2 gives the same v = x sqrt(k / m). A stiffer spring or a larger displacement gives a "
              "larger speed, a heavier block a smaller one; the units m x rad/s give m/s."),
    "S05": Plan(
        approach="Find the moment of inertia of the disc about its axis, then apply the rotational form of Newton's second law to the net "
                 "torque (driving torque minus friction torque) to get the angular acceleration.",
        steps=(
            Step("Inertia", "Moment of inertia of a uniform solid disc about its central axis: I = (1/2) m r^2",
                 "The disc is uniform and solid and turns about its centre, so this standard result gives the rotational inertia that "
                 "resists the net torque."),
            Step("alpha", "Rotational form of Newton's second law: tau_net = I alpha",
                 "The driving torque and the opposing friction torque both act about the axis, so the net torque is their difference; "
                 "dividing it by the moment of inertia gives the angular acceleration."),
        ),
        check="With zero friction torque the result is tau / I, and doubling the mass halves the angular acceleration. The units N m / (kg m^2) "
              "give 1/s^2, that is rad/s^2, and the answer is positive because the driving torque is larger than the friction torque."),
    "S10": Plan(
        approach="Treat the ball as a projectile: only the vertical component of the launch velocity matters for the highest point. Find it, "
                 "then use constant-acceleration kinematics for the rise above the platform and add the platform height.",
        steps=(
            Step("vy", "Resolution of the launch velocity into components: v_y = v sin(theta)",
                 "The horizontal and vertical motions are independent, and the highest point is reached when the vertical velocity is "
                 "zero, so only the vertical component of the launch velocity is needed."),
            Step("H", "Constant-acceleration kinematics: 0 = v_y^2 - 2 g (H - h0), so H = h0 + v_y^2 / (2 g)",
                 "With no air resistance the vertical acceleration is -g, so the ball rises v_y^2 / (2 g) above the platform before its "
                 "vertical velocity is zero; adding the platform height gives the height above the ground."),
        ),
        check="For theta = 90 degrees the ball rises v^2 / (2 g) above the platform, as for a vertical throw, and for theta = 0 the highest point "
              "is the platform itself. The result is always at least h0, and the units m + (m/s)^2 / (m/s^2) are metres."),
    "S11": Plan(
        approach="Use the work-energy theorem for the skid: the kinetic energy of the car is removed by the work of the constant kinetic "
                 "friction force, which gives the stopping distance without needing the mass.",
        steps=(
            Step("d", "Work-energy theorem with the friction law f = mu N, N = m g on a level road: (1/2) m v0^2 = mu m g d",
                 "The locked wheels slide, so a constant kinetic friction force mu m g acts against the motion over the distance d until "
                 "the car stops; the mass cancels and d = v0^2 / (2 mu g)."),
        ),
        check="Doubling the initial speed quadruples the distance and a larger friction coefficient shortens it; for a friction coefficient of "
              "order 0.5 and road speeds the distance is of order tens of metres, which is realistic. The units (m/s)^2 / (m/s^2) give m."),
    "S12": Plan(
        approach="At the maximum speed static friction at its limit supplies the whole centripetal force. Write the radial and the vertical "
                 "force balance for the car and solve for the speed.",
        steps=(
            Step("v", "Newton's second law for circular motion with the friction limit f = mu N, N = m g on a level road: mu m g = m v^2 / r",
                 "The only horizontal force on the car is friction, which points to the centre of the curve; at the limit it equals mu m g, "
                 "and equating it to the centripetal force m v^2 / r gives v = sqrt(mu g r), independent of the mass."),
        ),
        check="Quadrupling the radius doubles the speed limit, and the mass of the car does not matter. For a friction coefficient of order 0.5 "
              "and a radius of tens of metres the limit is of order 10 to 20 m/s (tens of km/h), a realistic value, and sqrt(m/s^2 m) gives m/s."),
    "S13": Plan(
        approach="For a small amplitude the restoring force on the bob is proportional to its displacement, so the pendulum is a simple "
                 "harmonic oscillator, and its period follows from the length and g.",
        steps=(
            Step("T", "Newton's second law for the tangential motion, m L theta'' = -m g sin(theta), with sin(theta) approximately theta for small angles, giving omega^2 = g / L and T = 2 pi sqrt(L / g)",
                 "The string tension is perpendicular to the motion, so only the tangential weight component restores the bob; for a small "
                 "angle this is linear in theta and the equation is that of a harmonic oscillator whose period depends only on L and g."),
        ),
        check="A length of 1 m gives a period of about 2 s, the familiar seconds pendulum, and the period does not depend on the mass; "
              "quadrupling the length doubles the period. The units sqrt(m / (m/s^2)) give s."),
    "S14": Plan(
        approach="At constant speed the motor force equals the weight, so the work done on the load is its gain of gravitational potential "
                 "energy; the average power is that work divided by the time taken.",
        steps=(
            Step("P", "Work-energy relation for a lift at constant speed, W = m g h, and the definition of average power, P = W / t",
                 "The speed is constant, so the kinetic energy does not change and the work done by the motor equals the increase of "
                 "potential energy m g h; dividing by the time of the lift gives the average mechanical power."),
        ),
        check="Lifting 1 kg through 1 m in 1 s takes about 10 W, so the power is about 10 W times the mass in kg times the height in m divided by "
              "the time in s, consistent with the result. The units kg (m/s^2) m / s give W."),
    "S19": Plan(
        approach="Split the motion into a uniform horizontal part and a vertical part with acceleration -g. The vertical motion fixes the time "
                 "of flight, and the horizontal velocity times that time is the range.",
        steps=(
            Step("R", "Independence of horizontal and vertical motion: x = v cos(theta) t, vertical motion with y = v sin(theta) t - (1/2) g t^2 = 0 for the landing time t = 2 v sin(theta) / g",
                 "The ball is launched from and lands on the same level, so the flight ends when y returns to zero; with no air resistance "
                 "the horizontal velocity v cos(theta) stays constant, so the range is v cos(theta) times the flight time, which equals "
                 "v^2 sin(2 theta) / g."),
        ),
        check="The range is largest at 45 degrees, complementary launch angles give the same range, and it vanishes at 0 and 90 degrees. "
              "The units (m/s)^2 / (m/s^2) give m."),
    "S28": Plan(
        approach="Write the position of the truck and of the car as functions of time, both measured from the passing point, and find the "
                 "non-zero time at which the two positions are equal.",
        steps=(
            Step("t", "Constant-velocity motion x_truck = v t and constant-acceleration motion from rest x_car = (1/2) a t^2; the car draws level when the positions are equal",
                 "The car and the truck start at the same point and the car draws level when (1/2) a t^2 = v t; the root t = 0 is the "
                 "start and the other root, t = 2 v / a, is the moment of overtaking."),
        ),
        check="At that moment the car's speed a t = 2 v is twice the truck's speed, which is consistent with its average speed being v over the "
              "interval. A larger acceleration shortens the time, and the units (m/s) / (m/s^2) give s."),
    "S29": Plan(
        approach="The power delivered by a force is the rate at which it does work, which is the dot product of the force and the velocity. "
                 "Only the component of the rope tension along the direction of motion contributes.",
        steps=(
            Step("P", "Definition of power for a constant force, P = F . v = F v cos(theta), where theta is the angle between the force and the velocity",
                 "The sled moves along the ground at constant velocity and the rope pulls at an angle theta above the horizontal, so only "
                 "the horizontal component F cos(theta) of the tension does work on it, and the power is that component times the speed."),
        ),
        check="For theta = 0 the power is F v, and for a force perpendicular to the motion (theta = 90 degrees) it is zero. The units N m/s "
              "give W."),
}

LEVELS: dict[str, str] = {
    "S31": "high_school", "S32": "high_school", "S33": "high_school", "S34": "intro_university", "S35": "intro_university",
    "S36": "upper_university", "S37": "intro_university", "S38": "intro_university",
    "S01": "intro_university", "S02": "high_school", "S03": "high_school", "S04": "intro_university", "S05": "intro_university",
    "S10": "high_school", "S11": "high_school", "S12": "high_school", "S13": "high_school", "S14": "high_school",
    "S19": "high_school", "S28": "high_school", "S29": "high_school",
}

TOPICS: dict[str, str] = {
    "S31": "projectile motion from a cliff", "S32": "work-energy with a spring and friction", "S33": "impulse and restitution",
    "S34": "rolling without slipping on an incline", "S35": "conical pendulum, circular motion", "S36": "physical pendulum, rotational dynamics",
    "S37": "gravitation, circular orbit", "S38": "statics and torque, ladder",
    "S01": "Atwood machine with a massive pulley", "S02": "block on a rough incline", "S03": "one-dimensional elastic collision",
    "S04": "spring-mass oscillator", "S05": "rotational second law with friction torque", "S10": "projectile maximum height",
    "S11": "braking distance with friction", "S12": "circular motion on a flat curve", "S13": "simple pendulum period",
    "S14": "work and power of a lift", "S19": "projectile range", "S28": "kinematic pursuit", "S29": "power of an angled force",
}
