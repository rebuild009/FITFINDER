# FitFinder

Fashion search for people standard sizes skip: very tall, petite, plus-size, big and tall.

You enter your measurements once. FitFinder checks every size of every product against your body, then
tells you which size fits and where it would be tight or loose. A "2XL" means different things at
different brands; FitFinder compares measurements, not labels.

## What's in V1

- **True-Fit engine**: deterministic size matching. Your body is compared against each size's chart, one
  measurement at a time, weighted by garment type, and adjusted for how you like clothes to fit.
- **Natural-language search**: "shirt for a 52 inch chest under 3000" becomes Shirts, chest 132 cm,
  up to ₹3,000. A built-in parser works with no setup. GPT-4o takes over when `OPENAI_API_KEY` is set
  and falls back to the built-in parser on any error.
- **Data pipeline**: a scraper for public Shopify stores. It reads the brand's own size charts (from the
  product page, the theme's embedded chart, or the Kiwi Sizing app) and falls back to standard charts
  only where a brand publishes none.
- **Real catalog** (default): 1,722 products from 9 Indian brands, every one with the brand's own size
  chart. Men: bigbanana (2XL–10XL), Instafab Plus (3XL–6XL), My Designation, Nobero, Blackberrys,
  Jaywalking and Bluorng (XXXS–5XL). Women: Janasya and Angrakhaa (up to 7XL). Collected 19–20 Nov 2026
  with `scraper/stores.india.json`. The original synthetic catalog of 8 fictional brands is still
  available with `CATALOG=demo`.
- **Evaluation on real data**: True-Fit run on 6,068 real bodies (ANSUR II) against all 1,722 products
  and their brand charts. See [docs/real_evaluation.md](docs/real_evaluation.md).
- **Browser version**: the same app running entirely in the browser (Python via Pyodide), shareable as a
  link. See [browser-demo/README.md](browser-demo/README.md).
- **Web app**: React + Tailwind, with a measurement card, search, fit-ranked results, and a per-size
  breakdown drawn as measuring tape.

## Run it

You need Python 3.11+ and Node 20+. Use two terminals.

```bash
# 1. backend: http://localhost:8000 (API docs at /docs)
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

```bash
# 2. frontend: http://localhost:5173
cd frontend
npm install
npm run dev
```

The backend uses SQLite and loads the real-store catalog on first start, so nothing else is needed. Set `CATALOG=demo` to use the synthetic catalog instead.

**PostgreSQL** (optional): run `docker compose up -d db`, then set
`DATABASE_URL=postgresql://fitfinder:fitfinder@localhost:5432/fitfinder` in `backend/.env`.

**GPT-4o** (optional): set `OPENAI_API_KEY` in `backend/.env`. The page shows which parser read each query.

**Real stores**: see [scraper/README.md](scraper/README.md).

```bash
cd scraper && pip install -r requirements.txt
python -m fitfinder_scraper --store somebrand.com --gender women --tag plus-size
cd ../backend && python -m app.cli ingest ../scraper/output/*.json
```

## How it fits together

```mermaid
flowchart LR
    S[Shopify stores] -->|products.json| SC[scraper]
    SC -->|catalog JSON| IN[ingest]
    SEED[real + demo catalogs] --> IN
    IN --> DB[(SQLite / PostgreSQL)]
    U[Shopper] -->|measurements + query| FE[React app]
    FE -->|/api/search| API[FastAPI]
    API --> P{query parser}
    P -->|key set| GPT[GPT-4o]
    P -->|no key or error| R[rule parser]
    API --> DB
    API --> TF[True-Fit engine]
    TF -->|best size, verdict, per-measurement notes| FE
```

## How True-Fit decides

Every size chart stores the body-measurement range that size is cut for, for example
`2XL: chest 112–119 cm`. For each product, the engine works through these steps:

1. It compares each of your measurements with each size's range. Inside the range scores well, and
   where you sit inside it matters: a snug-fit preference likes the top of the range, relaxed likes the
   bottom. Outside the range, tight is penalised harder than loose, and too short harder than too long,
   since hems can be taken up.
2. It weights each measurement by garment type: chest leads for tops, waist for bottoms, and chest,
   waist and hips together for dresses.
3. It caps the score when something can't work. A chest that won't close makes a size unwearable
   however well the rest fits.
4. It picks the best in-stock size and gives it a verdict: True Fit (90+), Good fit (75+),
   Fits with a compromise (55+), or Won't fit.

When inseam is missing it is estimated from height, and the estimate is labelled as such. Every
result says where its size chart came from (the product page, the brand, or a standard chart), so
you know how much to trust it.

## Project layout

```
backend/    FastAPI app, True-Fit engine, search, real and demo catalogs, tests
frontend/   React + Vite + Tailwind web app
scraper/    Shopify data pipeline, tests
docs/       notes and diagrams
```

## Tests

```bash
cd backend && python -m pytest -q     # engine, parser, GPT-4o (mocked), API, ingest
cd scraper && python -m pytest -q     # labels, size-chart parsing, end-to-end scrape (mocked)
cd frontend && npm run lint && npm run build
```

## Next (V2)

- A custom-trained fit model that learns from returns and reviews ("runs small") on top of the
  deterministic engine
- Embedding search (Pinecone) for "more like this"
- Accounts with saved profiles and wishlists
- GPT-4o reading size charts published as images
