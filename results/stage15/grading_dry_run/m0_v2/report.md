# Grading dry run: m0_v2

Cells: 454; cells with foils or placebo: 298 (1380 values); source-ambiguous cells: 24.
Unexpected failures: **0**; source-ambiguous exemptions: 8.

| check family : view | checks run |
|---|---|
| foil:declared | 2760 |
| gold:convertible | 1362 |
| gold:declared | 1362 |
| gold:rel1pct | 1362 |
| gold_alt_unit:convertible | 4530 |
| gold_alt_unit:rel1pct | 4530 |
| support_tolerance_status:convertible | 84 |
| support_tolerance_status:declared | 84 |
| support_tolerance_status:rel1pct | 84 |

Gold formats required correct under every view: plain_full, plain_4sf, sci_4sf. Alternative units are required correct under `convertible` and `rel1pct` only. Foils and the placebo must not be correct under `declared`.

## Unexpected failures
None.

## Source-ambiguous exemptions
- S72-i0:D:z0:d0:after_context | foil:add:mc2:plain_4sf | declared | `100.1 pm` graded correct
- S72-i0:D:z0:d1:after_context | foil:add:mc2:plain_4sf | declared | `100.1 pm` graded correct
- S72-i0:D:z1:d0:after_context | foil:add:mc2:plain_4sf | declared | `100.1 pm` graded correct
- S72-i0:D:z1:d1:after_context | foil:add:mc2:plain_4sf | declared | `100.1 pm` graded correct
- S72-i0:D:z2:d0:after_context | foil:add:mc2:plain_4sf | declared | `100.1 pm` graded correct
- S72-i0:D:z2:d1:after_context | foil:add:mc2:plain_4sf | declared | `100.1 pm` graded correct
- S72-i0:D:z1:d0:after_context:instr_relevance | foil:add:mc2:plain_4sf | declared | `100.1 pm` graded correct
- S72-i0:D:z1:d1:after_context:instr_relevance | foil:add:mc2:plain_4sf | declared | `100.1 pm` graded correct
