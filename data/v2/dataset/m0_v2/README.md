# M0 v2: the design-validation pilot, revised wording and values

Data role: **EXPLORATION**. Status: **agent-authored, solver-certified, NOT yet reviewed by the LLM panel (and not yet reviewed by a human)**.

454 cells on 12 structures (instance 0 of each), a gold solving trace for every cell, and a certificate for every structure. Built by `scripts/v2/s188_build_m0_v2.py` from the specs in `src/physmon/benchmark/v2/roles_m0v2*.py`; rebuild with the same command to get identical files (the builder refuses to overwrite).

## What this is

The same twelve structures and the same base problems as the sealed `m0_pilot`. Each structure gets one extra sentence that carries a number q in a role: R (the answer must change by a certified amount), D (no physical path to the target, the answer must not change), C (appears in the governing relations and cancels), K (irrelevant while a regime holds), or N (the same sentence with no number). `m0_pilot` stays untouched; it already ran on models and is an immutable record.

## What changed against `m0_pilot`, and why

1. **Wording.** In M0, one R sentence explained its own consequence ("so it was already moving when the stated distance began"), a D sentence was unnatural ("across the floor of the next room yesterday"), and every D sentence signalled irrelevance only by being far away in place or time. Now every quantity has exactly two phrasing pairs. In a pair the R and D sentences share frame, number and unit and differ in a short attachment phrase (the difference is recorded in `certificates.json`; word counts differ by at most three). Pair 0 is object style and its D puts the number on another object in the same scene at the same time (`other_object_same_scene`); pair 1 is event style and its D puts it on the target object in an event that leaves the problem unchanged: `same_object_other_event` (a different event of the same object: S02, S20, S92) or `same_object_undone_event` (the change is added and then removed: the other nine). A checked list of consequence words and an extended list of marker words rule out explanations and giveaway words in every sentence; the flags `consequence_free` and `marker_free` are on every row. Two pairs (S02 and S26, pair 0) cannot share one frame honestly and are recorded as `pair_frame_matched: false` with the reason. In the nine `same_object_undone_event` structures the R twin says "left there" and the D twin "taken out again"; the three `same_object_other_event` structures use a different event (a slide along a bench, a rinse). Pair 0 of S26 is also recorded unmatched (the subject and the reference direction differ as well as the attachment). These are judgements a reviewer should check. Every row also carries `target_phrases` and `target_symbols` for the H4 trace extractor.
2. **Where the number lies.** No study value equals a displayed input, and none shares two leading digits with an input or with any answer of its structure (the old R values 5 kOhm, 2 kg, 6 V equalled inputs; 100 eV copied the 100.15 pm answer). Each row records `digit_overlap_with_inputs` and `digit_overlap_with_gold`. No value, read as a number or as a digit copy, equals another cell's answer.
3. **Gold traces for every cell** (`traces.jsonl`): R traces include the step where q enters, D and N traces the base trace plus a line saying the quantity has no path to the target, C traces show q entering the listed relations and cancelling, K traces check the regime predicate numerically. Each trace ends at the cell's certified answer (tested to 1e-9).
4. **Supporting cells from October** (`family: supporting`), with the proximity conditions now distinct and certified against the grading code: an exact-match value (the displayed gold), a near value 1.1% to 5% from the gold that all three grading views mark wrong (with high and with low leading-digit overlap), moderate and far values, the gold's digits in an incompatible unit, the gold's magnitude in a convertible unit, a non-numeric sentence, numeric metadata, a relevant edit and a role reversal. The October sentences that state that system B is isolated are kept for these cells, so they carry marker words (`marker_free: false`) by design; the role-by-value cells carry none.
5. **New supporting cells.** The relevance instruction ("Some of the information given may not be needed. Identify which quantities matter before you solve.") appended after the question for no-cue and for R and D at the middle value in both pairs (`instruction: relevance`). The sentence-before-context position cells (R and D, middle value, pair 0) exist only where the sentence reads correctly ahead of the context: 0 built, 24 recorded as infeasible (each R sentence refers to entities that the context introduces, or to a change that follows the stated state; the reason is in each structure's certificate). K_out cells (`stratum: K_out`) exist for S07 only: the other conditional quantities would make the question ill posed or ambiguous in time (reasons in the certificates).
6. **C familiarity.** Every cancelling quantity carries `textbook_familiarity` (famous, standard or uncommon) with a one-line reason, in `certificates.json` under `c_textbook_familiarity` and on every C row.
7. **Held-out values.** Every R/D, C and K quantity keeps two held-out values in its spec, certified and hygiene-checked like the study values and never emitted as cells (K_out has none).

## Files

- `cells.jsonl`: one row per cell. Fields of the October job format (usable by `s170_sampled_run.py plan --cells`) plus `family`, `stratum`, `condition`, `pair_id`, `d_kind`, `phrasing_id`, `instruction`, `consequence_free`, `marker_free`, `digit_overlap_with_inputs`, `digit_overlap_with_gold`, `source_ambiguous`, `cue_equals_gold`, `foils`, `placebo`, `confounded`, `tolerance_status`, `d_rationale` (D and N rows), `pair_token_difference`, `pair_frame_matched`, `source_ambiguous_by_design`, `ambiguous_views`, `textbook_familiarity` (C rows) and a `role` block as in `m0_pilot`. Supporting rows have `stratum: support` and `role.stratum: support`, so an analysis that selects R, D, C, K, N by stratum does not pool them.
- `traces.jsonl`: one gold trace per cell (`job_id`, `cell_id`, `gold_trace` with structured steps and text).
- `certificates.json`: per structure, every check with pass or fail, the pair records (token differences, word counts), the value hygiene, the infeasibility records, K_out and C familiarity.
- `manifest.json`: counts and file hashes.

## Reading `source_ambiguous` and `cue_equals_gold`

`source_ambiguous` is true when the sentence's own numeral (a role value copied or read in the target unit, or a proximity cue) lies inside a grading tolerance of the gold, so a correct answer could come from the sentence. In this build it is true on these rows only: {'nongov_convertible_unit_same_magnitude': 12, 'nongov_same_unit_exact': 12} (the exact-match cell, graded correct by all three views and carrying `cue_equals_gold: true`, and the convertible-unit cell, graded correct by the convertible and 1% views; `ambiguous_views` lists which). Both are source-ambiguous by design (rows that are ambiguous and not by design: none). It is false on every other row, including all near cells, which are certified wrong under the declared, convertible and 1% views.

## Counts

By family: {'role_by_value': 262, 'supporting': 192}. By stratum: {'C': 48, 'D': 72, 'K': 30, 'K_out': 4, 'N': 24, 'R': 72, 'none': 12, 'support': 192}.

Conditions that could not be built (never replaced by a nonsensical prompt; reasons in the certificates): K_out x4, before_context x24.

## What has not been done

No LLM-panel or human review of these sentences yet, and no model has seen the cells. Physics judgements for each structure (why the D event is disconnected, which stated conditions it leaves true, why K_out is or is not well posed) are in the specs and in `certificates.json` for a reviewer to check.
