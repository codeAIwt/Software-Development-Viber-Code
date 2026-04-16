"""
自习室 REST 路由：``/api/room/*``。
契约见 RoomCreateAttend.md §11；业务委托 ``services.room_service``（本阶段使用 Redis 模拟自习室状态）。
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config.db import get_db
from models.user import User
from services import room_service
from services.ai_service import detect_person
from services.room_service import RoomServiceError
from utils import auth as auth_utils

router = APIRouter()


def _json_ok(data=None, msg: str = "OK"):
    return {"code": 200, "msg": msg, "data": data if data is not None else {}}


def _json_err(status: int, code: int, msg: str, data: dict | None = None):
    return JSONResponse(
        status_code=status,
        content={"code": code, "msg": msg, "data": data if data is not None else {}},
    )


def _http_status_for_room_error(code: int) -> int:
    return code if code in (400, 401, 403, 404, 409, 429, 500) else 400


class RoomCreateBody(BaseModel):
    theme: str
    max_people: int = Field(..., ge=1, le=8)
    tags: list = Field(default=[])


class RoomJoinBody(BaseModel):
    room_id: str = Field(..., min_length=32, max_length=32, description="32 位十六进制 UUID，无短横线")
    match_type: Literal["manual", "auto"] = "manual"


class RoomLeaveBody(BaseModel):
    room_id: str = Field(..., min_length=32, max_length=32)


class DetectPersonBody(BaseModel):
    image: str
    room_id: str = Field(..., min_length=32, max_length=32)
    user_id: str


@router.post("/create")
def create_room(
    body: RoomCreateBody,
    user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    try:
        data = room_service.create_room(db, user.id, body.theme, body.max_people, body.tags)
    except RoomServiceError as e:
        return _json_err(_http_status_for_room_error(e.code), e.code, e.msg, e.data)
    except NotImplementedError:
        return _json_err(501, 501, "自习室创建逻辑未接入存储层", {})
    return _json_ok(data, "创建成功")


@router.get("/list")
def list_rooms(
    user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
    theme: str | None = Query(default=None),
):
    try:
        data = room_service.list_idle_rooms(db, user.id, theme)
    except RoomServiceError as e:
        return _json_err(_http_status_for_room_error(e.code), e.code, e.msg, e.data)
    except NotImplementedError:
        return _json_err(501, 501, "自习室列表逻辑未接入存储层", {})
    return _json_ok(data, "OK")


@router.post("/join")
def join_room(
    body: RoomJoinBody,
    user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    try:
        data = room_service.join_room(db, user.id, body.room_id, body.match_type)
    except RoomServiceError as e:
        return _json_err(_http_status_for_room_error(e.code), e.code, e.msg, e.data)
    except NotImplementedError:
        return _json_err(501, 501, "加入自习室逻辑未接入存储层", {})
    return _json_ok(data, "加入成功")


@router.post("/leave")
def leave_room(
    body: RoomLeaveBody,
    user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    try:
        data = room_service.leave_room(db, user.id, body.room_id)
    except RoomServiceError as e:
        return _json_err(_http_status_for_room_error(e.code), e.code, e.msg, e.data)
    except NotImplementedError:
        return _json_err(501, 501, "退出自习室逻辑未接入存储层", {})
    return _json_ok(data, "退出成功")

@router.get("/info/{room_id}")
def get_room_info(
    room_id: str,
    user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    try:
        data = room_service.get_room_info(db, room_id)
    except RoomServiceError as e:
        return _json_err(_http_status_for_room_error(e.code), e.code, e.msg, e.data)
    return _json_ok(data, "获取成功")

class RoomUpdateBody(BaseModel):
    theme: str | None = None

@router.put("/update/{room_id}")
def update_room(
    room_id: str,
    body: RoomUpdateBody,
    user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    try:
        data = room_service.update_room_info(db, user.id, room_id, body.theme)
    except RoomServiceError as e:
        return _json_err(_http_status_for_room_error(e.code), e.code, e.msg, e.data)
    return _json_ok(data, "更新成功")

@router.delete("/destroy/{room_id}")
def destroy_room(
    room_id: str,
    user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    try:
        data = room_service.destroy_room(db, user.id, room_id)
    except RoomServiceError as e:
        return _json_err(_http_status_for_room_error(e.code), e.code, e.msg, e.data)
    return _json_ok(data, "销毁成功")


@router.post("/detect-person")
def detect_person_api(
    body: DetectPersonBody,
    user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    """
    检测摄像头前是否有人
    """
    try:
        # 验证用户身份，只能检测自己的摄像头
        if body.user_id != user.id:
            return _json_err(403, 403, "无权检测其他用户", {})
        
        # 处理Base64图像
        import base64
        image_data = base64.b64decode(body.image.split(',')[1])
        
        # 检测是否有人
        has_person = detect_person(image_data)
        
        if not has_person:
            # 检测到无人，自动退出房间
            room_service.leave_room(db, user.id, body.room_id)
        
        return _json_ok({
            "has_person": has_person
        })
    except Exception as e:
        print(f"AI检测API失败: {str(e)}")
        # 检测失败时默认返回有人，避免误判
        return _json_ok({
            "has_person": True
        })