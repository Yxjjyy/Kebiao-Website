"""写操作审计中间件测试。"""

from collections.abc import Iterator

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings, get_settings
from app.database import Base, get_db
from app.deps import require_session
from app.middleware.audit import AuditMiddleware
from app.models import AuditLog
from app.routers import auth, students


@pytest.fixture
def session_factory(tmp_path) -> sessionmaker[Session]:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'audit.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, autocommit=False)
    engine.dispose()


@pytest.fixture
def audit_app(session_factory) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    factory = session_factory

    settings = Settings(
        ACCESS_TOKEN="script-key",
        LOGIN_USERNAME="yang",
        LOGIN_PASSWORD="secret123",
        SESSION_TTL_DAYS=365,
    )

    value = FastAPI()
    value.add_middleware(AuditMiddleware, session_factory=factory)
    value.include_router(auth.router, prefix="/api/v1")
    value.include_router(
        students.router,
        prefix="/api/v1",
        dependencies=[Depends(require_session)],
    )
    value.dependency_overrides[get_db] = override_get_db
    value.dependency_overrides[get_settings] = lambda: settings
    with TestClient(value) as client:
        yield client


def _login(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "yang", "password": "secret123"},
    )
    assert response.status_code == 200
    return response.json()["token"]


def test_write_requests_are_audited(audit_app, session_factory):
    token = _login(audit_app)
    headers = {"Authorization": f"Bearer {token}"}
    response = audit_app.post(
        "/api/v1/students",
        json={"name": "审计", "color": "#123456", "hourly_rate": 100},
        headers=headers,
    )
    assert response.status_code == 200

    db = session_factory()
    try:
        row = db.query(AuditLog).filter(AuditLog.uri == "/api/v1/students").first()
        assert row is not None
        assert row.method == "POST"
        assert row.status == 200
        assert row.session_id is not None
        assert row.ip is not None
    finally:
        db.close()


def test_login_is_not_audited(audit_app, session_factory):
    _login(audit_app)
    db = session_factory()
    try:
        assert db.query(AuditLog).filter(AuditLog.uri == "/api/v1/auth/login").count() == 0
    finally:
        db.close()
