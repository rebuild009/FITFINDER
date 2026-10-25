"""Generate the demo catalog (data/seed_catalog.json).

Brands are fictional. Each has its own size chart, so the same label (say 2XL)
covers different bodies at different brands, which is exactly the problem True-Fit solves.
Deterministic: the same seed always produces the same catalog.

    python -m app.seed.generate
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "data" / "seed_catalog.json"

# (label, chest_lo, chest_hi) in cm, body measurements
MEN_TOPS = [
    ("XS", 84, 88), ("S", 88, 94), ("M", 94, 100), ("L", 100, 106), ("XL", 106, 112),
    ("2XL", 112, 119), ("3XL", 119, 127), ("4XL", 127, 135), ("5XL", 135, 143),
    ("6XL", 143, 151), ("7XL", 151, 159), ("8XL", 159, 167),
]
WOMEN_TOPS = [
    ("XXS", 76, 80), ("XS", 80, 84), ("S", 84, 88), ("M", 88, 94), ("L", 94, 100),
    ("XL", 100, 106), ("2XL", 106, 114), ("3XL", 114, 122), ("4XL", 122, 130),
    ("5XL", 130, 138), ("6XL", 138, 146),
]
UK_PLUS = [(f"UK {n}", 96 + i * 5.5, 101.5 + i * 5.5) for i, n in enumerate(range(14, 34, 2))]

INSEAM = {
    "men": {"S": (71, 76), "R": (76, 81), "L": (81, 86), "XL": (86, 91)},
    "women": {"S": (68, 73), "R": (73, 78), "L": (78, 83), "XL": (83, 88)},
}
DEFAULT_HEIGHT = {"men": (163, 186), "unisex": (160, 186), "women": (153, 172)}

BRANDS = [
    {
        "slug": "ample-co", "name": "Ample & Co", "offset": 3,
        "sizes": {"men": ("XL", "8XL"), "women": ("XL", "6XL")},
        "cats": {"men": ["tshirt", "shirt", "polo", "kurta", "joggers"], "women": ["top", "kurta", "dress", "joggers"]},
        "price": (999, 3499), "tags": ["plus-size", "extended-sizes"],
        "blurb": "Cut from the ground up for bigger bodies, with extra room through the chest and middle.",
    },
    {
        "slug": "broadline", "name": "Broadline", "offset": 0,
        "sizes": {"men": ("2XL", "7XL")}, "waist": {"men": (38, 56)}, "inseams": {"men": ["R", "L"]},
        "cats": {"men": ["shirt", "tshirt", "jacket", "jeans", "trousers"]},
        "price": (1499, 4999), "tags": ["big-and-tall", "plus-size"],
        "blurb": "Big-and-tall essentials from 2XL to 7XL.",
    },
    {
        "slug": "tall-tale", "name": "Tall Tale", "offset": 0,
        "sizes": {"men": ("S", "3XL"), "women": ("XS", "2XL")},
        "height": {"men": (183, 206), "women": (172, 192)},
        "waist": {"men": (28, 44), "women": (24, 38)}, "inseams": {"men": ["L", "XL"], "women": ["L", "XL"]},
        "cats": {"men": ["shirt", "tshirt", "hoodie", "jeans", "trousers"], "women": ["top", "jeans", "dress"]},
        "price": (1799, 4499), "tags": ["tall"],
        "blurb": "Longer bodies, sleeves and inseams for people 6 ft and up.",
    },
    {
        "slug": "petite-atlas", "name": "Petite Atlas", "offset": -1,
        "sizes": {"women": ("XXS", "L")}, "height": {"women": (143, 160)},
        "waist": {"women": (24, 34)}, "inseams": {"women": ["S"]},
        "cats": {"women": ["top", "dress", "jeans", "trousers", "kurta"]},
        "price": (1199, 3299), "tags": ["petite"],
        "blurb": "Proportioned for 5'3\" and under: shorter rise, sleeves and hems.",
    },
    {
        "slug": "northfold", "name": "Northfold", "offset": -4,
        "sizes": {"men": ("S", "2XL"), "women": ("XS", "XL")},
        "waist": {"men": (28, 38), "women": (24, 34)}, "inseams": {"men": ["R"], "women": ["R"]},
        "cats": {"men": ["shirt", "tshirt", "polo", "jeans", "jacket"], "women": ["top", "jeans", "dress"]},
        "price": (1299, 3999), "tags": ["slim-fit"],
        "blurb": "Slim, mainstream cuts that run small.",
    },
    {
        "slug": "kinfit", "name": "Kinfit", "offset": 0,
        "sizes": {"unisex": ("XS", "6XL")},
        "cats": {"unisex": ["tshirt", "hoodie", "joggers", "shorts"]},
        "price": (599, 1999), "tags": ["extended-sizes"], "per_category": 3,
        "blurb": "Unisex basics in one consistent size run from XS to 6XL.",
    },
    {
        "slug": "grande-studio", "name": "Grande Studio", "offset": 0, "uk_plus": True,
        "waist": {"women": (34, 50)}, "inseams": {"women": ["R", "L"]},
        "cats": {"women": ["dress", "top", "kurta", "trousers"]},
        "price": (1499, 4999), "tags": ["plus-size"],
        "blurb": "Occasion and everyday wear in UK sizes 14 to 32.",
    },
    {
        "slug": "deep-seam", "name": "Deep Seam Denim", "offset": 0,
        "waist": {"men": (28, 56), "women": (24, 50)},
        "inseams": {"men": ["S", "R", "L", "XL"], "women": ["S", "R", "L"]},
        "cats": {"men": ["jeans", "shorts"], "women": ["jeans", "shorts"]},
        "price": (1999, 4499), "tags": ["extended-sizes", "tall", "petite"],
        "blurb": "Denim in every waist from 28 to 56, with up to four leg lengths.",
    },
]

# (title, materials, description, fit tag)
TEMPLATES = {
    "tshirt": [
        ("Heavyweight Crew Tee", ["cotton"], "240 GSM cotton jersey that holds its shape wash after wash.", "regular-fit"),
        ("Oversized Drop-Shoulder Tee", ["cotton"], "Boxy drop-shoulder cut with a longer back hem.", "relaxed-fit"),
        ("Pique Henley", ["cotton"], "Three-button placket in breathable pique.", "regular-fit"),
        ("Everyday V-Neck Tee", ["cotton", "modal"], "Soft cotton-modal blend with a clean V-neck.", "regular-fit"),
    ],
    "shirt": [
        ("Relaxed Linen Shirt", ["linen"], "Breathable pure linen with a relaxed body and curved hem.", "relaxed-fit"),
        ("Oxford Button-Down", ["cotton"], "Classic oxford weave with a soft roll collar.", "regular-fit"),
        ("Mandarin Collar Shirt", ["cotton", "linen"], "Band collar in a cotton-linen blend for hot days.", "regular-fit"),
        ("Brushed Flannel Check Shirt", ["cotton"], "Brushed cotton flannel in a heritage check.", "regular-fit"),
    ],
    "polo": [
        ("Classic Pique Polo", ["cotton"], "Two-button pique polo with a ribbed collar.", "regular-fit"),
        ("Knit Resort Polo", ["cotton"], "Open-knit polo with a camp collar.", "relaxed-fit"),
    ],
    "hoodie": [
        ("Fleece Pullover Hoodie", ["cotton", "polyester"], "Brushed-back fleece with a kangaroo pocket.", "relaxed-fit"),
        ("Zip-Through Hoodie", ["cotton"], "Midweight loopback cotton with a two-way zip.", "regular-fit"),
        ("French Terry Sweatshirt Hoodie", ["cotton"], "Lightweight terry for in-between weather.", "regular-fit"),
    ],
    "jacket": [
        ("Denim Trucker Jacket", ["denim"], "Rigid denim trucker with chest pockets.", "regular-fit"),
        ("Quilted Bomber", ["polyester"], "Light quilted bomber with ribbed cuffs.", "regular-fit"),
        ("Unstructured Linen Blazer", ["linen"], "Soft-shoulder blazer with no lining.", "regular-fit"),
    ],
    "kurta": [
        ("Straight Cotton Kurta", ["cotton"], "Everyday straight kurta with side slits.", "regular-fit"),
        ("Chikankari Kurta", ["cotton"], "Hand-embroidered chikankari on soft mulmul.", "regular-fit"),
        ("Khadi Short Kurta", ["khadi"], "Handspun khadi in a hip-length cut.", "relaxed-fit"),
    ],
    "top": [
        ("Wrap Top", ["rayon"], "Adjustable wrap with a tie at the waist.", "regular-fit"),
        ("Tiered Peplum Top", ["cotton"], "Fitted bodice with a soft tiered peplum.", "regular-fit"),
        ("Ribbed Tank", ["cotton"], "Stretch rib tank with a scoop neck.", "slim-fit"),
        ("Boxy Linen Top", ["linen"], "Cropped boxy linen top with dropped shoulders.", "relaxed-fit"),
    ],
    "jeans": [
        ("Straight Fit Jeans", ["denim"], "Mid-rise straight leg in 2% stretch denim.", "regular-fit"),
        ("Relaxed Tapered Jeans", ["denim"], "Roomy seat and thigh with a tapered ankle.", "relaxed-fit"),
        ("Bootcut Jeans", ["denim"], "Classic bootcut with a slight flare.", "regular-fit"),
        ("Wide-Leg High-Rise Jeans", ["denim"], "High rise with a full wide leg.", "relaxed-fit"),
    ],
    "trousers": [
        ("Pleated Chinos", ["cotton"], "Single-pleat cotton twill chinos.", "regular-fit"),
        ("Linen Drawstring Trousers", ["linen"], "Easy linen trousers with a drawstring waist.", "relaxed-fit"),
        ("Flat-Front Formal Trousers", ["polyester", "viscose"], "Crease-resistant suiting fabric.", "regular-fit"),
    ],
    "joggers": [
        ("Fleece Joggers", ["cotton", "polyester"], "Brushed fleece joggers with cuffed ankles.", "regular-fit"),
        ("Cargo Joggers", ["cotton"], "Cotton twill joggers with cargo pockets.", "relaxed-fit"),
    ],
    "shorts": [
        ("Chino Shorts", ["cotton"], "9-inch chino shorts with a flat front.", "regular-fit"),
        ("Denim Shorts", ["denim"], "Rolled-hem denim shorts.", "regular-fit"),
        ("Mesh Training Shorts", ["polyester"], "Quick-dry training shorts with zip pockets.", "relaxed-fit"),
    ],
    "dress": [
        ("Wrap Midi Dress", ["rayon"], "Flattering wrap midi with flutter sleeves.", "regular-fit"),
        ("Tiered Maxi Dress", ["cotton"], "Floaty tiered cotton maxi.", "relaxed-fit"),
        ("Belted Shirt Dress", ["cotton", "linen"], "Button-through shirt dress with a self belt.", "regular-fit"),
        ("A-Line Knit Dress", ["cotton"], "Stretch knit dress with an A-line skirt.", "regular-fit"),
    ],
}

COLORS = [
    "black", "white", "navy", "olive", "sage", "rust", "maroon", "beige", "grey", "charcoal",
    "sky blue", "mustard", "teal", "indigo", "pink", "lavender", "brown", "cream",
]
DENIM_COLORS = ["indigo", "black", "light blue", "grey", "navy"]

PRICE_FACTOR = {
    "tshirt": 0.55, "polo": 0.7, "shirt": 0.85, "hoodie": 1.0, "jacket": 1.4, "kurta": 0.8,
    "top": 0.65, "jeans": 1.1, "trousers": 0.95, "joggers": 0.75, "shorts": 0.6, "dress": 1.15,
}

TOPS = {"tshirt", "shirt", "polo", "hoodie", "jacket", "kurta", "top"}


def _r(x: float) -> float:
    return round(x, 1)


def _slice(ladder, start, end):
    labels = [row[0] for row in ladder]
    return ladder[labels.index(start): labels.index(end) + 1]


def _top_rows(gender: str, brand: dict) -> list[dict]:
    """Chest/bust-led charts for tops and dresses."""
    off = brand["offset"]
    height = brand.get("height", {}).get(gender, DEFAULT_HEIGHT[gender])
    rows = []
    if gender == "women" and brand.get("uk_plus"):
        n = len(UK_PLUS)
        for i, (label, lo, hi) in enumerate(UK_PLUS):
            waist_diff = 12 - 4 * i / (n - 1)
            hip_diff = 8 - 3 * i / (n - 1)
            sh = 39 + i * 0.8
            rows.append((label, {
                "chest": [_r(lo), _r(hi)],
                "waist": [_r(lo - waist_diff), _r(hi - waist_diff)],
                "hips": [_r(lo + hip_diff), _r(hi + hip_diff)],
                "shoulder": [_r(sh - 1.5), _r(sh + 1.5)],
                "height": list(height),
            }))
        return rows

    ladder = WOMEN_TOPS if gender == "women" else MEN_TOPS
    start, end = brand["sizes"][gender]
    full = [row[0] for row in ladder]
    for label, lo, hi in _slice(ladder, start, end):
        i = full.index(label)
        mid = (lo + hi) / 2
        if gender == "women":
            waist_diff = 18 - 10 * i / (len(ladder) - 1)
            hip_diff = 8 - 4 * i / (len(ladder) - 1)
            sh = 36 + (mid - 78) * 0.15 + off * 0.25
            m = {
                "chest": [lo + off, hi + off],
                "waist": [lo - waist_diff + off, hi - waist_diff + off],
                "hips": [lo + hip_diff + off, hi + hip_diff + off],
                "shoulder": [sh - 1.5, sh + 1.5],
            }
        else:
            waist_diff = 14 - 12 * i / (len(ladder) - 1)
            sh = 41 + (mid - 86) * 0.2 + off * 0.25
            m = {
                "chest": [lo + off, hi + off],
                "waist": [lo - waist_diff + off - 1, hi - waist_diff + off + 1],
                "shoulder": [sh - 1.8, sh + 1.8],
            }
        m = {k: [_r(v[0]), _r(v[1])] for k, v in m.items()}
        m["height"] = list(height)
        rows.append((label, m))
    return rows


def _waist_label_rows(gender: str, brand: dict, with_inseam: bool) -> list[tuple]:
    g = "women" if gender == "women" else "men"
    wmin, wmax = brand["waist"][g]
    inseams = brand.get("inseams", {}).get(g, ["R"]) if with_inseam else [None]
    rows = []
    for w in range(wmin, wmax + 1, 2):
        wcm = w * 2.54 + brand["offset"]
        if g == "women":
            hips = wcm + 26 - (w - 24) * 0.35
            hip_band = 3
        else:
            hips = wcm + 16 - (w - 28) * 0.25
            hip_band = 2.5
        for ins in inseams:
            m = {"waist": [_r(wcm - 1.3), _r(wcm + 1.3)], "hips": [_r(hips - hip_band), _r(hips + hip_band)]}
            label = str(w)
            if ins:
                m["inseam"] = list(INSEAM[g][ins])
                label = f"{w}{ins}"
            rows.append((label, m))
    return rows


def _alpha_bottom_rows(gender: str, brand: dict, with_inseam: bool) -> list[tuple]:
    """Elastic-waist bottoms (joggers, gym shorts) sized S/M/L... with generous ranges."""
    rows = []
    tall = "tall" in brand["tags"]
    for label, m in _top_rows(gender, {**brand, "uk_plus": False}):
        wlo, whi = m["waist"]
        if gender == "women":
            hlo, hhi = m["hips"]
        else:
            hlo, hhi = wlo + 14, whi + 16
        out = {"waist": [_r(wlo - 2), _r(whi + 2)], "hips": [_r(hlo - 2), _r(hhi + 2)]}
        if with_inseam:
            g = "women" if gender == "women" else "men"
            band = INSEAM[g]["L" if tall else "R"]
            out["inseam"] = [band[0] - 1, band[1] + 2]
        rows.append((label, out))
    return rows


def size_chart(brand: dict, gender: str, category: str) -> dict:
    if category in TOPS or category == "dress":
        rows = _top_rows(gender, brand)
        if category != "dress":
            rows = [(label, {k: v for k, v in m.items() if k != "hips"}) for label, m in rows]
    elif category in ("jeans", "trousers"):
        rows = _waist_label_rows(gender, brand, with_inseam=True)
    elif category == "joggers":
        rows = _alpha_bottom_rows(gender, brand, with_inseam=True)
    elif category == "shorts":
        rows = (
            _waist_label_rows(gender, brand, with_inseam=False)
            if "waist" in brand
            else _alpha_bottom_rows(gender, brand, with_inseam=False)
        )
    else:
        raise ValueError(category)
    return {"unit": "cm", "source": "brand", "sizes": [{"label": label, "measurements": m} for label, m in rows]}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def generate(seed: int = 42) -> dict:
    rng = random.Random(seed)
    products = []
    for brand in BRANDS:
        for gender, cats in brand["cats"].items():
            for category in cats:
                templates = TEMPLATES[category][:]
                rng.shuffle(templates)
                count = brand.get("per_category", rng.choice([2, 2, 3]))
                for title, materials, desc, fit_tag in templates[:count]:
                    palette = DENIM_COLORS if "denim" in materials else COLORS
                    colors = rng.sample(palette, rng.choice([1, 2, 3]))
                    lo, hi = brand["price"]
                    price = rng.uniform(lo, hi) * PRICE_FACTOR[category] / 0.9
                    price = max(499, round(price / 100) * 100 - 1)
                    chart = size_chart(brand, gender, category)
                    labels = [s["label"] for s in chart["sizes"]]
                    out_of_stock = set(rng.sample(labels, k=min(len(labels) // 6, 3))) if len(labels) > 4 else set()
                    who = {"men": "Men's", "women": "Women's", "unisex": "Unisex"}[gender]
                    products.append({
                        "external_id": f"seed:{brand['slug']}:{gender}:{_slug(title)}",
                        "source": "seed",
                        "store": brand["name"],
                        "brand": brand["name"],
                        "title": f"{who} {title}",
                        "description": f"{desc} {brand['blurb']}",
                        "category": category,
                        "gender": gender,
                        "price": float(price),
                        "currency": "INR",
                        "colors": colors,
                        "materials": materials,
                        "tags": sorted(set(brand["tags"] + [fit_tag])),
                        "image_url": None,
                        "product_url": None,
                        "sizes_available": [label for label in labels if label not in out_of_stock],
                        "size_chart": chart,
                    })
    return {"source": "seed", "note": "Fictional demo catalog generated by app.seed.generate", "products": products}


if __name__ == "__main__":
    data = generate()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1))
    print(f"Wrote {len(data['products'])} products to {OUT}")
