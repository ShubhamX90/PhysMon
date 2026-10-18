# Stage Journal Index

Plan of record: `docs/proposals/PhysMon_Research_v2.pdf`. Stage ordering below is the agent proposal in
`docs/proposals/PhysMon_Research_v2_working_digest.md` section 9, adopted on the user's instruction of
2026-10-16 ("start implementing stage by stage"). Stages are gated on correctness, not dates (v2 p.15, p.48).

| Stage | Topic | v2 reference | Compute | Status | Journal |
|---|---|---|---|---|---|
| 14.0 | Governance ingest: journal, decision-log entry, claim-to-artifact ledger, evidence-record contract, cards X01-X03 | P0.1, §9.1, §7 | CPU only | done | [14.0](stage14/14.0_governance_ingest.md) |
| 14.1 | X01 authoritative reproduction from committed raw records | P0.2, card X01 | CPU only | done (CPU scope); P0 gate open | [14.1](stage14/14.1_x01_reproduction.md) |
| 14.2 | X02 base-rotation attack with an executable CM_B_UM_059 unit test | B1.2, B1.3, P1.1, card X02 | CPU only | done (stored-value scope); retirement of the legacy base-0 label confirmed by the user 2026-10-17 (J14.2-011) | [14.2](stage14/14.2_x02_base_rotation.md) |
| 14.3 | Scoring-interface contract (prompt bytes, answer spans, wrappers) | B1.4, P1.3, card X03 | CPU design, small GPU later | done (tokenizer-only scope); reviewer sign-off and GPU cases pending | [14.3](stage14/14.3_scoring_contract.md) |
| 14.4 | Structure overlap and the five excluded stable families | B1.6, P3.5, P3.6, card X05 | CPU only | done (committed-data scope); monitor under cluster-held-out folds NOT_EVALUATED | [14.4](stage14/14.4_structure_overlap.md) |
| 14.5 | Validator qualification materials | B4, P3.1 | human task | done (instruments and candidate materials v2); bank reviewed by the user (30 of 33 items carried, 3 to re-review); no validator qualified, no physicist confirmation | [14.5](stage14/14.5_validator_qualification.md) |
| 14.6 | Typed generator and first 10 certified v2 structures | B3.2, B3 deliverable | CPU plus human review | done (generator and solver certificates); all 10 approved by one open user walkthrough, certificates still UNREVIEWED | [14.6](stage14/14.6_typed_generator.md) |
| 14.7 | Pilot on two dense models | B6, P1 | GPU | done (exploratory): smoke rerun passed (399217); full two-model pilot run (399969, 422 records OK); correctness rule declared (protocol 4b); both models near the correctness floor; open: certified-structure review, P0 gate | [14.7](stage14/14.7_pilot_preparation.md) |
| 14.8 | Descriptive analysis of the pilot records | B2, P1 | CPU only | done; no cue contrast is interpretable (design gaps recorded) | [14.8](stage14/14.8_pilot_analysis.md) |
| 14.9 | Anchor-matched decoy scoring and dtype noise floor | P1.7, §4 | GPU (job 400932) | done; noise floor and anchor-matched shifts measured; descriptive only | [14.9](stage14/14.9_anchor_decoy_and_noise.md) |
| 14.10 | X03 format and tokenization falsification (v2 structures, 7 wrappers) | X03, P1.3, P1.4 | CPU plan, GPU run | done (v2-structure version, job 401287); one wrapper (Qwen scientific) dominates the near-cell shift, sign persists in all 7; legacy-family version not done | [14.10](stage14/14.10_x03_wrapper_multiverse.md) |
| 14.11 | Immutable artifact registry and Slurm job register | P0.1, §9.1 | CPU only | done; 22 artifacts and 9 jobs registered, verification passes | [14.11](stage14/14.11_artifact_registry.md) |
| 14.12 | Copying versus relevance from the existing pilot records | P4, protocol §5 row 4 | CPU only | done for what the records support; matched relevant-role control not possible with these records | [14.12](stage14/14.12_copying_vs_relevance.md) |
| 14.13 | Reasoning-allowed pilot (correctness floor) | B2.4, B1.4 | CPU tooling, GPU run | tooling and frozen analysis committed; run pending | [14.13](stage14/14.13_reasoning_pilot.md) |
| 14.14 | Numeral-presence control (matched relevant-role comparison) | P4, protocol §5 row 4 | CPU plan and analysis, GPU run | plan (3,924 jobs) and analysis tooling committed; run pending | [14.14](stage14/14.14_numeral_presence_control.md) |
| 14.15 | Second structure batch S11-S20 (shorter chains, four domains) | B3, B6.1 | CPU only | done (certified, UNREVIEWED); 20 of 40 to 60 structures | [14.15](stage14/14.15_structures_batch_b.md) |
| 14.16 | Legacy-family X03 plan (60 families, 4 wrappers, candidate matrix) | X03, P1.3, P1.4 | CPU plan, GPU run | plan (8,448 jobs) committed; run pending | [14.16](stage14/14.16_legacy_x03_plan.md) |

Status values: `not started`, `in progress`, `done`, `blocked`, `superseded`.
