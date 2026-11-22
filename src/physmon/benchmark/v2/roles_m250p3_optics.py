"""M250 phase 3, batch optics: v2.1 role-by-value specifications for the new structures S301 to S310 (plan revision v2.2, section G;
admission standard 3.2, 6.1, 6.2, 6.3; the wording rules 1-8 of the earlier waves and the lessons A-L of the phase-3 brief).

Every spec follows `roles_m0v21` (the v2.1 design) on instance 0 of the new structure:

* one R/D quantity with three study values and two held-out values, chosen first (lesson H) so that the base text could be written around
  a natural added quantity: a sheet laid on a plate, water poured into a tank or a pool, a mirror slid along a bench, the angle of a
  prism turned, a laser tuned, a coat brushed on, a coating deposited, an iris opened, the power of a beam raised;
* a co-present D (pair 0, `other_object_same_scene`) whose object is introduced by a number-free scene clause in the base context of every
  cell, is of a different type from the target object and receives an ordinary, purposeful action (a glass block, a bucket, a fountain
  basin, a screen, a plane mirror, a monochromator, a microscope slide, a telescope mirror, a camera lens, a laser pointer); and a
  same-object D (pair 1, `same_object_other_event`: "For an earlier run only, ... had been ..." in every case, so that nothing reads as
  still changed) whose R twin names the moment of the question in the perfect tense ("Before ..., ... has been ..."), with the same numeral
  and unit within a pair (pair 1 differs in tense only, declared as a frame mismatch), an attachment-only difference, word counts within three, marker- and consequence-free wording and
  value hygiene;
* a C quantity where the physics supports a real cancellation (S301, S302, S304, S305, S307, S308, S309);
* a K quantity where a genuine regime condition of the physics itself exists (S303, S308); the kind of regime is recorded in
  `K_KINDS`. K_out is recorded as infeasible with the reason in every case.

`NO_C` and `NO_K` hold the reason a structure has no C or K quantity, so that an absence is a judgement on record and not an omission.
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_m250p3_optics as lo
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2

P = rv.Phrasing
Pair = r2.PhrasePair
CO = r2.D_KIND_CO_PRESENT
EVENT = r2.D_KIND_OTHER_EVENT
V21 = r2.VERSION_V21
CERT_VERSION = "v2.1"


def _spec(sid: str, **fields) -> r2.RoleSpecV2:
    return r2.RoleSpecV2(structure_id=sid, version=V21, author="agent (M250 phase 3, optics)", **fields)


def _ko(reason: str) -> r2.KOut:
    return r2.KOut(False, reason)


# --- S301 --------------------------------------------------------------------------------------------------------------------------

S301_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the distance of a screen beyond the plate", "length", "cm", (24.0, 55.0, 95.0),
        "A screen parallel to the plate {relation} {value} {unit} beyond the plate.", (P("c0", "stands"), P("c1", "is set")),
        "((t + q)*tan(theta) - (t*tan(thr) + q*tan(theta)))*cos(theta)",
        ("the emerging ray meets the screen at t tan(theta_r) + q tan(theta) along the screen",
         "the line of the incident ray meets the screen at (t + q) tan(theta)",
         "the perpendicular distance is the difference of the two positions times cos(theta)"),
        "((t + q)*tan(theta) - t*tan(thr))*cos(theta)", nonnumeric_fill="a known distance"),
    "uncommon", "That the sideways shift of a ray crossing a plate does not depend on how far away the screen that records it stands "
                "follows from the emergent ray being parallel to the incident ray, but it is not a stated textbook fact.", (38.0, 72.0))

S301 = _spec(
    "S301", quantity_phrase="an extra sheet of glass", quantity_type="length", unit="mm", values=(2.6, 5.3, 7.4),
    heldout_values=(3.7, 6.2),
    relevant=rv.RelevantWiring("t", "add", "A sheet of the same glass laid flat on the plate adds its thickness q to the thickness of glass "
                                           "that the ray crosses, because each parallel-sided layer shifts the ray in proportion to its "
                                           "thickness, so the shift is that of a plate of thickness t + q."),
    cancelling=S301_C,
    scene_clause="A wooden tray lies on the bench beside the plate, and no light from the beam reaches it.",
    scene_object_rationale="A wooden tray lying on the bench beside the plate receives none of the beam, so the ray, the plate it "
                           "crosses and its thickness are those of the base problem.",
    scene_refs=("wooden tray",), target_terms=("the plate",),
    pairs=(
        Pair("p0", "A {value} {unit} sheet of the same glass is laid flat on {relation}.", "the plate", "the wooden tray", CO,
             "A sheet laid flat on the wooden tray lies on the tray only; the plate that the ray crosses has the stated thickness "
             "and index.", ("parallel-sided plate of glass", "does not absorb light"), "thin",
             before_context_reason="The R sentence refers to 'the plate' and to its glass before the context introduces them."),
        Pair("p1", "{relation}, a {value} {unit} sheet of the same glass has been laid flat on the plate.",
             "Before the beam is sent through the plate", "For an earlier run only", EVENT,
             "The sheet lay on the plate in an earlier run only, which is over; in the stated run the ray crosses the plate alone, of "
             "the stated thickness.", ("parallel-sided plate of glass", "does not absorb light"), "thin"),
    ),
    notes="M250 phase 3: R is a sheet of the same glass laid flat on the plate (the shifts of parallel-sided layers add, whether or not "
          "an air gap lies between them); C is the distance of a screen beyond the plate (the emergent ray is parallel to the incident "
          "ray); no K (see NO_K).")

# --- S302 --------------------------------------------------------------------------------------------------------------------------

S302_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the height of the eye above the oil", "length", "cm", (40.0, 75.0, 120.0),
        "The eye of the observer {relation} {value} {unit} above the upper surface of the oil.", (P("c0", "is"), P("c1", "is held")),
        "(q + dw + do_) - q",
        ("the apparent distance of the coin from the eye is q + dw + do_",
         "the apparent depth below the upper surface is that distance minus the height q of the eye"),
        "(q + dw + do_)", nonnumeric_fill="a known height"),
    "uncommon", "That the apparent depth below the surface does not depend on how high the eye is held is true for near-vertical "
                "viewing but is not a stated textbook fact.", (55.0, 95.0))

S302 = _spec(
    "S302", quantity_phrase="an extra depth of water", quantity_type="length", unit="cm", values=(5.0, 23.0, 27.0),
    heldout_values=(15.0, 25.5),
    relevant=rv.RelevantWiring("h", "add", "Water poured into the tank deepens the water layer by q and lifts the oil on top of it, "
                                           "making the water depth h + q, so the apparent thickness of the water layer is (h + q) / n."),
    cancelling=S302_C,
    scene_clause="A bucket of water stands on the floor beside the tank.",
    scene_object_rationale="A bucket of water on the floor is a vessel of its own; what is poured into the bucket does not reach the "
                           "tank, so the layers over the coin keep their depths.",
    scene_refs=("bucket",), target_terms=("the tank",),
    pairs=(
        Pair("p0", "A further {value} {unit} of water is poured into {relation}.", "the tank", "the bucket", CO,
             "Water poured into the bucket deepens the water in the bucket only; the layers of water and oil above the coin keep "
             "their stated depths.", ("do not mix", "flat and horizontal"), "amount",
             before_context_reason="The R sentence refers to 'the tank' and to its water before the context introduces them."),
        Pair("p1", "{relation}, a further {value} {unit} of water has been poured into the tank.", "Before the coin is viewed",
             "For an earlier run only", EVENT,
             "The extra water was in the tank in an earlier run only, which is over; in the stated run the tank holds the stated "
             "layers of water and oil.", ("do not mix", "flat and horizontal"), "amount"),
    ),
    notes="M250 phase 3: R is extra water poured into the tank (the oil floats on top and keeps its thickness); C is the height of the "
          "eye above the oil (the apparent depth below the surface does not depend on it); no K (see NO_K).")

# --- S303 --------------------------------------------------------------------------------------------------------------------------

S303_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the half-angle of the cone of light of the lamp", "angle", "deg", (62.0, 71.0, 79.0),
        "The light of the lamp {relation} {value} {unit} on either side of the vertical.",
        (P("k0", "spreads out to"), P("k1", "fans out to")),
        "q > thc", "pi*(h*tan(q))**2", 35.0, nonnumeric_fill="a wide angle"),
    _ko("The problem states that the cone is wide enough for the edge of the disc to be set by total internal reflection; a cone narrower "
        "than the critical angle would contradict that statement, and the disc would then be set by the cone, which the question does "
        "not describe."),
    (66.0, 75.0))

S303 = _spec(
    "S303", quantity_phrase="an extra depth of water", quantity_type="length", unit="m", values=(0.8, 1.5, 2.2),
    heldout_values=(1.1, 2.1),
    relevant=rv.RelevantWiring("h", "add", "Water added to the pool raises the surface above the lamp by q, which rests on the bottom, "
                                           "making the depth h + q; the disc radius is (h + q) tan(theta_c)."),
    conditional=S303_K,
    scene_clause="A diving tank stands on the terrace beside the pool, and no pipe joins them.",
    scene_object_rationale="A diving tank on the terrace is a vessel of its own with its own water; what is added to the basin does not "
                           "reach the pool, so the lamp stays at its depth under the surface of the pool.",
    scene_refs=("diving tank",), target_terms=("the pool",),
    pairs=(
        Pair("p0", "A further {value} {unit} of water is added to {relation}.", "the pool", "the diving tank", CO,
             "Water added to the diving tank deepens the tank only; the depth of the lamp under the surface of the pool is the "
             "stated one.", ("flat, still surface", "total internal reflection"), "amount",
             before_context_reason="The R sentence refers to 'the pool' before the context introduces it."),
        Pair("p1", "{relation}, a further {value} {unit} of water has been added to the pool.", "Before the disc is measured",
             "For an earlier run only", EVENT,
             "The extra water was in the pool in an earlier run only, which is over; in the stated run the lamp lies at the stated "
             "depth under the surface.", ("flat, still surface", "total internal reflection"), "amount"),
    ),
    notes="M250 phase 3: R is extra water added to the pool (the lamp rests on the bottom); K is the half-angle of the cone of light "
          "(wider than the critical angle: total internal reflection sets the edge); no C (see NO_C).")

# --- S304 --------------------------------------------------------------------------------------------------------------------------

S304_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the height of the object", "length", "mm", (3.0, 7.5, 10.5), "The height of the object {relation} {value} {unit}.",
        (P("c0", "is"), P("c1", "is measured as")),
        "((q*v1/u)*(v2/s2))/q",
        ("the height of the first image is q v1 / u", "the height of the final image is q (v1 / u) (v2 / s2)",
         "the magnification is the final image height over the object height q"),
        "(v1/u)*(v2/s2)*q/(q + u)", nonnumeric_fill="known"),
    "standard", "That a magnification does not depend on the size of the object follows from writing it as image height over object "
                "height; it is taught but not a headline fact.", (5.5, 9.5))

S304 = _spec(
    "S304", quantity_phrase="an extra distance", quantity_type="length", unit="cm", values=(5.5, 10.0, 20.0),
    heldout_values=(6.0, 16.0),
    relevant=rv.RelevantWiring("g", "add", "Sliding the mirror farther along the bench by q puts it at g + q behind the lens, so the "
                                           "second object distance is 2 (g + q) - v1."),
    cancelling=S304_C,
    scene_clause="A white screen stands on the bench beside the lens and the mirror, off the axis.",
    scene_object_rationale="A white screen standing on the bench off the axis neither reflects nor refracts the light of the object, so the "
                           "lens, the mirror and their distances are those of the base problem.",
    scene_refs=("white screen",), target_terms=("the mirror", "the lens"),
    pairs=(
        Pair("p0", "{relation} is slid {value} {unit} farther along the bench.", "The mirror", "The white screen", CO,
             "Sliding the white screen along the bench moves the screen only; the distance of the mirror behind the lens is the "
             "stated one.", ("thin converging lens", "perpendicular to the axis"), "a short distance",
             before_context_reason="The R sentence refers to 'the mirror' and to its place on the bench before the context introduces them."),
        Pair("p1", "{relation}, the mirror has been slid {value} {unit} farther along the bench.", "Before the final image is located",
             "For an earlier run only", EVENT,
             "The mirror was slid in an earlier run, which is over; in the stated run the mirror stands at the stated distance "
             "behind the lens.", ("thin converging lens", "perpendicular to the axis"), "a short distance"),
    ),
    notes="M250 phase 3: R is a further distance of the mirror from the lens; C is the object height (magnification as a ratio of "
          "heights); no K (see NO_K).")

# --- S305 --------------------------------------------------------------------------------------------------------------------------

S305_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the distance of a screen beyond the prism", "length", "cm", (30.0, 65.0, 110.0),
        "A screen {relation} {value} {unit} beyond the prism, square to the incident ray.", (P("c0", "stands"), P("c1", "is set")),
        "atan(q*tan(delta)/q)",
        ("the spot of the emergent ray on the screen is displaced from the line of the incident ray by q tan(delta)",
         "the deviation is the arctangent of the displacement over the distance q to the screen"),
        "atan(q*tan(delta)/(q + 0.5))", nonnumeric_fill="a known distance"),
    "standard", "That an angle found as an arctangent of a displacement over a distance does not depend on the distance at which the "
                "displacement is read is taught but not a headline fact.", (45.0, 85.0))

S305 = _spec(
    "S305", quantity_phrase="an extra angle", quantity_type="angle", unit="deg", values=(3.5, 6.0, 13.5), heldout_values=(4.5, 12.5),
    relevant=rv.RelevantWiring("theta", "add", "Turning the prism so that the angle of incidence is raised by q makes it theta + q, and "
                                               "the deviation follows from the two refractions at the new angle."),
    cancelling=S305_C,
    scene_clause="A plane mirror stands on the bench beside the prism and reflects the ray of a laser pointer onto the wall.",
    scene_object_rationale="A plane mirror beside the prism reflects another ray onto the wall and takes none of the ray that crosses "
                           "the prism, so the ray, the prism and its angle of incidence are those of the base problem.",
    scene_refs=("plane mirror",), target_terms=("the prism",),
    pairs=(
        Pair("p0", "The angle of incidence of the ray on {relation} is raised by a further {value} {unit}.", "the prism",
             "the plane mirror", CO,
             "Turning the plane mirror changes the angle of its own ray only; the ray that crosses the prism meets it at the stated "
             "angle of incidence.", ("apex angle", "does not disperse or absorb light"), "small amount",
             before_context_reason="The R sentence refers to 'the prism' and to the angle of incidence on it before the context "
                                   "introduces them."),
        Pair("p1", "{relation}, the angle of incidence of the ray on the prism has been raised by a further {value} {unit}.",
             "Before the ray enters the prism", "For an earlier run only", EVENT,
             "The angle was raised in an earlier run, which is over; in the stated run the ray meets the prism at the stated angle "
             "of incidence.", ("apex angle", "does not disperse or absorb light"), "small amount"),
    ),
    notes="M250 phase 3: R is a further turn of the prism (a raised angle of incidence, with the emergent ray still leaving the "
          "second face); C is the distance of a screen beyond the prism; no K (see NO_K).")

# --- S306 --------------------------------------------------------------------------------------------------------------------------

S306 = _spec(
    "S306", quantity_phrase="a longer wavelength", quantity_type="length", unit="nm", values=(47.0, 95.0, 140.0),
    heldout_values=(68.0, 120.0),
    relevant=rv.RelevantWiring("lam", "add", "Tuning the laser to a wavelength longer by q makes the wavelength lam + q, and the maximum "
                                             "of the order moves out according to sin(theta) = m (lam + q) / d."),
    scene_clause="A monochromator stands on the bench beside the grating and sends its light to a detector.",
    scene_object_rationale="A monochromator beside the grating sends its light to a detector, not to the grating or the screen, so the "
                           "light that falls on the grating is that of the laser alone.",
    scene_refs=("monochromator",), target_terms=("the laser",),
    pairs=(
        Pair("p0", "{relation} is tuned to a wavelength longer by a further {value} {unit}.", "The laser", "The monochromator", CO,
             "Tuning the monochromator changes the light that goes to its detector only; the wavelength of the laser that falls on "
             "the grating is the stated one.", ("transmission diffraction grating", "far-field pattern"), "small amount",
             before_context_reason="The R sentence refers to 'the laser' and to its wavelength before the context introduces them."),
        Pair("p1", "{relation}, the laser has been tuned to a wavelength longer by a further {value} {unit}.",
             "Before the beam reaches the grating", "For an earlier run only", EVENT,
             "The laser was tuned in an earlier run, which is over; in the stated run the laser has the stated wavelength when its "
             "beam reaches the grating.", ("transmission diffraction grating", "far-field pattern"), "small amount"),
    ),
    notes="M250 phase 3: R is a longer wavelength of the laser; no C and no K (see NO_C and NO_K).")

# --- S307 --------------------------------------------------------------------------------------------------------------------------

S307_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the wavelength of the light", "length", "nm", (470.0, 590.0, 700.0),
        "The light {relation} a wavelength of {value} {unit}.", (P("c0", "has"), P("c1", "is chosen to have")),
        "D*tan(asin(((n - 1)*t/q)*q/d))",
        ("the number of fringes by which the film shifts the pattern is (n - 1) t / q",
         "the fringes are spaced by q in sine of the angle per d, so the shift in sine is (number of fringes) q / d",
         "the position is D tan of that angle"),
        "((n - 1)*t/q)*D", nonnumeric_fill="a known value"),
    "uncommon", "That the shift of the central fringe caused by a film does not depend on the wavelength follows from the equal-path "
                "condition (the fringe count scales as 1 / lambda and the fringe spacing as lambda), but it is rarely stated.",
    (520.0, 640.0))

S307 = _spec(
    "S307", quantity_phrase="an extra coat", quantity_type="length", unit="μm", values=(21.0, 37.0, 45.0), heldout_values=(26.0, 42.0),
    relevant=rv.RelevantWiring("t", "add", "A coat of the same lacquer brushed onto the film adds its thickness q, so the film is "
                                           "t + q thick and the extra optical path is (n - 1)(t + q)."),
    cancelling=S307_C,
    scene_clause="A glass microscope slide, coated with the same lacquer, lies on the bench beside the slits.",
    scene_object_rationale="A coated microscope slide lying on the bench beside the slits covers no slit and is crossed by no light, so "
                           "the film over the slit and its thickness are those of the base problem.",
    scene_refs=("microscope slide",), target_terms=("the film",),
    pairs=(
        Pair("p0", "A {value} {unit} coat of the same lacquer is brushed onto {relation}.", "the film over the slit",
             "the microscope slide", CO,
             "A coat brushed onto the microscope slide thickens the coating of the slide only; the film over the slit has the stated "
             "thickness and index.", ("uniform film of lacquer", "does not disperse or absorb light"), "thin",
             before_context_reason="The R sentence refers to 'the film over the slit' before the context introduces any film."),
        Pair("p1", "{relation}, a {value} {unit} coat of the same lacquer has been brushed onto the film over the slit.",
             "Before the central fringe is located", "For an earlier run only", EVENT,
             "The extra coat was on the film in an earlier run only, which is over; in the stated run the film over the slit has "
             "the stated thickness.", ("uniform film of lacquer", "does not disperse or absorb light"), "thin"),
    ),
    notes="M250 phase 3: R is a further coat of the same lacquer on the film over the slit; C is the wavelength of the light (the "
          "equal-path fringe does not depend on it); no K (see NO_K).")

# --- S308 --------------------------------------------------------------------------------------------------------------------------

S308_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the cross-section area of the beam", "area", "mm^2", (3.1, 6.8, 10.7), "The beam {relation} {value} {unit}.",
        (P("c0", "has a cross-sectional area of"), P("c1", "covers an area of")),
        "(P0/q*Rf)*q",
        ("intensity of the incident beam I0 = P0 / q", "reflected intensity I_r = I0 R per unit area of the beam",
         "reflected power = I_r q"),
        "(P0/q*Rf)", nonnumeric_fill="a known area"),
    "standard", "That a reflected power fraction does not depend on the cross-section area of the beam follows from writing power as "
                "intensity times area; it is taught but not a headline fact.", (6.7, 9.7))

S308_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the coherence length of the light", "length", "μm", (70.0, 300.0, 450.0),
        "The coherence length of the light {relation} {value} {unit}.", (P("k0", "is"), P("k1", "has been measured as")),
        "q > 20*n1*t", "P0*(r1**2 + (1 - r1**2)**2*r2**2/(1 - r1**2*r2**2))", 0.05, nonnumeric_fill="a known length"),
    _ko("The problem states that the light is coherent over the thickness of the coating; a coherence length shorter than the round-trip "
        "optical path in the coating would make the reflected waves add in power and not in amplitude, which the stated model excludes."),
    (200.0, 350.0))

S308 = _spec(
    "S308", quantity_phrase="a further layer of coating", quantity_type="length", unit="nm", values=(34.0, 38.0, 68.0),
    heldout_values=(37.0, 53.0),
    relevant=rv.RelevantWiring("t", "add", "A further layer of the same coating material deposited on the coating adds q to its "
                                           "thickness, making it t + q, which changes the phase thickness of the coating."),
    cancelling=S308_C, conditional=S308_K,
    scene_clause="A telescope mirror, coated with the same material, hangs on a rack beside the lens.",
    scene_object_rationale="A telescope mirror hanging on a rack beside the lens receives no light of the beam and shares no surface with "
                           "the lens, so the coating of the lens and its thickness are those of the base problem.",
    scene_refs=("telescope mirror",), target_terms=("the lens",),
    pairs=(
        Pair("p0", "A further {value} {unit} of the same coating material is deposited on {relation}.", "the lens",
             "the telescope mirror", CO,
             "Coating material deposited on the telescope mirror thickens the coating of the mirror only; the coating of the lens "
             "has the stated thickness.", ("single uniform coating", "do not absorb light"), "amount",
             before_context_reason="The R sentence refers to 'the lens' and to its coating before the context introduces them."),
        Pair("p1", "{relation}, a further {value} {unit} of the same coating material has been deposited on the lens.",
             "Before the beam strikes the lens", "For an earlier run only", EVENT,
             "The extra coating material was on the lens in an earlier run only, which is over; in the stated run the coating of the "
             "lens has the stated thickness.", ("single uniform coating", "do not absorb light"), "amount"),
    ),
    notes="M250 phase 3: R is a further layer of the same coating material deposited on the lens; C is the cross-section area of the "
          "beam (power as intensity times area); K is the coherence length of the light (coherent regime of the thin-film "
          "interference).")

# --- S309 --------------------------------------------------------------------------------------------------------------------------

S309_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the focal length of the telescope", "length", "cm", (95.0, 160.0, 240.0),
        "The telescope {relation} a focal length of {value} {unit}.", (P("c0", "has"), P("c1", "is built with")),
        "L*((q*thr)/q)",
        ("the radius of the first dark ring in the focal plane is q theta", "the angle seen at the telescope is that radius over q",
         "the separation on the Moon is L times that angle"),
        "L*((q*thr)/(q + 1))", nonnumeric_fill="a known value"),
    "standard", "That the angular resolution of a telescope does not depend on its focal length follows from the focal-plane radius "
                "being the focal length times the angle; it is taught but not a headline fact.", (120.0, 200.0))

S309 = _spec(
    "S309", quantity_phrase="a wider opening", quantity_type="length", unit="cm", values=(2.6, 4.7, 7.4), heldout_values=(3.4, 5.6),
    relevant=rv.RelevantWiring("D", "add", "Opening the circular stop of the telescope by a further q widens the opening to D + q, and "
                                           "the angular radius of the first dark ring is x1 lambda / (pi (D + q))."),
    cancelling=S309_C,
    scene_clause="A camera lens with its own iris lies on the observing table beside the telescope.",
    scene_object_rationale="A camera lens lying on the observing table beside the telescope takes none of the light of the Moon and "
                           "does not touch the iris of the telescope, so the opening and the diffraction pattern are those of the "
                           "base problem.",
    scene_refs=("camera lens",), target_terms=("the telescope", "the stop"),
    pairs=(
        Pair("p0", "{relation} is opened by a further {value} {unit}.", "The circular stop of the telescope", "The iris of the camera lens", CO,
             "Opening the iris of the camera lens changes the opening of the camera lens only; the circular stop that the light of "
             "the Moon passes in the telescope has the stated diameter.", ("circular stop", "diffraction of the light"),
             "small amount", before_context_reason="The R sentence refers to 'the telescope' and to its iris before the context "
                                                   "introduces them."),
        Pair("p1", "{relation}, the circular stop of the telescope has been opened by a further {value} {unit}.",
             "Before the features are observed", "For an earlier run only", EVENT,
             "The stop was opened in an earlier run, which is over; in the stated observation the circular stop has the stated "
             "diameter.", ("circular stop", "diffraction of the light"), "small amount"),
    ),
    notes="M250 phase 3: R is a wider opening of the iris of the telescope; C is the focal length of the telescope (focal-plane radius "
          "over focal length); no K (see NO_K).")

# --- S310 --------------------------------------------------------------------------------------------------------------------------

S310 = _spec(
    "S310", quantity_phrase="an extra power", quantity_type="power", unit="mW", values=(3.1, 6.2, 10.0), heldout_values=(4.5, 9.4),
    relevant=rv.RelevantWiring("P0", "add", "Raising the power of the beam by a further q makes the incident power P0 + q, and the "
                                            "reflected power is the same fraction of it."),
    scene_clause="A small LED lamp with a dimmer knob stands on the bench beside the glass block, switched on.",
    scene_object_rationale="An LED lamp standing on the bench sends no light onto the glass block, so the power that strikes the block "
                           "and is reflected from it is that of the beam alone.",
    scene_refs=("LED lamp",), target_terms=("the beam",),
    pairs=(
        Pair("p0", "The power of {relation} is turned up by a further {value} {unit}.", "the beam", "the LED lamp", CO,
             "Turning up the power of the LED lamp changes the lamp only; the power of the beam that strikes the glass block is "
             "the stated one.", ("plane-polarised", "does not absorb light"), "small amount",
             before_context_reason="The R sentence refers to 'the beam' and to its power before the context introduces them."),
        Pair("p1", "{relation}, the power of the beam has been turned up by a further {value} {unit}.", "Before the beam strikes the block",
             "For an earlier run only", EVENT,
             "The power was raised in an earlier run, which is over; in the stated run the beam that strikes the block has the "
             "stated power.", ("plane-polarised", "does not absorb light"), "small amount"),
    ),
    notes="M250 phase 3: R is a further power of the beam; no C and no K (see NO_C and NO_K).")


_TENSE = ("The frame differs between R and D only in tense: the R sentence says that the change has been made before the asked moment "
          "and the D sentence that it had been made for an earlier run, so the two tenses cannot share one frame.")


def _perfect(spec: r2.RoleSpecV2) -> r2.RoleSpecV2:
    """Give pair 1 the past-perfect D frame ("had been ...") beside the perfect R frame ("has been ...")."""

    p1 = spec.pairs[1]
    assert "has been" in p1.frame
    p1 = dataclasses.replace(p1, d_frame=p1.frame.replace("has been", "had been"), frame_mismatch_reason=_TENSE)
    return dataclasses.replace(spec, pairs=(spec.pairs[0], p1))


SPECS: dict[str, r2.RoleSpecV2] = {
    s.structure_id: _perfect(s) for s in (S301, S302, S303, S304, S305, S306, S307, S308, S309, S310)}
ROLE_SPECS = SPECS

STRUCTURE_FACTORIES = {f().structure_id: f for f in lo.ALL}

INFEASIBLE: dict[str, str] = {}

NO_C: dict[str, str] = {
    "S303": "The area of the disc depends on the depth and the refractive index only; no further quantity of the system enters an "
            "intermediate relation and then leaves it.",
    "S306": "The position of the maximum follows from the ruling spacing, the wavelength, the order and the distance to the screen; "
            "every further quantity of the system (the width of the beam, the number of rulings) either does not enter a relation "
            "or changes the answer.",
    "S310": "The reflected power follows from the index, the polarisation angle and the incident power; a further quantity (the "
            "cross-section of the beam) would enter only as intensity times area and the question asks for power throughout, so no "
            "honest relation of the structure carries it.",
}

NO_K: dict[str, str] = {
    "S301": "The ray passes from air into glass and out again; total internal reflection cannot occur in this direction at any angle "
            "of incidence, and Snell's law holds at every angle, so no further quantity switches the law of the answer.",
    "S302": "The base text states that the observer looks straight down at tiny angles; the apparent-depth rule holds for every depth "
            "and thickness in that regime, and a viewing angle that left the regime would only restate the stated viewing condition.",
    "S304": "The thin-lens equation holds on each pass for real and for virtual images alike, and the mirror is plane; no further "
            "quantity switches the law that gives the magnification.",
    "S305": "The ray leaves the second face for every combination of the stated apex angle, index and angle of incidence; the "
            "condition for emergence is a relation among stated inputs, and no further quantity of the system decides it.",
    "S306": "The grating equation holds for every order that exists; whether the order exists is fixed by the stated spacing, "
            "wavelength and order, not by a further quantity.",
    "S307": "The equal-path condition holds for the stated film and slits at every thickness in the stated range; no further "
            "quantity switches the law that gives the position of the central fringe.",
    "S309": "The only regime that could decide the answer is diffraction-limited against seeing-limited imaging, but outside the "
            "diffraction-limited regime the resolution has no definite value that a closed law gives (only an order-of-magnitude "
            "estimate), so no K quantity is claimed.",
    "S310": "At the angle of incidence stated in the problem the Fresnel formulas hold for air-to-glass incidence at every index; "
            "total internal reflection cannot occur in this direction, and no further quantity switches the law of the answer.",
}

# The kind of regime that each K quantity expresses (a condition of the physics itself, not an equipment rating).
K_KINDS: dict[str, str] = {
    "S303": "total internal reflection (the cone of light is wider than the critical angle, so the edge of the disc is set by "
            "total internal reflection and not by the cone)",
    "S308": "coherence regime (coherence length much greater than the optical thickness of the coating, so the reflected waves "
            "interfere in amplitude)",
}


def structure(structure_id: str) -> gr.Structure:
    """The new structure with the spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), SPECS[structure_id].scene_clause)


# What the H4 trace extractor (`TraceContext.target_phrases` / `target_symbols`) must read as a statement of the target.
TARGET_TERMS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "S301": (("perpendicular distance between the emerging ray", "perpendicular distance"), ("shift", "d", "Δ")),
    "S302": (("how far below the upper surface of the oil", "appear to be", "apparent depth"), ("D", "d_app")),
    "S303": (("area of this bright disc", "area"), ("A", "S")),
    "S304": (("overall lateral magnification", "magnification"), ("m", "M")),
    "S305": (("through what angle is the ray turned", "angle", "turned"), ("delta", "δ")),
    "S306": (("how far from the centre of the pattern", "distance"), ("y", "x")),
    "S307": (("how far does the central bright fringe lie", "central bright fringe"), ("y", "x")),
    "S308": (("power is carried by the beam reflected", "power"), ("Pr", "P_r", "P")),
    "S309": (("smallest separation of the two features", "smallest separation"), ("sep", "s")),
    "S310": (("power is carried by the reflected beam", "power"), ("Pr", "P_r", "P")),
}
