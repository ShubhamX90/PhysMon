# M0 v2.1: M0 v2 revised after the LLM panel review

Data role: **EXPLORATION**. Status: **agent-authored, solver-certified, NOT yet reviewed by the LLM panel (and not yet reviewed by a human)**.

454 cells on 12 structures (instance 0 of each), a gold solving trace for every cell, a certificate for every structure. Built by `scripts/v2/s192_build_m0_v21.py` from `src/physmon/benchmark/v2/roles_m0v21.py` (which reuses the M0 v2 specs for everything it does not change); rebuild with the same command for identical files (the builder refuses to overwrite). `m0_v2` is unchanged and stays as the record of the review that led here (`docs/validation/v2/llm_panel/admission_m0v2/`).

## What changed against M0 v2, and why (plan revision v2.2, section G)

1. **No undone events (G1).** `same_object_undone_event` is withdrawn: a change applied to the target and then reversed acts on the target and cancels (stratum C), so it is not a disconnected sentence. Pair 1 of every structure is now a genuine other event of the target object that leaves no state behind (`same_object_other_event`: history in an earlier experiment, or an event after the stated process, for example a jug emptied into the water after the heating ended). For S72 only, no honest same-object event exists for an energy quantity, so pair 1 puts the energy on a second co-present object of a different type (an alpha particle; `other_object_same_scene` with `d_kind_note`). The certificate rejects any D or N phrasing with a reversal pattern (`again`, `back`, `removed`, `taken out`, `cut out`, `loses`, `lets it ... back`, ...), any co-present D that names the target, and any same-object D without a time anchor away from the stated situation.
2. **Scene integration (G2).** The co-present object of d0 is introduced by one number-free clause (the scene clause) appended to the base context of EVERY cell of the structure (no cue, N, R, D, C, K, K_out and supporting), so the pair-0 D sentence refers to an object that is already in the scene, as R refers to the target. The clause is on every row (`scene_clause`, `scene_object_rationale`). The base problem is the October problem with the clause before the question and nothing else; the base gold and every gold of the role cells are unchanged (the builder and the tests check this).
3. **Wording fixes (G4).** S27 r1 (time marker 'Afterwards', same R wiring), S07 K ('broken again' reworded), S13 (the cord is stated light in every sentence), S55 (the g/mol to kg/mol conversion is stated in the relation listed to the panel), S02 R0 (no meta-wording) and the S02 quantity label.
4. **Naturalness rewrites.** Every D, N and R sentence was rewritten from the panel's reasons as a plausible part of the scene; the pair rules hold (same frame, numeral and unit; attachment-only difference except S02 p0 and S26 p0, declared with reasons; word counts within 3; marker- and consequence-free; value hygiene). C and K sentences are those of M0 v2 except S07's k0.

D cells by kind: {'other_object_same_scene': 39, 'same_object_other_event': 33}. K_out exists for S07 only.

## Files

As in M0 v2 (`cells.jsonl`, `traces.jsonl`, `certificates.json`, `manifest.json`), with the extra row fields `m0_version`, `scene_clause`, `scene_object_rationale` and `d_kind_note` (pair-1 D and N rows of a structure whose pair 1 is co-present).

## Reading `source_ambiguous`

True on these rows only (by design): {'nongov_convertible_unit_same_magnitude': 12, 'nongov_same_unit_exact': 12}.

## Counts

By family: {'role_by_value': 262, 'supporting': 192}. By stratum: {'C': 48, 'D': 72, 'K': 30, 'K_out': 4, 'N': 24, 'R': 72, 'none': 12, 'support': 192}.

Conditions that could not be built (never replaced by a nonsensical prompt; reasons in the certificates): K_out x4, before_context x24.

## What has not been done

No LLM-panel or human review of M0 v2.1 yet, and no model has seen the cells. Panel packets are built by `scripts/v2/s193_m0v21_panel_packets.py`.
