from datetime import date

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models import Lesson, ScheduleTemplate, Student, TemplateLessonTombstone
from app.schemas.template import TemplateCreate, TemplateUpdate
from app.services import lesson_service
from app.timeutil import today


def list_templates(db: Session, student_id: int | None = None) -> list[ScheduleTemplate]:
    stmt = select(ScheduleTemplate)
    if student_id is not None:
        stmt = stmt.where(ScheduleTemplate.student_id == student_id)
    stmt = stmt.order_by(ScheduleTemplate.day_of_week, ScheduleTemplate.start_time)
    return list(db.execute(stmt).scalars().all())


def get_template(db: Session, template_id: int) -> ScheduleTemplate:
    t = db.get(ScheduleTemplate, template_id)
    if not t:
        raise HTTPException(status_code=404, detail="模板不存在")
    return t


def create_template(db: Session, payload: TemplateCreate) -> tuple[ScheduleTemplate, int]:
    student = db.get(Student, payload.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    try:
        t = ScheduleTemplate(**payload.model_dump())
        db.add(t)
        db.flush()
        created = lesson_service.materialize_template(db, t, commit=False)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(t)
    return t, created


def update_template(
    db: Session, template_id: int, payload: TemplateUpdate
) -> tuple[ScheduleTemplate, int]:
    t = get_template(db, template_id)
    data = payload.model_dump(exclude_unset=True)
    apply_mode = data.pop("apply_mode", "future_only")
    apply_from = data.pop("apply_from_date", None)

    if apply_mode not in {"template_only", "update_all", "future_only", "from_date"}:
        raise HTTPException(status_code=422, detail="不支持的 apply_mode")
    if apply_mode == "from_date" and not apply_from:
        raise HTTPException(status_code=422, detail="apply_mode=from_date 时必须提供 apply_from_date")

    for k, v in data.items():
        setattr(t, k, v)

    try:
        if apply_mode == "template_only":
            db.commit()
            db.refresh(t)
            return t, 0

        if apply_mode == "update_all":
            from_date = today()
        else:
            from_date = apply_from or today()

        affected = lesson_service.regenerate_template_future(
            db, t, from_date=from_date, commit=False
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(t)
    return t, affected


def delete_template(
    db: Session, template_id: int, cancel_future: bool = True
) -> int:
    t = get_template(db, template_id)
    cancelled = 0
    if cancel_future:
        rows = db.execute(
            select(Lesson).where(
                and_(
                    Lesson.template_id == t.id,
                    Lesson.date >= today(),
                    Lesson.status == "待上",
                    Lesson.rescheduled_from_id.is_(None),
                )
            )
        ).scalars().all()
        for ls in rows:
            db.delete(ls)
        cancelled = len(rows)
    db.execute(
        TemplateLessonTombstone.__table__.delete().where(
            TemplateLessonTombstone.template_id == t.id
        )
    )
    db.delete(t)
    db.commit()
    return cancelled
