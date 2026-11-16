# M0 v2.2: M0 v2.1 revised after its LLM panel review

Data role: **EXPLORATION**. Status: **solver-certified; all 11 structures ADMITTED by the qualified Claude judge (prompt v3) with no sentence rated artificial (M0 v2.1 review, J15.1-038; S20, S26, S92 re-reviewed, J15.1-039); not yet reviewed by GPT or a human**.

411 cells on 11 structures (instance 0 of each), a gold solving trace for every cell. Built by `scripts/v2/s195_build_m0_v22.py` (the M0 v2.1 builder run with `src/physmon/benchmark/v2/roles_m0v22.py`). `m0_v21` is unchanged and is the record of the review (`docs/validation/v2/llm_panel/admission_m0v21/`).

## What changed against M0 v2.1, and why

* **S02 rejected and replaced** (not in M0 v2.2): panel REJECT (ANSWER_AMBIGUOUS, high flag) on M0 v2.1: an extra release distance cannot be stated without contradicting 'released from rest ... slides 4 m ... after it has slid that distance'; replaced, not rewritten.
* **S92 pair 1 R** reworded: the judge's high flag (the question's present tense left open whether the later liquid applies, and the sentence did not say the same string held the cube in this tank).
* **S20 and S26 pair 0**: the co-present object is a lamp that lights the object (S20) and a camera that films the interface (S26), replacing a stool pushed and a desk lamp tilted, which blind raters called pointless actions (rated artificial).

D cells by kind: {'other_object_same_scene': 36, 'same_object_other_event': 30}. By stratum: {'C': 42, 'D': 66, 'K': 24, 'K_out': 4, 'N': 22, 'R': 66, 'none': 11, 'support': 176}.

## What has not been done

No GPT or human review yet (evidence class LLM_PANEL, one judge); no model has seen the cells.
