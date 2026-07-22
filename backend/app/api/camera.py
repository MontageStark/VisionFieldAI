"""Camera API endpoints."""
from __future__ import annotations

import io
import logging
import urllib.request
from typing import Iterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.deps import get_camera_service
from app.config.loader import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/camera", tags=["camera"])


@router.get("/status")
def camera_status() -> dict:
    svc = get_camera_service()
    return svc.status()


@router.post("/start")
def camera_start() -> dict:
    svc = get_camera_service()
    return svc.start()


@router.post("/stop")
def camera_stop() -> dict:
    svc = get_camera_service()
    return svc.stop()


@router.get("/stream")
def camera_stream():
    """Proxy MJPEG stream from phone to browser.

    The phone's MJPEG server sends multipart/x-mixed-replace frames.
    This endpoint proxies them to the frontend as a standard MJPEG stream
    that the browser can render in an <img> tag.
    """
    settings = get_settings()
    phone_url = settings.camera.http_url

    def mjpeg_generator() -> Iterator[bytes]:
        boundary = b"--frame\r\n"
        while True:
            try:
                req = urllib.request.Request(phone_url)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    content_type = resp.headers.get("Content-Type", "")
                    if "multipart" in content_type:
                        # Phone sends proper multipart MJPEG — relay as-is
                        while True:
                            chunk = resp.read(4096)
                            if not chunk:
                                break
                            yield chunk
                    else:
                        # Phone sends raw JPEG stream (no multipart)
                        while True:
                            jpeg_data = resp.read(65536)
                            if not jpeg_data:
                                break
                            yield (
                                boundary
                                + b"Content-Type: image/jpeg\r\n"
                                + b"Content-Length: " + str(len(jpeg_data)).encode() + b"\r\n\r\n"
                                + jpeg_data
                                + b"\r\n"
                            )
            except Exception as exc:
                logger.warning("MJPEG proxy error, retrying in 2s: %s", exc)
                import time
                time.sleep(2)

    return StreamingResponse(
        mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
