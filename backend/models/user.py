from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from config.db import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    phone: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(64), nullable=False)
    nickname: Mapped[str] = mapped_column(String(20), nullable=False)
    avatar: Mapped[str] = mapped_column(String(255), nullable=False)
    registertime: Mapped[datetime] = mapped_column("registertime", DateTime, nullable=False)
    lastlogintime: Mapped[datetime | None] = mapped_column("lastlogintime", DateTime, nullable=True)
    tags: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    is_first_login: Mapped[bool] = mapped_column(nullable=False, default=True)