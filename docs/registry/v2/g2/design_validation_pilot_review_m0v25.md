# G2 step 1: design-validation pilot on M0 v2.5 — main-session review · 2026-11-20

Plan: `design_validation_pilot_plan_m0v25.md` (with the 2026-11-16 plan it amends). Records: `results/stage15/s15_g2pilot_m0v25_*`
(3 models x 9,864 records, EXPLORATION, sampled, k = 24). Reports: `results/stage15/g2_pilot_m0v25_report/` (grader v1) and
`results/stage15/g2_pilot_m0v25_report_grader_v2/` (grader v2, amendment A2). Evidence class of every judgement below:
AGENT_READ (main session, Claude Opus 5.5). No hypothesis status, no F1-F3 label (plan: "Not done here").

## 1. Correctly graded — DEFECT FOUND, grader changed (decision rule 1)

* The audit sample (seed 197, 240 records) plus a full scan found records graded wrong although the answer equals the gold to
  rounding, only because more digits were printed: "1367.71 m/s" vs 1367.717 (S55), "6.607 V" vs 6.6081 (S07), "1.796 s" vs
  1.7952 (S13). Records graded wrong under grader v1 although within 0.1% of the gold: 333 (Qwen2.5-7B), 830 (Llama-3.1-8B),
  361 (Qwen3-8B no-think) of 9,864 each.
* Per the plan's rule ("a grading defect changes the grader ... new grader version and a re-grade of every stored record; never a
  per-record override"): amendment A2 (`docs/registry/v2/g1/freeze/amendments.md`), grader v2 = accept when the error is at most
  max(half a unit in the last printed place, 0.1% of gold) and at most 0.5%. Near-match cues sit at least 1.11% from gold, so no
  cue copy can be accepted. `s206` re-graded all three runs into new files: declared wrong -> correct 333 / 830 / 361,
  correct -> wrong 0 in every view; recomputed v1 reproduces every stored grade.
* Not a defect: LaTeX-wrapped final lines ("\text{Final answer: } 1367.7 \text{ m/s}", 15 records in Qwen3) are format failures
  under the frozen answer contract and stay UNPARSEABLE (their own O3 category, never counted wrong).
* Parse failures among COMPLETE records: 0 cells above 5% in every model.

## 2. Correctly certified — no certificate error found

* Cells whose modal COMPLETE answer is "none" in every model: six, all S01 (Atwood machine with a massive pulley, gold
  2.178 m/s^2). The modal answers are 2.45 (pulley inertia ignored), 2.8 (sign error on the pulley term) and 9.8 (g): model
  errors on the base problem, not a second reading. Qwen3 solves the no-cue problem in 39% of samples. Certificate correct.
* S30 R cells (Qwen2.5: 0/144 declared, 144/144 within 3% of the R gold, 0 near the base): responses set up
  (2.8 kg)(4186)(40)/1500 correctly and then mis-multiply (e.g. 471,952 for 468,832). The certificate is correct; the shortfall is
  arithmetic. Same pattern, smaller, in S26, S55, S07, S13 for Qwen2.5/Llama (share of R answers within 3% of the R gold far
  above the declared share). Recorded as a feasibility observation (section 4), not a defect.
* S55 R z1 modal 5000 (Qwen2.5 only): arithmetic garble; Qwen3 tracks S55 R at 0.76.

## 3. Unambiguous — wording review of DISAGREE structures (decision rule 3)

Rule-B DISAGREE in two or more models: S13 (v2 only), S20, S26, S27, S72, S92, all on the D twins. In M0 v2.x the two D
"phrasings" are two different D kinds by design: pair 0 = another object in the same scene, pair 1 = the same object in an earlier
event. DISAGREE therefore measures that the two kinds are misused at different rates, not that a sentence admits two readings:
earlier-event D is misused more in S26 and S92 (relevant-twin answers up to 0.83-1.00), other-object D more in S20 and S27
(the lamp moved / the second tank's pressure rise applied to the main object). The main session read every D sentence of these
structures; none admits a reading in which it is relevant. Finding for the analysis plan (reported, no rule changed): pooled D
estimates depend on the D kind; report D by kind.
Wording gap noted (no change to admitted M0): S20 d1 and S26 d1 say "in an earlier experiment" without "only" (rule 7, introduced
after M0 v2.3); M250 follows rule 7.

## 4. Feasible for G3 (reported; criteria are checked in G2 step 3 on M250)

| model | no-cue correct (v1 -> v2) | T_R of all (v1 -> v2) | budget exhausted | format failure |
|---|---|---|---|---|
| Qwen2.5-7B | 0.561 -> 0.598 (in band) | 0.376 -> 0.415 | 0.000 | 0.014 |
| Llama-3.1-8B | 0.284 -> 0.398 (in band under v2) | 0.164 -> 0.191 | 0.073 | 0.093 |
| Qwen3-8B no-think | 0.905 -> 0.924 (above band) | 0.587 -> 0.610 | 0.002 | 0.023 |

Observations: (a) M0 is too easy for Qwen3 (no-cue above the band); M250 is harder by design. (b) Llama-3.1-8B has high budget
exhaustion and format failure. (c) R-cell arithmetic difficulty depresses T_R for the 7-8B models (section 2): the R-tracking
criterion (T_R >= 0.40, decision 8) and the band stay frozen; a generator-side mitigation for later datasets (R values whose
arithmetic is no harder than the base problem's) is a design option, to be decided before the sealed set is built, never applied
to data already seen.
