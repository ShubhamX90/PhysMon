# Handoff · 2026-11-15 · Claude Opus 5.5 main session (user: Shubham Mishra)

Format and rules: `skills/physmon-journaling/SKILL.md`. Overwrite at every checkpoint.

## State in one paragraph
Stage 15, gate G1 (physics construct) nearly complete under plan of record **v2.2** (`docs/proposals/PhysMon_Research_v2.tex`,
revision file `docs/registry/v2/g1/plan_revision_v2.2_2026-11-14.md`). Done: LLM panel qualified (Claude Opus 5.5 and GPT-6.1 Sol,
prompt v3, protocol v3; J15.1-029); statistics, scorecard, phrasing-agreement rule B and k = 24 (J15.1-026, commit 0095a5e);
H4 trace extractor h4-v1 (J15.1-031); dataset admission standard (`docs/registry/v2/g1/dataset_admission_standard.md`);
M0 v2 dataset, 454 cells (`data/v2/dataset/m0_v2/`, J15.1-032); vLLM parity PASS for all three models (J15.1-030). The sealed
M0 pilot (`data/v2/runs/s15_m0pilot_*`, old wording) stays sealed.

## Running now
* Agent (Sonnet): M0 v2 LLM-panel packets, naturalness packets and admission scorer: `scripts/v2/s190*`,
  `docs/validation/v2/llm_panel/admission_m0v2/`, `/scratch/pabitra/physmon/judge/m0v2_{admission,naturalness}/`. When done:
  review, commit, then run fresh Claude judge instances (prompt v3 verbatim + assignment; audit with `s180`), score with `s190b`.
* Agent (Sonnet): non-physics control set, 16 structures: `src/physmon/benchmark/v2/nonphysics*.py`, `scripts/v2/s191*`,
  `data/v2/dataset/nonphysics_v1/`. When done: review every sentence and gold, commit, then panel review like M0 v2.
* Slurm: 449313 G0 extended HF-vs-TL parity (H200, pending); PhysMon generic workers 448194/448195 (A100, pending; no
  registered work left for them unless new runs are registered).

## Next steps, in order
1. Review and commit the two agents' outputs.
2. Claude panel review of M0 v2 and the non-physics set; GPT review after the user logs in to Codex
   (`CODEX_HOME=/scratch/pabitra/physmon/codex_home codex login --device-auth`; remove with `codex logout` afterwards).
3. G1 freeze record (decision log + journal): frozen analysis, scorecard, k, agreement rule, cards, admission standard,
   lexicons, extractor version; then unseal the M0 pilot as a pipeline/grading check only.
4. G2 design-validation pilot on M0 v2 (k = 24), then the M250 build.

## Open decisions
* None pending from the user. Recorded options: M1000 decided at M500 (plan v2.2 B2).

## Do not
* Modify `data/v2/dataset/{m0_pilot,v1,m0_v2}/`, `data/v2/runs/*`, banks v3-v5 or frozen prompts/protocols.
* Unseal the M0 pilot before the G1 freeze record.
* Edit files an active agent owns (listed above).

## Credentials and external state
* Codex/ChatGPT login: removed 2026-11-14 (`codex_home` deleted). Needed again for GPT panel reviews.

## Last journal entry and last commit
J15.1-032 (M0 v2) in `docs/journal/stage15/15.1_runner_and_batch1.md`; commit bfa88d5.
