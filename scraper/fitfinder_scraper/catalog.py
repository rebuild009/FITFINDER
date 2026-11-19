"""Combine scraper outputs into the catalog the backend ships with, keeping only trustworthy charts.

    python -m fitfinder_scraper.catalog output/*.json -o ../backend/data/real_catalog.json

A product is kept only if
  * its size chart is the brand's own (source "brand" or "product"), not the generic fallback, and
  * the chart is physically plausible: sizes get bigger in order, and no adult size is cut for a body
    smaller than the limits below. This catches charts measured laid flat (half the chest) without saying
    so, and relaxed elastic waists read as body waists.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .classify import DRESS_STYLE

MIN_CM = {"chest": 70.0, "waist": 55.0}
MIN_CM_MEN = {"chest": 76.0, "waist": 64.0}


def problem(product: dict) -> str | None:
    chart = product.get("size_chart") or {}
    if chart.get("source") not in ("brand", "product"):
        return "no brand chart"
    limits = MIN_CM_MEN if product.get("gender") in ("men", "unisex") else MIN_CM
    rows = chart.get("sizes", [])
    for dim, low in limits.items():
        lows = [r["measurements"][dim][0] for r in rows if dim in r.get("measurements", {})]
        if any(v < low for v in lows):
            return "implausible chart"
        if any(b < a for a, b in zip(lows, lows[1:])):
            return "implausible chart"
    return None


def build(files: list[Path]) -> tuple[dict, Counter]:
    stores, kept, dropped = [], [], Counter()
    for f in files:
        data = json.loads(f.read_text())
        stores.append(data["store"])
        for p in data["products"]:
            p["brand"] = p.get("store") or p.get("brand")  # a D2C store is the brand
            if DRESS_STYLE.search(p.get("title", "")):  # outputs scraped before this rule existed
                p["category"] = "dress"
            why = problem(p)
            if why:
                dropped[(p.get("store"), why)] += 1
            else:
                kept.append(p)
    catalog = {
        "source": "shopify",
        "stores": stores,
        "note": "Real products and brand-published size charts from public Shopify stores, scraped with "
                "fitfinder_scraper (stores.india.json). Only products with the brand's own, physically "
                "plausible size chart are kept.",
        "products": kept,
    }
    return catalog, dropped


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    args = ap.parse_args()
    catalog, dropped = build(args.files)
    args.out.write_text(json.dumps(catalog, indent=0, ensure_ascii=False))
    print(f"kept {len(catalog['products'])} products from {len(catalog['stores'])} stores -> {args.out}")
    for (store, why), n in sorted(dropped.items()):
        print(f"  dropped {n:3d} from {store}: {why}")


if __name__ == "__main__":
    main()
