from datetime import date, datetime

from sqlalchemy import func, select

from app.models import Lesson, ScheduleTemplate, Student
from app.services import lesson_service


def test_auto_complete_is_idempotent(db_session, monkeypatch):
    student = Student(name="林晓", color="#8b5cf6", hourly_rate=200)
    db_session.add(student)
    db_session.flush()
    lesson = Lesson(
        student_id=student.id, date=date(2026, 8, 12), start_time="10:00",
        duration_hours=1, status="待上", price=200,
    )
    db_session.add(lesson)
    db_session.commit()
    monkeypatch.setattr(lesson_service, "today", lambda: date(2026, 8, 13))
    monkeypatch.setattr(lesson_service, "now", lambda: datetime(2026, 8, 13, 12, 0))

    assert lesson_service.auto_complete_past_lessons(db_session) == 1
    assert lesson_service.auto_complete_past_lessons(db_session) == 0
    db_session.refresh(lesson)
    assert lesson.status == "已完成"


def test_roll_forward_is_idempotent(db_session, monkeypatch):
    student = Student(name="林晓", color="#8b5cf6", hourly_rate=200)
    db_session.add(student)
    db_session.flush()
    template = ScheduleTemplate(
        student_id=student.id, day_of_week=3, start_time="10:00", duration_hours=1,
        effective_from=date(2026, 8, 13), effective_to=date(2026, 8, 27), repeat_interval=1,
    )
    db_session.add(template)
    db_session.commit()
    monkeypatch.setattr(lesson_service, "today", lambda: date(2026, 8, 13))
    monkeypatch.setattr(lesson_service, "_get_horizon", lambda _db: date(2026, 8, 27))

    assert lesson_service.roll_forward_all_templates(db_session) == 3
    assert lesson_service.roll_forward_all_templates(db_session) == 0
    assert db_session.scalar(select(func.count()).select_from(Lesson)) == 3


def test_scheduler_module_imports_with_dynamic_timezone():
    from app import scheduler
    assert scheduler.scheduler is None
