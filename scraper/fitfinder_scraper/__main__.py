"""Scrape the stores in a config file and write catalog JSON per store.

    python -m fitfinder_scraper --config stores.json --out output
    python -m fitfinder_scraper --store somebrand.com --gender women --tag plus-size

Then load the results into the backend:

    cd ../backend && python -m app.cli ingest ../scraper/output/*.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .shopify import Store, scrape_store


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="fitfinder_scraper", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", help="JSON file with a list of stores (see stores.example.json)")
    ap.add_argument("--store", help="A single store domain, e.g. shop.example.com")
    ap.add_argument("--name", help="Display name for --store")
    ap.add_argument("--gender", default="unisex", choices=["men", "women", "unisex"], help="Default gender for --store")
    ap.add_argument("--tag", action="append", default=[], help="Tag every product, e.g. --tag plus-size")
    ap.add_argument("--max-pages", type=int, default=4)
    ap.add_argument("--out", default="output", help="Output folder")
    ap.add_argument("--delay", type=float, default=1.0, help="Seconds between page requests")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    stores: list[Store] = []
    if args.config:
        cfg = json.loads(Path(args.config).read_text())
        stores += [Store(**s) for s in cfg.get("stores", cfg if isinstance(cfg, list) else [])]
    if args.store:
        stores.append(Store(domain=args.store, name=args.name, gender=args.gender, tags=args.tag, max_pages=args.max_pages))
    if not stores:
        ap.error("give --config or --store")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    failed = 0
    for store in stores:
        try:
            items, report = scrape_store(store, delay_s=args.delay)
        except Exception as exc:  # one bad store shouldn't stop the rest
            print(f"✗ {store.host}: {exc}", file=sys.stderr)
            failed += 1
            continue
        path = out / f"{store.host.replace('/', '_')}.json"
        path.write_text(json.dumps({"source": "shopify", "store": store.host, "products": items}, indent=1))
        print(f"✓ {store.host}: kept {report.kept}/{report.fetched} products -> {path}")
        if report.charts:
            print(f"    size charts: {report.charts}  (product = read from the product page, standard = generic fallback)")
        for reason, n in report.skipped.items():
            print(f"    skipped {n}: {reason}")
    return 1 if failed == len(stores) else 0


if __name__ == "__main__":
    raise SystemExit(main())
