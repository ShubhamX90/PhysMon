# PhysMon Scoring Contract (Research v2.0, Stage 14.3)

Status: **prepared by the agent; independent reviewer sign-off PENDING (human).** An agent's own review is not
independent validation (v2 §9, p.43). Contract version `v2-scoring-contract-1`, fingerprint
`bb6bbec489ef185850a40c2d83955b4371a22b2343196135f2db885e6dabca81`
(`physmon.benchmark.scoring_contract.contract_fingerprint()`).

Plan reference: v2 B1.4 (p.7), P1.3 and P1.4 (p.17), C04 and C05 (p.33), card X03 (p.39), first sprint item 3
(p.48). Journal: `docs/journal/stage14/14.3_scoring_contract.md`. Evidence:
`results/stage14/s143_scoring_contract/attempt_20261016_6b78234/` (source commit `6b78234`, clean tree).

Scope of the evidence: tokenizer-only audit of the 1,120 committed Stage 6 behavioural records (140 families x 4
variants x 2 models) with the restored Qwen2.5-7B-Instruct and Llama-3.1-8B-Instruct tokenizers
(`tokenizer.json` sha256 `c0382117...` and `79e3e522...`; transformers 5.11.0). No model weights were opened.
Manual teacher-forced scoring is **NOT_EVALUATED** (it needs a forward pass).

## 1. What the Stage 6 records actually scored

- Scored string: the bare reference answer, for example `6.928 N*m` (`scripts/run_behavioural.py:531-535`).
- Prompt: the fixed system prompt plus the raw problem text, through the model's native chat template with the
  generation prompt (`run_behavioural.py:233-252`), tokenized with `add_special_tokens=True`
  (`src/physmon/models/logprob.py:35`); the answer is tokenized separately with `add_special_tokens=False` and
  concatenated (`logprob.py:36-37`). The score is the summed log-probability of the answer tokens.
- The instruction given to the model asks for exactly `Answer: [value] [unit]` (`run_behavioural.py:41-46`).

## 2. Audit of the Stage 6 interface

| Clause | Requirement | Result | Evidence |
|---|---|---|---|
| S1 | Raw prompt bytes and reference answer equal the rendered family JSON | PASS | 560 of 560 records per model |
| S2 | Native chat template applied with the generation prompt | PASS | 1,120 of 1,120 |
| S3 | No duplicated special token at the start of the scored prompt | **FAIL** | Llama: 560 of 560 prompts start with two BOS tokens (`128000, 128000`); Qwen: 0 |
| S4 | Separate tokenization of prompt and answer equals joint tokenization (the span is exact) | PASS | 560 of 560 per model |
| S5 | The scored string is the string the model is instructed to emit | **FAIL** | 1,120 of 1,120 generations start with `Answer:`; the scored string has no such prefix |
| S6 | Behavioural scoring and activation extraction used identical prompt token ids | **FAIL** | Llama: 0 of 560 identical (two BOS versus one); Qwen: 560 of 560 identical |
| S7 | The same boundary check holds for every frozen wrapper | PASS | all seven wrappers, 140 families, both models |

Answer-token counts differ by tokenizer: the same answer string is 3 to 10 tokens for Qwen (digits are split one
by one; median 6) and 2 to 7 for Llama (median 4). Raw gold log-probabilities are therefore not comparable across
models, and the plan already requires within-model, within-wrapper contrasts.

Length control (P1.4, descriptive, families are not independent): Spearman between answer-token count and the
legacy score S0 is 0.03 (Qwen) and 0.00 (Llama); with the range 0.08 and -0.11. Summed gold log-probability falls
with answer length (Spearman -0.45 Qwen, -0.25 Llama), as expected for a sum. These stored values give no
evidence that longer answers make the 0.5-nat label easier to cross.

## 3. Consequences for Phase-I numbers (not yet quantified)

- **Llama behavioural scores and generations (Stage 6 and later scripts that tokenize with
  `add_special_tokens=True`) used a double BOS.** The size of the effect on log-probabilities and on answers is
  unknown until a forward pass compares single and double BOS (required case, section 5).
- **Llama activations were extracted on a single-BOS prompt while the Llama labels and causal runs used the
  double-BOS prompt.** Any Llama claim that joins a probe trained on extracted activations to behavioural labels
  rests on two different token sequences. Qwen is unaffected by S3 and S6.
- **The teacher-forced target omits the instructed `Answer:` prefix** for both models. The gold log-probabilities
  (median -21.6 for Llama and -29.4 for Qwen; 5th to 95th percentile -29.2 to -14.9 and -47.0 to -11.1)
  therefore score a string the model does not start with; how much of the level and of the
  across-variant spread comes from this mismatch (hypothesis H0-F, v2 §4.1) is untested.

These do not change any committed value; they qualify how it may be interpreted. They are recorded in the claim
ledger as repo-derived findings.

## 4. Normative rules for every new scoring run (Stage 14.7 onward)

1. **Wrappers.** Use `scoring_contract.WRAPPERS`. The system instruction is `instruction_for(wrapper_id)` and the
   scored string is `render_target(wrapper_id, value, unit)`, so the scored string is the string the model is told
   to emit. Report only within-wrapper contrasts; never average raw log-probabilities across wrappers (v2 P1.3).
2. **Special tokens.** Tokenize a chat-templated string with `add_special_tokens=False`, or build ids from the
   template with the tokenizer's own template function, so that BOS appears exactly once. Assert
   `leading_special_count(ids, bos) <= 1` on every prompt; a violation is a failed record, not a warning.
3. **Span.** Score only `answer_span(n_prompt, n_answer)`; assert separate tokenization equals joint
   tokenization for every record; no prompt or padding position enters the sum.
4. **Identical sequences.** Behavioural scoring, generation, patching and activation extraction must use the
   same token ids for the same prompt; a preflight asserts it per model.
5. **Record fields.** For every score store the contract fingerprint, wrapper id, formatted-prompt SHA-256, prompt
   and target token ids (or lengths and hash), span start and end, tokenizer file hashes, model revision and
   dtype (v2 §9.1, p.43).
6. **Length and tokenization.** Report total, per-token, value-only and value-plus-unit log-likelihoods
   (P1.4). The value-only span needs character-offset alignment, which this stage does not implement.
7. **Parsing.** A generation that does not parse is a recorded outcome (`NOT_EVALUATED` for the endpoints that
   need it), never a zero.
8. **Gate before use.** The manual teacher-forced cases in section 5 must agree with an independent computation
   before a new scoring pipeline's numbers are reported.

## 5. Open items (require a model forward pass and explicit GPU authorization)

`manual_scoring_cases.json` in the attempt directory lists six representative cases for both models, with the
formatted-prompt hash and the expected answer span: the plan's near-match example (`CM_B_UM_059`), a frame or unit
rendering case, a wrong-answer case, a parse-failure (degraded) case, the smallest-magnitude answer, and a
scientific-notation answer. All are `NOT_EVALUATED`. Two further checks are needed before anything else is
scored on Llama:

- score a sample with a single BOS and with the double BOS and report the shift in gold log-probability and in the
  generated answer;
- score the bare answer and the `Answer: `-prefixed answer to measure the format-mismatch contribution (H0-F).

## 6. Sign-off

| Role | Name | Date | Decision |
|---|---|---|---|
| Contract author (agent) | Claude Sonnet 5.5 for atharvgaur1845 | 2026-10-16 | prepared |
| Independent reviewer | | | PENDING |
