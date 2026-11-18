from app.fit.engine import evaluate_dimension, fit_product, with_estimates

SHIRT_CHART = {
    "unit": "cm",
    "source": "brand",
    "sizes": [
        {"label": "XL", "measurements": {"chest": [106, 112], "shoulder": [46, 49], "waist": [96, 104], "height": [163, 186]}},
        {"label": "2XL", "measurements": {"chest": [112, 119], "shoulder": [47, 50], "waist": [103, 111], "height": [163, 186]}},
        {"label": "3XL", "measurements": {"chest": [119, 127], "shoulder": [48, 52], "waist": [111, 119], "height": [163, 186]}},
    ],
}

JEANS_CHART = {
    "unit": "cm",
    "source": "product",
    "sizes": [
        {"label": "36R", "measurements": {"waist": [90, 93], "hips": [103, 108], "inseam": [76, 81]}},
        {"label": "36L", "measurements": {"waist": [90, 93], "hips": [103, 108], "inseam": [81, 86]}},
        {"label": "38R", "measurements": {"waist": [95, 98], "hips": [107, 112], "inseam": [76, 81]}},
    ],
}


def test_in_range_is_good():
    d = evaluate_dimension("chest", 109, 106, 112, "regular")
    assert d.status == "good" and d.score >= 0.95 and d.delta_cm == 0


def test_tight_is_worse_than_loose_by_the_same_amount():
    tight = evaluate_dimension("chest", 114, 106, 112)
    loose = evaluate_dimension("chest", 104, 106, 112)
    assert tight.status == "snug" and loose.status == "loose"
    assert tight.score < loose.score


def test_way_too_tight():
    d = evaluate_dimension("chest", 125, 106, 112)
    assert d.status == "too_tight" and d.score == 0


def test_preference_moves_the_sweet_spot():
    # Body at the top of the range = close fit: snug lovers score it higher than relaxed lovers.
    snug = evaluate_dimension("chest", 111, 106, 112, "snug")
    relaxed = evaluate_dimension("chest", 111, 106, 112, "relaxed")
    assert snug.score > relaxed.score


def test_length_dims_report_short_and_long():
    assert evaluate_dimension("inseam", 90, 76, 81).status == "too_short"
    assert evaluate_dimension("inseam", 74, 76, 81).status == "long"
    assert evaluate_dimension("height", 198, 163, 186).status == "too_short"


def test_picks_the_right_size():
    fit = fit_product("shirt", SHIRT_CHART, {"chest": 116, "shoulder": 48.5, "waist": 105, "height": 178})
    assert fit.best_size == "2XL"
    assert fit.verdict == "true_fit"
    assert fit.confidence == "medium"


def test_roomy_waist_on_a_shirt_is_fine():
    fit = fit_product("shirt", SHIRT_CHART, {"chest": 116, "waist": 92})
    waist = next(d for d in fit.dimensions if d.dimension == "waist")
    assert waist.status == "good"


def test_reports_when_sizes_run_out():
    fit = fit_product("shirt", SHIRT_CHART, {"chest": 140, "shoulder": 55})
    assert fit.verdict == "no_fit"
    assert "3XL" in fit.summary and "127" in fit.summary


def test_needs_primary_measurement():
    fit = fit_product("jeans", JEANS_CHART, {"chest": 100})
    assert fit.verdict == "needs_measurements" and fit.best_size is None
    assert fit.missing[0] == "waist"


def test_out_of_stock_sizes_are_skipped():
    fit = fit_product("jeans", JEANS_CHART, {"waist": 91, "hips": 105, "inseam": 78}, sizes_available=["36L", "38R"])
    assert fit.best_size == "36L"


def test_inseam_estimated_from_height():
    body, estimated = with_estimates({"waist": 91, "height": 190})
    assert estimated == {"inseam"} and body["inseam"] == 85.5
    fit = fit_product("jeans", JEANS_CHART, {"waist": 91, "hips": 105, "height": 190})
    assert fit.best_size == "36L"
    inseam = next(d for d in fit.dimensions if d.dimension == "inseam")
    assert inseam.estimated and "estimated" in inseam.note


def test_dress_needs_all_three_girths_to_fit():
    chart = {"source": "brand", "sizes": [{"label": "UK 24", "measurements": {"chest": [124, 130], "waist": [113, 119], "hips": [131, 137]}}]}
    good = fit_product("dress", chart, {"chest": 127, "waist": 116, "hips": 134})
    bad_hips = fit_product("dress", chart, {"chest": 127, "waist": 116, "hips": 150})
    assert good.verdict == "true_fit"
    assert bad_hips.verdict == "no_fit"


def test_notes_use_the_shoppers_unit():
    d = evaluate_dimension("chest", 115.08, 106, 112, unit="in")
    assert d.note == "1.2 in tighter than this size is cut for"
    h = evaluate_dimension("height", 198, 163, 186, unit="in")
    assert "6′1″" in h.note
    fit = fit_product("shirt", SHIRT_CHART, {"chest": 140, "shoulder": 55}, unit="in")
    assert "50 in" in fit.summary
