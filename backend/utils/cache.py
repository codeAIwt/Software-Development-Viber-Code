import json
from datetime import datetime, timezone
from typing import Any

import redis

from config.settings import settings

_mem = None


def _redis() -> redis.Redis:
    global _mem
    if settings.redis_url == "fakeredis":
        if _mem is None:
            import fakeredis

            _mem = fakeredis.FakeRedis(decode_responses=True)
        return _mem
    return redis.from_url(settings.redis_url, decode_responses=True)


def session_key(jti: str) -> str:
    return f"auth:session:{jti}"


def session_set(jti: str, user_id: str, ttl_seconds: int) -> None:
    r = _redis()
    r.setex(session_key(jti), ttl_seconds, json.dumps({"user_id": user_id}))


def session_get(jti: str) -> dict[str, Any] | None:
    r = _redis()
    raw = r.get(session_key(jti))
    if not raw:
        return None
    return json.loads(raw)


def session_delete(jti: str) -> None:
    r = _redis()
    r.delete(session_key(jti))


def rate_limit_increment(prefix: str, ip: str, limit: int) -> tuple[bool, int]:
    """
    固定窗口（分钟）限流。键：{prefix}:{ip}:{yyyyMMddHHmm}
    返回 (allowed, current_count)。
    """
    slot = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    key = f"{prefix}:{ip}:{slot}"
    r = _redis()
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.ttl(key)
    count, ttl = pipe.execute()
    if ttl == -1:
        r.expire(key, 120)
    return count <= limit, int(count)


# --- 自习室 Redis 键与锁（RoomCreateAttend.md §9）；以下为契约函数，业务逻辑在 room_service 迭代中实现 ---


def room_meta_key(room_id: str) -> str:
    """``room:meta:{room_id}`` Hash。"""
    return f"room:meta:{room_id}"


def rooms_idle_zset_key(theme: str) -> str:
    """``rooms:idle:{theme}`` Sorted Set。"""
    return f"rooms:idle:{theme}"


def match_waiting_users_key(theme: str) -> str:
    """``match:waiting_users:{theme}`` Sorted Set。"""
    return f"match:waiting_users:{theme}"


def match_invite_key(room_id: str, user_id: str) -> str:
    """``match:invite:{room_id}:{user_id}`` String。"""
    return f"match:invite:{room_id}:{user_id}"


def lock_room_join_key(room_id: str) -> str:
    """``lock:room_join:{room_id}`` 分布式锁。"""
    return f"lock:room_join:{room_id}"


def lock_room_leave_key(room_id: str) -> str:
    """``lock:room_leave:{room_id}`` 分布式锁。"""
    return f"lock:room_leave:{room_id}"


def acquire_room_join_lock(room_id: str, timeout_ms: int = 3000, wait_ms: int = 1000) -> bool:
    """
    获取加入房间锁（SET NX PX）。``LOCK_TTL_MS`` / ``LOCK_WAIT_MS`` 见 RoomCreateAttend.md §9.2。
    成功返回 True；当前为占位实现，应在 room_service 中接入真实 Redis 命令。
    """
    r = _redis()
    key = lock_room_join_key(room_id)
    # Use a token to emulate uniqueness; release is best-effort in this MVP.
    token = f"join:{room_id}:{datetime.now(timezone.utc).timestamp()}"
    deadline = datetime.now(timezone.utc).timestamp() + wait_ms / 1000.0
    import time

    while True:
        acquired = r.set(key, token, nx=True, px=timeout_ms)
        if acquired:
            return True
        if datetime.now(timezone.utc).timestamp() >= deadline:
            return False
        time.sleep(0.05)


def release_room_join_lock(room_id: str) -> None:
    """释放加入房间锁（占位）。"""
    r = _redis()
    try:
        r.delete(lock_room_join_key(room_id))
    except Exception:
        return


def acquire_room_leave_lock(room_id: str, timeout_ms: int = 3000, wait_ms: int = 1000) -> bool:
    """获取离开房间锁（占位）。"""
    r = _redis()
    key = lock_room_leave_key(room_id)
    token = f"leave:{room_id}:{datetime.now(timezone.utc).timestamp()}"
    deadline = datetime.now(timezone.utc).timestamp() + wait_ms / 1000.0
    import time

    while True:
        acquired = r.set(key, token, nx=True, px=timeout_ms)
        if acquired:
            return True
        if datetime.now(timezone.utc).timestamp() >= deadline:
            return False
        time.sleep(0.05)


def release_room_leave_lock(room_id: str) -> None:
    """释放离开房间锁（占位）。"""
    r = _redis()
    try:
        r.delete(lock_room_leave_key(room_id))
    except Exception:
        return


# --- 高层封装：自习室相关键与常用操作（减少业务层对 Redis 命令与键名的直接依赖）
def room_users_all_key(room_id: str) -> str:
    """历史/所有成员集合键。"""
    return f"room:users:{room_id}"


def room_users_active_key(room_id: str) -> str:
    """活跃成员集合键（等价于 leave_time IS NULL）。"""
    return f"room:active_users:{room_id}"


def user_join_time_key(room_id: str, user_id: str) -> str:
    return f"room:join_time:{room_id}:{user_id}"


def user_leave_time_key(room_id: str, user_id: str) -> str:
    return f"room:leave_time:{room_id}:{user_id}"


def user_study_duration_key(room_id: str, user_id: str) -> str:
    return f"room:study_duration:{room_id}:{user_id}"


def get_room_meta(room_id: str) -> dict | None:
    """Fetch room meta hash; return None when missing."""
    r = _redis()
    meta = r.hgetall(room_meta_key(room_id))
    if not meta:
        return None
    return meta


def get_idle_rooms(theme: str, start: int = 0, end: int = -1) -> list:
    """Return room ids from idle zset (most-recent first)."""
    r = _redis()
    return r.zrevrange(rooms_idle_zset_key(theme), start, end)


def is_user_active_in_room(room_id: str, user_id: str) -> bool:
    r = _redis()
    return r.sismember(room_users_active_key(room_id), user_id)


def get_room_active_members(room_id: str) -> set:
    r = _redis()
    return r.smembers(room_users_active_key(room_id))


def get_room_all_members(room_id: str) -> set:
    r = _redis()
    return r.smembers(room_users_all_key(room_id))

