import logging
import re

from fastapi.testclient import TestClient


def test_echoes_valid_client_request_id(client: TestClient):
    response = client.get("/api/v1/health", headers={"X-Request-ID": "req-client_123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-client_123"


def test_generates_request_id_when_missing(client: TestClient):
    response = client.get("/api/v1/health")

    assert re.fullmatch(r"[0-9a-f-]{36}", response.headers["X-Request-ID"])


def test_replaces_invalid_or_oversized_request_id(client: TestClient):
    invalid = "unsafe value/" + "x" * 200
    response = client.get("/api/v1/health", headers={"X-Request-ID": invalid})

    assert response.headers["X-Request-ID"] != invalid
    assert re.fullmatch(r"[0-9a-f-]{36}", response.headers["X-Request-ID"])


def test_logs_request_context(client: TestClient, caplog):
    caplog.set_level(logging.INFO, logger="app.request")

    response = client.get("/api/v1/health", headers={"X-Request-ID": "req-log"})

    assert response.status_code == 200
    record = next(record for record in caplog.records if record.name == "app.request")
    assert "request_id=req-log" in record.message
    assert "method=GET" in record.message
    assert "path=/api/v1/health" in record.message
    assert "status=200" in record.message
    assert re.search(r"duration_ms=\d+(?:\.\d+)?", record.message)
