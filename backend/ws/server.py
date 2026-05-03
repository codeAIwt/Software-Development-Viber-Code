"""
WebSocket 信令服务器 - 处理 WebRTC 信令和 AI 检测消息
"""

from __future__ import annotations

from fastapi import WebSocket

from utils.ws_client import manager


SIGNAL_TYPES = ["offer", "answer", "ice_candidate"]


async def handle_signaling_message(room_id: str, user_id: str, data: dict) -> None:
    """处理 WebRTC 信令消息：转发给目标用户"""
    message_type = data.get("type")
    target_user_id = data.get("target_user_id")

    if target_user_id:
        await manager.send_personal_message(
            room_id,
            target_user_id,
            {
                "type": message_type,
                "user_id": user_id,
                "data": data.get("data")
            }
        )


async def handle_ai_detection_message(room_id: str, user_id: str, data: dict) -> None:
    """处理 AI 检测消息：广播给房间内其他用户"""
    await manager.broadcast(
        room_id,
        {
            "type": "ai_detection",
            "user_id": user_id,
            "data": data.get("data")
        },
        exclude_user=user_id
    )


async def handle_websocket_session(websocket: WebSocket, room_id: str, user_id: str) -> None:
    """处理 WebSocket 会话的消息循环"""
    await manager.connect(websocket, room_id, user_id)
    await manager.broadcast_user_join(room_id, user_id)

    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type in SIGNAL_TYPES:
                await handle_signaling_message(room_id, user_id, data)
            elif message_type == "ai_detection":
                await handle_ai_detection_message(room_id, user_id, data)
    except Exception:
        pass
