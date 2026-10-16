# v2 claim-to-artifact ledger

`claim_ledger.jsonl` is the single, timestamped table of claims for Research Redesign v2.0
(`docs/proposals/PhysMon_Research_v2.pdf`; P0.1 p.16; audit alert C p.5). One JSON object per line.

- Contract and vocabularies: `src/physmon/governance/v2_contract.py`.
- Validator: `python3 scripts/v2/validate_claim_ledger.py` (fails on an empty or missing ledger).
- Journal: `docs/journal/stage14/`.

Row types: `phase1_ledger_item` (values transcribed from the plan's Phase-I table, source tag
`SUBMITTED`), `audit_alert`, `claim_level` (C1 to C6).

Every row starts as `verification_label=not_yet_checked` and `evidence_status=NOT_EVALUATED`. A row
changes only when a stage reproduces or checks it; the change must set `verified_in_stage` and
`journal_ref`, and `verified` or `different_but_explained` rows must list at least one artifact path.
`paper_eligibility` is `false` everywhere and can only become `true` for a confirmatory, verified row.

This ledger does not replace the Stage 13 registry (`docs/registry/experiment_registry.jsonl`), which is a
separate, historical record with its own vocabulary.
