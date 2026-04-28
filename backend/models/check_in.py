"""打卡记录模型"""

from datetime import datetime, date, timezone

from sqlalchemy import Date, DateTime, String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from config.db import Base


class CheckIn(Base):
    """打卡记录表"""

    __tablename__ = "check_in"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column("userid", String(32), nullable=False)
    check_in_date: Mapped[date] = mapped_column("checkindate", Date, nullable=False)
    create_time: Mapped[datetime] = mapped_column("createtime", DateTime, nullable=False, default=datetime.now(timezone.utc))
