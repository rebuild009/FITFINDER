"""GPT-4o query parser. Used only when OPENAI_API_KEY is set; any failure falls back to the rule parser."""

from __future__ import annotations

import json
import logging
from functools import lru_cache

from ..config import settings
from ..fit.dimensions import CATEGORIES
from ..schemas import ParsedQuery

log = logging.getLogger(__name__)

SYSTEM_PROMPT = f"""You read clothing search queries for FitFinder, a fashion search for people whose bodies
standard sizing misses: very tall, petite, plus-size, big and tall. Turn the query into filters.

Rules:
- category: one of {sorted(CATEGORIES)} or null. Tee/henley -> tshirt; pants/chinos -> trousers; kurti -> kurta;
  sweatshirt -> hoodie; blazer/coat -> jacket; trackpants -> joggers.
- gender: men, women or unisex, only if the query says or clearly implies it; else null.
- measurements: body measurements stated in the query, converted to centimetres (1 inch = 2.54 cm).
  Keys: chest (also bust), waist, hips, shoulder, inseam, height. Bare numbers for chest/waist/hips under 70
  are inches. Heights like 6'2" -> 188; Indian shorthand "5.8" for height means 5 ft 8 in. Null when not stated.
- min_price / max_price: rupees. "under 3k" -> max_price 3000.
- colors: colour words as written (navy, olive, sky blue). materials: fabrics (linen, cotton, denim, khadi...).
- fit_preference: relaxed (loose, oversized, baggy), snug (slim, fitted), regular (if stated), else null.
- tags: any of tall, petite, plus-size, big-and-tall that the query asks for.
- size_label: a stated size, normalised: XXL -> 2XL, XXXL -> 3XL, "uk 24" -> "UK 24". Else null.
- keywords: up to 5 other product words worth matching (style, pattern, occasion). No filler words.
Return only the JSON object."""

_NUM_OR_NULL = {"type": ["number", "null"]}
_STR_OR_NULL = {"type": ["string", "null"]}

RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "category": {"type": ["string", "null"], "enum": [*sorted(CATEGORIES), None]},
        "gender": {"type": ["string", "null"], "enum": ["men", "women", "unisex", None]},
        "colors": {"type": "array", "items": {"type": "string"}},
        "materials": {"type": "array", "items": {"type": "string"}},
        "min_price": _NUM_OR_NULL,
        "max_price": _NUM_OR_NULL,
        "measurements": {
            "type": "object",
            "additionalProperties": False,
            "properties": {d: _NUM_OR_NULL for d in ("chest", "waist", "hips", "shoulder", "inseam", "height")},
            "required": ["chest", "waist", "hips", "shoulder", "inseam", "height"],
        },
        "size_label": _STR_OR_NULL,
        "fit_preference": {"type": ["string", "null"], "enum": ["snug", "regular", "relaxed", None]},
        "tags": {"type": "array", "items": {"type": "string", "enum": ["tall", "petite", "plus-size", "big-and-tall"]}},
        "keywords": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "category", "gender", "colors", "materials", "min_price", "max_price", "measurements",
        "size_label", "fit_preference", "tags", "keywords",
    ],
}

# Sanity bounds in cm; anything outside is treated as a parsing mistake and dropped.
_BOUNDS = {"chest": (50, 200), "waist": (40, 200), "hips": (50, 210), "shoulder": (25, 75), "inseam": (40, 110), "height": (120, 230)}


def llm_enabled() -> bool:
    return bool(settings.openai_api_key)


def _client():
    from openai import OpenAI

    return OpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_s, max_retries=1)


def _to_parsed(raw_text: str, data: dict) -> ParsedQuery:
    measurements = {}
    for dim, value in (data.get("measurements") or {}).items():
        if isinstance(value, (int, float)) and dim in _BOUNDS:
            lo, hi = _BOUNDS[dim]
            if lo <= value <= hi:
                measurements[dim] = round(float(value), 1)
    category = data.get("category")
    return ParsedQuery(
        text=raw_text,
        category=category if category in CATEGORIES else None,
        gender=data.get("gender") if data.get("gender") in ("men", "women", "unisex") else None,
        colors=[c.lower() for c in data.get("colors") or []][:4],
        materials=[m.lower() for m in data.get("materials") or []][:4],
        min_price=data.get("min_price"),
        max_price=data.get("max_price"),
        measurements=measurements,
        size_label=data.get("size_label") or None,
        fit_preference=data.get("fit_preference"),
        tags=[t for t in data.get("tags") or [] if t in ("tall", "petite", "plus-size", "big-and-tall")],
        keywords=[k.lower() for k in data.get("keywords") or []][:5],
    )


@lru_cache(maxsize=512)
def _call(text: str) -> str:
    response = _client().chat.completions.create(
        model=settings.openai_model,
        temperature=0,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": text}],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "parsed_query", "strict": True, "schema": RESPONSE_SCHEMA},
        },
    )
    return response.choices[0].message.content or "{}"


def parse_with_llm(text: str) -> ParsedQuery:
    """Raises on any API or validation problem so the caller can fall back."""
    return _to_parsed(text, json.loads(_call(text)))
