import json
import sys
from pathlib import Path

import httpx
import pytest

from fitfinder_scraper.charts import chart_from_html, standard_chart
from fitfinder_scraper.shopify import Store, scrape_store
from fitfinder_scraper.sizes import normalise, waist_inseam

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "products.json").read_text())
BACKEND = Path(__file__).resolve().parents[2] / "backend"


def _client(robots: str = "", products=FIXTURE) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text=robots)
        if request.url.path == "/products.json":
            page = int(request.url.params.get("page", 1))
            return httpx.Response(200, json=products if page == 1 else {"products": []})
        return httpx.Response(404)

    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.mark.parametrize(
    "raw,label",
    [("XX-Large", "2XL"), ("3X-Large", "3XL"), ("xxxl", "3XL"), ("Medium", "M"), ("x-large", "XL"), ("4 XL", "4XL"), ("uk 24", "UK 24"), ("32/32", "32/32")],
)
def test_normalise(raw, label):
    assert normalise(raw) == label


def test_waist_inseam():
    assert waist_inseam("34/32") == (34, 32)
    assert waist_inseam("W36 L34") == (36, 34)
    assert waist_inseam("40") == (40, None)
    assert waist_inseam("M") == (None, None)


def test_chart_sizes_across_header_in_inches():
    html = FIXTURE["products"][0]["body_html"]
    chart = chart_from_html(html, "shirt")
    assert chart["source"] == "product"
    by = {s["label"]: s["measurements"] for s in chart["sizes"]}
    assert by["M"]["chest"] == [96.5, 101.6]  # 38-40 in
    assert by["2XL"]["chest"] == [111.8, 116.8]  # "XXL" normalised
    # single shoulder values become ranges that meet halfway between sizes
    assert by["M"]["shoulder"][1] == by["L"]["shoulder"][0]


def test_chart_garment_half_measurements_in_cm():
    html = FIXTURE["products"][1]["body_html"]
    chart = chart_from_html(html, "dress")
    by = {s["label"]: s["measurements"] for s in chart["sizes"]}
    # pit to pit 59 cm -> 118 cm garment chest -> about 108 cm body after ease
    lo, hi = by["2XL"]["chest"]
    assert lo < 108 < hi
    assert "length" not in by["2XL"]


def test_standard_chart_for_waist_labels():
    chart = standard_chart("jeans", "men", ["34/32", "44/34"])
    by = {s["label"]: s["measurements"] for s in chart["sizes"]}
    assert by["34/32"]["waist"][0] < 34 * 2.54 < by["34/32"]["waist"][1]
    assert by["44/34"]["inseam"][0] < 34 * 2.54 < by["44/34"]["inseam"][1]
    assert standard_chart("kurta", "women", ["Free Size"]) is None


def test_scrape_store_end_to_end():
    items, report = scrape_store(Store(domain="test-store.com", name="Test Store", gender="unisex"), client=_client(), delay_s=0)
    assert report.fetched == 6 and report.kept == 4
    assert sum(report.skipped.values()) == 2
    by = {i["title"]: i for i in items}

    shirt = by["Men's Relaxed Linen Shirt"]
    assert shirt["category"] == "shirt" and shirt["gender"] == "men"
    assert shirt["size_chart"]["source"] == "product"
    assert "S" not in shirt["sizes_available"] and "2XL" in shirt["sizes_available"]
    assert shirt["colors"] == ["sage", "white"] and "linen" in shirt["materials"]
    assert shirt["price"] == 2499.0 and shirt["product_url"] == "https://test-store.com/products/relaxed-linen-shirt"
    assert shirt["image_url"] == "https://cdn.example.com/shirt.jpg"

    dress = by["Wrap Midi Dress"]
    assert dress["gender"] == "women" and dress["category"] == "dress"

    jeans = by["Straight Fit Jeans"]
    assert jeans["size_chart"]["source"] == "standard"

    tee = by["Heavyweight Tee"]
    assert tee["category"] == "tshirt" and tee["sizes_available"] == ["XL", "2XL", "3XL", "4XL"]


def test_robots_disallow_is_respected():
    items, report = scrape_store(Store(domain="test-store.com"), client=_client("User-agent: *\nDisallow: /products.json"), delay_s=0)
    assert items == [] and "robots.txt disallows /products.json" in report.skipped


def test_output_is_accepted_by_backend_ingest():
    """Contract test with the backend. Runs when the backend's requirements are installed too."""
    pytest.importorskip("sqlalchemy")
    pytest.importorskip("pydantic_settings")
    sys.path.insert(0, str(BACKEND))
    try:
        from app.ingest import validate
    finally:
        sys.path.remove(str(BACKEND))
    items, _ = scrape_store(Store(domain="test-store.com"), client=_client(), delay_s=0)
    assert items and all(validate(i) is None for i in items)
