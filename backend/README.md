# Backend: FastAPI

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload       # http://localhost:8000, interactive docs at /docs
python -m pytest -q
```

Settings come from environment variables or `backend/.env`; see `.env.example`. All are optional.

## API

| Method | Path | What it does |
| --- | --- | --- |
| GET | `/api/health` | Status and product count |
| GET | `/api/meta` | Categories, brands, price range, active parser |
| POST | `/api/search` | Natural-language search: `{query, profile, filters, only_fitting, sort, limit, offset}` |
| POST | `/api/match` | The same without a query (filters only) |
| POST | `/api/parse` | Only parse a query, for debugging |
| GET | `/api/products/{id}` | Product and size chart |
| POST | `/api/products/{id}/fit` | Product, best size and a per-size breakdown for a profile |

A profile looks like this:

```json
{"unit": "in", "gender": "men", "fit_preference": "regular",
 "measurements": {"chest": 52, "waist": 46, "shoulder": 20.5, "height": 74}}
```

Measurements typed into a query override the profile for that search. Fit notes come back in the
profile's unit.

## Code map

- `app/fit/engine.py`: True-Fit scoring (`evaluate_dimension` → `score_size` → `fit_product`)
- `app/fit/dimensions.py`: categories, per-category weights, tolerances
- `app/search/rules.py`: rule-based query parser; `app/search/llm.py`: GPT-4o parser
- `app/search/service.py`: filtering, relevance, fit ranking
- `app/ingest.py` / `app/cli.py`: load the demo catalog or scraper output (`python -m app.cli ingest FILE`)
- `app/seed/generate.py`: regenerates `data/seed_catalog.json` (fictional brands)
