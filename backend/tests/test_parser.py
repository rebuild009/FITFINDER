import pytest

from app.search.rules import parse_query


def p(text):
    return parse_query(text)


def test_flagship_query():
    q = p("linen shirt for 52 inch chest under 3000")
    assert q.category == "shirt"
    assert q.materials == ["linen"]
    assert q.max_price == 3000
    assert q.measurements == {"chest": 132.1}


@pytest.mark.parametrize(
    "text,height",
    [("6'4 guy", 193.0), ("6 ft 4 in", 193.0), ("5.8 ft woman", 172.7), ("height 5.8", 172.7), ("193 cm tall", 193.0), ("6ft", 182.9)],
)
def test_heights(text, height):
    assert p(text).measurements["height"] == height


def test_bare_numbers_are_inches_for_small_values_cm_for_large():
    assert p("waist 34").measurements["waist"] == 86.4
    assert p("chest 120").measurements["chest"] == 120.0
    assert p("46 chest").measurements["chest"] == 116.8


def test_chest_in_cm_is_not_a_height():
    q = p("tee chest 132 cm")
    assert q.measurements == {"chest": 132.0}


def test_in_as_a_preposition():
    q = p("slim fit tee chest 120 in cotton")
    assert q.measurements["chest"] == 120.0 and q.materials == ["cotton"] and q.fit_preference == "snug"


@pytest.mark.parametrize(
    "text,lo,hi",
    [
        ("under 2k", None, 2000),
        ("below rs 2500", None, 2500),
        ("between 1500 and 3000", 1500, 3000),
        ("₹1,999", None, 1999),
        ("above 1000", 1000, None),
    ],
)
def test_prices(text, lo, hi):
    q = p("shirt " + text)
    assert (q.min_price, q.max_price) == (lo, hi)


@pytest.mark.parametrize("text,label", [("xxxl", "3XL"), ("5XL", "5XL"), ("5 xl", "5XL"), ("uk 26", "UK 26"), ("size m", "M")])
def test_size_labels(text, label):
    assert p("hoodie " + text).size_label == label


def test_category_gender_color_tags():
    q = p("big and tall navy blue polo for him")
    assert q.category == "polo" and q.gender == "men" and q.colors == ["navy blue"] and q.tags == ["big-and-tall"]


def test_tshirt_is_not_shirt_and_keywords_survive():
    q = p("oversized graphic t-shirt")
    assert q.category == "tshirt" and q.fit_preference == "relaxed" and q.keywords == ["graphic"]


def test_material_words_are_not_eaten_by_category():
    q = p("flannel shirt")
    assert q.category == "shirt" and q.materials == ["flannel"]
