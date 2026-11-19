#!/usr/bin/env bash
# Build a self-contained FitFinder page that runs the real backend in the browser (Pyodide).
# Output: browser-demo/dist/ — index.html, assets/, py/ (backend code + catalog as JSON, and bridge.py as bridge.txt).
# Every file is text: serve it from any static host, or publish it as a claude.ai artifact.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=browser-demo/dist
rm -rf "$OUT" && mkdir -p "$OUT/py"

# 1. the React app, with relative asset paths
(cd frontend && npx vite build --base ./ --outDir "../$OUT" --emptyOutDir false >/dev/null)

# 2. backend code and real catalog; bridge.py runs them (and stands in for pydantic-settings)
python3 browser-demo/pack.py backend "$OUT/py/fitfinder.json"
cp browser-demo/bridge.py "$OUT/py/bridge.txt"  # static hosts may not serve .py

# 3. Archivo from Google Fonts instead of bundled font files, then start the backend before the app
python3 browser-demo/pack.py fonts "$OUT"
python3 browser-demo/pack.py page "$OUT/index.html"

du -sh "$OUT"; find "$OUT" -type f | sort
