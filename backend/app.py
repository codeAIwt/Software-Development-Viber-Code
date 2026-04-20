from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.db import init_db
from controllers.room_controller import router as room_router
from controllers.user_controller import router as user_router
from controllers.duration_controller import router as duration_router
from services import room_service
from config.db import SessionLocal
from starlette.concurrency import run_in_threadpool


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


class ConnectionManager:
    def __init__(self):
        # room_id -> {user_id: WebSocket}
        self.active_connections: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        self.active_connections[room_id][user_id] = websocket
        
        # 通知房间内其他用户有新用户加入
        await self.broadcast(room_id, {
            "type": "user_join",
            "user_id": user_id
        }, exclude_user=user_id)

    def disconnect(self, room_id: str, user_id: str):
        if room_id in self.active_connections and user_id in self.active_connections[room_id]:
            del self.active_connections[room_id][user_id]
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: str, message: dict, exclude_user: str = None):
        if room_id in self.active_connections:
            for user_id, connection in self.active_connections[room_id].items():
                if user_id != exclude_user:
                    await connection.send_json(message)

    async def send_personal_message(self, room_id: str, user_id: str, message: dict):
        if room_id in self.active_connections and user_id in self.active_connections[room_id]:
            await self.active_connections[room_id][user_id].send_json(message)


manager = ConnectionManager()


def create_app() -> FastAPI:
    app = FastAPI(title="线上伴学 API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_, exc: HTTPException):
        detail = exc.detail
        if isinstance(detail, dict) and "code" in detail:
            return JSONResponse(status_code=exc.status_code, content=detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code, "msg": str(detail), "data": {}},
        )

    @app.websocket("/ws/room/{room_id}")
    async def websocket_endpoint(websocket: WebSocket, room_id: str):
        user_id = websocket.query_params.get("user_id")
        if not user_id:
            await websocket.close(code=1008, reason="Missing user_id")
            return
        
        await manager.connect(websocket, room_id, user_id)
        
        try:
            while True:
                data = await websocket.receive_json()
                message_type = data.get("type")
                
                if message_type in ["offer", "answer", "ice_candidate"]:
                    # 转发信令消息
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
        except WebSocketDisconnect:
            manager.disconnect(room_id, user_id)
            # 尝试在服务器端将该用户从房间中移除（清理 Redis / 持久化学习时长）
            try:
                db = SessionLocal()
                try:
                    # room_service.leave_room 是同步阻塞函数，在线程池中执行
                    await run_in_threadpool(room_service.leave_room, db, user_id, room_id)
                finally:
                    db.close()
            except Exception as e:
                print(f"Error during websocket disconnect cleanup: {e}")

            # 通知房间内其他用户有用户离开
            await manager.broadcast(room_id, {
                "type": "user_leave",
                "user_id": user_id
            })

    app.include_router(user_router, prefix="/api/user", tags=["user"])
    app.include_router(room_router, prefix="/api/room", tags=["room"])
    app.include_router(duration_router, prefix="/api/duration", tags=["duration"])
    return app


app = create_app()