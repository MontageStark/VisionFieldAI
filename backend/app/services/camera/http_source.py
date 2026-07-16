"""HTTP camera source for receiving phone video streams."""
from __future__ import annotations

import logging
from typing import Optional, Tuple

import cv2
import numpy as np

from .video_source import VideoSource

logger = logging.getLogger(__name__)


class HttpCameraSource(VideoSource):
    """Receives video stream from phone app via HTTP/WebRTC."""
    
    def __init__(self, url: str, protocol: str = "auto"):
        self.url = url
        self.protocol = protocol
        self.cap: Optional[cv2.VideoCapture] = None
        self._connected = False
        self._fps: float = 0.0
        self._resolution: Tuple[int, int] = (0, 0)
    
    def open(self) -> bool:
        """Connect to phone stream using best available protocol."""
        if self.protocol == "auto":
            return self._auto_connect()
        else:
            return self._try_connect()
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read next frame from stream."""
        if not self.cap or not self._connected:
            return False, None
        
        ret, frame = self.cap.read()
        if not ret:
            self._connected = False
            return False, None
        
        return True, frame
    
    def release(self) -> None:
        """Disconnect and cleanup."""
        if self.cap:
            self.cap.release()
            self.cap = None
        self._connected = False
    
    def is_opened(self) -> bool:
        """Return True if the source is currently open."""
        return self._connected and self.cap is not None and self.cap.isOpened()
    
    @property
    def fps(self) -> float:
        """Reported frames per second."""
        if self.cap and self._connected:
            return self.cap.get(cv2.CAP_PROP_FPS)
        return self._fps
    
    @property
    def resolution(self) -> Tuple[int, int]:
        """Reported (width, height) of the source."""
        if self.cap and self._connected:
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return (width, height)
        return self._resolution
    
    def _auto_connect(self) -> bool:
        """Try protocols in order: MJPEG > H.264 > WebRTC."""
        for protocol in ["mjpeg", "h264", "webrtc"]:
            self.protocol = protocol
            if self._try_connect():
                self._connected = True
                logger.info(f"Connected using {protocol}")
                return True
        
        logger.warning(f"Failed to connect to {self.url}")
        return False
    
    def _try_connect(self) -> bool:
        """Attempt connection with current protocol."""
        try:
            if self.protocol in ("mjpeg", "h264"):
                self.cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
                if self.cap.isOpened():
                    self._connected = True
                    return True
                return False
            elif self.protocol == "webrtc":
                # WebRTC connection would be implemented here
                # For now, return False
                logger.warning("WebRTC not yet implemented")
                return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
        
        return False
