"""M250 phase 3, batch optics: ten new structures S301 to S310 (geometric and physical optics) and their gold plans.

Same pattern as `lib_m250_waves.py`: a typed graph, an independently coded numeric solver (a vector-Snell ray trace, a tiny-angle ray
trace, a bracketing root finder with a quadrature, a ray-transfer matrix, a two-face prism trace, a root finder on the phase condition,
the optical-path equation of a double slit, a thin-film characteristic matrix, the first zero of a Bessel function, the Fresnel
amplitudes from a linear system), at least four numeric instantiations and a relevant edit that moves the answer.

Geometric optics: S301 (a beam through a glass plate), S302 (apparent depth under two liquids), S303 (the disc of light at the surface
of a pool: total internal reflection), S304 (a lens in front of a plane mirror), S305 (a prism). Physical optics: S306 (a grating),
S307 (a double slit with a film over one slit), S308 (a thin-film coating), S309 (the Rayleigh limit of a telescope) and S310
(reflection of polarised light at Brewster's angle).

Every answer-deciding condition is stated in the prompt; the prompt carries no numeral that is not a graph input. Admission status:
agent-verified, not expert-reviewed.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.special import j1

from physmon.benchmark.v2.graph import Assumption, Structure
from physmon.benchmark.v2.library import _co, _in, _spec
from physmon.benchmark.v2.trace import Plan, Step

# --- solvers (independent routes; SI inputs in node order) -----------------------------------------------------------------------


def _refract(direction, normal, n1, n2):
    # Vector form of Snell's law: the tangential part of the direction is scaled by n1/n2; the normal part follows from the norm.
    direction = np.asarray(direction, dtype=float)
    normal = np.asarray(normal, dtype=float)
    along = float(np.dot(direction, normal))
    tangential = (direction - along * normal) * (n1 / n2)
    rest = 1.0 - float(np.dot(tangential, tangential))
    if rest <= 0.0:
        raise ValueError("total internal reflection")
    return tangential + math.copysign(math.sqrt(rest), along) * normal


def _solve_plate_shift(thickness, theta, n):
    # Trace the ray with vector refraction at both faces, then the perpendicular distance of the exit point from the incident line.
    incident = np.array([math.sin(theta), math.cos(theta)])
    inside = _refract(incident, np.array([0.0, 1.0]), 1.0, n)
    exit_point = inside * (thickness / inside[1])
    return float(abs(exit_point[0] * incident[1] - exit_point[1] * incident[0]))


def _solve_apparent_depth(h_w, t_o, n_w, n_o):
    # Trace a ray that reaches the eye at a tiny angle from the vertical, back down through oil and water with exact Snell's law,
    # and divide the sideways offset by the tangent of the angle in air.
    alpha = 1.0e-4
    sin_air = math.sin(alpha)
    offset = t_o * math.tan(math.asin(sin_air / n_o)) + h_w * math.tan(math.asin(sin_air / n_w))
    return float(offset / math.tan(alpha))


def _solve_pool_disc(depth, n):
    # The outermost ray that still leaves the water is the root of the grazing-emergence condition n sin(phi) = 1; the area of the disc
    # is then the integral of 2 pi r dr out to the radius at which that ray meets the surface.
    phi = brentq(lambda p: n * math.sin(p) - 1.0, 0.0, 0.5 * math.pi, xtol=1e-15, rtol=1e-14)
    radius = depth * math.tan(phi)
    area, _ = quad(lambda r: 2.0 * math.pi * r, 0.0, radius, epsabs=0.0, epsrel=1e-13)
    return float(area)


def _solve_lens_mirror(f, u, g):
    # Ray-transfer matrices of the unfolded system: lens, a free path of 2 g to the mirror and back (a plane mirror leaves the matrix
    # unchanged), the lens again. The image plane is where the B element vanishes, and the A element there is the magnification.
    def lens(power):
        return np.array([[1.0, 0.0], [-1.0 / power, 1.0]])

    def gap(length):
        return np.array([[1.0, length], [0.0, 1.0]])

    def system(s):
        return gap(s) @ lens(f) @ gap(2.0 * g) @ lens(f) @ gap(u)

    s_image = brentq(lambda s: float(system(s)[0, 1]), 1e-9, 50.0 * (u + f + g), xtol=1e-15, rtol=1e-14)
    return float(system(s_image)[0, 0])


def _solve_prism_deviation(apex, n, theta):
    # Trace the ray through the two faces with vector refraction; the face normals differ by the apex angle. The deviation is the
    # angle of the emergent direction.
    first = np.array([math.cos(theta), math.sin(theta)])
    second = np.array([math.cos(theta - apex), math.sin(theta - apex)])
    incident = np.array([1.0, 0.0])
    inside = _refract(incident, first, 1.0, n)
    out = _refract(inside, second, n, 1.0)
    return float(math.atan2(out[1], out[0]))


def _solve_grating_position(spacing, lam, order, dist):
    # The maximum of the order is the root of the adjacent-ruling path condition d sin(theta) = m lambda; the position follows from
    # the right triangle to the flat screen.
    theta = brentq(lambda th: spacing * math.sin(th) - order * lam, 0.0, 0.5 * math.pi, xtol=1e-15, rtol=1e-14)
    return float(dist * math.tan(theta))


def _solve_film_shift(n, t, d, big_d):
    # The central bright fringe is where the two optical paths from the slits are equal: the extra optical path (n - 1) t through the
    # film over one slit is cancelled by the geometric path difference to a point at height y on the screen.
    def gap(y):
        return math.hypot(big_d, y + d / 2.0) - math.hypot(big_d, y - d / 2.0) - (n - 1.0) * t

    return float(brentq(gap, 0.0, 50.0 * big_d, xtol=1e-15, rtol=1e-14))


def _solve_coating_power(n1, n2, t, lam, p0):
    # Characteristic matrix of the single layer on the substrate (air has index one): the amplitude reflection coefficient from the
    # input admittance, then the power.
    delta = 2.0 * math.pi * n1 * t / lam
    layer = np.array([[math.cos(delta), 1j * math.sin(delta) / n1], [1j * n1 * math.sin(delta), math.cos(delta)]])
    b, c = layer @ np.array([1.0, n2])
    r = (b - c) / (b + c)
    return float(p0 * abs(r) ** 2)


def _solve_rayleigh_separation(lam, aperture, dist, x1):
    # The first dark ring of the Airy pattern is the first zero of the Bessel function J1 of pi D sin(theta) / lambda; locate it with a
    # bracketing root finder (the stated argument only brackets the root), then the separation from the distance to the Moon.
    bracket = (0.9 * x1, 1.1 * x1)
    zero = brentq(j1, *bracket, xtol=1e-14, rtol=1e-14)
    theta = math.asin(zero * lam / (math.pi * aperture))
    return float(dist * theta)


def _fresnel_amplitudes(n, theta, polarisation):
    # Continuity of the tangential electric and magnetic fields at the surface as a 2x2 linear system for (r, t), air to a medium n.
    cos_i = math.cos(theta)
    cos_t = math.sqrt(1.0 - (math.sin(theta) / n) ** 2)
    if polarisation == "s":
        matrix = np.array([[1.0, -1.0], [cos_i, n * cos_t]])
        rhs = np.array([-1.0, cos_i])
    else:
        matrix = np.array([[-cos_i, -cos_t], [1.0, -n]])
        rhs = np.array([-cos_i, -1.0])
    r, _t = np.linalg.solve(matrix, rhs)
    return float(r)


def _solve_brewster_power(p0, n, psi):
    # Find the angle of incidence at which the p-polarised amplitude reflection coefficient vanishes, then add the reflected powers of
    # the two components of the field (cos psi in the plane of incidence, sin psi perpendicular to it).
    theta_b = brentq(lambda th: _fresnel_amplitudes(n, th, "p"), 0.2, 1.5, xtol=1e-15, rtol=1e-14)
    r_p = _fresnel_amplitudes(n, theta_b, "p")
    r_s = _fresnel_amplitudes(n, theta_b, "s")
    return float(p0 * (math.cos(psi) ** 2 * r_p ** 2 + math.sin(psi) ** 2 * r_s ** 2))


# --- structures --------------------------------------------------------------------------------------------------------------


def s301_plate_lateral_shift() -> Structure:
    return Structure(
        "S301", "Sideways shift of a ray that crosses a parallel-sided glass plate", "optics", "plate_lateral_displacement",
        (_in("t", "length", "mm", "thickness of the plate", 12.0, (2.0, 50.0)),
         _in("theta", "angle", "deg", "angle of incidence on the first face, measured from the normal", 50.0, (10.0, 80.0)),
         _in("n", "refractive_index", "1", "refractive index of the glass", 1.52, (1.3, 2.0)),
         _co("thr", "angle", "deg", "angle of refraction inside the glass", "asin(sin(theta)/n)"),
         _co("path", "length", "mm", "length of the path of the ray inside the glass", "t/cos(thr)"),
         _co("shift", "length", "mm", "perpendicular distance between the emerging ray and the line of the incident ray",
             "path*sin(theta - thr)")),
        "shift",
        (Assumption("A-air", "The plate stands in air, whose refractive index is taken as one, and the glass is uniform and does not "
                             "absorb light.", "modelling", ("n",)),
         Assumption("A-ray", "The beam is narrow enough to be treated as a single ray, and the two faces are flat and parallel.",
                    "boundary_condition", ("t", "theta"))),
        _spec("A parallel-sided plate of glass of refractive index {n} and thickness {t} mm stands in air, whose refractive index is taken "
              "as one. A narrow beam of light, narrow enough to be treated as a single ray, strikes one flat face at an angle of "
              "incidence of {theta} degrees, passes through the plate and leaves by the opposite flat face. The glass is uniform and "
              "does not absorb light.",
              "What is the perpendicular distance between the emerging ray and the straight line along which the incident ray was "
              "travelling?", "perpendicular distance between the emerging ray and the line of the incident ray", "mm",
              "A separate ray B in another plate is shifted sideways by {v} {u}, but it is unrelated to this plate.",
              "A reference plate B shifts a ray sideways by {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the refraction.", "W", equivalent="cm"),
        ("t", 1.5), _solve_plate_shift, 3,
        "a vector-Snell ray trace through both faces, then the perpendicular distance of the exit point from the incident line, "
        "instead of the closed form t sin(theta - theta_r) / cos(theta_r)",
        solver_rel_tol=1e-9,
        instances=({"t": 12.0, "theta": 50.0, "n": 1.52}, {"t": 20.0, "theta": 35.0, "n": 1.6}, {"t": 15.0, "theta": 60.0, "n": 1.46},
                   {"t": 9.0, "theta": 42.0, "n": 1.7}))


def s302_apparent_depth_two_layers() -> Structure:
    return Structure(
        "S302", "Apparent depth of a coin under a layer of oil on water", "optics", "apparent_depth_layered_paraxial",
        (_in("h", "length", "cm", "depth of the water", 30.0, (10.0, 80.0)),
         _in("t", "length", "cm", "thickness of the oil layer", 6.0, (1.0, 20.0)),
         _in("nw", "refractive_index", "1", "refractive index of the water", 1.33, (1.3, 1.4)),
         _in("no", "refractive_index", "1", "refractive index of the oil", 1.47, (1.4, 1.55)),
         _co("dw", "length", "cm", "apparent thickness of the water layer seen from above", "h/nw"),
         _co("do_", "length", "cm", "apparent thickness of the oil layer seen from above", "t/no"),
         _co("D", "length", "cm", "apparent depth of the coin below the upper surface of the oil", "dw + do_")),
        "D",
        (Assumption("A-air", "The tank stands in air, whose refractive index is taken as one; the surfaces of the layers are flat and "
                             "horizontal, and the oil and the water do not mix.", "modelling", ("nw", "no")),
         Assumption("A-paraxial", "The observer looks straight down, so the rays that reach the eye make only tiny angles with the "
                                  "vertical and sin, tan and the angle itself are equal to the accuracy needed.",
                    "boundary_condition", ("h", "t"))),
        _spec("A coin lies flat on the bottom of a tank that holds a layer of water of refractive index {nw} and depth {h} cm, with a "
              "layer of oil of refractive index {no} and thickness {t} cm floating on top of the water. The oil and the water do not "
              "mix, and the surfaces of both layers are flat and horizontal. The tank stands in air, whose refractive index is taken as "
              "one. An observer looks straight down at the coin from directly above it, so that the rays that reach the eye make only "
              "tiny angles with the vertical.",
              "How far below the upper surface of the oil does the coin appear to be?",
              "apparent depth of the coin below the upper surface of the oil", "cm",
              "A separate coin B in another tank appears {v} {u} deep, but it is unrelated to this coin.",
              "A reference tank B has an apparent depth of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the refraction.", "W", equivalent="mm"),
        ("h", 1.4), _solve_apparent_depth, 4,
        "a ray traced from the coin to the eye at a tiny angle with exact Snell's law at both interfaces, the sideways offset divided "
        "by the tangent of the angle in air, instead of the sum of thickness over index",
        solver_rel_tol=1e-6,
        instances=({"h": 30.0, "t": 6.0, "nw": 1.33, "no": 1.47}, {"h": 25.0, "t": 4.0, "nw": 1.34, "no": 1.46},
                   {"h": 40.0, "t": 9.0, "nw": 1.33, "no": 1.5}, {"h": 18.0, "t": 3.0, "nw": 1.35, "no": 1.48}))


def s303_pool_light_disc() -> Structure:
    return Structure(
        "S303", "Area of the disc of light on the surface above a lamp at the bottom of a pool", "optics",
        "total_internal_reflection_snell_window_area",
        (_in("h", "length", "m", "depth of the lamp below the surface of the water", 1.8, (0.5, 4.0)),
         _in("n", "refractive_index", "1", "refractive index of the water", 1.33, (1.3, 1.4)),
         _co("thc", "angle", "deg", "critical angle at the surface of the water", "asin(1/n)"),
         _co("r", "length", "m", "radius of the disc of light on the surface", "h*tan(thc)"),
         _co("A", "area", "m^2", "area of the disc of light on the surface", "pi*r**2")),
        "A",
        (Assumption("A-air", "The air above the pool has a refractive index of one, the surface of the water is flat and still, and the "
                             "water is clear and does not absorb light.", "modelling", ("n",)),
         Assumption("A-lamp", "The lamp is small enough to be treated as a point and sends light in a cone about the vertical that is "
                              "wide enough for the edge of the disc to be set by total internal reflection at the surface.",
                    "boundary_condition", ("h",))),
        _spec("A small lamp rests on the bottom of a large swimming pool, at a depth of {h} m below the flat, still surface of the "
              "water, whose refractive index is {n}. The water is clear and does not absorb light, and the air above it has a "
              "refractive index of one. The lamp is small enough to be treated as a point, and it shines upwards in a cone about the "
              "vertical that is wide enough for the edge of the bright disc on the surface to be set by total internal reflection. "
              "Seen from above, the light that escapes forms a bright disc on the surface, centred directly above the lamp.",
              "What is the area of this bright disc on the surface of the water?", "area of the bright disc on the surface", "m^2",
              "A separate pond B in another garden has a lit patch of {v} {u}, but it is unrelated to this pool.",
              "A reference pool B has a bright disc of area {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the refraction.", "W", equivalent="cm^2"),
        ("h", 1.5), _solve_pool_disc, 2,
        "the root of the grazing-emergence condition n sin(phi) = 1 for the outermost escaping ray and a quadrature of 2 pi r dr out to "
        "the radius at which it meets the surface, instead of the closed form pi h^2 / (n^2 - 1)",
        solver_rel_tol=1e-9,
        instances=({"h": 1.8, "n": 1.33}, {"h": 2.5, "n": 1.34}, {"h": 1.2, "n": 1.36}, {"h": 3.0, "n": 1.31}))


def s304_lens_and_plane_mirror() -> Structure:
    return Structure(
        "S304", "Magnification of the final image of a lens with a plane mirror behind it", "optics",
        "lens_plane_mirror_double_pass_magnification",
        (_in("f", "length", "cm", "focal length of the lens", 15.0, (10.0, 16.0)),
         _in("u", "length", "cm", "distance of the object from the lens", 40.0, (36.0, 80.0)),
         _in("g", "length", "cm", "distance of the plane mirror behind the lens", 45.0, (40.0, 60.0)),
         _co("v1", "length", "cm", "distance of the first image behind the lens", "u*f/(u - f)"),
         _co("s2", "length", "cm", "distance of the first image from the lens when its light returns to the lens (object distance of "
                                   "the second pass)", "2*g - v1"),
         _co("v2", "length", "cm", "distance of the final image in front of the lens", "s2*f/(s2 - f)"),
         _co("m", "magnification", "1", "overall lateral magnification of the final image", "(v1/u)*(v2/s2)")),
        "m",
        (Assumption("A-thin", "The lens is thin and its aperture is small, so that the thin-lens equation holds on each of the two passes; "
                              "the mirror is perfectly plane and perfectly reflecting.", "modelling", ("f", "g")),
         Assumption("A-axis", "The object, the lens and the mirror share one axis, the mirror stands perpendicular to it, and the object "
                              "is a small flat object perpendicular to the axis, in front of the lens.", "boundary_condition",
                    ("u", "g"))),
        _spec("A small flat object stands on the axis of a thin converging lens of focal length {f} cm, at a distance of {u} cm in front "
              "of the lens. A perfectly reflecting plane mirror stands {g} cm behind the lens, perpendicular to the axis, so that the "
              "light that has passed through the lens once is reflected back through it. The object, the lens and the mirror all stand "
              "on an optical bench that runs along the axis, from the object through the lens to the mirror. The lens is thin, its "
              "aperture is small, and "
              "the object is small and perpendicular to the axis. Light from the object reaches the mirror only by passing through the "
              "lens.",
              "What is the overall lateral magnification of the final image that the lens forms of the object, counted as positive if "
              "that image is upright?", "overall lateral magnification of the final image", "1",
              "A separate lens system B in another laboratory has a magnification of {v}, but it is unrelated to this lens.",
              "A reference lens system B has an overall magnification of {v}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the imaging.", "W"),
        ("g", 1.3), _solve_lens_mirror, 3,
        "the ray-transfer matrices of the unfolded system (lens, a free path of 2 g, lens, a free path to the image plane where the B "
        "element vanishes), reading the magnification from the A element, instead of two thin-lens equations in series",
        solver_rel_tol=1e-9,
        instances=({"f": 15.0, "u": 40.0, "g": 45.0}, {"f": 12.0, "u": 50.0, "g": 52.0}, {"f": 10.0, "u": 36.0, "g": 41.0},
                   {"f": 14.0, "u": 60.0, "g": 48.0}))


def s305_prism_deviation() -> Structure:
    return Structure(
        "S305", "Deviation of a ray of light by a glass prism", "optics", "prism_deviation_oblique_incidence",
        (_in("A", "angle", "deg", "apex angle of the prism", 40.0, (30.0, 50.0)),
         _in("n", "refractive_index", "1", "refractive index of the glass", 1.5, (1.45, 1.55)),
         _in("theta", "angle", "deg", "angle of incidence on the first face, measured from the normal", 55.0, (40.0, 70.0)),
         _co("th1", "angle", "deg", "angle of refraction at the first face", "asin(sin(theta)/n)"),
         _co("th2", "angle", "deg", "angle of incidence at the second face", "A - th1"),
         _co("tho", "angle", "deg", "angle of emergence at the second face, measured from the normal", "asin(n*sin(th2))"),
         _co("delta", "angle", "deg", "angle through which the ray is turned", "theta + tho - A")),
        "delta",
        (Assumption("A-air", "The prism stands in air, whose refractive index is taken as one; the glass is uniform, does not disperse "
                             "or absorb light, and the two refracting faces are flat.", "modelling", ("n", "A")),
         Assumption("A-plane", "The ray lies in a plane perpendicular to the edge where the two refracting faces meet, strikes the first "
                               "face and leaves by the second face, on the same side of the normals as in the usual sign convention.",
                    "boundary_condition", ("theta",))),
        _spec("A ray of light in air strikes one refracting face of a glass prism at an angle of incidence of {theta} degrees, measured "
              "from the normal to that face. The prism has an apex angle of {A} degrees between its two refracting faces and a "
              "refractive index of {n}. The air has a refractive index of one, the glass does not disperse or absorb light, the ray "
              "lies in a plane perpendicular to the edge of the prism and leaves through the second refracting face.",
              "Through what angle is the ray turned by the prism, that is, what is the angle between the direction of the emergent ray "
              "and the direction of the incident ray?", "angle through which the ray is turned by the prism", "deg",
              "A separate ray B in another prism is turned through {v} {u}, but it is unrelated to this prism.",
              "A reference prism B turns a ray through {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the refraction.", "W", equivalent="rad"),
        ("theta", 1.1), _solve_prism_deviation, 3,
        "a vector-Snell trace through the two refracting faces, whose normals differ by the apex angle, with the deviation read from "
        "the angle of the emergent direction, instead of theta + theta_o - A",
        solver_rel_tol=1e-9,
        instances=({"A": 40.0, "n": 1.5, "theta": 55.0}, {"A": 45.0, "n": 1.52, "theta": 60.0}, {"A": 35.0, "n": 1.47, "theta": 50.0},
                   {"A": 48.0, "n": 1.54, "theta": 62.0}))


def s306_grating_order_on_screen() -> Structure:
    return Structure(
        "S306", "Position on a screen of a diffraction maximum from a grating", "optics", "grating_order_screen_position",
        (_in("d", "length", "μm", "spacing of the rulings of the grating", 2.5, (1.8, 4.0)),
         _in("lam", "length", "nm", "wavelength of the light", 633.0, (400.0, 700.0)),
         _in("m", "coefficient", "1", "order of the maximum (zero at the centre)", 1.0, (1.0, 2.0)),
         _in("D", "length", "m", "distance from the grating to the screen", 1.5, (1.0, 3.0)),
         _co("s", "coefficient", "1", "sine of the angle of the maximum", "m*lam/d"),
         _co("th", "angle", "deg", "angle of the maximum from the normal to the grating", "asin(s)"),
         _co("y", "length", "cm", "distance of the maximum from the centre of the pattern", "D*tan(th)")),
        "y",
        (Assumption("A-normal", "The light falls at normal incidence on the grating, the beam is wide compared with the spacing of the "
                                "rulings, and the screen is flat and parallel to the grating, far enough away for the pattern to be "
                                "the far-field pattern.", "boundary_condition", ("d", "D")),
         Assumption("A-order", "The central maximum is the maximum of order zero, and the order asked for lies on one side of it.",
                    "boundary_condition", ("m",))),
        _spec("Light from a tunable laser, set to a wavelength of {lam} nm, falls at normal incidence on a transmission diffraction grating whose rulings "
              "are {d} μm apart. The beam is wide compared with the spacing of the rulings. A flat screen stands {D} m beyond the "
              "grating, parallel to it and far enough away for the pattern to be the far-field pattern. The central maximum is the "
              "maximum of order zero.",
              "How far from the centre of the pattern on the screen is the maximum of order {m} on one side of it?",
              "distance of the maximum from the centre of the pattern", "cm",
              "A separate grating B in another room has a maximum {v} {u} from its centre, but it is unrelated to this grating.",
              "A reference grating B has a maximum {v} {u} from its centre.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the diffraction.", "W", equivalent="mm"),
        ("D", 1.5), _solve_grating_position, 4,
        "the root of the phase condition d sin(theta) = m lambda found with a bracketing root finder, then the right triangle to the "
        "flat screen",
        solver_rel_tol=1e-9,
        instances=({"d": 2.5, "lam": 633.0, "m": 1.0, "D": 1.5}, {"d": 3.3, "lam": 532.0, "m": 2.0, "D": 2.0},
                   {"d": 2.0, "lam": 450.0, "m": 1.0, "D": 1.2}, {"d": 3.0, "lam": 650.0, "m": 2.0, "D": 2.5}))


def s307_film_over_one_slit() -> Structure:
    return Structure(
        "S307", "Shift of the central fringe when a transparent film covers one slit", "optics",
        "double_slit_film_central_fringe_shift",
        (_in("n", "refractive_index", "1", "refractive index of the film", 1.5, (1.4, 1.6)),
         _in("t", "length", "μm", "thickness of the film", 6.0, (2.0, 12.0)),
         _in("d", "length", "mm", "separation of the two slits", 0.5, (0.3, 1.0)),
         _in("D", "length", "m", "distance from the slits to the screen", 2.0, (1.0, 4.0)),
         _co("opd", "length", "μm", "extra optical path through the film compared with the same thickness of air", "(n - 1)*t"),
         _co("th", "angle", "deg", "angle at which the optical paths from the two slits are equal", "asin(opd/d)"),
         _co("y", "length", "mm", "distance the central bright fringe moves along the screen", "D*tan(th)")),
        "y",
        (Assumption("A-film", "The film does not disperse or absorb light, is uniform, and has the stated refractive index for the light "
                              "used; the light falls at normal incidence, so the extra optical path through the film is its "
                              "thickness times the refractive index minus one.", "modelling", ("n", "t")),
         Assumption("A-far", "The screen is far beyond the slits compared with their separation, the slits are narrow, and the central "
                             "bright fringe is the one at which the optical paths from the two slits are equal.",
                    "boundary_condition", ("d", "D"))),
        _spec("Monochromatic light falls at normal incidence on two narrow slits that are {d} mm apart. A uniform film of lacquer "
              "of refractive index {n} and thickness {t} μm covers one slit and no other part of the slits. The lacquer does not "
              "disperse or absorb light. A screen stands {D} m beyond the slits, far enough away for the pattern to be the far-field "
              "pattern. Without the film the central bright fringe, at which the optical paths from the two slits are equal, lies "
              "opposite the midpoint between the slits.",
              "How far does the central bright fringe lie from the point opposite the midpoint between the slits?",
              "distance of the central bright fringe from the point opposite the midpoint between the slits", "mm",
              "A separate double slit B in another laboratory has a fringe {v} {u} from its centre, but it is unrelated to these slits.",
              "A reference double slit B has a central fringe {v} {u} from its midpoint.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the interference.", "W", equivalent="cm"),
        ("t", 1.5), _solve_film_shift, 4,
        "the optical-path condition for equal paths from the two slits to a screen point, with the exact slit-to-point distances, "
        "solved with a bracketing root finder, instead of the far-field angle asin((n - 1) t / d)",
        solver_rel_tol=1e-6,
        instances=({"n": 1.5, "t": 6.0, "d": 0.5, "D": 2.0}, {"n": 1.45, "t": 4.0, "d": 0.4, "D": 1.5},
                   {"n": 1.55, "t": 9.0, "d": 0.8, "D": 3.0}, {"n": 1.6, "t": 3.0, "d": 0.35, "D": 2.5}))


def s308_coating_reflected_power() -> Structure:
    return Structure(
        "S308", "Power reflected from a lens with a single thin-film coating", "optics", "single_layer_coating_reflected_power",
        (_in("n1", "refractive_index", "1", "refractive index of the coating", 1.38, (1.25, 1.5)),
         _in("n2", "refractive_index", "1", "refractive index of the glass", 1.52, (1.45, 1.9)),
         _in("t", "length", "nm", "thickness of the coating", 90.0, (40.0, 200.0)),
         _in("lam", "length", "nm", "wavelength of the light in air", 550.0, (400.0, 700.0)),
         _in("P0", "power", "mW", "power of the incident beam", 5.0, (1.0, 50.0)),
         _co("r1", "amplitude_ratio", "1", "amplitude reflection coefficient at the air-coating interface", "(1 - n1)/(1 + n1)"),
         _co("r2", "amplitude_ratio", "1", "amplitude reflection coefficient at the coating-glass interface", "(n1 - n2)/(n1 + n2)"),
         _co("delta", "angle", "rad", "phase change of the light on one crossing of the coating", "2*pi*n1*t/lam"),
         _co("Rf", "reflectance", "1", "fraction of the power that is reflected",
             "(r1**2 + r2**2 + 2*r1*r2*cos(2*delta))/(1 + r1**2*r2**2 + 2*r1*r2*cos(2*delta))"),
         _co("Pr", "power", "mW", "power of the reflected beam", "P0*Rf")),
        "Pr",
        (Assumption("A-normal", "The light falls at normal incidence from air (refractive index one) on the coated surface, the coating "
                               "and the glass are uniform and do not absorb light, and only the light reflected by the coated surface "
                               "is counted, not that from any other surface of the lens.", "modelling", ("n1", "n2")),
         Assumption("A-coherent", "The light is coherent over the thickness of the coating, so that the waves reflected at the two "
                                  "interfaces and those that bounce between them interfere.", "boundary_condition", ("t", "lam"))),
        _spec("A beam of light of power {P0} mW and wavelength {lam} nm in air falls at normal incidence on the flat front surface of a "
              "thick lens of glass of refractive index {n2}. The surface carries a single uniform coating of refractive index {n1} and "
              "thickness {t} nm. The coating and the glass do not absorb light, and only the light reflected by the coated front "
              "surface is considered, not that from any other surface of the lens. The light is coherent over the thickness of the "
              "coating, so that the waves reflected at its two interfaces, with those that bounce between them, interfere.",
              "What power is carried by the beam reflected from the coated surface?", "power of the reflected beam", "mW",
              "A separate laser B in another room emits {v} {u}, but it is unrelated to this beam.",
              "A reference beam B has a reflected power of {v} {u}.",
              "A separate sensor B reads {v} {u}, but it plays no part in the reflection.", "Hz", equivalent="W"),
        ("t", 1.4), _solve_coating_power, 5,
        "the characteristic matrix of the single layer on the substrate, the amplitude reflection coefficient from the input "
        "admittance and its squared modulus, instead of the closed form with the phase thickness",
        solver_rel_tol=1e-9,
        instances=({"n1": 1.38, "n2": 1.52, "t": 90.0, "lam": 550.0, "P0": 5.0},
                   {"n1": 1.45, "n2": 1.75, "t": 60.0, "lam": 620.0, "P0": 8.0},
                   {"n1": 1.3, "n2": 1.62, "t": 140.0, "lam": 480.0, "P0": 3.0},
                   {"n1": 1.42, "n2": 1.5, "t": 170.0, "lam": 700.0, "P0": 12.0}))


def s309_telescope_rayleigh_separation() -> Structure:
    return Structure(
        "S309", "Smallest separation of two lunar features that a telescope resolves", "optics", "rayleigh_criterion_circular_aperture",
        (_in("lam", "length", "nm", "wavelength of the light", 550.0, (400.0, 700.0)),
         _in("D", "length", "cm", "diameter of the adjustable circular stop of the telescope", 15.0, (5.0, 40.0)),
         _in("L", "length", "km", "distance from the telescope to the Moon, a stated constant", 384400.0, (356000.0, 407000.0),
             provenance="assumed"),
         _in("x1", "coefficient", "1", "first zero of the Bessel function J1, a stated constant", 3.831706, (3.8316, 3.8318),
             provenance="assumed"),
         _co("sq", "coefficient", "1", "sine of the angular radius of the first dark ring", "x1*lam/(pi*D)"),
         _co("thr", "angle", "rad", "angular radius of the first dark ring", "asin(sq)"),
         _co("sep", "length", "km", "smallest separation of two features on the Moon that are just resolved", "L*thr")),
        "sep",
        (Assumption("A-const", "The distance to the Moon is the stated constant value, the two features are small, equally bright, "
                               "incoherent and at that distance, and the Bessel function of the first kind and first order first vanishes at the stated argument.",
                    "modelling", ("L", "x1")),
         Assumption("A-limit", "The telescope is limited by diffraction at its circular stop alone, and two features are just resolved "
                               "when the central maximum of the diffraction pattern of one falls on the first dark ring of the pattern "
                               "of the other.", "boundary_condition", ("lam", "D"))),
        _spec("A telescope looks at two small, equally bright, incoherent features on the surface of the Moon, whose distance from the "
              "telescope is {L} km. The light has a wavelength of {lam} nm. The light enters the telescope through an adjustable circular stop of diameter {D} cm "
              "in front of the objective, and the image is limited by the diffraction of the light at this stop alone. Two features are just resolved when the "
              "central maximum of the diffraction pattern of one falls on the first dark ring of the pattern of the other. For a circular "
              "stop, the first dark ring lies where the Bessel function of the first kind and first order, of the quantity π D sin(θ) / λ, first vanishes, at the "
              "argument {x1}, where θ is the angle from the axis.",
              "What is the smallest separation of the two features on the Moon that the telescope just resolves?",
              "smallest separation of the two features that the telescope just resolves", "km",
              "A separate telescope B on another hill resolves features {v} {u} apart, but it is unrelated to this telescope.",
              "A reference telescope B just resolves features {v} {u} apart.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the diffraction.", "W", equivalent="m",
              formats={"L": ".6g", "x1": ".7g"}),
        ("D", 1.5), _solve_rayleigh_separation, 4,
        "the first zero of the Bessel function J1 located with a bracketing root finder (the stated argument only brackets it), then "
        "the angle from the arcsine and the separation from the distance to the Moon",
        solver_rel_tol=1e-4,
        instances=({"lam": 550.0, "D": 15.0, "L": 384400.0, "x1": 3.831706}, {"lam": 500.0, "D": 12.0, "L": 363300.0, "x1": 3.831706},
                   {"lam": 620.0, "D": 18.0, "L": 405500.0, "x1": 3.831706}, {"lam": 450.0, "D": 10.0, "L": 384400.0, "x1": 3.831706}))


def s310_brewster_reflected_power() -> Structure:
    return Structure(
        "S310", "Power reflected from glass at Brewster's angle for light polarised obliquely", "optics",
        "brewster_angle_reflection_oblique_polarisation",
        (_in("P0", "power", "mW", "power of the incident beam", 8.0, (1.0, 50.0)),
         _in("n", "refractive_index", "1", "refractive index of the glass", 1.5, (1.3, 1.8)),
         _in("psi", "angle", "deg", "angle between the electric field of the beam and the plane of incidence", 35.0, (10.0, 70.0)),
         _co("thB", "angle", "deg", "angle of incidence, at which no light polarised in the plane of incidence is reflected",
             "atan(n)"),
         _co("thT", "angle", "deg", "angle of refraction at that angle of incidence", "asin(sin(thB)/n)"),
         _co("rs", "amplitude_ratio", "1", "amplitude reflection coefficient for light polarised perpendicular to the plane of "
                                           "incidence", "-sin(thB - thT)/sin(thB + thT)"),
         _co("Pr", "power", "mW", "power of the reflected beam", "P0*sin(psi)**2*rs**2")),
        "Pr",
        (Assumption("A-air", "The beam travels in air, whose refractive index is taken as one, and strikes the flat surface of a thick "
                             "block of glass that does not absorb light; only the first surface is considered.", "modelling", ("n",)),
         Assumption("A-brewster", "The angle of incidence is the one at which no light polarised in the plane of incidence is reflected.",
                    "boundary_condition", ("psi", "P0"))),
        _spec("A beam of plane-polarised light from an adjustable laser, of power {P0} mW, travels in air and strikes the flat surface of a thick block of glass of "
              "refractive index {n}. The electric field of the beam makes an angle of {psi} degrees with the plane of incidence. The "
              "angle of incidence is the one at which none of the light polarised in the plane of incidence is reflected. The glass does "
              "not absorb light, the air has a refractive index of one, and only the first surface of the block is considered.",
              "What power is carried by the reflected beam?", "power of the reflected beam", "mW",
              "A separate laser B in another room emits {v} {u}, but it is unrelated to this beam.",
              "A reference beam B has a reflected power of {v} {u}.",
              "A separate sensor B reads {v} {u}, but it plays no part in the reflection.", "Hz", equivalent="W"),
        ("P0", 1.5), _solve_brewster_power, 3,
        "a root finder for the angle at which the p-polarised Fresnel amplitude, from a 2x2 linear system of the boundary conditions, "
        "vanishes, then the reflected powers of the two components of the field added",
        solver_rel_tol=1e-9,
        instances=({"P0": 8.0, "n": 1.5, "psi": 35.0}, {"P0": 5.0, "n": 1.33, "psi": 50.0}, {"P0": 12.0, "n": 1.7, "psi": 25.0},
                   {"P0": 3.0, "n": 1.46, "psi": 60.0}))


ALL = (s301_plate_lateral_shift, s302_apparent_depth_two_layers, s303_pool_light_disc, s304_lens_and_plane_mirror,
       s305_prism_deviation, s306_grating_order_on_screen, s307_film_over_one_slit, s308_coating_reflected_power,
       s309_telescope_rayleigh_separation, s310_brewster_reflected_power)


def all_structures() -> list[Structure]:
    return [factory() for factory in ALL]


STRUCTURES: dict[str, Structure] = {s.structure_id: s for s in all_structures()}

# --- gold solution plans -----------------------------------------------------------------------------------------------------

PLANS: dict[str, Plan] = {
    "S301": Plan(
        approach="The plate bends the ray towards the normal on entering and back on leaving, so the emerging ray is parallel to the "
                 "incident ray but displaced sideways. Find the angle of refraction, the path in the glass, and the perpendicular "
                 "distance between the two parallel lines.",
        steps=(
            Step("thr", "Snell's law at the first face, sin(theta) = n sin(theta_r), with the refractive index of air taken as one",
                 "The ray passes from air into the glass, so its direction inside is fixed by Snell's law at the entry face."),
            Step("path", "Geometry of the path in a plate of thickness t at an angle theta_r to the normal, path = t / cos(theta_r)",
                 "The ray crosses the full thickness t of the plate while travelling at the angle theta_r to the normal, so its path "
                 "is longer than t by the factor 1 / cos(theta_r)."),
            Step("shift", "Perpendicular distance between two parallel lines, shift = path sin(theta - theta_r)",
                 "Inside the glass the ray departs from the straight line of the incident ray by the angle theta - theta_r; the "
                 "emergent ray is parallel to the incident one, so this departure over the path gives their perpendicular distance."),
        ),
        check="Limiting cases: at normal incidence the shift is zero; for a plate of index one it is zero for every angle. The shift "
              "grows in proportion to the thickness and tends to t when the angle of incidence tends to ninety degrees and the "
              "index is large."),
    "S302": Plan(
        approach="Seen from directly above, each layer looks thinner by its refractive index (relative to the air above). Add the apparent "
                 "thickness of the water layer and that of the oil layer.",
        steps=(
            Step("do_", "The same rule for the oil layer, apparent thickness = t / n_oil",
                 "Each flat layer displaces the apparent position by its own amount, and the oil layer sits above the water, so the "
                 "oil is treated by the same rule."),
            Step("dw", "Apparent depth for near-vertical viewing through a flat surface, apparent depth = real depth / n",
                 "For rays that make tiny angles with the vertical, Snell's law becomes n1 theta1 = n2 theta2, so a layer of "
                 "thickness h and index n looks like a layer of thickness h / n when viewed from above."),
            Step("D", "Apparent depths of stacked layers add, D = h / n_water + t / n_oil",
                 "The apparent depth below the upper surface of the oil is the sum of the apparent thicknesses of the layers that the "
                 "rays cross on the way to the eye."),
        ),
        check="Limiting cases: with n of both layers equal to one the apparent depth is the real depth h + t; a thicker or denser layer "
              "looks shallower. The apparent depth is always less than the real depth h + t."),
    "S303": Plan(
        approach="Light leaves the water only if its angle of incidence on the surface is below the critical angle. The bright disc "
                 "is bounded by the ray that meets the surface at the critical angle; find that angle, the radius at which it meets "
                 "the surface, and then the area.",
        steps=(
            Step("thc", "Critical angle for total internal reflection from water to air, sin(theta_c) = 1 / n",
                 "At the critical angle the refracted ray grazes the surface, so beyond it no light escapes; the cone of the lamp is "
                 "wide enough that this angle sets the edge of the disc."),
            Step("r", "Geometry of the ray from the lamp at depth h, r = h tan(theta_c)",
                 "The outermost escaping ray travels at the critical angle to the vertical, so it meets the surface at a horizontal "
                 "distance h tan(theta_c) from the point above the lamp."),
            Step("A", "Area of a circle, A = pi r^2",
                 "All the escaping light lies inside this circle, which is the bright disc on the surface."),
        ),
        check="Limiting cases: the area grows with the square of the depth, and for a larger refractive index the critical angle is "
              "smaller, so the disc is smaller. Order of magnitude: for water the radius is about 1.13 times the depth."),
    "S304": Plan(
        approach="Apply the thin-lens equation twice. The first pass forms a real image behind the lens. The plane mirror reflects the "
                 "light, so that image acts as an object for the second pass at a distance found from the mirror position. The overall "
                 "magnification is the product of the magnifications of the two passes.",
        steps=(
            Step("v1", "Thin-lens equation for the first pass, 1/u + 1/v1 = 1/f",
                 "The light from the object passes through the lens once on its way to the mirror, which forms the first image at the "
                 "distance v1 behind the lens."),
            Step("s2", "Reflection in a plane mirror: the light behaves as if the first image were an object at a distance 2 g - v1 "
                       "from the lens, on the mirror side",
                 "A plane mirror at distance g reflects the light, which then returns to the lens as if it came from the image's "
                 "mirror image, at a distance g + (g - v1) = 2 g - v1 from the lens."),
            Step("v2", "Thin-lens equation for the second pass, 1/s2 + 1/v2 = 1/f",
                 "The light crosses the lens a second time, so the thin-lens equation holds again with the object distance s2 and gives "
                 "the position v2 of the final image."),
            Step("m", "Lateral magnification of each pass, m1 = -v1/u and m2 = -v2/s2, and of a plane mirror, +1, multiply",
                 "The overall magnification is the product of the magnifications at each step; two inversions leave the final image "
                 "upright, so the product is positive."),
        ),
        check="Limiting case: when the mirror stands exactly at the first image (g equal to v1), the second object distance s2 equals v1 "
              "and the second pass magnifies by u / v1, so the overall magnification is exactly one. The product is positive because "
              "each of the two real images is inverted."),
    "S305": Plan(
        approach="Follow the ray through the two refracting faces with Snell's law, using the apex angle to relate the angles at the "
                 "two faces, and add the bending at each face to find the total deviation.",
        steps=(
            Step("th1", "Snell's law at the first face, sin(theta) = n sin(theta_1)",
                 "The ray enters the glass from air, so the angle of refraction at the first face follows from Snell's law."),
            Step("th2", "Geometry of the prism: the angles inside the glass at the two faces add up to the apex angle, theta_1 + theta_2 = A",
                 "The two normals and the ray inside the glass form a triangle whose angle at the apex is the apex angle A, so the "
                 "angle of incidence at the second face is A - theta_1."),
            Step("tho", "Snell's law at the second face, n sin(theta_2) = sin(theta_o)",
                 "The ray passes from the glass into air at the second face, and the sine of its angle of emergence is n sin(theta_2); "
                 "the ray leaves only if this is below one."),
            Step("delta", "Total deviation as the sum of the bending at the two faces, delta = (theta - theta_1) + (theta_o - theta_2) "
                          "= theta + theta_o - A",
                 "Each refraction turns the ray towards the base of the prism, by theta - theta_1 at the first face and "
                 "theta_o - theta_2 at the second; with theta_1 + theta_2 = A this gives the stated total."),
        ),
        check="Limiting cases: a prism of index one does not turn the ray; for a thin prism and small angles the deviation tends to "
              "(n - 1) A. The deviation has a minimum when the ray passes symmetrically through the prism."),
    "S306": Plan(
        approach="A grating sends light of wavelength lambda into maxima where the path difference between adjacent rulings is a whole "
                 "number of wavelengths. Find the sine of the angle, the angle, and then the position on the flat screen.",
        steps=(
            Step("s", "Grating equation at normal incidence, d sin(theta) = m lambda",
                 "The waves from neighbouring rulings are in phase in the direction where their path difference d sin(theta) is m "
                 "wavelengths, which fixes the sine of the angle of the maximum of order m."),
            Step("th", "The angle whose sine is s, theta = arcsin(s)",
                 "The sine must be below one for the order to exist; the angle is measured from the normal to the grating."),
            Step("y", "Right triangle between the grating and the flat screen, y = D tan(theta)",
                 "The screen is flat and parallel to the grating at distance D, so the maximum at the angle theta lies a distance "
                 "D tan(theta) from the centre; the small-angle approximation is not needed."),
        ),
        check="Limiting cases: for small angles y is about m lambda D / d, which grows with the wavelength and the distance and falls "
              "with the ruling spacing. The sine m lambda / d must be less than one for the maximum to exist."),
    "S307": Plan(
        approach="The film delays the light from one slit, so the equal-path (central) fringe moves towards the covered slit until the "
                 "geometric path difference cancels the extra optical path. Find the extra optical path, the angle at which it "
                 "is cancelled, and the position on the screen.",
        steps=(
            Step("opd", "Optical path through a film compared with the same thickness of air, (n - 1) t",
                 "Light crossing a film of thickness t and index n has an optical path n t, compared with t for air, so the extra "
                 "optical path is (n - 1) t."),
            Step("th", "Equal optical paths from the two slits at the angle theta, d sin(theta) = (n - 1) t",
                 "At the central bright fringe the geometric path difference d sin(theta) from the two slits exactly cancels the extra "
                 "optical path of the film, so the fringe sits at this angle on the side of the covered slit."),
            Step("y", "Right triangle between the slits and the screen, y = D tan(theta)",
                 "The screen is at distance D beyond the slits, so the fringe at the angle theta lies D tan(theta) from the point "
                 "opposite the midpoint."),
        ),
        check="Limiting cases: with no film (t = 0) the fringe does not move; the shift does not depend on the wavelength, because "
              "the extra path (n - 1) t does not. Order of magnitude: a few micrometres of film shift the fringe by millimetres."),
    "S308": Plan(
        approach="The waves reflected at the front of the coating and at the coating-glass interface (with those that bounce between "
                 "them) interfere. Find the amplitude reflection coefficients of the two interfaces, the phase change across the "
                 "coating, the total reflected fraction and then the reflected power.",
        steps=(
            Step("delta", "Phase change on one crossing of the coating, delta = 2 pi n1 t / lambda",
                 "The light crosses the coating twice before it recombines with the front reflection, so the relative phase is 2 delta."),
            Step("r1", "Fresnel amplitude reflection coefficient at normal incidence, r = (n_a - n_b) / (n_a + n_b), air to coating",
                 "The light passes from air to the coating, and at normal incidence the amplitude coefficient depends only on the two "
                 "refractive indices."),
            Step("r2", "The same coefficient at the interface between coating and glass",
                 "The light that enters the coating reaches the glass, where a second reflection arises with its own amplitude "
                 "coefficient."),
            Step("Rf", "Sum of the reflected waves including multiple reflections, R = |(r1 + r2 e^(-2 i delta)) / (1 + r1 r2 e^(-2 i delta))|^2",
                 "The infinite series of internal reflections sums to this ratio; its squared modulus is the reflected fraction of the "
                 "power, written with cos(2 delta)."),
            Step("Pr", "Reflected power from the incident power and the reflected fraction, P = R P0",
                 "The reflected fraction multiplies the incident power to give the power of the reflected beam."),
        ),
        check="Limiting cases: for a coating of zero thickness the result is the reflectance of the bare glass; for a quarter-wave "
              "coating of index sqrt(n2) the reflection vanishes at that wavelength. The fraction lies between zero and one."),
    "S309": Plan(
        approach="Two features are just resolved when the central maximum of one diffraction pattern falls on the first dark ring of the "
                 "other. Find the angle of that ring for the circular opening, then the separation on the Moon from the angle and the "
                 "distance.",
        steps=(
            Step("sq", "First dark ring of the Airy pattern, J1(pi D sin(theta) / lambda) = 0 at argument x1, so sin(theta) = x1 lambda / (pi D)",
                 "For a circular opening the intensity pattern is set by the Bessel function J1, whose first zero gives the first "
                 "dark ring."),
            Step("thr", "The angle whose sine is sq, theta = arcsin(sq)",
                 "The angular radius of the first dark ring is the angle itself, a few microradians here, so the arcsine is close to "
                 "the sine."),
            Step("sep", "Arc length at distance L for the angle theta, separation = L theta",
                 "Two features that the telescope just resolves are separated on the Moon by the angle theta seen from the distance "
                 "L, so the separation is L theta."),
        ),
        check="Limiting case: x1 / pi is about 1.22, so the angle is about 1.22 lambda / D, the familiar Rayleigh limit; a larger opening "
              "or a shorter wavelength resolves smaller features. Order of magnitude: a fifteen centimetre opening resolves about two "
              "kilometres on the Moon."),
    "S310": Plan(
        approach="At the angle at which light polarised in the plane of incidence is not reflected, only the component perpendicular to "
                 "that plane is reflected. Find that angle, the angle of refraction, the amplitude coefficient for the perpendicular "
                 "component, and the reflected power.",
        steps=(
            Step("thB", "Brewster's law, tan(theta_B) = n for light going from air to glass",
                 "At this angle the reflected and refracted rays are at right angles and the component polarised in the plane of "
                 "incidence is not reflected at all."),
            Step("thT", "Snell's law, sin(theta_B) = n sin(theta_T)",
                 "The angle of refraction in the glass follows from Snell's law at the angle of incidence just found."),
            Step("rs", "Fresnel amplitude coefficient for light polarised perpendicular to the plane of incidence, r_s = -sin(theta_B - theta_T) / sin(theta_B + theta_T)",
                 "Only this component is reflected, with the amplitude coefficient given by the Fresnel formula for perpendicular "
                 "polarisation."),
            Step("Pr", "The component of the power perpendicular to the plane of incidence is P0 sin^2(psi); the reflected power is that "
                       "times r_s^2",
                 "The field splits into a component in the plane of incidence, which is not reflected, and one perpendicular to it, "
                 "with the fraction sin^2(psi) of the power, which is reflected with the fraction r_s^2."),
        ),
        check="Limiting cases: for psi = 0 (field in the plane of incidence) nothing is reflected, and for psi = 90 degrees the reflected "
              "fraction is r_s^2, which is about 0.15 for glass of index 1.5. The reflected power is always below the incident power."),
}

LEVELS: dict[str, str] = {
    "S301": "intro_university", "S302": "intro_university", "S303": "intro_university", "S304": "upper_university",
    "S305": "intro_university", "S306": "intro_university", "S307": "upper_university", "S308": "upper_university",
    "S309": "upper_university", "S310": "upper_university",
}

TOPICS: dict[str, str] = {
    "S301": "refraction through a parallel-sided glass plate and the sideways shift of a ray",
    "S302": "apparent depth of an object under two flat layers of different refractive index",
    "S303": "total internal reflection and the disc of light at the surface above an underwater lamp",
    "S304": "thin lens with a plane mirror behind it: two passes through the lens and the overall magnification",
    "S305": "refraction at the two faces of a prism and the deviation of a ray",
    "S306": "diffraction grating maximum of a given order and its position on a flat screen",
    "S307": "double-slit interference with a transparent film over one slit and the shift of the central fringe",
    "S308": "thin-film interference in a single-layer coating and the reflected power",
    "S309": "Rayleigh criterion for a circular aperture and the smallest resolved separation",
    "S310": "Brewster's angle and the reflection of obliquely polarised light",
}
