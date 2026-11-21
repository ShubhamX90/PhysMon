"""Grammar guard for the M250 exploration sources: no N (vague, number-free) sentence and no rendered role sentence may carry an
ungrammatical fill such as "by a further a few kelvin". Covers every module in the builder's SOURCES list (roles_m0v25 read-only)."""

from __future__ import annotations

import importlib
import re

import pytest

from physmon.benchmark.v2 import rolevalue_v2 as r2

MODULES = (
    "roles_m0v25", "roles_m250_a", "roles_m250_b", "roles_m250_c", "roles_m250_d", "roles_m250n_mech", "roles_m250n_em",
    "roles_m250n_thermo", "roles_m250n_waves", "roles_m250n_modern", "roles_m250n_extra", "roles_m250n_circ", "roles_m250n_qastro",
    # repair round 1 (J15.1-059)
    "roles_m250r1_a", "roles_m250r1_b", "roles_m250r1_c", "roles_m250r1_d", "roles_m250r1n_mech", "roles_m250r1n_em",
    "roles_m250r1n_thermo", "roles_m250r1n_waves", "roles_m250r1n_modern", "roles_m250r1n_extra", "roles_m250r1n_circ",
    "roles_m250r1n_qastro",
)
BANNED_FILLS = ("further a little", "another a little", "a further a ", "another a ", "by a further a", "a further an ")
# 'a' before a number read with a vowel sound (eight, eleven, eighteen, eighty)
A_BEFORE_VOWEL_NUMBER = re.compile(r"\ba (8|11|18|80)\d*\b")
# 'a' before a word starting with a vowel letter, except words read with a consonant sound
A_VOWEL_WORD = re.compile(r"\ba ([aeiou]\w*)", re.IGNORECASE)
A_VOWEL_OK = re.compile(r"^(uni\w*|use\w*|usual\w*|one\w*|once|eu\w*|ubiquit\w*|ultra\w*\b)", re.IGNORECASE)
A_VOWEL_OK_EXACT = {"unit", "unity", "u", "ohm", "ohmic"}


def _specs(module):
    return getattr(module, "SPECS", None) or module.ROLE_SPECS


def _problems(sentence: str) -> list[str]:
    low = sentence.lower()
    found = [b for b in BANNED_FILLS if b in low]
    if A_BEFORE_VOWEL_NUMBER.search(sentence):
        found.append("a before vowel-sound number")
    for match in A_VOWEL_WORD.finditer(sentence):
        word = match.group(1).lower()
        if word in A_VOWEL_OK_EXACT or A_VOWEL_OK.match(word):
            continue
        found.append(f"a before vowel word '{match.group(0)}'")
    return found


@pytest.mark.parametrize("name", MODULES)
def test_no_ungrammatical_fill_in_rendered_sentences(name):
    module = importlib.import_module(f"physmon.benchmark.v2.{name}")
    for sid, spec in sorted(_specs(module).items()):
        structure = module.structure(sid)
        for pair in spec.pairs:
            n = r2.pair_sentence(pair, "D", None, spec.unit)
            assert not _problems(n), (name, sid, n, _problems(n))
            assert n[0].isupper() and n.endswith("."), (name, sid, n)
        for cell in r2.role_cells_v2(structure, spec, 0, include_heldout=True):
            if cell.sentence:
                assert not _problems(cell.sentence), (name, sid, cell.sentence, _problems(cell.sentence))
