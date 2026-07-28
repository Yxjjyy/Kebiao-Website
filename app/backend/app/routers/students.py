from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db
from app.schemas.student import (
    StudentCreate,
    StudentDetail,
    StudentOut,
    StudentUpdate,
)
from app.services import student_service

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=list[StudentOut])
def list_students(archived: bool | None = False, db: Session = Depends(get_db)):
    return student_service.list_students(db, archived=archived)


@router.post("", response_model=StudentOut)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    s = student_service.create_student(db, payload)
    return StudentOut.model_validate(s)


@router.get("/{student_id}", response_model=StudentDetail)
def get_student(student_id: int, db: Session = Depends(get_db)):
    return student_service.get_student_detail(db, student_id)


@router.patch("/{student_id}")
def update_student(student_id: int, payload: StudentUpdate, recalc_mode: str = "today", db: Session = Depends(get_db)):
    s, affected = student_service.update_student(db, student_id, payload, recalc_mode)
    return {
        "student": StudentOut.model_validate(s).model_dump(),
        "affected_future_lessons": affected,
    }


@router.post("/{student_id}/archive", response_model=StudentOut)
def archive_student(student_id: int, db: Session = Depends(get_db)):
    s = student_service.archive_student(db, student_id, True)
    return StudentOut.model_validate(s)


@router.post("/{student_id}/unarchive", response_model=StudentOut)
def unarchive_student(student_id: int, db: Session = Depends(get_db)):
    s = student_service.archive_student(db, student_id, False)
    return StudentOut.model_validate(s)


@router.delete("/{student_id}", status_code=204)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student_service.delete_student(db, student_id)
    return None
