# Stage Journal Index

Plan of record: `docs/proposals/PhysMon_Research_v2.pdf`. Stage ordering below is the agent proposal in
`docs/proposals/PhysMon_Research_v2_working_digest.md` section 9, adopted on the user's instruction of
2026-10-16 ("start implementing stage by stage"). Stages are gated on correctness, not dates (v2 p.15, p.48).

| Stage | Topic | v2 reference | Compute | Status | Journal |
|---|---|---|---|---|---|
| 14.0 | Governance ingest: journal, decision-log entry, claim-to-artifact ledger, evidence-record contract, cards X01-X03 | P0.1, §9.1, §7 | CPU only | done | [14.0](stage14/14.0_governance_ingest.md) |
| 14.1 | X01 authoritative reproduction from committed raw records | P0.2, card X01 | CPU only | done (CPU scope); P0 gate open | [14.1](stage14/14.1_x01_reproduction.md) |
| 14.2 | X02 base-rotation attack with an executable CM_B_UM_059 unit test | B1.2, B1.3, P1.1, card X02 | CPU only | done (stored-value scope); retirement of the legacy label awaits user confirmation | [14.2](stage14/14.2_x02_base_rotation.md) |
| 14.3 | Scoring-interface contract (prompt bytes, answer spans, wrappers) | B1.4, P1.3, card X03 | CPU design, small GPU later | done (tokenizer-only scope); reviewer sign-off and GPU cases pending | [14.3](stage14/14.3_scoring_contract.md) |
| 14.4 | Structure overlap and the five excluded stable families | B1.6, P3.5, P3.6, card X05 | CPU only | done (committed-data scope); monitor under cluster-held-out folds NOT_EVALUATED | [14.4](stage14/14.4_structure_overlap.md) |
| 14.5 | Validator qualification materials | B4, P3.1 | human task | not started | |
| 14.6 | Typed generator and first 10 certified v2 structures | B3.2, B3 deliverable | CPU plus human review | not started | |
| 14.7 | Pilot on two dense models | B6, P1 | GPU | blocked on 14.2 to 14.4 and user approval | |

Status values: `not started`, `in progress`, `done`, `blocked`, `superseded`.
