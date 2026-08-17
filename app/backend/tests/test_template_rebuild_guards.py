from datetime import date, timedelta

from sqlalchemy import func, select

from app.models import Lesson, ScheduleTemplate, Student, TemplateLessonTombstone
from app.services import lesson_service, template_service


def make_student(db) -> Student:
    student = Student(name="林晓", color="#8b5cf6", hourly_rate=200)
    db.add(student)
    db.flush()
    return student


def make_template(db, student: Student, *, day_of_week: int = 3, start_time: str = "10:00") -> ScheduleTemplate:
    template = ScheduleTemplate(
        student_id=student.id,
        day_of_week=day_of_week,
        start_time=start_time,
        duration_hours=1,
        effective_from=date(2026, 8, 1),
        effective_to=date(2026, 8, 31),
        repeat_interval=1,
    )
    db.add(template)
    db.flush()
    return template


def test_regenerate_keeps_rescheduled_lesson(db_session, monkeypatch):
    """H2: 模板重建不得删除调课生成的新课时。"""
    student = make_student(db_session)
    template = make_template(db_session, student)
    db_session.commit()

    old_lesson = Lesson(
        student_id=student.id, template_id=template.id, date=date(2026, 8, 12),
        start_time="10:00", duration_hours=1, status="已调课", price=200,
    )
    db_session.add(old_lesson)
    db_session.flush()
    new_lesson = Lesson(
        student_id=student.id, template_id=template.id, date=date(2026, 8, 14),
        start_time="15:00", duration_hours=1, status="待上", price=200,
        rescheduled_from_id=old_lesson.id,
    )
    db_session.add(new_lesson)
    db_session.flush()
    old_lesson.rescheduled_to_id = new_lesson.id
    db_session.commit()

    monkeypatch.setattr(lesson_service, "today", lambda: date(2026, 8, 13))
    monkeypatch.setattr(lesson_service, "_get_horizon", lambda _db: date(2026, 8, 20))
    lesson_service.regenerate_template_future(db_session, template, from_date=date(2026, 8, 13))

    assert db_session.get(Lesson, new_lesson.id) is not None
    assert db_session.get(Lesson, old_lesson.id) is not None


def test_deleted_template_lesson_not_recreated_by_materialize(db_session, monkeypatch):
    """H3: 用户删除的未来模板课时，滚动生成不得重建。"""
    student = make_student(db_session)
    template = make_template(db_session, student)
    db_session.commit()

    lesson = Lesson(
        student_id=student.id, template_id=template.id, date=date(2026, 8, 20),
        start_time="10:00", duration_hours=1, status="待上", price=200,
    )
    db_session.add(lesson)
    db_session.commit()

    monkeypatch.setattr(lesson_service, "today", lambda: date(2026, 8, 13))
    monkeypatch.setattr(lesson_service, "_get_horizon", lambda _db: date(2026, 8, 31))
    lesson_service.delete_lesson(db_session, lesson.id)

    assert db_session.scalar(select(func.count()).select_from(TemplateLessonTombstone)) == 1
    created = lesson_service.materialize_template(
        db_session, template, from_date=date(2026, 8, 13), to_date=date(2026, 8, 31)
    )
    # 软删除语义：原课时行保留但标记为已删除，不重建新行
    deleted_row = db_session.get(Lesson, lesson.id)
    assert deleted_row is not None
    assert deleted_row.status == "已删除"
    dates = {
        d for d in (
            db_session.execute(select(Lesson.date).where(Lesson.template_id == template.id)).scalars()
        )
    }
    assert date(2026, 8, 20) in dates
    assert sum(1 for d in dates if d == date(2026, 8, 20)) == 1
    assert created == 2  # 8/13 与 8/27 中 8/20 由墓碑/占位行跳过


def test_restore_rescheduled_cancels_replacement(db_session, monkeypatch):
    """M7: 恢复已调课旧课时后，替换新课时不再处于待上。"""
    student = make_student(db_session)
    template = make_template(db_session, student)
    db_session.commit()

    old_lesson = Lesson(
        student_id=student.id, template_id=template.id, date=date(2026, 8, 12),
        start_time="10:00", duration_hours=1, status="已调课", price=200,
    )
    db_session.add(old_lesson)
    db_session.flush()
    new_lesson = Lesson(
        student_id=student.id, template_id=template.id, date=date(2026, 8, 14),
        start_time="15:00", duration_hours=1, status="待上", price=200,
        rescheduled_from_id=old_lesson.id,
    )
    db_session.add(new_lesson)
    db_session.flush()
    old_lesson.rescheduled_to_id = new_lesson.id
    db_session.commit()

    monkeypatch.setattr(lesson_service, "today", lambda: date(2026, 8, 13))
    restored = lesson_service.restore_lesson(db_session, old_lesson.id)
    assert restored.status == "待上"
    db_session.refresh(new_lesson)
    assert new_lesson.status == "请假"
    assert new_lesson.rescheduled_from_id is None
    db_session.refresh(old_lesson)
    assert old_lesson.rescheduled_to_id is None


def test_delete_template_keeps_rescheduled_and_clears_tombstones(db_session, monkeypatch):
    """H2/H3: 删除模板保留调课新课时，并清理其墓碑。"""
    student = make_student(db_session)
    template = make_template(db_session, student)
    db_session.commit()

    lesson = Lesson(
        student_id=student.id, template_id=template.id, date=date(2026, 8, 20),
        start_time="10:00", duration_hours=1, status="待上", price=200,
    )
    db_session.add(lesson)
    db_session.commit()
    lesson_service.delete_lesson(db_session, lesson.id)

    new_lesson = Lesson(
        student_id=student.id, template_id=template.id, date=date(2026, 8, 14),
        start_time="15:00", duration_hours=1, status="待上", price=200,
        rescheduled_from_id=lesson.id,
    )
    db_session.add(new_lesson)
    db_session.commit()

    monkeypatch.setattr(lesson_service, "today", lambda: date(2026, 8, 13))
    template_service.delete_template(db_session, template.id)

    assert db_session.get(Lesson, new_lesson.id) is not None
    assert db_session.scalar(select(func.count()).select_from(TemplateLessonTombstone)) == 0
