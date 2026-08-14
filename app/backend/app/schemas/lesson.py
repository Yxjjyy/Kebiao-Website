from __future__ import annotations

from datetime import date as _date, datetime as _datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LessonStatus = Literal["待上", "已完成", "请假", "已调课"]


class LessonBase(BaseModel):
    student_id: int
    date: _date
    start_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    duration_hours: float = Field(gt=0, le=12)
    note: str | None = None


class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    date: _date | None = None
    start_time: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    duration_hours: float | None = Field(default=None, gt=0, le=12)
    # 请假/已调课 不通过 PATCH 直接设置（有专属端点与状态机）
    status: Literal["待上", "已完成"] | None = None
    note: str | None = None


class LessonReschedule(BaseModel):
    new_date: _date
    new_start_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    new_duration_hours: float | None = Field(default=None, gt=0, le=12)
    note: str | None = None


class LessonBulkAction(BaseModel):
    ids: list[int] = Field(min_length=1)
    action: Literal["complete", "cancel", "restore", "delete"]
    note: str | None = None


class StudentLite(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    color: str


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    template_id: int | None
    date: _date
    start_time: str
    duration_hours: float
    status: LessonStatus
    price: float
    note: str | None
    rescheduled_from_id: int | None
    rescheduled_to_id: int | None
    created_at: _datetime
    updated_at: _datetime
    student: StudentLite | None = None


class ConflictItem(BaseModel):
    id: int
    student_id: int
    student_name: str
    start_time: str
    duration_hours: float
