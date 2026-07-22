"""Streaming API endpoints."""
from __future__ import annotations

import logging
import socket
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
        sock.connect((host, port))
        return sock
    except Exception:
        return None


@router.get("/proxy")
def stream_proxy(phone_ip: str = "192.168.0.176", port: int = 8080) -> StreamingResponse:
    def frame_generator() -> Generator[bytes, None, None]:
        sock = None

        logger.info("Proxy: trying direct %s:%d", phone_ip, port)
        sock = _try_connect(phone_ip, port, timeout=3)
        if sock:
            logger.info("Proxy: connected to %s:%d directly", phone_ip, port)
        else:
            logger.info("Proxy: direct failed, trying localhost:%d (ADB forward)", port)
            sock = _try_connect("127.0.0.1", port, timeout=3)
            if sock:
                logger.info("Proxy: connected via ADB forward")
            else:
                logger.error("Proxy: cannot reach phone at %s:%d or localhost:%d", phone_ip, port, port)
                return

        try:
            sock.settimeout(30)

            # Send a proper HTTP request to the phone's StreamServer.
            # This is CRITICAL: without sending an HTTP request, ADB forward
            # wraps the response in chunked encoding. With a request, we get
            # plain HTTP that can be streamed directly.
            sock.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\nConnection: keep-alive\r\n\r\n")

            # Read until we find the end of HTTP response headers (\r\n\r\n)
            buf = b""
            while b"\r\n\r\n" not in buf:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buf += chunk

            header_end = buf.find(b"\r\n\r\n") + 4
            logger.info("Proxy: phone HTTP headers (%d bytes)", header_end)

            # Yield any body data that came with the headers
            body = buf[header_end:]
            if body:
                yield body

            # Stream remaining bytes directly from socket
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                yield chunk

        except Exception as e:
            logger.error("Proxy error: %s", e)
        finally:
            sock.close()
            logger.info("Proxy connection closed")

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
