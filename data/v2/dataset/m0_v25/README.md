# M0 v2.5: M0 v2.4 with two N sentences rewritten after the naturalness review

Data role: **EXPLORATION**. Status: **solver-certified; M0 v2.4 with two N sentences rewritten after the naturalness review (S26 D0/N0, S55 pair 1; J15.1-051); S26 and S55 not yet re-reviewed by the two-judge panel**.

411 cells on 11 structures (instance 0 of each), a gold solving trace for every cell. Built by `scripts/v2/s204_build_m0_v25.py` (the M0 v2.1 builder run with `src/physmon/benchmark/v2/roles_m0v25.py`). `m0_v21` to `m0_v24` are unchanged and are the record of the earlier reviews (`docs/validation/v2/llm_panel/admission_m0v21/` ... `admission_m0v24/`).

## What changed against M0 v2.4, and why (journal J15.1-051)

Both qualified judges admitted the four changed structures of M0 v2.4; the naturalness rater rated S26 N0 and S55 N1 artificial. No model has seen any M0 cell. Old -> new wording (templates; `{v}` is the study value; N is the numeral-free control):

* **S26**: `D0: The camera on the tripod is then tilted until its angle from the vertical has grown by {v}.` -> `D0: The camera on the tripod is then tilted {v} farther from the vertical to keep the ray in view.`; `N0: The camera on the tripod is then tilted until its angle from the vertical has grown by a little.` -> `N0: The camera on the tripod is then tilted a little farther from the vertical to keep the ray in view.`
* **S55**: `R1: Once the sample was in equilibrium, a heater warmed it by {v} just before the molecular speeds were measured.` -> `R1: Just before the molecular speeds were measured, a heater warmed this gas sample by {v}.`; `D1: Once the sample was in equilibrium, a heater warmed it by {v} in an earlier experiment.` -> `D1: In an earlier experiment, a heater warmed this gas sample by {v}.`; `N1: Once the sample was in equilibrium, a heater warmed it by a few kelvin in an earlier experiment.` -> `N1: In an earlier experiment, a heater warmed this gas sample by a few kelvin.`

The other nine structures are the M0 v2.4 specs unchanged.

D cells by kind: {'other_object_same_scene': 33, 'same_object_other_event': 33}. By stratum: {'C': 42, 'D': 66, 'K': 24, 'K_out': 4, 'N': 22, 'R': 66, 'none': 11, 'support': 176}.

## What has not been done

S26 and S55 have not been re-reviewed by the two-judge panel; no model has seen the cells.
