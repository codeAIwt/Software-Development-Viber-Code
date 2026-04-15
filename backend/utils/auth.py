from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import Depends, Header, HTTPException
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from config.db import get_db
from config.settings import settings
from models.user import User
from utils import cache


def create_access_token(user_id: str) -> tuple[str, str, int]:
    jti = str(uuid4())
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": user_id, "jti": jti, "exp": expire}
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    ttl = int((expire - datetime.now(timezone.utc)).total_seconds())
    cache.session_set(jti, user_id, max(ttl, 60))
    return token, jti, ttl


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def get_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    token = get_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail={"code": 401, "msg": "缺少 Token", "data": {}})
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail={"code": 401, "msg": "Token 无效或已过期", "data": {}})
    jti = payload.get("jti")
    sub = payload.get("sub")
    if not jti or not sub:
        raise HTTPException(status_code=401, detail={"code": 401, "msg": "Token 无效", "data": {}})
    sess = cache.session_get(jti)
    if not sess or str(sess.get("user_id")) != str(sub):
        raise HTTPException(status_code=401, detail={"code": 401, "msg": "Token 已失效", "data": {}})
    user = db.get(User, sub)
    if not user:
        raise HTTPException(status_code=401, detail={"code": 401, "msg": "用户不存在", "data": {}})
    return user
