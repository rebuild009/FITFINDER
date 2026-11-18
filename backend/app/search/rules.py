"""Rule-based parser for natural-language shopping queries. No API key needed.

    "linen shirt for 52 inch chest under 3000"
    -> category=shirt, materials=[linen], measurements={chest: 132.1}, max_price=3000
"""

from __future__ import annotations

import re

from ..schemas import ParsedQuery
from .vocab import (
    CATEGORY_SYNONYMS,
    COLOR_GROUPS,
    FIT_WORDS,
    GENDER_WORDS,
    INCH_THRESHOLD,
    MATERIALS,
    STOPWORDS,
    TAG_WORDS,
)

CM_PER_INCH = 2.54
MAX_CM = {"chest": 200, "waist": 200, "hips": 210, "shoulder": 75, "inseam": 110}
DIM_ALIASES = {
    "chest": "chest", "bust": "chest", "waist": "waist", "hip": "hips", "hips": "hips",
    "shoulder": "shoulder", "shoulders": "shoulder", "inseam": "inseam", "leg length": "inseam", "length": "inseam",
}
_DIM = r"(chest|bust|waist|hips?|shoulders?|inseam|leg length|length)"
_NUM = r"(\d{2,3}(?:\.\d+)?)"
_UNIT = r"(cm|cms|centimet(?:er|re)s?|inches|inch|in|\"|'')"
_CURRENCY = r"(?:(?<![a-z])(?:rs\.?|inr|rupees)(?![a-z]))"  # whole word: not the "rs" in trousers
_K = r"(k(?![a-z]))?"  # "2k" = 2000, but not the k in "2000 kurta"
_MAX_AFTER = r"(?:se\s+kam|se\s+n[ei]+che|ke\s+andar|ke\s+n[ei]+che|tak|max(?:imum)?|or\s+less|and\s+(?:below|under))(?![a-z])"
_NOT_A_UNIT = r"(?!\s*(?:cm|cms|in\b|inch|inches|\"|ft|feet|'))"


class _Span:
    def __init__(self, start: int, end: int):
        self._span = (start, end)

    def span(self):
        return self._span


class _Text:
    """Lower-cased query that remembers which parts have been understood."""

    def __init__(self, raw: str):
        text = raw.lower()
        for a, b in (("₹", " rs "), ("’", "'"), ("‘", "'"), ("”", '"'), ("“", '"'), ("″", '"'), ("′", "'")):
            text = text.replace(a, b)
        self.text = f" {text} "

    def take(self, match: re.Match) -> None:
        start, end = match.span()
        self.text = self.text[:start] + " " * (end - start) + self.text[end:]

    def finditer(self, pattern: str):
        return list(re.finditer(pattern, self.text))


def _word(phrase: str) -> str:
    return rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])"


def _money(digits: str, k: str | None) -> float:
    value = float(digits.replace(",", ""))
    return value * 1000 if k else value


def _to_cm(dim: str, value: float, unit: str | None) -> float | None:
    if unit and unit.startswith(("cm", "centimet")):
        cm = value
    elif unit:
        cm = value * CM_PER_INCH
        if cm > MAX_CM[dim]:  # "chest 120 in cotton": "in" was a preposition
            cm = value
    else:
        cm = value * CM_PER_INCH if value < INCH_THRESHOLD[dim] else value
    return round(cm, 1) if 20 <= cm <= MAX_CM[dim] else None


def _parse_height(t: _Text) -> float | None:
    patterns = [
        # 6'4", 6 ft 4 in, 6ft, 5 feet 11
        (r"(?<!\d)([4-7])\s*(?:'|ft|feet|foot)\s*(?:(\d{1,2})\s*(?:\"|''|inches|inch|in)?)?(?![\d.])(?:\s*tall\b)?", "ftin"),
        # 5.8 ft (Indian shorthand for 5'8")
        (r"(?<!\d)([4-7])\.(\d{1,2})\s*(?:ft|feet|foot)\b(?:\s*tall\b)?", "ftin"),
        # height 5.8 / 5.8 tall
        (r"(?:height|ht)\s*(?:of|is|:|=)?\s*([4-7])\.(\d{1,2})(?!\d)", "ftin"),
        (r"(?<!\d)([4-7])\.(\d{1,2})\s*tall\b", "ftin"),
        # 193 cm tall / height 193
        (r"(?<!\d)(1[3-9]\d|2[0-2]\d)\s*(?:cm|cms)\s*(?:tall)?", "cm"),
        (r"(?:height|ht)\s*(?:of|is|:|=)?\s*(1[3-9]\d|2[0-2]\d)\b", "cm"),
    ]
    for pattern, kind in patterns:
        for m in t.finditer(pattern):
            if kind == "cm":
                # "120 cm chest" / "chest 120 cm" is a chest, not a height
                after = t.text[m.end(): m.end() + 14]
                before = t.text[max(0, m.start() - 20): m.start()]
                if "tall" not in m.group(0) and (
                    re.match(r"\s*" + _DIM, after) or re.search(_DIM + r"\s*\W{0,3}\s*(?:of|is)?\s*$", before)
                ):
                    continue
                t.take(m)
                return float(m.group(1))
            feet = int(m.group(1))
            inches = int(m.group(2)) if m.lastindex and m.lastindex >= 2 and m.group(2) else 0
            if inches > 11:
                continue
            t.take(m)
            return round((feet * 12 + inches) * CM_PER_INCH, 1)
    return None


def _parse_prices(t: _Text, q: ParsedQuery) -> None:
    for pattern in (
        rf"between\s*{_CURRENCY}?\s*(\d[\d,]*(?:\.\d+)?)(?![\d,]|\.\d)\s*{_K}\s*(?:and|to|-)\s*{_CURRENCY}?\s*(\d[\d,]*(?:\.\d+)?)(?![\d,]|\.\d)\s*{_K}",
        rf"{_CURRENCY}\s*(\d[\d,]*(?:\.\d+)?)(?![\d,]|\.\d)\s*{_K}\s*(?:-|to)\s*{_CURRENCY}?\s*(\d[\d,]*(?:\.\d+)?)(?![\d,]|\.\d)\s*{_K}",
    ):
        for m in t.finditer(pattern):
            lo, hi = _money(m.group(1), m.group(2)), _money(m.group(3), m.group(4))
            q.min_price, q.max_price = min(lo, hi), max(lo, hi)
            t.take(m)
            return
    max_words = r"(?<![a-z])(?:under|below|less than|upto|up to|within|max(?:imum)?|cheaper than|budget(?: of| is)?|<)"
    min_words = r"(?<![a-z])(?:over|above|more than|min(?:imum)?|at least|starting(?: at| from)?|>)"
    for m in t.finditer(rf"{max_words}\s*{_CURRENCY}?\s*(\d[\d,]*(?:\.\d+)?)(?![\d,]|\.\d)\s*{_K}{_NOT_A_UNIT}(?:\s*{_CURRENCY})?"):
        q.max_price = _money(m.group(1), m.group(2))
        t.take(m)
    for m in t.finditer(rf"{min_words}\s*{_CURRENCY}?\s*(\d[\d,]*(?:\.\d+)?)(?![\d,]|\.\d)\s*{_K}{_NOT_A_UNIT}(?:\s*{_CURRENCY})?"):
        q.min_price = _money(m.group(1), m.group(2))
        t.take(m)
    if q.max_price is None:
        for m in t.finditer(rf"(?<![\d.])(\d[\d,]*(?:\.\d+)?)(?![\d,]|\.\d)\s*{_K}\s*(?:{_CURRENCY}\s*)?{_MAX_AFTER}"):
            q.max_price = _money(m.group(1), m.group(2))
            t.take(m)
    if q.max_price is None and q.min_price is None:
        for pattern in (rf"{_CURRENCY}\s*(\d[\d,]*(?:\.\d+)?)(?![\d,]|\.\d)\s*{_K}", rf"(?<!\d)(\d[\d,]*(?:\.\d+)?)(?![\d,]|\.\d)\s*{_K}\s*{_CURRENCY}\b",
                        r"(?<![\d.])(\d{1,3}(?:\.\d+)?)\s*(k)(?![a-z])"):
            for m in t.finditer(pattern):
                q.max_price = _money(m.group(1), m.group(2))
                t.take(m)
                return


def _parse_measurements(t: _Text, q: ParsedQuery) -> None:
    patterns = (
        (rf"{_NUM}\s*{_UNIT}?\s*(?:inch(?:es)?\s*)?{_DIM}\b", (1, 2, 3)),  # 52 inch chest
        (rf"\b{_DIM}\s*(?:size|measurement|measures|of|is|:|=|-)?\s*(?:of|is)?\s*{_NUM}\s*{_UNIT}?(?![a-z])", (2, 3, 1)),  # chest 52in
    )
    # A query is usually written one way throughout: "waist 38 length 34" or
    # "38 waist 34 length". Try first the style of whichever comes first, so
    # "waist 38 length 34" is not read as "38 length".
    firsts = [min((m.start() for m in t.finditer(p)), default=10**9) for p, _ in patterns]
    if firsts[1] < firsts[0]:
        patterns = patterns[::-1]
    for pattern, (num_i, unit_i, dim_i) in patterns:
        for m in t.finditer(pattern):
            dim = DIM_ALIASES[m.group(dim_i)]
            cm = _to_cm(dim, float(m.group(num_i)), m.group(unit_i))
            if cm is not None and dim not in q.measurements:
                q.measurements[dim] = cm
                t.take(m)


TOP_CATEGORIES = {"tshirt", "shirt", "polo", "hoodie", "jacket", "kurta"}
BOTTOM_CATEGORIES = {"jeans", "trousers", "joggers", "shorts"}


def _parse_numeric_size(t: _Text, q: ParsedQuery) -> None:
    if q.category in TOP_CATEGORIES:
        dim = "chest"
    elif q.category in BOTTOM_CATEGORIES:
        dim = "waist"
    else:
        return
    if dim in q.measurements:
        return
    for pattern in (r"\bsize\s*(?:of|is|:|-)?\s*(\d{2})(?![\d.])", r"(?<![\d.])(\d{2})\s*size\b"):
        for m in t.finditer(pattern):
            value = int(m.group(1))
            if 26 <= value <= 64:
                q.measurements[dim] = round(value * CM_PER_INCH, 1)
                t.take(m)
                return


def _parse_size_label(t: _Text) -> str | None:
    patterns = [
        (r"(?<![a-z0-9])([2-9])\s?xl(?![a-z])", lambda m: f"{m.group(1)}XL"),
        (r"(?<![a-z0-9])(x{2,5})l(?![a-z])", lambda m: f"{len(m.group(1))}XL"),
        (r"(?<![a-z0-9])xl(?![a-z])", lambda m: "XL"),
        (r"(?<![a-z0-9])(xx?s)(?![a-z])", lambda m: m.group(1).upper()),
        (r"\bsize\s+(s|m|l|small|medium|large)\b", lambda m: m.group(1)[0].upper()),
        (r"\buk\s?(\d{1,2})\b", lambda m: f"UK {m.group(1)}"),
    ]
    for pattern, fmt in patterns:
        for m in t.finditer(pattern):
            t.take(m)
            return fmt(m)
    return None


def _earliest(t: _Text, mapping: dict[str, list[str]]) -> str | None:
    """Find the key whose phrase appears first; consume every phrase that matched."""
    hits = []
    phrases = sorted(((p, k) for k, ps in mapping.items() for p in ps), key=lambda x: -len(x[0]))
    for phrase, key in phrases:
        for m in t.finditer(_word(phrase)):
            hits.append((m.start(), key))
            t.take(m)
    return min(hits)[1] if hits else None


def _all(t: _Text, phrases: list[str]) -> list[str]:
    found = []
    for phrase in sorted(phrases, key=len, reverse=True):
        for m in t.finditer(_word(phrase)):
            if phrase not in found:
                found.append(phrase)
            t.take(m)
    return found


def parse_query(raw: str) -> ParsedQuery:
    q = ParsedQuery(text=raw.strip())
    t = _Text(raw)

    _parse_prices(t, q)
    _parse_measurements(t, q)
    height = _parse_height(t)
    if height:
        q.measurements["height"] = height
    q.size_label = _parse_size_label(t)

    tags = []
    for m in t.finditer(r"(?<![a-z])(big|bade|bada|badi|bari|bare)\s+(guys?|m[ae]n|sizes?)(?![a-z])"):
        tags.append("plus-size")
        # keep "guys"/"men" for the gender reader; "size" is used up here
        t.take(m if m.group(2).startswith("size") else _Span(m.start(1), m.end(1)))
        break
    for tag, phrases in sorted(TAG_WORDS.items(), key=lambda kv: -max(len(p) for p in kv[1])):
        if _all(t, phrases):
            if tag not in tags:
                tags.append(tag)
    q.tags = tags

    q.fit_preference = _earliest(t, FIT_WORDS)
    q.category = _earliest(t, CATEGORY_SYNONYMS)
    q.gender = _earliest(t, GENDER_WORDS)
    _parse_numeric_size(t, q)
    q.colors = _all(t, list(COLOR_GROUPS))
    q.materials = _all(t, MATERIALS)

    keywords = []
    for word in re.findall(r"[a-z][a-z'-]+", t.text):
        word = word.strip("'-")
        if len(word) > 1 and word not in STOPWORDS and word not in keywords:
            keywords.append(word)
    q.keywords = keywords[:6]
    return q
