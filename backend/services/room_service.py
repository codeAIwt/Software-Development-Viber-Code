"""
自习室业务入口：创建 / 列表 / 加入 / 退出。

按你的阶段性要求：
- 匹配功能、摄像机/WebSocket 暂不接入
- 数据库暂不落地（不读写 MySQL 表；房间状态使用 Redis 内存结构模拟）

实现契约见 ``详细设计/RoomCreateAttend.md`` §11。
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Literal
from uuid import uuid4

from sqlalchemy.orm import Session

from models.study_room import StudyRoom
from models.room_user import RoomUser
from utils import cache

MatchType = Literal["manual", "auto"]


# 移除主题限制，使用标签作为主题
ALLOWED_THEMES = set()
LIST_ROOMS_LIMIT = 50
LIST_ROOMS_LIMIT_PER_THEME = 10


class RoomServiceError(Exception):
    """业务可预期错误；``code`` 与通用响应体 ``code`` 对齐。"""

    def __init__(self, code: int, msg: str, data: dict | None = None):
        self.code = code
        self.msg = msg
        self.data = data if data is not None else {}


def _now_ms() -> int:
    # 使用北京时间（UTC+8）
    beijing_timezone = timezone(timedelta(hours=8))
    now = datetime.now(beijing_timezone)
    print(f"当前时间: {now}")
    return int(now.timestamp() * 1000)


def _room_users_all_key(room_id: str) -> str:
    # 仅用于防止重复进入同一房间（历史成员也算重复）。
    return f"room:users:{room_id}"


def _room_users_active_key(room_id: str) -> str:
    # 用于判断“活跃成员”：leave_time IS NULL 的等价状态。
    return f"room:active_users:{room_id}"


def _user_join_time_key(room_id: str, user_id: str) -> str:
    # 记录用户加入房间的时间
    return f"room:join_time:{room_id}:{user_id}"


def _user_leave_time_key(room_id: str, user_id: str) -> str:
    # 记录用户离开房间的时间
    return f"room:leave_time:{room_id}:{user_id}"


def _user_study_duration_key(room_id: str, user_id: str) -> str:
    # 记录用户在房间中的学习时长（毫秒）
    return f"room:study_duration:{room_id}:{user_id}"


def _read_room_meta(r, room_id: str) -> dict | None:
    meta = r.hgetall(cache.room_meta_key(room_id))
    if not meta:
        return None
    # redis 返回全是 str；后续转类型
    return meta


def _check_user_in_any_room(r, user_id: str) -> str | None:
    """
    检查用户是否在任何房间中
    返回用户所在的房间ID，如果不在任何房间中返回None
    """
    # 遍历所有主题，检查用户是否在任何房间中
    themes = ["考研", "期末", "考公", "语言"]
    for theme in themes:
        # 获取该主题下的所有房间
        room_ids = r.zrevrange(cache.rooms_idle_zset_key(theme), 0, -1)
        for room_id in room_ids:
            # 检查用户是否在该房间的活跃成员中
            active_key = _room_users_active_key(room_id)
            if r.sismember(active_key, user_id):
                return room_id
    return None


def create_room(db: Session, creator_user_id: str, theme: str, max_people: int, tags: list = None) -> dict:
    if not theme:
        raise RoomServiceError(400, "theme 不能为空", {})
    if not isinstance(max_people, int) or max_people < 1 or max_people > 8:
        raise RoomServiceError(400, "max_people 非法", {})
    
    # 检查用户是否已经在其他房间中
    r = cache._redis()
    existing_room = _check_user_in_any_room(r, creator_user_id)
    if existing_room:
        raise RoomServiceError(400, "需要退出当前自习室才能创建新自习室", {"existing_room_id": existing_room})

    # 处理标签
    tags = tags or []
    if len(tags) > 3:
        raise RoomServiceError(400, "标签最多只能有3个", {})
    tags_str = ",".join(tags)

    r = cache._redis()
    room_id = uuid4().hex
    now_ms = _now_ms()

    status = "full" if max_people == 1 else "idle"
    meta_key = cache.room_meta_key(room_id)
    all_key = _room_users_all_key(room_id)
    active_key = _room_users_active_key(room_id)
    idle_zset_key = cache.rooms_idle_zset_key(theme)

    pipe = r.pipeline()
    pipe.hset(
        meta_key,
        mapping={
            "theme": theme,
            "max_people": str(max_people),
            "current_people": "1",
            "status": status,
            "creator_id": creator_user_id,
            "created_ts_ms": str(now_ms),
            "updated_ts_ms": str(now_ms),
            "tags": tags_str,
        },
    )
    pipe.sadd(all_key, creator_user_id)
    pipe.sadd(active_key, creator_user_id)
    # 记录创建者的加入时间
    pipe.set(_user_join_time_key(room_id, creator_user_id), str(now_ms))
    if status == "idle":
        pipe.zadd(idle_zset_key, {room_id: now_ms})
    else:
        pipe.zrem(idle_zset_key, room_id)
    pipe.execute()
    
    # 保存到数据库
    beijing_timezone = timezone(timedelta(hours=8))
    now = datetime.now(beijing_timezone)
    
    # 创建自习室记录
    study_room = StudyRoom(
        id=room_id,
        theme=theme,
        max_people=max_people,
        current_people=1,
        status=status,
        creator_id=creator_user_id,
        create_time=now,
        tags=tags_str
    )
    db.add(study_room)
    
    # 创建房间成员记录
    room_user = RoomUser(
        room_id=room_id,
        user_id=creator_user_id,
        join_time=now,
        leave_time=None,
        privacy_mode="blur",
        camera=1
    )
    db.add(room_user)
    
    # 提交事务
    db.commit()
    
    # 打印数据库中的自习室信息
    print("\n===== 数据库自习室信息 =====")
    print(f"房间ID: {study_room.id}")
    print(f"主题: {study_room.theme}")
    print(f"最大人数: {study_room.max_people}")
    print(f"当前人数: {study_room.current_people}")
    print(f"状态: {study_room.status}")
    print(f"创建者ID: {study_room.creator_id}")
    print(f"创建时间: {study_room.create_time}")
    print(f"标签: {study_room.tags}")
    print("==========================\n")
    
    # 打印创建者的加入时间
    print(f"创建房间 {room_id} 成功，创建者 {creator_user_id} 的加入时间: {now_ms}")

    return {
        "room_id": room_id,
        "room_status": status,
        "max_people": max_people,
        "current_people": 1,
        "tags": tags,
    }


def list_idle_rooms(db: Session, viewer_user_id: str, theme: str | None) -> dict:
    r = cache._redis()

    themes = ["考研", "期末", "考公", "语言"]
    rooms: list[dict] = []
    seen: set[str] = set()

    def add_from_theme(t: str) -> None:
        ids = r.zrevrange(cache.rooms_idle_zset_key(t), 0, LIST_ROOMS_LIMIT_PER_THEME - 1)
        for rid in ids:
            if rid in seen:
                continue
            meta = r.hgetall(cache.room_meta_key(rid))
            if not meta:
                continue
            if meta.get("status") != "idle":
                continue
            seen.add(rid)
            # 解析标签
            tags_str = meta.get("tags", "")
            tags = tags_str.split(",") if tags_str else []
            # 过滤空标签
            tags = [tag for tag in tags if tag]
            rooms.append(
                {
                    "room_id": rid,
                    "theme": meta.get("theme"),
                    "current_people": int(meta.get("current_people", "0")),
                    "max_people": int(meta.get("max_people", "0")),
                    "status": "idle",
                    "creator_id": meta.get("creator_id"),
                    "created_ts_ms": meta.get("created_ts_ms"),
                    "tags": tags,
                }
            )

    # 添加用户自己创建的房间，即使房间状态不是idle
    def add_user_created_rooms():
        # 遍历所有主题，查找用户创建的房间
        for t in themes:
            # 这里简化处理，实际项目中可能需要更高效的方式
            # 例如使用一个单独的集合存储用户创建的房间ID
            ids = r.zrevrange(cache.rooms_idle_zset_key(t), 0, -1)
            for rid in ids:
                if rid in seen:
                    continue
                meta = r.hgetall(cache.room_meta_key(rid))
                if not meta:
                    continue
                # 检查是否是用户创建的房间
                if meta.get("creator_id") == viewer_user_id:
                    seen.add(rid)
                    # 解析标签
                    tags_str = meta.get("tags", "")
                    tags = tags_str.split(",") if tags_str else []
                    # 过滤空标签
                    tags = [tag for tag in tags if tag]
                    rooms.append(
                        {
                            "room_id": rid,
                            "theme": meta.get("theme"),
                            "current_people": int(meta.get("current_people", "0")),
                            "max_people": int(meta.get("max_people", "0")),
                            "status": meta.get("status"),
                            "creator_id": meta.get("creator_id"),
                            "created_ts_ms": meta.get("created_ts_ms"),
                            "tags": tags,
                        }
                    )

    if theme is None:
        for t in themes:
            if len(rooms) >= LIST_ROOMS_LIMIT:
                break
            add_from_theme(t)
            if len(rooms) >= LIST_ROOMS_LIMIT:
                break
        # 添加用户自己创建的房间
        add_user_created_rooms()
        rooms = rooms[:LIST_ROOMS_LIMIT]
    else:
        add_from_theme(theme)
        # 添加用户自己创建的该主题的房间
        ids = r.zrevrange(cache.rooms_idle_zset_key(theme), 0, -1)
        for rid in ids:
            if rid in seen:
                continue
            meta = r.hgetall(cache.room_meta_key(rid))
            if not meta:
                continue
            if meta.get("creator_id") == viewer_user_id:
                seen.add(rid)
                # 解析标签
                tags_str = meta.get("tags", "")
                tags = tags_str.split(",") if tags_str else []
                # 过滤空标签
                tags = [tag for tag in tags if tag]
                rooms.append(
                    {
                        "room_id": rid,
                        "theme": meta.get("theme"),
                        "current_people": int(meta.get("current_people", "0")),
                        "max_people": int(meta.get("max_people", "0")),
                        "status": meta.get("status"),
                        "creator_id": meta.get("creator_id"),
                        "created_ts_ms": meta.get("created_ts_ms"),
                        "tags": tags,
                    }
                )
        rooms = rooms[:LIST_ROOMS_LIMIT_PER_THEME]

    return {"rooms": rooms}


def join_room(db: Session, user_id: str, room_id: str, match_type: MatchType) -> dict:
    r = cache._redis()
    now_ms = _now_ms()
    
    # 检查用户是否已经在其他房间中
    existing_room = _check_user_in_any_room(r, user_id)
    if existing_room and existing_room != room_id:
        raise RoomServiceError(400, "需要退出当前自习室才能加入新自习室", {"existing_room_id": existing_room})

    if not cache.acquire_room_join_lock(room_id):
        raise RoomServiceError(409, "加入房间超时", {"match_fail_reason": "timeout"})

    try:
        meta = _read_room_meta(r, room_id)
        if not meta:
            raise RoomServiceError(404, "房间不存在", {"match_fail_reason": "no_room"})

        status = meta.get("status")
        if status == "closed":
            raise RoomServiceError(404, "房间不存在", {"match_fail_reason": "no_room"})

        theme = meta.get("theme")
        max_people = int(meta.get("max_people", "0"))

        all_key = _room_users_all_key(room_id)
        active_key = _room_users_active_key(room_id)
        idle_zset_key = cache.rooms_idle_zset_key(theme)

        # 检查用户是否已经在房间中
        if r.sismember(active_key, user_id):
            # 用户已经在房间中，直接返回成功
            return {
                "room_id": room_id,
                "match_type": match_type,
                "privacy_mode": "blur",
                "camera": 1,
            }

        # 检查用户是否曾经在房间中但已退出
        if r.sismember(all_key, user_id):
            # 用户曾经在房间中，现在重新加入
            active_count = int(r.scard(active_key))
            if active_count >= max_people:
                raise RoomServiceError(409, "房间已满", {"match_fail_reason": "full"})

            new_current = active_count + 1
            new_status = "full" if new_current == max_people else "idle"

            pipe = r.pipeline()
            pipe.sadd(active_key, user_id)
            # 记录加入时间
            pipe.set(_user_join_time_key(room_id, user_id), str(now_ms))
            # 清除上次的离开时间
            pipe.delete(_user_leave_time_key(room_id, user_id))
            pipe.hset(
                cache.room_meta_key(room_id),
                mapping={
                    "theme": theme,
                    "max_people": str(max_people),
                    "current_people": str(new_current),
                    "status": new_status,
                    "creator_id": meta.get("creator_id", ""),
                    "created_ts_ms": meta.get("created_ts_ms", str(now_ms)),
                    "updated_ts_ms": str(now_ms),
                },
            )
            if new_status == "full":
                pipe.zrem(idle_zset_key, room_id)
            else:
                pipe.zadd(idle_zset_key, {room_id: now_ms})
            pipe.execute()
            
            # 打印用户加入时间
            print(f"用户 {user_id} 加入房间 {room_id}，加入时间: {now_ms}")
        else:
            # 新用户加入
            active_count = int(r.scard(active_key))
            if active_count >= max_people:
                raise RoomServiceError(409, "房间已满", {"match_fail_reason": "full"})

            new_current = active_count + 1
            new_status = "full" if new_current == max_people else "idle"

            pipe = r.pipeline()
            pipe.sadd(all_key, user_id)
            pipe.sadd(active_key, user_id)
            # 记录加入时间
            pipe.set(_user_join_time_key(room_id, user_id), str(now_ms))
            pipe.hset(
                cache.room_meta_key(room_id),
                mapping={
                    "theme": theme,
                    "max_people": str(max_people),
                    "current_people": str(new_current),
                    "status": new_status,
                    "creator_id": meta.get("creator_id", ""),
                    "created_ts_ms": meta.get("created_ts_ms", str(now_ms)),
                    "updated_ts_ms": str(now_ms),
                },
            )
            if new_status == "full":
                pipe.zrem(idle_zset_key, room_id)
            else:
                pipe.zadd(idle_zset_key, {room_id: now_ms})
            pipe.execute()
            
            # 打印用户加入时间
            print(f"用户 {user_id} 加入房间 {room_id}，加入时间: {now_ms}")

        return {
            "room_id": room_id,
            "match_type": match_type,
            "privacy_mode": "blur",
            "camera": 1,
        }
    finally:
        cache.release_room_join_lock(room_id)


def leave_room(db: Session, user_id: str, room_id: str) -> dict:
    r = cache._redis()
    now_ms = _now_ms()

    if not cache.acquire_room_leave_lock(room_id):
        raise RoomServiceError(409, "leave timeout", {})

    try:
        meta = _read_room_meta(r, room_id)
        if not meta:
            raise RoomServiceError(404, "房间不存在", {})

        active_key = _room_users_active_key(room_id)
        if not r.sismember(active_key, user_id):
            raise RoomServiceError(403, "不在房间中", {})

        theme = meta.get("theme")
        idle_zset_key = cache.rooms_idle_zset_key(theme)

        active_count = int(r.scard(active_key))
        new_current = active_count - 1
        new_status = "closed" if new_current == 0 else "idle"

        # 计算学习时长
        join_time_str = r.get(_user_join_time_key(room_id, user_id))
        study_duration = 0
        if join_time_str:
            join_time = int(join_time_str)
            study_duration = now_ms - join_time

        pipe = r.pipeline()
        pipe.srem(active_key, user_id)
        # 记录离开时间
        pipe.set(_user_leave_time_key(room_id, user_id), str(now_ms))
        # 记录学习时长
        pipe.set(_user_study_duration_key(room_id, user_id), str(study_duration))
        
        if new_status == "closed":
            # 当房间关闭时，删除房间的所有相关信息
            pipe.delete(cache.room_meta_key(room_id))
            pipe.delete(_room_users_all_key(room_id))
            pipe.delete(active_key)
            pipe.zrem(idle_zset_key, room_id)
            # 删除所有用户的加入时间、离开时间和学习时长
            users = r.smembers(_room_users_all_key(room_id))
            for u in users:
                pipe.delete(_user_join_time_key(room_id, u))
                pipe.delete(_user_leave_time_key(room_id, u))
                pipe.delete(_user_study_duration_key(room_id, u))
        else:
            # 否则更新房间信息
            pipe.hset(
                cache.room_meta_key(room_id),
                mapping={
                    "theme": theme,
                    "max_people": meta.get("max_people", "0"),
                    "current_people": str(new_current),
                    "status": new_status,
                    "creator_id": meta.get("creator_id", ""),
                    "created_ts_ms": meta.get("created_ts_ms", str(now_ms)),
                    "updated_ts_ms": str(now_ms),
                },
            )
            pipe.zadd(idle_zset_key, {room_id: now_ms})
        pipe.execute()
        
        # 打印用户离开时间和学习时长
        print(f"用户 {user_id} 离开房间 {room_id}，离开时间: {now_ms}")
        print(f"用户 {user_id} 在房间 {room_id} 中的学习时长: {study_duration // 60000} 分钟")
        
        # 如果房间关闭，打印关闭信息
        if new_status == "closed":
            print(f"房间 {room_id} 已关闭，所有成员已离开")

        return {
            "room_id": room_id,
            "study_duration": study_duration // 60000  # 转换为分钟
        }
    finally:
        cache.release_room_leave_lock(room_id)

def get_room_info(db: Session, room_id: str) -> dict:
    r = cache._redis()
    meta = r.hgetall(cache.room_meta_key(room_id))
    if not meta:
        raise RoomServiceError(404, "房间不存在", {})
    
    # 解析标签
    tags_str = meta.get("tags", "")
    tags = tags_str.split(",") if tags_str else []
    # 过滤空标签
    tags = [tag for tag in tags if tag]
    
    # 获取房间内的所有用户
    active_key = _room_users_active_key(room_id)
    users = r.smembers(active_key)
    
    return {
        "room_id": room_id,
        "theme": meta.get("theme"),
        "max_people": int(meta.get("max_people", "0")),
        "current_people": int(meta.get("current_people", "0")),
        "status": meta.get("status"),
        "creator_id": meta.get("creator_id"),
        "created_ts_ms": meta.get("created_ts_ms"),
        "tags": tags,
        "users": list(users),
    }

def update_room_info(db: Session, user_id: str, room_id: str, theme: str = None) -> dict:
    r = cache._redis()
    meta = _read_room_meta(r, room_id)
    if not meta:
        raise RoomServiceError(404, "房间不存在", {})
    
    # 检查是否是创建者
    if meta.get("creator_id") != user_id:
        raise RoomServiceError(403, "只有创建者可以修改房间信息", {})
    
    now_ms = _now_ms()
    pipe = r.pipeline()
    
    # 更新房间信息
    update_data = {
        "updated_ts_ms": str(now_ms),
    }
    
    if theme:
        if theme not in ALLOWED_THEMES:
            raise RoomServiceError(400, "主题非法", {})
        update_data["theme"] = theme
    
    pipe.hset(cache.room_meta_key(room_id), mapping=update_data)
    pipe.execute()
    
    # 返回更新后的房间信息
    return get_room_info(db, room_id)

def destroy_room(db: Session, user_id: str, room_id: str) -> dict:
    r = cache._redis()
    meta = _read_room_meta(r, room_id)
    if not meta:
        raise RoomServiceError(404, "房间不存在", {})
    
    # 检查是否是创建者
    if meta.get("creator_id") != user_id:
        raise RoomServiceError(403, "只有创建者可以销毁房间", {})
    
    # 获取房间内的所有用户
    active_key = _room_users_active_key(room_id)
    users = r.smembers(active_key)
    
    now_ms = _now_ms()
    pipe = r.pipeline()
    
    # 强制所有用户离开房间
    for user in users:
        # 记录离开时间和学习时长
        join_time_str = r.get(_user_join_time_key(room_id, user))
        if join_time_str:
            join_time = int(join_time_str)
            study_duration = now_ms - join_time
            pipe.set(_user_leave_time_key(room_id, user), str(now_ms))
            pipe.set(_user_study_duration_key(room_id, user), str(study_duration))
    
    # 移除所有用户
    pipe.srem(active_key, *users)
    
    # 更新房间状态为closed
    pipe.hset(
        cache.room_meta_key(room_id),
        mapping={
            "current_people": "0",
            "status": "closed",
            "updated_ts_ms": str(now_ms),
        },
    )
    
    # 从空闲房间列表中移除
    theme = meta.get("theme")
    idle_zset_key = cache.rooms_idle_zset_key(theme)
    pipe.zrem(idle_zset_key, room_id)
    
    pipe.execute()
    
    return {
        "room_id": room_id,
        "message": "房间已销毁，所有成员已被强制退出",
    }