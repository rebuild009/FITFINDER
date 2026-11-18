def test_health_and_autoseed(client):
    r = client.get("/api/health").json()
    assert r["status"] == "ok" and r["products"] > 100


def test_meta(client):
    m = client.get("/api/meta").json()
    assert m["parser"] == "rules"
    assert {c["key"] for c in m["categories"]} >= {"shirt", "jeans", "dress"}


PROFILE = {"unit": "in", "gender": "men", "measurements": {"chest": 52, "waist": 46, "shoulder": 20.5, "height": 72}}


def test_search_ranks_fitting_items_first(client):
    r = client.post("/api/search", json={"query": "shirt", "profile": PROFILE}).json()
    assert r["parsed"]["category"] == "shirt" and r["parser"] == "rules"
    scores = [i["fit"]["score"] for i in r["items"]]
    assert scores == sorted(scores, reverse=True)
    top = r["items"][0]
    assert top["fit"]["verdict"] in ("true_fit", "good")
    assert top["product"]["gender"] in ("men", "unisex")
    assert r["fitting"] < r["checked"]  # mainstream brands don't go up to 52in chests


def test_query_measurements_override_profile(client):
    r = client.post("/api/search", json={"query": "shirt chest 40", "profile": PROFILE}).json()
    assert r["applied"]["measurements_cm"]["chest"] == 101.6
    assert r["applied"]["measurements_cm"]["waist"] == 116.8


def test_only_fitting_filters(client):
    all_ = client.post("/api/search", json={"query": "shirt", "profile": PROFILE}).json()
    fit = client.post("/api/search", json={"query": "shirt", "profile": PROFILE, "only_fitting": True}).json()
    assert fit["total"] == all_["fitting"] < all_["total"]
    assert all(i["fit"]["score"] >= 55 for i in fit["items"])


def test_price_and_sort(client):
    r = client.post("/api/match", json={"filters": {"max_price": 1500}, "sort": "price_asc", "limit": 100}).json()
    prices = [i["product"]["price"] for i in r["items"]]
    assert prices and max(prices) <= 1500 and prices == sorted(prices)


def test_unknown_keywords_are_dropped_with_a_note(client):
    r = client.post("/api/search", json={"query": "velvet tuxedo shirt"}).json()
    assert r["total"] > 0 and any("velvet" in n for n in r["notes"])


def test_without_profile_asks_for_measurements(client):
    r = client.post("/api/search", json={"query": "jeans"}).json()
    assert r["fitting"] is None and r["items"][0]["fit"] is None
    assert any("measurements" in n for n in r["notes"])


def test_product_detail_and_fit(client):
    r = client.post("/api/match", json={"filters": {"category": "jeans", "gender": "men"}, "limit": 1}).json()
    pid = r["items"][0]["product"]["id"]
    d = client.get(f"/api/products/{pid}").json()
    assert d["fit"] is None and d["sizes"] and d["sizes"][0]["score"] is None
    d = client.post(f"/api/products/{pid}/fit", json={"unit": "in", "measurements": {"waist": 36, "hips": 42, "inseam": 32}}).json()
    assert d["fit"]["best_size"] and any(row["score"] is not None for row in d["sizes"])
    assert client.get("/api/products/999999").status_code == 404


def test_validation(client):
    assert client.post("/api/search", json={"query": ""}).status_code == 422
    bad = {"query": "shirt", "profile": {"measurements": {"chest": -4}}}
    assert client.post("/api/search", json=bad).status_code == 422
