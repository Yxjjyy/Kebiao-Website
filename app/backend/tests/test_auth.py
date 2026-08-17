"""登录会话认证测试。"""

from collections.abc import Iterator
from datetime import timedelta

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings, get_settings
from app.database import Base, get_db
from app.deps import hash_token, require_session
from app.models import AuthSession
from app.routers import auth, lessons
from app.routers.auth import clear_fail_counts
from app.timeutil import now


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    clear_fail_counts()
    yield
    clear_fail_counts()


@pytest.fixture
def session_factory(tmp_path) -> sessionmaker[Session]:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'auth.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, autocommit=False)
    engine.dispose()


@pytest.fixture
def auth_app(session_factory) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    settings = Settings(
        ACCESS_TOKEN="script-key",
        LOGIN_USERNAME="yang",
        LOGIN_PASSWORD="secret123",
        SESSION_TTL_DAYS=365,
    )

    value = FastAPI()
    value.include_router(auth.router, prefix="/api/v1")
    value.include_router(
        lessons.router,
        prefix="/api/v1",
        dependencies=[Depends(require_session)],
    )
    value.dependency_overrides[get_db] = override_get_db
    value.dependency_overrides[get_settings] = lambda: settings
    with TestClient(value) as client:
        yield client


def _login(client: TestClient, username="yang", password="secret123"):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})


def test_login_success_returns_session_token(auth_app):
    response = _login(auth_app)
    assert response.status_code == 200
    token = response.json()["token"]
    assert len(token) >= 32


def test_login_wrong_password_returns_401(auth_app):
    assert _login(auth_app, password="wrong").status_code == 401


def test_login_wrong_username_returns_401(auth_app):
    assert _login(auth_app, username="evil").status_code == 401


def test_login_rate_limit_after_5_failures(auth_app):
    for _ in range(5):
        _login(auth_app, password="wrong")
    assert _login(auth_app, password="wrong").status_code == 429
    assert _login(auth_app).status_code == 429


def test_api_without_session_returns_401(auth_app):
    response = auth_app.get("/api/v1/lessons", params={"from": "2026-08-10", "to": "2026-08-16"})
    assert response.status_code == 401


def test_api_with_session_token_returns_200(auth_app):
    token = _login(auth_app).json()["token"]
    response = auth_app.get(
        "/api/v1/lessons",
        params={"from": "2026-08-10", "to": "2026-08-16"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_me_validates_session(auth_app):
    assert auth_app.get("/api/v1/auth/me").status_code == 401
    token = _login(auth_app).json()["token"]
    assert auth_app.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_logout_invalidates_session(auth_app):
    token = _login(auth_app).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert auth_app.post("/api/v1/auth/logout", headers=headers).status_code == 200
    assert auth_app.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_expired_session_returns_401(auth_app, session_factory):
    token = _login(auth_app).json()["token"]
    db = session_factory()
    try:
        session = db.query(AuthSession).filter(AuthSession.token_hash == hash_token(token)).first()
        session.expires_at = now() - timedelta(days=1)
        db.commit()
    finally:
        db.close()
    response = auth_app.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
