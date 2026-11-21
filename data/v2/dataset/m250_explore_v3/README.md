# M250 EXPLORATION integration set (machine checks)

Data role: **EXPLORATION**. Built 2026-11-22 by `scripts/v2/s198_build_m250_exploration.py` (s198 v3). Status: agent-authored, solver-certified, machine-admitted against the dataset admission standard (checks 1.1-1.3, 2.1-2.8, 2.7b, 3.1-3.5, 4.1, 4.2, 6.2, 6.3); **not** panel-reviewed (checks 5.x and 6.1 are PENDING except for the M0 v2.5 structures, which are two-judge ADMITTED), not reviewed by a human. No model has seen these cells.

5232 cells (instance 0 of each structure) on **146 admitted** structures; **0 REJECTED**; 15 recorded infeasible without a spec; 0 source module(s) missing or broken.

## Source modules

- `roles_m0v25` (M0): 11 specs
- `roles_m250r2_a` (UPGRADED_V1): 16 specs
- `roles_m250r2_b` (UPGRADED_V1): 17 specs
- `roles_m250r2_c` (UPGRADED_V1): 17 specs
- `roles_m250r2_d` (UPGRADED_V1): 7 specs
- `roles_m250r2n_mech` (NEW): 10 specs
- `roles_m250r2n_em` (NEW): 10 specs
- `roles_m250r2n_thermo` (NEW): 10 specs
- `roles_m250r2n_waves` (NEW): 9 specs
- `roles_m250r2n_modern` (NEW): 10 specs
- `roles_m250r2n_extra` (NEW): 12 specs
- `roles_m250r2n_circ` (NEW): 9 specs
- `roles_m250r2n_qastro` (NEW): 8 specs

## Admitted (machine)

| structure | kind | domain | C | K | cells | panel |
|---|---|---|---|---|---|---|
| S01 | M0 | mechanics | yes | yes | 43 | ADMITTED |
| S07 | M0 | circuits | no | yes | 41 | ADMITTED |
| S13 | M0 | mechanics | yes | no | 37 | ADMITTED |
| S15 | M0 | circuits | no | yes | 37 | ADMITTED |
| S20 | M0 | optics | yes | no | 37 | ADMITTED |
| S26 | M0 | optics | no | no | 31 | ADMITTED |
| S27 | M0 | fluids | yes | no | 37 | ADMITTED |
| S30 | M0 | thermodynamics | yes | no | 37 | ADMITTED |
| S55 | M0 | thermodynamics | yes | no | 37 | ADMITTED |
| S72 | M0 | quantum | no | no | 31 | ADMITTED |
| S92 | M0 | fluids | yes | yes | 43 | ADMITTED |
| S03 | UPGRADED_V1 | mechanics | no | no | 31 | PENDING |
| S04 | UPGRADED_V1 | mechanics | yes | no | 37 | PENDING |
| S05 | UPGRADED_V1 | mechanics | yes | no | 36 | PENDING |
| S06 | UPGRADED_V1 | circuits | no | no | 31 | PENDING |
| S09 | UPGRADED_V1 | thermodynamics | no | no | 29 | PENDING |
| S10 | UPGRADED_V1 | mechanics | yes | yes | 43 | PENDING |
| S11 | UPGRADED_V1 | mechanics | yes | no | 37 | PENDING |
| S12 | UPGRADED_V1 | mechanics | yes | no | 37 | PENDING |
| S14 | UPGRADED_V1 | mechanics | yes | no | 37 | PENDING |
| S16 | UPGRADED_V1 | circuits | no | no | 31 | PENDING |
| S17 | UPGRADED_V1 | thermodynamics | yes | no | 37 | PENDING |
| S18 | UPGRADED_V1 | thermodynamics | yes | no | 36 | PENDING |
| S19 | UPGRADED_V1 | mechanics | no | no | 31 | PENDING |
| S21 | UPGRADED_V1 | acoustics | yes | no | 37 | PENDING |
| S22 | UPGRADED_V1 | acoustics | yes | yes | 43 | PENDING |
| S23 | UPGRADED_V1 | thermodynamics | no | no | 31 | PENDING |
| S24 | UPGRADED_V1 | thermodynamics | yes | no | 37 | PENDING |
| S25 | UPGRADED_V1 | circuits | yes | yes | 43 | PENDING |
| S28 | UPGRADED_V1 | mechanics | no | no | 31 | PENDING |
| S29 | UPGRADED_V1 | mechanics | yes | yes | 43 | PENDING |
| S31 | UPGRADED_V1 | mechanics | yes | no | 37 | PENDING |
| S32 | UPGRADED_V1 | mechanics | no | yes | 37 | PENDING |
| S33 | UPGRADED_V1 | mechanics | no | no | 31 | PENDING |
| S34 | UPGRADED_V1 | mechanics | yes | no | 37 | PENDING |
| S35 | UPGRADED_V1 | mechanics | yes | no | 37 | PENDING |
| S36 | UPGRADED_V1 | mechanics | yes | no | 37 | PENDING |
| S37 | UPGRADED_V1 | mechanics | yes | no | 36 | PENDING |
| S38 | UPGRADED_V1 | mechanics | yes | no | 36 | PENDING |
| S41 | UPGRADED_V1 | electromagnetism | yes | no | 37 | PENDING |
| S42 | UPGRADED_V1 | electromagnetism | yes | no | 37 | PENDING |
| S43 | UPGRADED_V1 | electromagnetism | no | no | 31 | PENDING |
| S44 | UPGRADED_V1 | electromagnetism | no | yes | 37 | PENDING |
| S45 | UPGRADED_V1 | electromagnetism | no | no | 30 | PENDING |
| S46 | UPGRADED_V1 | electromagnetism | no | no | 31 | PENDING |
| S47 | UPGRADED_V1 | electromagnetism | yes | yes | 43 | PENDING |
| S48 | UPGRADED_V1 | electromagnetism | yes | no | 36 | PENDING |
| S51 | UPGRADED_V1 | thermodynamics | yes | yes | 43 | PENDING |
| S52 | UPGRADED_V1 | thermodynamics | no | no | 31 | PENDING |
| S53 | UPGRADED_V1 | thermodynamics | yes | no | 37 | PENDING |
| S54 | UPGRADED_V1 | thermodynamics | no | no | 31 | PENDING |
| S56 | UPGRADED_V1 | thermodynamics | yes | yes | 42 | PENDING |
| S57 | UPGRADED_V1 | thermodynamics | no | no | 31 | PENDING |
| S61 | UPGRADED_V1 | optics | no | no | 31 | PENDING |
| S62 | UPGRADED_V1 | optics | yes | yes | 42 | PENDING |
| S63 | UPGRADED_V1 | acoustics | yes | yes | 43 | PENDING |
| S64 | UPGRADED_V1 | optics | yes | no | 37 | PENDING |
| S65 | UPGRADED_V1 | optics | no | no | 31 | PENDING |
| S66 | UPGRADED_V1 | optics | yes | no | 36 | PENDING |
| S67 | UPGRADED_V1 | optics | no | yes | 37 | PENDING |
| S71 | UPGRADED_V1 | quantum | yes | no | 36 | PENDING |
| S73 | UPGRADED_V1 | quantum | no | no | 31 | PENDING |
| S77 | UPGRADED_V1 | quantum | no | no | 31 | PENDING |
| S82 | UPGRADED_V1 | modern physics | no | no | 31 | PENDING |
| S91 | UPGRADED_V1 | fluids | yes | no | 37 | PENDING |
| S93 | UPGRADED_V1 | fluids | yes | no | 37 | PENDING |
| S94 | UPGRADED_V1 | fluids | yes | no | 36 | PENDING |
| S95 | UPGRADED_V1 | fluids | yes | no | 37 | PENDING |
| S201 | NEW | mechanics | yes | yes | 43 | PENDING |
| S202 | NEW | mechanics | yes | no | 37 | PENDING |
| S203 | NEW | mechanics | yes | no | 37 | PENDING |
| S204 | NEW | mechanics | no | no | 31 | PENDING |
| S205 | NEW | mechanics | no | yes | 37 | PENDING |
| S206 | NEW | mechanics | yes | yes | 43 | PENDING |
| S207 | NEW | mechanics | no | no | 31 | PENDING |
| S208 | NEW | mechanics | yes | no | 37 | PENDING |
| S209 | NEW | mechanics | no | no | 31 | PENDING |
| S210 | NEW | mechanics | yes | no | 36 | PENDING |
| S211 | NEW | electromagnetism | yes | no | 37 | PENDING |
| S212 | NEW | electromagnetism | yes | no | 37 | PENDING |
| S213 | NEW | electromagnetism | yes | no | 37 | PENDING |
| S214 | NEW | electromagnetism | yes | yes | 43 | PENDING |
| S215 | NEW | electromagnetism | yes | no | 37 | PENDING |
| S216 | NEW | electromagnetism | yes | no | 37 | PENDING |
| S217 | NEW | electromagnetism | no | yes | 36 | PENDING |
| S218 | NEW | electromagnetism | no | yes | 37 | PENDING |
| S219 | NEW | electromagnetism | yes | no | 36 | PENDING |
| S220 | NEW | electromagnetism | no | yes | 37 | PENDING |
| S221 | NEW | thermodynamics | yes | no | 37 | PENDING |
| S222 | NEW | thermodynamics | yes | no | 37 | PENDING |
| S223 | NEW | thermodynamics | yes | yes | 42 | PENDING |
| S224 | NEW | thermodynamics | yes | no | 36 | PENDING |
| S225 | NEW | thermodynamics | yes | no | 36 | PENDING |
| S226 | NEW | thermodynamics | yes | no | 35 | PENDING |
| S227 | NEW | thermodynamics | no | no | 31 | PENDING |
| S228 | NEW | thermodynamics | yes | no | 36 | PENDING |
| S229 | NEW | thermodynamics | yes | yes | 42 | PENDING |
| S230 | NEW | thermodynamics | no | no | 30 | PENDING |
| S231 | NEW | waves | yes | no | 36 | PENDING |
| S232 | NEW | waves | no | no | 31 | PENDING |
| S233 | NEW | optics | yes | no | 37 | PENDING |
| S234 | NEW | optics | yes | no | 37 | PENDING |
| S235 | NEW | fluids | yes | no | 36 | PENDING |
| S236 | NEW | waves | yes | no | 37 | PENDING |
| S238 | NEW | fluids | yes | no | 37 | PENDING |
| S239 | NEW | optics | no | no | 31 | PENDING |
| S240 | NEW | fluids | yes | yes | 42 | PENDING |
| S241 | NEW | modern physics | no | yes | 36 | PENDING |
| S242 | NEW | nuclear physics | yes | no | 37 | PENDING |
| S243 | NEW | nuclear physics | no | yes | 37 | PENDING |
| S244 | NEW | special relativity | no | no | 31 | PENDING |
| S245 | NEW | atomic physics | yes | yes | 42 | PENDING |
| S246 | NEW | nuclear physics | yes | no | 37 | PENDING |
| S247 | NEW | modern physics | yes | no | 37 | PENDING |
| S248 | NEW | modern physics | yes | no | 37 | PENDING |
| S249 | NEW | special relativity | no | no | 31 | PENDING |
| S250 | NEW | modern physics | yes | no | 37 | PENDING |
| S251 | NEW | gravitation | yes | no | 37 | PENDING |
| S252 | NEW | gravitation | no | no | 31 | PENDING |
| S253 | NEW | acoustics | yes | no | 37 | PENDING |
| S254 | NEW | acoustics | no | no | 29 | PENDING |
| S255 | NEW | solid_state | yes | no | 37 | PENDING |
| S256 | NEW | solid_state | yes | no | 37 | PENDING |
| S257 | NEW | nuclear | no | no | 31 | PENDING |
| S258 | NEW | nuclear | no | no | 30 | PENDING |
| S259 | NEW | statistical_physics | yes | no | 35 | PENDING |
| S260 | NEW | statistical_physics | yes | no | 37 | PENDING |
| S261 | NEW | fluids | no | no | 31 | PENDING |
| S262 | NEW | fluids | no | no | 31 | PENDING |
| S263 | NEW | circuits | yes | no | 35 | PENDING |
| S264 | NEW | circuits | yes | no | 37 | PENDING |
| S265 | NEW | circuits | yes | no | 36 | PENDING |
| S266 | NEW | circuits | no | no | 31 | PENDING |
| S267 | NEW | circuits | yes | no | 37 | PENDING |
| S268 | NEW | circuits | yes | no | 37 | PENDING |
| S270 | NEW | acoustics | yes | no | 36 | PENDING |
| S271 | NEW | acoustics | yes | yes | 42 | PENDING |
| S272 | NEW | acoustics | yes | no | 37 | PENDING |
| S273 | NEW | atomic physics | no | no | 31 | PENDING |
| S274 | NEW | atomic physics | no | yes | 37 | PENDING |
| S275 | NEW | quantum mechanics | no | no | 30 | PENDING |
| S276 | NEW | quantum mechanics | yes | no | 36 | PENDING |
| S277 | NEW | special relativity | yes | no | 36 | PENDING |
| S278 | NEW | special relativity | no | no | 31 | PENDING |
| S279 | NEW | special relativity | no | no | 31 | PENDING |
| S281 | NEW | gravitation | yes | no | 37 | PENDING |

## REJECTED

None.

Rejected structures keep their admission record (`admission/<id>.json`) and certificate; they have no cells and are never silently fixed (a replacement is a new spec, admission standard opening paragraph).

## Infeasible without a spec (recorded by the spec modules)

- **S08** (m250_a): repair round 1: both judges (high): the R sentence adds a capacitor in parallel, but the frozen dataset-v1 question asks for the energy in 'the two capacitors together'; the base text cannot change for an upgraded-v1 structure, so the R role has no unambiguous answer
- **S74** (m250_d): The inputs are the stated Bohr levels of the very atom (at rest in level n = 3, dropping to n = 2), its stated mass and constants. Re-preparing the atom in another level contradicts 'at rest in the Bohr level n = 3'; replacing it by another isotope offers only three honest masses (1, 2, 3 u) and contradicts the stated mass; attaching a fragment changes the Bohr levels through the bond. No R wording is true to the base, so no spec (new wording rule 2).
- **S75** (m250_d): Every input is a stated property of the scattering itself: the photon has the stated wavelength when it scatters. A preceding event that lengthens the wavelength (a first collision, a filter) contradicts 'a photon of wavelength 20 pm scatters', as the S02 extra release distance contradicted 'released from rest' (new wording rule 2); the angle is likewise a stated outcome, and the constants are stated.
- **S76** (m250_d): Zeff is a model input of the estimate, stated as the effective charge of the nucleus. Replacing the nucleus contradicts the stated charge, and the only second object with an effective charge is another nucleus, the same type as the target (new wording rule 4), so the co-present D has no different-type object and the R has no honest wording.
- **S78** (m250_d): The R quantity would have to be an isotopic replacement of the molecule (reduced mass), which contradicts the stated reduced mass; the co-present D needs another object that carries an isotopic reduced mass, which can only be another diatomic molecule, the same type as the target (new wording rule 4, ambiguous referent 'the molecule').
- **S79** (m250_d): The prompt states the kinetic energy with which the electrons strike the anode. A further accelerating stage before the anode contradicts that stated strike energy, and a replacement of the strike energy leaves no different-type object that is struck by electrons of a stated energy in the same frame (new wording rules 2 and 4).
- **S81** (m250_d): Every input is either a stated constant (c), the dimensionless speed beta or the lab flight distance d. A relevant event on d ('a further q of flight') contradicts the stated 'decays after it has travelled d at a constant speed', and an event on beta contradicts the stated constant speed; no honest additive or replacing event leaves the statement true.
- **S83** (m250_d): The inputs are the proton number, the neutron number and the mass defect of one fixed nucleus; the mass defect is not independent of the nucleon numbers, and the energy equivalent of the atomic mass unit is a stated constant. Changing any one input by an event describes a different nucleus, and the mass defect is dimensionless in the graph, so a quantity in physical units cannot be wired into it.
- **S84** (m250_d): The only inputs that change the age of this sample are its measured activity A, the activity of living carbon A0 and the half-life (a stated constant). Replacing the sample by another one (A replace) changes which tree the question is about, so the R contradicts the base; a background count (A subtract) contradicts the stated activity of the radiocarbon in the sample; A0 and the half-life are stated constants of the dating assumption. No quantity changes the asked age of THIS sample without replacing it or contradicting the prompt, so no spec (including the mass C).
- **S85** (m250_d): The released energy is Q = Dp - Dd - Da, so an excitation of the parent (Dp + q) is numerically identical to the opposite misuse on the daughter or the helium excess (Dd - q, Da - q): every additive event on one mass excess is confounded with a subtractive misuse on another, so the misuse curves cannot be separated from the gold (admission 2.5, blocking). The only other input that moves the answer is the daughter mass number, which no event changes honestly, and replacing the parent excess alone would describe a different parent whose daughter, stated in the problem, would differ.
- **S86** (m250_d): The answer is the speed, which saturates at c: two of the four instances start at 1500 and 2000 MeV, where a further energy that moves the speed by more than the loosest tolerance (1%) needs several GeV, and at those energies the misuse of replacing K by q lands within 1% of the relevant answer (confounded, blocking). Instances where the relevant event is distinguishable from its misuse and from D at all four instances do not exist for an additive event on K.
- **S237** (m250n_waves): repair round 1: no physically plausible R quantity: the added water height must be 9-47 m to pass the value and foil checks, far beyond any tide, and dredging (the v1 R) leaves a persistent state for the earlier-survey D
- **S269** (m250n_circ): repair round 1: the R quantity is a further pitch of the fork added to its stated frequency, and the base states that the pipe is tuned to exactly 440 Hz; any R sentence that raises the pitch before the tuning contradicts that stated value (GPT failed_transformation_identity), and one that raises it after the tuning changes the gold; a repair needs an R quantity on a separate input, which this structure does not have, and the K reference expression (c2/(4q) - f) is not physics either
- **S280** (m250n_qastro): repair round 2: no honest R quantity: any sentence that adds to the altitude of the initial or final orbit restates or contradicts the stated altitude, and a further burn contradicts 'two burns'; no added quantity enters the transfer without changing the premise
- **S282** (m250n_qastro): repair round 2: a stated added radius needs a thermal condition (peak wavelength unchanged) that makes the star's radius an action nobody performs; every wording of an increase of the radius is rated artificial and no added quantity avoids restating the stated 1.71 solar radii

## Composition (6.2, 6.3: reported, not forced)

- Domains: 16 (need >= 10), largest share 0.2055 (need <= 0.25): OK. {'acoustics': 8, 'atomic physics': 3, 'circuits': 11, 'electromagnetism': 18, 'fluids': 11, 'gravitation': 3, 'mechanics': 30, 'modern physics': 5, 'nuclear physics': 5, 'optics': 11, 'quantum mechanics': 6, 'solid state': 2, 'special relativity': 5, 'statistical physics': 2, 'thermodynamics': 23, 'waves': 3}
- Upper-university or multi-step: 113 of 146 (share 0.774, need >= 0.2): OK. Rule: level == upper_university or at least 3 computed relations.
- New structures admitted: 78; C feasible 0.6538 (need >= 0.5): OK; K feasible 0.1923 (need >= 0.3): NOT MET.
- Familiarity (6.2): 15 of 93 C quantities famous (share 0.1613, need <= 0.5): OK. {'famous': 15, 'standard': 57, 'uncommon': 21}
- Against the plan of record 5.2 target of 130 EXPLORATION structures: 146 admitted, shortfall 0.

## Judgement calls

1. **Flags count as failures.** An overlap detector flag (text ratio >= 0.85, relation-set Jaccard >= 0.8) rejects the structure under 1.2, as does an equal program hash or an identical value signature. The nearest neighbour and score are recorded for every structure, so a reviewer can see how far each was from a threshold.
2. **A structure is compared with its own id excluded**, so an upgraded v1 structure is not a duplicate of itself. Candidates are compared with the pool (dataset v1, every `library*`/`lib_*` structure) and with candidates admitted before them (M0 first, then upgraded, then new, by structure number), so two near-identical candidates do not both fall. DECOY-v1 and the EPC pool have no machine-readable structure pool in the repository and were not checked.
3. **Strict rule set is required.** `certify_v2` applies the reversal, co-present-D, time-anchor and scene-clause rules only for version `v2.1`; check 3.0 fails any structure whose spec version (or its module's `CERT_VERSION`) is not `v2.1`, and the version is recorded as `cert_version`. Checks 3.7 (article agreement) and 3.8 (pair distinctness) read every rendered sentence at every study and held-out value.
4. **Graph-level mutation report not run.** `certify.mutation_report` costs about 18 s per structure; 2.6 runs the role-spec mutations (identity values, repeated values, 1% solver error, broken cancellation, out-of-regime K values, marker word and reversal in D, digit in the scene clause) through `certify_v2`. Mutations that do not apply to a structure (no C, no K, a `replace` wiring) are not run for it.
5. **Absent C or K needs a reason.** A structure without C (or K) must have a NO_C (NO_K) reason of at least 20 characters in its spec module, else 2.3 (2.4) fails; the M0 specs carry no such tables and pass with the absence noted.
6. **Multi-step** (6.3) means at least 3 computed relations; upper-university is the level label of the v1 row or of `lib_m250_<domain>.LEVELS`.
7. **Provenance consistency** (`scripts/check_provenance_consistency.py`) is run once on this README text (dataset level), not per structure; its verdict is in `manifest.json`.
8. **Added row fields** against the M0 builder's rows: `dataset`, `data_role`, `m250_lineage`, `m250_source_module` (with `roles_m0v25` the M0 rows are otherwise byte-identical to `data/v2/dataset/m0_v25/cells.jsonl`; M0 module this build: `roles_m0v25`). New structures also get `level` from `lib_m250_<domain>.LEVELS` (the M0 builder leaves it empty).

## What has not been done

No panel review (5.x), no blind naturalness rating (6.1) for the structures marked PENDING; no human review; no model run. Panel packets: `scripts/v2/s199_m250_panel_packets.py`.

Provenance consistency (`scripts/check_provenance_consistency.py` on the text above): PASS {'NEGATED_MENTION': 2}.
