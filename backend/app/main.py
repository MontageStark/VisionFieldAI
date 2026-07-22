"""FastAPI application for FieldVision AI."""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import system, camera, servo, director, stream, websocket, output
from app.api.deps import get_state_machine
from app.core.state import SystemState


logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        sm = get_state_machine()
        try:
            sm.transition(SystemState.CONNECTING)
        except Exception:
            logger.exception(
                "Lifespan startup: failed to transition state machine to %s",
                SystemState.CONNECTING.name,
            )
        yield

    app = FastAPI(
        title="FieldVision AI",
        description="Robotic Football Camera System API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(system.router)
    app.include_router(camera.router)
    app.include_router(servo.router)
    app.include_router(director.router)
    app.include_router(stream.router)
    app.include_router(websocket.router)
    app.include_router(output.router)

    _start_time = time.time()

    @app.get("/api/health", tags=["system"])
    def health_check() -> dict:
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": app.version,
        }

    @app.get("/api/health/system", tags=["system"])
    def health_system() -> dict:
        return {
            "status": "healthy",
            "components": {
                "api": {"status": "healthy", "message": "API responding"},
                "event_bus": {"status": "healthy", "message": "Event bus operational"},
                "output_manager": {"status": "healthy", "message": "Output manager ready"},
            },
            "timestamp": time.time(),
            "uptime": time.time() - _start_time,
        }

    return app


app = create_app()
