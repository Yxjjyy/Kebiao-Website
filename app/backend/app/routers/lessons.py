from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.deps import get_db
from app.schemas.lesson import (
    LessonBulkAction,
    LessonCreate,
    LessonOut,
    LessonReschedule,
    LessonUpdate,
)
from app.services import lesson_service

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("", response_model=list[LessonOut])
def list_lessons(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    student_id: int | None = None,
    db: Session = Depends(get_db),
):
    rows = lesson_service.list_lessons(
        db, from_date=from_date, to_date=to_date, student_id=student_id
    )
    return [LessonOut.model_validate(r) for r in rows]


@router.post("", response_model=LessonOut)
def create_lesson(payload: LessonCreate, db: Session = Depends(get_db)):
    ls = lesson_service.create_lesson(db, payload)
    return LessonOut.model_validate(ls)


@router.post("/bulk")
def bulk_lessons(payload: LessonBulkAction, db: Session = Depends(get_db)):
    return lesson_service.bulk_action(
        db,
        lesson_ids=payload.ids,
        action=payload.action,
        note=payload.note,
    )


@router.patch("/{lesson_id}", response_model=LessonOut)
def update_lesson(lesson_id: int, payload: LessonUpdate, db: Session = Depends(get_db)):
    ls = lesson_service.update_lesson(db, lesson_id, payload)
    return LessonOut.model_validate(ls)


@router.post("/{lesson_id}/reschedule")
def reschedule_lesson(
    lesson_id: int, payload: LessonReschedule, db: Session = Depends(get_db)
):
    old, new = lesson_service.reschedule_lesson(db, lesson_id, payload)
    return {
        "old": LessonOut.model_validate(old).model_dump(mode="json"),
        "new": LessonOut.model_validate(new).model_dump(mode="json"),
    }


class CancelPayload(BaseModel):
    note: str | None = None


@router.post("/{lesson_id}/cancel", response_model=LessonOut)
def cancel_lesson(
    lesson_id: int, payload: CancelPayload | None = None, db: Session = Depends(get_db)
):
    ls = lesson_service.cancel_lesson(db, lesson_id, payload.note if payload else None)
    return LessonOut.model_validate(ls)


@router.post("/{lesson_id}/restore", response_model=LessonOut)
def restore_lesson(lesson_id: int, db: Session = Depends(get_db)):
    ls = lesson_service.restore_lesson(db, lesson_id)
    return LessonOut.model_validate(ls)


@router.delete("/{lesson_id}", status_code=204)
def delete_lesson(lesson_id: int, db: Session = Depends(get_db)):
    lesson_service.delete_lesson(db, lesson_id)
    return None
