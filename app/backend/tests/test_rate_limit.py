"""API 通用限流中间件测试。"""

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.rate_limit import RateLimitMiddleware, RATE_LIMIT_PER_MINUTE, clear_rate_limits


@pytest.fixture(autouse=True)
def _reset_limits():
    clear_rate_limits()
    yield
    clear_rate_limits()


@pytest.fixture
def rate_app() -> Iterator[TestClient]:
    value = FastAPI()
    value.add_middleware(RateLimitMiddleware)
    value.get("/api/v1/ping")(lambda: {"ok": True})
    value.get("/api/v1/health")(lambda: {"ok": True})
    with TestClient(value) as client:
        yield client


def test_health_and_normal_requests_pass(rate_app):
    assert rate_app.get("/api/v1/health").status_code == 200
    for _ in range(5):
        assert rate_app.get("/api/v1/ping").status_code == 200


def test_exceeding_limit_returns_429(rate_app):
    for _ in range(RATE_LIMIT_PER_MINUTE):
        rate_app.get("/api/v1/ping")
    response = rate_app.get("/api/v1/ping")
    assert response.status_code == 429
