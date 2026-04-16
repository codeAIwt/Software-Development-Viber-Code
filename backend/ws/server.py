"""
WebSocket 服务端骨架：自动匹配邀请与成员变更广播。
消息类型见 RoomCreateAttend.md §10；实现时与 utils/ws_client 维护连接映射。
"""

from __future__ import annotations

from typing import Any
from utils.ws_client import manager


async def send_room_invite(
    target_user_id: str,
    payload: dict[str, Any],
) -> None:
    """服务端 → 客户端 room_invite（§10.1）。"""
    connection = manager.active_connections.get(target_user_id)
    if connection:
        await connection.send_json({
            "type": "room_invite",
            "data": payload
        })


async def broadcast_user_join(room_id: str, payload: dict[str, Any]) -> None:
    """房间内广播 user_join（§10.2）。"""
    user_ids = manager.room_users.get(room_id, set())
    for user_id in user_ids:
        connection = manager.active_connections.get(user_id)
        if connection:
            try:
                await connection.send_json({
                    "type": "user_join",
                    "data": payload
                })
            except Exception:
                pass


async def broadcast_user_leave(room_id: str, payload: dict[str, Any]) -> None:
    """房间内广播 user_leave（§10.2）。"""
    user_ids = manager.room_users.get(room_id, set())
    for user_id in user_ids:
        connection = manager.active_connections.get(user_id)
        if connection:
            try:
                await connection.send_json({
                    "type": "user_leave",
                    "data": payload
                })
            except Exception:
                pass
