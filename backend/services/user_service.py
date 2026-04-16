from datetime import datetime, timezone
from uuid import uuid4
import re

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config.settings import settings
from models.user import User


class UserServiceError(Exception):
    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg


def _validate_phone(phone: str) -> bool:
    if not phone:
        return False
    return bool(re.match(r'^[0-9]{11}$', phone))


def _default_nickname(phone: str) -> str:
    tail = phone[-4:] if len(phone) >= 4 else phone
    return f"用户{tail}"


def register_user(db: Session, phone: str, password: str) -> User:
    if not phone or not password:
        raise UserServiceError(400, "phone 与 password 不能为空")
    if not _validate_phone(phone):
        raise UserServiceError(400, "手机号格式不正确，必须为11位纯数字")
    uid = uuid4().hex
    now = datetime.now(timezone.utc)
    user = User(
        id=uid,
        phone=phone,
        password=password,
        nickname=_default_nickname(phone),
        avatar=settings.default_avatar_url,
        registertime=now,
        lastlogintime=None,
        tags="",
        is_first_login=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise UserServiceError(409, "手机号已注册") from None
    db.refresh(user)
    return user


def login_user(db: Session, phone: str, password: str) -> User:
    if not phone or not password:
        raise UserServiceError(400, "phone 与 password 不能为空")
    if not _validate_phone(phone):
        raise UserServiceError(400, "手机号格式不正确，必须为11位纯数字")
    user = db.scalar(select(User).where(User.phone == phone))
    if not user or user.password != password:
        raise UserServiceError(400, "手机号或密码错误")
    user.lastlogintime = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_nickname(db: Session, user: User, nickname: str) -> User:
    name = nickname.strip()
    if not name or len(name) > 20:
        raise UserServiceError(400, "nickname 格式不合法")
    user.nickname = name
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_tags(db: Session, user: User, tags: list) -> User:
    # 将标签列表转换为逗号分隔的字符串
    tags_str = ",".join(tags)
    if len(tags_str) > 255:
        raise UserServiceError(400, "标签长度超出限制")
    user.tags = tags_str
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def set_first_login(db: Session, user: User, is_first_login: bool) -> User:
    user.is_first_login = is_first_login
    db.add(user)
    db.commit()
    return user

def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.id == user_id).first()