# Dataset admission standard (G1 item; frozen with the G1 freeze)

Written 2026-11-14 under the user's delegation (2026-11-13, 2026-11-14). Operationalises the plan of record v2.2
(`docs/proposals/PhysMon_Research_v2.tex`, section "Dataset plan", admission items 1-6, and the v2.2 paragraphs "Two
kinds of disconnection", "Paired phrasings and consequence-free wording", "Familiarity, hygiene and gold traces").
Applies to every structure counted towards M250, M500 or a possible M1000, and to the 16 non-physics control
structures. M0 v2 (design-validation pilot, EXPLORATION) is held to the same standard except item 5 (it may be admitted
on the Claude judge alone, labelled so).

A structure is ADMITTED only when every check below passes and its record says so. A structure that fails is
REPLACED, never edited after any model output on it exists. Planning: 1.3-1.5 generated per admitted structure.

## 1. Identity and independence (machine)
| # | Check | Pass condition |
|---|---|---|
| 1.1 | New template cluster and symbolic program | `template_cluster_id` and `symbolic_program_hash` unique against dataset v1, DECOY-v1, every admitted v2 structure and the EPC pool |
| 1.2 | Overlap detectors (P3.5) | no near-duplicate under the text, program and value-signature detectors; the nearest neighbour and its score are recorded |
| 1.3 | Provenance | `created_by`, generator version, spec hash, author agent, date; `scripts/check_provenance_consistency.py` passes |

## 2. Certification (machine; solver)
| # | Check | Pass condition |
|---|---|---|
| 2.1 | Typed dependency graph | every input, intermediate and target node typed with units; dimension check passes on every relation |
| 2.2 | R and D cells | certified y*_R(z) and y*_D(z) at the three study values and two held-out values; R separated from D by more than the loosest tolerance at every value; differing answer-token spans |
| 2.3 | C cells (where feasible) | symbolic cancellation (dy*/dq = 0 identically) plus numeric invariance; the intermediate relations containing q listed |
| 2.4 | K cells (where feasible) | regime predicate true at every study value; counter-regime value documented; K_out feasibility recorded with a reason; K_out cells certified where feasible |
| 2.5 | Misuse curves and placebo | every misuse curve and the placebo value separated from the gold and from each other by more than the loosest tolerance at two or more of three values; inseparable pairs recorded as confounded |
| 2.6 | Mutation tests (P3.3) | the certifier rejects every planted mutation, including broken cancellation (C) and out-of-regime values (K) |
| 2.7 | Gold traces | one per cell, rendered from the graph; last value equals the cell gold (relative 1e-9) |
| 2.8 | Feasibility | infeasible strata recorded with reason, never imputed; "complete" = R and D at three values in two phrasing pairs |

## 3. Wording (machine, then judge)
| # | Check | Pass condition |
|---|---|---|
| 3.1 | Pairs | two phrasing pairs (r0,d0), (r1,d1); same frame, numeral and unit within a pair; differ only in the attachment phrase; word counts within 3 |
| 3.2 | D kinds | d0 co-present (other object, same scene, same time); d1 other event of the target object; `d_rationale` for each |
| 3.3 | Lexicons | every phrasing `marker_free` and `consequence_free` (lexicons frozen with G1; additions only by a dated amendment before any model run on the affected items) |
| 3.4 | Conditions untouched | no added sentence changes a stated condition (initial state, regime, model) |
| 3.5 | Value hygiene | no study value equals a displayed input numeral; digit overlap with inputs and gold recorded |
| 3.6 | Supporting cells | proximity cells carry their tolerance status per grading view; exact-match cells flagged `source_ambiguous` |

## 4. Gradeability (machine)
| # | Check | Pass condition |
|---|---|---|
| 4.1 | Grading dry run | the gold of every cell, written in each of the three declared answer formats, grades CORRECT under every grading view |
| 4.2 | Foil dry run | every misuse value and the placebo grade NOT CORRECT under the primary view |

## 5. Physics validation (qualified LLM panel, protocol v3)
| # | Check | Pass condition |
|---|---|---|
| 5.1 | Panel review of every phrasing | the base problem and each role sentence reviewed by both qualified judges (Claude, GPT-6.1 Sol; Gemini when available) under `judge_prompt_v3.md`, blind pass then claims pass |
| 5.2 | Verdict | both judges `valid` with no `high` flag; any `high` flag from either judge = REJECTED (no majority override); disagreement on a `medium` flag is recorded |
| 5.3 | Rounding guard | where GPT accepts a displayed value with fewer significant figures than the inputs, Claude's verdict on precision decides (J15.1-029: GPT's weak point) |
| 5.4 | Label | `LLM_PANEL_VALIDATED` with judge ids; never "expert-validated". The later human accuracy study samples these verdicts |

## 6. Naturalness and composition (judge and machine)
| # | Check | Pass condition |
|---|---|---|
| 6.1 | Blind naturalness | each role sentence rated by a judge instance that sees only the problem plus the sentence (no role label): `natural` or `slightly_artificial`; `artificial` = rewrite before admission (allowed: no model output exists yet) |
| 6.2 | Familiarity | each C quantity tagged famous / standard / uncommon; at most half "famous" across the admitted set at each milestone |
| 6.3 | Composition (reported, not forced) | at least 10 domains, none above 25%; at least 20% upper-university or multi-step; C feasible in at least 50% and K in at least 30% of new structures |

## 7. Records
Every admitted structure has `admission.json` with the result of every check above (pass/fail, values, versions,
judge ids and verdicts) and the data role assigned by lineage before any model output (`EXPLORATION`,
`INTERNAL_CONFIRMATION`, shadow, `ADVERSARIAL_CHALLENGE`). The milestone report lists admitted, rejected (with the
failing check) and replaced structures.
