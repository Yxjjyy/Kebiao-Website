from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.timeutil import now


class TemplateLessonTombstone(Base):
    """模板生成课时的删除墓碑：防止夜间滚动任务重建用户已删除的未来课时。"""

    __tablename__ = "template_lesson_tombstones"
    __table_args__ = (Index("ix_tombstones_template_date", "template_id", "date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("schedule_templates.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=now)
