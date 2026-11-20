# Dated amendments to frozen G1 documents

Each entry: date, document and section, the change, the reason, what data existed when it was written.

## A1 · 2026-11-19 · `dataset_admission_standard.md` section 5 (new check 5.3b)

**Change.** New check 5.3b (a judge-error guard, parallel to 5.3): a `high` flag of type `rendering_not_minimal` (or any flag whose
stated reason is that a sentence lacks the number or unit of its twin) on a **numeral-free control (N) sentence** is a judge error,
because the N sentence is numeral-free by design and its pass-2 claim says so (`numeral_free_twin_of` plus the note "This sentence
is the numeral-free control by design: it deliberately carries no number; the matching D sentence carries the number."). Such a
flag is recorded, does not count under 5.2, and the other qualified judge's verdict on that sentence decides. Every other flag of
the same judge on the item still counts.

**Reason.** The GPT-6.1 Sol judge raised exactly this flag on M0 v2.2 S72 (J15.1-046) and on M0 v2.3 S13 and S72 (J15.1-048),
after the explicit note was added; it did not raise it on the other nine structures with identical N designs. The frozen judge
prompt v3 asks that "variants of the same quantity preserve its number and unit"; the N control is by construction not such a
variant. Without this guard every structure would depend on whether GPT happens to apply that sentence to its N twin.

**Data when written.** Panel reviews of M0 v2.2 and v2.3 (both judges). No model output exists on any M0 v2.x cell. The guard is
applied to every item from M0 v2.3 on, and reported in every admission report that uses it (`s190b` lists the flag as
"5.3b judge error"). The qualification results (J15.1-029) are unaffected: bank v5 has no N sentence.

## A2 · 2026-11-20 · `src/physmon/scoring/grading_views.py` declared view (grader version v2)

**Change.** The primary `declared` view becomes grader version **v2**: an answer in the exact gold unit is correct when its absolute
error is at most **max(half a unit in its last printed place, 0.1% of the gold)** and at most 0.5% of the gold. Version v1 (half a
unit in the last printed place **and** at most 0.5%) is kept as an extra reported view `declared_v1`; the `convertible` view applies
the same v2 rule after unit conversion; `rel1pct`, the parser, the answer contract (O3 statuses) and foil matching are unchanged.
Every stored Stage 15 record is re-graded by a separate script into a new file beside the original (originals never modified);
every report says which grader version it used.

**Reason.** The G2 design-validation pilot (plan `docs/registry/v2/g2/design_validation_pilot_plan_m0v25.md`, question 1
"correctly graded") found records graded wrong whose answers equal the gold to within rounding, only because they print more
digits: "1367.71 m/s" against gold 1367.717 (error 0.0005%), "6.607 V" against 6.6081 V (0.016%), "1.796 s" against 1.7952 s.
Under v1 the more digits an answer prints, the stricter its test. Records graded wrong under v1 although within 0.1% of the gold:
333 (Qwen2.5-7B), 830 (Llama-3.1-8B), 361 (Qwen3-8B no-think) of 9,864 each. The pilot plan's decision rule for exactly this case
is fixed in advance: "A grading defect changes the grader before any further run, with a new grader version and a re-grade of
every stored record; never a per-record override."

**Why 0.1% and why the 0.5% ceiling stays.** v1's half-unit rule was chosen (J14.7-020) because a plain relative tolerance either
rejected correctly rounded answers (0.1%) or accepted a copy of a near-match cue (0.5%). The floor added here only accepts more;
it never rejects a correctly rounded answer that v1 accepted. Near-match cues in the v2.x datasets sit at least 1.1% from the gold
(M0 v2.5: minimum 1.11%), so a 0.1% floor cannot accept a cue copy. Answers 0.1-0.5% off still need correct rounding at their
printed precision, as before.

**Not changed, and why.** The pilot also shows R-cell answers 0.5-2% off because of arithmetic slips after a correct set-up (for
example Qwen2.5 on S30: every R answer within 3% of the R gold, none within the declared tolerance). These are wrong answers, not
grading defects; the T_R criterion (`r_tracking_criterion.md`, decision 8), the band and every threshold stay as frozen and are
checked in G2 step 3 on M250 as planned. The finding is recorded as a feasibility observation in the pilot review.

**Data when written.** The three G2 pilot runs on M0 v2.5 (29,592 records, EXPLORATION, sampled), their `s197` report and audit
sample, read by the main session. No G2 step-3 (M250 calibration) or G3 record exists. This amendment was written after seeing
those pilot records and is labelled so.
