"""Shared pytest fixtures: an isolated SQLite DB and logged-in API clients."""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Point the app at a throwaway DB file BEFORE importing app modules.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"
os.environ["SESSION_SECRET"] = "test-secret"

from app.core import config  # noqa: E402
from app.core.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import DEMO_PASSWORD  # noqa: E402

engine = create_engine(config.DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(scope="function", autouse=True)
def fresh_db():
    """Rebuild the schema and reseed demo users before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    from app.seed import seed

    db = TestingSessionLocal()
    try:
        seed(db)
    finally:
        db.close()
    yield


def login(email: str) -> TestClient:
    """Return a TestClient with a valid session cookie for the given demo user."""
    client = TestClient(app)
    resp = client.post("/api/auth/login", json={"email": email, "password": DEMO_PASSWORD})
    assert resp.status_code == 200, resp.text
    return client


@pytest.fixture
def alice():
    return login("alice@demo.com")


@pytest.fixture
def bob():
    return login("bob@demo.com")


@pytest.fixture
def carol():
    return login("carol@demo.com")
