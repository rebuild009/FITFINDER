"""Work out category, gender, colours and materials from Shopify product fields."""

from __future__ import annotations

import re

# Order matters: more specific phrases first (t-shirt before shirt, sweatshirt before shirt).
CATEGORY_RULES = [
    ("tshirt", ["t-shirt", "t shirt", "tshirt", "tee", "henley"]),
    ("polo", ["polo"]),
    ("hoodie", ["hoodie", "sweatshirt", "hoody"]),
    ("jacket", ["jacket", "blazer", "bomber", "coat", "shacket"]),
    ("kurta", ["kurta", "kurti"]),
    ("dress", ["dress", "gown"]),
    ("jeans", ["jeans", "jean", "denims"]),
    ("joggers", ["jogger", "trackpant", "track pant", "sweatpant", "lowers"]),
    ("shorts", ["shorts", "bermuda"]),
    ("trousers", ["trouser", "pant", "chino", "slacks"]),
    ("shirt", ["shirt", "button-down", "button down"]),
    ("top", ["top", "blouse", "tank", "cami", "tunic"]),
]

GENDER_RULES = [
    ("women", ["women", "womens", "woman", "ladies", "female", "girls"]),
    ("men", ["men", "mens", "man", "male", "boys", "gents"]),
    ("unisex", ["unisex"]),
]

COLORS = [
    "black", "white", "navy", "olive", "sage", "rust", "maroon", "beige", "grey", "gray", "charcoal", "sky blue",
    "light blue", "blue", "mustard", "yellow", "teal", "green", "indigo", "pink", "lavender", "purple", "brown",
    "cream", "off white", "red", "orange", "khaki",
]

MATERIALS = [
    "linen", "cotton", "denim", "wool", "fleece", "khadi", "rayon", "silk", "polyester", "modal", "viscose",
    "corduroy", "jersey", "terry", "flannel", "lycra", "spandex",
]


def _has(text: str, word: str) -> bool:
    return re.search(rf"(?<![a-z]){re.escape(word)}s?(?![a-z])", text) is not None


def category_of(title: str, product_type: str, tags: list[str]) -> str | None:
    # Product type is the most reliable signal, then the title, then tags.
    for text in (product_type, title, " ".join(tags)):
        text = (text or "").lower()
        for category, words in CATEGORY_RULES:
            if any(_has(text, w) for w in words):
                return category
    return None


def gender_of(title: str, product_type: str, tags: list[str], default: str = "unisex") -> str:
    text = " ".join([title or "", product_type or "", *tags]).lower()
    for gender, words in GENDER_RULES:
        if any(_has(text, w) for w in words):
            return gender
    return default


def colors_of(option_values: list[str], title: str) -> list[str]:
    values = [v.strip().lower() for v in option_values if v and v.strip()]
    if values:
        return values[:6]
    text = (title or "").lower()
    return [c for c in COLORS if _has(text, c)][:3]


def materials_of(*texts: str) -> list[str]:
    text = " ".join(t or "" for t in texts).lower()
    return [m for m in MATERIALS if _has(text, m)]
