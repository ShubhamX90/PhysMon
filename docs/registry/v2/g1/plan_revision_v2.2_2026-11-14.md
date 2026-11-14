# Plan revision v2.2: amendments decided 2026-11-14

Authority: user instruction of 2026-11-14 ("go through the project entirely with heavy focus on the v2 plan ... improve
the plan wherever you find core issues ... special focus on the dataset ... just fix them"), on top of the delegation of
2026-11-13. Reviewed: the plan of record (`docs/proposals/PhysMon_Research_v2.tex`, sections on the construct, strata,
role-by-value design, outcomes, hypotheses, causal standard, gates, dataset plan, statistics), the G1 decisions
(`decisions_2026-11-13.md`), the generator (`src/physmon/benchmark/v2/rolevalue.py`, the M0 specs), the M0 pilot cells and
the October dataset v1. Data seen: none of the sealed M0 pilot outputs. Each amendment states the issue, the change and
where it lands. Labels: [V] checked in the repository, [I] reasoning.

Status of each: ADOPTED (text change only), ADOPTED + DATA (dataset work, `data/v2/dataset/m0_v2/`), ADOPTED + CODE,
PENDING-SIM (number fixed by the simulation in `results/stage15/g1_power/`).

## A. Core issues in the construct and design

### A1. The confirmatory core tests only the least physical stratum (ADOPTED)
**Issue [V].** G3's core run and G4's preregistered family are R and D only; C and K are "targeted ablations, added only
when the core run shows something to explain" and at most one secondary family reaches G4. But D is irrelevance by
*narrative* (another object, place or time): a model can pass it by reading the story, with no physics. C (cancellation)
and K (regime) are the strata in which irrelevance follows from the physics itself. As written, the confirmatory result
could be "selects correctly" without the physical strata ever being confirmed, and H6-extended could not be reached.
**Change.** (1) C and K cells are part of the G3 core run for every structure where they are feasible, unconditionally.
(2) G4 preregisters two families in fixed sequence: the primary R/D family F1-F3 (unchanged), then the **C/K family**
(tracking loss against N in C and in K, Holm within the family; decision 22), unconditionally and not as the "one secondary
family chosen in G3". The G3-chosen secondary family remains, third in the sequence. (3) Composition targets rise so the
C/K family can be powered: C feasible in at least 50% and K in at least 30% of *new* structures (was 30% and 20% overall).
**Lands in:** plan sections Gates G3/G4, statistics (multiple comparisons), dataset plan composition targets.

### A2. Disconnected (D) sentences signal irrelevance by remoteness only (ADOPTED + DATA)
**Issue [V].** Every M0 D phrasing puts the quantity somewhere else or at another time ("along a lab bench before it was
carried over", "across the floor of the next room yesterday"). That measures sensitivity to narrative remoteness, not
system membership; some read as artificial.
**Change.** Two D kinds, one per phrasing pair, both required: **co-present** (`other_object_same_scene`: a different
object or subsystem in the same scene at the same time, no physical path to the target) and **other event**
(`same_object_other_event`: the target object, in an event with no path to the target). Results are reported per kind;
the kind difference is the "system membership" moderator of H3. No marker words in either.

### A3. Relevant (R) and D sentences are not minimal pairs, and one R wording gives the answer away (ADOPTED + DATA + CODE)
**Issue [V].** S02 r0 ends "so it was already moving when the stated distance began": it states the physical consequence,
yet counts as marker-free because the lexicon only lists irrelevance words. R and D sentences also differ in length and
structure, so role is confounded with wording.
**Change.** (1) A consequence lexicon: no phrasing in any role may explain its own effect (`consequence_free` must be
true). (2) Phrasings come in pairs (r_i, d_i) sharing frame, numeral and unit and differing only in the attachment
phrase; length within three words; the difference is recorded. (3) Analyses pair phrasings by index (already in code,
J15.1-026).

### A4. C can be passed from memory (ADOPTED + DATA)
**Issue [I].** "Mass cancels on an incline / in a pendulum" is a classroom fact; a model can state it without computing.
**Change.** Each C quantity carries `textbook_familiarity` (famous / standard / uncommon); C results are reported by
familiarity; at M250 at most half of the C quantities may be "famous".

### A5. K is never tested where the condition fails (ADOPTED + DATA, optional per structure)
**Issue [I].** Invariance inside the regime cannot be told from ignoring the quantity. The spec already certifies an
out-of-regime law and a counter-regime value, but no cell uses them.
**Change.** A `K_out` cell where the question stays well-posed outside the regime (certified answer changes); recorded as
infeasible with the reason where it does not (a block that never slides has no "speed after sliding 4 m"). K_out is a
supporting condition: with K it shows whether the model establishes the condition (the stratum's stated correct
behaviour). Not part of a confirmatory family.

### A6. Usefulness is optional (ADOPTED)
**Issue [V].** Reviewer Bsyk's question (does any of this improve answers?) is answered only in optional G7.
**Change.** Two zero- or low-cost arms become required in G3 and are reported in G4: (1) **self-consistency**: the
majority answer over the k samples of a cell scored for tracking (no new generation); (2) **relevance instruction** on
no-cue, R and D cells at the middle value: does telling the model to identify what matters reduce D losses, and does it
make the model ignore R quantities (instruction-induced neglect)? Both are secondary, estimation only.

### A7. Step-by-step gold solutions exist only for base problems (ADOPTED + DATA)
**Issue [V].** October dataset v1 has a gold trace per base problem; M0 role cells have certified answers only, yet H4
(trace correct, answer contaminated) needs the certified intermediate values of the cell's own world.
**Change.** Every cell has a gold trace rendered from the graph: R with the step where q enters; D and N with the base
trace and the statement that q has no path; C showing q entering and cancelling; K checking the regime predicate. The H4
extractor (decision 12) reads against these.

### A8. Supporting conditions of October are missing from M0, and "exact match" never existed (ADOPTED + DATA)
**Issue [V].** The plan's G1 list requires proximity conditions with exact-match, near-within-tolerance and
tolerance-separated cues as distinct conditions; October's "near" cells were 5.38 and 5.4 against a gold of 5.387 and no
exact-match cell exists. M0 has none of the supporting cells.
**Change.** M0 v2 merges the October cells (non-numeric extra, numeric metadata, target-unit value on a separate object
at exact / near-high-overlap / near-low-overlap / moderate / far, incompatible unit, convertible unit, relevant edit,
role reversal) with certified tolerance status per grading view, plus relevance-instruction and position cells.

### A9. Value hygiene (ADOPTED + DATA + CODE)
**Issue [I].** Study values such as 1, 2, 3 m beside a 4 m input invite accidental coincidences with inputs or answers.
**Change.** A value may not equal a displayed input numeral; digit overlap with inputs and gold is recorded.

## B. Statistics and sampling

### B1. Samples per cell and the phrasing-agreement rule (PENDING-SIM)
**Issue [V].** At k = 8, J = 30 the implemented agreement check fails in worlds that are truly invariant (J15.1-026), so a
correct model would be labelled wording-dependent.
**Change.** k and the operational form of the plan's agreement rule are fixed from the simulation
(`results/stage15/g1_power/attempt_20261114/`) by this rule, written before the results exist: choose the agreement rule
that is closest to the plan's wording among those with false-disagreement at most 0.05 in agreeing worlds, then the
smallest k in {8, 12, 16, 24, 32, 40} giving at least 0.80 probability of the correct outcome in the invariant world and
at least 0.80 detection of true wording dependence at the planned J. The choice replaces decision 16's k = 8.

### B2. Dataset size (ADOPTED)
M250 and M500 stand. **M1000 option**: decided at the M500 point from the power simulation for the C/K family and
per-domain results; the generator, overlap detectors and id scheme are built now to reach 1,000 structures without
redesign. Admission standards never relax to reach a count.

## C. What does not change
The four strata and their certificates; tracking as the primary estimand; F1-F3 and their SESOIs; the four-outcome
language; structure as the unit of inference; the gates and data roles; the causal standard; the claim hierarchy; the
LLM panel protocol (v3). The sealed M0 pilot (`data/v2/dataset/m0_pilot/`, old wording) stays sealed and immutable; after
the freeze it is opened only as a pipeline and grading check. The design-validation pilot of G2 runs on M0 v2.

## D. Order of work after this revision
1. M0 v2 built, reviewed line by line, then reviewed by the qualified Claude judge (GPT when the user logs in again).
2. k and agreement rule fixed from the simulation (B1).
3. Plan text updated to v2.2 with a revision-log entry; PDF rebuilt.
4. Remaining G1 items: H4 trace extractor (against the new gold traces), non-physics control set (16 structures, same
   pair rules), dataset admission standard including A2-A5 and A9; then the freeze.
