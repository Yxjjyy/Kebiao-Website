from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db
from app.schemas.template import TemplateCreate, TemplateOut, TemplateUpdate
from app.services import template_service

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=list[TemplateOut])
def list_templates(student_id: int | None = None, db: Session = Depends(get_db)):
    rows = template_service.list_templates(db, student_id)
    return [TemplateOut.model_validate(r) for r in rows]


@router.post("")
def create_template(payload: TemplateCreate, db: Session = Depends(get_db)):
    t, created = template_service.create_template(db, payload)
    return {"template": TemplateOut.model_validate(t).model_dump(mode="json"), "generated_lessons": created}


@router.patch("/{template_id}")
def update_template(template_id: int, payload: TemplateUpdate, db: Session = Depends(get_db)):
    t, affected = template_service.update_template(db, template_id, payload)
    return {"template": TemplateOut.model_validate(t).model_dump(mode="json"), "regenerated_lessons": affected}


@router.delete("/{template_id}")
def delete_template(
    template_id: int, cancel_future: bool = True, db: Session = Depends(get_db)
):
    cancelled = template_service.delete_template(db, template_id, cancel_future)
    return {"cancelled_lessons": cancelled}
