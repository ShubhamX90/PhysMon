# G2 design-validation pilot report (M0 v2.2)

EXPLORATION, sampled. Plan: `docs/registry/v2/g2/design_validation_pilot_plan.md`. No hypothesis status, no F1-F3 label, no Holm. Non-COMPLETE records are their own category, never wrong; missing records are NOT_EVALUATED. Expected samples per cell: 24.

## Model `s15_g2pilot_m0v25_qwen25_7b`

Records 9864; cells 411, of which without records 0.

### 1. Grading (all structures)

| stratum | cells (missing) | O3 statuses | COMPLETE | declared | convertible | rel1pct | gap rel1pct-declared | unparsed among COMPLETE |
|---|---|---|---|---|---|---|---|---|
| none | 11 (0) | COMPLETE 263, UNPARSEABLE 1 | 263 | 148/263 (0.563) | 148/263 (0.563) | 184/263 (0.700) | 36/263 (0.137) | 0/263 (0.000) |
| R | 66 (0) | COMPLETE 1574, UNPARSEABLE 10 | 1574 | 595/1574 (0.378) | 595/1574 (0.378) | 968/1574 (0.615) | 373/1574 (0.237) | 0/1574 (0.000) |
| D | 66 (0) | COMPLETE 1572, UNPARSEABLE 12 | 1572 | 785/1572 (0.499) | 785/1572 (0.499) | 899/1572 (0.572) | 114/1572 (0.073) | 0/1572 (0.000) |
| N | 22 (0) | COMPLETE 524, MULTIPLE_CANDIDATES 3, UNPARSEABLE 1 | 524 | 322/524 (0.615) | 322/524 (0.615) | 394/524 (0.752) | 72/524 (0.137) | 0/524 (0.000) |
| C | 42 (0) | COMPLETE 996, MULTIPLE_CANDIDATES 2, UNPARSEABLE 10 | 996 | 631/996 (0.634) | 631/996 (0.634) | 697/996 (0.700) | 66/996 (0.066) | 0/996 (0.000) |
| K | 24 (0) | COMPLETE 556, UNPARSEABLE 20 | 556 | 423/556 (0.761) | 423/556 (0.761) | 423/556 (0.761) | 0/556 (0.000) | 0/556 (0.000) |
| K_out | 4 (0) | COMPLETE 96 | 96 | 0/96 (0.000) | 0/96 (0.000) | 0/96 (0.000) | 0/96 (0.000) | 0/96 (0.000) |
| support | 176 (0) | BUDGET_EXHAUSTED 2, COMPLETE 4146, MULTIPLE_CANDIDATES 1, UNPARSEABLE 75 | 4146 | 2375/4146 (0.573) | 2375/4146 (0.573) | 2957/4146 (0.713) | 582/4146 (0.140) | 0/4146 (0.000) |

Per structure, all strata (correct among COMPLETE):

| structure | records | COMPLETE | declared | convertible | rel1pct |
|---|---|---|---|---|---|
| S01 | 1032 | 951 | 42/951 (0.044) | 42/951 (0.044) | 43/951 (0.045) |
| S07 | 984 | 979 | 729/979 (0.745) | 729/979 (0.745) | 806/979 (0.823) |
| S13 | 888 | 863 | 501/863 (0.581) | 501/863 (0.581) | 779/863 (0.903) |
| S15 | 888 | 888 | 587/888 (0.661) | 587/888 (0.661) | 587/888 (0.661) |
| S20 | 888 | 887 | 459/887 (0.517) | 459/887 (0.517) | 459/887 (0.517) |
| S26 | 744 | 744 | 175/744 (0.235) | 175/744 (0.235) | 644/744 (0.866) |
| S27 | 888 | 882 | 694/882 (0.787) | 694/882 (0.787) | 694/882 (0.787) |
| S30 | 888 | 887 | 686/887 (0.773) | 686/887 (0.773) | 799/887 (0.901) |
| S55 | 888 | 871 | 467/871 (0.536) | 467/871 (0.536) | 675/871 (0.775) |
| S72 | 744 | 743 | 89/743 (0.120) | 89/743 (0.120) | 186/743 (0.250) |
| S92 | 1032 | 1032 | 850/1032 (0.824) | 850/1032 (0.824) | 850/1032 (0.824) |

Cells with more than 5% of COMPLETE records unparsed (no value in the gold unit): 0.
Cells with more than 5% of all records failing the answer format (UNPARSEABLE and similar): 25: `S01-i0:C:z0:c1:after_context`, `S01-i0:C:z2:c0:after_context`, `S01-i0:D:z0:d0:after_context`, `S01-i0:D:z0:d1:after_context`, `S01-i0:D:z1:d1:after_context`, `S01-i0:K:z0:k0:after_context`, `S01-i0:K:z0:k1:after_context`, `S01-i0:K:z1:k0:after_context`, `S01-i0:K:z1:k1:after_context`, `S01-i0:K:z2:k0:after_context`, `S01-i0:K:z2:k1:after_context`, `S01-i0:R:z0:r0:after_context`, `S01-i0:R:z1:r0:after_context`, `S01-i0:S:nongov_same_unit_exact`, `S01-i0:S:nongov_same_unit_moderate`, `S01-i0:S:nongov_same_unit_near_low_overlap`, `S01-i0:S:role_reversal`, `S07-i0:D:z1:d1:after_context:instr_relevance`, `S13-i0:N:d1:after_context`, `S13-i0:S:nongov_same_unit_exact`, `S13-i0:S:nongov_same_unit_far`, `S13-i0:S:numeric_metadata`, `S13-i0:no_cue:instr_relevance`, `S27-i0:S:role_reversal`, `S55-i0:S:role_reversal`.

### 2. Certification (per cell)

| cell | R gold | base gold | misuse (any) | placebo | modal (n of valued) | modal is |
|---|---|---|---|---|---|---|
| `S01-i0:N:d0:after_context` (S01) | n/a | 0/23 (0.000) | no declared misuse values | n/a | 2.45 (9 of 23) | none |
| `S01-i0:N:d1:after_context` (S01) | n/a | 0/24 (0.000) | no declared misuse values | n/a | 2.45 (13 of 24) | none |
| `S01-i0:R:z0:r0:after_context` (S01) | 0/22 (0.000) | 0/22 (0.000) | n/a | n/a | 1.6 (4 of 22) | none |
| `S01-i0:R:z0:r1:after_context` (S01) | 0/23 (0.000) | 0/23 (0.000) | n/a | n/a | 1.6 (3 of 23) | none |
| `S01-i0:D:z0:d0:after_context` (S01) | n/a | 1/22 (0.045) | 2/22 (0.091) [add 0/22 (0.000), digit_copy 0/22 (0.000), relevant_twin 0/22 (0.000), replace 2/22 (0.091), subtract 0/22 (0.000)] | n/a | 2.45 (6 of 22) | none |
| `S01-i0:D:z0:d1:after_context` (S01) | n/a | 0/20 (0.000) | 0/20 (0.000) [add 0/20 (0.000), digit_copy 0/20 (0.000), relevant_twin 0/20 (0.000), replace 0/20 (0.000), subtract 0/20 (0.000)] | n/a | 9.8 (5 of 20) | none |
| `S01-i0:R:z1:r0:after_context` (S01) | 2/21 (0.095) | 0/21 (0.000) | n/a | n/a | 1.21 (3 of 21) | none |
| `S01-i0:R:z1:r1:after_context` (S01) | 1/24 (0.042) | 0/24 (0.000) | n/a | n/a | 1.21 (6 of 24) | none |
| `S01-i0:D:z1:d0:after_context` (S01) | n/a | 1/23 (0.043) | 0/23 (0.000) [add 0/23 (0.000), digit_copy 0/23 (0.000), relevant_twin 0/23 (0.000), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 2.45 (8 of 23) | none |
| `S01-i0:D:z1:d1:after_context` (S01) | n/a | 0/22 (0.000) | 1/22 (0.045) [add 0/22 (0.000), digit_copy 0/22 (0.000), relevant_twin 1/22 (0.045), replace 0/22 (0.000), subtract 0/22 (0.000)] | n/a | 9.8 (6 of 22) | none |
| `S01-i0:R:z2:r0:after_context` (S01) | 0/23 (0.000) | 1/23 (0.043) | n/a | n/a | 0.738 (2 of 23, tie) | none |
| `S01-i0:R:z2:r1:after_context` (S01) | 1/23 (0.043) | 0/23 (0.000) | n/a | n/a | 0.737 (3 of 23) | none |
| `S01-i0:D:z2:d0:after_context` (S01) | n/a | 2/23 (0.087) | 0/23 (0.000) [add 0/23 (0.000), digit_copy 0/23 (0.000), relevant_twin 0/23 (0.000), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 2.45 (8 of 23) | none |
| `S01-i0:D:z2:d1:after_context` (S01) | n/a | 2/24 (0.083) | 0/24 (0.000) [add 0/24 (0.000), digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 0.737 (3 of 24, tie) | none |
| `S07-i0:N:d0:after_context` (S07) | n/a | 24/24 (1.000) | no declared misuse values | n/a | 6.61 (24 of 24) | gold (gold) |
| `S07-i0:N:d1:after_context` (S07) | n/a | 24/24 (1.000) | no declared misuse values | n/a | 6.61 (24 of 24) | gold (gold) |
| `S07-i0:R:z0:r0:after_context` (S07) | 0/24 (0.000) | 2/24 (0.083) | n/a | n/a | 5.56 (11 of 24) | none |
| `S07-i0:R:z0:r1:after_context` (S07) | 0/24 (0.000) | 2/24 (0.083) | n/a | n/a | 5.56 (11 of 24) | none |
| `S07-i0:D:z0:d0:after_context` (S07) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 6.61 (24 of 24) | gold (gold) |
| `S07-i0:D:z0:d1:after_context` (S07) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 6.61 (24 of 24) | gold (gold) |
| `S07-i0:R:z1:r0:after_context` (S07) | 5/24 (0.208) | 3/24 (0.125) | n/a | n/a | 12 (6 of 24) | none |
| `S07-i0:R:z1:r1:after_context` (S07) | 2/24 (0.083) | 1/24 (0.042) | n/a | n/a | 4.524 (7 of 24) | gold (gold) |
| `S07-i0:D:z1:d0:after_context` (S07) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 6.61 (24 of 24) | gold (gold) |
| `S07-i0:D:z1:d1:after_context` (S07) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 6.61 (24 of 24) | gold (gold) |
| `S07-i0:R:z2:r0:after_context` (S07) | 21/24 (0.875) | 2/24 (0.083) | n/a | n/a | 3.402 (20 of 24) | gold (gold) |
| `S07-i0:R:z2:r1:after_context` (S07) | 20/24 (0.833) | 0/24 (0.000) | n/a | n/a | 3.402 (18 of 24) | gold (gold) |
| `S07-i0:D:z2:d0:after_context` (S07) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 6.61 (24 of 24) | gold (gold) |
| `S07-i0:D:z2:d1:after_context` (S07) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 6.61 (24 of 24) | gold (gold) |
| `S13-i0:N:d0:after_context` (S13) | n/a | 16/23 (0.696) | no declared misuse values | n/a | 1.8 (19 of 23) | gold (gold) |
| `S13-i0:N:d1:after_context` (S13) | n/a | 17/22 (0.773) | no declared misuse values | n/a | 1.8 (18 of 22) | gold (gold) |
| `S13-i0:R:z0:r0:after_context` (S13) | 19/24 (0.792) | 1/24 (0.042) | n/a | n/a | 2.11 (19 of 24) | gold (gold) |
| `S13-i0:R:z0:r1:after_context` (S13) | 20/24 (0.833) | 0/24 (0.000) | n/a | n/a | 2.11 (20 of 24) | gold (gold) |
| `S13-i0:D:z0:d0:after_context` (S13) | n/a | 12/23 (0.522) | 0/23 (0.000) [digit_copy 0/23 (0.000), relevant_twin 0/23 (0.000), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 1.8 (13 of 23) | gold (gold) |
| `S13-i0:D:z0:d1:after_context` (S13) | n/a | 8/24 (0.333) | 11/24 (0.458) [digit_copy 0/24 (0.000), relevant_twin 3/24 (0.125), replace 0/24 (0.000), subtract 8/24 (0.333)] | n/a | 1.42 (8 of 24, tie) | foil (subtract:L) |
| `S13-i0:R:z1:r0:after_context` (S13) | 1/24 (0.042) | 7/24 (0.292) | n/a | n/a | 2.28 (8 of 24) | gold (gold) |
| `S13-i0:R:z1:r1:after_context` (S13) | 3/24 (0.125) | 0/24 (0.000) | n/a | n/a | 2.28 (14 of 24) | gold (gold) |
| `S13-i0:D:z1:d0:after_context` (S13) | n/a | 21/24 (0.875) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 1.8 (20 of 24) | gold (gold) |
| `S13-i0:D:z1:d1:after_context` (S13) | n/a | 10/23 (0.435) | 11/23 (0.478) [digit_copy 0/23 (0.000), relevant_twin 2/23 (0.087), replace 0/23 (0.000), subtract 9/23 (0.391)] | n/a | 1.8 (10 of 23) | gold (gold) |
| `S13-i0:R:z2:r0:after_context` (S13) | 12/24 (0.500) | 1/24 (0.042) | n/a | n/a | 2.46 (12 of 24) | gold (gold) |
| `S13-i0:R:z2:r1:after_context` (S13) | 12/23 (0.522) | 0/23 (0.000) | n/a | n/a | 2.46 (12 of 23) | gold (gold) |
| `S13-i0:D:z2:d0:after_context` (S13) | n/a | 13/24 (0.542) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 1.8 (16 of 24) | gold (gold) |
| `S13-i0:D:z2:d1:after_context` (S13) | n/a | 13/24 (0.542) | 6/24 (0.250) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 6/24 (0.250)] | n/a | 1.8 (14 of 24) | gold (gold) |
| `S15-i0:N:d0:after_context` (S15) | n/a | 19/24 (0.792) | no declared misuse values | n/a | 36 (19 of 24) | gold (gold) |
| `S15-i0:N:d1:after_context` (S15) | n/a | 18/24 (0.750) | no declared misuse values | n/a | 36 (18 of 24) | gold (gold) |
| `S15-i0:R:z0:r0:after_context` (S15) | 5/24 (0.208) | 0/24 (0.000) | n/a | n/a | 45.56 (5 of 24, tie) | gold (gold) |
| `S15-i0:R:z0:r1:after_context` (S15) | 4/24 (0.167) | 1/24 (0.042) | n/a | n/a | 205 (7 of 24) | none |
| `S15-i0:D:z0:d0:after_context` (S15) | n/a | 21/24 (0.875) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 36 (21 of 24) | gold (gold) |
| `S15-i0:D:z0:d1:after_context` (S15) | n/a | 19/24 (0.792) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 36 (19 of 24) | gold (gold) |
| `S15-i0:R:z1:r0:after_context` (S15) | 6/24 (0.250) | 4/24 (0.167) | n/a | n/a | 253.1 (10 of 24) | none |
| `S15-i0:R:z1:r1:after_context` (S15) | 6/24 (0.250) | 1/24 (0.042) | n/a | n/a | 253.1 (14 of 24) | none |
| `S15-i0:D:z1:d0:after_context` (S15) | n/a | 21/24 (0.875) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 36 (21 of 24) | gold (gold) |
| `S15-i0:D:z1:d1:after_context` (S15) | n/a | 17/24 (0.708) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 36 (17 of 24) | gold (gold) |
| `S15-i0:R:z2:r0:after_context` (S15) | 6/24 (0.250) | 1/24 (0.042) | n/a | n/a | 288 (10 of 24) | none |
| `S15-i0:R:z2:r1:after_context` (S15) | 6/24 (0.250) | 0/24 (0.000) | n/a | n/a | 288 (13 of 24) | none |
| `S15-i0:D:z2:d0:after_context` (S15) | n/a | 18/24 (0.750) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 36 (18 of 24) | gold (gold) |
| `S15-i0:D:z2:d1:after_context` (S15) | n/a | 15/24 (0.625) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 36 (15 of 24) | gold (gold) |
| `S20-i0:N:d0:after_context` (S20) | n/a | 7/24 (0.292) | no declared misuse values | n/a | 9.23 (17 of 24) | none |
| `S20-i0:N:d1:after_context` (S20) | n/a | 10/24 (0.417) | no declared misuse values | n/a | 9.23 (14 of 24) | none |
| `S20-i0:R:z0:r0:after_context` (S20) | 23/24 (0.958) | 0/24 (0.000) | n/a | n/a | 16.24 (23 of 24) | gold (gold) |
| `S20-i0:R:z0:r1:after_context` (S20) | 19/24 (0.792) | 0/24 (0.000) | n/a | n/a | 16.24 (19 of 24) | gold (gold) |
| `S20-i0:D:z0:d0:after_context` (S20) | n/a | 1/24 (0.042) | 17/24 (0.708) [add 0/24 (0.000), copy 0/24 (0.000), relevant_twin 17/24 (0.708), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 16.24 (16 of 24) | foil (relevant_twin) |
| `S20-i0:D:z0:d1:after_context` (S20) | n/a | 16/24 (0.667) | 6/24 (0.250) [add 0/24 (0.000), copy 0/24 (0.000), relevant_twin 6/24 (0.250), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 17.14 (16 of 24) | gold (gold) |
| `S20-i0:R:z1:r0:after_context` (S20) | 21/24 (0.875) | 0/24 (0.000) | n/a | n/a | 15.13 (21 of 24) | gold (gold) |
| `S20-i0:R:z1:r1:after_context` (S20) | 21/24 (0.875) | 0/24 (0.000) | n/a | n/a | 15.13 (21 of 24) | gold (gold) |
| `S20-i0:D:z1:d0:after_context` (S20) | n/a | 2/24 (0.083) | 18/24 (0.750) [add 0/24 (0.000), copy 0/24 (0.000), relevant_twin 16/24 (0.667), replace 0/24 (0.000), subtract 2/24 (0.083)] | n/a | 15.13 (16 of 24) | foil (relevant_twin) |
| `S20-i0:D:z1:d1:after_context` (S20) | n/a | 7/24 (0.292) | 12/24 (0.500) [add 0/24 (0.000), copy 0/24 (0.000), relevant_twin 12/24 (0.500), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 15.13 (12 of 24) | foil (relevant_twin) |
| `S20-i0:R:z2:r0:after_context` (S20) | 18/24 (0.750) | 0/24 (0.000) | n/a | n/a | 14.48 (15 of 24) | gold (gold) |
| `S20-i0:R:z2:r1:after_context` (S20) | 22/24 (0.917) | 0/24 (0.000) | n/a | n/a | 14.48 (19 of 24) | gold (gold) |
| `S20-i0:D:z2:d0:after_context` (S20) | n/a | 2/24 (0.083) | 15/24 (0.625) [add 0/24 (0.000), copy 0/24 (0.000), relevant_twin 15/24 (0.625), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 14.48 (15 of 24) | foil (relevant_twin) |
| `S20-i0:D:z2:d1:after_context` (S20) | n/a | 14/24 (0.583) | 6/24 (0.250) [add 0/24 (0.000), copy 0/24 (0.000), relevant_twin 6/24 (0.250), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 17.14 (14 of 24) | gold (gold) |
| `S26-i0:N:d0:after_context` (S26) | n/a | 1/24 (0.042) | no declared misuse values | n/a | 25.34 (7 of 24) | gold (gold) |
| `S26-i0:N:d1:after_context` (S26) | n/a | 4/24 (0.167) | no declared misuse values | n/a | 25.34 (5 of 24) | gold (gold) |
| `S26-i0:R:z0:r0:after_context` (S26) | 0/24 (0.000) | 0/24 (0.000) | n/a | n/a | 28.67 (5 of 24) | gold (gold) |
| `S26-i0:R:z0:r1:after_context` (S26) | 3/24 (0.125) | 0/24 (0.000) | n/a | n/a | 28.64 (4 of 24) | gold (gold) |
| `S26-i0:D:z0:d0:after_context` (S26) | n/a | 15/24 (0.625) | 0/24 (0.000) [add 0/24 (0.000), copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 25.37 (13 of 24) | gold (gold) |
| `S26-i0:D:z0:d1:after_context` (S26) | n/a | 0/24 (0.000) | 20/24 (0.833) [add 0/24 (0.000), copy 0/24 (0.000), relevant_twin 20/24 (0.833), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 28.67 (5 of 24) | foil (relevant_twin) |
| `S26-i0:R:z1:r0:after_context` (S26) | 0/24 (0.000) | 0/24 (0.000) | n/a | n/a | 31.09 (7 of 24) | gold (gold) |
| `S26-i0:R:z1:r1:after_context` (S26) | 0/24 (0.000) | 0/24 (0.000) | n/a | n/a | 31.14 (4 of 24, tie) | gold (gold) |
| `S26-i0:D:z1:d0:after_context` (S26) | n/a | 14/24 (0.583) | 0/24 (0.000) [add 0/24 (0.000), copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 25.37 (14 of 24) | gold (gold) |
| `S26-i0:D:z1:d1:after_context` (S26) | n/a | 1/24 (0.042) | 20/24 (0.833) [add 0/24 (0.000), copy 0/24 (0.000), relevant_twin 20/24 (0.833), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 31.16 (12 of 24) | foil (relevant_twin) |
| `S26-i0:R:z2:r0:after_context` (S26) | 2/24 (0.083) | 0/24 (0.000) | n/a | n/a | 32.74 (9 of 24) | gold (gold) |
| `S26-i0:R:z2:r1:after_context` (S26) | 4/24 (0.167) | 0/24 (0.000) | n/a | n/a | 32.62 (7 of 24) | gold (gold) |
| `S26-i0:D:z2:d0:after_context` (S26) | n/a | 15/24 (0.625) | 0/24 (0.000) [add 0/24 (0.000), copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 25.37 (15 of 24) | gold (gold) |
| `S26-i0:D:z2:d1:after_context` (S26) | n/a | 0/24 (0.000) | 24/24 (1.000) [add 0/24 (0.000), copy 0/24 (0.000), relevant_twin 24/24 (1.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 32.67 (6 of 24) | foil (relevant_twin) |
| `S27-i0:N:d0:after_context` (S27) | n/a | 23/24 (0.958) | no declared misuse values | n/a | 218.6 (23 of 24) | gold (gold) |
| `S27-i0:N:d1:after_context` (S27) | n/a | 24/24 (1.000) | no declared misuse values | n/a | 218.6 (24 of 24) | gold (gold) |
| `S27-i0:R:z0:r0:after_context` (S27) | 21/24 (0.875) | 0/24 (0.000) | n/a | n/a | 226.1 (21 of 24) | gold (gold) |
| `S27-i0:R:z0:r1:after_context` (S27) | 24/24 (1.000) | 0/24 (0.000) | n/a | n/a | 226.1 (24 of 24) | gold (gold) |
| `S27-i0:D:z0:d0:after_context` (S27) | n/a | 0/24 (0.000) | 23/24 (0.958) [copy 0/24 (0.000), relevant_twin 23/24 (0.958), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 226.1 (23 of 24) | foil (relevant_twin) |
| `S27-i0:D:z0:d1:after_context` (S27) | n/a | 10/24 (0.417) | 14/24 (0.583) [copy 0/24 (0.000), relevant_twin 13/24 (0.542), replace 1/24 (0.042), subtract 0/24 (0.000)] | n/a | 226.1 (13 of 24) | foil (relevant_twin) |
| `S27-i0:R:z1:r0:after_context` (S27) | 22/24 (0.917) | 0/24 (0.000) | n/a | n/a | 233.6 (22 of 24) | gold (gold) |
| `S27-i0:R:z1:r1:after_context` (S27) | 24/24 (1.000) | 0/24 (0.000) | n/a | n/a | 233.6 (24 of 24) | gold (gold) |
| `S27-i0:D:z1:d0:after_context` (S27) | n/a | 3/24 (0.125) | 20/24 (0.833) [copy 0/24 (0.000), relevant_twin 20/24 (0.833), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 233.6 (20 of 24) | foil (relevant_twin) |
| `S27-i0:D:z1:d1:after_context` (S27) | n/a | 12/24 (0.500) | 12/24 (0.500) [copy 0/24 (0.000), relevant_twin 10/24 (0.417), replace 2/24 (0.083), subtract 0/24 (0.000)] | n/a | 218.6 (12 of 24) | gold (gold) |
| `S27-i0:R:z2:r0:after_context` (S27) | 15/24 (0.625) | 0/24 (0.000) | n/a | n/a | 253.6 (15 of 24) | gold (gold) |
| `S27-i0:R:z2:r1:after_context` (S27) | 22/24 (0.917) | 0/24 (0.000) | n/a | n/a | 253.6 (22 of 24) | gold (gold) |
| `S27-i0:D:z2:d0:after_context` (S27) | n/a | 0/24 (0.000) | 22/24 (0.917) [copy 0/24 (0.000), relevant_twin 22/24 (0.917), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 253.6 (22 of 24) | foil (relevant_twin) |
| `S27-i0:D:z2:d1:after_context` (S27) | n/a | 14/24 (0.583) | 10/24 (0.417) [copy 0/24 (0.000), relevant_twin 10/24 (0.417), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 218.6 (14 of 24) | gold (gold) |
| `S30-i0:N:d0:after_context` (S30) | n/a | 24/24 (1.000) | no declared misuse values | n/a | 223.3 (23 of 24) | gold (gold) |
| `S30-i0:N:d1:after_context` (S30) | n/a | 24/24 (1.000) | no declared misuse values | n/a | 223.3 (22 of 24) | gold (gold) |
| `S30-i0:R:z0:r0:after_context` (S30) | 0/24 (0.000) | 0/24 (0.000) | n/a | n/a | 314.9 (3 of 24) | none |
| `S30-i0:R:z0:r1:after_context` (S30) | 0/24 (0.000) | 0/24 (0.000) | n/a | n/a | 309.2 (6 of 24) | none |
| `S30-i0:D:z0:d0:after_context` (S30) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 223.3 (24 of 24) | gold (gold) |
| `S30-i0:D:z0:d1:after_context` (S30) | n/a | 23/24 (0.958) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 223.3 (23 of 24) | gold (gold) |
| `S30-i0:R:z1:r0:after_context` (S30) | 0/24 (0.000) | 0/24 (0.000) | n/a | n/a | 380 (3 of 24) | gold (gold) |
| `S30-i0:R:z1:r1:after_context` (S30) | 0/24 (0.000) | 0/24 (0.000) | n/a | n/a | 375.2 (3 of 24) | none |
| `S30-i0:D:z1:d0:after_context` (S30) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 223.3 (24 of 24) | gold (gold) |
| `S30-i0:D:z1:d1:after_context` (S30) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 223.3 (24 of 24) | gold (gold) |
| `S30-i0:R:z2:r0:after_context` (S30) | 0/24 (0.000) | 0/24 (0.000) | n/a | n/a | 509.3 (3 of 24) | none |
| `S30-i0:R:z2:r1:after_context` (S30) | 0/24 (0.000) | 0/24 (0.000) | n/a | n/a | 509.1 (2 of 24, tie) | none |
| `S30-i0:D:z2:d0:after_context` (S30) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 223.3 (24 of 24) | gold (gold) |
| `S30-i0:D:z2:d1:after_context` (S30) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 223.3 (23 of 24) | gold (gold) |
| `S55-i0:N:d0:after_context` (S55) | n/a | 17/24 (0.708) | no declared misuse values | n/a | 1368 (22 of 24) | gold (gold) |
| `S55-i0:N:d1:after_context` (S55) | n/a | 14/24 (0.583) | no declared misuse values | n/a | 1368 (23 of 24) | gold (gold) |
| `S55-i0:R:z0:r0:after_context` (S55) | 0/24 (0.000) | 0/24 (0.000) | n/a | n/a | 1504 (5 of 24, tie) | none |
| `S55-i0:R:z0:r1:after_context` (S55) | 0/23 (0.000) | 0/23 (0.000) | n/a | n/a | 1512 (6 of 23) | none |
| `S55-i0:D:z0:d0:after_context` (S55) | n/a | 19/24 (0.792) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 1368 (22 of 24) | gold (gold) |
| `S55-i0:D:z0:d1:after_context` (S55) | n/a | 16/24 (0.667) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 1368 (22 of 24) | gold (gold) |
| `S55-i0:R:z1:r0:after_context` (S55) | 0/24 (0.000) | 0/24 (0.000) | n/a | n/a | 5000 (21 of 24) | none |
| `S55-i0:R:z1:r1:after_context` (S55) | 0/24 (0.000) | 0/24 (0.000) | n/a | n/a | 5000 (22 of 24) | none |
| `S55-i0:D:z1:d0:after_context` (S55) | n/a | 18/24 (0.750) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 1368 (23 of 24) | gold (gold) |
| `S55-i0:D:z1:d1:after_context` (S55) | n/a | 16/24 (0.667) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 1368 (24 of 24) | gold (gold) |
| `S55-i0:R:z2:r0:after_context` (S55) | 19/24 (0.792) | 0/24 (0.000) | n/a | n/a | 1766 (23 of 24) | gold (gold) |
| `S55-i0:R:z2:r1:after_context` (S55) | 17/24 (0.708) | 0/24 (0.000) | n/a | n/a | 1766 (20 of 24) | gold (gold) |
| `S55-i0:D:z2:d0:after_context` (S55) | n/a | 11/24 (0.458) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 1368 (21 of 24) | gold (gold) |
| `S55-i0:D:z2:d1:after_context` (S55) | n/a | 15/24 (0.625) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 1368 (22 of 24) | gold (gold) |
| `S72-i0:N:d0:after_context` (S72) | n/a | 7/24 (0.292) | no declared misuse values | n/a | 100 (4 of 24) | gold (gold) |
| `S72-i0:N:d1:after_context` (S72) | n/a | 2/24 (0.083) | no declared misuse values | n/a | 100 (2 of 24) | gold (gold) |
| `S72-i0:R:z0:r0:after_context` (S72) | 0/24 (0.000) | 0/24 (0.000) | n/a | n/a | 88.6 (3 of 24) | gold (gold) |
| `S72-i0:R:z0:r1:after_context` (S72) | 0/24 (0.000) | 1/24 (0.042) | n/a | n/a | 88.7 (2 of 24, tie) | gold (gold) |
| `S72-i0:D:z0:d0:after_context` (S72) | n/a | 4/24 (0.167) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 100 (3 of 24, tie) | gold (add:mc2, gold, subtract:mc2) |
| `S72-i0:D:z0:d1:after_context` (S72) | n/a | 0/24 (0.000) | 4/24 (0.167) [digit_copy 0/24 (0.000), relevant_twin 4/24 (0.167), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 89.5 (2 of 24) | none |
| `S72-i0:R:z1:r0:after_context` (S72) | 6/24 (0.250) | 0/24 (0.000) | n/a | n/a | 79.2 (6 of 24) | gold (gold) |
| `S72-i0:R:z1:r1:after_context` (S72) | 3/24 (0.125) | 0/24 (0.000) | n/a | n/a | 79.2 (2 of 24, tie) | gold (gold) |
| `S72-i0:D:z1:d0:after_context` (S72) | n/a | 1/24 (0.042) | 1/24 (0.042) [digit_copy 1/24 (0.042), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 31.8 (2 of 24, tie) | none |
| `S72-i0:D:z1:d1:after_context` (S72) | n/a | 0/24 (0.000) | 10/24 (0.417) [digit_copy 0/24 (0.000), relevant_twin 10/24 (0.417), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 79.2 (3 of 24, tie) | foil (relevant_twin) |
| `S72-i0:R:z2:r0:after_context` (S72) | 2/24 (0.083) | 0/24 (0.000) | n/a | n/a | 67.4 (2 of 24, tie) | gold (gold) |
| `S72-i0:R:z2:r1:after_context` (S72) | 1/24 (0.042) | 0/24 (0.000) | n/a | n/a | 213.7 (6 of 24) | none |
| `S72-i0:D:z2:d0:after_context` (S72) | n/a | 3/24 (0.125) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000)] | n/a | 100.1 (2 of 24, tie) | gold (add:mc2, gold, subtract:mc2) |
| `S72-i0:D:z2:d1:after_context` (S72) | n/a | 0/24 (0.000) | 5/24 (0.208) [digit_copy 0/24 (0.000), relevant_twin 5/24 (0.208), replace 0/24 (0.000)] | n/a | 67.4 (3 of 24) | foil (relevant_twin) |
| `S92-i0:N:d0:after_context` (S92) | n/a | 23/24 (0.958) | no declared misuse values | n/a | 3.92 (23 of 24) | gold (gold) |
| `S92-i0:N:d1:after_context` (S92) | n/a | 24/24 (1.000) | no declared misuse values | n/a | 3.92 (24 of 24) | gold (gold) |
| `S92-i0:R:z0:r0:after_context` (S92) | 21/24 (0.875) | 1/24 (0.042) | n/a | n/a | 5.39 (21 of 24) | gold (gold) |
| `S92-i0:R:z0:r1:after_context` (S92) | 24/24 (1.000) | 0/24 (0.000) | n/a | n/a | 5.39 (24 of 24) | gold (gold) |
| `S92-i0:D:z0:d0:after_context` (S92) | n/a | 23/24 (0.958) | 0/24 (0.000) [add 0/24 (0.000), digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 3.92 (23 of 24) | gold (gold) |
| `S92-i0:D:z0:d1:after_context` (S92) | n/a | 5/24 (0.208) | 19/24 (0.792) [add 0/24 (0.000), digit_copy 0/24 (0.000), relevant_twin 19/24 (0.792), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 5.39 (19 of 24) | foil (relevant_twin) |
| `S92-i0:R:z1:r0:after_context` (S92) | 21/24 (0.875) | 3/24 (0.125) | n/a | n/a | 6.37 (21 of 24) | gold (gold) |
| `S92-i0:R:z1:r1:after_context` (S92) | 23/24 (0.958) | 1/24 (0.042) | n/a | n/a | 6.37 (23 of 24) | gold (gold) |
| `S92-i0:D:z1:d0:after_context` (S92) | n/a | 19/24 (0.792) | 0/24 (0.000) [add 0/24 (0.000), digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 3.92 (19 of 24) | gold (gold) |
| `S92-i0:D:z1:d1:after_context` (S92) | n/a | 6/24 (0.250) | 18/24 (0.750) [add 0/24 (0.000), digit_copy 0/24 (0.000), relevant_twin 18/24 (0.750), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 6.37 (18 of 24) | foil (relevant_twin) |
| `S92-i0:R:z2:r0:after_context` (S92) | 21/24 (0.875) | 2/24 (0.083) | n/a | n/a | 7.35 (21 of 24) | gold (gold) |
| `S92-i0:R:z2:r1:after_context` (S92) | 24/24 (1.000) | 0/24 (0.000) | n/a | n/a | 7.35 (24 of 24) | gold (gold) |
| `S92-i0:D:z2:d0:after_context` (S92) | n/a | 19/24 (0.792) | 0/24 (0.000) [add 0/24 (0.000), digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 3.92 (19 of 24) | gold (gold) |
| `S92-i0:D:z2:d1:after_context` (S92) | n/a | 3/24 (0.125) | 21/24 (0.875) [add 0/24 (0.000), digit_copy 0/24 (0.000), relevant_twin 21/24 (0.875), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 7.35 (21 of 24) | foil (relevant_twin) |

### 3. Ambiguity (rule B on tracking share, phrasing 0 vs 1)

| structure | R state (diff, 95% CI) | D state (diff, 95% CI) |
|---|---|---|
| S01 | AGREE (+0.000, [-0.071, +0.071]; 2/72 (0.028) vs 2/72 (0.028)) | AGREE (+0.028, [-0.048, +0.109]; 4/72 (0.056) vs 2/72 (0.028)) |
| S07 | UNRESOLVED (+0.056, [-0.097, +0.205]; 26/72 (0.361) vs 22/72 (0.306)) | AGREE (+0.000, [-0.051, +0.051]; 72/72 (1.000) vs 72/72 (1.000)) |
| S13 | UNRESOLVED (-0.042, [-0.199, +0.118]; 32/72 (0.444) vs 35/72 (0.486)) | DISAGREE (+0.208, [+0.045, +0.356]; 46/72 (0.639) vs 31/72 (0.431)) |
| S15 | UNRESOLVED (+0.014, [-0.123, +0.150]; 17/72 (0.236) vs 16/72 (0.222)) | UNRESOLVED (+0.125, [-0.013, +0.258]; 60/72 (0.833) vs 51/72 (0.708)) |
| S20 | AGREE (+0.000, [-0.116, +0.116]; 62/72 (0.861) vs 62/72 (0.861)) | DISAGREE (-0.444, [-0.563, -0.304]; 5/72 (0.069) vs 37/72 (0.514)) |
| S26 | UNRESOLVED (-0.069, [-0.162, +0.015]; 2/72 (0.028) vs 7/72 (0.097)) | DISAGREE (+0.597, [+0.467, +0.702]; 44/72 (0.611) vs 1/72 (0.014)) |
| S27 | DISAGREE (-0.167, [-0.274, -0.066]; 58/72 (0.806) vs 70/72 (0.972)) | DISAGREE (-0.458, [-0.574, -0.324]; 3/72 (0.042) vs 36/72 (0.500)) |
| S30 | AGREE (+0.000, [-0.051, +0.051]; 0/72 (0.000) vs 0/72 (0.000)) | AGREE (+0.014, [-0.038, +0.075]; 72/72 (1.000) vs 71/72 (0.986)) |
| S55 | UNRESOLVED (+0.028, [-0.113, +0.167]; 19/72 (0.264) vs 17/72 (0.236)) | UNRESOLVED (+0.014, [-0.138, +0.165]; 48/72 (0.667) vs 47/72 (0.653)) |
| S72 | UNRESOLVED (+0.056, [-0.040, +0.155]; 8/72 (0.111) vs 4/72 (0.056)) | DISAGREE (+0.111, [+0.037, +0.204]; 8/72 (0.111) vs 0/72 (0.000)) |
| S92 | DISAGREE (-0.111, [-0.208, -0.027]; 63/72 (0.875) vs 71/72 (0.986)) | DISAGREE (+0.653, [+0.507, +0.752]; 61/72 (0.847) vs 14/72 (0.194)) |

Cross-structure rule B (library `phrasing_difference_agreement` on per-structure differences): R: AGREE (J=11); D: UNRESOLVED (J=11).
WORDING_DEPENDENT structures (DISAGREE on R or D twins): S13, S20, S26, S27, S72, S92.

Medium-flag cells (reported apart):

* S26 R:r1 cell `S26-i0:R:z0:r1:after_context`: R gold 3/24 (0.125); base gold 0/24 (0.000); modal 28.64.
* S26 R:r1 cell `S26-i0:R:z1:r1:after_context`: R gold 0/24 (0.000); base gold 0/24 (0.000); modal 31.14.
* S26 R:r1 cell `S26-i0:R:z2:r1:after_context`: R gold 4/24 (0.167); base gold 0/24 (0.000); modal 32.62.
* S55 R:r1 cell `S55-i0:R:z0:r1:after_context`: R gold 0/23 (0.000); base gold 0/23 (0.000); modal 1512.0.
* S55 R:r1 cell `S55-i0:R:z1:r1:after_context`: R gold 0/24 (0.000); base gold 0/24 (0.000); modal 5000.0.
* S55 R:r1 cell `S55-i0:R:z2:r1:after_context`: R gold 17/24 (0.708); base gold 0/24 (0.000); modal 1766.0.

### 4. Feasibility

| structure | no-cue correct, of all samples | of COMPLETE | band [0.30, 0.85] | T_R of all | T_R of COMPLETE | budget exhausted | format failure | tokens mean / max |
|---|---|---|---|---|---|---|---|---|
| S01 | 0/24 (0.000) | 0/23 (0.000) | out of band | 4/144 (0.028) | 4/136 (0.029) | 1/1032 (0.001) | 80/1032 (0.078) | 479 / 4096 |
| S07 | 24/24 (1.000) | 24/24 (1.000) | out of band | 48/144 (0.333) | 48/144 (0.333) | 0/984 (0.000) | 5/984 (0.005) | 405 / 658 |
| S13 | 15/24 (0.625) | 15/24 (0.625) | in band | 67/144 (0.465) | 67/143 (0.469) | 0/888 (0.000) | 25/888 (0.028) | 302 / 528 |
| S15 | 17/24 (0.708) | 17/24 (0.708) | in band | 33/144 (0.229) | 33/144 (0.229) | 0/888 (0.000) | 0/888 (0.000) | 452 / 1045 |
| S20 | 3/24 (0.125) | 3/24 (0.125) | out of band | 124/144 (0.861) | 124/144 (0.861) | 0/888 (0.000) | 1/888 (0.001) | 349 / 620 |
| S26 | 2/24 (0.083) | 2/24 (0.083) | out of band | 9/144 (0.062) | 9/144 (0.062) | 0/744 (0.000) | 0/744 (0.000) | 353 / 625 |
| S27 | 23/24 (0.958) | 23/24 (0.958) | out of band | 128/144 (0.889) | 128/144 (0.889) | 0/888 (0.000) | 6/888 (0.007) | 392 / 852 |
| S30 | 24/24 (1.000) | 24/24 (1.000) | out of band | 0/144 (0.000) | 0/144 (0.000) | 0/888 (0.000) | 1/888 (0.001) | 320 / 516 |
| S55 | 14/24 (0.583) | 14/24 (0.583) | in band | 36/144 (0.250) | 36/143 (0.252) | 0/888 (0.000) | 17/888 (0.019) | 388 / 550 |
| S72 | 4/24 (0.167) | 4/24 (0.167) | out of band | 12/144 (0.083) | 12/144 (0.083) | 1/744 (0.001) | 0/744 (0.000) | 683 / 4096 |
| S92 | 22/24 (0.917) | 22/24 (0.917) | out of band | 134/144 (0.931) | 134/144 (0.931) | 0/1032 (0.000) | 0/1032 (0.000) | 495 / 856 |
| ALL | 148/264 (0.561) | 148/263 (0.563) | in band | 595/1584 (0.376) | 595/1574 (0.378) | 2/9864 (0.000) | 135/9864 (0.014) | 419 / 4096 |

## Model `s15_g2pilot_m0v25_llama31_8b`

Records 9864; cells 411, of which without records 0.

### 1. Grading (all structures)

| stratum | cells (missing) | O3 statuses | COMPLETE | declared | convertible | rel1pct | gap rel1pct-declared | unparsed among COMPLETE |
|---|---|---|---|---|---|---|---|---|
| none | 11 (0) | BUDGET_EXHAUSTED 17, COMPLETE 231, UNPARSEABLE 16 | 231 | 75/231 (0.325) | 75/231 (0.325) | 132/231 (0.571) | 57/231 (0.247) | 0/231 (0.000) |
| R | 66 (0) | BUDGET_EXHAUSTED 125, COMPLETE 1311, UNPARSEABLE 148 | 1311 | 260/1311 (0.198) | 260/1311 (0.198) | 522/1311 (0.398) | 262/1311 (0.200) | 4/1311 (0.003) |
| D | 66 (0) | BUDGET_EXHAUSTED 129, COMPLETE 1271, UNPARSEABLE 184 | 1271 | 141/1271 (0.111) | 141/1271 (0.111) | 367/1271 (0.289) | 226/1271 (0.178) | 5/1271 (0.004) |
| N | 22 (0) | BUDGET_EXHAUSTED 36, COMPLETE 454, UNPARSEABLE 38 | 454 | 143/454 (0.315) | 143/454 (0.315) | 247/454 (0.544) | 104/454 (0.229) | 1/454 (0.002) |
| C | 42 (0) | BUDGET_EXHAUSTED 64, COMPLETE 838, UNPARSEABLE 106 | 838 | 317/838 (0.378) | 317/838 (0.378) | 507/838 (0.605) | 190/838 (0.227) | 1/838 (0.001) |
| K | 24 (0) | BUDGET_EXHAUSTED 76, COMPLETE 455, UNPARSEABLE 45 | 455 | 78/455 (0.171) | 78/455 (0.171) | 182/455 (0.400) | 104/455 (0.229) | 0/455 (0.000) |
| K_out | 4 (0) | BUDGET_EXHAUSTED 12, COMPLETE 82, UNPARSEABLE 2 | 82 | 2/82 (0.024) | 2/82 (0.024) | 6/82 (0.073) | 4/82 (0.049) | 0/82 (0.000) |
| support | 176 (0) | BUDGET_EXHAUSTED 259, COMPLETE 3591, UNPARSEABLE 374 | 3591 | 961/3591 (0.268) | 961/3591 (0.268) | 1749/3591 (0.487) | 788/3591 (0.219) | 9/3591 (0.003) |

Per structure, all strata (correct among COMPLETE):

| structure | records | COMPLETE | declared | convertible | rel1pct |
|---|---|---|---|---|---|
| S01 | 1032 | 720 | 2/720 (0.003) | 2/720 (0.003) | 8/720 (0.011) |
| S07 | 984 | 906 | 35/906 (0.039) | 35/906 (0.039) | 494/906 (0.545) |
| S13 | 888 | 835 | 131/835 (0.157) | 131/835 (0.157) | 622/835 (0.745) |
| S15 | 888 | 849 | 283/849 (0.333) | 283/849 (0.333) | 284/849 (0.335) |
| S20 | 888 | 661 | 409/661 (0.619) | 409/661 (0.619) | 426/661 (0.644) |
| S26 | 744 | 674 | 21/674 (0.031) | 21/674 (0.031) | 295/674 (0.438) |
| S27 | 888 | 815 | 581/815 (0.713) | 581/815 (0.713) | 588/815 (0.721) |
| S30 | 888 | 780 | 223/780 (0.286) | 223/780 (0.286) | 559/780 (0.717) |
| S55 | 888 | 822 | 3/822 (0.004) | 3/822 (0.004) | 117/822 (0.142) |
| S72 | 744 | 473 | 2/473 (0.004) | 2/473 (0.004) | 8/473 (0.017) |
| S92 | 1032 | 698 | 287/698 (0.411) | 287/698 (0.411) | 311/698 (0.446) |

Cells with more than 5% of COMPLETE records unparsed (no value in the gold unit): 10: `S20-i0:S:role_reversal`, `S55-i0:D:z0:d0:after_context`, `S55-i0:D:z1:d1:after_context:instr_relevance`, `S55-i0:R:z1:r1:after_context:instr_relevance`, `S72-i0:D:z0:d1:after_context`, `S72-i0:D:z2:d0:after_context`, `S72-i0:N:d0:after_context`, `S72-i0:R:z0:r1:after_context`, `S72-i0:R:z1:r1:after_context:instr_relevance`, `S92-i0:D:z1:d1:after_context:instr_relevance`.
Cells with more than 5% of all records failing the answer format (UNPARSEABLE and similar): 216: `S01-i0:C:z0:c0:after_context`, `S01-i0:C:z0:c1:after_context`, `S01-i0:C:z1:c1:after_context`, `S01-i0:C:z2:c0:after_context`, `S01-i0:C:z2:c1:after_context`, `S01-i0:D:z0:d0:after_context`, `S01-i0:D:z1:d0:after_context`, `S01-i0:D:z1:d0:after_context:instr_relevance`, `S01-i0:D:z1:d1:after_context`, `S01-i0:D:z2:d0:after_context`, `S01-i0:D:z2:d1:after_context`, `S01-i0:K:z0:k0:after_context`, `S01-i0:K:z0:k1:after_context`, `S01-i0:K:z1:k0:after_context`, `S01-i0:K:z1:k1:after_context`, `S01-i0:K:z2:k0:after_context`, `S01-i0:K:z2:k1:after_context`, `S01-i0:N:d0:after_context`, `S01-i0:N:d1:after_context`, `S01-i0:R:z0:r0:after_context`, `S01-i0:R:z0:r1:after_context`, `S01-i0:R:z1:r0:after_context`, `S01-i0:R:z1:r0:after_context:instr_relevance`, `S01-i0:R:z2:r0:after_context`, `S01-i0:S:nongov_incompatible_unit_same_digits`, `S01-i0:S:nongov_same_unit_exact`, `S01-i0:S:nongov_same_unit_far`, `S01-i0:S:nongov_same_unit_moderate`, `S01-i0:S:nongov_same_unit_near_high_overlap`, `S01-i0:S:nongov_same_unit_near_low_overlap`, `S01-i0:S:nonnumeric_extra`, `S01-i0:S:relevant_edit`, `S01-i0:no_cue:instr_relevance`, `S07-i0:K:z2:k1:after_context`, `S07-i0:N:d1:after_context`, `S07-i0:S:role_reversal`, `S13-i0:C:z2:c1:after_context`, `S13-i0:D:z0:d0:after_context`, `S13-i0:D:z0:d1:after_context`, `S13-i0:D:z1:d0:after_context`, `S13-i0:N:d0:after_context`, `S13-i0:N:d1:after_context`, `S13-i0:R:z0:r1:after_context`, `S13-i0:R:z1:r0:after_context`, `S13-i0:R:z1:r0:after_context:instr_relevance`, `S13-i0:S:nongov_convertible_unit_same_magnitude`, `S13-i0:S:nongov_same_unit_exact`, `S13-i0:S:nongov_same_unit_far`, `S13-i0:S:nongov_same_unit_near_high_overlap`, `S13-i0:no_cue`, `S15-i0:D:z0:d1:after_context`, `S15-i0:D:z2:d0:after_context`, `S15-i0:K:z0:k0:after_context`, `S15-i0:K:z0:k1:after_context`, `S15-i0:R:z0:r1:after_context`, `S15-i0:R:z1:r0:after_context:instr_relevance`, `S15-i0:R:z1:r1:after_context:instr_relevance`, `S20-i0:C:z0:c0:after_context`, `S20-i0:C:z0:c1:after_context`, `S20-i0:C:z1:c0:after_context`, `S20-i0:C:z1:c1:after_context`, `S20-i0:C:z2:c0:after_context`, `S20-i0:C:z2:c1:after_context`, `S20-i0:D:z0:d0:after_context`, `S20-i0:D:z0:d1:after_context`, `S20-i0:D:z1:d0:after_context`, `S20-i0:D:z1:d0:after_context:instr_relevance`, `S20-i0:D:z1:d1:after_context`, `S20-i0:D:z1:d1:after_context:instr_relevance`, `S20-i0:D:z2:d0:after_context`, `S20-i0:D:z2:d1:after_context`, `S20-i0:N:d0:after_context`, `S20-i0:R:z0:r0:after_context`, `S20-i0:R:z0:r1:after_context`, `S20-i0:R:z1:r0:after_context`, `S20-i0:R:z1:r0:after_context:instr_relevance`, `S20-i0:R:z1:r1:after_context`, `S20-i0:R:z1:r1:after_context:instr_relevance`, `S20-i0:R:z2:r0:after_context`, `S20-i0:R:z2:r1:after_context`, `S20-i0:S:nongov_convertible_unit_same_magnitude`, `S20-i0:S:nongov_incompatible_unit_same_digits`, `S20-i0:S:nongov_same_unit_exact`, `S20-i0:S:nongov_same_unit_far`, `S20-i0:S:nongov_same_unit_moderate`, `S20-i0:S:nongov_same_unit_near_high_overlap`, `S20-i0:S:nongov_same_unit_near_low_overlap`, `S20-i0:S:relevant_edit`, `S20-i0:S:role_reversal`, `S20-i0:no_cue:instr_relevance`, `S26-i0:D:z0:d0:after_context`, `S26-i0:D:z0:d1:after_context`, `S26-i0:D:z1:d0:after_context`, `S26-i0:D:z1:d0:after_context:instr_relevance`, `S26-i0:D:z1:d1:after_context:instr_relevance`, `S26-i0:D:z2:d0:after_context`, `S26-i0:R:z1:r0:after_context:instr_relevance`, `S26-i0:R:z1:r1:after_context:instr_relevance`, `S26-i0:R:z2:r0:after_context`, `S26-i0:S:nongov_convertible_unit_same_magnitude`, `S26-i0:S:nongov_same_unit_exact`, `S26-i0:S:nongov_same_unit_near_high_overlap`, `S26-i0:S:role_reversal`, `S27-i0:C:z1:c0:after_context`, `S27-i0:C:z1:c1:after_context`, `S27-i0:D:z0:d1:after_context`, `S27-i0:D:z1:d0:after_context:instr_relevance`, `S27-i0:D:z1:d1:after_context:instr_relevance`, `S27-i0:D:z2:d0:after_context`, `S27-i0:D:z2:d1:after_context`, `S27-i0:N:d0:after_context`, `S27-i0:N:d1:after_context`, `S27-i0:R:z0:r0:after_context`, `S27-i0:S:nongov_incompatible_unit_same_digits`, `S27-i0:S:nongov_same_unit_exact`, `S30-i0:C:z0:c1:after_context`, `S30-i0:C:z1:c0:after_context`, `S30-i0:C:z2:c0:after_context`, `S30-i0:D:z0:d0:after_context`, `S30-i0:D:z0:d1:after_context`, `S30-i0:D:z1:d0:after_context`, `S30-i0:D:z1:d1:after_context`, `S30-i0:D:z1:d1:after_context:instr_relevance`, `S30-i0:D:z2:d0:after_context`, `S30-i0:D:z2:d1:after_context`, `S30-i0:N:d0:after_context`, `S30-i0:R:z0:r0:after_context`, `S30-i0:R:z0:r1:after_context`, `S30-i0:R:z1:r0:after_context`, `S30-i0:R:z1:r1:after_context`, `S30-i0:R:z2:r0:after_context`, `S30-i0:R:z2:r1:after_context`, `S30-i0:S:nongov_convertible_unit_same_magnitude`, `S30-i0:S:nongov_incompatible_unit_same_digits`, `S30-i0:S:nongov_same_unit_exact`, `S30-i0:S:nongov_same_unit_far`, `S30-i0:S:nongov_same_unit_moderate`, `S30-i0:S:numeric_metadata`, `S30-i0:S:relevant_edit`, `S30-i0:no_cue`, `S30-i0:no_cue:instr_relevance`, `S55-i0:C:z1:c0:after_context`, `S55-i0:N:d1:after_context`, `S55-i0:R:z1:r1:after_context`, `S55-i0:S:numeric_metadata`, `S55-i0:S:relevant_edit`, `S55-i0:no_cue`, `S72-i0:D:z0:d0:after_context`, `S72-i0:D:z0:d1:after_context`, `S72-i0:D:z1:d0:after_context`, `S72-i0:D:z1:d0:after_context:instr_relevance`, `S72-i0:D:z1:d1:after_context`, `S72-i0:D:z1:d1:after_context:instr_relevance`, `S72-i0:D:z2:d0:after_context`, `S72-i0:D:z2:d1:after_context`, `S72-i0:N:d0:after_context`, `S72-i0:N:d1:after_context`, `S72-i0:R:z0:r0:after_context`, `S72-i0:R:z0:r1:after_context`, `S72-i0:R:z1:r0:after_context`, `S72-i0:R:z1:r0:after_context:instr_relevance`, `S72-i0:R:z1:r1:after_context`, `S72-i0:R:z1:r1:after_context:instr_relevance`, `S72-i0:R:z2:r0:after_context`, `S72-i0:R:z2:r1:after_context`, `S72-i0:S:nongov_convertible_unit_same_magnitude`, `S72-i0:S:nongov_incompatible_unit_same_digits`, `S72-i0:S:nongov_same_unit_exact`, `S72-i0:S:nongov_same_unit_far`, `S72-i0:S:nongov_same_unit_moderate`, `S72-i0:S:nongov_same_unit_near_high_overlap`, `S72-i0:S:nongov_same_unit_near_low_overlap`, `S72-i0:S:nonnumeric_extra`, `S72-i0:S:numeric_metadata`, `S72-i0:S:relevant_edit`, `S72-i0:S:role_reversal`, `S72-i0:no_cue`, `S72-i0:no_cue:instr_relevance`, `S92-i0:C:z0:c0:after_context`, `S92-i0:C:z0:c1:after_context`, `S92-i0:C:z1:c0:after_context`, `S92-i0:C:z1:c1:after_context`, `S92-i0:C:z2:c0:after_context`, `S92-i0:C:z2:c1:after_context`, `S92-i0:D:z0:d0:after_context`, `S92-i0:D:z1:d0:after_context`, `S92-i0:D:z1:d0:after_context:instr_relevance`, `S92-i0:D:z1:d1:after_context`, `S92-i0:D:z1:d1:after_context:instr_relevance`, `S92-i0:D:z2:d0:after_context`, `S92-i0:D:z2:d1:after_context`, `S92-i0:K:z0:k0:after_context`, `S92-i0:K:z0:k1:after_context`, `S92-i0:K:z1:k0:after_context`, `S92-i0:K:z1:k1:after_context`, `S92-i0:N:d0:after_context`, `S92-i0:N:d1:after_context`, `S92-i0:R:z0:r0:after_context`, `S92-i0:R:z0:r1:after_context`, `S92-i0:R:z1:r0:after_context`, `S92-i0:R:z1:r0:after_context:instr_relevance`, `S92-i0:R:z1:r1:after_context`, `S92-i0:R:z1:r1:after_context:instr_relevance`, `S92-i0:R:z2:r0:after_context`, `S92-i0:R:z2:r1:after_context`, `S92-i0:S:nongov_convertible_unit_same_magnitude`, `S92-i0:S:nongov_incompatible_unit_same_digits`, `S92-i0:S:nongov_same_unit_exact`, `S92-i0:S:nongov_same_unit_far`, `S92-i0:S:nongov_same_unit_moderate`, `S92-i0:S:nongov_same_unit_near_high_overlap`, `S92-i0:S:nongov_same_unit_near_low_overlap`, `S92-i0:S:nonnumeric_extra`, `S92-i0:S:numeric_metadata`, `S92-i0:S:role_reversal`, `S92-i0:no_cue:instr_relevance`.

### 2. Certification (per cell)

| cell | R gold | base gold | misuse (any) | placebo | modal (n of valued) | modal is |
|---|---|---|---|---|---|---|
| `S01-i0:N:d0:after_context` (S01) | n/a | 0/20 (0.000) | no declared misuse values | n/a | 9.8 (6 of 20) | none |
| `S01-i0:N:d1:after_context` (S01) | n/a | 0/21 (0.000) | no declared misuse values | n/a | 9.8 (6 of 21) | none |
| `S01-i0:R:z0:r0:after_context` (S01) | 0/13 (0.000) | 0/13 (0.000) | n/a | n/a | 1.59 (2 of 13) | none |
| `S01-i0:R:z0:r1:after_context` (S01) | 0/15 (0.000) | 0/15 (0.000) | n/a | n/a | 0.146 (1 of 15, tie) | none |
| `S01-i0:D:z0:d0:after_context` (S01) | n/a | 0/14 (0.000) | 0/14 (0.000) [add 0/14 (0.000), digit_copy 0/14 (0.000), relevant_twin 0/14 (0.000), replace 0/14 (0.000), subtract 0/14 (0.000)] | n/a | 9.8 (3 of 14) | none |
| `S01-i0:D:z0:d1:after_context` (S01) | n/a | 0/19 (0.000) | 1/19 (0.053) [add 0/19 (0.000), digit_copy 0/19 (0.000), relevant_twin 0/19 (0.000), replace 0/19 (0.000), subtract 1/19 (0.053)] | n/a | 2.45 (4 of 19) | none |
| `S01-i0:R:z1:r0:after_context` (S01) | 0/15 (0.000) | 0/15 (0.000) | n/a | n/a | 5.39 (2 of 15) | none |
| `S01-i0:R:z1:r1:after_context` (S01) | 0/16 (0.000) | 0/16 (0.000) | n/a | n/a | -0.882 (1 of 16, tie) | none |
| `S01-i0:D:z1:d0:after_context` (S01) | n/a | 0/19 (0.000) | 0/19 (0.000) [add 0/19 (0.000), digit_copy 0/19 (0.000), relevant_twin 0/19 (0.000), replace 0/19 (0.000), subtract 0/19 (0.000)] | n/a | 2.45 (5 of 19) | none |
| `S01-i0:D:z1:d1:after_context` (S01) | n/a | 0/19 (0.000) | 0/19 (0.000) [add 0/19 (0.000), digit_copy 0/19 (0.000), relevant_twin 0/19 (0.000), replace 0/19 (0.000), subtract 0/19 (0.000)] | n/a | 2.45 (5 of 19) | none |
| `S01-i0:R:z2:r0:after_context` (S01) | 0/12 (0.000) | 0/12 (0.000) | n/a | n/a | 0.0072 (1 of 12, tie) | none |
| `S01-i0:R:z2:r1:after_context` (S01) | 0/20 (0.000) | 0/20 (0.000) | n/a | n/a | -0.738 (1 of 20, tie) | none |
| `S01-i0:D:z2:d0:after_context` (S01) | n/a | 0/13 (0.000) | 0/13 (0.000) [add 0/13 (0.000), digit_copy 0/13 (0.000), relevant_twin 0/13 (0.000), replace 0/13 (0.000), subtract 0/13 (0.000)] | n/a | 2.45 (2 of 13) | none |
| `S01-i0:D:z2:d1:after_context` (S01) | n/a | 0/14 (0.000) | 0/14 (0.000) [add 0/14 (0.000), digit_copy 0/14 (0.000), relevant_twin 0/14 (0.000), replace 0/14 (0.000), subtract 0/14 (0.000)] | n/a | 2.45 (2 of 14) | none |
| `S07-i0:N:d0:after_context` (S07) | n/a | 2/24 (0.083) | no declared misuse values | n/a | 6.607 (12 of 24) | gold (gold) |
| `S07-i0:N:d1:after_context` (S07) | n/a | 1/21 (0.048) | no declared misuse values | n/a | 6.607 (11 of 21) | gold (gold) |
| `S07-i0:R:z0:r0:after_context` (S07) | 0/21 (0.000) | 0/21 (0.000) | n/a | n/a | 12 (3 of 21) | none |
| `S07-i0:R:z0:r1:after_context` (S07) | 3/20 (0.150) | 0/20 (0.000) | n/a | n/a | 12 (4 of 20) | none |
| `S07-i0:D:z0:d0:after_context` (S07) | n/a | 0/22 (0.000) | 2/22 (0.091) [digit_copy 0/22 (0.000), relevant_twin 2/22 (0.091), replace 0/22 (0.000), subtract 0/22 (0.000)] | n/a | 6.607 (12 of 22) | gold (gold) |
| `S07-i0:D:z0:d1:after_context` (S07) | n/a | 0/21 (0.000) | 0/21 (0.000) [digit_copy 0/21 (0.000), relevant_twin 0/21 (0.000), replace 0/21 (0.000), subtract 0/21 (0.000)] | n/a | 6.607 (13 of 21) | gold (gold) |
| `S07-i0:R:z1:r0:after_context` (S07) | 0/20 (0.000) | 0/20 (0.000) | n/a | n/a | 4.56 (3 of 20, tie) | none |
| `S07-i0:R:z1:r1:after_context` (S07) | 0/21 (0.000) | 0/21 (0.000) | n/a | n/a | 12 (6 of 21) | none |
| `S07-i0:D:z1:d0:after_context` (S07) | n/a | 0/24 (0.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 6.607 (18 of 24) | gold (gold) |
| `S07-i0:D:z1:d1:after_context` (S07) | n/a | 0/22 (0.000) | 0/22 (0.000) [digit_copy 0/22 (0.000), relevant_twin 0/22 (0.000), replace 0/22 (0.000), subtract 0/22 (0.000)] | n/a | 6.607 (13 of 22) | gold (gold) |
| `S07-i0:R:z2:r0:after_context` (S07) | 4/22 (0.182) | 2/22 (0.091) | n/a | n/a | 3.4 (3 of 22) | gold (gold) |
| `S07-i0:R:z2:r1:after_context` (S07) | 2/23 (0.087) | 0/23 (0.000) | n/a | n/a | 3.404 (3 of 23) | gold (gold) |
| `S07-i0:D:z2:d0:after_context` (S07) | n/a | 2/21 (0.095) | 1/21 (0.048) [digit_copy 0/21 (0.000), relevant_twin 1/21 (0.048), replace 0/21 (0.000), subtract 0/21 (0.000)] | n/a | 6.607 (18 of 21) | gold (gold) |
| `S07-i0:D:z2:d1:after_context` (S07) | n/a | 0/23 (0.000) | 0/23 (0.000) [digit_copy 0/23 (0.000), relevant_twin 0/23 (0.000), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 6.607 (14 of 23) | gold (gold) |
| `S13-i0:N:d0:after_context` (S13) | n/a | 2/22 (0.091) | no declared misuse values | n/a | 1.794 (5 of 22) | gold (gold) |
| `S13-i0:N:d1:after_context` (S13) | n/a | 3/22 (0.136) | no declared misuse values | n/a | 1.79 (4 of 22) | gold (gold) |
| `S13-i0:R:z0:r0:after_context` (S13) | 10/23 (0.435) | 3/23 (0.130) | n/a | n/a | 2.11 (9 of 23) | gold (gold) |
| `S13-i0:R:z0:r1:after_context` (S13) | 9/22 (0.409) | 1/22 (0.045) | n/a | n/a | 2.11 (9 of 22) | gold (gold) |
| `S13-i0:D:z0:d0:after_context` (S13) | n/a | 1/21 (0.048) | 5/21 (0.238) [digit_copy 0/21 (0.000), relevant_twin 5/21 (0.238), replace 0/21 (0.000), subtract 0/21 (0.000)] | n/a | 2.11 (5 of 21) | foil (relevant_twin) |
| `S13-i0:D:z0:d1:after_context` (S13) | n/a | 2/21 (0.095) | 0/21 (0.000) [digit_copy 0/21 (0.000), relevant_twin 0/21 (0.000), replace 0/21 (0.000), subtract 0/21 (0.000)] | n/a | 1.794 (6 of 21) | gold (gold) |
| `S13-i0:R:z1:r0:after_context` (S13) | 2/21 (0.095) | 3/21 (0.143) | n/a | n/a | 2.291 (4 of 21) | gold (gold) |
| `S13-i0:R:z1:r1:after_context` (S13) | 2/22 (0.091) | 2/22 (0.091) | n/a | n/a | 2.291 (4 of 22, tie) | gold (gold) |
| `S13-i0:D:z1:d0:after_context` (S13) | n/a | 4/22 (0.182) | 2/22 (0.091) [digit_copy 0/22 (0.000), relevant_twin 1/22 (0.045), replace 1/22 (0.045), subtract 0/22 (0.000)] | n/a | 1.795 (4 of 22) | gold (gold) |
| `S13-i0:D:z1:d1:after_context` (S13) | n/a | 4/24 (0.167) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 1.79 (8 of 24) | gold (gold) |
| `S13-i0:R:z2:r0:after_context` (S13) | 1/24 (0.042) | 2/24 (0.083) | n/a | n/a | 2.464 (4 of 24) | gold (gold) |
| `S13-i0:R:z2:r1:after_context` (S13) | 6/23 (0.261) | 4/23 (0.174) | n/a | n/a | 2.46 (6 of 23) | gold (gold) |
| `S13-i0:D:z2:d0:after_context` (S13) | n/a | 2/22 (0.091) | 4/22 (0.182) [digit_copy 0/22 (0.000), relevant_twin 4/22 (0.182), replace 0/22 (0.000), subtract 0/22 (0.000)] | n/a | 1.79 (3 of 22, tie) | gold (gold) |
| `S13-i0:D:z2:d1:after_context` (S13) | n/a | 2/22 (0.091) | 0/22 (0.000) [digit_copy 0/22 (0.000), relevant_twin 0/22 (0.000), replace 0/22 (0.000), subtract 0/22 (0.000)] | n/a | 1.79 (3 of 22, tie) | gold (gold) |
| `S15-i0:N:d0:after_context` (S15) | n/a | 11/23 (0.478) | no declared misuse values | n/a | 36 (11 of 23) | gold (gold) |
| `S15-i0:N:d1:after_context` (S15) | n/a | 5/23 (0.217) | no declared misuse values | n/a | 162 (15 of 23) | none |
| `S15-i0:R:z0:r0:after_context` (S15) | 7/22 (0.318) | 2/22 (0.091) | n/a | n/a | 45.56 (7 of 22) | gold (gold) |
| `S15-i0:R:z0:r1:after_context` (S15) | 7/20 (0.350) | 1/20 (0.050) | n/a | n/a | 45.56 (7 of 20) | gold (gold) |
| `S15-i0:D:z0:d0:after_context` (S15) | n/a | 6/23 (0.261) | 1/23 (0.043) [digit_copy 0/23 (0.000), relevant_twin 1/23 (0.043), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 162 (11 of 23) | none |
| `S15-i0:D:z0:d1:after_context` (S15) | n/a | 5/21 (0.238) | 0/21 (0.000) [digit_copy 0/21 (0.000), relevant_twin 0/21 (0.000), replace 0/21 (0.000), subtract 0/21 (0.000)] | n/a | 162 (12 of 21) | none |
| `S15-i0:R:z1:r0:after_context` (S15) | 7/23 (0.304) | 2/23 (0.087) | n/a | n/a | 56.25 (7 of 23) | gold (gold) |
| `S15-i0:R:z1:r1:after_context` (S15) | 9/23 (0.391) | 1/23 (0.043) | n/a | n/a | 56.25 (9 of 23) | gold (gold) |
| `S15-i0:D:z1:d0:after_context` (S15) | n/a | 3/23 (0.130) | 3/23 (0.130) [digit_copy 0/23 (0.000), relevant_twin 3/23 (0.130), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 162 (15 of 23) | none |
| `S15-i0:D:z1:d1:after_context` (S15) | n/a | 9/24 (0.375) | 1/24 (0.042) [digit_copy 0/24 (0.000), relevant_twin 1/24 (0.042), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 162 (11 of 24) | none |
| `S15-i0:R:z2:r0:after_context` (S15) | 13/24 (0.542) | 2/24 (0.083) | n/a | n/a | 64 (13 of 24) | gold (gold) |
| `S15-i0:R:z2:r1:after_context` (S15) | 7/23 (0.304) | 0/23 (0.000) | n/a | n/a | 288 (11 of 23) | none |
| `S15-i0:D:z2:d0:after_context` (S15) | n/a | 4/22 (0.182) | 1/22 (0.045) [digit_copy 0/22 (0.000), relevant_twin 1/22 (0.045), replace 0/22 (0.000), subtract 0/22 (0.000)] | n/a | 162 (15 of 22) | none |
| `S15-i0:D:z2:d1:after_context` (S15) | n/a | 11/22 (0.500) | 0/22 (0.000) [digit_copy 0/22 (0.000), relevant_twin 0/22 (0.000), replace 0/22 (0.000), subtract 0/22 (0.000)] | n/a | 36 (11 of 22) | gold (gold) |
| `S20-i0:N:d0:after_context` (S20) | n/a | 14/16 (0.875) | no declared misuse values | n/a | 17.14 (13 of 16) | gold (gold) |
| `S20-i0:N:d1:after_context` (S20) | n/a | 21/23 (0.913) | no declared misuse values | n/a | 17.14 (21 of 23) | gold (gold) |
| `S20-i0:R:z0:r0:after_context` (S20) | 8/18 (0.444) | 1/18 (0.056) | n/a | n/a | 16.24 (7 of 18) | gold (gold) |
| `S20-i0:R:z0:r1:after_context` (S20) | 9/17 (0.529) | 1/17 (0.059) | n/a | n/a | 16.24 (7 of 17) | gold (gold) |
| `S20-i0:D:z0:d0:after_context` (S20) | n/a | 5/16 (0.312) | 3/16 (0.188) [add 0/16 (0.000), copy 0/16 (0.000), relevant_twin 2/16 (0.125), replace 0/16 (0.000), subtract 1/16 (0.062)] | n/a | 17.14 (5 of 16) | gold (gold) |
| `S20-i0:D:z0:d1:after_context` (S20) | n/a | 3/17 (0.176) | 12/17 (0.706) [add 0/17 (0.000), copy 0/17 (0.000), relevant_twin 9/17 (0.529), replace 0/17 (0.000), subtract 3/17 (0.176)] | n/a | 16.24 (5 of 17) | foil (relevant_twin) |
| `S20-i0:R:z1:r0:after_context` (S20) | 5/11 (0.455) | 1/11 (0.091) | n/a | n/a | 15.13 (4 of 11) | gold (gold) |
| `S20-i0:R:z1:r1:after_context` (S20) | 7/17 (0.412) | 2/17 (0.118) | n/a | n/a | 15.13 (6 of 17) | gold (gold) |
| `S20-i0:D:z1:d0:after_context` (S20) | n/a | 3/15 (0.200) | 8/15 (0.533) [add 0/15 (0.000), copy 0/15 (0.000), relevant_twin 7/15 (0.467), replace 0/15 (0.000), subtract 1/15 (0.067)] | n/a | 15.13 (6 of 15) | foil (relevant_twin) |
| `S20-i0:D:z1:d1:after_context` (S20) | n/a | 5/17 (0.294) | 8/17 (0.471) [add 0/17 (0.000), copy 0/17 (0.000), relevant_twin 3/17 (0.176), replace 0/17 (0.000), subtract 5/17 (0.294)] | n/a | 17.14 (5 of 17, tie) | gold (gold) |
| `S20-i0:R:z2:r0:after_context` (S20) | 12/18 (0.667) | 0/18 (0.000) | n/a | n/a | 14.48 (12 of 18) | gold (gold) |
| `S20-i0:R:z2:r1:after_context` (S20) | 8/17 (0.471) | 1/17 (0.059) | n/a | n/a | 14.48 (8 of 17) | gold (gold) |
| `S20-i0:D:z2:d0:after_context` (S20) | n/a | 0/13 (0.000) | 7/13 (0.538) [add 0/13 (0.000), copy 0/13 (0.000), relevant_twin 5/13 (0.385), replace 2/13 (0.154), subtract 0/13 (0.000)] | n/a | 14.48 (4 of 13) | foil (relevant_twin) |
| `S20-i0:D:z2:d1:after_context` (S20) | n/a | 2/15 (0.133) | 9/15 (0.600) [add 0/15 (0.000), copy 0/15 (0.000), relevant_twin 9/15 (0.600), replace 0/15 (0.000), subtract 0/15 (0.000)] | n/a | 14.48 (8 of 15) | foil (relevant_twin) |
| `S26-i0:N:d0:after_context` (S26) | n/a | 1/23 (0.043) | no declared misuse values | n/a | 25.84 (3 of 23) | none |
| `S26-i0:N:d1:after_context` (S26) | n/a | 1/24 (0.042) | no declared misuse values | n/a | 25.5 (3 of 24) | gold (gold) |
| `S26-i0:R:z0:r0:after_context` (S26) | 0/23 (0.000) | 0/23 (0.000) | n/a | n/a | 28.9 (4 of 23) | none |
| `S26-i0:R:z0:r1:after_context` (S26) | 0/22 (0.000) | 0/22 (0.000) | n/a | n/a | 28.87 (4 of 22) | none |
| `S26-i0:D:z0:d0:after_context` (S26) | n/a | 0/19 (0.000) | 0/19 (0.000) [add 0/19 (0.000), copy 0/19 (0.000), relevant_twin 0/19 (0.000), replace 0/19 (0.000), subtract 0/19 (0.000)] | n/a | 22 (2 of 19, tie) | none |
| `S26-i0:D:z0:d1:after_context` (S26) | n/a | 0/18 (0.000) | 1/18 (0.056) [add 0/18 (0.000), copy 0/18 (0.000), relevant_twin 1/18 (0.056), replace 0/18 (0.000), subtract 0/18 (0.000)] | n/a | 25.84 (2 of 18, tie) | none |
| `S26-i0:R:z1:r0:after_context` (S26) | 0/22 (0.000) | 1/22 (0.045) | n/a | n/a | 40 (2 of 22, tie) | none |
| `S26-i0:R:z1:r1:after_context` (S26) | 2/24 (0.083) | 0/24 (0.000) | n/a | n/a | 31.3 (5 of 24) | gold (gold) |
| `S26-i0:D:z1:d0:after_context` (S26) | n/a | 0/16 (0.000) | 2/16 (0.125) [add 0/16 (0.000), copy 1/16 (0.062), relevant_twin 1/16 (0.062), replace 0/16 (0.000), subtract 0/16 (0.000)] | n/a | 40 (2 of 16) | none |
| `S26-i0:D:z1:d1:after_context` (S26) | n/a | 0/23 (0.000) | 10/23 (0.435) [add 0/23 (0.000), copy 0/23 (0.000), relevant_twin 10/23 (0.435), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 31.3 (6 of 23) | foil (relevant_twin) |
| `S26-i0:R:z2:r0:after_context` (S26) | 0/22 (0.000) | 3/22 (0.136) | n/a | n/a | 32 (6 of 22) | none |
| `S26-i0:R:z2:r1:after_context` (S26) | 0/24 (0.000) | 0/24 (0.000) | n/a | n/a | 32 (8 of 24) | none |
| `S26-i0:D:z2:d0:after_context` (S26) | n/a | 3/21 (0.143) | 1/21 (0.048) [add 1/21 (0.048), copy 0/21 (0.000), relevant_twin 0/21 (0.000), replace 0/21 (0.000), subtract 0/21 (0.000)] | n/a | 25.4 (3 of 21) | gold (gold) |
| `S26-i0:D:z2:d1:after_context` (S26) | n/a | 0/21 (0.000) | 6/21 (0.286) [add 6/21 (0.286), copy 0/21 (0.000), relevant_twin 0/21 (0.000), replace 0/21 (0.000), subtract 0/21 (0.000)] | n/a | 32 (5 of 21) | none |
| `S27-i0:N:d0:after_context` (S27) | n/a | 17/20 (0.850) | no declared misuse values | n/a | 218.6 (17 of 20) | gold (gold) |
| `S27-i0:N:d1:after_context` (S27) | n/a | 19/21 (0.905) | no declared misuse values | n/a | 218.6 (18 of 21) | gold (gold) |
| `S27-i0:R:z0:r0:after_context` (S27) | 13/20 (0.650) | 0/20 (0.000) | n/a | n/a | 226.1 (13 of 20) | gold (gold) |
| `S27-i0:R:z0:r1:after_context` (S27) | 15/24 (0.625) | 5/24 (0.208) | n/a | n/a | 226.1 (15 of 24) | gold (gold) |
| `S27-i0:D:z0:d0:after_context` (S27) | n/a | 8/22 (0.364) | 11/22 (0.500) [copy 0/22 (0.000), relevant_twin 9/22 (0.409), replace 2/22 (0.091), subtract 0/22 (0.000)] | n/a | 226.1 (9 of 22) | foil (relevant_twin) |
| `S27-i0:D:z0:d1:after_context` (S27) | n/a | 5/20 (0.250) | 14/20 (0.700) [copy 0/20 (0.000), relevant_twin 12/20 (0.600), replace 1/20 (0.050), subtract 1/20 (0.050)] | n/a | 226.1 (8 of 20) | foil (relevant_twin) |
| `S27-i0:R:z1:r0:after_context` (S27) | 18/23 (0.783) | 0/23 (0.000) | n/a | n/a | 233.6 (18 of 23) | gold (gold) |
| `S27-i0:R:z1:r1:after_context` (S27) | 17/23 (0.739) | 4/23 (0.174) | n/a | n/a | 233.6 (17 of 23) | gold (gold) |
| `S27-i0:D:z1:d0:after_context` (S27) | n/a | 6/24 (0.250) | 13/24 (0.542) [copy 0/24 (0.000), relevant_twin 12/24 (0.500), replace 1/24 (0.042), subtract 0/24 (0.000)] | n/a | 233.6 (12 of 24) | foil (relevant_twin) |
| `S27-i0:D:z1:d1:after_context` (S27) | n/a | 1/18 (0.056) | 17/18 (0.944) [copy 0/18 (0.000), relevant_twin 16/18 (0.889), replace 1/18 (0.056), subtract 0/18 (0.000)] | n/a | 233.6 (16 of 18) | foil (relevant_twin) |
| `S27-i0:R:z2:r0:after_context` (S27) | 19/22 (0.864) | 0/22 (0.000) | n/a | n/a | 253.6 (19 of 22) | gold (gold) |
| `S27-i0:R:z2:r1:after_context` (S27) | 21/24 (0.875) | 0/24 (0.000) | n/a | n/a | 253.6 (21 of 24) | gold (gold) |
| `S27-i0:D:z2:d0:after_context` (S27) | n/a | 3/21 (0.143) | 17/21 (0.810) [copy 0/21 (0.000), relevant_twin 16/21 (0.762), replace 1/21 (0.048), subtract 0/21 (0.000)] | n/a | 253.6 (16 of 21) | foil (relevant_twin) |
| `S27-i0:D:z2:d1:after_context` (S27) | n/a | 2/21 (0.095) | 17/21 (0.810) [copy 0/21 (0.000), relevant_twin 15/21 (0.714), replace 1/21 (0.048), subtract 1/21 (0.048)] | n/a | 253.6 (15 of 21) | foil (relevant_twin) |
| `S30-i0:N:d0:after_context` (S30) | n/a | 15/22 (0.682) | no declared misuse values | n/a | 223.2 (15 of 22) | gold (gold) |
| `S30-i0:N:d1:after_context` (S30) | n/a | 15/23 (0.652) | no declared misuse values | n/a | 223.2 (14 of 23) | gold (gold) |
| `S30-i0:R:z0:r0:after_context` (S30) | 0/21 (0.000) | 0/21 (0.000) | n/a | n/a | 312 (5 of 21) | gold (gold) |
| `S30-i0:R:z0:r1:after_context` (S30) | 0/22 (0.000) | 1/22 (0.045) | n/a | n/a | 314 (2 of 22) | gold (gold) |
| `S30-i0:D:z0:d0:after_context` (S30) | n/a | 2/18 (0.111) | 8/18 (0.444) [digit_copy 0/18 (0.000), relevant_twin 3/18 (0.167), replace 4/18 (0.222), subtract 1/18 (0.056)] | n/a | 223.2 (3 of 18) | gold (gold) |
| `S30-i0:D:z0:d1:after_context` (S30) | n/a | 2/21 (0.095) | 13/21 (0.619) [digit_copy 0/21 (0.000), relevant_twin 13/21 (0.619), replace 0/21 (0.000), subtract 0/21 (0.000)] | n/a | 223.2 (2 of 21, tie) | gold (gold) |
| `S30-i0:R:z1:r0:after_context` (S30) | 0/19 (0.000) | 0/19 (0.000) | n/a | n/a | 378 (2 of 19, tie) | gold (gold) |
| `S30-i0:R:z1:r1:after_context` (S30) | 1/22 (0.045) | 0/22 (0.000) | n/a | n/a | 376 (2 of 22, tie) | none |
| `S30-i0:D:z1:d0:after_context` (S30) | n/a | 1/19 (0.053) | 6/19 (0.316) [digit_copy 0/19 (0.000), relevant_twin 2/19 (0.105), replace 4/19 (0.211), subtract 0/19 (0.000)] | n/a | 223 (2 of 19) | gold (gold) |
| `S30-i0:D:z1:d1:after_context` (S30) | n/a | 0/20 (0.000) | 11/20 (0.550) [digit_copy 0/20 (0.000), relevant_twin 11/20 (0.550), replace 0/20 (0.000), subtract 0/20 (0.000)] | n/a | 380 (4 of 20) | foil (relevant_twin) |
| `S30-i0:R:z2:r0:after_context` (S30) | 0/21 (0.000) | 0/21 (0.000) | n/a | n/a | 513.1 (2 of 21, tie) | gold (gold) |
| `S30-i0:R:z2:r1:after_context` (S30) | 1/21 (0.048) | 0/21 (0.000) | n/a | n/a | 513 (3 of 21) | gold (gold) |
| `S30-i0:D:z2:d0:after_context` (S30) | n/a | 3/19 (0.158) | 2/19 (0.105) [digit_copy 0/19 (0.000), relevant_twin 2/19 (0.105), replace 0/19 (0.000), subtract 0/19 (0.000)] | n/a | 223 (2 of 19, tie) | gold (gold) |
| `S30-i0:D:z2:d1:after_context` (S30) | n/a | 4/19 (0.211) | 6/19 (0.316) [digit_copy 0/19 (0.000), relevant_twin 6/19 (0.316), replace 0/19 (0.000), subtract 0/19 (0.000)] | n/a | 223.2 (3 of 19) | gold (gold) |
| `S55-i0:N:d0:after_context` (S55) | n/a | 0/24 (0.000) | no declared misuse values | n/a | 43 (2 of 24) | none |
| `S55-i0:N:d1:after_context` (S55) | n/a | 0/20 (0.000) | no declared misuse values | n/a | 1379 (2 of 20) | none |
| `S55-i0:R:z0:r0:after_context` (S55) | 0/21 (0.000) | 0/21 (0.000) | n/a | n/a | 93.38 (2 of 20) | none |
| `S55-i0:R:z0:r1:after_context` (S55) | 0/24 (0.000) | 0/24 (0.000) | n/a | n/a | 93.37 (4 of 24) | none |
| `S55-i0:D:z0:d0:after_context` (S55) | n/a | 0/23 (0.000) | 0/23 (0.000) [digit_copy 0/23 (0.000), relevant_twin 0/23 (0.000), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 86.23 (2 of 21, tie) | none |
| `S55-i0:D:z0:d1:after_context` (S55) | n/a | 0/22 (0.000) | 2/22 (0.091) [digit_copy 0/22 (0.000), relevant_twin 2/22 (0.091), replace 0/22 (0.000), subtract 0/22 (0.000)] | n/a | 0.0019 (1 of 22, tie) | none |
| `S55-i0:R:z1:r0:after_context` (S55) | 0/24 (0.000) | 0/24 (0.000) | n/a | n/a | 314.9 (3 of 24) | none |
| `S55-i0:R:z1:r1:after_context` (S55) | 0/22 (0.000) | 0/22 (0.000) | n/a | n/a | 99.83 (2 of 21, tie) | foil (digit_copy) |
| `S55-i0:D:z1:d0:after_context` (S55) | n/a | 0/22 (0.000) | 1/22 (0.045) [digit_copy 1/22 (0.045), relevant_twin 0/22 (0.000), replace 0/22 (0.000), subtract 0/22 (0.000)] | n/a | 86.45 (2 of 22, tie) | none |
| `S55-i0:D:z1:d1:after_context` (S55) | n/a | 0/23 (0.000) | 3/23 (0.130) [digit_copy 2/23 (0.087), relevant_twin 1/23 (0.043), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 43.21 (1 of 22, tie) | none |
| `S55-i0:R:z2:r0:after_context` (S55) | 0/22 (0.000) | 0/22 (0.000) | n/a | n/a | 3515 (2 of 21) | none |
| `S55-i0:R:z2:r1:after_context` (S55) | 2/23 (0.087) | 0/23 (0.000) | n/a | n/a | 1766 (3 of 23) | gold (gold) |
| `S55-i0:D:z2:d0:after_context` (S55) | n/a | 0/24 (0.000) | 1/24 (0.042) [digit_copy 0/24 (0.000), relevant_twin 1/24 (0.042), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 86.32 (2 of 24) | none |
| `S55-i0:D:z2:d1:after_context` (S55) | n/a | 0/20 (0.000) | 0/20 (0.000) [digit_copy 0/20 (0.000), relevant_twin 0/20 (0.000), replace 0/20 (0.000), subtract 0/20 (0.000)] | n/a | 21.66 (1 of 20, tie) | none |
| `S72-i0:N:d0:after_context` (S72) | n/a | 0/17 (0.000) | no declared misuse values | n/a | 31.55 (2 of 16) | none |
| `S72-i0:N:d1:after_context` (S72) | n/a | 0/16 (0.000) | no declared misuse values | n/a | 2.02 (1 of 16, tie) | none |
| `S72-i0:R:z0:r0:after_context` (S72) | 0/16 (0.000) | 0/16 (0.000) | n/a | n/a | 2.183 (1 of 16, tie) | none |
| `S72-i0:R:z0:r1:after_context` (S72) | 0/15 (0.000) | 0/15 (0.000) | n/a | n/a | 0.852 (1 of 14, tie) | none |
| `S72-i0:D:z0:d0:after_context` (S72) | n/a | 0/18 (0.000) | 0/18 (0.000) [digit_copy 0/18 (0.000), relevant_twin 0/18 (0.000), replace 0/18 (0.000), subtract 0/18 (0.000)] | n/a | 4.48 (1 of 18, tie) | none |
| `S72-i0:D:z0:d1:after_context` (S72) | n/a | 0/15 (0.000) | 0/15 (0.000) [digit_copy 0/15 (0.000), relevant_twin 0/15 (0.000), replace 0/15 (0.000), subtract 0/15 (0.000)] | n/a | 0.287 (1 of 14, tie) | none |
| `S72-i0:R:z1:r0:after_context` (S72) | 0/17 (0.000) | 0/17 (0.000) | n/a | n/a | 250 (2 of 17) | none |
| `S72-i0:R:z1:r1:after_context` (S72) | 0/13 (0.000) | 0/13 (0.000) | n/a | n/a | 3.45 (1 of 13, tie) | none |
| `S72-i0:D:z1:d0:after_context` (S72) | n/a | 0/16 (0.000) | 0/16 (0.000) [digit_copy 0/16 (0.000), relevant_twin 0/16 (0.000), replace 0/16 (0.000), subtract 0/16 (0.000)] | n/a | 0.07903 (1 of 16, tie) | none |
| `S72-i0:D:z1:d1:after_context` (S72) | n/a | 0/10 (0.000) | 0/10 (0.000) [digit_copy 0/10 (0.000), relevant_twin 0/10 (0.000), replace 0/10 (0.000), subtract 0/10 (0.000)] | n/a | 7.482 (1 of 10, tie) | none |
| `S72-i0:R:z2:r0:after_context` (S72) | 0/14 (0.000) | 0/14 (0.000) | n/a | n/a | 1.162 (1 of 14, tie) | none |
| `S72-i0:R:z2:r1:after_context` (S72) | 0/14 (0.000) | 0/14 (0.000) | n/a | n/a | 2.025 (1 of 14, tie) | none |
| `S72-i0:D:z2:d0:after_context` (S72) | n/a | 0/17 (0.000) | 0/17 (0.000) [digit_copy 0/17 (0.000), relevant_twin 0/17 (0.000), replace 0/17 (0.000)] | n/a | 0.825 (1 of 16, tie) | none |
| `S72-i0:D:z2:d1:after_context` (S72) | n/a | 0/14 (0.000) | 0/14 (0.000) [digit_copy 0/14 (0.000), relevant_twin 0/14 (0.000), replace 0/14 (0.000)] | n/a | 0.203 (1 of 14, tie) | none |
| `S92-i0:N:d0:after_context` (S92) | n/a | 9/14 (0.643) | no declared misuse values | n/a | 3.92 (9 of 14) | gold (gold) |
| `S92-i0:N:d1:after_context` (S92) | n/a | 7/15 (0.467) | no declared misuse values | n/a | 3.92 (7 of 15) | gold (gold) |
| `S92-i0:R:z0:r0:after_context` (S92) | 4/20 (0.200) | 3/20 (0.150) | n/a | n/a | 5.39 (4 of 20) | gold (gold) |
| `S92-i0:R:z0:r1:after_context` (S92) | 1/17 (0.059) | 1/17 (0.059) | n/a | n/a | 5.41 (2 of 17, tie) | gold (gold) |
| `S92-i0:D:z0:d0:after_context` (S92) | n/a | 6/19 (0.316) | 3/19 (0.158) [add 1/19 (0.053), digit_copy 0/19 (0.000), relevant_twin 2/19 (0.105), replace 0/19 (0.000), subtract 1/19 (0.053)] | n/a | 3.92 (6 of 19) | gold (gold) |
| `S92-i0:D:z0:d1:after_context` (S92) | n/a | 5/18 (0.278) | 5/18 (0.278) [add 0/18 (0.000), digit_copy 0/18 (0.000), relevant_twin 5/18 (0.278), replace 0/18 (0.000), subtract 0/18 (0.000)] | n/a | 3.92 (5 of 18) | gold (gold) |
| `S92-i0:R:z1:r0:after_context` (S92) | 2/12 (0.167) | 0/12 (0.000) | n/a | n/a | 3.43 (2 of 12, tie) | none |
| `S92-i0:R:z1:r1:after_context` (S92) | 5/13 (0.385) | 4/13 (0.308) | n/a | n/a | 6.37 (5 of 13) | gold (gold) |
| `S92-i0:D:z1:d0:after_context` (S92) | n/a | 4/14 (0.286) | 1/14 (0.071) [add 0/14 (0.000), digit_copy 0/14 (0.000), relevant_twin 1/14 (0.071), replace 0/14 (0.000), subtract 0/14 (0.000)] | n/a | 3.92 (4 of 14) | gold (gold) |
| `S92-i0:D:z1:d1:after_context` (S92) | n/a | 2/17 (0.118) | 6/17 (0.353) [add 0/17 (0.000), digit_copy 0/17 (0.000), relevant_twin 6/17 (0.353), replace 0/17 (0.000), subtract 0/17 (0.000)] | n/a | 6.37 (6 of 17) | foil (relevant_twin) |
| `S92-i0:R:z2:r0:after_context` (S92) | 1/19 (0.053) | 2/19 (0.105) | n/a | n/a | 7.34 (8 of 19) | gold (gold) |
| `S92-i0:R:z2:r1:after_context` (S92) | 0/20 (0.000) | 2/20 (0.100) | n/a | n/a | 7.34 (8 of 20) | gold (gold) |
| `S92-i0:D:z2:d0:after_context` (S92) | n/a | 6/14 (0.429) | 0/14 (0.000) [add 0/14 (0.000), digit_copy 0/14 (0.000), relevant_twin 0/14 (0.000), replace 0/14 (0.000), subtract 0/14 (0.000)] | n/a | 3.92 (6 of 14) | gold (gold) |
| `S92-i0:D:z2:d1:after_context` (S92) | n/a | 5/14 (0.357) | 3/14 (0.214) [add 0/14 (0.000), digit_copy 0/14 (0.000), relevant_twin 3/14 (0.214), replace 0/14 (0.000), subtract 0/14 (0.000)] | n/a | 3.92 (5 of 14) | gold (gold) |

### 3. Ambiguity (rule B on tracking share, phrasing 0 vs 1)

| structure | R state (diff, 95% CI) | D state (diff, 95% CI) |
|---|---|---|
| S01 | AGREE (+0.000, [-0.051, +0.051]; 0/72 (0.000) vs 0/72 (0.000)) | AGREE (+0.000, [-0.051, +0.051]; 0/72 (0.000) vs 0/72 (0.000)) |
| S07 | AGREE (-0.014, [-0.104, +0.074]; 4/72 (0.056) vs 5/72 (0.069)) | AGREE (+0.028, [-0.027, +0.096]; 2/72 (0.028) vs 0/72 (0.000)) |
| S13 | UNRESOLVED (-0.056, [-0.187, +0.078]; 13/72 (0.181) vs 17/72 (0.236)) | UNRESOLVED (-0.014, [-0.119, +0.091]; 7/72 (0.097) vs 8/72 (0.111)) |
| S15 | UNRESOLVED (+0.056, [-0.098, +0.206]; 27/72 (0.375) vs 23/72 (0.319)) | DISAGREE (-0.167, [-0.302, -0.022]; 13/72 (0.181) vs 25/72 (0.347)) |
| S20 | UNRESOLVED (+0.014, [-0.138, +0.165]; 25/72 (0.347) vs 24/72 (0.333)) | UNRESOLVED (-0.028, [-0.140, +0.084]; 8/72 (0.111) vs 10/72 (0.139)) |
| S26 | AGREE (-0.028, [-0.096, +0.027]; 0/72 (0.000) vs 2/72 (0.028)) | AGREE (+0.042, [-0.016, +0.115]; 3/72 (0.042) vs 0/72 (0.000)) |
| S27 | UNRESOLVED (-0.042, [-0.186, +0.105]; 50/72 (0.694) vs 53/72 (0.736)) | DISAGREE (+0.125, [+0.000, +0.247]; 17/72 (0.236) vs 8/72 (0.111)) |
| S30 | AGREE (-0.028, [-0.096, +0.027]; 0/72 (0.000) vs 2/72 (0.028)) | AGREE (+0.000, [-0.098, +0.098]; 6/72 (0.083) vs 6/72 (0.083)) |
| S55 | AGREE (-0.028, [-0.096, +0.027]; 0/72 (0.000) vs 2/72 (0.028)) | AGREE (+0.000, [-0.051, +0.051]; 0/72 (0.000) vs 0/72 (0.000)) |
| S72 | AGREE (+0.000, [-0.051, +0.051]; 0/72 (0.000) vs 0/72 (0.000)) | AGREE (+0.000, [-0.051, +0.051]; 0/72 (0.000) vs 0/72 (0.000)) |
| S92 | AGREE (+0.014, [-0.086, +0.114]; 7/72 (0.097) vs 6/72 (0.083)) | UNRESOLVED (+0.056, [-0.075, +0.184]; 16/72 (0.222) vs 12/72 (0.167)) |

Cross-structure rule B (library `phrasing_difference_agreement` on per-structure differences): R: AGREE (J=11); D: AGREE (J=11).
WORDING_DEPENDENT structures (DISAGREE on R or D twins): S15, S27.

Medium-flag cells (reported apart):

* S26 R:r1 cell `S26-i0:R:z0:r1:after_context`: R gold 0/22 (0.000); base gold 0/22 (0.000); modal 28.87.
* S26 R:r1 cell `S26-i0:R:z1:r1:after_context`: R gold 2/24 (0.083); base gold 0/24 (0.000); modal 31.3.
* S26 R:r1 cell `S26-i0:R:z2:r1:after_context`: R gold 0/24 (0.000); base gold 0/24 (0.000); modal 32.0.
* S55 R:r1 cell `S55-i0:R:z0:r1:after_context`: R gold 0/24 (0.000); base gold 0/24 (0.000); modal 93.37.
* S55 R:r1 cell `S55-i0:R:z1:r1:after_context`: R gold 0/22 (0.000); base gold 0/22 (0.000); modal 99.83.
* S55 R:r1 cell `S55-i0:R:z2:r1:after_context`: R gold 2/23 (0.087); base gold 0/23 (0.000); modal 1766.0.

### 4. Feasibility

| structure | no-cue correct, of all samples | of COMPLETE | band [0.30, 0.85] | T_R of all | T_R of COMPLETE | budget exhausted | format failure | tokens mean / max |
|---|---|---|---|---|---|---|---|---|
| S01 | 0/24 (0.000) | 0/17 (0.000) | out of band | 0/144 (0.000) | 0/91 (0.000) | 189/1032 (0.183) | 123/1032 (0.119) | 1368 / 4096 |
| S07 | 0/24 (0.000) | 0/24 (0.000) | out of band | 9/144 (0.062) | 9/127 (0.071) | 56/984 (0.057) | 22/984 (0.022) | 631 / 4096 |
| S13 | 3/24 (0.125) | 3/22 (0.136) | out of band | 30/144 (0.208) | 30/135 (0.222) | 12/888 (0.014) | 41/888 (0.046) | 302 / 4096 |
| S15 | 5/24 (0.208) | 5/24 (0.208) | out of band | 50/144 (0.347) | 50/135 (0.370) | 11/888 (0.012) | 28/888 (0.032) | 482 / 4096 |
| S20 | 18/24 (0.750) | 18/23 (0.783) | in band | 49/144 (0.340) | 49/98 (0.500) | 58/888 (0.065) | 169/888 (0.190) | 611 / 4096 |
| S26 | 1/24 (0.042) | 1/24 (0.042) | out of band | 2/144 (0.014) | 2/137 (0.015) | 16/744 (0.022) | 54/744 (0.073) | 482 / 4096 |
| S27 | 22/24 (0.917) | 22/23 (0.957) | out of band | 103/144 (0.715) | 103/136 (0.757) | 37/888 (0.042) | 36/888 (0.041) | 528 / 4096 |
| S30 | 12/24 (0.500) | 12/20 (0.600) | in band | 2/144 (0.014) | 2/126 (0.016) | 11/888 (0.012) | 97/888 (0.109) | 387 / 4096 |
| S55 | 0/24 (0.000) | 0/21 (0.000) | out of band | 2/144 (0.014) | 2/136 (0.015) | 43/888 (0.048) | 23/888 (0.026) | 550 / 4096 |
| S72 | 0/24 (0.000) | 0/13 (0.000) | out of band | 0/144 (0.000) | 0/89 (0.000) | 116/744 (0.156) | 155/744 (0.208) | 1300 / 4096 |
| S92 | 14/24 (0.583) | 14/20 (0.700) | in band | 13/144 (0.090) | 13/101 (0.129) | 169/1032 (0.164) | 165/1032 (0.160) | 1144 / 4096 |
| ALL | 75/264 (0.284) | 75/231 (0.325) | out of band | 260/1584 (0.164) | 260/1311 (0.198) | 718/9864 (0.073) | 913/9864 (0.093) | 718 / 4096 |

## Model `s15_g2pilot_m0v25_qwen3_8b_nothink`

Records 9864; cells 411, of which without records 0.

### 1. Grading (all structures)

| stratum | cells (missing) | O3 statuses | COMPLETE | declared | convertible | rel1pct | gap rel1pct-declared | unparsed among COMPLETE |
|---|---|---|---|---|---|---|---|---|
| none | 11 (0) | COMPLETE 259, UNPARSEABLE 5 | 259 | 239/259 (0.923) | 239/259 (0.923) | 244/259 (0.942) | 5/259 (0.019) | 0/259 (0.000) |
| R | 66 (0) | BUDGET_EXHAUSTED 5, COMPLETE 1563, UNPARSEABLE 16 | 1563 | 930/1563 (0.595) | 930/1563 (0.595) | 1042/1563 (0.667) | 112/1563 (0.072) | 0/1563 (0.000) |
| D | 66 (0) | BUDGET_EXHAUSTED 3, COMPLETE 1554, MULTIPLE_CANDIDATES 1, UNPARSEABLE 26 | 1554 | 1215/1554 (0.782) | 1215/1554 (0.782) | 1262/1554 (0.812) | 47/1554 (0.030) | 0/1554 (0.000) |
| N | 22 (0) | BUDGET_EXHAUSTED 1, COMPLETE 513, UNPARSEABLE 14 | 513 | 459/513 (0.895) | 459/513 (0.895) | 472/513 (0.920) | 13/513 (0.025) | 0/513 (0.000) |
| C | 42 (0) | BUDGET_EXHAUSTED 2, COMPLETE 978, UNPARSEABLE 28 | 978 | 876/978 (0.896) | 876/978 (0.896) | 887/978 (0.907) | 11/978 (0.011) | 0/978 (0.000) |
| K | 24 (0) | COMPLETE 570, UNPARSEABLE 6 | 570 | 458/570 (0.804) | 458/570 (0.804) | 490/570 (0.860) | 32/570 (0.056) | 0/570 (0.000) |
| K_out | 4 (0) | COMPLETE 96 | 96 | 6/96 (0.062) | 6/96 (0.062) | 6/96 (0.062) | 0/96 (0.000) | 0/96 (0.000) |
| support | 176 (0) | BUDGET_EXHAUSTED 5, COMPLETE 4091, MULTIPLE_CANDIDATES 1, UNPARSEABLE 127 | 4091 | 3346/4091 (0.818) | 3346/4091 (0.818) | 3596/4091 (0.879) | 250/4091 (0.061) | 0/4091 (0.000) |

Per structure, all strata (correct among COMPLETE):

| structure | records | COMPLETE | declared | convertible | rel1pct |
|---|---|---|---|---|---|
| S01 | 1032 | 995 | 408/995 (0.410) | 408/995 (0.410) | 409/995 (0.411) |
| S07 | 984 | 984 | 556/984 (0.565) | 556/984 (0.565) | 703/984 (0.714) |
| S13 | 888 | 826 | 642/826 (0.777) | 642/826 (0.777) | 724/826 (0.877) |
| S15 | 888 | 878 | 865/878 (0.985) | 865/878 (0.985) | 865/878 (0.985) |
| S20 | 888 | 879 | 776/879 (0.883) | 776/879 (0.883) | 779/879 (0.886) |
| S26 | 744 | 731 | 599/731 (0.819) | 599/731 (0.819) | 684/731 (0.936) |
| S27 | 888 | 848 | 753/848 (0.888) | 753/848 (0.888) | 753/848 (0.888) |
| S30 | 888 | 883 | 707/883 (0.801) | 707/883 (0.801) | 744/883 (0.843) |
| S55 | 888 | 860 | 801/860 (0.931) | 801/860 (0.931) | 855/860 (0.994) |
| S72 | 744 | 723 | 519/723 (0.718) | 519/723 (0.718) | 580/723 (0.802) |
| S92 | 1032 | 1017 | 903/1017 (0.888) | 903/1017 (0.888) | 903/1017 (0.888) |

Cells with more than 5% of COMPLETE records unparsed (no value in the gold unit): 0.
Cells with more than 5% of all records failing the answer format (UNPARSEABLE and similar): 56: `S01-i0:D:z0:d1:after_context`, `S01-i0:D:z1:d0:after_context:instr_relevance`, `S01-i0:D:z2:d1:after_context`, `S01-i0:K:z0:k1:after_context`, `S01-i0:K:z1:k1:after_context`, `S01-i0:R:z0:r1:after_context`, `S01-i0:R:z1:r0:after_context:instr_relevance`, `S01-i0:R:z1:r1:after_context:instr_relevance`, `S01-i0:S:relevant_edit`, `S01-i0:no_cue:instr_relevance`, `S13-i0:C:z0:c1:after_context`, `S13-i0:C:z1:c0:after_context`, `S13-i0:C:z2:c0:after_context`, `S13-i0:C:z2:c1:after_context`, `S13-i0:D:z1:d0:after_context:instr_relevance`, `S13-i0:N:d1:after_context`, `S13-i0:R:z0:r0:after_context`, `S13-i0:R:z0:r1:after_context`, `S13-i0:R:z1:r0:after_context`, `S13-i0:S:nongov_convertible_unit_same_magnitude`, `S13-i0:S:nongov_same_unit_far`, `S13-i0:S:nongov_same_unit_near_high_overlap`, `S13-i0:S:nongov_same_unit_near_low_overlap`, `S13-i0:S:nonnumeric_extra`, `S13-i0:S:relevant_edit`, `S13-i0:no_cue`, `S13-i0:no_cue:instr_relevance`, `S15-i0:no_cue:instr_relevance`, `S20-i0:D:z1:d1:after_context:instr_relevance`, `S20-i0:S:role_reversal`, `S26-i0:D:z0:d0:after_context`, `S26-i0:D:z1:d0:after_context`, `S26-i0:R:z0:r1:after_context`, `S26-i0:R:z1:r1:after_context`, `S27-i0:C:z0:c1:after_context`, `S27-i0:C:z2:c0:after_context`, `S27-i0:N:d0:after_context`, `S27-i0:S:nongov_incompatible_unit_same_digits`, `S27-i0:S:nongov_same_unit_far`, `S27-i0:S:nongov_same_unit_near_high_overlap`, `S27-i0:S:nonnumeric_extra`, `S27-i0:S:relevant_edit`, `S27-i0:no_cue:instr_relevance`, `S30-i0:D:z2:d0:after_context`, `S55-i0:C:z0:c1:after_context`, `S55-i0:D:z0:d1:after_context`, `S55-i0:D:z1:d1:after_context:instr_relevance`, `S55-i0:N:d1:after_context`, `S55-i0:S:nongov_convertible_unit_same_magnitude`, `S55-i0:S:nonnumeric_extra`, `S55-i0:S:relevant_edit`, `S55-i0:no_cue:instr_relevance`, `S72-i0:D:z1:d0:after_context:instr_relevance`, `S72-i0:R:z1:r1:after_context:instr_relevance`, `S92-i0:D:z1:d1:after_context:instr_relevance`, `S92-i0:no_cue:instr_relevance`.

### 2. Certification (per cell)

| cell | R gold | base gold | misuse (any) | placebo | modal (n of valued) | modal is |
|---|---|---|---|---|---|---|
| `S01-i0:N:d0:after_context` (S01) | n/a | 6/23 (0.261) | no declared misuse values | n/a | 2.8 (14 of 23) | none |
| `S01-i0:N:d1:after_context` (S01) | n/a | 11/23 (0.478) | no declared misuse values | n/a | 2.18 (11 of 23) | gold (gold) |
| `S01-i0:R:z0:r0:after_context` (S01) | 16/24 (0.667) | 0/24 (0.000) | n/a | n/a | 1.43 (16 of 24) | gold (gold) |
| `S01-i0:R:z0:r1:after_context` (S01) | 10/22 (0.455) | 1/22 (0.045) | n/a | n/a | 1.43 (10 of 22) | gold (gold) |
| `S01-i0:D:z0:d0:after_context` (S01) | n/a | 8/24 (0.333) | 1/24 (0.042) [add 0/24 (0.000), digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 1/24 (0.042), subtract 0/24 (0.000)] | n/a | 2.8 (15 of 24) | none |
| `S01-i0:D:z0:d1:after_context` (S01) | n/a | 11/22 (0.500) | 2/22 (0.091) [add 0/22 (0.000), digit_copy 0/22 (0.000), relevant_twin 0/22 (0.000), replace 2/22 (0.091), subtract 0/22 (0.000)] | n/a | 2.18 (11 of 22) | gold (gold) |
| `S01-i0:R:z1:r0:after_context` (S01) | 11/24 (0.458) | 1/24 (0.042) | n/a | n/a | 1.09 (11 of 24) | gold (gold) |
| `S01-i0:R:z1:r1:after_context` (S01) | 12/24 (0.500) | 0/24 (0.000) | n/a | n/a | 1.09 (12 of 24) | gold (gold) |
| `S01-i0:D:z1:d0:after_context` (S01) | n/a | 10/23 (0.435) | 0/23 (0.000) [add 0/23 (0.000), digit_copy 0/23 (0.000), relevant_twin 0/23 (0.000), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 2.8 (13 of 23) | none |
| `S01-i0:D:z1:d1:after_context` (S01) | n/a | 8/24 (0.333) | 0/24 (0.000) [add 0/24 (0.000), digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 2.8 (13 of 24) | none |
| `S01-i0:R:z2:r0:after_context` (S01) | 13/24 (0.542) | 0/24 (0.000) | n/a | n/a | 0.666 (13 of 24) | gold (gold) |
| `S01-i0:R:z2:r1:after_context` (S01) | 6/24 (0.250) | 0/24 (0.000) | n/a | n/a | 0.826 (9 of 24) | none |
| `S01-i0:D:z2:d0:after_context` (S01) | n/a | 10/23 (0.435) | 0/23 (0.000) [add 0/23 (0.000), digit_copy 0/23 (0.000), relevant_twin 0/23 (0.000), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 2.18 (10 of 23, tie) | gold (gold) |
| `S01-i0:D:z2:d1:after_context` (S01) | n/a | 5/22 (0.227) | 1/22 (0.045) [add 0/22 (0.000), digit_copy 0/22 (0.000), relevant_twin 1/22 (0.045), replace 0/22 (0.000), subtract 0/22 (0.000)] | n/a | 2.8 (13 of 22) | none |
| `S07-i0:N:d0:after_context` (S07) | n/a | 20/24 (0.833) | no declared misuse values | n/a | 6.61 (20 of 24) | gold (gold) |
| `S07-i0:N:d1:after_context` (S07) | n/a | 19/24 (0.792) | no declared misuse values | n/a | 6.61 (19 of 24) | gold (gold) |
| `S07-i0:R:z0:r0:after_context` (S07) | 0/24 (0.000) | 23/24 (0.958) | n/a | n/a | 6.61 (17 of 24) | foil (neglect) |
| `S07-i0:R:z0:r1:after_context` (S07) | 0/24 (0.000) | 14/24 (0.583) | n/a | n/a | 6.61 (11 of 24) | foil (neglect) |
| `S07-i0:D:z0:d0:after_context` (S07) | n/a | 18/24 (0.750) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 6.61 (18 of 24) | gold (gold) |
| `S07-i0:D:z0:d1:after_context` (S07) | n/a | 22/24 (0.917) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 6.61 (22 of 24) | gold (gold) |
| `S07-i0:R:z1:r0:after_context` (S07) | 0/24 (0.000) | 24/24 (1.000) | n/a | n/a | 6.61 (22 of 24) | foil (neglect) |
| `S07-i0:R:z1:r1:after_context` (S07) | 0/24 (0.000) | 4/24 (0.167) | n/a | n/a | 8.17 (13 of 24) | foil (replace:R) |
| `S07-i0:D:z1:d0:after_context` (S07) | n/a | 22/24 (0.917) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 6.61 (22 of 24) | gold (gold) |
| `S07-i0:D:z1:d1:after_context` (S07) | n/a | 23/24 (0.958) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 6.61 (23 of 24) | gold (gold) |
| `S07-i0:R:z2:r0:after_context` (S07) | 0/24 (0.000) | 24/24 (1.000) | n/a | n/a | 6.61 (19 of 24) | foil (neglect) |
| `S07-i0:R:z2:r1:after_context` (S07) | 0/24 (0.000) | 4/24 (0.167) | n/a | n/a | 5.232 (14 of 24) | foil (replace:R) |
| `S07-i0:D:z2:d0:after_context` (S07) | n/a | 23/24 (0.958) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 6.61 (23 of 24) | gold (gold) |
| `S07-i0:D:z2:d1:after_context` (S07) | n/a | 20/24 (0.833) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 6.61 (20 of 24) | gold (gold) |
| `S13-i0:N:d0:after_context` (S13) | n/a | 21/23 (0.913) | no declared misuse values | n/a | 1.795 (18 of 23) | gold (gold) |
| `S13-i0:N:d1:after_context` (S13) | n/a | 20/20 (1.000) | no declared misuse values | n/a | 1.795 (19 of 20) | gold (gold) |
| `S13-i0:R:z0:r0:after_context` (S13) | 10/22 (0.455) | 5/22 (0.227) | n/a | n/a | 2.105 (6 of 22) | gold (gold) |
| `S13-i0:R:z0:r1:after_context` (S13) | 9/22 (0.409) | 3/22 (0.136) | n/a | n/a | 2.105 (8 of 22) | gold (gold) |
| `S13-i0:D:z0:d0:after_context` (S13) | n/a | 21/23 (0.913) | 0/23 (0.000) [digit_copy 0/23 (0.000), relevant_twin 0/23 (0.000), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 1.795 (20 of 23) | gold (gold) |
| `S13-i0:D:z0:d1:after_context` (S13) | n/a | 22/23 (0.957) | 0/23 (0.000) [digit_copy 0/23 (0.000), relevant_twin 0/23 (0.000), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 1.795 (19 of 23) | gold (gold) |
| `S13-i0:R:z1:r0:after_context` (S13) | 9/21 (0.429) | 3/21 (0.143) | n/a | n/a | 2.29 (9 of 21) | gold (gold) |
| `S13-i0:R:z1:r1:after_context` (S13) | 12/23 (0.522) | 5/23 (0.217) | n/a | n/a | 2.29 (12 of 23) | gold (gold) |
| `S13-i0:D:z1:d0:after_context` (S13) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 1.795 (22 of 24) | gold (gold) |
| `S13-i0:D:z1:d1:after_context` (S13) | n/a | 21/24 (0.875) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 1.795 (19 of 24) | gold (gold) |
| `S13-i0:R:z2:r0:after_context` (S13) | 8/24 (0.333) | 4/24 (0.167) | n/a | n/a | 2.46 (8 of 24) | gold (gold) |
| `S13-i0:R:z2:r1:after_context` (S13) | 16/24 (0.667) | 4/24 (0.167) | n/a | n/a | 2.46 (16 of 24) | gold (gold) |
| `S13-i0:D:z2:d0:after_context` (S13) | n/a | 22/24 (0.917) | 1/24 (0.042) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 1/24 (0.042), subtract 0/24 (0.000)] | n/a | 1.795 (20 of 24) | gold (gold) |
| `S13-i0:D:z2:d1:after_context` (S13) | n/a | 23/24 (0.958) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 1.795 (19 of 24) | gold (gold) |
| `S15-i0:N:d0:after_context` (S15) | n/a | 23/23 (1.000) | no declared misuse values | n/a | 36 (23 of 23) | gold (gold) |
| `S15-i0:N:d1:after_context` (S15) | n/a | 22/23 (0.957) | no declared misuse values | n/a | 36 (22 of 23) | gold (gold) |
| `S15-i0:R:z0:r0:after_context` (S15) | 24/24 (1.000) | 0/24 (0.000) | n/a | n/a | 45.56 (24 of 24) | gold (gold) |
| `S15-i0:R:z0:r1:after_context` (S15) | 24/24 (1.000) | 0/24 (0.000) | n/a | n/a | 45.56 (24 of 24) | gold (gold) |
| `S15-i0:D:z0:d0:after_context` (S15) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 36 (24 of 24) | gold (gold) |
| `S15-i0:D:z0:d1:after_context` (S15) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 36 (24 of 24) | gold (gold) |
| `S15-i0:R:z1:r0:after_context` (S15) | 24/24 (1.000) | 0/24 (0.000) | n/a | n/a | 56.25 (24 of 24) | gold (gold) |
| `S15-i0:R:z1:r1:after_context` (S15) | 24/24 (1.000) | 0/24 (0.000) | n/a | n/a | 56.25 (24 of 24) | gold (gold) |
| `S15-i0:D:z1:d0:after_context` (S15) | n/a | 23/24 (0.958) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 36 (23 of 24) | gold (gold) |
| `S15-i0:D:z1:d1:after_context` (S15) | n/a | 22/23 (0.957) | 0/23 (0.000) [digit_copy 0/23 (0.000), relevant_twin 0/23 (0.000), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 36 (22 of 23) | gold (gold) |
| `S15-i0:R:z2:r0:after_context` (S15) | 22/24 (0.917) | 0/24 (0.000) | n/a | n/a | 64 (22 of 24) | gold (gold) |
| `S15-i0:R:z2:r1:after_context` (S15) | 24/24 (1.000) | 0/24 (0.000) | n/a | n/a | 64 (24 of 24) | gold (gold) |
| `S15-i0:D:z2:d0:after_context` (S15) | n/a | 23/24 (0.958) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 36 (23 of 24) | gold (gold) |
| `S15-i0:D:z2:d1:after_context` (S15) | n/a | 22/24 (0.917) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 36 (22 of 24) | gold (gold) |
| `S20-i0:N:d0:after_context` (S20) | n/a | 24/24 (1.000) | no declared misuse values | n/a | 17.14 (24 of 24) | gold (gold) |
| `S20-i0:N:d1:after_context` (S20) | n/a | 24/24 (1.000) | no declared misuse values | n/a | 17.14 (24 of 24) | gold (gold) |
| `S20-i0:R:z0:r0:after_context` (S20) | 24/24 (1.000) | 0/24 (0.000) | n/a | n/a | 16.23 (19 of 24) | gold (gold) |
| `S20-i0:R:z0:r1:after_context` (S20) | 23/24 (0.958) | 0/24 (0.000) | n/a | n/a | 16.23 (24 of 24) | gold (gold) |
| `S20-i0:D:z0:d0:after_context` (S20) | n/a | 0/24 (0.000) | 24/24 (1.000) [add 0/24 (0.000), copy 0/24 (0.000), relevant_twin 24/24 (1.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 16.23 (14 of 24) | foil (relevant_twin) |
| `S20-i0:D:z0:d1:after_context` (S20) | n/a | 24/24 (1.000) | 0/24 (0.000) [add 0/24 (0.000), copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 17.14 (24 of 24) | gold (gold) |
| `S20-i0:R:z1:r0:after_context` (S20) | 24/24 (1.000) | 0/24 (0.000) | n/a | n/a | 15.13 (24 of 24) | gold (gold) |
| `S20-i0:R:z1:r1:after_context` (S20) | 23/24 (0.958) | 0/24 (0.000) | n/a | n/a | 15.13 (23 of 24) | gold (gold) |
| `S20-i0:D:z1:d0:after_context` (S20) | n/a | 0/24 (0.000) | 24/24 (1.000) [add 0/24 (0.000), copy 0/24 (0.000), relevant_twin 24/24 (1.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 15.13 (24 of 24) | foil (relevant_twin) |
| `S20-i0:D:z1:d1:after_context` (S20) | n/a | 22/24 (0.917) | 2/24 (0.083) [add 0/24 (0.000), copy 0/24 (0.000), relevant_twin 2/24 (0.083), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 17.14 (22 of 24) | gold (gold) |
| `S20-i0:R:z2:r0:after_context` (S20) | 24/24 (1.000) | 0/24 (0.000) | n/a | n/a | 14.48 (24 of 24) | gold (gold) |
| `S20-i0:R:z2:r1:after_context` (S20) | 23/24 (0.958) | 0/24 (0.000) | n/a | n/a | 14.48 (23 of 24) | gold (gold) |
| `S20-i0:D:z2:d0:after_context` (S20) | n/a | 0/24 (0.000) | 24/24 (1.000) [add 0/24 (0.000), copy 0/24 (0.000), relevant_twin 24/24 (1.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 14.48 (24 of 24) | foil (relevant_twin) |
| `S20-i0:D:z2:d1:after_context` (S20) | n/a | 24/24 (1.000) | 0/24 (0.000) [add 0/24 (0.000), copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 17.14 (24 of 24) | gold (gold) |
| `S26-i0:N:d0:after_context` (S26) | n/a | 24/24 (1.000) | no declared misuse values | n/a | 25.37 (24 of 24) | gold (gold) |
| `S26-i0:N:d1:after_context` (S26) | n/a | 24/24 (1.000) | no declared misuse values | n/a | 25.37 (24 of 24) | gold (gold) |
| `S26-i0:R:z0:r0:after_context` (S26) | 0/24 (0.000) | 0/24 (0.000) | n/a | n/a | 28.6 (23 of 24) | gold (gold) |
| `S26-i0:R:z0:r1:after_context` (S26) | 0/22 (0.000) | 12/22 (0.545) | n/a | n/a | 28.6 (10 of 22) | gold (gold) |
| `S26-i0:D:z0:d0:after_context` (S26) | n/a | 16/21 (0.762) | 0/21 (0.000) [add 0/21 (0.000), copy 0/21 (0.000), relevant_twin 0/21 (0.000), replace 0/21 (0.000), subtract 0/21 (0.000)] | n/a | 25.37 (16 of 21) | gold (gold) |
| `S26-i0:D:z0:d1:after_context` (S26) | n/a | 22/23 (0.957) | 0/23 (0.000) [add 0/23 (0.000), copy 0/23 (0.000), relevant_twin 0/23 (0.000), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 25.37 (22 of 23) | gold (gold) |
| `S26-i0:R:z1:r0:after_context` (S26) | 24/24 (1.000) | 0/24 (0.000) | n/a | n/a | 31.2 (24 of 24) | gold (gold) |
| `S26-i0:R:z1:r1:after_context` (S26) | 12/22 (0.545) | 10/22 (0.455) | n/a | n/a | 31.2 (12 of 22) | gold (gold) |
| `S26-i0:D:z1:d0:after_context` (S26) | n/a | 21/22 (0.955) | 0/22 (0.000) [add 0/22 (0.000), copy 0/22 (0.000), relevant_twin 0/22 (0.000), replace 0/22 (0.000), subtract 0/22 (0.000)] | n/a | 25.37 (21 of 22) | gold (gold) |
| `S26-i0:D:z1:d1:after_context` (S26) | n/a | 23/24 (0.958) | 0/24 (0.000) [add 0/24 (0.000), copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 25.37 (23 of 24) | gold (gold) |
| `S26-i0:R:z2:r0:after_context` (S26) | 24/24 (1.000) | 0/24 (0.000) | n/a | n/a | 32.6 (24 of 24) | gold (gold) |
| `S26-i0:R:z2:r1:after_context` (S26) | 15/24 (0.625) | 9/24 (0.375) | n/a | n/a | 32.6 (15 of 24) | gold (gold) |
| `S26-i0:D:z2:d0:after_context` (S26) | n/a | 16/23 (0.696) | 3/23 (0.130) [add 0/23 (0.000), copy 0/23 (0.000), relevant_twin 3/23 (0.130), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 25.37 (16 of 23) | gold (gold) |
| `S26-i0:D:z2:d1:after_context` (S26) | n/a | 23/24 (0.958) | 0/24 (0.000) [add 0/24 (0.000), copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 25.37 (23 of 24) | gold (gold) |
| `S27-i0:N:d0:after_context` (S27) | n/a | 21/21 (1.000) | no declared misuse values | n/a | 218.6 (21 of 21) | gold (gold) |
| `S27-i0:N:d1:after_context` (S27) | n/a | 24/24 (1.000) | no declared misuse values | n/a | 218.6 (24 of 24) | gold (gold) |
| `S27-i0:R:z0:r0:after_context` (S27) | 22/24 (0.917) | 2/24 (0.083) | n/a | n/a | 226.1 (22 of 24) | gold (gold) |
| `S27-i0:R:z0:r1:after_context` (S27) | 12/23 (0.522) | 11/23 (0.478) | n/a | n/a | 226.1 (12 of 23) | gold (gold) |
| `S27-i0:D:z0:d0:after_context` (S27) | n/a | 13/23 (0.565) | 9/23 (0.391) [copy 0/23 (0.000), relevant_twin 9/23 (0.391), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 218.6 (13 of 23) | gold (gold) |
| `S27-i0:D:z0:d1:after_context` (S27) | n/a | 22/23 (0.957) | 1/23 (0.043) [copy 0/23 (0.000), relevant_twin 1/23 (0.043), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 218.6 (22 of 23) | gold (gold) |
| `S27-i0:R:z1:r0:after_context` (S27) | 19/24 (0.792) | 5/24 (0.208) | n/a | n/a | 233.6 (19 of 24) | gold (gold) |
| `S27-i0:R:z1:r1:after_context` (S27) | 11/24 (0.458) | 12/24 (0.500) | n/a | n/a | 218.6 (12 of 24) | foil (neglect) |
| `S27-i0:D:z1:d0:after_context` (S27) | n/a | 20/23 (0.870) | 2/23 (0.087) [copy 0/23 (0.000), relevant_twin 2/23 (0.087), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 218.6 (20 of 23) | gold (gold) |
| `S27-i0:D:z1:d1:after_context` (S27) | n/a | 22/23 (0.957) | 1/23 (0.043) [copy 0/23 (0.000), relevant_twin 1/23 (0.043), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 218.6 (22 of 23) | gold (gold) |
| `S27-i0:R:z2:r0:after_context` (S27) | 21/24 (0.875) | 2/24 (0.083) | n/a | n/a | 253.6 (21 of 24) | gold (gold) |
| `S27-i0:R:z2:r1:after_context` (S27) | 12/24 (0.500) | 11/24 (0.458) | n/a | n/a | 253.6 (12 of 24) | gold (gold) |
| `S27-i0:D:z2:d0:after_context` (S27) | n/a | 10/24 (0.417) | 12/24 (0.500) [copy 0/24 (0.000), relevant_twin 12/24 (0.500), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 253.6 (12 of 24) | foil (relevant_twin) |
| `S27-i0:D:z2:d1:after_context` (S27) | n/a | 21/23 (0.913) | 1/23 (0.043) [copy 0/23 (0.000), relevant_twin 1/23 (0.043), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 218.6 (21 of 23) | gold (gold) |
| `S30-i0:N:d0:after_context` (S30) | n/a | 24/24 (1.000) | no declared misuse values | n/a | 223.2 (18 of 24) | gold (gold) |
| `S30-i0:N:d1:after_context` (S30) | n/a | 24/24 (1.000) | no declared misuse values | n/a | 223.2 (18 of 24) | gold (gold) |
| `S30-i0:R:z0:r0:after_context` (S30) | 3/24 (0.125) | 19/24 (0.792) | n/a | n/a | 223.2 (17 of 24) | foil (neglect) |
| `S30-i0:R:z0:r1:after_context` (S30) | 10/23 (0.435) | 0/23 (0.000) | n/a | n/a | 312.6 (10 of 23) | gold (gold) |
| `S30-i0:D:z0:d0:after_context` (S30) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 223.2 (22 of 24) | gold (gold) |
| `S30-i0:D:z0:d1:after_context` (S30) | n/a | 11/23 (0.478) | 12/23 (0.522) [digit_copy 0/23 (0.000), relevant_twin 12/23 (0.522), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 223.2 (10 of 23) | gold (gold) |
| `S30-i0:R:z1:r0:after_context` (S30) | 6/24 (0.250) | 12/24 (0.500) | n/a | n/a | 223.2 (10 of 24) | foil (neglect) |
| `S30-i0:R:z1:r1:after_context` (S30) | 10/24 (0.417) | 1/24 (0.042) | n/a | n/a | 379.5 (11 of 24) | gold (gold) |
| `S30-i0:D:z1:d0:after_context` (S30) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 223.2 (14 of 24) | gold (gold) |
| `S30-i0:D:z1:d1:after_context` (S30) | n/a | 21/24 (0.875) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 223.2 (19 of 24) | gold (gold) |
| `S30-i0:R:z2:r0:after_context` (S30) | 0/24 (0.000) | 15/24 (0.625) | n/a | n/a | 223.2 (15 of 24) | foil (neglect) |
| `S30-i0:R:z2:r1:after_context` (S30) | 2/24 (0.083) | 0/24 (0.000) | n/a | n/a | 512.8 (14 of 24) | gold (gold) |
| `S30-i0:D:z2:d0:after_context` (S30) | n/a | 22/22 (1.000) | 0/22 (0.000) [digit_copy 0/22 (0.000), relevant_twin 0/22 (0.000), replace 0/22 (0.000), subtract 0/22 (0.000)] | n/a | 223.2 (17 of 22) | gold (gold) |
| `S30-i0:D:z2:d1:after_context` (S30) | n/a | 20/24 (0.833) | 3/24 (0.125) [digit_copy 0/24 (0.000), relevant_twin 3/24 (0.125), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 223.2 (15 of 24) | gold (gold) |
| `S55-i0:N:d0:after_context` (S55) | n/a | 24/24 (1.000) | no declared misuse values | n/a | 1368 (24 of 24) | gold (gold) |
| `S55-i0:N:d1:after_context` (S55) | n/a | 22/22 (1.000) | no declared misuse values | n/a | 1368 (22 of 22) | gold (gold) |
| `S55-i0:R:z0:r0:after_context` (S55) | 8/24 (0.333) | 0/24 (0.000) | n/a | n/a | 1477 (18 of 24) | gold (gold) |
| `S55-i0:R:z0:r1:after_context` (S55) | 13/24 (0.542) | 0/24 (0.000) | n/a | n/a | 1477 (23 of 24) | gold (gold) |
| `S55-i0:D:z0:d0:after_context` (S55) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 1368 (24 of 24) | gold (gold) |
| `S55-i0:D:z0:d1:after_context` (S55) | n/a | 22/22 (1.000) | 0/22 (0.000) [digit_copy 0/22 (0.000), relevant_twin 0/22 (0.000), replace 0/22 (0.000), subtract 0/22 (0.000)] | n/a | 1368 (22 of 22) | gold (gold) |
| `S55-i0:R:z1:r0:after_context` (S55) | 20/23 (0.870) | 0/23 (0.000) | n/a | n/a | 1579 (20 of 23) | gold (gold) |
| `S55-i0:R:z1:r1:after_context` (S55) | 22/24 (0.917) | 0/24 (0.000) | n/a | n/a | 1579 (22 of 24) | gold (gold) |
| `S55-i0:D:z1:d0:after_context` (S55) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 1368 (24 of 24) | gold (gold) |
| `S55-i0:D:z1:d1:after_context` (S55) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 1368 (24 of 24) | gold (gold) |
| `S55-i0:R:z2:r0:after_context` (S55) | 23/24 (0.958) | 0/24 (0.000) | n/a | n/a | 1766 (24 of 24) | gold (gold) |
| `S55-i0:R:z2:r1:after_context` (S55) | 23/24 (0.958) | 1/24 (0.042) | n/a | n/a | 1766 (23 of 24) | gold (gold) |
| `S55-i0:D:z2:d0:after_context` (S55) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 1368 (24 of 24) | gold (gold) |
| `S55-i0:D:z2:d1:after_context` (S55) | n/a | 24/24 (1.000) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 1368 (24 of 24) | gold (gold) |
| `S72-i0:N:d0:after_context` (S72) | n/a | 19/24 (0.792) | no declared misuse values | n/a | 100.1 (11 of 24) | gold (gold) |
| `S72-i0:N:d1:after_context` (S72) | n/a | 17/23 (0.739) | no declared misuse values | n/a | 100.2 (10 of 23) | gold (gold) |
| `S72-i0:R:z0:r0:after_context` (S72) | 20/24 (0.833) | 0/24 (0.000) | n/a | n/a | 89 (20 of 24) | gold (gold) |
| `S72-i0:R:z0:r1:after_context` (S72) | 11/23 (0.478) | 6/23 (0.261) | n/a | n/a | 89 (11 of 23) | gold (gold) |
| `S72-i0:D:z0:d0:after_context` (S72) | n/a | 22/24 (0.917) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 100.1 (17 of 24) | gold (add:mc2, gold, subtract:mc2) |
| `S72-i0:D:z0:d1:after_context` (S72) | n/a | 19/23 (0.826) | 0/23 (0.000) [digit_copy 0/23 (0.000), relevant_twin 0/23 (0.000), replace 0/23 (0.000), subtract 0/23 (0.000)] | n/a | 100.1 (12 of 23) | gold (add:mc2, gold, subtract:mc2) |
| `S72-i0:R:z1:r0:after_context` (S72) | 18/23 (0.783) | 2/23 (0.087) | n/a | n/a | 79.2 (18 of 23) | gold (gold) |
| `S72-i0:R:z1:r1:after_context` (S72) | 4/24 (0.167) | 15/24 (0.625) | n/a | n/a | 100.1 (8 of 24) | foil (add:mc2, neglect, subtract:mc2) |
| `S72-i0:D:z1:d0:after_context` (S72) | n/a | 19/24 (0.792) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 100.2 (11 of 24) | gold (add:mc2, gold, subtract:mc2) |
| `S72-i0:D:z1:d1:after_context` (S72) | n/a | 15/22 (0.682) | 0/22 (0.000) [digit_copy 0/22 (0.000), relevant_twin 0/22 (0.000), replace 0/22 (0.000), subtract 0/22 (0.000)] | n/a | 100.1 (11 of 22) | gold (add:mc2, gold, subtract:mc2) |
| `S72-i0:R:z2:r0:after_context` (S72) | 16/23 (0.696) | 2/23 (0.087) | n/a | n/a | 67.5 (16 of 23) | gold (gold) |
| `S72-i0:R:z2:r1:after_context` (S72) | 3/23 (0.130) | 16/23 (0.696) | n/a | n/a | 100.1 (9 of 23) | foil (add:mc2, neglect, subtract:mc2) |
| `S72-i0:D:z2:d0:after_context` (S72) | n/a | 21/23 (0.913) | 0/23 (0.000) [digit_copy 0/23 (0.000), relevant_twin 0/23 (0.000), replace 0/23 (0.000)] | n/a | 100.2 (14 of 23) | gold (add:mc2, gold, subtract:mc2) |
| `S72-i0:D:z2:d1:after_context` (S72) | n/a | 20/24 (0.833) | 0/24 (0.000) [digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000)] | n/a | 100.2 (12 of 24) | gold (add:mc2, gold, subtract:mc2) |
| `S92-i0:N:d0:after_context` (S92) | n/a | 24/24 (1.000) | no declared misuse values | n/a | 3.92 (24 of 24) | gold (gold) |
| `S92-i0:N:d1:after_context` (S92) | n/a | 22/24 (0.917) | no declared misuse values | n/a | 3.92 (22 of 24) | gold (gold) |
| `S92-i0:R:z0:r0:after_context` (S92) | 19/24 (0.792) | 5/24 (0.208) | n/a | n/a | 5.39 (19 of 24) | gold (gold) |
| `S92-i0:R:z0:r1:after_context` (S92) | 24/24 (1.000) | 0/24 (0.000) | n/a | n/a | 5.39 (24 of 24) | gold (gold) |
| `S92-i0:D:z0:d0:after_context` (S92) | n/a | 24/24 (1.000) | 0/24 (0.000) [add 0/24 (0.000), digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 3.92 (24 of 24) | gold (gold) |
| `S92-i0:D:z0:d1:after_context` (S92) | n/a | 4/24 (0.167) | 20/24 (0.833) [add 0/24 (0.000), digit_copy 0/24 (0.000), relevant_twin 20/24 (0.833), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 5.39 (20 of 24) | foil (relevant_twin) |
| `S92-i0:R:z1:r0:after_context` (S92) | 23/24 (0.958) | 1/24 (0.042) | n/a | n/a | 6.37 (23 of 24) | gold (gold) |
| `S92-i0:R:z1:r1:after_context` (S92) | 23/24 (0.958) | 0/24 (0.000) | n/a | n/a | 6.37 (23 of 24) | gold (gold) |
| `S92-i0:D:z1:d0:after_context` (S92) | n/a | 23/24 (0.958) | 0/24 (0.000) [add 0/24 (0.000), digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 3.92 (23 of 24) | gold (gold) |
| `S92-i0:D:z1:d1:after_context` (S92) | n/a | 8/24 (0.333) | 16/24 (0.667) [add 0/24 (0.000), digit_copy 0/24 (0.000), relevant_twin 16/24 (0.667), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 6.37 (16 of 24) | foil (relevant_twin) |
| `S92-i0:R:z2:r0:after_context` (S92) | 19/24 (0.792) | 5/24 (0.208) | n/a | n/a | 7.35 (19 of 24) | gold (gold) |
| `S92-i0:R:z2:r1:after_context` (S92) | 23/24 (0.958) | 0/24 (0.000) | n/a | n/a | 7.35 (23 of 24) | gold (gold) |
| `S92-i0:D:z2:d0:after_context` (S92) | n/a | 23/24 (0.958) | 0/24 (0.000) [add 0/24 (0.000), digit_copy 0/24 (0.000), relevant_twin 0/24 (0.000), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 3.92 (23 of 24) | gold (gold) |
| `S92-i0:D:z2:d1:after_context` (S92) | n/a | 3/24 (0.125) | 20/24 (0.833) [add 0/24 (0.000), digit_copy 0/24 (0.000), relevant_twin 20/24 (0.833), replace 0/24 (0.000), subtract 0/24 (0.000)] | n/a | 7.35 (20 of 24) | foil (relevant_twin) |

### 3. Ambiguity (rule B on tracking share, phrasing 0 vs 1)

| structure | R state (diff, 95% CI) | D state (diff, 95% CI) |
|---|---|---|
| S01 | DISAGREE (+0.167, [+0.004, +0.318]; 40/72 (0.556) vs 28/72 (0.389)) | UNRESOLVED (+0.056, [-0.100, +0.207]; 28/72 (0.389) vs 24/72 (0.333)) |
| S07 | AGREE (+0.000, [-0.051, +0.051]; 0/72 (0.000) vs 0/72 (0.000)) | UNRESOLVED (-0.028, [-0.136, +0.079]; 63/72 (0.875) vs 65/72 (0.903)) |
| S13 | UNRESOLVED (-0.139, [-0.291, +0.023]; 27/72 (0.375) vs 37/72 (0.514)) | AGREE (+0.014, [-0.080, +0.109]; 67/72 (0.931) vs 66/72 (0.917)) |
| S15 | AGREE (-0.028, [-0.096, +0.027]; 70/72 (0.972) vs 72/72 (1.000)) | AGREE (+0.028, [-0.048, +0.109]; 70/72 (0.972) vs 68/72 (0.944)) |
| S20 | AGREE (+0.042, [-0.016, +0.115]; 72/72 (1.000) vs 69/72 (0.958)) | DISAGREE (-0.972, [-0.992, -0.887]; 0/72 (0.000) vs 70/72 (0.972)) |
| S26 | DISAGREE (+0.292, [+0.129, +0.434]; 48/72 (0.667) vs 27/72 (0.375)) | DISAGREE (-0.208, [-0.325, -0.090]; 53/72 (0.736) vs 68/72 (0.944)) |
| S27 | DISAGREE (+0.375, [+0.225, +0.503]; 62/72 (0.861) vs 35/72 (0.486)) | DISAGREE (-0.306, [-0.431, -0.167]; 43/72 (0.597) vs 65/72 (0.903)) |
| S30 | DISAGREE (-0.181, [-0.308, -0.046]; 9/72 (0.125) vs 22/72 (0.306)) | DISAGREE (+0.250, [+0.137, +0.364]; 70/72 (0.972) vs 52/72 (0.722)) |
| S55 | UNRESOLVED (-0.097, [-0.233, +0.043]; 51/72 (0.708) vs 58/72 (0.806)) | AGREE (+0.028, [-0.027, +0.096]; 72/72 (1.000) vs 70/72 (0.972)) |
| S72 | DISAGREE (+0.500, [+0.343, +0.621]; 54/72 (0.750) vs 18/72 (0.250)) | UNRESOLVED (+0.111, [-0.019, +0.238]; 62/72 (0.861) vs 54/72 (0.750)) |
| S92 | DISAGREE (-0.125, [-0.227, -0.031]; 61/72 (0.847) vs 70/72 (0.972)) | DISAGREE (+0.764, [+0.637, +0.844]; 70/72 (0.972) vs 15/72 (0.208)) |

Cross-structure rule B (library `phrasing_difference_agreement` on per-structure differences): R: UNRESOLVED (J=11); D: UNRESOLVED (J=11).
WORDING_DEPENDENT structures (DISAGREE on R or D twins): S01, S20, S26, S27, S30, S72, S92.

Medium-flag cells (reported apart):

* S26 R:r1 cell `S26-i0:R:z0:r1:after_context`: R gold 0/22 (0.000); base gold 12/22 (0.545); modal 28.6.
* S26 R:r1 cell `S26-i0:R:z1:r1:after_context`: R gold 12/22 (0.545); base gold 10/22 (0.455); modal 31.2.
* S26 R:r1 cell `S26-i0:R:z2:r1:after_context`: R gold 15/24 (0.625); base gold 9/24 (0.375); modal 32.6.
* S55 R:r1 cell `S55-i0:R:z0:r1:after_context`: R gold 13/24 (0.542); base gold 0/24 (0.000); modal 1477.0.
* S55 R:r1 cell `S55-i0:R:z1:r1:after_context`: R gold 22/24 (0.917); base gold 0/24 (0.000); modal 1579.0.
* S55 R:r1 cell `S55-i0:R:z2:r1:after_context`: R gold 23/24 (0.958); base gold 1/24 (0.042); modal 1766.0.

### 4. Feasibility

| structure | no-cue correct, of all samples | of COMPLETE | band [0.30, 0.85] | T_R of all | T_R of COMPLETE | budget exhausted | format failure | tokens mean / max |
|---|---|---|---|---|---|---|---|---|
| S01 | 9/24 (0.375) | 9/23 (0.391) | in band | 68/144 (0.472) | 68/142 (0.479) | 2/1032 (0.002) | 35/1032 (0.034) | 989 / 4096 |
| S07 | 23/24 (0.958) | 23/24 (0.958) | out of band | 0/144 (0.000) | 0/144 (0.000) | 0/984 (0.000) | 0/984 (0.000) | 434 / 868 |
| S13 | 20/24 (0.833) | 20/22 (0.909) | in band | 64/144 (0.444) | 64/136 (0.471) | 0/888 (0.000) | 62/888 (0.070) | 338 / 1000 |
| S15 | 24/24 (1.000) | 24/24 (1.000) | out of band | 142/144 (0.986) | 142/144 (0.986) | 0/888 (0.000) | 10/888 (0.011) | 444 / 918 |
| S20 | 23/24 (0.958) | 23/23 (1.000) | out of band | 141/144 (0.979) | 141/144 (0.979) | 0/888 (0.000) | 9/888 (0.010) | 392 / 741 |
| S26 | 24/24 (1.000) | 24/24 (1.000) | out of band | 75/144 (0.521) | 75/140 (0.536) | 0/744 (0.000) | 13/744 (0.017) | 395 / 579 |
| S27 | 23/24 (0.958) | 23/23 (1.000) | out of band | 97/144 (0.674) | 97/143 (0.678) | 0/888 (0.000) | 40/888 (0.045) | 419 / 848 |
| S30 | 24/24 (1.000) | 24/24 (1.000) | out of band | 31/144 (0.215) | 31/143 (0.217) | 2/888 (0.002) | 3/888 (0.003) | 375 / 4096 |
| S55 | 24/24 (1.000) | 24/24 (1.000) | out of band | 109/144 (0.757) | 109/143 (0.762) | 0/888 (0.000) | 28/888 (0.032) | 376 / 534 |
| S72 | 21/24 (0.875) | 21/24 (0.875) | out of band | 72/144 (0.500) | 72/140 (0.514) | 12/744 (0.016) | 9/744 (0.012) | 725 / 4096 |
| S92 | 24/24 (1.000) | 24/24 (1.000) | out of band | 131/144 (0.910) | 131/144 (0.910) | 0/1032 (0.000) | 15/1032 (0.015) | 555 / 859 |
| ALL | 239/264 (0.905) | 239/259 (0.923) | out of band | 930/1584 (0.587) | 930/1563 (0.595) | 16/9864 (0.002) | 224/9864 (0.023) | 500 / 4096 |

## Cells whose modal answer is `none` in every model

* `S01-i0:D:z0:d0:after_context`: modal {'s15_g2pilot_m0v25_qwen25_7b': 2.45, 's15_g2pilot_m0v25_llama31_8b': 9.8, 's15_g2pilot_m0v25_qwen3_8b_nothink': 2.8}; models s15_g2pilot_m0v25_llama31_8b, s15_g2pilot_m0v25_qwen25_7b, s15_g2pilot_m0v25_qwen3_8b_nothink
* `S01-i0:D:z1:d0:after_context`: modal {'s15_g2pilot_m0v25_qwen25_7b': 2.45, 's15_g2pilot_m0v25_llama31_8b': 2.45, 's15_g2pilot_m0v25_qwen3_8b_nothink': 2.8}; models s15_g2pilot_m0v25_llama31_8b, s15_g2pilot_m0v25_qwen25_7b, s15_g2pilot_m0v25_qwen3_8b_nothink
* `S01-i0:D:z1:d1:after_context`: modal {'s15_g2pilot_m0v25_qwen25_7b': 9.8, 's15_g2pilot_m0v25_llama31_8b': 2.45, 's15_g2pilot_m0v25_qwen3_8b_nothink': 2.8}; models s15_g2pilot_m0v25_llama31_8b, s15_g2pilot_m0v25_qwen25_7b, s15_g2pilot_m0v25_qwen3_8b_nothink
* `S01-i0:D:z2:d1:after_context`: modal {'s15_g2pilot_m0v25_qwen25_7b': 0.737, 's15_g2pilot_m0v25_llama31_8b': 2.45, 's15_g2pilot_m0v25_qwen3_8b_nothink': 2.8}; models s15_g2pilot_m0v25_llama31_8b, s15_g2pilot_m0v25_qwen25_7b, s15_g2pilot_m0v25_qwen3_8b_nothink
* `S01-i0:N:d0:after_context`: modal {'s15_g2pilot_m0v25_qwen25_7b': 2.45, 's15_g2pilot_m0v25_llama31_8b': 9.8, 's15_g2pilot_m0v25_qwen3_8b_nothink': 2.8}; models s15_g2pilot_m0v25_llama31_8b, s15_g2pilot_m0v25_qwen25_7b, s15_g2pilot_m0v25_qwen3_8b_nothink
* `S01-i0:R:z2:r1:after_context`: modal {'s15_g2pilot_m0v25_qwen25_7b': 0.737, 's15_g2pilot_m0v25_llama31_8b': -0.738, 's15_g2pilot_m0v25_qwen3_8b_nothink': 0.826}; models s15_g2pilot_m0v25_llama31_8b, s15_g2pilot_m0v25_qwen25_7b, s15_g2pilot_m0v25_qwen3_8b_nothink

## WORDING_DEPENDENT structures across models

* S01: s15_g2pilot_m0v25_qwen3_8b_nothink
* S13: s15_g2pilot_m0v25_qwen25_7b
* S15: s15_g2pilot_m0v25_llama31_8b
* S20: s15_g2pilot_m0v25_qwen25_7b, s15_g2pilot_m0v25_qwen3_8b_nothink (wording review required: two or more models)
* S26: s15_g2pilot_m0v25_qwen25_7b, s15_g2pilot_m0v25_qwen3_8b_nothink (wording review required: two or more models)
* S27: s15_g2pilot_m0v25_llama31_8b, s15_g2pilot_m0v25_qwen25_7b, s15_g2pilot_m0v25_qwen3_8b_nothink (wording review required: two or more models)
* S30: s15_g2pilot_m0v25_qwen3_8b_nothink
* S72: s15_g2pilot_m0v25_qwen25_7b, s15_g2pilot_m0v25_qwen3_8b_nothink (wording review required: two or more models)
* S92: s15_g2pilot_m0v25_qwen25_7b, s15_g2pilot_m0v25_qwen3_8b_nothink (wording review required: two or more models)

Audit sample: `audit_sample.jsonl` (seed 197, up to 10 records per model and stratum) for the main session to read.
