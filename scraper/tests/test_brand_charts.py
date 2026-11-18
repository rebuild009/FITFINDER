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
