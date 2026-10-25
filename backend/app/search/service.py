"""Search: filter the catalog, score relevance, run True-Fit on every candidate, rank."""

from __future__ import annotations

import logging
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..fit import fit_product
from ..fit.dimensions import CATEGORIES
from ..models import Product
from ..schemas import (
    Applied,
    FitOut,
    FitProfile,
    Filters,
    MatchItem,
    MatchResponse,
    ParsedQuery,
    ProductOut,
)
from .llm import llm_enabled, parse_with_llm
from .rules import parse_query as parse_with_rules
from .vocab import COLOR_GROUPS, STOPWORDS

log = logging.getLogger(__name__)

FITTING_THRESHOLD = 55  # "Fits with a compromise" or better


def parse(text: str) -> tuple[ParsedQuery, str, list[str]]:
    """Parse with GPT-4o when configured, filling any gaps from the rule parser."""
    rules = parse_with_rules(text)
    if not llm_enabled():
        return rules, "rules", []
    try:
        llm = parse_with_llm(text)
    except Exception as exc:  # network, auth, schema: never break search over it
        log.warning("LLM parse failed, using rules: %s", exc)
        return rules, "rules", ["AI parsing was unavailable, so the built-in parser read your query."]
    merged = llm.model_copy()
    for field in ("category", "gender", "min_price", "max_price", "size_label", "fit_preference"):
        if getattr(merged, field) is None and getattr(rules, field) is not None:
            setattr(merged, field, getattr(rules, field))
    merged.measurements = {**rules.measurements, **llm.measurements}
    for field in ("colors", "materials", "tags"):
        if not getattr(merged, field):
            setattr(merged, field, getattr(rules, field))
    return merged, settings.openai_model, []


def _color_matches(wanted: str, product_colors: list[str]) -> bool:
    targets = COLOR_GROUPS.get(wanted, [wanted])
    return any(t in c or c in t for t in targets for c in product_colors)


def _relevance(product: Product, keywords: list[str], tags: list[str]) -> float:
    text = product.search_text
    score = 0.0
    for kw in keywords:
        if re.search(rf"\b{re.escape(kw)}", text):
            score += 1.0
    for tag in tags:
        if tag in product.tags:
            score += 0.5
    return score


def _merge(filters: Filters, parsed: ParsedQuery | None, profile: FitProfile | None) -> Applied:
    p = parsed or ParsedQuery()
    keywords = list(p.keywords)
    if filters.q:
        keywords += [w for w in re.findall(r"[a-z][a-z'-]+", filters.q.lower()) if w not in STOPWORDS]
    body = profile.body_cm() if profile else {}
    body.update(p.measurements)
    category = filters.category or p.category
    return Applied(
        category=category if category in CATEGORIES else None,
        gender=filters.gender or p.gender or (profile.gender if profile else None),
        min_price=filters.min_price if filters.min_price is not None else p.min_price,
        max_price=filters.max_price if filters.max_price is not None else p.max_price,
        colors=filters.colors or p.colors,
        materials=filters.materials or p.materials,
        brands=filters.brands,
        size_label=filters.size_label or p.size_label,
        keywords=list(dict.fromkeys(keywords)),
        fit_preference=p.fit_preference or (profile.fit_preference if profile else "regular"),
        measurements_cm={k: round(v, 1) for k, v in body.items()},
    )


def run_search(
    session: Session,
    filters: Filters,
    profile: FitProfile | None = None,
    parsed: ParsedQuery | None = None,
    only_fitting: bool = False,
    sort: str = "fit",
    limit: int = 24,
    offset: int = 0,
) -> MatchResponse:
    applied = _merge(filters, parsed, profile)
    notes: list[str] = []

    stmt = select(Product)
    if applied.category:
        stmt = stmt.where(Product.category == applied.category)
    if applied.gender in ("men", "women"):
        stmt = stmt.where(Product.gender.in_([applied.gender, "unisex"]))
    elif applied.gender == "unisex":
        stmt = stmt.where(Product.gender == "unisex")
    if applied.min_price is not None:
        stmt = stmt.where(Product.price >= applied.min_price)
    if applied.max_price is not None:
        stmt = stmt.where(Product.price <= applied.max_price)
    if applied.brands:
        stmt = stmt.where(Product.brand.in_(applied.brands))
    products = list(session.scalars(stmt))

    if applied.colors:
        products = [p for p in products if any(_color_matches(c, p.colors) for c in applied.colors)]
    if applied.materials:
        products = [p for p in products if all(m in p.materials or m in p.search_text for m in applied.materials)]
    if applied.size_label:
        wanted = applied.size_label.upper().replace(" ", "")
        sized = [p for p in products if any(s.upper().replace(" ", "") == wanted for s in p.sizes_available)]
        if sized or not applied.measurements_cm:
            products = sized
        else:
            notes.append(f"Nothing is listed in {applied.size_label}, so results are matched on your measurements instead.")
            applied.size_label = None

    scored = [(p, _relevance(p, applied.keywords, (parsed.tags if parsed else []))) for p in products]
    if applied.keywords:
        hits = [(p, r) for p, r in scored if r >= 1.0]
        if hits:
            scored = hits
        else:
            notes.append("No products mention " + ", ".join(f"“{k}”" for k in applied.keywords) + "; showing everything else that matches.")
            applied.keywords = []

    body = applied.measurements_cm
    items: list[MatchItem] = []
    for product, rel in scored:
        fit = None
        if body:
            result = fit_product(product.category, product.size_chart, body, applied.fit_preference, product.sizes_available)
            fit = FitOut(**result.to_dict())
        items.append(MatchItem(product=ProductOut.model_validate(product), fit=fit, relevance=rel))

    checked = len(items)
    fitting = None
    if body:
        fitting = sum(1 for i in items if i.fit and i.fit.score is not None and i.fit.score >= FITTING_THRESHOLD)
        if only_fitting:
            items = [i for i in items if i.fit and (i.fit.score is None or i.fit.score >= FITTING_THRESHOLD)]
    else:
        notes.append("Add your measurements to see which size fits you.")

    def fit_key(i: MatchItem) -> float:
        return -1 if not i.fit or i.fit.score is None else i.fit.score

    if sort == "price_asc":
        items.sort(key=lambda i: (i.product.price, -fit_key(i)))
    elif sort == "price_desc":
        items.sort(key=lambda i: (-i.product.price, -fit_key(i)))
    elif sort == "relevance":
        items.sort(key=lambda i: (-i.relevance, -fit_key(i), i.product.price))
    else:
        items.sort(key=lambda i: (-fit_key(i), -i.relevance, i.product.price))

    return MatchResponse(
        total=len(items),
        checked=checked,
        fitting=fitting,
        items=items[offset: offset + limit],
        applied=applied,
        notes=notes,
    )
