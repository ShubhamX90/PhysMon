# G2 step 1: design-validation pilot on M0 v2.2 · plan fixed before any record (2026-11-16)

Authority: plan of record v2.2, section 5.1 "G2. Measurement and calibration", item 1 ("are the contrasts unambiguous, feasible,
correctly certified and correctly graded? ... Defects found here change the generator, never the analysis of later data"); G1
freeze record `docs/registry/v2/g1/freeze/G1_FREEZE_RECORD.md`. Written before any run on M0 v2.2 exists. Journal J15.1-040.

## Runs (EXPLORATION, sampled, reasoning-v2, vLLM)

| Run id | Model | Thinking |
|---|---|---|
| `s15_g2pilot_m0v22_qwen25_7b` | Qwen2.5-7B-Instruct (`qwen_primary`) | none |
| `s15_g2pilot_m0v22_llama31_8b` | Llama-3.1-8B-Instruct (`llama_primary`) | none |
| `s15_g2pilot_m0v22_qwen3_8b_nothink` | Qwen3-8B (`qwen3_8b`) | off |

All 411 cells of `data/v2/dataset/m0_v22/cells.jsonl` (11 structures; no-cue, R, D, N, C, K, K_out, supporting), k = 24 samples per
cell (the G1-frozen k; the design check needs per-cell rates, and vLLM makes this cheap), 4,096 new tokens, max model length 8,192,
default sampling of the reasoning-v2 contract, one seed per sample fixed in the spec. Each model has a passed vLLM-vs-HF greedy
parity (J15.1-030).

## What the pilot checks (design questions, not hypotheses)

The pilot answers the four design questions per structure and per cell. Nothing here is a test of H0-H7; no F1-F3 status is
reported from M0 (it is EXPLORATION and too small), only the quantities below, each with its denominator.

1. **Correctly graded.** Grading audit: every record's O3 status (COMPLETE, budget exhaustion, format failure) and the three grading
   views. A sample of 10 records per (model, stratum) is read by the main session against the gold (reported as the reader's check,
   evidence class AGENT_READ). Defect: a record graded wrong whose final answer equals the gold within tolerance under a declared
   view, or graded right when it is not; any systematic parse failure (> 5% of COMPLETE records of a cell unparsed).
2. **Correctly certified.** For R cells: the share of COMPLETE samples matching the R gold, and the share matching the base gold
   (ignoring the R sentence). For D and N cells: the share matching the base gold, and the share matching any misuse curve. A cell is
   flagged for review (not a defect by itself) when, in every model, the modal COMPLETE answer equals neither the cell's gold nor a
   declared misuse value nor the placebo (an answer no certified route predicts suggests a reading the certificate missed).
3. **Unambiguous.** For R and D twins: phrasing agreement under rule B per structure (AGREE / DISAGREE / UNRESOLVED) on tracking
   share; WORDING_DEPENDENT structures listed. The two medium-flag sentences (S26 R1, S55 R1) are reported separately.
4. **Feasible for G3.** Per model: no-cue correctness over the 24 samples per structure (band [0.30, 0.85] of decision 9 reported
   beside), R-tracking share T_R per structure (criterion of decision 8 is checked in G2 step 3 on M250, not here), budget exhaustion
   and format failure rates, tokens per sample.

## Decision rules (fixed now)

* A grading defect (1) changes the grader before any further run, with a new grader version and a re-grade of every stored record;
  never a per-record override.
* A cell flagged under (2) is reviewed by the main session; if the review finds the certificate wrong or the sentence admits a
  second reading, the structure's spec is fixed in a new dataset version and the panel re-reviews it. The pilot records stay as the
  record of the defect and are never pooled with later data.
* A structure with DISAGREE under (3) in two or more models gets its wording reviewed before M250 uses the same pattern.
* No result of the pilot changes any frozen analysis rule, SESOI, k, or threshold (plan: "never the analysis of later data").

## Not done here

No hypothesis status, no model selection (G2 step 4 runs on M250 calibration), no misuse attribution beyond the per-cell shares.
