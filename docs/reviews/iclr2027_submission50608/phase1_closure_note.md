# Phase-I closure note (2026-11-12)

G0 item 4 of the plan of record (`docs/proposals/PhysMon_Research_v2.tex`, "G0. Integrity closure"; its Phase-I
ledger section `sec:ledger`). Written in Stage 15.0 (journal J15.0-008). It states which statements of the
withdrawn submission 50608 (*Confidence Without Cause*) survive and which do not, on the evidence in this
repository. It adds no new result and changes no file beside it. Labels: [V] recomputed from committed files
(by `scripts/reviews/check_iclr2027_review_claims.py`, output `results/reviews/iclr2027_submission50608/attempt_20261111/claims_check.{json,md}`, or by the G0 scripts, output `results/g0/attempt_20261112/`); [I] inference.

## What survives: descriptive statements about the legacy label

All are descriptive, exploratory (data role UNASSIGNED_LEGACY / EXPLORATION), not paper-eligible, and about the
legacy `S_lp` label (largest drop of the teacher-forced log-probability of the bare certified string relative to
rendering 0), not about physics reasoning or reliability.

1. **The numbers in the paper reproduce from the committed artifacts** (X01, Stage 14.1; 21 of 23 review checks
   reproduce the reviewers' and the paper's values, `analysis.md` section 3) [V].
2. **The label moves with the base rendering**: 40-49% (Qwen) and 41-56% (Llama) of base-0 positives change
   with the choice of base (X02, Stage 14.2) [V].
3. **The label moves with the answer instruction**: on the 30 pilot families the S_lp of the threshold-registration
   run and of the panel run correlate at Spearman 0.043 (Qwen) and 0.447 (Llama); labels agree on 17 of 30 (Qwen,
   chance 16.2) and 27 of 30 (Llama, chance 25.4, with 2 and 3 positives); the same instruction reproduces exactly
   (40 of 40 families, Spearman 1.0, both models) (C2b, C2c; G0 item a) [V].
4. **The label moves with in-context answer information**: a correct formula hint lowers the bare-string
   log-probability by 3.69 to 5.53 nats on five stable families (baseline S_lp 0.0), so the label fires on all
   five, while the generated answer stays correct on four and becomes correct on one (TH_B_UM_003: 10460 J to
   41860 J); none becomes wrong (Qwen only; Llama NOT_EVALUATED: no Llama records exist, the file named
   `llama_primary_formula_stub.jsonl` is a byte copy of a Qwen run) (C3; G0 item b) [V]. Stage 14.14 and 14.17
   show the same phenomenon prospectively: every number in a prompt, including the numbers the problem needs,
   is boosted as an answer [V, Stage 14 journal].
5. **The label moves with the scoring string**: the scorer receives the bare certified string while all 560 Qwen
   generations begin with `Answer:`; median gold log-probability -29.45, and -27.03 even for the 209 renderings
   answered exactly `Answer: <certified string>` (C1) [V].
6. **The released benchmark and records keep their value as artifacts** (templates, per-rendering records,
   predictions, decision log), with the caveats of `analysis.md` sections 4 and 7: 155 of 155 templates are
   `created_by: agent`; cue-irrelevance rests on the symbolic certificate alone; template-cluster leakage
   (110 families in 34 clusters) [V].

## What does not survive, as stated

Every causal and every monitoring claim of the paper, and the framing that the label measures confidence or
reliability.

| Paper claim (contribution) | Status | Why (evidence) |
|---|---|---|
| (a) A certified benchmark of irrelevant-cue invariance, independently validated | Survives only as "solver-certified, agent-authored, not human-validated" | All templates `created_by: agent`; `pi_validated` set by PI self-review or an agent review delegated by the PI; human validation never run (C9; `results/g0/attempt_20261112/provenance_phase1_paper.json`: the paper's statement that language models "could not write physics" conflicts with the records); no Cue C identity check, loose Coulomb tolerance (C10) |
| (b) "Sensitivity" is common (Qwen 70/140, Llama 32/140) and reflects confidence in the answer | Not supported as a property of the model's physics behaviour | The counts reproduce, but the label depends on base, instruction, in-context information and scoring string (points 2-5 above); "registered" threshold chosen after the Stage 4 results (`docs/registry/v2/threshold_history.md`) |
| (c) A pre-generation monitor (L18 probe AUROC 0.760) "on par" with or beyond baselines | Not supported | The fitted entropy comparator (0.727) and the Wave 2 combined comparator (0.7048) are oracle (built from `logprob_correct_answer`); the oracle-free entropy baseline is 0.520 (C4; `docs/registry/v2/comparator_tags.yml`); the monitor scores 0.649 [0.46, 0.82] on the 37 families without an unresolved leakage sibling against 0.789 on the 98 clustered (C5d); the correctness probe's 0.766 is on its own target and 0.380 on the sensitivity label (C5b); the label it predicts is not a valid endpoint |
| (d) A paired-baseline evaluation standard | The standard survives as a method; the reported comparisons do not | Comparators were mislabelled as non-activation (C4); the standard itself is kept in v2 with oracle/deployable tags |
| (e) A causal handle: four L16 heads whose knockout "cancels" the sensitivity and are "necessary" | Not supported | The knockout inverts 17 of 20 families (+4.16 to -3.08 nats; recovery 1.87 is inversion, not cancellation); removing head 11 raises the certified answer's first-token logit by 3.76 on base and 3.77 on sensitive renderings (20 of 20 each), i.e. a cue-independent answer boost; heads chosen on the panel they were tested on (C8a-c). "Cancels" and "necessary" breach the registry's prohibited wording for C08 (4 violations found mechanically, `results/g0/attempt_20261112/claim_wording_phase1_paper.json`) |
| Frozen-probe transfer (0.820 pooled on 15 later families) and cross-model statements | Not supported | The paper's own within-cue-type values are 0.667 and 0.6875; that pooling inflates the 0.820 through cue-type base rates is the reviewers' reading, not recomputed here [R]; the paper itself reports no reliable causal effect for DeepSeek and Llama; registry C07/C09 prohibit transfer and shared-mechanism wording |

## Consequences for v2 [I]

- No v2 claim rests on a Phase-I number. Phase-I values stay SUBMITTED in the claim ledger
  (`docs/registry/v2/claim_ledger.jsonl`, rows P1L-*); none is promoted.
- The descriptive points 2-5 are the reason the v2 primary endpoint is free-generation correctness read against
  the model's own sampling noise, with every intervention read as an interaction (`src/physmon/causal/interaction.py`)
  and every comparator tagged oracle or deployable.
- The authorship and validation objection (reviewer Y9cR, Q5) applies equally to the Stage 14.19 gold dataset
  (260 items, all `UNREVIEWED`, agent-verified by the user's instruction of 2026-10-26); any text about it must pass
  `scripts/check_provenance_consistency.py`, and any manuscript must pass `scripts/check_claim_wording.py`.
