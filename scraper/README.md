# Scraper: data pipeline

Pulls products from public Shopify stores and turns them into catalog JSON the backend can load.

Most Shopify stores publish their catalog at `https://<store>/products.json`. Open that URL in a browser.
If you see JSON, the scraper can read the store.

## Run it

```bash
cd scraper
pip install -r requirements.txt

# one store
python -m fitfinder_scraper --store somebrand.com --name "Some Brand" --gender women --tag plus-size

# the three real stores behind the bundled catalog
python -m fitfinder_scraper --config stores.india.json

# or several, from a config file
cp stores.example.json stores.json   # edit the list
python -m fitfinder_scraper --config stores.json

# load into the backend
cd ../backend
python -m app.cli ingest ../scraper/output/*.json
```

Each run prints how many products were kept, where each size chart came from, and why anything was skipped.

## What it does with each product

1. **Category**: from product type, then title, then tags. Accessories and footwear are skipped.
2. **Sizes**: from the variant option named Size. Labels are normalised (`XX-Large` → `2XL`, `uk 24` → `UK 24`), and sold-out sizes are dropped from `sizes_available`.
3. **Size chart** (what True-Fit compares against):
   - **product**: a `<table>` in the product description is parsed, in either orientation. It handles inches or cm, ranges or single values, and garment or "pit to pit" measurements. Garment measurements are converted to body measurements by subtracting typical ease.
   - **brand**: the brand's own chart for the product's category, read from where the store keeps it.
     Set `"charts"` on a store in the config: `"script"` for themes that embed a chart in the page
     (bigbanana), `"kiwi"` for stores using the Kiwi Sizing app (Janasya, Angrakhaa). For Kiwi stores
     the scraper makes the same public chart request the product page makes, one product at a time
     with a pause. See `fitfinder_scraper/brand_charts.py`.
   - **standard**: if there's no table, a generic chart is mapped onto the product's labels (`XL`, `2XL`, `34/32`...). The app shows these fits as lower confidence.
   - Products whose sizes can't be mapped at all (e.g. "Free Size") are skipped.
4. **Gender, colours, materials** from tags, options and text, with the store's `gender` as the default.

## Being a good citizen

The scraper checks `robots.txt` and skips the store if `/products.json` is disallowed. It identifies itself with a user agent and waits a second between pages. Only scrape stores whose terms allow it, and keep page counts low.

## Tests

```bash
python -m pytest -q
```

The tests run against a saved fixture (`tests/fixtures/products.json`), so they need no network access.
