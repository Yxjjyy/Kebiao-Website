from __future__ import annotations

from datetime import date as _date

from pydantic import BaseModel, ConfigDict, Field


class TemplateBase(BaseModel):
    student_id: int
    day_of_week: int = Field(ge=0, le=6)
    start_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    duration_hours: float = Field(gt=0, le=12)
    effective_from: _date
    effective_to: _date | None = None
    repeat_interval: int = Field(default=1, ge=1, le=4)


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    start_time: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    duration_hours: float | None = Field(default=None, gt=0, le=12)
    effective_from: _date | None = None
    effective_to: _date | None = None
    repeat_interval: int | None = Field(default=None, ge=1, le=4)
    apply_mode: str = Field(default="future_only", pattern=r"^(future_only|from_date|template_only|update_all)$")
    apply_from_date: _date | None = None


class TemplateOut(TemplateBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
