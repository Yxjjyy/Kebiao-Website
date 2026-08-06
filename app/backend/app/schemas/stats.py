from datetime import date

from pydantic import BaseModel

from app.schemas.lesson import LessonOut


class TodayStats(BaseModel):
    date: date
    total_lessons: int
    expected_income: float
    earned_income: float
    total_hours: float
    lessons: list[LessonOut]


class RangeBucket(BaseModel):
    bucket: str
    income: float
    hours: float
    lesson_count: int


class RangeStats(BaseModel):
    from_date: date
    to_date: date
    granularity: str
    total_income: float
    total_hours: float
    total_lessons: int
    completed_lessons: int
    pending_lessons: int
    leave_count: int
    reschedule_count: int
    active_students: int
    buckets: list[RangeBucket]


class StudentStatsRow(BaseModel):
    student_id: int
    name: str
    color: str
    lesson_count: int
    total_hours: float
    total_income: float
    leave_count: int
    reschedule_count: int


class LeaveItem(BaseModel):
    id: int
    student_id: int
    student_name: str
    date: date
    start_time: str
    duration_hours: float
    status: str
    note: str | None


class ComparisonStats(BaseModel):
    period: str
    current_income: float
    previous_income: float
    income_growth_pct: float | None
    current_hours: float
    previous_hours: float
    hours_growth_pct: float | None
    current_lessons: int
    previous_lessons: int
