"""True-Fit engine: deterministic size matching from body measurements and size charts.

For every size in a product's chart, each relevant body dimension is compared with
the range that size is cut for. Dimensions are scored 0-1, weighted by how much they
matter for the garment category, and hard problems (e.g. a chest that won't close)
cap the score. The best-scoring size is the recommendation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .dimensions import (
    CATEGORY_WEIGHTS,
    DIM_LABELS,
    GIRTH_DIMS,
    PRIMARY_DIMS,
    TIGHT_ONLY_DIMS,
    TOLERANCE_CM,
)

FIT_PREFERENCES = ("snug", "regular", "relaxed")

# Where in a size's range the body should ideally sit (0 = bottom of range = roomy).
PREF_TARGET = {"snug": 0.75, "regular": 0.5, "relaxed": 0.25}
# Multipliers on the tolerance: how much tightness / looseness each preference accepts.
TIGHT_ALLOWANCE = {"snug": 1.3, "regular": 1.0, "relaxed": 0.8}
LOOSE_ALLOWANCE = {"snug": 1.0, "regular": 1.6, "relaxed": 2.5}

# Differences smaller than this are below measuring-tape accuracy and count as in range.
GRACE_CM = 0.5

# Average inseam is about 45% of height; used only when the inseam itself is unknown.
INSEAM_PER_HEIGHT = 0.45

CHART_CONFIDENCE = {"product": "high", "brand": "medium", "standard": "low"}

VERDICTS = (
    (90, "true_fit", "True Fit"),
    (75, "good", "Good fit"),
    (55, "compromise", "Fits with a compromise"),
    (0, "no_fit", "Won't fit"),
)


@dataclass
class DimensionFit:
    dimension: str
    label: str
    body_cm: float
    range_cm: tuple[float, float]
    status: str  # good | snug | too_tight | loose | too_loose | short | too_short | long | too_long
    delta_cm: float  # >0 body is beyond the top of the range, <0 below the bottom, 0 inside
    score: float
    note: str
    estimated: bool = False


@dataclass
class SizeFit:
    size: str
    score: int
    dimensions: list[DimensionFit]

    @property
    def issues(self) -> list[DimensionFit]:
        return [d for d in self.dimensions if d.status != "good"]


@dataclass
class FitResult:
    score: int | None
    verdict: str
    verdict_label: str
    best_size: str | None
    summary: str
    confidence: str
    dimensions: list[DimensionFit] = field(default_factory=list)
    alternatives: list[dict] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _len(cm: float, unit: str = "cm", dim: str = "") -> str:
    """Format a length for notes in the shopper's own unit."""
    if unit == "in":
        inches = cm / 2.54
        if dim == "height":
            ft, rest = divmod(round(inches), 12)
            return f"{ft}′{rest}″"
        text = f"{inches:.1f}".rstrip("0").rstrip(".")
        return f"{text} in"
    text = f"{cm:.1f}".rstrip("0").rstrip(".")
    return f"{text} cm"


def evaluate_dimension(
    dim: str, body: float, lo: float, hi: float, pref: str = "regular", unit: str = "cm"
) -> DimensionFit:
    """Score one body measurement against the range a size is cut for."""
    if lo > hi:
        lo, hi = hi, lo
    pref = pref if pref in PREF_TARGET else "regular"
    tol = TOLERANCE_CM.get(dim, 2.5)
    label = DIM_LABELS.get(dim, dim.title())
    is_girth = dim in GIRTH_DIMS

    if lo - GRACE_CM <= body <= hi + GRACE_CM:
        width = hi - lo
        pos = 0.5 if width <= 0 else min(1.0, max(0.0, (body - lo) / width))
        # Where you sit inside a girth range is a matter of taste; inside a length range it just fits.
        score = 1.0 - 0.15 * abs(pos - PREF_TARGET[pref]) / 0.75 if is_girth else 1.0
        if is_girth:
            where = "roomy" if pos < 0.34 else ("close to the body" if pos > 0.66 else "right in the middle")
            note = f"In range, {where}"
        else:
            note = "Right length"
        return DimensionFit(dim, label, round(body, 1), (lo, hi), "good", 0.0, round(score, 3), note)

    if body > hi:
        over = body - hi
        if is_girth:
            allow = tol * TIGHT_ALLOWANCE[pref]
            status = "snug" if over <= allow else "too_tight"
            note = f"{_len(over, unit)} tighter than this size is cut for"
        else:
            allow = tol
            status = "short" if over <= allow else "too_short"
            note = (
                f"Inseam {_len(over, unit)} short" if dim == "inseam" else f"Cut for up to {_len(hi, unit, dim)} tall; may ride short"
            )
        score = 0.85 * max(0.0, 1 - over / (2 * allow))
        return DimensionFit(dim, label, round(body, 1), (lo, hi), status, round(over, 1), round(score, 3), note)

    under = lo - body
    if is_girth:
        allow = tol * LOOSE_ALLOWANCE[pref]
        status = "loose" if under <= allow else "too_loose"
        note = f"{_len(under, unit)} looser than this size is cut for"
        score = 0.85 * max(0.0, 1 - under / (2.5 * allow))
    else:
        allow = tol * 1.5
        status = "long" if under <= allow else "too_long"
        note = (
            f"Inseam {_len(under, unit)} long, can be hemmed"
            if dim == "inseam"
            else f"Cut for {_len(lo, unit, dim)} and taller; may sit long"
        )
        floor = 0.45 if dim == "inseam" else 0.3
        score = max(floor, 0.85 * max(0.0, 1 - under / (3 * allow)))
    return DimensionFit(dim, label, round(body, 1), (lo, hi), status, round(-under, 1), round(score, 3), note)


def with_estimates(body: dict) -> tuple[dict, set[str]]:
    """Fill gaps we can reasonably estimate. Returns the new body and which dimensions were estimated."""
    body = {k: v for k, v in body.items() if v is not None and v > 0}
    estimated: set[str] = set()
    if "inseam" not in body and "height" in body:
        body["inseam"] = round(body["height"] * INSEAM_PER_HEIGHT, 1)
        estimated.add("inseam")
    return body, estimated


def score_size(
    category: str,
    size_ranges: dict,
    body: dict,
    pref: str = "regular",
    estimated: set[str] | frozenset = frozenset(),
    unit: str = "cm",
) -> SizeFit | None:
    """Score one size. Returns None when no primary dimension can be compared."""
    weights = CATEGORY_WEIGHTS.get(category, {})
    primary = PRIMARY_DIMS.get(category, set())
    tight_only = TIGHT_ONLY_DIMS.get(category, set())
    dims: list[DimensionFit] = []
    for dim, weight in weights.items():
        rng = size_ranges.get(dim)
        value = body.get(dim)
        if rng is None or value is None or value <= 0:
            continue
        d = evaluate_dimension(dim, float(value), float(rng[0]), float(rng[1]), pref, unit)
        if dim in tight_only and d.status in ("loose", "too_loose"):
            d.status, d.score, d.note = "good", 0.95, "Roomy here, which is fine for this cut"
        if dim in estimated:
            d.estimated = True
            d.note += " (estimated from your height)"
        dims.append(d)
    if not any(d.dimension in primary for d in dims):
        return None

    total_w = sum(weights[d.dimension] for d in dims)
    score = sum(weights[d.dimension] * d.score for d in dims) / total_w

    # Hard problems cap the score no matter how well the rest fits.
    for d in dims:
        if d.status == "too_tight":
            score = min(score, 0.30 if d.dimension in primary else 0.60)
        elif d.status == "too_loose" and d.dimension in primary:
            score = min(score, 0.50)
        elif d.status == "too_short":
            score = min(score, 0.60)
    return SizeFit(size="", score=round(score * 100), dimensions=dims)


def _verdict(score: int) -> tuple[str, str]:
    for threshold, key, label in VERDICTS:
        if score >= threshold:
            return key, label
    return VERDICTS[-1][1], VERDICTS[-1][2]


def fit_product(
    category: str,
    size_chart: dict,
    body: dict,
    pref: str = "regular",
    sizes_available: list[str] | None = None,
    unit: str = "cm",
) -> FitResult:
    """Find the best size of a product for a body. `body` holds centimetres per dimension."""
    sizes = size_chart.get("sizes", []) if size_chart else []
    confidence = CHART_CONFIDENCE.get((size_chart or {}).get("source", "standard"), "low")
    if sizes_available:
        in_stock = set(sizes_available)
        sizes = [s for s in sizes if s["label"] in in_stock] or sizes

    weights = CATEGORY_WEIGHTS.get(category, {})
    chart_dims = {d for s in sizes for d in s.get("measurements", {})}
    missing = [
        d
        for d in sorted(weights, key=lambda k: -weights[k])
        if d in chart_dims and (body.get(d) is None or body.get(d) <= 0)
    ]
    body, estimated = with_estimates(body)

    scored: list[SizeFit] = []
    for s in sizes:
        fit = score_size(category, s.get("measurements", {}), body, pref, estimated, unit)
        if fit is not None:
            fit.size = s["label"]
            scored.append(fit)

    if not scored:
        return FitResult(
            score=None,
            verdict="needs_measurements",
            verdict_label="Add measurements",
            best_size=None,
            summary="Add your " + " and ".join(DIM_LABELS[d].lower() for d in missing[:2]) + " to check fit"
            if missing
            else "No size chart to compare against",
            confidence=confidence,
            missing=missing,
        )

    # Highest score wins; ties go to the size whose primary dims sit closest to the preferred spot.
    best = max(scored, key=lambda f: (f.score, sum(d.score for d in f.dimensions)))
    verdict, verdict_label = _verdict(best.score)

    issues = best.issues
    if not issues:
        summary = "Fits on every measurement you gave"
    else:
        summary = "; ".join(f"{d.label}: {d.note[0].lower() + d.note[1:]}" for d in issues[:2])

    if verdict == "no_fit":
        primary = PRIMARY_DIMS.get(category, set())
        tight = [d for d in best.dimensions if d.dimension in primary and d.status == "too_tight"]
        if tight:
            d = tight[0]
            largest = max(sizes, key=lambda s: s.get("measurements", {}).get(d.dimension, (0, 0))[1])
            top = largest["measurements"][d.dimension][1]
            summary = f"Sizes stop at {largest['label']} ({d.label.lower()} up to {_len(top, unit)})"

    alternatives = [
        {"size": f.size, "score": f.score, "verdict": _verdict(f.score)[0]}
        for f in sorted((f for f in scored if f is not best), key=lambda f: -f.score)[:2]
        if f.score >= 40
    ]

    return FitResult(
        score=best.score,
        verdict=verdict,
        verdict_label=verdict_label,
        best_size=best.size,
        summary=summary,
        confidence=confidence,
        dimensions=best.dimensions,
        alternatives=alternatives,
        missing=missing,
    )


def fit_all_sizes(category: str, size_chart: dict, body: dict, pref: str = "regular", unit: str = "cm") -> list[dict]:
    """Per-size breakdown for the product detail view."""
    out = []
    body, estimated = with_estimates(body)
    for s in (size_chart or {}).get("sizes", []):
        fit = score_size(category, s.get("measurements", {}), body, pref, estimated, unit)
        row = {"size": s["label"], "measurements": s.get("measurements", {})}
        if fit is None:
            row.update(score=None, verdict="needs_measurements", dimensions=[])
        else:
            row.update(score=fit.score, verdict=_verdict(fit.score)[0], dimensions=[asdict(d) for d in fit.dimensions])
        out.append(row)
    return out
