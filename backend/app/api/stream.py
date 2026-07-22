"""Streaming API endpoints."""
from __future__ import annotations

import logging
import socket
import time
from typing import Generator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.deps import get_stream_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stream", tags=["stream"])


@router.get("/status")
def stream_status() -> dict:
    svc = get_stream_service()
    return svc.status()


@router.post("/start")
def stream_start() -> dict:
    svc = get_stream_service()
    return svc.start()


@router.post("/stop")
def stream_stop() -> dict:
    svc = get_stream_service()
    return svc.stop()


def _try_connect(host: str, port: int, timeout: float = 3) -> socket.socket | None:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.connect((host, port))
        return sock
    except Exception:
        return None


@router.get("/proxy")
def stream_proxy(phone_ip: str = "192.168.0.176", port: int = 8080) -> StreamingResponse:
    MAX_RECONNECT_ATTEMPTS = 5
    RECONNECT_DELAY_BASE = 2  # seconds, doubles each attempt

    def frame_generator() -> Generator[bytes, None, None]:
        attempt = 0

        while attempt < MAX_RECONNECT_ATTEMPTS:
            sock = None
            try:
                logger.info("Proxy: connecting to %s:%d (attempt %d/%d)",
                            phone_ip, port, attempt + 1, MAX_RECONNECT_ATTEMPTS)

                sock = _try_connect(phone_ip, port, timeout=5)
                if not sock:
                    sock = _try_connect("127.0.0.1", port, timeout=5)
                if not sock:
                    logger.warning("Proxy: connection failed, retrying in %ds",
                                   RECONNECT_DELAY_BASE * (2 ** attempt))
                    attempt += 1
                    time.sleep(RECONNECT_DELAY_BASE * (2 ** min(attempt, 3)))
                    continue

                logger.info("Proxy: connected to %s:%d", phone_ip, port)
                sock.settimeout(30)

                # Send HTTP request to phone
                sock.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\nConnection: keep-alive\r\n\r\n")

                # Read until end of HTTP response headers
                buf = b""
                while b"\r\n\r\n" not in buf:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    buf += chunk

                header_end = buf.find(b"\r\n\r\n") + 4
                logger.info("Proxy: phone HTTP headers (%d bytes)", header_end)

                # Yield body data that came with headers
                body = buf[header_end:]
                if body:
                    yield body

                # Reset attempt counter on successful connection
                attempt = 0

                # Stream remaining bytes — if this breaks, we reconnect
                while True:
                    chunk = sock.recv(65536)
                    if not chunk:
                        logger.warning("Proxy: connection lost to %s:%d, reconnecting...", phone_ip, port)
                        break
                    yield chunk

            except Exception as e:
                logger.error("Proxy error: %s", e)
            finally:
                if sock:
                    try:
                        sock.close()
                    except Exception:
                        pass

            # If we get here, connection was lost — reconnect
            attempt += 1
            delay = RECONNECT_DELAY_BASE * (2 ** min(attempt - 1, 3))
            logger.info("Proxy: reconnecting in %ds (attempt %d/%d)", delay, attempt, MAX_RECONNECT_ATTEMPTS)
            time.sleep(delay)

        logger.error("Proxy: gave up after %d reconnect attempts", MAX_RECONNECT_ATTEMPTS)

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
