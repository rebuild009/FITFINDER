"""Size charts: read them from product HTML when a store publishes one, otherwise fall back to a standard chart.

Charts hold BODY measurement ranges in cm per size, the format the backend's True-Fit engine expects.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .sizes import normalise, waist_inseam

CM = 2.54
TOPS = {"tshirt", "shirt", "polo", "hoodie", "jacket", "kurta", "top"}

# ---------------------------------------------------------------- standard charts (low confidence)

_MEN_TOPS = [
    ("XS", 84, 88), ("S", 88, 94), ("M", 94, 100), ("L", 100, 106), ("XL", 106, 112), ("2XL", 112, 119),
    ("3XL", 119, 127), ("4XL", 127, 135), ("5XL", 135, 143), ("6XL", 143, 151), ("7XL", 151, 159), ("8XL", 159, 167),
]
_WOMEN_TOPS = [
    ("XXS", 76, 80), ("XS", 80, 84), ("S", 84, 88), ("M", 88, 94), ("L", 94, 100), ("XL", 100, 106),
    ("2XL", 106, 114), ("3XL", 114, 122), ("4XL", 122, 130), ("5XL", 130, 138), ("6XL", 138, 146),
]
_INSEAM_REGULAR = {"men": (76, 81), "women": (73, 78), "unisex": (75, 81)}


def _alpha_rows(gender: str) -> dict[str, dict]:
    ladder = _WOMEN_TOPS if gender == "women" else _MEN_TOPS
    rows = {}
    n = len(ladder)
    for i, (label, lo, hi) in enumerate(ladder):
        if gender == "women":
            wd, hd = 18 - 10 * i / (n - 1), 8 - 4 * i / (n - 1)
            rows[label] = {"chest": [lo, hi], "waist": [lo - wd, hi - wd], "hips": [lo + hd, hi + hd]}
        else:
            wd = 14 - 12 * i / (n - 1)
            mid = (lo + hi) / 2
            sh = 41 + (mid - 86) * 0.2
            rows[label] = {"chest": [lo, hi], "waist": [lo - wd - 1, hi - wd + 1], "shoulder": [sh - 1.8, sh + 1.8]}
    return {k: {d: [round(a, 1), round(b, 1)] for d, (a, b) in v.items()} for k, v in rows.items()}


def standard_chart(category: str, gender: str, labels: list[str]) -> dict | None:
    """Generic chart for the given labels, or None when the labels can't be mapped."""
    sizes = []
    if category in TOPS or category == "dress":
        rows = _alpha_rows(gender)
        for label in labels:
            m = rows.get(label)
            if m:
                m = dict(m)
                if category != "dress":
                    m.pop("hips", None)
                sizes.append({"label": label, "measurements": m})
    else:
        alpha = _alpha_rows(gender)
        for label in labels:
            waist, inseam = waist_inseam(label)
            if waist:
                wcm = waist * CM
                hips = wcm + (24 if gender == "women" else 16)
                m = {"waist": [round(wcm - 1.3, 1), round(wcm + 1.3, 1)], "hips": [round(hips - 3, 1), round(hips + 3, 1)]}
                if category != "shorts":
                    if inseam:
                        m["inseam"] = [round(inseam * CM - 1.5, 1), round(inseam * CM + 1.5, 1)]
                    else:
                        m["inseam"] = list(_INSEAM_REGULAR.get(gender, (75, 81)))
            elif label in alpha:
                w = alpha[label]["waist"]
                h = alpha[label].get("hips") or [w[0] + 14, w[1] + 16]
                m = {"waist": [round(w[0] - 2, 1), round(w[1] + 2, 1)], "hips": [round(h[0] - 2, 1), round(h[1] + 2, 1)]}
            else:
                continue
            sizes.append({"label": label, "measurements": m})
    return {"unit": "cm", "source": "standard", "sizes": sizes} if sizes else None


# ---------------------------------------------------------------- charts published in product HTML

_DIMS = [
    ("chest", r"pit\s*to\s*pit|half\s*chest|across\s*chest|chest|bust"),
    ("waist", r"waist"),
    ("hips", r"hips?|seat"),
    ("shoulder", r"shoulders?|across\s*shoulder"),
    ("inseam", r"inseam|inside\s*leg"),
]
_HALF = re.compile(r"pit\s*to\s*pit|half\s*chest|across\s*chest|\bflat\b", re.I)
# Ease: how much bigger a garment is than the body it is cut for (cm), used for garment-measurement charts.
_EASE = {"chest": 10.0, "waist": 3.0, "hips": 6.0, "shoulder": 1.0, "inseam": 0.0}
_SIZE_RE = re.compile(r"^(?:x{0,5}s|m|x{0,5}l|\d\s?x{1,2}l|\d{2}(?:\s*[/x]\s*\d{2})?|uk\s?\d{1,2}|small|medium|large|x+-?large)$", re.I)


def _dim_of(text: str) -> tuple[str | None, bool]:
    t = text.lower()
    for dim, pattern in _DIMS:
        if re.search(pattern, t):
            return dim, bool(_HALF.search(t))
    return None, False


def _numbers(text: str) -> list[float]:
    return [float(n) for n in re.findall(r"\d+(?:\.\d+)?", text.replace(",", "."))]


def _is_size(text: str) -> bool:
    return bool(_SIZE_RE.match(text.strip().lower()))


def _table_rows(table) -> list[list[str]]:
    rows = []
    for tr in table.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
        if any(cells):
            rows.append(cells)
    return rows


def _read_table(rows: list[list[str]]) -> dict[str, dict[str, tuple[list[float], bool]]]:
    """Return {size_label: {dim: (numbers, is_half)}} for either table orientation."""
    out: dict[str, dict] = {}
    if len(rows) < 2:
        return out
    header = rows[0]
    # Orientation 1: sizes across the header, measurements down the first column.
    if sum(_is_size(h) for h in header[1:]) >= 2:
        for row in rows[1:]:
            dim, half = _dim_of(row[0])
            if not dim:
                continue
            for label, cell in zip(header[1:], row[1:]):
                if _is_size(label) and _numbers(cell):
                    out.setdefault(normalise(label), {})[dim] = (_numbers(cell), half)
        return out
    # Orientation 2: measurements across the header, sizes down the first column.
    dims = [_dim_of(h) for h in header[1:]]
    if any(d for d, _ in dims):
        for row in rows[1:]:
            if not row or not _is_size(row[0]):
                continue
            for (dim, half), cell in zip(dims, row[1:]):
                if dim and _numbers(cell):
                    out.setdefault(normalise(row[0]), {})[dim] = (_numbers(cell), half)
    return out


def _guess_unit(context: str, values: list[float]) -> str:
    c = context.lower()
    if re.search(r"\bcms?\b|centimet", c):
        return "cm"
    if re.search(r"\binch(es)?\b|\bin\.|\"", c):
        return "in"
    big = [v for v in values if v > 20]
    return "in" if big and max(big) < 70 else "cm"


def chart_from_html(body_html: str, category: str) -> dict | None:
    """Parse the first usable size table in a product description."""
    if not body_html or "<table" not in body_html.lower():
        return None
    soup = BeautifulSoup(body_html, "html.parser")
    page_text = soup.get_text(" ", strip=True)
    garment = bool(_GARMENT.search(page_text))
    for table in soup.find_all("table"):
        chart = chart_from_rows(_table_rows(table), category, table.get_text(" ", strip=True) + " " + page_text[:400], garment)
        if chart:
            return chart
    return None


_GARMENT = re.compile(r"garment|product\s+measurement|flat\s+measurement|laid\s+flat", re.I)


def chart_from_rows(rows: list[list[str]], category: str, context: str = "", garment: bool = False,
                    unit: str | None = None, source: str = "product") -> dict | None:
    """Turn a size table (rows of cell text, either orientation) into body ranges in cm."""
    data = _read_table(rows)
    if len(data) < 2:
        return None
    all_values = [n for dims in data.values() for nums, _ in dims.values() for n in nums]
    unit = unit or _guess_unit(context, all_values)
    factor = CM if unit == "in" else 1.0

    # Convert every cell to a (lo, hi) body range in cm.
    per_dim: dict[str, list[tuple[str, float, float | None]]] = {}
    for label, dims in data.items():
        for dim, (nums, half) in dims.items():
            vals = [n * factor * (2 if half else 1) for n in nums[:2]]
            if garment:
                vals = [v - _EASE[dim] for v in vals]
            per_dim.setdefault(dim, []).append((label, vals[0], vals[1] if len(vals) > 1 else None))

    sizes: dict[str, dict] = {label: {} for label in data}
    for dim, cells in per_dim.items():
        # Single values become ranges that meet halfway between neighbouring sizes.
        singles = sorted((v, label) for label, v, hi in cells if hi is None)
        for i, (v, label) in enumerate(singles):
            prev_v = singles[i - 1][0] if i > 0 else None
            next_v = singles[i + 1][0] if i + 1 < len(singles) else None
            gap = next_v - v if next_v is not None else (v - prev_v if prev_v is not None else 4.0)
            lo = (prev_v + v) / 2 if prev_v is not None else v - gap / 2
            hi = (next_v + v) / 2 if next_v is not None else v + gap / 2
            sizes[label][dim] = [round(lo, 1), round(hi, 1)]
        for label, lo, hi in cells:
            if hi is not None:
                sizes[label][dim] = [round(min(lo, hi), 1), round(max(lo, hi), 1)]

    primary = "waist" if category in ("jeans", "trousers", "joggers", "shorts") else "chest"
    rows_out = [{"label": label, "measurements": m} for label, m in sizes.items() if primary in m]
    if len(rows_out) >= 2:
        return {"unit": "cm", "source": source, "sizes": rows_out}
    return None
