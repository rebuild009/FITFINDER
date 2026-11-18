"""GPT-4o parsing, exercised against a mocked OpenAI endpoint (no key or network needed)."""

import json

import httpx
import pytest
from openai import OpenAI

from app.config import settings
from app.search import llm, service


def _completion(content: dict) -> dict:
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 0,
        "model": "gpt-4o",
        "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": json.dumps(content)}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


LLM_ANSWER = {
    "category": "kurta",
    "gender": "women",
    "colors": ["Maroon"],
    "materials": [],
    "min_price": None,
    "max_price": 2500,
    "measurements": {"chest": 121.9, "waist": None, "hips": None, "shoulder": None, "inseam": None, "height": 999},
    "size_label": None,
    "fit_preference": "relaxed",
    "tags": ["plus-size"],
    "keywords": ["festive"],
}


@pytest.fixture()
def with_key(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "sk-test")
    llm._call.cache_clear()
    yield
    llm._call.cache_clear()


def _mock_client(monkeypatch, handler):
    client = OpenAI(api_key="sk-test", http_client=httpx.Client(transport=httpx.MockTransport(handler)), max_retries=0)
    monkeypatch.setattr(llm, "_client", lambda: client)


def test_request_shape_and_parsing(with_key, monkeypatch):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json=_completion(LLM_ANSWER))

    _mock_client(monkeypatch, handler)
    parsed, parser, notes = service.parse("loose maroon festive kurta for a 48 inch bust, under 2.5k")

    assert seen["path"].endswith("/chat/completions")
    fmt = seen["body"]["response_format"]
    assert fmt["type"] == "json_schema" and fmt["json_schema"]["strict"] is True
    assert seen["body"]["model"] == settings.openai_model and seen["body"]["temperature"] == 0

    assert parser == settings.openai_model and notes == []
    assert parsed.category == "kurta" and parsed.gender == "women"
    assert parsed.colors == ["maroon"] and parsed.max_price == 2500
    assert parsed.measurements == {"chest": 121.9}  # height 999 is rejected as implausible
    assert parsed.fit_preference == "relaxed" and parsed.keywords == ["festive"]


def test_falls_back_to_rules_when_the_api_fails(with_key, monkeypatch):
    _mock_client(monkeypatch, lambda request: httpx.Response(401, json={"error": {"message": "bad key"}}))
    parsed, parser, notes = service.parse("linen shirt for 52 inch chest under 3000")
    assert parser == "rules" and notes
    assert parsed.category == "shirt" and parsed.measurements == {"chest": 132.1}


def test_rules_fill_gaps_the_model_left(with_key, monkeypatch):
    answer = {**LLM_ANSWER, "max_price": None, "measurements": {k: None for k in LLM_ANSWER["measurements"]}}
    _mock_client(monkeypatch, lambda request: httpx.Response(200, json=_completion(answer)))
    parsed, _, _ = service.parse("kurta bust 48 under 2500")
    assert parsed.max_price == 2500 and parsed.measurements["chest"] == 121.9


def test_no_key_means_rules():
    assert not llm.llm_enabled()
    _, parser, _ = service.parse("shirt")
    assert parser == "rules"
