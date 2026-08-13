from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Lesson, ScheduleTemplate, Student
from app.schemas.lesson import LessonReschedule, LessonUpdate
from app.services import lesson_service


@pytest.fixture
def student(db_session: Session) -> Student:
    value = Student(name="林晓", color="#8b5cf6", hourly_rate=200)
    db_session.add(value)
    db_session.commit()
    db_session.refresh(value)
    return value


def add_lesson(db: Session, student: Student, **overrides) -> Lesson:
    values = {
        "student_id": student.id,
        "date": date(2026, 8, 13),
        "start_time": "10:00",
        "duration_hours": 1,
        "status": "待上",
        "price": 200,
    }
    values.update(overrides)
    lesson = Lesson(**values)
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


@pytest.mark.parametrize(
    ("current", "target", "allowed"),
    [
        ("待上", "已完成", True),
        ("已完成", "待上", True),
        ("请假", "待上", True),
        ("已调课", "待上", True),
        ("待上", "待上", True),
        ("已完成", "请假", False),
        ("请假", "已完成", False),
        ("已调课", "已完成", False),
    ],
)
def test_status_transition_matrix(db_session, student, current, target, allowed):
    lesson = add_lesson(db_session, student, status=current)

    if allowed:
        result = lesson_service.update_lesson(db_session, lesson.id, LessonUpdate(status=target))
        assert result.status == target
    else:
        with pytest.raises(HTTPException) as raised:
            lesson_service.update_lesson(db_session, lesson.id, LessonUpdate(status=target))
        assert raised.value.status_code == 409
        assert raised.value.detail["error"] == "invalid_status_transition"
        db_session.expire_all()
        assert db_session.get(Lesson, lesson.id).status == current


def test_cross_midnight_conflict_checks_adjacent_date(db_session, student):
    existing = add_lesson(
        db_session, student, date=date(2026, 8, 13), start_time="23:30", duration_hours=2,
    )

    conflicts = lesson_service.find_conflicts(
        db_session, on_date=date(2026, 8, 14), start_time="01:00", duration_hours=1,
    )
    touching = lesson_service.find_conflicts(
        db_session, on_date=date(2026, 8, 14), start_time="01:30", duration_hours=1,
    )

    assert [lesson.id for lesson in conflicts] == [existing.id]
    assert touching == []


def test_same_day_overlap_but_not_touching_boundary(db_session, student):
    existing = add_lesson(db_session, student, start_time="10:00", duration_hours=1)

    overlap = lesson_service.find_conflicts(
        db_session, on_date=existing.date, start_time="10:30", duration_hours=1,
    )
    touching = lesson_service.find_conflicts(
        db_session, on_date=existing.date, start_time="11:00", duration_hours=1,
    )

    assert [lesson.id for lesson in overlap] == [existing.id]
    assert touching == []


def test_restore_rejects_a_conflicting_time(db_session, student):
    leave = add_lesson(db_session, student, status="请假")
    add_lesson(db_session, student, start_time="10:30", duration_hours=1)

    with pytest.raises(HTTPException) as raised:
        lesson_service.restore_lesson(db_session, leave.id)

    assert raised.value.status_code == 409
    assert raised.value.detail["error"] == "time_conflict"
    db_session.expire_all()
    assert db_session.get(Lesson, leave.id).status == "请假"


def test_reschedule_excludes_original_but_rejects_non_pending(db_session, student):
    pending = add_lesson(db_session, student)
    old, new = lesson_service.reschedule_lesson(
        db_session,
        pending.id,
        LessonReschedule(new_date=pending.date, new_start_time=pending.start_time),
    )
    assert old.status == "已调课"
    assert new.status == "待上"

    completed = add_lesson(
        db_session, student, date=date(2026, 8, 15), status="已完成",
    )
    with pytest.raises(HTTPException) as raised:
        lesson_service.reschedule_lesson(
            db_session,
            completed.id,
            LessonReschedule(new_date=date(2026, 8, 16), new_start_time="10:00"),
        )
    assert raised.value.status_code == 409
    assert raised.value.detail["error"] == "invalid_status_transition"


def test_template_materialization_is_idempotent(db_session, student):
    template = ScheduleTemplate(
        student_id=student.id,
        day_of_week=3,
        start_time="16:00",
        duration_hours=1,
        effective_from=date(2026, 8, 13),
        effective_to=date(2026, 8, 20),
        repeat_interval=1,
    )
    db_session.add(template)
    db_session.commit()

    first = lesson_service.materialize_template(
        db_session, template, from_date=date(2026, 8, 13), to_date=date(2026, 8, 20),
    )
    second = lesson_service.materialize_template(
        db_session, template, from_date=date(2026, 8, 13), to_date=date(2026, 8, 20),
    )

    assert first == 2
    assert second == 0


def test_bulk_failure_rolls_back_prior_changes(db_session, student):
    valid = add_lesson(db_session, student, status="待上")
    invalid = add_lesson(
        db_session, student, date=date(2026, 8, 14), status="请假",
    )

    with pytest.raises(HTTPException):
        lesson_service.bulk_action(
            db_session, lesson_ids=[valid.id, invalid.id], action="complete",
        )

    db_session.expire_all()
    assert db_session.get(Lesson, valid.id).status == "待上"
    assert db_session.get(Lesson, invalid.id).status == "请假"


def test_bulk_error_identifies_the_failed_lesson(db_session, student):
    valid = add_lesson(db_session, student, status="待上")
    invalid = add_lesson(db_session, student, date=date(2026, 8, 14), status="请假")

    with pytest.raises(HTTPException) as raised:
        lesson_service.bulk_action(
            db_session, lesson_ids=[valid.id, invalid.id], action="complete",
        )

    assert raised.value.detail["lesson_id"] == invalid.id
