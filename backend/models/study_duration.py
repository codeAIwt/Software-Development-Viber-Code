"""学习时长模型；物理字段见 database-design.md §5.4。"""

from datetime import datetime, date, timezone

from sqlalchemy import Date, DateTime, String, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from config.db import Base


class StudyDuration(Base):
    """学习时长表模型"""

    __tablename__ = "study_duration"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column("userid", String(32), nullable=False)
    study_date: Mapped[date] = mapped_column("studydate", Date, nullable=False)
    total_minutes: Mapped[int] = mapped_column("totalminutes", Integer, nullable=False, default=0)
    beat_percent: Mapped[float | None] = mapped_column("beatpercent", Numeric(5, 2), nullable=True)
    create_time: Mapped[datetime] = mapped_column("createtime", DateTime, nullable=False, default=datetime.now(timezone.utc))