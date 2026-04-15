from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config.db import get_db
from config.settings import settings
from models.user import User
from services import user_service
from services.user_service import UserServiceError
from utils import auth as auth_utils
from utils import cache

router = APIRouter()


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _json_ok(data=None, msg: str = "OK"):
    return {"code": 200, "msg": msg, "data": data if data is not None else {}}


def _json_err(status: int, code: int, msg: str):
    return JSONResponse(status_code=status, content={"code": code, "msg": msg, "data": {}})


class RegisterBody(BaseModel):
    phone: str = Field(default="")
    password: str = Field(default="")


class LoginBody(BaseModel):
    phone: str = Field(default="")
    password: str = Field(default="")


class NicknameBody(BaseModel):
    nickname: str = Field(default="用户{phone 最后4位}")


class TagsBody(BaseModel):
    tags: list = Field(default=[])


@router.post("/register")
def register(request: Request, body: RegisterBody, db: Session = Depends(get_db)):
    allowed, _ = cache.rate_limit_increment(
        "rl:ip:register",
        _client_ip(request),
        settings.rate_limit_register_ip_max,
    )
    if not allowed:
        return _json_err(429, 429, "too many requests")
    try:
        user = user_service.register_user(db, body.phone.strip(), body.password)
    except UserServiceError as e:
        return _json_err(400 if e.code != 409 else 409, e.code, e.msg)
    token, _, _ = auth_utils.create_access_token(user.id)
    return _json_ok(
        {"user_id": user.id, "token": token},
        msg="注册成功",
    )


@router.post("/login")
def login(request: Request, body: LoginBody, db: Session = Depends(get_db)):
    allowed, _ = cache.rate_limit_increment(
        "rl:ip:login",
        _client_ip(request),
        settings.rate_limit_login_ip_max,
    )
    if not allowed:
        return _json_err(429, 429, "too many requests")
    try:
        user = user_service.login_user(db, body.phone.strip(), body.password)
    except UserServiceError as e:
        return _json_err(400, e.code, e.msg)
    token, _, _ = auth_utils.create_access_token(user.id)
    is_first_login = user.is_first_login
    # 登录后设置为非首次登录
    if is_first_login:
        user_service.set_first_login(db, user, False)
    return _json_ok(
        {"user_id": user.id, "token": token, "is_first_login": is_first_login},
        msg="登录成功",
    )


@router.post("/logout")
def logout(authorization: str | None = Header(default=None)):
    token = auth_utils.get_bearer_token(authorization)
    if not token:
        return _json_err(401, 401, "缺少 Token")
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return _json_err(401, 401, "Token 无效或已过期")
    jti = payload.get("jti")
    if jti:
        cache.session_delete(str(jti))
    return _json_ok(msg="退出成功")


@router.get("/profile")
def profile(user: User = Depends(auth_utils.get_current_user)):
    # 将标签字符串转换为列表
    tags = user.tags.split(",") if user.tags else []
    # 过滤空字符串
    tags = [tag for tag in tags if tag]
    return _json_ok(
        {
            "user_id": user.id,
            "phone": user.phone,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "tags": tags,
            "registertime": user.registertime.isoformat() if user.registertime else None,
            "lastlogintime": user.lastlogintime.isoformat() if user.lastlogintime else None,
        }
    )


@router.put("/profile/nickname")
def profile_nickname(body: NicknameBody, user: User = Depends(auth_utils.get_current_user), db: Session = Depends(get_db)):
    try:
        user = user_service.update_nickname(db, user, body.nickname)
    except UserServiceError as e:
        return _json_err(400, e.code, e.msg)
    return _json_ok({"user_id": user.id, "nickname": user.nickname}, msg="昵称更新成功")


@router.put("/profile/tags")
def profile_tags(body: TagsBody, user: User = Depends(auth_utils.get_current_user), db: Session = Depends(get_db)):
    try:
        user = user_service.update_tags(db, user, body.tags)
    except UserServiceError as e:
        return _json_err(400, e.code, e.msg)
    return _json_ok({"user_id": user.id, "tags": body.tags}, msg="标签更新成功")

@router.get("/info/{user_id}")
def get_user_info(
    user_id: str,
    db: Session = Depends(get_db),
):
    try:
        user = user_service.get_user_by_id(db, user_id)
        if not user:
            return _json_err(404, 404, "用户不存在")
        return _json_ok({"nickname": user.nickname, "phone": user.phone})
    except UserServiceError as e:
        return _json_err(400, e.code, e.msg)