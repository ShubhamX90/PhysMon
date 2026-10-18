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
| 14.5 | Validator qualification materials | B4, P3.1 | human task | done (instruments and candidate materials v2); bank reviewed by the user (30 of 33 items carried, 3 to re-review); no validator qualified, no physicist confirmation | [14.5](stage14/14.5_validator_qualification.md) |
| 14.6 | Typed generator and first 10 certified v2 structures | B3.2, B3 deliverable | CPU plus human review | done (generator and solver certificates); all 10 approved by one open user walkthrough, certificates still UNREVIEWED | [14.6](stage14/14.6_typed_generator.md) |
| 14.7 | Pilot on two dense models | B6, P1 | GPU | prepared; smoke rerun passed (399217); 20-job throughput test of the runner done (399539, Qwen, S01 only); full pilot not run; open: correctness-tolerance rule, new authorization, certified-structure review, P0 gate | [14.7](stage14/14.7_pilot_preparation.md) |
| 14.8 | Descriptive analysis of the pilot records | B2, P1 | CPU only | done; no cue contrast is interpretable (design gaps recorded) | [14.8](stage14/14.8_pilot_analysis.md) |
| 14.9 | Anchor-matched decoy scoring and dtype noise floor | P1.7, §4 | GPU (job 400932) | done; noise floor and anchor-matched shifts measured; descriptive only | [14.9](stage14/14.9_anchor_decoy_and_noise.md) |

Status values: `not started`, `in progress`, `done`, `blocked`, `superseded`.
