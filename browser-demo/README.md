# FitFinder in the browser

A single page that runs the **real FitFinder backend** (FastAPI, Pydantic, SQLAlchemy, SQLite, the parser
and the True-Fit engine) inside the browser with [Pyodide](https://pyodide.org), so anyone can use the app
from a link, with nothing installed and no server.

```
./browser-demo/build.sh     # needs Node and Python; writes browser-demo/dist/
```

Serve `browser-demo/dist/` from any static host (or publish it as a claude.ai artifact). First load takes
about 10 seconds while Python starts.

How it works:

- `bootstrap.js` (inlined into `index.html`) loads Pyodide and its FastAPI/Pydantic/SQLAlchemy/SQLite
  packages from jsDelivr, writes the backend code and catalog (`py/fitfinder.json`) into the browser's file
  system, runs `bridge.py`, and then answers every `/api/...` request from the React app through it.
- `bridge.py` runs the unchanged FastAPI app. Two things a browser can't do are swapped: FastAPI's thread
  pool (functions run in place) and `pydantic-settings` (a few-line stand-in reads environment variables).
- Product photos are hosted on the brands' sites, which a sandboxed page can't load, so the browser build
  shows FitFinder's garment illustrations; "View at store" links to the real product page.
