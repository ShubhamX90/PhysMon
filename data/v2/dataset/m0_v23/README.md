# M0 v2.3: M0 v2.2 revised for the GPT judge's flags

Data role: **EXPLORATION**. Status: **solver-certified; M0 v2.2 revised for the GPT judge's legitimate flags (J15.1-046; wording rules 1-8); not yet reviewed by the two-judge panel (Claude and GPT) or a human**.

411 cells on 11 structures (instance 0 of each), a gold solving trace for every cell. Built by `scripts/v2/s200_build_m0_v23.py` (the M0 v2.1 builder run with `src/physmon/benchmark/v2/roles_m0v23.py`). `m0_v21` and `m0_v22` are unchanged and are the record of the earlier reviews (`docs/validation/v2/llm_panel/admission_m0v21/`, `admission_m0v22/`, `admission_m0v22b/`).

## What changed against M0 v2.2, and why (journal J15.1-046)

S02 stays rejected. The structures are fixed before any model run (no model output exists on M0 v2.2). Old -> new wording (templates; `{v}` is the study value):

* **S01**: `A {v} kg block was hung from the left block in an earlier experiment.` -> `A {v} kg block was hung from the left block for an earlier experiment only.`
* **S07**: `A {v} kOhm resistor was connected in series with the capacitor in an earlier experiment.` -> `A {v} kOhm resistor was connected in series with the capacitor for an earlier experiment only.`; `Beside the circuit, a small lamp is connected to a second battery.` -> `Beside the circuit, a small lamp is connected to a second battery. The batteries and the wires are ideal, and the capacitor does not leak.`; `K_out reason: ... Assumes an ideal, non-leaking capacitor, which the in-regime answer does not need.` -> `K_out reason: ... Assumes an ideal, non-leaking capacitor, which the stated answer needs before the break as well.`
* **S13**: `A {v} m light cord was tied between the string and the bob in an earlier experiment.` -> `A {v} m light cord was tied between the string and the bob for an earlier experiment only.`
* **S15**: `In an earlier experiment, a {v} V cell ... was connected in series with the first battery, facing the same way.` -> `For an earlier experiment only, a {v} V cell ... was connected in series with the first battery, facing the same way.`
* **S26**: `The ray is then tilted {v} farther from the normal in the plane of incidence.` -> `The ray is then tilted {v} farther from the normal than the stated angle of incidence.`; `The laser that produces the ray was tilted {v} farther from the normal in the plane of incidence before the refraction was observed.` -> `The laser that produces the ray was tilted {v} farther from the normal than the stated angle of incidence before the refraction was observed.`; `The camera that films the interface is then tilted {v} farther from the vertical.` -> `The camera that films the interface is then tilted {v} farther from the vertical than before.`; `The laser ... was tilted {v} farther from the normal in the plane of incidence in an earlier experiment.` -> `The laser ... was tilted {v} farther from the normal than the stated angle of incidence in an earlier experiment.`
* **S27**: `A second tank, filled with the same liquid, stands beside it.` -> `A second tank, filled with the same liquid, stands beside it. At the start the liquid in both tanks is at rest and both tanks are open to the same air above; the depth is measured in the first tank.`; `The tank has a flat base with an area of {v} m2.` -> `The first tank has vertical sides and a flat base with an area of {v} m2.`; `The tank has a uniform horizontal cross-sectional area of {v} m2.` -> `The first tank has a uniform horizontal cross-sectional area of {v} m2.`
* **S30**: `A jug stands on the bench beside the heater.` -> `A jug stands on the bench beside the heater. No heat is lost to the surroundings, and the water does not boil.`
* **S55**: `The sample is in a flask, and a sample of a different gas is in another flask beside it.` -> `The sample is in a flask, and a sample of a different gas is in another flask beside it. The two flasks are thermally insulated from each other.`; `A heater warmed this gas sample by {v} K before its molecular speeds were measured.` -> `From the stated temperature, a heater warmed this gas sample by {v} K before the molecular speeds are measured.`; `A heater warmed this gas sample by {v} K in an earlier experiment.` -> `From the stated temperature, a heater warmed this gas sample by {v} K in an earlier experiment.`
* **S92**: `A liquid whose density is {v} kg/m3 now fills the second tank beside this one.` -> `A liquid whose density is {v} kg/m3 is poured into the second tank beside this one.`; `In an earlier experiment, the liquid in the tank was replaced by one whose density is {v} kg/m3, with the string still holding the cube under it.` -> `For an earlier experiment only, the liquid in the tank was replaced by one whose density is {v} kg/m3, with the string still holding the cube under it.`

S72 and S20: no sentence changed (S72's numeral-free N sentences are explained as controls in the panel packets).

D cells by kind: {'other_object_same_scene': 36, 'same_object_other_event': 30}. By stratum: {'C': 42, 'D': 66, 'K': 24, 'K_out': 4, 'N': 22, 'R': 66, 'none': 11, 'support': 176}.

## What has not been done

No review of M0 v2.3 yet (two-judge admission, Claude and GPT, is required); no model has seen the cells.
