"""
WebSocket 连接侧工具：维护 `user_id` / `room_id` → 连接句柄 映射，供 `ws/server` 定向推送。
"""

from __future__ import annotations

from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # Maps user_id -> WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}
        # Maps room_id -> set of user_id
        self.room_users: Dict[str, Set[str]] = {}

    def register_connection(self, user_id: str, connection: WebSocket) -> None:
        """用户上线时登记连接。"""
        self.active_connections[user_id] = connection

    def unregister_connection(self, user_id: str) -> None:
        """断开时移除。"""
        self.active_connections.pop(user_id, None)
        # Check and remove the user from any rooms they were registered in
        for room_id, users in self.room_users.items():
            if user_id in users:
                users.discard(user_id)

    def bind_user_room(self, user_id: str, room_id: str) -> None:
        """用户进入房间会话时绑定 room 上下文。"""
        if room_id not in self.room_users:
            self.room_users[room_id] = set()
        self.room_users[room_id].add(user_id)

    def unbind_user_room(self, user_id: str, room_id: str) -> None:
        """离开房间时解除绑定。"""
        if room_id in self.room_users:
            self.room_users[room_id].discard(user_id)
            # Cleanup empty rooms
            if not self.room_users[room_id]:
                del self.room_users[room_id]


# Global instance
manager = ConnectionManager()
