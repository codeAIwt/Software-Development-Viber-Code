"""
WebSocket 连接管理器 - 统一实现
维护 room_id -> user_id -> WebSocket 连接映射
"""

from __future__ import annotations

from typing import Dict
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: str) -> None:
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        self.active_connections[room_id][user_id] = websocket

    def disconnect(self, room_id: str, user_id: str) -> None:
        if room_id in self.active_connections and user_id in self.active_connections[room_id]:
            del self.active_connections[room_id][user_id]
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: str, message: dict, exclude_user: str = None) -> None:
        if room_id in self.active_connections:
            recipients = []
            for user_id, connection in self.active_connections[room_id].items():
                if user_id != exclude_user:
                    recipients.append(user_id)
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        print(f"[ConnectionManager] failed to send to {user_id}: {e}")
            print(f"[ConnectionManager] broadcast to room {room_id}, recipients: {recipients}, message: {message}")

    async def send_personal_message(self, room_id: str, user_id: str, message: dict) -> None:
        if room_id in self.active_connections and user_id in self.active_connections[room_id]:
            await self.active_connections[room_id][user_id].send_json(message)

    async def broadcast_user_join(self, room_id: str, user_id: str) -> None:
        await self.broadcast(room_id, {
            "type": "user_join",
            "user_id": user_id
        }, exclude_user=user_id)

    async def broadcast_user_leave(self, room_id: str, user_id: str) -> None:
        print(f"[ConnectionManager] broadcast_user_leave: room_id={room_id}, user_id={user_id}")
        print(f"[ConnectionManager] active_connections before broadcast: {list(self.active_connections.get(room_id, {}).keys())}")
        await self.broadcast(room_id, {
            "type": "user_leave",
            "user_id": user_id
        })
        print(f"[ConnectionManager] broadcast_user_leave completed for {user_id}")

    async def broadcast_room_destroyed(self, room_id: str) -> None:
        print(f"[ConnectionManager] broadcast_room_destroyed: room_id={room_id}")
        await self.broadcast(room_id, {
            "type": "room_destroyed",
            "room_id": room_id
        })
        print(f"[ConnectionManager] broadcast_room_destroyed completed")


manager = ConnectionManager()
