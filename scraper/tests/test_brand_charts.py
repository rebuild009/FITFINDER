import json
from pathlib import Path

from fitfinder_scraper.brand_charts import kiwi_chart, parse_script_charts, script_chart

FIX = Path(__file__).parent / "fixtures"


def test_reads_bigbanana_embedded_charts():
    charts = parse_script_charts((FIX / "bigbanana_size_charts.html").read_text())
    assert set(charts) == {"tshirt", "shirt", "trackpants", "trouser"}
    chart = script_chart(charts["trouser"])
    assert chart["source"] == "brand" and chart["unit"] == "cm"
    labels = [s["label"] for s in chart["sizes"]]
    assert labels[0] == "2XL" and labels[-1] == "10XL"
    first = chart["sizes"][0]["measurements"]
    assert first["waist"] == [95.5, 101.0] and first["hips"] == [113.5, 119.0]  # "hip" -> hips


def test_reads_kiwi_chart_in_inches_as_body_ranges_in_cm():
    payload = json.loads((FIX / "kiwi_suit_set.json").read_text())
    sizing_id, chart = kiwi_chart(payload, "kurta")
    assert sizing_id == 3387955 and chart["source"] == "brand"
    by_label = {s["label"]: s["measurements"] for s in chart["sizes"]}
    assert list(by_label)[:3] == ["XS", "S", "M"]
    # bust 36 in, between 34 and 38 -> 35..37 in -> 88.9..94.0 cm; body chart, so no ease subtracted
    assert by_label["S"]["chest"] == [88.9, 94.0]
    assert by_label["S"]["hips"] == [96.5, 101.6]


def test_disabled_kiwi_chart_is_ignored():
    payload = json.loads((FIX / "kiwi_suit_set.json").read_text())
    payload["sizings"][0]["isEnabled"] = False
    assert kiwi_chart(payload, "kurta") == (None, None)


def test_reads_a_to_fit_table_on_the_product_page():
    from fitfinder_scraper.brand_charts import page_chart

    chart = page_chart((FIX / "instafab_trousers_page.html").read_text(), "trousers")
    by_label = {s["label"]: s["measurements"] for s in chart["sizes"]}
    assert list(by_label) == ["38", "40", "42", "44"]
    # "TO FIT WAIST 40" is a body size: 39-41 in, no ease taken off
    assert by_label["40"]["waist"] == [99.1, 104.1]


def test_garment_page_table_has_ease_removed():
    from fitfinder_scraper.brand_charts import page_chart

    html = (FIX / "instafab_trousers_page.html").read_text()
    body = page_chart(html, "trousers")["sizes"][1]["measurements"]["waist"]
    garment = page_chart(html, "trousers", measures="garment")["sizes"][1]["measurements"]["waist"]
    assert round(body[0] - garment[0], 1) == 3.0  # standard waist ease


def test_reads_one_size_from_a_variant_page():
    from fitfinder_scraper.brand_charts import variant_measurements

    m = variant_measurements((FIX / "nobero_variant_s.html").read_text())
    assert round(m["chest"], 1) == 96.5  # "To Fit Chest 38" wins over garment "Chest 41"
    assert round(m["shoulder"], 1) == round(17.375 * 2.54 - 1.0, 1)  # garment shoulder minus ease


def test_catalog_build_drops_generic_and_implausible_charts():
    from fitfinder_scraper.catalog import problem

    def product(gender, source, chest_lows):
        sizes = [{"label": f"S{i}", "measurements": {"chest": [lo, lo + 5]}} for i, lo in enumerate(chest_lows)]
        return {"gender": gender, "size_chart": {"source": source, "sizes": sizes}}

    assert problem(product("men", "brand", [92, 97, 102])) is None
    assert problem(product("men", "standard", [92, 97, 102])) == "no brand chart"
    assert problem(product("women", "brand", [52, 56, 60])) == "implausible chart"  # measured flat
    assert problem(product("men", "brand", [97, 92, 102])) == "implausible chart"  # not in order
    assert problem(product("women", "brand", [72, 77])) is None  # fine for women, too small for men
    assert problem(product("men", "brand", [72, 77])) == "implausible chart"


def test_dress_styles_and_dress_shirts():
    from fitfinder_scraper.classify import category_of

    assert category_of("Molly Long Tee Dress", "", []) == "dress"
    assert category_of("Shirt Dress in Blue", "", []) == "dress"
    assert category_of("White Dress Shirt", "", []) == "shirt"
    assert category_of("Polo T-Shirt", "", []) == "polo"
