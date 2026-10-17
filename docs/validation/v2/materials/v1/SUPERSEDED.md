# v1 is superseded by v2 (2026-10-17)

The files in this directory are kept unchanged as evidence of what was reviewed. Use `../v2/` instead.

Why: the user's walkthrough of the 33-item planted-defect bank (`bank_confirmation_2026-10-17.json`) found three problems in
these materials: Q009 deleted "from rest" from "dropped from rest" (not a defect), Q002 and Q004 appended a note whose value equals
the target's own quantity (ambiguity, not contradiction), and Q017, Q057 and Q069 stored only the unchanged rendering 0 so the
edit was invisible. v2 fixes these and keeps the other 30 reviewed items identical (`../v2/bank_review_status.json`).
Journal: `docs/journal/stage14/14.5_validator_qualification.md` J14.5-012.
