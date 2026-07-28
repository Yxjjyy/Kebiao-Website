from datetime import datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.timeutil import now


class UserProfile(Base):
    __tablename__ = "user_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    display_name: Mapped[str] = mapped_column(String(64), default="")
    avatar_color: Mapped[str] = mapped_column(String(16), default="#4C7DFF")
    created_at: Mapped[datetime] = mapped_column(default=now)
