from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Lesson, ScheduleTemplate, Student
from app.schemas.student import (
    StudentCreate,
    StudentDetail,
    StudentDetailStats,
    StudentOut,
    StudentUpdate,
)
from app.timeutil import month_end, month_start, today


def list_students(db: Session, *, archived: bool | None = False) -> list[StudentOut]:
    stmt = select(Student)
    if archived is False:
        stmt = stmt.where(Student.archived == 0)
    elif archived is True:
        stmt = stmt.where(Student.archived == 1)
    stmt = stmt.order_by(Student.archived, Student.name)
    rows = db.execute(stmt).scalars().all()
    return [StudentOut.model_validate(r) for r in rows]


def get_student(db: Session, student_id: int) -> Student:
    s = db.get(Student, student_id)
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="学生不存在")
    return s


def get_student_detail(db: Session, student_id: int) -> StudentDetail:
    s = get_student(db, student_id)
    today_ = today()
    m_start = month_start(today_)
    m_end = month_end(today_)

    agg = db.execute(
        select(
            func.coalesce(
                func.sum(
                    func.iif(Lesson.status.in_(("待上", "已完成")), Lesson.price, 0.0)
                ),
                0.0,
            ),
            func.coalesce(
                func.sum(
                    func.iif(
                        Lesson.status.in_(("待上", "已完成")), Lesson.duration_hours, 0.0
                    )
                ),
                0.0,
            ),
            func.coalesce(
                func.sum(func.iif(Lesson.status.in_(("待上", "已完成")), 1, 0)), 0
            ),
            func.coalesce(func.sum(func.iif(Lesson.status == "请假", 1, 0)), 0),
        ).where(
            Lesson.student_id == student_id,
            Lesson.date >= m_start,
            Lesson.date <= m_end,
        )
    ).one()

    income, hours, lessons, leaves = agg
    tpl_count = db.execute(
        select(func.count(ScheduleTemplate.id)).where(
            ScheduleTemplate.student_id == student_id
        )
    ).scalar_one()

    base = StudentOut.model_validate(s).model_dump()
    return StudentDetail(
        **base,
        stats=StudentDetailStats(
            month_income=float(income or 0),
            month_hours=float(hours or 0),
            month_lesson_count=int(lessons or 0),
            month_leave_count=int(leaves or 0),
        ),
        template_count=int(tpl_count or 0),
    )


def create_student(db: Session, payload: StudentCreate) -> Student:
    s = Student(**payload.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def update_student(
    db: Session, student_id: int, payload: StudentUpdate, recalc_mode: str = "today"
) -> tuple[Student, int]:
    """返回 (student, affected_future_lessons)。
    recalc_mode: 'today' 从今天起重算 | 'tomorrow' 从明天起重算 | 'none' 不重算"""
    s = get_student(db, student_id)
    data = payload.model_dump(exclude_unset=True)
    rate_changed = "hourly_rate" in data and data["hourly_rate"] != s.hourly_rate
    affected = 0
    for k, v in data.items():
        setattr(s, k, v)
    if rate_changed and recalc_mode != "none":
        from datetime import date as dt_date, timedelta
        start_date = today() if recalc_mode == "today" else today() + timedelta(days=1)
        future = (
            db.execute(
                select(Lesson).where(
                    Lesson.student_id == s.id,
                    Lesson.date >= start_date,
                    Lesson.status == "待上",
                )
            )
            .scalars()
            .all()
        )
        for ls in future:
            ls.price = s.hourly_rate * ls.duration_hours
        affected = len(future)
    db.commit()
    db.refresh(s)
    return s, affected


def archive_student(db: Session, student_id: int, archived: bool) -> Student:
    s = get_student(db, student_id)
    s.archived = 1 if archived else 0
    db.commit()
    db.refresh(s)
    return s


def delete_student(db: Session, student_id: int) -> None:
    s = get_student(db, student_id)
    count = db.execute(
        select(func.count(Lesson.id)).where(Lesson.student_id == student_id)
    ).scalar_one()
    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该学生有课时记录，请改用归档（archive）保留历史",
        )
    db.delete(s)
    db.commit()
