"""Body dimensions, categories and how much each dimension matters per category.

All measurements inside the engine are BODY measurements in centimetres.
Size charts store, for each size, the body-measurement range that size is cut for.
"""

DIMENSIONS = ("chest", "waist", "hips", "shoulder", "inseam", "height")

# Girth dimensions: body bigger than the range = too tight, smaller = too loose.
# Length dimensions: body bigger than the range = garment too short, smaller = too long.
GIRTH_DIMS = {"chest", "waist", "hips", "shoulder"}
LENGTH_DIMS = {"inseam", "height"}

# How far outside a range (cm) still counts as "a little" off.
TOLERANCE_CM = {
    "chest": 2.5,
    "waist": 2.5,
    "hips": 2.5,
    "shoulder": 2.0,
    "inseam": 2.5,
    "height": 4.0,
}

DIM_LABELS = {
    "chest": "Chest / bust",
    "waist": "Waist",
    "hips": "Hips",
    "shoulder": "Shoulder",
    "inseam": "Inseam",
    "height": "Height",
}

TOPS = ("tshirt", "shirt", "polo", "hoodie", "jacket", "kurta", "top")
BOTTOMS = ("jeans", "trousers", "joggers", "shorts")
DRESSES = ("dress",)

CATEGORIES = {
    "tshirt": "T-shirts",
    "shirt": "Shirts",
    "polo": "Polos",
    "hoodie": "Hoodies",
    "jacket": "Jackets",
    "kurta": "Kurtas",
    "top": "Tops",
    "jeans": "Jeans",
    "trousers": "Trousers",
    "joggers": "Joggers",
    "shorts": "Shorts",
    "dress": "Dresses",
}

_TOP_WEIGHTS = {"chest": 1.0, "shoulder": 0.6, "waist": 0.4, "height": 0.45}
_BOTTOM_WEIGHTS = {"waist": 1.0, "hips": 0.7, "inseam": 0.5}
_DRESS_WEIGHTS = {"chest": 1.0, "waist": 0.9, "hips": 0.8, "height": 0.45}

CATEGORY_WEIGHTS = {
    **{c: _TOP_WEIGHTS for c in TOPS},
    **{c: _BOTTOM_WEIGHTS for c in BOTTOMS},
    "shorts": {"waist": 1.0, "hips": 0.7},
    "dress": _DRESS_WEIGHTS,
}

# A size cannot be judged without at least one of these.
PRIMARY_DIMS = {
    **{c: {"chest"} for c in TOPS},
    **{c: {"waist"} for c in BOTTOMS},
    "dress": {"chest", "waist", "hips"},
}


# Dimensions where only "too small" matters: a shirt that is roomy at the waist still fits.
TIGHT_ONLY_DIMS = {c: {"waist"} for c in TOPS}


def category_group(category: str) -> str:
    if category in TOPS:
        return "tops"
    if category in BOTTOMS:
        return "bottoms"
    return "dresses"
