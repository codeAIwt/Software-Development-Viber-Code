"""自习室表逻辑模型骨架；物理字段见 database-design.md §5.2、RoomCreateAttend.md §7。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from config.db import Base


@dataclass
class StudyRoomRecord:
    """
    与 `study_room` 表一一对应的领域记录（非 SQLAlchemy 映射）。
    字段命名与库表一致，便于后续 ORM 落地。
    """

    id: str
    theme: str
    maxpeople: int
    currentpeople: int
    status: str
    creatorid: str
    createtime: datetime


class StudyRoom(Base):
    __tablename__ = "study_room"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    theme: Mapped[str] = mapped_column(String(20), nullable=False)
    max_people: Mapped[int] = mapped_column("maxpeople", nullable=False)
    current_people: Mapped[int] = mapped_column("currentpeople", nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="idle")
    creator_id: Mapped[str] = mapped_column("creatorid", String(32), nullable=False)
    create_time: Mapped[datetime] = mapped_column("createtime", DateTime, nullable=False, default=datetime.now(timezone.utc))
    tags: Mapped[str] = mapped_column(String(255), nullable=True, default="")