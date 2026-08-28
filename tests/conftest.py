import os

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Point the app at an isolated test database before importing anything that
# reads settings. Derived from APP_DATABASE_URL by suffixing the db name.
_BASE_URL = os.environ.get(
    "APP_DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5544/realestate",
)
_TEST_URL = _BASE_URL if _BASE_URL.endswith("_test") else _BASE_URL + "_test"
os.environ["APP_DATABASE_URL"] = _TEST_URL
os.environ["APP_ENVIRONMENT"] = "test"

from realestate_rag_agent.core.db import Base, get_session  # noqa: E402
from realestate_rag_agent.main import create_app  # noqa: E402
from realestate_rag_agent.repositories import models  # noqa: E402,F401


def _ensure_test_database() -> None:
    url = sa.make_url(_TEST_URL)
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.scalar(
            sa.text("SELECT 1 FROM pg_database WHERE datname = :n"),
            {"n": url.database},
        )
        if not exists:
            conn.execute(sa.text(f'CREATE DATABASE "{url.database}"'))
    admin.dispose()


@pytest.fixture(scope="session")
def engine():
    _ensure_test_database()
    eng = create_engine(_TEST_URL)
    with eng.begin() as conn:
        conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db_session(engine) -> Session:
    SessionTest = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionTest()
    try:
        yield session
    finally:
        session.close()
        tables = ", ".join(t.name for t in reversed(Base.metadata.sorted_tables))
        with engine.begin() as conn:
            conn.execute(sa.text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def client(db_session: Session) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    return TestClient(app)
