"""Load catalog JSON (seed or scraper output) into the database. Upserts by external_id."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .fit.dimensions import CATEGORIES
from .models import Product

SEED_PATH = Path(__file__).resolve().parents[1] / "data" / "seed_catalog.json"

FIELDS = (
    "source", "store", "brand", "title", "description", "category", "gender", "price", "currency",
    "colors", "materials", "tags", "image_url", "product_url", "sizes_available", "size_chart",
)


def validate(item: dict) -> str | None:
    """Return a reason the item can't be ingested, or None if it's fine."""
    for key in ("external_id", "title", "category", "gender", "price", "size_chart"):
        if item.get(key) in (None, ""):
            return f"missing {key}"
    if item["category"] not in CATEGORIES:
        return f"unknown category {item['category']!r}"
    if item["gender"] not in ("men", "women", "unisex"):
        return f"unknown gender {item['gender']!r}"
    if not item["size_chart"].get("sizes"):
        return "empty size chart"
    return None


def ingest_items(session: Session, items: list[dict]) -> dict:
    existing = {p.external_id: p for p in session.scalars(select(Product).where(
        Product.external_id.in_([i.get("external_id") for i in items if i.get("external_id")])
    ))}
    added = updated = skipped = 0
    reasons: dict[str, int] = {}
    for item in items:
        reason = validate(item)
        if reason:
            skipped += 1
            reasons[reason] = reasons.get(reason, 0) + 1
            continue
        values = {k: item.get(k) for k in FIELDS}
        values["brand"] = values["brand"] or values["store"]
        values["description"] = values["description"] or ""
        values["currency"] = values["currency"] or "INR"
        for key in ("colors", "materials", "tags", "sizes_available"):
            values[key] = values[key] or []
        product = existing.get(item["external_id"])
        if product:
            for k, v in values.items():
                setattr(product, k, v)
            updated += 1
        else:
            session.add(Product(external_id=item["external_id"], **values))
            added += 1
    session.commit()
    return {"added": added, "updated": updated, "skipped": skipped, "skip_reasons": reasons}


def ingest_file(session: Session, path: str | Path) -> dict:
    data = json.loads(Path(path).read_text())
    items = data["products"] if isinstance(data, dict) else data
    return ingest_items(session, items)


def seed_if_empty(session: Session) -> dict | None:
    if session.scalar(select(func.count()).select_from(Product)):
        return None
    return ingest_file(session, SEED_PATH)
