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


STORES = {"bigbanana", "Janasya", "Angrakhaa", "Instafab Plus", "My Designation", "Nobero",
          "Blackberrys", "Jaywalking", "Bluorng"}


def test_real_catalog_uses_only_brand_charts(products):
    assert all(p["size_chart"]["source"] == "brand" for p in products)
    assert {p["store"] for p in products} == STORES
    assert all(p["brand"] == p["store"] for p in products)


def test_men_range_from_xxs_to_10xl(products):
    labels = {r["label"] for p in products if p["gender"] != "women" for r in p["size_chart"]["sizes"]}
    assert {"XXS", "XS", "6XL", "10XL"} <= labels


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
    assert top["product"]["brand"] in ("bigbanana", "Instafab Plus")  # the two plus-size men's brands
    assert top["fit"]["best_size"] in ("3XL", "4XL", "5XL") and top["fit"]["score"] >= 90
