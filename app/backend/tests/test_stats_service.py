from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.deps import get_db
from app.models import Lesson, Student
from app.routers import stats as stats_router
from app.services import stats_service


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


def add_student(db: Session, name: str) -> Student:
    student = Student(name=name, color="#7c3aed", hourly_rate=200)
    db.add(student)
    db.flush()
    return student


def add_lesson(
    db: Session,
    student_id: int,
    status: str,
    price: float,
    start_time: str,
) -> None:
    db.add(
        Lesson(
            student_id=student_id,
            date=date(2026, 7, 15),
            start_time=start_time,
            duration_hours=1,
            status=status,
            price=price,
        )
    )


def test_range_stats_exposes_decision_metrics(db: Session):
    active = add_student(db, "林晓")
    leave_only = add_student(db, "周然")
    moved_only = add_student(db, "顾宁")
    add_lesson(db, active.id, "已完成", 200, "09:00")
    add_lesson(db, active.id, "待上", 200, "10:00")
    add_lesson(db, leave_only.id, "请假", 300, "11:00")
    add_lesson(db, moved_only.id, "已调课", 400, "12:00")
    db.commit()

    result = stats_service.range_stats(
        db,
        from_date=date(2026, 7, 1),
        to_date=date(2026, 7, 31),
        granularity="day",
    )

    assert result.total_income == 200
    assert result.total_hours == 2
    assert result.total_lessons == 2
    assert result.completed_lessons == 1
    assert result.pending_lessons == 1
    assert result.leave_count == 1
    assert result.reschedule_count == 1
    assert result.active_students == 2


@pytest.mark.parametrize(
    ("from_date", "to_date", "period", "expected"),
    [
        (
            date(2026, 7, 29),
            date(2026, 7, 29),
            "day",
            (date(2026, 7, 28), date(2026, 7, 28)),
        ),
        (
            date(2026, 7, 27),
            date(2026, 7, 29),
            "week",
            (date(2026, 7, 20), date(2026, 7, 22)),
        ),
        (
            date(2026, 7, 1),
            date(2026, 7, 29),
            "month",
            (date(2026, 6, 1), date(2026, 6, 29)),
        ),
        (
            date(2026, 7, 1),
            date(2026, 7, 31),
            "month",
            (date(2026, 6, 1), date(2026, 6, 30)),
        ),
    ],
)
def test_previous_period_uses_matching_natural_range(
    from_date: date,
    to_date: date,
    period: str,
    expected: tuple[date, date],
):
    assert stats_service.previous_period(from_date, to_date, period) == expected


def test_comparison_uses_requested_historical_range(db: Session):
    student = add_student(db, "林晓")
    db.add_all(
        [
            Lesson(
                student_id=student.id,
                date=date(2026, 6, 10),
                start_time="09:00",
                duration_hours=1,
                status="已完成",
                price=100,
            ),
            Lesson(
                student_id=student.id,
                date=date(2026, 7, 10),
                start_time="09:00",
                duration_hours=2,
                status="已完成",
                price=200,
            ),
        ]
    )
    db.commit()

    result = stats_service.comparison(
        db,
        period="month",
        from_date=date(2026, 7, 1),
        to_date=date(2026, 7, 31),
    )

    assert result.current_income == 200
    assert result.previous_income == 100
    assert result.income_growth_pct == 100


def test_comparison_route_accepts_explicit_range(db: Session):
    student = add_student(db, "林晓")
    db.add(
        Lesson(
            student_id=student.id,
            date=date(2026, 7, 10),
            start_time="09:00",
            duration_hours=1,
            status="已完成",
            price=200,
        )
    )
    db.commit()
    app = FastAPI()
    app.include_router(stats_router.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: db

    response = TestClient(app).get(
        "/api/v1/stats/comparison",
        params={
            "period": "month",
            "from": "2026-07-01",
            "to": "2026-07-31",
        },
    )

    assert response.status_code == 200
    assert response.json()["current_income"] == 200


def test_comparison_route_rejects_partial_range(db: Session):
    app = FastAPI()
    app.include_router(stats_router.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: db

    response = TestClient(app).get(
        "/api/v1/stats/comparison",
        params={"period": "month", "from": "2026-07-01"},
    )

    assert response.status_code == 422
