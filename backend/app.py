from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.db import init_db
from controllers.room_controller import router as room_router
from controllers.user_controller import router as user_router
from controllers.duration_controller import router as duration_router
from controllers.bookmark_controller import router as bookmark_router
from services import room_service
from config.db import SessionLocal
from starlette.concurrency import run_in_threadpool

from ws.server import handle_websocket_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="线上伴学 API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ],
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

        try:
            await handle_websocket_session(websocket, room_id, user_id)
        except WebSocketDisconnect:
            pass

        await manager.broadcast_user_leave(room_id, user_id)
        manager.disconnect(room_id, user_id)

        try:
            db = SessionLocal()
            try:
                await run_in_threadpool(room_service.leave_room, db, user_id, room_id)
            finally:
                db.close()
        except Exception as e:
            print(f"Error during websocket disconnect cleanup: {e}")

    app.include_router(user_router, prefix="/api/user", tags=["user"])
    app.include_router(room_router, prefix="/api/room", tags=["room"])
    app.include_router(duration_router, prefix="/api/duration", tags=["duration"])
    app.include_router(bookmark_router, prefix="/api/bookmark", tags=["bookmark"])
    return app


app = create_app()
