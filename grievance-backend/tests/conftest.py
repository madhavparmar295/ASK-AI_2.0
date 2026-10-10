import os

# Settings must be in place before the app is imported.
os.environ.update({
    "ENV": "test",
    "DATABASE_URL": "sqlite://",
    "SECRET_KEY": "test-secret-key-test-secret-key-0123456789",
    "ALLOWED_EMAIL_DOMAIN": "college.edu",
    "GOOGLE_CLIENT_ID": "test-client-id",
    "DEV_LOGIN_ENABLED": "true",
    "COOKIE_SECURE": "false",
    "UNKNOWN_EMAIL_POLICY": "reject",
    "REQUIRE_HD": "true",
})

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.db import Base, get_db, make_engine
from app.main import create_app
from app.security import ratelimit
from app.seed import seed


@pytest.fixture()
def settings():
    get_settings.cache_clear()
    s = get_settings()
    yield s
    get_settings.cache_clear()


@pytest.fixture()
def db_session():
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with Session() as session:
        yield session
    Base.metadata.drop_all(engine)


@pytest.fixture()
def world(db_session):
    """Seeded data: dict with users, categories, units."""
    return seed(db_session)


@pytest.fixture()
def client(db_session, world, settings):
    ratelimit.reset()
    app = create_app()

    def _get_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as c:
        yield c


def login_as(client, key, domain="college.edu"):
    """Dev-login as a seeded user and attach the CSRF header for later requests."""
    r = client.post("/api/grievance/auth/dev-login", json={"email": f"{key}@{domain}"})
    assert r.status_code == 200, r.text
    client.headers["X-CSRF-Token"] = r.json()["csrf_token"]
    return r.json()
