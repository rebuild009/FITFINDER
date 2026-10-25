# Frontend: React + Vite + Tailwind

```bash
npm install
npm run dev        # http://localhost:5173, proxies /api to the backend on :8000
npm run build      # production build in dist/
npm run lint
```

## Structure

- `src/App.jsx`: page layout, search state, and requests
- `src/components/ProfileCard.jsx`: measurements (cm or inches), fit preference, and sample bodies. Saved in localStorage.
- `src/components/SearchBar.jsx`: natural-language search, plus a "Reading this as" breakdown of what was understood
- `src/components/FilterBar.jsx`: category, price, sort, and the "Only what fits me" toggle
- `src/components/ProductCard.jsx`: recommended size, verdict, and the deciding measurement as a tape
- `src/components/FitTape.jsx`: the tape-measure strip, showing the size's range against your body
- `src/components/ProductDrawer.jsx`: every measurement for the chosen size, every size checked, and the size chart
- `src/components/GarmentArt.jsx`: flat garment drawings for demo products without photos
- `src/lib/`: API client, unit conversion, profile storage, and display helpers

Design tokens (colours, type) live in `src/index.css` under `@theme`. The typeface is Archivo, bundled
through `@fontsource-variable/archivo` so the app works offline. Expanded widths are used for headings
and condensed widths for size labels.
