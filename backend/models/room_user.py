"""自习室成员表逻辑模型骨架；物理字段见 database-design.md §5.3、RoomCreateAttend.md §8。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from config.db import Base


@dataclass
class RoomUserRecord:
    """与 `room_user` 表对应的领域记录（非 ORM）。"""

    id: int | None
    roomid: str
    userid: str
    jointime: datetime
    leavetime: datetime | None
    privacymode: str
    camera: int


class RoomUser(Base):
    """
    数据访问层占位类型；活跃成员判定以 ``leavetime is None`` 为准。
    MVP 业务默认写入 ``privacymode=blur``、``camera=1``（database-design.md §15）。
    """

    __tablename__ = "room_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[str] = mapped_column("roomid", String(32), nullable=False)
    user_id: Mapped[str] = mapped_column("userid", String(32), nullable=False)
    join_time: Mapped[datetime] = mapped_column("jointime", DateTime, nullable=False, default=datetime.now(timezone.utc))
    leave_time: Mapped[datetime | None] = mapped_column("leavetime", DateTime, nullable=True)
    privacy_mode: Mapped[str] = mapped_column("privacymode", String(10), nullable=False, default="blur")
    camera: Mapped[int] = mapped_column(nullable=False, default=1)