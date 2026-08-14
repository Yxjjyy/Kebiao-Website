from collections.abc import Iterator

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.deps import require_token
from app.routers import auth, lessons


@pytest.fixture
def auth_app() -> Iterator[TestClient]:
    value = FastAPI()
    value.include_router(
        auth.router,
        prefix="/api/v1",
        dependencies=[Depends(require_token)],
    )
    value.include_router(
        lessons.router,
        prefix="/api/v1",
        dependencies=[Depends(require_token)],
    )
    with TestClient(value) as client:
        yield client


def test_health_without_token_allowed():
    from app.main import app

    with TestClient(app) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_api_without_token_returns_401(auth_app):
    response = auth_app.get("/api/v1/lessons", params={"from": "2026-08-10", "to": "2026-08-16"})
    assert response.status_code == 401


def test_api_with_wrong_token_returns_401(auth_app):
    response = auth_app.get(
        "/api/v1/lessons",
        params={"from": "2026-08-10", "to": "2026-08-16"},
        headers={"Authorization": "Bearer wrong"},
    )
    assert response.status_code == 401


def test_api_with_bearer_token_returns_200(auth_app):
    response = auth_app.get(
        "/api/v1/lessons",
        params={"from": "2026-08-10", "to": "2026-08-16"},
        headers={"Authorization": "Bearer yang"},
    )
    assert response.status_code == 200


def test_verify_validates_token(auth_app):
    assert auth_app.post("/api/v1/auth/verify").status_code == 401
    assert (
        auth_app.post(
            "/api/v1/auth/verify",
            headers={"Authorization": "Bearer yang"},
        ).status_code
        == 200
    )
