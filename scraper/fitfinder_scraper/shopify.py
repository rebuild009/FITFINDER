"""Scrape a public Shopify store's /products.json into FitFinder catalog items."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from urllib import robotparser

import httpx
from bs4 import BeautifulSoup

from .charts import chart_from_html, standard_chart
from .classify import category_of, colors_of, gender_of, materials_of
from .sizes import normalise

log = logging.getLogger(__name__)

USER_AGENT = "FitFinderBot/1.0 (student project; size-inclusive fashion search)"
PAGE_SIZE = 250


@dataclass
class Store:
    domain: str
    name: str | None = None
    gender: str = "unisex"  # used when a product doesn't say
    currency: str = "INR"
    max_pages: int = 4
    tags: list[str] = field(default_factory=list)  # e.g. ["plus-size"] for a plus-size store

    @property
    def base(self) -> str:
        d = self.domain.strip().rstrip("/")
        return d if d.startswith("http") else f"https://{d}"

    @property
    def host(self) -> str:
        return re.sub(r"^https?://", "", self.base)


@dataclass
class ScrapeReport:
    store: str
    fetched: int = 0
    kept: int = 0
    skipped: dict[str, int] = field(default_factory=dict)
    charts: dict[str, int] = field(default_factory=dict)

    def skip(self, reason: str) -> None:
        self.skipped[reason] = self.skipped.get(reason, 0) + 1


def allowed_by_robots(client: httpx.Client, store: Store) -> bool:
    try:
        r = client.get(f"{store.base}/robots.txt")
    except httpx.HTTPError:
        return True
    if r.status_code != 200:
        return True
    parser = robotparser.RobotFileParser()
    parser.parse(r.text.splitlines())
    return parser.can_fetch(USER_AGENT, f"{store.base}/products.json")


def fetch_products(client: httpx.Client, store: Store, delay_s: float = 1.0) -> list[dict]:
    products: list[dict] = []
    for page in range(1, store.max_pages + 1):
        r = client.get(f"{store.base}/products.json", params={"limit": PAGE_SIZE, "page": page})
        if r.status_code == 404:
            raise RuntimeError(f"{store.host} has no /products.json (not a Shopify store, or it is disabled)")
        r.raise_for_status()
        batch = r.json().get("products", [])
        products.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        time.sleep(delay_s)
    return products


def _option_values(product: dict, *names: str) -> tuple[int | None, list[str]]:
    for opt in product.get("options", []):
        if opt.get("name", "").strip().lower() in names:
            return opt.get("position"), opt.get("values", [])
    return None, []


def normalise_product(raw: dict, store: Store, report: ScrapeReport) -> dict | None:
    title = raw.get("title", "").strip()
    tags = raw.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    product_type = raw.get("product_type", "")

    category = category_of(title, product_type, tags)
    if not category:
        report.skip("not clothing we size (accessory, footwear, unknown type)")
        return None

    size_pos, size_values = _option_values(raw, "size", "sizes")
    if not size_pos:
        report.skip("no size option")
        return None
    variants = raw.get("variants", [])
    available = []
    for value in size_values:
        if any(v.get(f"option{size_pos}") == value and v.get("available", True) for v in variants):
            available.append(normalise(value))
    labels = [normalise(v) for v in size_values]

    gender = gender_of(title, product_type, tags, store.gender)
    chart = chart_from_html(raw.get("body_html", ""), category)
    if chart:
        known = set(labels)
        matched = [s for s in chart["sizes"] if s["label"] in known]
        chart["sizes"] = matched or chart["sizes"]
    else:
        chart = standard_chart(category, gender, labels)
    if not chart:
        report.skip("sizes we can't map to measurements (e.g. free size)")
        return None
    report.charts[chart["source"]] = report.charts.get(chart["source"], 0) + 1

    prices = [float(v["price"]) for v in variants if v.get("price")]
    if not prices:
        report.skip("no price")
        return None
    _, color_values = _option_values(raw, "color", "colour")
    description = BeautifulSoup(raw.get("body_html") or "", "html.parser").get_text(" ", strip=True)
    images = raw.get("images") or []

    return {
        "external_id": f"shopify:{store.host}:{raw.get('handle') or raw.get('id')}",
        "source": "shopify",
        "store": store.name or store.host,
        "brand": raw.get("vendor") or store.name or store.host,
        "title": title,
        "description": description[:600],
        "category": category,
        "gender": gender,
        "price": min(prices),
        "currency": store.currency,
        "colors": colors_of(color_values, title),
        "materials": materials_of(title, description, product_type),
        "tags": sorted(set(store.tags + [t.lower() for t in tags if len(t) < 30][:8])),
        "image_url": images[0].get("src") if images else None,
        "product_url": f"{store.base}/products/{raw.get('handle')}",
        "sizes_available": available,
        "size_chart": chart,
    }


def scrape_store(store: Store, client: httpx.Client | None = None, delay_s: float = 1.0) -> tuple[list[dict], ScrapeReport]:
    own = client is None
    client = client or httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=20, follow_redirects=True)
    report = ScrapeReport(store=store.host)
    try:
        if not allowed_by_robots(client, store):
            report.skip("robots.txt disallows /products.json")
            return [], report
        raw = fetch_products(client, store, delay_s)
    finally:
        if own:
            client.close()
    report.fetched = len(raw)
    items = [p for p in (normalise_product(r, store, report) for r in raw) if p]
    report.kept = len(items)
    return items, report
