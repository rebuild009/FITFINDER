"""Evaluate True-Fit on real bodies (ANSUR II) against real brand size charts (data/real_catalog.json).

    python -m eval.real_fit_eval --ansur-dir /path/to/ansur      # folder with MALE.csv and FEMALE.csv

ANSUR II is public: https://www.openlab.psu.edu/ansur2/ (4,082 men, 1,986 women, US Army, 2012).
Writes eval/results/real_fit_eval.json and prints the tables.

Measurements used (mm -> cm): chestcircumference -> chest (bust for women), waistcircumference -> waist,
buttockcircumference -> hips, biacromialbreadth -> shoulder, crotchheight -> inseam, stature -> height.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path

from app.fit.dimensions import BOTTOMS, PRIMARY_DIMS, TOPS
from app.fit.engine import INSEAM_PER_HEIGHT, fit_product
from app.ingest import CATALOGS

OUT = Path(__file__).parent / "results" / "real_fit_eval.json"
COLUMNS = {"chest": "chestcircumference", "waist": "waistcircumference", "hips": "buttockcircumference",
           "shoulder": "biacromialbreadth", "inseam": "crotchheight", "height": "stature"}
SEGMENTS = {
    "men": [
        ("Men, mainstream", lambda b: b["chest"] < 110 and b["height"] < 188),
        ("Men, very tall", lambda b: b["height"] >= 188 and b["chest"] < 115),
        ("Men, plus-size", lambda b: b["chest"] >= 115 and b["height"] < 185),
        ("Men, big & tall", lambda b: b["chest"] >= 115 and b["height"] >= 185),
        ("Men, chest >= 123 cm (bigbanana's 2XL and up)", lambda b: b["chest"] >= 123),
    ],
    "women": [
        ("Women, mainstream", lambda b: b["chest"] < 104 and 157 < b["height"] < 173),
        ("Women, petite", lambda b: b["chest"] < 104 and b["height"] <= 157),
        ("Women, tall", lambda b: b["chest"] < 104 and b["height"] >= 173),
        ("Women, plus-size", lambda b: b["chest"] >= 104),
    ],
}


def load_bodies(path: Path) -> list[dict]:
    with path.open(encoding="latin-1") as f:
        return [{dim: float(row[col]) / 10 for dim, col in COLUMNS.items()} for row in csv.DictReader(f)]


def chart_groups(products: list[dict], gender: str) -> list[dict]:
    """Products sharing a category and chart score identically, so score each chart once and weight it."""
    groups: dict[str, dict] = {}
    for p in products:
        if p["gender"] not in (gender, "unisex"):
            continue
        key = json.dumps([p["store"], p["category"], p["size_chart"]], sort_keys=True)
        g = groups.setdefault(key, {"store": p["store"], "category": p["category"], "chart": p["size_chart"], "n": 0})
        g["n"] += 1
    return list(groups.values())


def run_stops(group: dict, body: dict) -> bool:
    """The body is bigger than the largest size on a primary dimension: the size run ends too soon."""
    for dim in PRIMARY_DIMS.get(group["category"], ()):
        tops = [s["measurements"][dim][1] for s in group["chart"]["sizes"] if dim in s["measurements"]]
        if tops and body.get(dim, 0) > max(tops):
            return True
    return False


def coverage(bodies, groups, segments):
    rows = []
    for name, rule in segments:
        seg = [b for b in bodies if rule(b)]
        pairs = fit75 = fit90 = fit55 = stops = 0
        for b in seg:
            for g in groups:
                r = fit_product(g["category"], g["chart"], b)
                s = r.score or 0
                pairs += g["n"]
                fit55 += g["n"] * (s >= 55)
                fit75 += g["n"] * (s >= 75)
                fit90 += g["n"] * (s >= 90)
                stops += g["n"] * run_stops(g, b)
        rows.append({"segment": name, "bodies": len(seg), "pairs": pairs,
                     "fits_55": fit55 / pairs if pairs else None, "good_fit_75": fit75 / pairs if pairs else None,
                     "true_fit_90": fit90 / pairs if pairs else None, "size_run_ends": stops / pairs if pairs else None})
    return rows


def usual_label(bodies, groups, reference):
    """Shopper finds their size on one reference chart, then buys that label everywhere else (tops/dresses).

    Counts how often that label fits (score >= 75), and, when it doesn't, how often the engine finds a size
    of the same product that does. Like the paper's baseline this uses the engine to judge both, so it shows
    the value of reading each chart, not real-world fit.
    """
    ref = next(g for g in groups if g["store"] == reference[0] and g["category"] == reference[1])
    targets = [g for g in groups if g is not ref and (g["category"] in TOPS or g["category"] == "dress")]
    tried = label_ok = rescued = label_missing = 0
    shoppers = 0
    for b in bodies:
        r = fit_product(ref["category"], ref["chart"], b)
        if (r.score or 0) < 75:  # only shoppers whose label genuinely fits them on the reference chart
            continue
        label = r.best_size
        shoppers += 1
        for g in targets:
            sizes = {s["label"]: s for s in g["chart"]["sizes"]}
            tried += g["n"]
            if label not in sizes:
                label_missing += g["n"]
                ok = False
            else:
                one = {**g["chart"], "sizes": [sizes[label]]}
                ok = (fit_product(g["category"], one, b).score or 0) >= 75
            label_ok += g["n"] * ok
            if not ok and (fit_product(g["category"], g["chart"], b).score or 0) >= 75:
                rescued += g["n"]
    failed = tried - label_ok
    return {"reference_chart": f"{reference[0]} {reference[1]}", "shoppers": shoppers, "pairs": tried,
            "label_fits": label_ok / tried, "label_not_offered": label_missing / tried,
            "engine_finds_fit_when_label_fails": rescued / failed if failed else None}


def robustness(bodies, groups, sigmas=(1.0, 2.0), n=500, seed=7):
    """How often measurement error changes the recommended size, over pairs where a good fit (>= 75) was found."""
    rng = random.Random(seed)
    sample = rng.sample(bodies, min(n, len(bodies)))
    out = {}
    for sigma in sigmas:
        changed = total = 0
        for b in sample:
            noisy = {k: v + rng.gauss(0, sigma) for k, v in b.items()}
            for g in groups:
                ra = fit_product(g["category"], g["chart"], b)
                a, c = ra.best_size, fit_product(g["category"], g["chart"], noisy).best_size
                if (ra.score or 0) >= 75:
                    total += g["n"]
                    changed += g["n"] * (a != c)
        out[f"sigma_{sigma:g}cm"] = changed / total if total else None
    return out


def inseam_estimate(bodies, groups):
    """Compare the engine's inseam-from-height estimate with measured crotch height, and its effect on size."""
    errors = [b["height"] * INSEAM_PER_HEIGHT - b["inseam"] for b in bodies]
    bottoms = [g for g in groups if g["category"] in BOTTOMS and any("inseam" in s["measurements"] for s in g["chart"]["sizes"])]
    same = total = 0
    for b in bodies:
        without = {k: v for k, v in b.items() if k != "inseam"}
        for g in bottoms:
            total += g["n"]
            same += g["n"] * (fit_product(g["category"], g["chart"], b).best_size == fit_product(g["category"], g["chart"], without).best_size)
    errors.sort()
    return {"ratio_used": INSEAM_PER_HEIGHT, "mean_measured_ratio": sum(b["inseam"] / b["height"] for b in bodies) / len(bodies),
            "median_error_cm": errors[len(errors) // 2], "mean_abs_error_cm": sum(abs(e) for e in errors) / len(errors),
            "bottoms_with_inseam_in_chart": len(bottoms), "same_size_when_estimated": same / total if total else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ansur-dir", required=True)
    args = ap.parse_args()
    products = json.loads(CATALOGS["real"].read_text())["products"]
    results = {"catalog": {"products": len(products), "stores": sorted({p["store"] for p in products})}}
    for gender, csv_name, reference in (("men", "MALE.csv", ("bigbanana", "tshirt")),
                                        ("women", "FEMALE.csv", ("Janasya", "kurta"))):
        bodies = load_bodies(Path(args.ansur_dir) / csv_name)
        groups = chart_groups(products, gender)
        results[gender] = {
            "bodies": len(bodies), "products": sum(g["n"] for g in groups), "distinct_charts": len(groups),
            "coverage": coverage(bodies, groups, SEGMENTS[gender]),
            "usual_label": usual_label(bodies, groups, reference),
            "robustness": robustness(bodies, groups),
            "inseam": inseam_estimate(bodies, groups),
        }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(results, indent=1))
    print(json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
