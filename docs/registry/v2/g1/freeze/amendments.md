# Dated amendments to frozen G1 documents

Each entry: date, document and section, the change, the reason, what data existed when it was written.

## A1 · 2026-11-19 · `dataset_admission_standard.md` section 5 (new check 5.3b)

**Change.** New check 5.3b (a judge-error guard, parallel to 5.3): a `high` flag of type `rendering_not_minimal` (or any flag whose
stated reason is that a sentence lacks the number or unit of its twin) on a **numeral-free control (N) sentence** is a judge error,
because the N sentence is numeral-free by design and its pass-2 claim says so (`numeral_free_twin_of` plus the note "This sentence
is the numeral-free control by design: it deliberately carries no number; the matching D sentence carries the number."). Such a
flag is recorded, does not count under 5.2, and the other qualified judge's verdict on that sentence decides. Every other flag of
the same judge on the item still counts.

**Reason.** The GPT-6.1 Sol judge raised exactly this flag on M0 v2.2 S72 (J15.1-046) and on M0 v2.3 S13 and S72 (J15.1-048),
after the explicit note was added; it did not raise it on the other nine structures with identical N designs. The frozen judge
prompt v3 asks that "variants of the same quantity preserve its number and unit"; the N control is by construction not such a
variant. Without this guard every structure would depend on whether GPT happens to apply that sentence to its N twin.

**Data when written.** Panel reviews of M0 v2.2 and v2.3 (both judges). No model output exists on any M0 v2.x cell. The guard is
applied to every item from M0 v2.3 on, and reported in every admission report that uses it (`s190b` lists the flag as
"5.3b judge error"). The qualification results (J15.1-029) are unaffected: bank v5 has no N sentence.
