from datetime import date, datetime

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.timeutil import now


class ScheduleTemplate(Base):
    __tablename__ = "schedule_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=周一
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)  # "HH:MM"
    duration_hours: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    repeat_interval: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 1=每周 2=隔周
    created_at: Mapped[datetime] = mapped_column(default=now)
    updated_at: Mapped[datetime] = mapped_column(default=now, onupdate=now)

    student = relationship("Student", back_populates="templates")
    lessons = relationship("Lesson", back_populates="template")
