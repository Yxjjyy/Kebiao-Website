from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    timezone: Mapped[str] = mapped_column(String(32), default="Asia/Shanghai")
    week_start: Mapped[int] = mapped_column(Integer, default=1)  # 1=周一
    currency_symbol: Mapped[str] = mapped_column(String(4), default="¥")
    generate_weeks_ahead: Mapped[int] = mapped_column(Integer, default=12)
    default_duration_hours: Mapped[float] = mapped_column(Float, default=1.0)
    visible_time_start: Mapped[str] = mapped_column(String(5), default="07:00")
    visible_time_end: Mapped[str] = mapped_column(String(5), default="22:00")
    theme: Mapped[str] = mapped_column(String(8), default="auto")
