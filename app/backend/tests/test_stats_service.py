from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Lesson, Student
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
