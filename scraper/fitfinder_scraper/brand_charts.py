"""Size charts a brand publishes outside the product description.

Two kinds of store are covered:

* **script**: the theme embeds a body-measurement chart per category in each product
  page (bigbanana's `SIZE_CHARTS = {tshirt: [{size, chest: [lo, hi], ...}], ...}`).
  One page is enough, because the chart is the same for every product of a category.
* **kiwi**: the store uses the Kiwi Sizing app. Each product page asks Kiwi for the
  chart that matches it; we make the same public request the page makes, one product
  at a time with a pause, and cache by chart id.

* **page**: the theme prints a size table on each product page (Instafab Plus, Jaywalking,
  Bluorng). One page request per product, with a pause.
* **variant**: the page shows the chart for the selected size only, as "Label value" pairs
  (Nobero). One request per size of the product (one colour), with a pause.

A store can say its chart lists garment measurements (`"measures": "garment"` in the config);
those are turned into body ranges by subtracting standard ease (charts._EASE).

All return charts in the scraper's usual format with source "brand", which the
backend shows as medium confidence (a real brand chart, but per category, not per item).
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Callable

import httpx
from bs4 import BeautifulSoup

from .charts import _EASE, CM, chart_from_rows
from .sizes import normalise

log = logging.getLogger(__name__)

ChartLookup = Callable[[dict, str], "dict | None"]
_DIM_KEYS = {"chest": "chest", "bust": "chest", "waist": "waist", "hip": "hips", "hips": "hips", "shoulder": "shoulder", "inseam": "inseam"}


# ---------------------------------------------------------------- script charts (bigbanana)

def parse_script_charts(html: str) -> dict[str, list[dict]]:
    """Read `SIZE_CHARTS = { type: [ { size: 'XL', chest: [a, b], ... }, ... ], ... };` from page HTML."""
    i = html.find("SIZE_CHARTS = {")
    if i < 0:
        return {}
    depth, j = 0, html.index("{", i)
    for k in range(j, len(html)):
        depth += {"{": 1, "}": -1}.get(html[k], 0)
        if depth == 0:
            body = html[j:k + 1]
            break
    else:
        return {}
    # JS object literal -> JSON: quote keys, single to double quotes.
    body = re.sub(r"([{,]\s*)([A-Za-z_]\w*)\s*:", r'\1"\2":', body).replace("'", '"')
    return json.loads(body)


def script_chart(rows: list[dict]) -> dict:
    sizes = []
    for row in rows:
        m = {_DIM_KEYS[k]: [float(v[0]), float(v[1])] for k, v in row.items() if k in _DIM_KEYS and isinstance(v, list)}
        sizes.append({"label": normalise(row["size"]), "measurements": m})
    return {"unit": "cm", "source": "brand", "sizes": sizes}


# The theme's own rules for which chart a product uses, by title (copied from its page script).
_BIGBANANA_TYPES = [
    (r"t-shirt|sweatshirt|sweater|vest", "tshirt"),
    (r"shirt|kurta|jacket", "shirt"),
    (r"jogger|short", "trackpants"),
    (r"jean|trouser", "trouser"),
]


_BY_CATEGORY = {"tshirt": "tshirt", "polo": "tshirt", "hoodie": "tshirt", "shirt": "shirt", "kurta": "shirt",
                "jacket": "shirt", "joggers": "trackpants", "shorts": "trackpants", "jeans": "trouser", "trousers": "trouser"}


def script_lookup(client: httpx.Client, base: str, raw_products: list[dict], delay_s: float = 1.0,
                  measures: str | None = None) -> ChartLookup | None:
    if not raw_products:
        return None
    r = client.get(f"{base}/products/{raw_products[0]['handle']}")
    charts = parse_script_charts(r.text) if r.status_code == 200 else {}
    if not charts:
        log.warning("no SIZE_CHARTS found on %s", base)
        return None
    built = {name: script_chart(rows) for name, rows in charts.items()}

    def lookup(raw: dict, category: str) -> dict | None:
        title = raw.get("title", "").lower()
        name = next((n for pattern, n in _BIGBANANA_TYPES if re.search(pattern, title)), None)
        # Titles the theme's rules miss ("Round Neck", "Trackpant") still get their category's chart.
        name = name or _BY_CATEGORY.get(category)
        return json.loads(json.dumps(built[name])) if name in built else None

    return lookup


# ---------------------------------------------------------------- Kiwi Sizing charts

KIWI_API = "https://app.kiwisizing.com/api/getSizingChart"
_BODY_HINT = re.compile(r"your (?:bust|chest|waist|hips?|body)|measure (?:yourself|your)|take your measurements|fullest part", re.I)
_GARMENT_HINT = re.compile(r"garment measurement|product measurement|measured flat|laid flat|garment size", re.I)


def kiwi_shop(client: httpx.Client, base: str) -> str | None:
    """The store's myshopify domain, which Kiwi uses as its key (printed in every page)."""
    r = client.get(base)
    m = re.search(r'KiwiSizing\.shop\s*=\s*"([^"]+)"', r.text) or re.search(r"Shopify\.shop\s*=\s*\"([^\"]+)\"", r.text)
    return m.group(1) if m else None


def _kiwi_table_rows(table: dict) -> tuple[list[list[str]], str | None]:
    rows, units = [], set()
    for row in table.get("data", []):
        cells = []
        for cell in row:
            value = str(cell.get("value", "")).strip()
            if cell.get("unitType") in ("in", "cm"):
                units.add(cell["unitType"])
            cells.append(BeautifulSoup(value, "html.parser").get_text(" ", strip=True))
        rows.append(cells)
    unit = units.pop() if len(units) == 1 else None
    return rows, unit


def kiwi_chart(payload: dict, category: str, measures: str | None = None) -> tuple[int | None, dict | None]:
    """Pick the first enabled sizing whose table parses; return (sizing id, chart)."""
    for sizing in payload.get("sizings", []):
        if not sizing.get("isEnabled", True):
            continue
        text = BeautifulSoup(json.dumps(sizing.get("layout", "")), "html.parser").get_text(" ")
        tables = list((sizing.get("tables") or {}).values())
        for table in tables:
            context = f"{table.get('header', '')} {table.get('footer', '')} {text}"
            garment = measures == "garment" if measures else bool(_GARMENT_HINT.search(context)) and not _BODY_HINT.search(context)
            rows, unit = _kiwi_table_rows(table)
            chart = chart_from_rows(rows, category, context, garment=garment, unit=unit, source="brand")
            if chart:
                return sizing.get("id"), chart
    return None, None


def kiwi_lookup(client: httpx.Client, base: str, raw_products: list[dict], delay_s: float = 1.0,
                measures: str | None = None) -> ChartLookup | None:
    shop = kiwi_shop(client, base)
    if not shop:
        log.warning("could not find the Kiwi shop id on %s", base)
        return None
    cache: dict[tuple, dict | None] = {}

    def lookup(raw: dict, category: str) -> dict | None:
        tags = raw.get("tags") or []
        tags = tags if isinstance(tags, list) else [t.strip() for t in tags.split(",")]
        params = {
            "shop": shop, "product": raw.get("id"), "title": raw.get("title", ""),
            "tags": ",".join(tags), "metafields": "[]", "type": raw.get("product_type", ""),
            "vendor": raw.get("vendor", ""), "collections": "",
        }
        try:
            r = client.get(KIWI_API, params=params)
            time.sleep(delay_s)
            payload = r.json() if r.status_code == 200 else {}
        except (httpx.HTTPError, ValueError):
            return None
        ids = tuple(s.get("id") for s in payload.get("sizings", []))
        key = (ids, category)
        if key not in cache:
            cache[key] = kiwi_chart(payload, category, measures)[1]
        chart = cache[key]
        return json.loads(json.dumps(chart)) if chart else None

    return lookup


# ---------------------------------------------------------------- tables printed on the product page

def page_chart(html: str, category: str, measures: str | None = None) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")
    for table in soup.find_all("table"):
        rows = [[c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])] for tr in table.find_all("tr")]
        # the heading or note just before the table often says "to fit" or "garment measurement"
        before = " ".join(e.get_text(" ", strip=True) for e in table.find_all_previous(["h2", "h3", "h4", "p", "strong"], limit=3))
        context = f"{before} {table.get_text(' ', strip=True)}"
        if measures:
            garment = measures == "garment"
        else:
            garment = bool(_GARMENT_HINT.search(context)) and not re.search(r"to\s+fit", context, re.I)
        chart = chart_from_rows(rows, category, context, garment=garment, source="brand")
        if chart:
            return chart
    return None


def page_lookup(client: httpx.Client, base: str, raw_products: list[dict], delay_s: float = 1.0,
                measures: str | None = None) -> ChartLookup | None:
    def lookup(raw: dict, category: str) -> dict | None:
        try:
            r = client.get(f"{base}/products/{raw['handle']}")
            time.sleep(delay_s)
        except httpx.HTTPError:
            return None
        return page_chart(r.text, category, measures) if r.status_code == 200 else None

    return lookup


# ---------------------------------------------------------------- one size at a time (Nobero)

_PAIR = re.compile(r">\s*((?:To Fit )?[A-Za-z ]{3,20}?)\s*</span>\s*<span[^>]*>\s*([\d.]+)\s*<", re.I)
_VARIANT_DIMS = {"chest": "chest", "waist": "waist", "hip": "hips", "hips": "hips", "shoulder": "shoulder", "inseam": "inseam"}


def variant_measurements(html: str) -> dict[str, float]:
    """{dim: body cm} from 'Chest 41 / To Fit Chest 38 / Shoulder 17.4' pairs (inches). "To fit" wins over garment."""
    garment, body = {}, {}
    for label, value in _PAIR.findall(html):
        label = label.strip().lower()
        fit = label.startswith("to fit ")
        dim = _VARIANT_DIMS.get(label.removeprefix("to fit ").strip())
        if dim:
            (body if fit else garment).setdefault(dim, float(value) * CM)
    out = {d: v - _EASE[d] for d, v in garment.items()}
    out.update(body)
    return out


def variant_lookup(client: httpx.Client, base: str, raw_products: list[dict], delay_s: float = 1.0,
                   measures: str | None = None) -> ChartLookup | None:
    def lookup(raw: dict, category: str) -> dict | None:
        size_opt = next((i for i, o in enumerate(raw.get("options", [])) if o.get("name", "").lower() in ("size", "sizes")), None)
        if size_opt is None:
            return None
        seen, points = set(), []
        for v in raw.get("variants", []):  # first variant of each size, so one colour's worth of requests
            label = normalise(v.get(f"option{size_opt + 1}") or "")
            if not label or label in seen:
                continue
            seen.add(label)
            try:
                r = client.get(f"{base}/products/{raw['handle']}", params={"variant": v["id"]})
                time.sleep(delay_s)
            except httpx.HTTPError:
                continue
            m = variant_measurements(r.text) if r.status_code == 200 else {}
            if m:
                points.append((label, m))
        if len(points) < 2:
            return None
        # each size is one point; make ranges that meet halfway, like single-value tables
        rows = [["Size", *sorted({d for _, m in points for d in m})]]
        rows += [[label] + [f"{m.get(d, ''):.1f}" if d in m else "" for d in rows[0][1:]] for label, m in points]
        return chart_from_rows(rows, category, "cm", garment=False, unit="cm", source="brand")

    return lookup


PROVIDERS = {"script": script_lookup, "kiwi": kiwi_lookup, "page": page_lookup, "variant": variant_lookup}
