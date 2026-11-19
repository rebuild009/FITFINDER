"""Run the real FitFinder FastAPI app inside the browser (Pyodide), with no server.

bootstrap.js writes backend/ into the browser's file system, runs this file, awaits startup(),
and then sends every /api/... request from the React app to handle(). The backend code is the
same code that runs on a server; only the two things a browser can't do are swapped here:
threads (FastAPI runs plain functions on a thread pool) and a network socket.
"""

import asyncio
import os
import sys

os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/fitfinder.db")
os.environ.setdefault("CATALOG", "real")
os.environ.setdefault("OPENAI_API_KEY", "")
sys.path.insert(0, "/home/pyodide/fitfinder/backend")

import types  # noqa: E402

import anyio.to_thread  # noqa: E402
import pydantic  # noqa: E402


# pydantic-settings isn't in Pyodide. The app only needs "fields can be set from environment
# variables", so this small stand-in does that instead of shipping the package.
def SettingsConfigDict(**kwargs):
    return pydantic.ConfigDict(extra=kwargs.get("extra", "ignore"))


class BaseSettings(pydantic.BaseModel):
    def __init__(self, **values):
        for name in type(self).model_fields:
            if name not in values and name.upper() in os.environ:
                values[name] = os.environ[name.upper()]
        super().__init__(**values)


_settings_module = types.ModuleType("pydantic_settings")
_settings_module.BaseSettings = BaseSettings
_settings_module.SettingsConfigDict = SettingsConfigDict
sys.modules["pydantic_settings"] = _settings_module


async def _run_sync(func, *args, abandon_on_cancel=False, cancellable=None, limiter=None):
    return func(*args)  # no threads in the browser: run in place


anyio.to_thread.run_sync = _run_sync

from app.main import app  # noqa: E402

_lifespan = None


async def startup():
    """Create the tables and load the catalog, as the server does when it starts."""
    global _lifespan
    _lifespan = app.router.lifespan_context(app)
    await _lifespan.__aenter__()


async def handle(method: str, path: str, query: str, body: str):
    """Send one HTTP request through the ASGI app and return [status, response body]."""
    scope = {
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
        "method": method.upper(), "scheme": "http", "path": path, "raw_path": path.encode(),
        "root_path": "", "query_string": query.encode(),
        "headers": [(b"host", b"fitfinder.local"), (b"content-type", b"application/json")],
        "server": ("fitfinder.local", 80), "client": ("browser", 0),
    }
    request = [{"type": "http.request", "body": (body or "").encode(), "more_body": False}]

    async def receive():
        if request:
            return request.pop()
        await asyncio.sleep(3600)
        return {"type": "http.disconnect"}

    status, chunks = 500, []

    async def send(message):
        nonlocal status
        if message["type"] == "http.response.start":
            status = message["status"]
        elif message["type"] == "http.response.body":
            chunks.append(message.get("body", b""))

    await app(scope, receive, send)
    return [status, b"".join(chunks).decode()]
