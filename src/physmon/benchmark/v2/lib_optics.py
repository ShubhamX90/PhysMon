"""Optics, waves and acoustics structures S61 to S67 and gold solution plans (Stage 14.19, domain batch).

Seven new structures (double-slit fringes, a polariser stack, a resonating closed pipe in a gas, a two-lens system, the acceptance
angle of an optical fibre, the angular separation of two lines in a grating order, the transmission of a glass plate with
multiple reflections), each with a typed graph, an independently coded numeric solver (a bracketing root finder, a ray-transfer
matrix, a quadrature over polarisation angle, a ray trace, a term-by-term series), at least four numeric instantiations and a
relevant edit. The module also carries gold solution plans for the existing structures S20, S21, S22 and S26 of this domain.

Admission status: agent-verified, not expert-reviewed. The certifier checks the graph, the solver route and the rendered numerals;
a blind verifier agent re-derives the answers. No human physicist has reviewed any text in this module.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq

from physmon.benchmark.v2.graph import Assumption, Structure
from physmon.benchmark.v2.library import _co, _in, _spec
from physmon.benchmark.v2.trace import Plan, Step

# --- solvers (independent routes; SI inputs in node order, including stated constants) -----------------


def _solve_double_slit(lam, d, big_d, m):
    # Paraxial path lengths from each slit to the screen point y, r = D + (y -+ d/2)^2 / (2 D); the bright fringe of order m is the
    # screen position where the path difference r1 - r2 equals m wavelengths, found with a bracketing root finder.
    def gap(y):
        r_upper = big_d + (y + d / 2.0) ** 2 / (2.0 * big_d)
        r_lower = big_d + (y - d / 2.0) ** 2 / (2.0 * big_d)
        return (r_upper - r_lower) - m * lam

    return float(brentq(gap, 0.0, 10.0 * big_d, xtol=1e-15, rtol=1e-14))


def _solve_polarisers(p0, th1, th2):
    # Average over the random polarisation direction of the incident light; project the field vector onto each axis in turn.
    axis1 = np.array([1.0, 0.0])
    axis2 = np.array([math.cos(th1), math.sin(th1)])
    axis3 = np.array([math.cos(th1 + th2), math.sin(th1 + th2)])

    def transmitted(phi):
        field = np.array([math.cos(phi), math.sin(phi)])  # unit incident intensity
        field = np.dot(field, axis1) * axis1
        field = np.dot(field, axis2) * axis2
        field = np.dot(field, axis3) * axis3
        return float(np.dot(field, field))

    mean, _ = quad(transmitted, 0.0, 2.0 * math.pi, epsabs=1e-14, epsrel=1e-12, limit=200)
    return float(p0 * mean / (2.0 * math.pi))


def _solve_pipe(gam, molar, temp, length, gas_r):
    # The speed from c^2 = gamma p / rho with rho from the ideal-gas law at an arbitrary pressure; then the second root of the
    # closed-open boundary condition cos(k L) = 0 (displacement node at the closed end, antinode at the open end).
    p_ref = 101325.0
    rho = p_ref * molar / (gas_r * temp)
    speed = math.sqrt(gam * p_ref / rho)
    kl = brentq(lambda x: math.cos(x), math.pi, 2.0 * math.pi, xtol=1e-15, rtol=1e-14)  # the root at 3 pi / 2
    return float(speed * kl / (2.0 * math.pi * length))


def _solve_two_lenses(f1, do, sep, f2):
    # Ray-transfer matrices: the image plane is where the B element of the system matrix from object plane to screen vanishes.
    def lens(f):
        return np.array([[1.0, 0.0], [-1.0 / f, 1.0]])

    def gap(s):
        return np.array([[1.0, s], [0.0, 1.0]])

    def b_element(s):
        total = gap(s) @ lens(f2) @ gap(sep) @ lens(f1) @ gap(do)
        return float(total[0, 1])

    return float(brentq(b_element, 1e-9, 1e3, xtol=1e-15, rtol=1e-14))


def _solve_fibre(n0, n_core, n_clad):
    # Ray trace: for an entry angle theta the ray refracts to theta_r inside the core and meets the cladding at 90 deg - theta_r.
    # The ray is guided while n_core cos(theta_r) >= n_clad; the largest such entry angle is the root of the margin.
    def margin(theta):
        sin_r = n0 * math.sin(theta) / n_core
        return n_core * math.sqrt(1.0 - sin_r * sin_r) - n_clad

    return float(brentq(margin, 0.0, 0.5 * math.pi, xtol=1e-15, rtol=1e-14))


def _solve_grating(spacing, lam1, lam2, order):
    # Each principal maximum is the root of the adjacent-slit phase condition 2 pi d sin(theta) / lambda = 2 pi m.
    def angle(lam):
        return brentq(lambda th: spacing * math.sin(th) - order * lam, 0.0, 0.5 * math.pi, xtol=1e-15, rtol=1e-14)

    return float(angle(lam2) - angle(lam1))


def _solve_slab(n_air, n_glass, p0):
    # Follow the beam: each pass through the plate transmits (1 - R)^2 and each internal round trip multiplies by R^2.
    r = ((n_glass - n_air) / (n_glass + n_air)) ** 2
    total, term = 0.0, p0 * (1.0 - r) ** 2
    for _ in range(200):
        total += term
        term *= r * r
    return float(total)


# --- structures --------------------------------------------------------------------------------------


def s61_double_slit_fringe() -> Structure:
    return Structure(
        "S61", "Position of a bright fringe in a double-slit pattern", "optics", "double_slit_fringe_position",
        (_in("lam", "length", "nm", "wavelength of the light", 600.0, (450.0, 700.0)),
         _in("d", "length", "mm", "separation of the two slits", 0.3, (0.15, 0.5)),
         _in("D", "length", "m", "distance from the slits to the screen", 2.0, (1.0, 3.0)),
         _in("m", "coefficient", "1", "order of the bright fringe (zero at the centre)", 3.0, (2.0, 5.0)),
         _co("dy", "length", "mm", "spacing between neighbouring bright fringes", "lam*D/d"),
         _co("y", "length", "mm", "distance of the bright fringe from the centre of the pattern", "m*dy")),
        "y",
        (Assumption("A-small", "All angles are small, so that sin of the angle, tan of the angle and the angle itself are equal.", "modelling", ("lam", "d", "D")),
         Assumption("A-slits", "The slits are narrow, the light is monochromatic and falls on them at normal incidence.", "modelling", ("lam", "d")),
         Assumption("A-order", "The central bright fringe is the fringe of order zero.", "boundary_condition", ("m",))),
        _spec("Monochromatic light of wavelength {lam} nm falls at normal incidence on two narrow slits that are {d} mm apart. A screen is "
              "placed {D} m beyond the slits. All angles are small, so the small-angle approximation holds.",
              "How far from the centre of the pattern is the bright fringe of order {m}? The central bright fringe is the fringe of order zero.",
              "distance of the bright fringe from the centre of the pattern", "mm",
              "A separate double-slit set-up B in another laboratory has a fringe at {v} {u} from its centre, but it is unrelated to this one.",
              "A reference double-slit set-up B has the same fringe at {v} {u} from its centre.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the interference.", "W", equivalent="cm"),
        ("D", 1.25), _solve_double_slit, 4,
        "the paraxial path difference from the two slits to the screen point, set equal to m wavelengths and solved for the position with a bracketing root finder",
        solver_rel_tol=1e-9,
        instances=({"lam": 600.0, "d": 0.3, "D": 2.0, "m": 3.0}, {"lam": 500.0, "d": 0.25, "D": 1.5, "m": 2.0},
                   {"lam": 650.0, "d": 0.2, "D": 2.4, "m": 4.0}, {"lam": 480.0, "d": 0.4, "D": 3.0, "m": 5.0}))


def s62_polariser_stack() -> Structure:
    return Structure(
        "S62", "Power of an unpolarised beam after three polarisers", "optics", "three_polariser_malus_stack",
        (_in("P0", "power", "mW", "power of the incident unpolarised beam", 40.0, (10.0, 100.0)),
         _in("th1", "angle", "deg", "angle between the transmission axes of the first and second polarisers", 30.0, (20.0, 60.0)),
         _in("th2", "angle", "deg", "angle between the transmission axes of the second and third polarisers", 40.0, (20.0, 60.0)),
         _co("P1", "power", "mW", "power of the beam after the first polariser", "P0/2"),
         _co("P2", "power", "mW", "power of the beam after the second polariser", "P1*cos(th1)**2"),
         _co("P3", "power", "mW", "power of the beam after the third polariser", "P2*cos(th2)**2")),
        "P3",
        (Assumption("A-ideal", "The polarisers are ideal: each passes all of the light polarised along its transmission axis and none of the light polarised across it.", "modelling", ("P0",)),
         Assumption("A-beam", "The beam is uniform and unpolarised, so power and intensity are proportional.", "modelling", ("P0",)),
         Assumption("A-angles", "The angles are the angles between the transmission axes of successive polarisers.", "boundary_condition", ("th1", "th2"))),
        _spec("An unpolarised laser beam of power {P0} mW passes in turn through three ideal polarisers. The transmission axis of the second "
              "polariser makes an angle of {th1} degrees with that of the first, and the transmission axis of the third polariser makes an "
              "angle of {th2} degrees with that of the second.",
              "What is the power of the beam that emerges from the third polariser?", "power of the emerging beam", "mW",
              "A separate laser B on another bench emits a beam of {v} {u}, but it is unrelated to this stack.",
              "A reference beam B has a power of {v} {u}.",
              "A separate lamp B flickers at {v} {u}, but it plays no part in the polarisation.", "Hz", equivalent="W"),
        ("th1", 1.5), _solve_polarisers, 3,
        "an average over the random incident polarisation direction of the squared field after projecting it onto each axis in turn, by quadrature",
        solver_rel_tol=1e-9,
        instances=({"P0": 40.0, "th1": 30.0, "th2": 40.0}, {"P0": 60.0, "th1": 45.0, "th2": 45.0},
                   {"P0": 100.0, "th1": 25.0, "th2": 35.0}, {"P0": 80.0, "th1": 50.0, "th2": 20.0}))


def s63_closed_pipe_second_resonance() -> Structure:
    return Structure(
        "S63", "Second-lowest resonance of a closed pipe filled with a gas", "acoustics", "closed_pipe_gas_resonance",
        (_in("gam", "coefficient", "1", "ratio of the specific heats of the gas", 1.4, (1.3, 1.67)),
         _in("M", "molar_mass", "g/mol", "molar mass of the gas", 29.0, (4.0, 44.0)),
         _in("T", "temperature", "K", "temperature of the gas", 293.0, (250.0, 350.0)),
         _in("L", "length", "m", "length of the pipe", 0.6, (0.3, 1.2)),
         _in("R", "gas_constant", "J/(mol*K)", "molar gas constant, a stated constant", 8.314, (8.3, 8.33), provenance="assumed"),
         _co("c", "speed", "m/s", "speed of sound in the gas", "sqrt(gam*R*T/M)"),
         _co("lam", "length", "m", "wavelength of the second-lowest resonance", "4*L/3"),
         _co("f", "frequency", "Hz", "frequency of the second-lowest resonance", "c/lam")),
        "f",
        (Assumption("A-ideal", "The gas is ideal and sound travels through it adiabatically.", "modelling", ("gam", "M", "T")),
         Assumption("A-R", "The molar gas constant is the stated constant.", "modelling", ("R",)),
         Assumption("A-pipe", "The pipe is closed at one end and open at the other, its width is much smaller than its length, and end corrections are neglected.", "boundary_condition", ("L",))),
        _spec("A pipe of length {L} m is closed at one end and open at the other. It is filled with an ideal gas of molar mass {M} g/mol "
              "and ratio of specific heats {gam}, at a temperature of {T} K. Sound travels through the gas adiabatically. Take "
              "R = {R} J/(mol·K) and neglect end corrections.",
              "What is the second-lowest frequency at which the gas column in the pipe resonates? The lowest is the fundamental.",
              "second-lowest resonant frequency of the gas column", "Hz",
              "A separate tuning fork B in another room vibrates at {v} {u}, but it is unrelated to this pipe.",
              "A reference pipe B has a resonance at {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the resonance.", "W", equivalent="kHz"),
        ("L", 1.5), _solve_pipe, 5,
        "the speed from c squared equal to gamma p over rho with rho from the ideal-gas law, and the resonance as the second root of the closed-open boundary condition cos(kL) = 0",
        solver_rel_tol=1e-9,
        instances=({"gam": 1.4, "M": 29.0, "T": 293.0, "L": 0.6, "R": 8.314}, {"gam": 1.4, "M": 29.0, "T": 300.0, "L": 0.45, "R": 8.314},
                   {"gam": 1.67, "M": 4.0, "T": 290.0, "L": 0.5, "R": 8.314}, {"gam": 1.3, "M": 44.0, "T": 280.0, "L": 0.9, "R": 8.314}))


def s64_two_lens_image() -> Structure:
    return Structure(
        "S64", "Final image distance for two thin lenses on one axis", "optics", "two_thin_lens_system_image",
        (_in("f1", "length", "cm", "focal length of the first lens", 12.0, (10.0, 16.0)),
         _in("do", "length", "cm", "distance of the object from the first lens", 36.0, (30.0, 60.0)),
         _in("sep", "length", "cm", "distance between the two lenses", 45.0, (45.0, 70.0)),
         _in("f2", "length", "cm", "focal length of the second lens", 9.0, (6.0, 9.0)),
         _co("di1", "length", "cm", "distance of the first image from the first lens", "f1*do/(do - f1)"),
         _co("o2", "length", "cm", "distance of the first image in front of the second lens", "sep - di1"),
         _co("di2", "length", "cm", "distance of the final image behind the second lens", "f2*o2/(o2 - f2)")),
        "di2",
        (Assumption("A-thin", "Both lenses are thin converging lenses on a common axis, and the rays are close to the axis.", "modelling", ("f1", "f2")),
         Assumption("A-object", "The object is on the axis, in front of the first lens and farther from it than the focal length.", "boundary_condition", ("do",)),
         Assumption("A-order", "The first image forms between the two lenses, so that it acts as a real object for the second lens.", "boundary_condition", ("sep",))),
        _spec("A thin converging lens of focal length {f1} cm is used to image an object that is placed {do} cm in front of it on the axis. "
              "A second thin converging lens, of focal length {f2} cm, is placed on the same axis {sep} cm behind the first lens.",
              "How far behind the second lens is the final image formed?", "distance of the final image from the second lens", "cm",
              "A separate camera B in another laboratory has its sensor {v} {u} behind its lens, but it is unrelated to these lenses.",
              "A reference lens system B forms its image {v} {u} behind its last lens.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the imaging.", "W", equivalent="mm"),
        ("f2", 0.8), _solve_two_lenses, 4,
        "ray-transfer matrices for the two lenses and the free spaces, with the image plane found as the root of the B element of the system matrix",
        solver_rel_tol=1e-9,
        instances=({"f1": 12.0, "do": 36.0, "sep": 45.0, "f2": 9.0}, {"f1": 10.0, "do": 30.0, "sep": 50.0, "f2": 7.0},
                   {"f1": 15.0, "do": 45.0, "sep": 60.0, "f2": 7.5}, {"f1": 12.0, "do": 60.0, "sep": 48.0, "f2": 8.0}))


def s65_fibre_acceptance_angle() -> Structure:
    return Structure(
        "S65", "Acceptance angle of a step-index optical fibre", "optics", "fibre_acceptance_angle_tir",
        (_in("n0", "coefficient", "1", "refractive index of the air outside the fibre, a stated constant", 1.0, (1.0, 1.003), provenance="assumed"),
         _in("n1", "coefficient", "1", "refractive index of the fibre core", 1.5, (1.46, 1.6)),
         _in("n2", "coefficient", "1", "refractive index of the cladding", 1.44, (1.4, 1.45)),
         _co("thc", "angle", "deg", "critical angle at the core-cladding boundary", "asin(n2/n1)"),
         _co("thr", "angle", "deg", "largest angle between a guided ray and the axis, inside the core", "pi/2 - thc"),
         _co("thm", "angle", "deg", "largest angle of incidence on the fibre end, measured from the axis, for a guided ray", "asin(n1*sin(thr)/n0)")),
        "thm",
        (Assumption("A-air", "The refractive index of the air is the stated constant.", "modelling", ("n0",)),
         Assumption("A-fibre", "The fibre is straight and has a core of uniform refractive index surrounded by a cladding of lower uniform refractive index.", "modelling", ("n1", "n2")),
         Assumption("A-meridional", "The ray travels in a plane that contains the axis of the fibre, and the end face is flat and perpendicular to the axis.", "boundary_condition", ("n1",))),
        _spec("Light enters the flat end of a straight step-index optical fibre from air of refractive index {n0}. The core of the fibre has "
              "refractive index {n1} and the cladding around it has refractive index {n2}. Consider rays in a plane containing the axis of the fibre.",
              "What is the largest angle, measured from the axis of the fibre, at which a ray can strike the end face and still be guided along "
              "the fibre by total internal reflection?", "largest angle of acceptance", "deg",
              "A separate fibre B in another cable reaches a bend of {v} {u}, but it is unrelated to this fibre.",
              "A reference fibre B has an acceptance angle of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the guiding.", "W", equivalent="rad"),
        ("n1", 1.06), _solve_fibre, 3,
        "a ray trace over entry angles: the largest entry angle is the root of the margin n1 cos(theta_r) minus n2, with theta_r from Snell's law at the end face",
        solver_rel_tol=1e-9,
        instances=({"n0": 1.0, "n1": 1.5, "n2": 1.44}, {"n0": 1.0, "n1": 1.48, "n2": 1.41}, {"n0": 1.0, "n1": 1.55, "n2": 1.45},
                   {"n0": 1.0, "n1": 1.6, "n2": 1.42}))


def s66_grating_line_separation() -> Structure:
    return Structure(
        "S66", "Angular separation of two spectral lines in a grating order", "optics", "grating_two_wavelength_separation",
        (_in("d", "length", "μm", "spacing between neighbouring slits of the grating", 4.0, (2.5, 6.0)),
         _in("lam1", "length", "nm", "shorter wavelength in the beam", 450.0, (400.0, 480.0)),
         _in("lam2", "length", "nm", "longer wavelength in the beam", 650.0, (600.0, 700.0)),
         _in("m", "coefficient", "1", "order of the diffraction maxima that are compared", 2.0, (1.0, 3.0)),
         _co("th1", "angle", "deg", "diffraction angle of the shorter wavelength", "asin(m*lam1/d)"),
         _co("th2", "angle", "deg", "diffraction angle of the longer wavelength", "asin(m*lam2/d)"),
         _co("dth", "angle", "deg", "angular separation of the two maxima", "th2 - th1")),
        "dth",
        (Assumption("A-grating", "The grating is a plane transmission grating with equally spaced narrow slits, and the beam is collimated and falls on it at normal incidence.", "modelling", ("d",)),
         Assumption("A-side", "Both maxima are on the same side of the undeviated central beam, which is the order zero maximum.", "boundary_condition", ("m",)),
         Assumption("A-wave", "Each wavelength has its own sharp maximum of the stated order.", "modelling", ("lam1", "lam2"))),
        _spec("A beam of collimated light that contains two wavelengths, {lam1} nm and {lam2} nm, falls at normal incidence on a transmission "
              "diffraction grating whose neighbouring slits are {d} μm apart.",
              "What is the angular separation between the two wavelengths in the maxima of order {m}, on one side of the central beam? "
              "The undeviated central beam is the maximum of order zero.", "angular separation of the two maxima", "deg",
              "A separate spectrometer B in another laboratory resolves two lines {v} {u} apart, but it is unrelated to this grating.",
              "A reference grating B separates the two lines by {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the diffraction.", "W", equivalent="rad"),
        ("d", 0.75), _solve_grating, 4,
        "each maximum as the root of the adjacent-slit phase condition d sin(theta) = m lambda, found with a bracketing root finder, then the difference",
        solver_rel_tol=1e-9,
        instances=({"d": 4.0, "lam1": 450.0, "lam2": 650.0, "m": 2.0}, {"d": 3.0, "lam1": 480.0, "lam2": 620.0, "m": 2.0},
                   {"d": 5.0, "lam1": 420.0, "lam2": 690.0, "m": 3.0}, {"d": 2.5, "lam1": 410.0, "lam2": 600.0, "m": 1.0}))


def s67_glass_plate_transmission() -> Structure:
    return Structure(
        "S67", "Power transmitted through a glass plate with multiple reflections", "optics", "slab_incoherent_multiple_reflection",
        (_in("na", "coefficient", "1", "refractive index of the air around the plate, a stated constant", 1.0, (1.0, 1.003), provenance="assumed"),
         _in("n", "coefficient", "1", "refractive index of the glass", 1.5, (1.4, 1.9)),
         _in("P0", "power", "mW", "power of the incident beam", 50.0, (10.0, 100.0)),
         _co("Rf", "coefficient", "1", "fraction of the power reflected at a single surface", "((n - na)/(n + na))**2"),
         _co("Tf", "coefficient", "1", "fraction of the power transmitted by the whole plate", "(1 - Rf)/(1 + Rf)"),
         _co("Pt", "power", "mW", "power of the transmitted beam", "Tf*P0")),
        "Pt",
        (Assumption("A-air", "The refractive index of the air is the stated constant.", "modelling", ("na",)),
         Assumption("A-incoherent", "The plate is parallel-sided and does not absorb light, and the beams reflected inside it do not interfere, so that their powers add.", "modelling", ("n",)),
         Assumption("A-normal", "The beam falls at normal incidence and the reflectance of each surface is given by the Fresnel formula for normal incidence.", "boundary_condition", ("P0",))),
        _spec("A parallel-sided plate of glass of refractive index {n} stands in air of refractive index {na}. A beam of light of power {P0} mW "
              "falls on it at normal incidence. The glass does not absorb light, and the light reflected back and forth inside the plate is not "
              "coherent, so that the powers of the different beams add.",
              "What is the total power of the light transmitted through the plate, including all the beams that have been reflected inside it?",
              "total transmitted power", "mW",
              "A separate laser B on another bench emits a beam of {v} {u}, but it is unrelated to this plate.",
              "A reference beam B transmitted through another plate has a power of {v} {u}.",
              "A separate lamp B flickers at {v} {u}, but it plays no part in the transmission.", "Hz", equivalent="W"),
        ("n", 1.25), _solve_slab, 3,
        "the transmitted beams followed one by one and summed term by term, each pass transmitting (1 - R) squared and each internal round trip multiplying by R squared",
        solver_rel_tol=1e-9,
        instances=({"na": 1.0, "n": 1.5, "P0": 50.0}, {"na": 1.0, "n": 1.7, "P0": 80.0}, {"na": 1.0, "n": 1.45, "P0": 30.0},
                   {"na": 1.0, "n": 1.8, "P0": 100.0}))


ALL = (s61_double_slit_fringe, s62_polariser_stack, s63_closed_pipe_second_resonance, s64_two_lens_image, s65_fibre_acceptance_angle,
       s66_grating_line_separation, s67_glass_plate_transmission)


def all_structures() -> list[Structure]:
    return [factory() for factory in ALL]


# --- gold solution plans -----------------------------------------------------------------------------

PLANS: dict[str, Plan] = {
    # ---- new structures ----
    "S61": Plan(
        approach="We want the position of one bright fringe on the screen. Bright fringes lie where the paths from the two slits differ by a "
                 "whole number of wavelengths, and for small angles they are evenly spaced, so we first find the fringe spacing and then count "
                 "fringes outward from the central one.",
        steps=(
            Step("dy",
                 "Young's double-slit condition: a bright fringe occurs where the path difference d sin(theta) equals m times the wavelength; "
                 "for small angles sin(theta) is about tan(theta) = y/D, so neighbouring fringes are a distance lam D / d apart",
                 "The small-angle approximation is stated, so the pattern is a ladder of equally spaced fringes, and the spacing is the one "
                 "quantity that fixes the whole pattern; it is found from the wavelength, the screen distance and the slit separation."),
            Step("y",
                 "Position of the m-th bright fringe: y = m times the fringe spacing, which is the condition d y / D = m lam solved for y",
                 "The central fringe is the fringe of order zero and the fringes are evenly spaced, so the fringe of order m is m spacings "
                 "away from the centre; this is the distance the question asks for.")),
        check="The dimensions are right: a wavelength times a ratio of two lengths is a length. Halving the slit separation doubles the "
              "spacing, and the fringe of order zero sits at the centre. For visible light, slits a fraction of a millimetre apart and a "
              "screen a few metres away give fringes a few millimetres apart, which is what is seen in practice."),
    "S62": Plan(
        approach="Unpolarised light is first made polarised by the first polariser; every later polariser then removes the part of the light "
                 "that is not polarised along its axis. We therefore apply the one-half rule for unpolarised light once, then Malus's law "
                 "twice, working along the stack in order.",
        steps=(
            Step("P1",
                 "Transmission of unpolarised light through an ideal polariser: the polarisation direction is random, the average of "
                 "cos squared over all directions is one half, so half of the incident power is transmitted",
                 "The incident beam has no definite polarisation direction, so Malus's law cannot be used yet; the first polariser halves "
                 "the power and leaves light polarised along its axis."),
            Step("P2",
                 "Malus's law: the transmitted power is the incident power times cos squared of the angle between the polarisation "
                 "direction and the transmission axis (the field component along the axis is E cos(theta) and power goes as E squared)",
                 "After the first polariser the light is polarised along axis one, and axis two makes the first stated angle with it, "
                 "so Malus's law gives the power that gets through the second polariser."),
            Step("P3",
                 "Malus's law again, applied to the light that leaves the second polariser, which is polarised along axis two",
                 "Axis three makes the second stated angle with axis two, so the power after the third polariser is the power after the "
                 "second one times cos squared of that angle; this is the power asked for.")),
        check="The result is half the incident power times two factors that each lie between zero and one, so it cannot exceed half the "
              "incident power. If an angle were zero its polariser would change nothing, and if it were ninety degrees no light would get through."),
    "S63": Plan(
        approach="The resonant frequency of a pipe is the speed of sound divided by the wavelength of the standing wave. We find the speed "
                 "of sound in the gas from its temperature and molar mass, find the wavelength of the second-lowest standing wave that the "
                 "closed-open boundary conditions allow, and divide.",
        steps=(
            Step("c",
                 "Speed of sound in an ideal gas for adiabatic compressions: c = sqrt(gamma R T / M), which follows from c squared = gamma p / "
                 "rho and the ideal-gas law p = rho R T / M",
                 "The wave speed is needed to convert a wavelength into a frequency. The gas is ideal and sound is adiabatic, so the "
                 "speed depends only on the ratio of specific heats, the temperature and the molar mass (in kilograms per mole)."),
            Step("lam",
                 "Standing waves in a pipe closed at one end and open at the other: a displacement node at the closed end and an "
                 "antinode at the open end require L = (2k - 1) lam / 4, so the resonances are the odd quarter-wavelength fits",
                 "The lowest resonance has L = lam/4 and the second-lowest has L = 3 lam/4, so the wavelength of the second-lowest "
                 "resonance is four thirds of the pipe length."),
            Step("f",
                 "The wave relation for a periodic wave: speed = frequency times wavelength",
                 "We have the wave speed in the gas and the wavelength of the standing wave, so their ratio is the resonant frequency asked for.")),
        check="The second-lowest resonance of a closed pipe is three times the fundamental, c/(4L), so the answer must equal 3c/(4L). The "
              "speed of sound is a few hundred metres per second for heavy gases and air and about a thousand for a light gas such as "
              "helium, so frequencies of order a hundred hertz to a few kilohertz are reasonable for a pipe of this length."),
    "S64": Plan(
        approach="The final image is found by imaging in two stages: the first lens makes an image of the object, and that image is the "
                 "object for the second lens. Each stage uses the thin-lens equation, and the object distance for the second lens follows "
                 "from the lens separation.",
        steps=(
            Step("di1",
                 "The thin-lens (Gaussian) equation, 1/f = 1/do + 1/di, with distances positive for real objects and images, which "
                 "follows from paraxial refraction at the two surfaces of a thin lens",
                 "The first lens acts alone on the original object, so its image distance comes from its focal length and the object "
                 "distance: solving gives f do / (do - f), positive for an object beyond the focal length (a real image)."),
            Step("o2",
                 "Geometry of the lens system: the image formed by the first lens is the object of the second lens, and an object that lies "
                 "in front of the second lens has a positive object distance",
                 "The first image lies di1 behind the first lens while the second lens lies at the separation behind it, so the first "
                 "image is a real object at the distance (separation minus di1) in front of the second lens."),
            Step("di2",
                 "The thin-lens equation again, applied to the second lens with the object distance found above",
                 "The second lens now images the first image, so the same relation f2 o2 / (o2 - f2) gives the distance behind the "
                 "second lens at which the final image forms; a positive value means a real image behind it.")),
        check="If the second lens were absent (or had a very long focal length) the light would simply continue to the first image, so the "
              "second step is consistent with the first. The first image distance exceeds the first focal length, and the final image "
              "distance exceeds the second focal length because o2 is larger than f2, so the final image is real and behind the second lens."),
    "S65": Plan(
        approach="A ray is guided when it strikes the core-cladding boundary at an angle of incidence at least equal to the critical angle. "
                 "The steepest guided ray inside the core is found from the critical angle, and Snell's law at the end face then gives the "
                 "largest angle in air from which such a ray can enter.",
        steps=(
            Step("thc",
                 "Total internal reflection and the critical angle: at the core-cladding boundary Snell's law with a refraction angle of "
                 "ninety degrees gives sin(theta_c) = n2 / n1",
                 "A ray is trapped only if its angle of incidence on the boundary is at least the critical angle, so the critical angle "
                 "sets the limiting ray that is still guided."),
            Step("thr",
                 "Geometry of the straight fibre: the normal to the core-cladding boundary is perpendicular to the axis, so a ray whose "
                 "angle of incidence on the boundary is theta_c makes the angle (ninety degrees minus theta_c) with the axis",
                 "This converts the limiting angle at the side wall into the angle that the limiting ray makes with the axis inside the "
                 "core, which is also its angle of refraction at the end face because the end-face normal lies along the axis."),
            Step("thm",
                 "Snell's law of refraction at the end face: n0 sin(theta) = n1 sin(theta_r), with both angles measured from the axis, "
                 "which is the normal to the end face",
                 "The limiting ray inside the core came from the largest entry angle, so solving for theta gives the largest angle in air "
                 "that is still guided; this is the acceptance angle asked for.")),
        check="Combining the steps gives n0 sin(theta_max) = sqrt(n1 squared - n2 squared), the numerical aperture of the fibre. If the "
              "cladding index approached the core index, the acceptance angle would shrink to zero, and the sine of the angle must stay "
              "below one, which it does for these indices."),
    "S66": Plan(
        approach="Each wavelength has its own diffraction angle in a given order, given by the grating equation. We find the angle for each "
                 "of the two wavelengths in the stated order and subtract.",
        steps=(
            Step("th1",
                 "The grating equation for a plane grating at normal incidence: the maxima lie where the path difference between "
                 "neighbouring slits, d sin(theta), equals a whole number m of wavelengths",
                 "The slit spacing and the order are given, so the shorter wavelength has its maximum of that order at "
                 "theta = asin(m lam1 / d), with the sine less than one so that the order exists."),
            Step("th2",
                 "The grating equation again, d sin(theta) = m lam, now with the longer wavelength",
                 "The same slit spacing and order apply, so the longer wavelength is diffracted to theta = asin(m lam2 / d), "
                 "farther from the central beam than the shorter one."),
            Step("dth",
                 "Definition of the angular separation of two maxima on the same side of the central beam as the difference of their angles",
                 "Both maxima lie on the same side of the undeviated beam, so subtracting the smaller angle from the larger gives the "
                 "separation the question asks for.")),
        check="The longer wavelength must be diffracted through the larger angle, so the separation is positive. For small angles it is "
              "about m (lam2 - lam1) / d, so a coarser grating (a larger spacing) would separate the lines less, and the true separation "
              "is a little larger than this estimate because of the asin."),
    "S67": Plan(
        approach="Some power is reflected at each of the two surfaces of the plate, and the light trapped between the surfaces bounces back "
                 "and forth, adding a little to the transmitted power on every round trip. We find the reflectance of one surface, sum the "
                 "whole series of transmitted beams, and multiply by the incident power.",
        steps=(
            Step("Rf",
                 "The Fresnel reflectance at normal incidence, R = ((n - na) / (n + na)) squared, which follows from continuity of the "
                 "tangential electric and magnetic fields at an interface",
                 "Both surfaces of the plate are air-glass interfaces and the beam is at normal incidence, so each surface reflects the "
                 "same fraction R of the power that reaches it, from whichever side it arrives."),
            Step("Tf",
                 "Incoherent multiple reflections in a lossless plate: the first transmitted beam carries (1 - R) squared, each round trip "
                 "inside multiplies by R squared, and the series (1 - R) squared (1 + R squared + R to the fourth + ...) sums to (1 - R) / (1 + R)",
                 "The powers of the beams add because they do not interfere, and no light is absorbed, so the geometric series of "
                 "transmitted beams gives the fraction of the incident power that the plate transmits in total."),
            Step("Pt",
                 "Definition of the transmitted fraction: the transmitted power equals the transmittance times the incident power",
                 "The beam power is given and the fraction transmitted by the plate is known, so their product is the transmitted power asked for.")),
        check="If the glass index equalled the air index there would be no reflection and all of the power would be transmitted. The total "
              "reflected fraction is 2R/(1+R), and the transmitted fraction plus this must equal one (no absorption); the transmitted "
              "fraction exceeds the single-pass value (1 - R) squared because of the extra beams, and it is less than one."),
    # ---- existing structures: gold plans only ----
    "S20": Plan(
        approach="We are asked where the real image forms. The thin-lens equation relates the focal length, the object distance and the "
                 "image distance, so we solve it for the image distance.",
        steps=(
            Step("di",
                 "The thin-lens (Gaussian) equation, 1/f = 1/do + 1/di, with real objects and real images counted positive; it follows "
                 "from paraxial refraction at the two surfaces of a thin lens",
                 "The lens is thin and the rays are close to the axis, so the equation applies; solving it gives the image distance "
                 "di = f do / (do - f), which is positive when the object is beyond the focal length, so the image is real."),),
        check="For a very distant object the image distance tends to the focal length. For an object at twice the focal length the image "
              "is also at twice the focal length, and as the object approaches the focal point the image moves out to infinity."),
    "S26": Plan(
        approach="We want the angle of the refracted ray. The ray bends at a flat interface according to Snell's law, so we apply it with "
                 "both angles measured from the normal and solve for the angle in the second medium.",
        steps=(
            Step("theta2",
                 "Snell's law of refraction, n1 sin(theta1) = n2 sin(theta2), with both angles measured from the normal to the interface",
                 "The light crosses a flat interface between two media of known refractive index, so the sine of the refraction angle is "
                 "n1 sin(theta1) / n2, and taking the inverse sine gives the angle in the second medium."),),
        check="At normal incidence the ray is not deflected. If the second index is larger than the first, the ray bends toward the normal, "
              "so the refraction angle is smaller than the incidence angle, and with equal indices the two angles are equal."),
    "S21": Plan(
        approach="The source moves toward a listener at rest, so the sound waves are crowded together in front of it. We find the shortened "
                 "wavelength in the air and divide the speed of sound by it to get the frequency that the listener hears.",
        steps=(
            Step("fo",
                 "The Doppler effect for a moving source and a stationary listener: f_obs = f c / (c - vs), because in one period the "
                 "source advances vs/f and the wavelength in the air becomes (c - vs)/f",
                 "The air is still, so the sound still travels at c relative to the listener, but each wave crest is emitted closer to the "
                 "previous one; the listener therefore receives c divided by the shortened wavelength, a higher frequency than that emitted."),),
        check="If the source were at rest the heard frequency would equal the emitted one. For a source much slower than sound the shift "
              "is about f vs / c, and the heard frequency rises without limit as the source speed approaches the speed of sound."),
    "S22": Plan(
        approach="The fundamental standing wave on a string fixed at both ends has a wavelength of twice the string length. We find the "
                 "wave speed from the tension and the mass per unit length, and divide it by that wavelength.",
        steps=(
            Step("f1",
                 "Wave speed on a stretched string, v = sqrt(T / mu) with mu = m / L, together with the fundamental standing wave "
                 "of a string fixed at both ends, lam = 2 L, so that f1 = v / (2 L) = sqrt(T / (m L)) / 2",
                 "The string is uniform and fixed at both ends, so the mass per unit length is the mass divided by the length and the "
                 "lowest mode fits half a wavelength into the string; the frequency is the wave speed divided by that wavelength."),),
        check="Dimensionally, the square root of newtons per (kilogram metre) is one over a second. A tighter or lighter or shorter string "
              "gives a higher pitch, and doubling the tension raises the frequency by a factor of the square root of two."),
}

LEVELS: dict[str, str] = {
    "S61": "high_school", "S62": "high_school", "S63": "intro_university", "S64": "intro_university", "S65": "intro_university",
    "S66": "intro_university", "S67": "upper_university",
    "S20": "high_school", "S26": "high_school", "S21": "intro_university", "S22": "intro_university",
}

TOPICS: dict[str, str] = {
    "S61": "double-slit interference, fringe position",
    "S62": "polarisation, Malus law with an unpolarised beam",
    "S63": "standing waves in a closed pipe, speed of sound in a gas",
    "S64": "thin lens combination, image of an image",
    "S65": "total internal reflection, acceptance angle of a fibre",
    "S66": "diffraction grating, angular separation of two wavelengths",
    "S67": "Fresnel reflectance and multiple reflections in a glass plate",
    "S20": "thin lens, image distance",
    "S26": "refraction, Snell law",
    "S21": "Doppler effect, moving source",
    "S22": "standing waves on a string, fundamental frequency",
}
