# M0 v2.4: M0 v2.3 with the last fixes before the G2 pilot

Data role: **EXPLORATION**. Status: **solver-certified; M0 v2.3 with the last fixes before the G2 pilot (S72 pair 1 a same-electron event; S26, S55, S92 naturalness rewrites; J15.1-048); S26, S55, S72, S92 not yet re-reviewed by the two-judge panel**.

411 cells on 11 structures (instance 0 of each), a gold solving trace for every cell. Built by `scripts/v2/s202_build_m0_v24.py` (the M0 v2.1 builder run with `src/physmon/benchmark/v2/roles_m0v24.py`). `m0_v21`, `m0_v22` and `m0_v23` are unchanged and are the record of the earlier reviews (`docs/validation/v2/llm_panel/admission_m0v21/` ... `admission_m0v23/`).

## What changed against M0 v2.3, and why (journal J15.1-048)

Both qualified judges reviewed M0 v2.3: with the 5.3b guard 10 structures ADMIT and S72 REJECTS (its pair 1 claimed no same-electron event exists, which is false); naturalness rewrites were required for S26 R1, S55 N1 and S92 N1. No model has seen any M0 cell. Old -> new wording (templates; `{v}` is the study value; N is the numeral-free control):

* **S26**: `The ray is then tilted {v} farther from the normal than the stated angle of incidence.` -> `The ray is then tilted until its angle of incidence at the interface has grown by {v}.`; `The camera that films the interface is then tilted {v} farther from the vertical than before.` -> `The camera on the tripod is then tilted until its angle from the vertical has grown by {v}.`; `The laser that produces the ray was tilted {v} farther from the normal than the stated angle of incidence before the refraction was observed.` -> `Before the refraction was observed, the laser that produces the ray was tilted until the angle of incidence had grown by {v}.`; `The laser ... was tilted {v} farther from the normal than the stated angle of incidence in an earlier experiment.` -> `In an earlier experiment, the laser that produces the ray was tilted until the angle of incidence had grown by {v}.`
* **S55**: `From the stated temperature, a heater warmed this gas sample by {v} K before the molecular speeds are measured.` -> `Once the sample was in equilibrium, a heater warmed it by {v} K just before the molecular speeds were measured.`; `From the stated temperature, a heater warmed this gas sample by {v} K in an earlier experiment.` -> `Once the sample was in equilibrium, a heater warmed it by {v} K in an earlier experiment.`
* **S72**: `The electron in this apparatus gains a further {v} eV of kinetic energy in one more accelerating gap. (D: The alpha particle in the other apparatus gains ...)` -> `R1: The electron in this apparatus gains a further {v} eV of kinetic energy in one more accelerating gap before the wavelength is determined. D1: the same sentence ending after the wavelength has been determined.`
* **S92**: `N0: A liquid whose density is different from the original's is poured into the second tank beside this one.` -> `N0: A liquid whose density is somewhat greater than the original's is poured into the second tank beside this one.`; `N1: For an earlier experiment only, the liquid in the tank was replaced by one whose density is different from the original's, with the string still holding the cube under it.` -> `N1: For an earlier experiment only, the liquid in the tank was replaced by one whose density is somewhat greater than the original's, with the string still holding the cube under it.`

S01, S07, S13, S15, S20, S27 and S30 are the M0 v2.3 specs unchanged.

D cells by kind: {'other_object_same_scene': 33, 'same_object_other_event': 33}. By stratum: {'C': 42, 'D': 66, 'K': 24, 'K_out': 4, 'N': 22, 'R': 66, 'none': 11, 'support': 176}.

## What has not been done

S26, S55, S72 and S92 have not been re-reviewed by the two-judge panel; no model has seen the cells.
