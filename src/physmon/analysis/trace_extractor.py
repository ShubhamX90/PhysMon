"""The frozen rule-based trace extractor for hypothesis H4, "readout contamination" (G1 decision 12; version h4-v1).

H4 asks, among disconnected (D) samples whose FINAL answer matches an attributed misuse curve f_h(z), whether the reasoning trace
had already computed the certified gold y*_D(z) (contamination at readout) or computed the misuse value itself (a selection
failure in the computation). The trace-correct share TC = x / n feeds `scorecard._h4` through `ScorecardInputs.trace`.

No LLM judge is involved (plan "Outcomes": rule-based, frozen, tested on synthetic traces before G3). The rules below are the
whole extractor; `extractor_fingerprint()` hashes every pattern and constant, and `tests/v2/test_trace_extractor.py` pins that
hash to `TRACE_EXTRACTOR_VERSION`. CHANGING ANY RULE AFTER A G3 RECORD EXISTS REQUIRES A NEW VERSION STRING (and a new pinned
fingerprint); `EXTRACTOR_FROZEN` stays True only while the synthetic and real-trace suites pass.

Rules (all choices where the specification was ambiguous take the conservative option and are listed in the test module docstring):

R1  Trace region. Thinking models: the thinking block plus the text after the end-of-thinking marker that precedes the first
    final-answer line. Other models: the text before the first final-answer line. The final-answer line itself (contract line,
    or the same line after LaTeX/Markdown recovery) and anything after it are excluded. Without a final-answer line the whole
    generation is the region. An empty region is NO_TRACE.
R2  Normalisation. Markdown emphasis, `$`, `\\( \\)`, LaTeX spacing, `\\text{}`/`\\mathrm{}`/`\\boxed{}` wrappers, `\\frac`,
    `\\sqrt`, `\\approx`, `\\times`, scientific notation (`4.5 \\times 10^{-4}`, `4.5 * 10^-4`), thousands commas and the unicode
    minus are turned into plain text; positions are those of the normalised text.
R3  Candidate statements of the target:
    (a) a number followed by a unit that the dimension registry knows and that converts to the target unit (same dimension;
        a unit of another dimension, an unknown unit or `1` is never a target statement and the value is never unit-stripped);
    (b) a number with no unit that is the last segment of an equation chain whose head names the target (a target phrase,
        "the speed of the block is 5.39", or a target symbol, "v = 12/3 = 5.39").
    Excluded: a statement equal, in the same dimension, to a numeral of the problem text or to q (kept only when it is named
    as the target and is the gold or a misuse value, as the copy of q is); any statement
    in a sentence that discards the value ("we discard t = 0"); any statement in a unit identity (`1 J = 1000 mJ`).
R4  The extracted value is the LAST candidate statement (by position) in the region.
R5  Classification (tolerance of the declared view: half a unit in the last printed place, converted with the unit ratio, and
    within 0.5% of the target; view `rel1pct`: within 1%): TRACE_CORRECT, TRACE_MISUSE(h), TRACE_AMBIGUOUS, TRACE_OTHER,
    NO_TRACE_VALUE, NO_TRACE. Every record keeps all matches.
R6  TC: among D samples whose final answer is a UNIQUE_MATCH to an attributed, unconfounded misuse curve (and is not itself
    within tolerance of the gold), x = TRACE_CORRECT and n = TRACE_CORRECT + TRACE_MISUSE + TRACE_OTHER. TRACE_AMBIGUOUS,
    NO_TRACE_VALUE and NO_TRACE are reported with counts and excluded from n; a sensitivity analysis beside it counts them as
    not-correct (same x, n enlarged by them).
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from physmon.analysis import rolevalue_stats as rvs
from physmon.benchmark import reasoning_contract_v2 as rc2
from physmon.scoring import grading_views as gv
from physmon.scoring import unit_convertible as uc
from physmon.scoring import v2_scorer as vs

TRACE_EXTRACTOR_VERSION = "h4-v1"
EXTRACTOR_FROZEN = True  # guarded by tests/v2/test_trace_extractor.py; never flip it without a new version string

CLASSES = ("TRACE_CORRECT", "TRACE_MISUSE", "TRACE_AMBIGUOUS", "TRACE_OTHER", "NO_TRACE_VALUE", "NO_TRACE")
CLASSIFIABLE = ("TRACE_CORRECT", "TRACE_MISUSE", "TRACE_OTHER")
REL_TOL_COARSE = vs.COARSE_REL_TOL
REL_TOL_1PCT = gv.REL_1PCT
ALLOWED_SUBSCRIPTS = ("f", "final", "max", "avg", "rms", "terminal", "abs", "eq", "total", "net", "new", "out", "2")

# interrogative / head noun -> (target phrases, target symbols); the first key found after the interrogative word is used
_LEXICON: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "angular acceleration": (("angular acceleration",), ("alpha", "α")),
    "acceleration": (("acceleration",), ("a",)),
    "speed": (("speed",), ("v",)),
    "velocity": (("velocity",), ("v",)),
    "current": (("current",), ("I",)),
    "voltage": (("voltage", "potential difference"), ("V",)),
    "energy": (("energy",), ("E", "U", "K")),
    "power": (("power",), ("P",)),
    "period": (("period",), ("T",)),
    "frequency": (("frequency",), ("f",)),
    "force": (("force",), ("F",)),
    "pressure": (("pressure",), ("P", "p")),
    "tension": (("tension",), ("T",)),
    "work": (("work",), ("W",)),
    "charge": (("charge",), ("Q", "q")),
    "radius": (("radius",), ("r", "R")),
    "height": (("height",), ("h", "H")),
    "wavelength": (("wavelength",), ("lambda", "λ")),
    "temperature": (("temperature",), ("T",)),
    "how far": (("distance",), ("d", "x", "s")),
    "distance": (("distance",), ("d", "x", "s")),
    "how long": (("time", "duration"), ("t",)),
    "time": (("time", "duration"), ("t",)),
    "rate": (("rate",), ()),
}


# --- context --------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class TraceContext:
    """What the extractor needs about one cell (the target and what must not be mistaken for it)."""

    gold: float  # y*_D(z), in `gold_unit`
    gold_unit: str
    misuse: Mapping[str, float]  # foil name -> f_h(z), in `gold_unit`
    target_phrases: tuple[str, ...] = ()
    target_symbols: tuple[str, ...] = ()
    prompt_numerals: tuple[tuple[float, str | None], ...] = ()  # (value, unit) of every numeral of the problem text
    q: tuple[float, str | None] | None = None  # the irrelevant quantity's own value and unit
    view: str = "declared"


def normalise_view(view: str) -> str:
    out = view[6:] if view.startswith("grade_") else view
    if out not in gv.VIEWS:
        raise ValueError(f"unknown grading view {view!r}; expected one of {gv.VIEWS}")
    return out


_QUESTION_START = re.compile(r"\b(?:what|how|at what|with what|by how)\b")
_LEADING = re.compile(r"^(?:at what|with what|by how many|by how much|what|how much|how many)\s+"
                      r"(?:(?:is|are|does|do|did)\s+)?(?:(?:the|a|an)\s+)?(?:(?:magnitude|size|value) of\s+(?:the\s+)?)?")
_HEAD_STOP = re.compile(r"\b(?:of|between|through|across|at|from|in|on|that|which|whose|after|before|for|with|does|do|is|are|can|"
                        r"must|will|has|have|equals|measured)\b|[,?]")


def derive_target_terms(question: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Default target phrases and symbols from the question sentence: the lexicon key inside the head noun phrase (the words
    after the interrogative up to the first preposition or verb). An empty result means no unitless statement can be read."""

    low = question.lower()
    m = _QUESTION_START.search(low)
    tail = low[m.start():] if m else low
    for key in ("how far", "how long"):
        if tail.startswith(key):
            return _LEXICON[key]
    head = _LEADING.sub("", tail, count=1)
    stop = _HEAD_STOP.search(head)
    chunk = head[:stop.start()] if stop else head
    best: tuple[int, str] | None = None
    for key in _LEXICON:
        if key.startswith("how"):
            continue
        i = chunk.find(key)
        if i >= 0 and (best is None or len(key) > len(best[1]) or (len(key) == len(best[1]) and i < best[0])):
            best = (i, key)
    return _LEXICON[best[1]] if best else ((), ())


def context_from_row(row: Mapping[str, Any], cell: rvs.Cell | None = None, view: str = "declared",
                     target_phrases: Sequence[str] | None = None, target_symbols: Sequence[str] | None = None) -> TraceContext:
    """A context from a dataset cell row (`prompt`, `gold_unit`, `gold_value`, `foils`, `role.value`/`role.unit` for q)."""

    prompt = str(row.get("prompt") or "")
    question = prompt.strip().split("\n")[-1] if prompt else ""
    phrases, symbols = derive_target_terms(question)
    role = row.get("role") or {}
    q = (float(role["value"]), role.get("unit")) if role.get("value") is not None else None
    foils = dict(cell.foils if cell is not None else (row.get("foils") or {}))
    gold = cell.gold if cell is not None else float(row["gold_value"])
    return TraceContext(gold, str(row["gold_unit"]), {k: float(v) for k, v in foils.items() if k not in rvs.NOT_MISUSE},
                        tuple(target_phrases) if target_phrases is not None else phrases,
                        tuple(target_symbols) if target_symbols is not None else symbols,
                        tuple(prompt_numerals(prompt)), q, normalise_view(view))


# --- normalisation ----------------------------------------------------------------------------------------------------------

_WRAP = re.compile(r"\\(?:text|mathrm|textrm|textbf|mathbf|operatorname|boxed|mbox|textit|mathit)\s*\{([^{}]*)\}")
_FRAC = re.compile(r"\\[dt]?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}")
_SQRT = re.compile(r"\\sqrt\s*\{([^{}]*)\}")
_SCI = re.compile(r"(?P<m>\d+(?:\.\d+)?)\s*(?:\\times|×|\*|x|\\cdot|·)\s*10\s*\^\s*\{?\s*(?P<e>[-+]?\d+)\s*\}?")
_SCI_PURE = re.compile(r"(?<![\d.\w])10\s*\^\s*\{?\s*(?P<e>[-+]?\d+)\s*\}?")
_SPACING = re.compile(r"\\(?:,|;|:|!|quad|qquad|ldots|dots)|\\ |~")
_THOUSANDS = re.compile(r"(?<![\d.])(\d{1,3})((?:,\d{3})+)(?![\d])")


def normalise_trace(text: str) -> str:
    """R2: plain text with the same order as the source; positions are those of the returned string."""

    out = text.replace("<think>", "\n").replace("</think>", "\n")
    out = out.replace("**", "").replace("__", "").replace("`", "")
    out = out.replace("\\\\", "\n")
    for token in ("\\(", "\\)", "\\[", "\\]", "$"):
        out = out.replace(token, " ")
    out = re.sub(r"\\(?:overline|bar)\s*\{[^{}]*\}", "", out)  # repeating-decimal bars: \overline{6} is dropped
    out = out.replace("\\ldots", "...").replace("\\dots", "...")
    out = _SPACING.sub(" ", out)
    out = (out.replace("\\approx", "≈").replace("\\simeq", "≈").replace("\\times", "×").replace("\\cdot", "*")
           .replace("\\Rightarrow", "\n").replace("\\Longrightarrow", "\n").replace("\\implies", "\n")
           .replace("⇒", "\n").replace("\\left", "").replace("\\right", "").replace("\\mu", "μ")
           .replace("\\Omega", "Ω").replace("\\%", "%").replace("−", "-").replace("\\leq", "≤").replace("\\geq", "≥"))
    out = re.sub(r"\^\s*\{?\s*\\circ\s*\}?", " deg ", out)
    previous = None
    while previous != out:  # nested wrappers and fractions
        previous = out
        out = _WRAP.sub(lambda m: m.group(1), out)
        out = _FRAC.sub(lambda m: f"({m.group(1).strip()})/({m.group(2).strip()})", out)
        out = _SQRT.sub(lambda m: f"sqrt({m.group(1)})", out)
    out = _SCI.sub(lambda m: f"{m.group('m')}e{m.group('e')}", out)
    out = _SCI_PURE.sub(lambda m: f"1e{m.group('e')}", out)
    out = re.sub(r"\^\s*\{\s*([-+]?\d+)\s*\}", r"^\1", out)
    out = re.sub(r"_\s*\{\s*([A-Za-z0-9]+)\s*\}", r"_\1", out)
    out = out.replace("{", "").replace("}", "")
    out = _THOUSANDS.sub(lambda m: m.group(1) + m.group(2).replace(",", ""), out)
    out = re.sub(r"(?<=[A-Za-z])\s+per\s+(?=[A-Za-z])", "/", out)
    out = re.sub(r"(?<=[A-Za-zμΩ])\s+/\s+(?=[A-Za-zμΩ])", "/", out)
    out = re.sub(r"\\([A-Za-z]+)", r"\1", out)
    return re.sub(r"[ \t]+", " ", out)


# --- numbers and units ------------------------------------------------------------------------------------------------------

_NUM = re.compile(r"(?<![A-Za-z_\d.^])(?P<s>[-+](?=\d))?(?P<n>\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)")
_UNIT_TOKEN = re.compile(r"[ ]?(?P<u>[A-Za-zμΩ°%][^\s,;:()=≈\n]*)")
_SIGN_OK_BEFORE = " (=≈:,\n"
_VARIABLE_AFTER = re.compile(r"\s+(?:[A-Za-zα-ωΑ-Ω](?![A-Za-z])|\()")


@dataclass(frozen=True)
class Number:
    text: str  # as printed, without sign
    value: float
    start: int
    end: int  # end of the number itself
    unit_raw: str | None
    unit: str | None  # a registry unit, or None
    stmt_end: int  # end of number plus unit


def resolve_unit(token: str) -> str | None:
    """A registry unit for a token written after a number, or None (also for the unit `1`)."""

    from physmon.benchmark.v2 import dimensions as dm

    base = token.rstrip(".,;:!?)]-").lstrip("(")
    if not base:
        return None
    for candidate in (base, base.replace("·", "*")):
        norm = uc.canonical_unit(candidate)
        if norm in dm.UNITS and norm != "1":
            return norm
    parts = []
    for part in vs.normalise_unit(base).split("/"):
        m = re.fullmatch(r"([A-Za-zμΩ]+)(\^-?\d)?", part)
        word = m.group(1) if m else part
        alias = uc.ALIASES.get(word.lower()) if len(word) > 1 else None
        parts.append((alias or word) + (m.group(2) or "" if m else ""))
    norm = uc.canonical_unit("/".join(parts))
    return norm if norm in dm.UNITS and norm != "1" else None


def scan_numbers(text: str) -> list[Number]:
    """Every number of the normalised text with the unit that follows it, when one does."""

    found: list[Number] = []
    for m in _NUM.finditer(text):
        sign = m.group("s")
        prev = text[m.start() - 1] if m.start() > 0 else "\n"
        negative = sign == "-" and prev in _SIGN_OK_BEFORE
        start = m.start("n") - (1 if sign and negative else 0)
        value = float(m.group("n")) * (-1 if negative else 1)
        unit_raw = unit = None
        stmt_end = m.end()
        nxt = text[m.end():m.end() + 1]
        if nxt in (" ", "") or nxt.isalpha() or nxt in "°%μΩ":
            u = _UNIT_TOKEN.match(text, m.end())
            if u:
                token = u.group("u")
                resolved = resolve_unit(token)
                if resolved is not None and len(token.rstrip(".,;:!?)]")) == 1 and _VARIABLE_AFTER.match(text, u.end()):
                    resolved = None  # "8 m L^2": a coefficient times a variable, not 8 metres
                if resolved is not None:
                    unit_raw, unit, stmt_end = token, resolved, u.end()
        found.append(Number(m.group("n"), value, start, m.end(), unit_raw, unit, stmt_end))
    return found


def prompt_numerals(prompt: str) -> list[tuple[float, str | None]]:
    """Value and registry unit of every numeral of the problem text (used to ignore a restated input)."""

    return [(n.value, n.unit) for n in scan_numbers(normalise_trace(prompt))]


def _ratio(unit: str | None, gold_unit: str) -> float | None:
    if unit is None:
        return 1.0
    return uc.conversion_ratio(unit, gold_unit)


def within_tolerance(text: str, value: float, ratio: float, target: float, view: str) -> bool:
    """The grading view's rule for a trace value written `text` in a unit with factor `ratio` to the target's unit.

    `declared` and `convertible` views: the declared rule (half a unit in the last printed place, scaled by `ratio`, and within
    0.5% of the target) OR within the strict relative tolerance of 0.1% (`v2_scorer.STRICT_REL_TOL`): a value printed to many
    digits carries the rounding noise of earlier intermediates, which the half-unit rule would reject. `rel1pct`: within 1%.
    """

    converted = value * ratio
    error = abs(converted - target)
    scale = max(abs(target), 1e-300)
    if view == "rel1pct":
        return error <= REL_TOL_1PCT * scale * (1 + 1e-9)
    half = vs.half_unit_in_last_place(text) * ratio
    return (error <= half * (1 + 1e-9) and error <= REL_TOL_COARSE * scale) or error <= vs.STRICT_REL_TOL * scale * (1 + 1e-9)


# --- statements -------------------------------------------------------------------------------------------------------------

_CONNECTIVE = (r"(?:\s+(?:is|are|was|will be|would be|equals|equal to)|\s*[=≈:])"
               r"(?:\s+(?:approximately|about|roughly|around|equal to|≈|=|is))*\s*")
_TERMINATOR = re.compile(r"\n|;|\.(?=\s|$)|,(?=\s)|\s(?:and|but|so|which|where|since|because|therefore|thus|hence|when|while)\s")
_SPLIT_EQ = re.compile(r"\s*(?:=|≈)\s*")
_BARE = re.compile(r"(?P<s>[-+])?(?P<n>\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)")


@dataclass(frozen=True)
class Statement:
    text: str
    value: float
    unit: str | None
    value_in_gold_unit: float
    start: int
    end: int
    kind: str  # "unit" or "named_bare"
    named: bool
    context: str  # the surrounding text of the statement, for the record


def _heads(ctx: TraceContext, text: str) -> list[re.Match[str]]:
    out: list[re.Match[str]] = []
    if ctx.target_phrases:
        phrases = "|".join(re.escape(p) for p in sorted(ctx.target_phrases, key=len, reverse=True))
        out += list(re.finditer(rf"\b(?:{phrases})\b(?:\s+[A-Za-z'-]+){{0,5}}?{_CONNECTIVE}", text, re.I))
    if ctx.target_symbols:
        syms = "|".join(re.escape(s) for s in sorted(ctx.target_symbols, key=len, reverse=True))
        subs = "|".join(ALLOWED_SUBSCRIPTS)
        out += list(re.finditer(rf"(?<![A-Za-z0-9_\\])(?:{syms})(?:_(?:{subs})|2)?\s*(?:=|≈)\s*", text))
    return out


def _named_segments(ctx: TraceContext, text: str) -> list[tuple[int, int]]:
    """Spans (start, end) of the last segment of every equation chain whose head names the target."""

    spans: set[tuple[int, int]] = set()
    for m in _heads(ctx, text):
        rhs_start = m.end()
        term = _TERMINATOR.search(text, rhs_start)
        rhs_end = term.start() if term else len(text)
        rhs = text[rhs_start:rhs_end]
        cuts = [0]
        ends = []
        for sp in _SPLIT_EQ.finditer(rhs):
            ends.append(sp.start())
            cuts.append(sp.end())
        ends.append(len(rhs))
        last_start, last_end = cuts[-1], ends[-1]
        seg = rhs[last_start:last_end]
        stripped = seg.rstrip(" .…")
        while True:  # a trailing parenthetical remark
            trimmed = re.sub(r"\s*\([^()]*\)\s*$", "", stripped)
            if trimmed == stripped:
                break
            stripped = trimmed
        lead = len(stripped) - len(stripped.lstrip(" ≈"))
        for word in ("approximately ", "about ", "roughly ", "around "):
            if stripped.lstrip(" ≈").startswith(word):
                lead += len(word)
                break
        body = stripped[lead:]
        found = scan_numbers(body)
        if len(found) == 1 and found[0].start == 0 and found[0].stmt_end == len(body.rstrip()):  # exactly "number [unit]"
            spans.add((rhs_start + last_start + lead, rhs_start + last_start + len(stripped)))
    return sorted(spans)


_IDENTITY = re.compile(r"(?:[^=≈\n]*?[\s(:])?1(?:\.0+)?\s*[A-Za-zμΩ°][^\s=≈]*\s*")


def _conversion_identity(text: str, pos: int) -> bool:
    """The statement containing `pos` starts `1 <unit> = ...`: a unit identity, not a statement of the target."""

    cut = max(text.rfind("\n", 0, pos) + 1, 0)
    for term in _TERMINATOR.finditer(text, cut, pos):
        cut = term.end()
    m = _SPLIT_EQ.search(text, cut)
    end = _TERMINATOR.search(text, cut)
    if not m or (end and end.start() < m.start()):
        return False
    return bool(_IDENTITY.fullmatch(text[cut:m.start()]))


_REJECTED = re.compile(r"\b(?:discard|discarded|reject|rejected|ignore|ignored|extraneous|spurious|unphysical|invalid|impossible|"
                       r"not physical|not valid|cannot be)\b", re.I)


def _rejected(text: str, pos: int) -> bool:
    """The sentence containing `pos` says the value is discarded (`we discard t = 0`)."""

    left = max(text.rfind("\n", 0, pos), text.rfind(". ", 0, pos))
    ends = [e for e in (text.find("\n", pos), text.find(". ", pos)) if e >= 0]
    return bool(_REJECTED.search(text[left + 1:min(ends) if ends else len(text)]))


def _restated(value: float, unit: str, gold_unit: str, ctx: TraceContext) -> bool:
    sources = list(ctx.prompt_numerals) + ([ctx.q] if ctx.q is not None else [])
    for pv, pu in sources:
        if pu is None:
            continue
        ratio = uc.conversion_ratio(pu, unit)
        if ratio is not None and abs(pv * ratio - value) <= 1e-9 * max(abs(value), 1e-300):
            return True
    return False


def candidate_statements(trace: str, ctx: TraceContext) -> list[Statement]:
    """R3: every candidate statement of the target in the (raw) trace region, in order of position."""

    text = normalise_trace(trace)
    named = _named_segments(ctx, text)
    out: list[Statement] = []
    for n in scan_numbers(text):
        in_named = next(((a, b) for a, b in named if a <= n.start and n.end <= b), None)
        if n.unit is None and in_named is None:
            continue  # a unitless number is a statement only when a target-naming chain ends in it
        ratio = _ratio(n.unit, ctx.gold_unit)
        if ratio is None or _rejected(text, n.start):  # another dimension, or a discarded value
            continue
        if in_named is None and _conversion_identity(text, n.start):
            continue
        shown = n.text if n.value >= 0 else "-" + n.text
        if _restated(n.value, n.unit or ctx.gold_unit, ctx.gold_unit, ctx):
            # a restated input is no statement of the target, unless the model names it as the target AND it is the gold or
            # a misuse value (the copy of q is such a value)
            targets = [ctx.gold, *ctx.misuse.values()]
            if in_named is None or not any(within_tolerance(n.text, n.value, ratio, t, ctx.view) for t in targets):
                continue
        context = text[max(0, n.start - 40):min(len(text), n.stmt_end + 20)].replace("\n", " ")
        out.append(Statement(shown, n.value, n.unit, n.value * ratio, n.start, n.stmt_end,
                             "unit" if n.unit is not None else "named_bare", in_named is not None, context))
    return out


# --- trace region and classification ----------------------------------------------------------------------------------------

def _is_final_line(line: str) -> bool:
    if rc2._FINAL.search(line):
        return True
    return bool(rc2._RECOVER_LINE.search(rc2.normalise_markup(line)))


def trace_region(text: str, *, thinking_expected: bool, hit_token_limit: bool = False) -> str:
    """R1: the reasoning text before the first final-answer line (thinking block included for thinking models)."""

    comp = rc2.assess(text, hit_token_limit=hit_token_limit, thinking_expected=thinking_expected)
    thinking = comp.thinking_text.replace("<think>", "") if thinking_expected else ""
    lines = comp.answer_text.split("\n")
    cut = next((i for i, line in enumerate(lines) if _is_final_line(line)), len(lines))
    answer_part = "\n".join(lines[:cut])
    return (thinking + "\n" + answer_part) if thinking_expected else answer_part


@dataclass
class TraceResult:
    status: str  # one of CLASSES
    misuse_names: list[str] = field(default_factory=list)  # for TRACE_MISUSE and TRACE_AMBIGUOUS
    value_in_gold_unit: float | None = None
    value_text: str | None = None
    unit: str | None = None
    sign_only: bool = False  # TRACE_AMBIGUOUS because only the opposite sign of the extracted value matches
    matches_gold: bool = False
    matches_misuse: list[str] = field(default_factory=list)  # every misuse value the extracted value is within tolerance of
    n_candidates: int = 0
    statements: list[Statement] = field(default_factory=list)  # all candidates, in order

    @property
    def label(self) -> str:
        return f"TRACE_MISUSE({self.misuse_names[0]})" if self.status == "TRACE_MISUSE" else self.status


def classify_trace(region: str, ctx: TraceContext) -> TraceResult:
    """R4 and R5 on a trace region."""

    if not region.strip():
        return TraceResult("NO_TRACE")
    statements = candidate_statements(region, ctx)
    if not statements:
        return TraceResult("NO_TRACE_VALUE")
    last = statements[-1]
    ratio = _ratio(last.unit, ctx.gold_unit) or 1.0
    text = last.text.lstrip("+-")
    gold = within_tolerance(text, last.value, ratio, ctx.gold, ctx.view)
    hits = sorted(h for h, f in ctx.misuse.items() if within_tolerance(text, last.value, ratio, f, ctx.view))
    flipped = False
    if not gold and not hits and last.value != 0:  # a sign-only difference is not evidence of a different value
        flip_gold = within_tolerance(text, -last.value, ratio, ctx.gold, ctx.view)
        flip_hits = sorted(h for h, f in ctx.misuse.items() if within_tolerance(text, -last.value, ratio, f, ctx.view))
        if flip_gold or flip_hits:
            flipped, gold, hits = True, flip_gold, flip_hits
    if flipped:
        status, names = "TRACE_AMBIGUOUS", hits
    elif gold and not hits:
        status, names = "TRACE_CORRECT", []
    elif gold or len(hits) > 1:
        status, names = "TRACE_AMBIGUOUS", hits
    elif hits:
        status, names = "TRACE_MISUSE", hits
    else:
        status, names = "TRACE_OTHER", []
    return TraceResult(status, names, last.value_in_gold_unit, last.text, last.unit, flipped, gold, hits, len(statements),
                       statements)


def classify_record(record: Mapping[str, Any], ctx: TraceContext) -> TraceResult:
    """Classify one sampled record's trace (its full generation text under its thinking mode)."""

    region = trace_region(str(record.get("generated_answer_raw") or ""),
                          thinking_expected=record.get("thinking_mode") == "on",
                          hit_token_limit=bool(record.get("hit_token_limit", False)))
    return classify_trace(region, ctx)


# --- TC ------------------------------------------------------------------------------------------------------------------------

def attributed_class_names(attributed: Iterable[str] | Mapping[str, Any]) -> set[str]:
    """Curve classes from a list of names or from `misuse_attribution` output (keeps `attribution == ATTRIBUTED`)."""

    if isinstance(attributed, Mapping):
        return {h for h, v in attributed.items() if isinstance(v, Mapping) and v.get("attribution") == "ATTRIBUTED"}
    return set(attributed)


def final_matches_attributed(record: Mapping[str, Any], cell: rvs.Cell, attributed: set[str], view: str) -> str | None:
    """The attributed curve class a COMPLETE record's final answer UNIQUELY matches under `view`, else None. A final answer
    that is also within tolerance of the gold, or that matches any other foil too, does not count."""

    if record.get("completion_status") != "COMPLETE" or record.get("value_in_gold_unit") is None:
        return None
    value = float(record["value_in_gold_unit"])
    tol = REL_TOL_1PCT if view == "rel1pct" else REL_TOL_COARSE
    if gv.within(value, cell.gold, tol):
        return None
    hit = gv.match_foils(value, cell.foils, tol)
    if hit["match_class"] != "UNIQUE_MATCH":
        return None
    name = hit["matches"][0]
    h = rvs.curve_class(name)
    confounded = {p for pair in cell.confounded for p in pair.split("~")}
    return h if h in attributed and name not in confounded else None


def trace_inputs(records: Sequence[Mapping[str, Any]], cells: Mapping[str, rvs.Cell], attributed_curves: Iterable[str] | Mapping[str, Any],
                 view: str = "declared", *, rows: Mapping[str, Mapping[str, Any]] | None = None,
                 contexts: Mapping[str, TraceContext] | None = None, return_records: bool = False) -> dict[str, Any]:
    """The dict for `ScorecardInputs.trace`: TC's x and n with the counts behind them (R6).

    `rows`: dataset cell rows keyed by cell key (job id without the sample suffix), from which contexts are built (prompt,
    target phrases, q); `contexts` overrides per cell. A cell with neither gets a context from the cell and the record's gold
    unit alone: only unit-attached statements can then be extracted. `relevance_delta` is left None (an F1 contrast, filled in
    by the caller when the relevance-instruction ablation ran).
    """

    view = normalise_view(view)
    attributed = attributed_class_names(attributed_curves)
    counts = {c: 0 for c in CLASSES}
    by_curve: dict[str, dict[str, int]] = {}
    details: list[dict[str, Any]] = []
    n_d = n_final_match = n_with_trace_region = n_final_also_gold = 0
    context_cache: dict[str, TraceContext] = dict(contexts or {})
    for rec in records:
        key = rvs.cell_key(rec)
        cell = cells.get(key)
        if cell is None or cell.stratum != "D" or cell.heldout or cell.value_index is None:
            continue
        if rec.get("completion_status") != "COMPLETE":
            continue
        n_d += 1
        region = trace_region(str(rec.get("generated_answer_raw") or ""), thinking_expected=rec.get("thinking_mode") == "on",
                              hit_token_limit=bool(rec.get("hit_token_limit", False)))
        n_with_trace_region += bool(region.strip())
        h = final_matches_attributed(rec, cell, attributed, view)
        if h is None:
            if rec.get("value_in_gold_unit") is not None and gv.within(float(rec["value_in_gold_unit"]), cell.gold,
                                                                         REL_TOL_1PCT if view == "rel1pct" else REL_TOL_COARSE):
                n_final_also_gold += 1
            continue
        n_final_match += 1
        if key not in context_cache:
            if rows is not None and key in rows:
                context_cache[key] = context_from_row(rows[key], cell, view)
            else:
                context_cache[key] = TraceContext(cell.gold, str(rec["gold_unit"]),
                                                  {k: v for k, v in cell.foils.items() if k not in rvs.NOT_MISUSE}, view=view)
        res = classify_trace(region, context_cache[key])
        counts[res.status] += 1
        slot = by_curve.setdefault(h, {c: 0 for c in CLASSES})
        slot[res.status] += 1
        if return_records:
            details.append({"job_id": rec.get("job_id"), "final_curve": h, "status": res.status, "label": res.label,
                            "value_in_gold_unit": res.value_in_gold_unit, "value_text": res.value_text,
                            "matches_gold": res.matches_gold, "matches_misuse": res.matches_misuse,
                            "n_candidates": res.n_candidates,
                            "statements": [(s.text, s.unit, s.value_in_gold_unit) for s in res.statements]})
    x = counts["TRACE_CORRECT"]
    n = sum(counts[c] for c in CLASSIFIABLE)
    excluded = counts["TRACE_AMBIGUOUS"] + counts["NO_TRACE_VALUE"] + counts["NO_TRACE"]
    out: dict[str, Any] = {
        "extractor_frozen": bool(EXTRACTOR_FROZEN), "extractor_version": TRACE_EXTRACTOR_VERSION,
        "extractor_fingerprint": extractor_fingerprint(), "view": view, "reasoning_trace": n_with_trace_region > 0,
        "x": x, "n": n, "relevance_delta": None,
        "counts": {**counts, "d_samples_complete": n_d, "final_matches_attributed_curve": n_final_match,
                   "final_also_within_gold_tolerance": n_final_also_gold, "excluded_from_n": excluded},
        "by_curve": by_curve,
        "attributed_curves": sorted(attributed),
        "sensitivity": {"unclassifiable_as_not_correct": {"x": x, "n": n + excluded,
                                                         "note": "TRACE_AMBIGUOUS, NO_TRACE_VALUE and NO_TRACE counted as not trace-correct"}},
        "rule": "TC = TRACE_CORRECT / (TRACE_CORRECT + TRACE_MISUSE + TRACE_OTHER); ambiguous and valueless traces excluded from n",
    }
    if n:
        out["tc"] = x / n
    if return_records:
        out["records"] = details
    return out


def extractor_fingerprint() -> str:
    """A hash of every pattern and constant; pinned in the tests to `TRACE_EXTRACTOR_VERSION`."""

    import inspect

    functions = (normalise_trace, resolve_unit, scan_numbers, within_tolerance, _heads, _named_segments, _restated,
                 candidate_statements, _rejected, _conversion_identity, _is_final_line, trace_region, classify_trace, final_matches_attributed,
                 derive_target_terms, context_from_row, classify_record, trace_inputs, attributed_class_names)
    payload = {"version": TRACE_EXTRACTOR_VERSION, "source": [inspect.getsource(f) for f in functions],
               "patterns": [p.pattern for p in (_WRAP, _FRAC, _SQRT, _SCI, _SCI_PURE, _SPACING, _THOUSANDS, _NUM, _UNIT_TOKEN,
                                                _TERMINATOR, _SPLIT_EQ, _BARE, _VARIABLE_AFTER, _IDENTITY, _REJECTED,
                                                _QUESTION_START, _LEADING, _HEAD_STOP)],
        "connective": _CONNECTIVE, "subscripts": list(ALLOWED_SUBSCRIPTS), 
        "lexicon": {k: [list(v[0]), list(v[1])] for k, v in sorted(_LEXICON.items())},
        "tolerances": [REL_TOL_COARSE, REL_TOL_1PCT], "final_pattern": rc2._FINAL.pattern,
        "recover_pattern": rc2._RECOVER_LINE.pattern}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
