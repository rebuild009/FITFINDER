"""The bundled real-store catalog loads cleanly and gives sensible fits."""

import json

import pytest

from app.ingest import CATALOGS, validate


@pytest.fixture(scope="module")
def products():
    return json.loads(CATALOGS["real"].read_text())["products"]


def test_every_real_product_is_valid(products):
    assert len(products) > 500
    assert [p["title"] for p in products if validate(p)] == []


def test_real_catalog_uses_brand_charts(products):
    brand = sum(p["size_chart"]["source"] == "brand" for p in products)
    assert brand / len(products) > 0.95
    assert {p["store"] for p in products} == {"bigbanana", "Janasya", "Angrakhaa"}


def test_search_on_real_catalog(client, monkeypatch):
    from app import db
    from app.ingest import ingest_file
    from app.models import Product

    with db.SessionLocal() as s:  # swap the demo catalog for the real one
        s.query(Product).delete()
        s.commit()
        ingest_file(s, CATALOGS["real"])
    r = client.post("/api/search", json={"query": "tshirt for 54 inch chest under 1500"}).json()
    assert r["parsed"]["measurements"] == {"chest": 137.2}
    top = r["items"][0]
    assert top["product"]["brand"].lower() == "bigbanana"
    assert top["fit"]["best_size"] in ("3XL", "4XL")  # bigbanana tshirt chart: 3XL 130.5-137, 4XL 137-143.5
