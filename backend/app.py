from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.db import init_db
from controllers.room_controller import router as room_router
from controllers.user_controller import router as user_router
from controllers.duration_controller import router as duration_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


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

    app.include_router(user_router, prefix="/api/user", tags=["user"])
    app.include_router(room_router, prefix="/api/room", tags=["room"])
    app.include_router(duration_router, prefix="/api/duration", tags=["duration"])
    return app


app = create_app()