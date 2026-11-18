import os

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite://")  # overridden per test below
os.environ["OPENAI_API_KEY"] = ""
os.environ.setdefault("CATALOG", "demo")  # API tests assert on the fixed synthetic catalog


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from sqlalchemy.orm import sessionmaker

    from app import db, main
    from app.db import make_engine

    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(db, "SessionLocal", session_factory)
    monkeypatch.setattr(main, "SessionLocal", session_factory)
    monkeypatch.setattr(main, "init_db", lambda: db.init_db(engine))

    def _session():
        with session_factory() as s:
            yield s

    main.app.dependency_overrides[db.get_session] = _session
    from fastapi.testclient import TestClient

    with TestClient(main.app) as c:
        yield c
    main.app.dependency_overrides.clear()
