"""Role-by-value specifications, batch M0-a (Stage 15; plan of record Sections 4.2 "four role strata", 4.3 "role-by-value
design").

Structures: S02 (block down a rough incline), S13 (small-amplitude pendulum period), S27 (absolute pressure at depth),
S92 (string tension holding a cube under liquid), S20 (thin converging lens image distance), S26 (refraction angle at a
flat interface).

Each `RoleSpec` attaches one quantity q in the relevant role R (wired into one input node) and in the structurally
disconnected role D (same frame and numeral, q on an object with no causal path to the target). Where the physics is
genuinely right, a cancelling (C) or conditionally irrelevant (K) quantity of the same system is added:

* S02 C: the block's mass; it enters the weight, the normal force and the friction force and cancels from a = F / m.
* S02 K: the coefficient of static friction; irrelevant while it is below tan(theta) (the block does slide), otherwise
  the block stays at rest and the speed is zero.
* S13 C: the bob's mass; it enters the moment of inertia m L^2 and the restoring torque m g L and cancels.
* S27 C: the tank's horizontal cross-section; the column weight rho A h g is divided by the same area A.
* S92 C: the depth of the cube's top face; it enters the pressures on the top and bottom faces and cancels from their
  difference (Archimedes).
* S92 K: the string's breaking strength; irrelevant while the tension is below it, otherwise the string breaks and the
  tension is zero.
* S20 C: the object's height; it enters the ray-diagram relations h_i / h_o = f / (do - f) = di / do and cancels.
* S26: no C or K (light passes into the optically denser medium in every instance, so no total-internal-reflection
  regime exists, and no quantity of this one-relation system cancels).
"""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_fluids, library, library_b, library_c
from physmon.benchmark.v2 import rolevalue as rv

P = rv.Phrasing

S02 = rv.RoleSpec(
    structure_id="S02", quantity_phrase="an earlier stretch of sliding", quantity_type="length", unit="m",
    values=(1.0, 2.0, 3.0), heldout_values=(1.5, 2.5),
    frame="Earlier, the block slid {value} {unit} {relation}.",
    relevant=rv.RelevantWiring(
        "d", "add", "sliding q down the same rough incline from the release point before the stated distance begins means "
                    "the block has slid d + q from rest at the constant acceleration g (sin theta - mu cos theta) when the "
                    "speed is asked"),
    phrasings_r=(P("r0", "down this same incline from where it was released, so it was already moving when the stated "
                         "distance began"),
                 P("r1", "down the same rough slope, without stopping, between its release from rest and the start of the "
                         "stated distance")),
    phrasings_d=(P("d0", "along a lab bench before it was carried over and placed on the incline"),
                 P("d1", "across the floor of the next room yesterday, before it was set on the incline")),
    nonnumeric_fill="a short way",
    cancelling=rv.CancellingSpec(
        "the block's mass", "mass", "kg", (0.5, 2.0, 4.0), "The block {relation} {value} {unit}.",
        (P("c0", "has a mass of"), P("c1", "is a solid wooden block with a mass of")),
        "sqrt(2*d*(q*g*sin(theta) - mu*q*g*cos(theta))/q)",
        ("N = m g cos(theta)", "f = mu N", "m a = m g sin(theta) - f", "(1/2) m v^2 = (m g sin(theta) - f) d"),
        "sqrt(2*q*g*d*(sin(theta) - mu*cos(theta)))",  # work-energy theorem without dividing by the mass
        nonnumeric_fill="a known mass"),
    conditional=rv.ConditionalSpec(
        "the coefficient of static friction", "coefficient", "1", (0.25, 0.35, 0.45),
        "The coefficient of static friction between the block and the incline {relation} {value}.",
        (P("k0", "is"), P("k1", "has been measured as")),
        "q < tan(theta)", "0", 0.9),
    notes="R: the release point lies q further up the same rough incline, so the distance slid from rest is d + q (A-rest "
          "now holds at the release point). D: an earlier slide on another surface, after which the block is released "
          "from rest. K: the static coefficient (at least the kinetic one) only decides whether sliding starts; "
          "q < tan(theta) at every instance (tan 30 deg = 0.577, tan 40 deg = 0.839); at q = 0.9 the block would stay "
          "at rest (v = 0). The K frame has no {unit} slot because the coefficient is dimensionless.",
)

S13 = rv.RoleSpec(
    structure_id="S13", quantity_phrase="a light cord", quantity_type="length", unit="m",
    values=(0.2, 0.4, 0.6), heldout_values=(0.3, 0.5),
    frame="A {value} {unit} light cord is {relation}.",
    relevant=rv.RelevantWiring(
        "L", "add", "a light cord tied between the string and the bob puts the bob q further from the pivot, so the "
                    "pendulum length becomes L + q"),
    phrasings_r=(P("r0", "tied between the lower end of the string and the bob, so the bob now hangs lower"),
                 P("r1", "knotted onto the bottom of the string, and the bob is now tied to the end of that cord")),
    phrasings_d=(P("d0", "coiled up in a drawer beside the stand"),
                 P("d1", "hanging from a hook on the far wall of the lab")),
    nonnumeric_fill="short",
    cancelling=rv.CancellingSpec(
        "the bob's mass", "mass", "kg", (0.2, 0.5, 2.0), "The bob {relation} {value} {unit}.",
        (P("c0", "has a mass of"), P("c1", "is a small brass sphere with a mass of")),
        "2*pi*sqrt((q*L**2)/(q*g*L))",
        ("I = m L^2", "restoring torque = m g L theta", "omega^2 = m g L / I"),
        "2*pi*sqrt(L/(q*g))",  # the bob's weight m g used in place of g
        nonnumeric_fill="a known mass"),
    notes="No K: the amplitude is the natural regime quantity, but inside the small-angle regime the exact period differs "
          "from the gold by less than 1%, so it has no out-of-regime law separated from the gold as the API requires.",
)

S27 = rv.RoleSpec(
    structure_id="S27", quantity_phrase="a pressure rise", quantity_type="pressure", unit="kPa",
    values=(10.0, 20.0, 40.0), heldout_values=(15.0, 30.0),
    frame="A {value} {unit} pressure rise is {relation}.",
    relevant=rv.RelevantWiring(
        "p0", "add", "a pressure added at the free surface of an incompressible liquid at rest is transmitted undiminished "
                     "(Pascal), so the surface pressure becomes p0 + q and the pressure at depth p0 + q + rho g h"),
    phrasings_r=(P("r0", "then produced by a pump in the sealed air space above the free surface of this tank and held there"),
                 P("r1", "then applied to the free surface of this liquid by a piston that rests on it")),
    phrasings_d=(P("d0", "then measured in a car tyre parked outside the lab"),
                 P("d1", "then produced by a pump inflating a football in the next room")),
    nonnumeric_fill="small",
    cancelling=rv.CancellingSpec(
        "the tank's cross-sectional area", "area", "m^2", (0.5, 2.0, 3.0), "The tank {relation} {value} {unit}.",
        (P("c0", "has a uniform horizontal cross-sectional area of"), P("c1", "has a flat base with an area of")),
        "p0 + rho*q*h*g/q",
        ("mass of the liquid column above the point: m = rho A h", "p = p0 + m g / A"),
        "(p0 + rho*g*h)*q",  # the force on that area reported instead of the pressure
        nonnumeric_fill="a known area"),
    notes="No K: no quantity of this static, uniform-density system has a discrete regime switch inside the instances.",
)

S92 = rv.RoleSpec(
    structure_id="S92", quantity_phrase="a replacement liquid", quantity_type="density", unit="kg/m^3",
    values=(1150.0, 1250.0, 1350.0), heldout_values=(1300.0, 1400.0),
    frame="A liquid whose density is {value} {unit} {relation}.",
    relevant=rv.RelevantWiring(
        "rho_l", "replace", "when the tank's liquid is replaced and the string still holds the cube fully submerged, the "
                            "buoyant force becomes q g a^3, so the tension is (q - rho_s) g a^3"),
    phrasings_r=(P("r0", "then replaces the original liquid in the tank, and the string still holds the cube completely "
                         "under its surface"),
                 P("r1", "is poured into the tank after the first liquid has been drained, so the same string now holds "
                         "the cube under this new liquid")),
    phrasings_d=(P("d0", "fills a beaker on the next bench"),
                 P("d1", "is stored in a sealed bottle on a shelf by the door")),
    nonnumeric_fill="unknown",
    cancelling=rv.CancellingSpec(
        "the depth of the cube's top face", "length", "cm", (20.0, 50.0, 80.0),
        "The top face of the cube {relation} {value} {unit}.",
        (P("c0", "is at a depth of"), P("c1", "lies below the free surface of the liquid by")),
        "(rho_l*g*(q + a) - rho_l*g*q)*a**2 - rho_s*a**3*g",
        ("pressure on the top face: p_top = p_surface + rho_l g q",
         "pressure on the bottom face: p_bottom = p_surface + rho_l g (q + a)",
         "buoyant force: Fb = (p_bottom - p_top) a^2"),
        "rho_l*g*(q + a)*a**2 - rho_s*a**3*g",  # only the push on the bottom face, the top face forgotten
        nonnumeric_fill="some depth"),
    conditional=rv.ConditionalSpec(
        "the string's breaking strength", "force", "N", (30.0, 50.0, 80.0), "The string {relation} {value} {unit}.",
        (P("k0", "can withstand a tension of up to"), P("k1", "is rated to break only above")),
        "T < q", "0", 2.0),
    notes="R uses replace (not a salt addition) because one instance has rho_l = 900 kg/m^3, an oil-like liquid in which "
          "salt does not dissolve. Every R value exceeds every rho_s, so the string stays taut. K: tensions are 2.5 N to "
          "21.5 N across instances; at a breaking strength of 2 N the string would break and the tension would be zero.",
)

S20 = rv.RoleSpec(
    structure_id="S20", quantity_phrase="a shift of a stand", quantity_type="length", unit="cm",
    values=(5.0, 15.0, 25.0), heldout_values=(8.0, 20.0),
    frame="The stand {relation} is then pushed {value} {unit} farther from the lens.",
    relevant=rv.RelevantWiring(
        "do", "add", "moving the object's stand q farther from the lens along the axis raises the object distance to do + q"),
    phrasings_r=(P("r0", "that holds the object"), P("r1", "on which the object is mounted")),
    phrasings_d=(P("d0", "of a microphone beside the bench"), P("d1", "of a desk fan at the far end of the bench")),
    nonnumeric_fill="a little",
    cancelling=rv.CancellingSpec(
        "the object's height", "length", "cm", (2.0, 4.0, 6.0), "The object {relation} {value} {unit}.",
        (P("c0", "is an upright arrow of height"), P("c1", "stands perpendicular to the axis with a height of")),
        "do*(q*f/(do - f))/q",
        ("ray parallel to the axis then through the focus: h_i / h_o = f / (do - f)",
         "ray through the centre of the lens: h_i / h_o = di / do"),
        "q*f/(do - f)",  # the image height reported instead of the image distance
        nonnumeric_fill="a known height"),
    notes="C: the object height enters the two ray-diagram similar-triangle relations and cancels from di; the copy foil "
          "(q itself, a length) is also emitted by the generator. No K: the lens diameter only matters through "
          "aberrations, which have no out-of-regime law separated by more than 1% inside the paraxial regime.",
)

S26 = rv.RoleSpec(
    structure_id="S26", quantity_phrase="a tilt", quantity_type="angle", unit="deg",
    values=(5.0, 10.0, 15.0), heldout_values=(8.0, 12.0),
    frame="A {value} {unit} tilt {relation}.",
    relevant=rv.RelevantWiring(
        "theta1", "add", "tilting the incoming ray q further from the normal within the plane of incidence raises the angle "
                         "of incidence to theta1 + q; the media and the interface are unchanged"),
    phrasings_r=(P("r0", "away from the normal is then given to the incoming ray"),
                 P("r1", "is then applied to the laser that produces this ray, turning the ray farther from the normal "
                         "within the same plane of incidence")),
    phrasings_d=(P("d0", "is then given to a picture frame hanging on the lab wall"),
                 P("d1", "is then given to the solar panel on the roof of the building")),
    nonnumeric_fill="small",
    notes="Light passes from the lower to the higher index in every instance, so any incidence below 90 degrees refracts; "
          "the largest R incidence is 55 degrees. The unit renders as 'deg'. No C or K (see the module docstring).",
)

ROLE_SPECS: dict[str, rv.RoleSpec] = {"S02": S02, "S13": S13, "S27": S27, "S92": S92, "S20": S20, "S26": S26}

STRUCTURE_FACTORIES = {
    "S02": library.s02_rough_incline_speed,
    "S13": library_b.s13_pendulum_period,
    "S27": library_c.s27_hydrostatic_pressure,
    "S92": lib_fluids.s92_cube_held_under_liquid,
    "S20": library_b.s20_thin_lens_image,
    "S26": library_c.s26_snell_refraction,
}


def structure(structure_id: str) -> gr.Structure:
    return STRUCTURE_FACTORIES[structure_id]()
