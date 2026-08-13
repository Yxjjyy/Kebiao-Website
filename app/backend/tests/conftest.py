from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.middleware.request_context import RequestContextMiddleware
from app.models import Lesson, ScheduleTemplate, Settings, Student, UserProfile  # noqa: F401
from app.routers import auth, backup, export, lessons, settings, stats, students, templates


@pytest.fixture
def test_app(tmp_path) -> Iterator[FastAPI]:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    def override_get_db() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    value = FastAPI()
    value.add_middleware(RequestContextMiddleware)
    value.get("/api/v1/health")(lambda: {"status": "ok"})
    for router in (auth, settings, students, templates, lessons, stats, export, backup):
        value.include_router(router.router, prefix="/api/v1")
    value.dependency_overrides[get_db] = override_get_db
    yield value
    engine.dispose()


@pytest.fixture
def client(test_app: FastAPI) -> Iterator[TestClient]:
    with TestClient(test_app) as value:
        yield value
