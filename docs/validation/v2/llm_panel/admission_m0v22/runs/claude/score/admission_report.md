# M0 v2.2 changed items (Claude judge)

Applies admission standard 5.2-5.3 (physics, qualified LLM panel) and 6.1 (naturalness) to the panel's reviews.
Judges: claude. Naturalness raters: claude. Judges required per structure: 1.

A structure is ADMITTED only if every judge calls it valid with no high flag. Missing reviews make it INCOMPLETE (a missing review is not a verdict). A sentence rated artificial must be rewritten, and so must a D sentence rated more than one level worse than its R twin (natural > slightly_artificial > artificial; standard 6.1 as amended 2026-11-15).

Structures: ADMIT 3

## M0V22-S20: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The claimed quantity label 'a shift of a stand' is applied to the lamp sentences too, though the lamp is not described as a stand; this is a cosmetic labelling issue that does not affect any stratum or answer.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N0', 'D0', 'R1', 'N1', 'D1']

## M0V22-S26: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite ['R1'], pending 0, slightly artificial ['N0', 'N1', 'R0', 'D1', 'D0']
  - REWRITE R1 (R): claude: Tilting the laser after the 40-degree incidence angle was set contradicts the stated angle, making the scene incoherent as written.

## M0V22-S92: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): TBB34/T1B91 say a liquid 'now fills' the second tank that the base calls empty, and T98F1/T70A2 leave implicit that the original liquid was restored after the earlier experiment; both read naturally as stated but are slightly awkward wording.
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['N0', 'D0', 'R1', 'R0', 'N1', 'D1']

