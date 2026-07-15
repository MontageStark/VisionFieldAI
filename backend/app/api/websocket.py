"""WebSocket endpoint for real-time updates."""
from __future__ import annotations

import asyncio
import json
import time
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)

    async def broadcast(self, message: dict) -> None:
        dead: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections.discard(ws)

    @property
    def count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            msg_type = msg.get("type", "ping")

            if msg_type == "ping":
                await ws.send_json({"type": "pong", "timestamp": time.time()})
            elif msg_type == "subscribe":
                # TODO(incomplete): Currently a no-op acknowledgement only.
                # Subscription state is not yet stored on ConnectionManager,
                # and broadcasts are not filtered by topic — every client
                # still receives every message via ConnectionManager.broadcast.
                # Wire up per-topic subscriptions before relying on this in
                # production.
                topic = msg.get("topic", "all")
                await ws.send_json({
                    "type": "subscribed",
                    "topic": topic,
                    "timestamp": time.time(),
                })
            else:
                await ws.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                })
    except WebSocketDisconnect:
        manager.disconnect(ws)
