from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StudentBase(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    color: str = Field(default="#4C7DFF", pattern=r"^#[0-9A-Fa-f]{6}$")
    hourly_rate: float = Field(gt=0)
    phone: str | None = None
    note: str | None = None


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    hourly_rate: float | None = Field(default=None, gt=0)
    phone: str | None = None
    note: str | None = None


class StudentOut(StudentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    archived: int
    created_at: datetime
    updated_at: datetime


class StudentDetailStats(BaseModel):
    month_income: float
    month_hours: float
    month_lesson_count: int
    month_leave_count: int


class StudentDetail(StudentOut):
    stats: StudentDetailStats
    template_count: int
