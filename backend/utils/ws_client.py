"""
WebSocket 连接侧工具：维护 ``user_id`` / ``room_id`` → 连接句柄 映射，供 ``ws/server`` 定向推送。
本文件仅定义函数契约；具体实现依赖选用的 ASGI WebSocket 栈。
"""

from __future__ import annotations

from typing import Any


def register_connection(user_id: str, connection: Any) -> None:
    """用户上线时登记连接。"""
    raise NotImplementedError("register_connection")


def unregister_connection(user_id: str) -> None:
    """断开时移除。"""
    raise NotImplementedError("unregister_connection")


def bind_user_room(user_id: str, room_id: str) -> None:
    """用户进入房间会话时绑定 room 上下文。"""
    raise NotImplementedError("bind_user_room")


def unbind_user_room(user_id: str, room_id: str) -> None:
    """离开房间时解除绑定。"""
    raise NotImplementedError("unbind_user_room")
