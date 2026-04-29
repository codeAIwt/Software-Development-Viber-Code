"""收藏夹数据模型"""

from datetime import datetime, timezone, timedelta

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from config.db import Base


class Bookmark(Base):
    """收藏夹表"""

    __tablename__ = "bookmark"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column("userid", String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    created_time: Mapped[datetime] = mapped_column(
        "createtime",
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone(timedelta(hours=8)))
    )
