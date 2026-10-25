from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db import init_db
from app.ingest import ingest_items
from app.models import Product

ITEM = {
    "external_id": "shopify:example.com:linen-shirt",
    "source": "shopify",
    "store": "example.com",
    "brand": "Example",
    "title": "Linen Shirt",
    "category": "shirt",
    "gender": "men",
    "price": 1999,
    "size_chart": {"source": "standard", "sizes": [{"label": "XL", "measurements": {"chest": [106, 112]}}]},
}


def test_upsert_and_validation():
    engine = create_engine("sqlite://")
    init_db(engine)
    with Session(engine) as s:
        r = ingest_items(s, [ITEM, {**ITEM, "external_id": "x", "category": "socks"}])
        assert r["added"] == 1 and r["skipped"] == 1 and "unknown category 'socks'" in r["skip_reasons"]
        r = ingest_items(s, [{**ITEM, "price": 1499}])
        assert r["updated"] == 1
        assert s.scalar(select(Product.price)) == 1499
