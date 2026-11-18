"""FitFinder API.

    uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import settings
from .db import SessionLocal, get_session, init_db
from .fit import CATEGORIES, category_group, fit_all_sizes, fit_product
from .ingest import seed_if_empty
from .models import Product
from .schemas import (
    FitOut,
    FitProfile,
    MatchRequest,
    MatchResponse,
    ParsedQuery,
    ProductDetail,
    ProductOut,
    SearchRequest,
    SizeRow,
)
from .search.llm import llm_enabled
from .search.service import parse, run_search

log = logging.getLogger("fitfinder")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    if settings.auto_seed:
        with SessionLocal() as session:
            result = seed_if_empty(session)
            if result:
                log.info("Loaded demo catalog: %s", result)
    yield


app = FastAPI(title="FitFinder API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health(session: Session = Depends(get_session)) -> dict:
    count = session.scalar(select(func.count()).select_from(Product))
    return {"status": "ok", "products": count}


@app.get("/api/meta")
def meta(session: Session = Depends(get_session)) -> dict:
    by_cat = dict(session.execute(select(Product.category, func.count()).group_by(Product.category)).all())
    brands = session.execute(
        select(Product.brand, Product.source, func.count()).group_by(Product.brand, Product.source).order_by(Product.brand)
    ).all()
    lo, hi = session.execute(select(func.min(Product.price), func.max(Product.price))).one()
    return {
        "categories": [
            {"key": k, "label": label, "group": category_group(k), "count": by_cat.get(k, 0)}
            for k, label in CATEGORIES.items()
        ],
        "brands": [{"name": b, "source": s, "count": n} for b, s, n in brands],
        "price": {"min": lo or 0, "max": hi or 0, "currency": "INR"},
        "parser": settings.openai_model if llm_enabled() else "rules",
        "total": sum(by_cat.values()),
    }


@app.post("/api/parse", response_model=ParsedQuery)
def parse_only(body: SearchRequest) -> ParsedQuery:
    parsed, _, _ = parse(body.query)
    return parsed


@app.post("/api/match", response_model=MatchResponse)
def match(body: MatchRequest, session: Session = Depends(get_session)) -> MatchResponse:
    """Structured search: filters plus an optional fit profile."""
    return run_search(session, body.filters, body.profile, None, body.only_fitting, body.sort, body.limit, body.offset)


@app.post("/api/search", response_model=MatchResponse)
def search(body: SearchRequest, session: Session = Depends(get_session)) -> MatchResponse:
    """Natural-language search. Measurements in the query override the saved profile."""
    parsed, parser, notes = parse(body.query)
    result = run_search(session, body.filters, body.profile, parsed, body.only_fitting, body.sort, body.limit, body.offset)
    result.parsed = parsed
    result.parser = parser
    result.notes = notes + result.notes
    return result


def _get_product(session: Session, product_id: int) -> Product:
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def _detail(product: Product, profile: FitProfile | None) -> ProductDetail:
    body = profile.body_cm() if profile else {}
    pref = profile.fit_preference if profile else "regular"
    unit = profile.unit if profile else "cm"
    fit = None
    if body:
        result = fit_product(product.category, product.size_chart, body, pref, product.sizes_available, unit)
        fit = FitOut(**result.to_dict())
    in_stock = set(product.sizes_available or [])
    rows = [
        SizeRow(**row, in_stock=row["size"] in in_stock)
        for row in fit_all_sizes(product.category, product.size_chart, body, pref, unit)
    ]
    return ProductDetail(
        product=ProductOut.model_validate(product),
        size_chart_source=(product.size_chart or {}).get("source", "standard"),
        fit=fit,
        sizes=rows,
    )


@app.get("/api/products/{product_id}", response_model=ProductDetail)
def product_detail(product_id: int, session: Session = Depends(get_session)) -> ProductDetail:
    return _detail(_get_product(session, product_id), None)


@app.post("/api/products/{product_id}/fit", response_model=ProductDetail)
def product_fit(product_id: int, profile: FitProfile, session: Session = Depends(get_session)) -> ProductDetail:
    return _detail(_get_product(session, product_id), profile)
