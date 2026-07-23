"""PipelineService — connects camera → analysis → director in a background loop."""
from __future__ import annotations

import logging
import socket
import struct
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """A single detected object."""
    label: str
    confidence: float
    x: float  # center x (0-1 normalized)
    y: float  # center y (0-1 normalized)
    w: float  # width (0-1 normalized)
    h: float  # height (0-1 normalized)


@dataclass
class TrackingState:
    """Current tracking state."""
    frame_count: int = 0
    fps: float = 0.0
    detections: List[Detection] = field(default_factory=list)
    ball_position: Optional[tuple] = None
    player_count: int = 0
    last_update: float = 0.0


@dataclass
class DirectorDecision:
    """Director's camera decision."""
    target_pan: float = 90.0
    target_tilt: float = 90.0
    zoom: float = 1.0
    shot_type: str = "wide"
    reasoning: str = ""
    confidence: float = 0.0
    timestamp: float = 0.0


class FrameAnalyzer:
    """Lightweight frame analysis — motion detection + color blobs.
    
    Replace with YOLO11 when GPU is available:
        from ultralytics import YOLO
        model = YOLO("yolo11.pt")
    """

    def __init__(self):
        self._prev_gray: Optional[np.ndarray] = None
        self._frame_count = 0

    def analyze(self, jpeg_bytes: bytes) -> List[Detection]:
        """Analyze a JPEG frame and return detections."""
        try:
            import cv2
            # Decode JPEG to numpy array
            arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is None:
                return []

            h, w = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            detections = []

            if self._prev_gray is not None:
                # Motion detection via frame differencing
                diff = cv2.absdiff(self._prev_gray, gray)
                thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
                thresh = cv2.dilate(thresh, None, iterations=2)

                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area < 500:  # skip small noise
                        continue
                    x, y, cw, ch = cv2.boundingRect(contour)
                    detections.append(Detection(
                        label="motion",
                        confidence=min(1.0, area / 5000),
                        x=(x + cw / 2) / w,
                        y=(y + ch / 2) / h,
                        w=cw / w,
                        h=ch / h,
                    ))

            self._prev_gray = gray
            self._frame_count += 1
            return detections

        except ImportError:
            # cv2 not available — return empty
            return []
        except Exception as e:
            logger.debug("Frame analysis error: %s", e)
            return []


class PipelineService:
    """Runs the full camera → analysis → director pipeline in a background thread.
    
    Captures frames from the phone's MJPEG stream, analyzes them,
    and publishes results via the event bus.
    """

    def __init__(
        self,
        phone_ip: str = "192.168.0.187",
        port: int = 8080,
        event_bus: Any = None,
    ):
        self.phone_ip = phone_ip
        self.port = port
        self.event_bus = event_bus
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._analyzer = FrameAnalyzer()
        self._tracking = TrackingState()
        self._decision = DirectorDecision()
        self._last_frame_time = 0.0
        self._frame_times: List[float] = []

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Pipeline started: phone=%s:%d", self.phone_ip, self.port)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Pipeline stopped")

    @property
    def is_running(self):
        return self._running

    def get_tracking(self) -> dict:
        t = self._tracking
        return {
            "frame_count": t.frame_count,
            "fps": round(t.fps, 1),
            "player_count": t.player_count,
            "ball_position": t.ball_position,
            "detection_count": len(t.detections),
            "last_update": t.last_update,
        }

    def get_decision(self) -> dict:
        d = self._decision
        return {
            "target_pan": round(d.target_pan, 1),
            "target_tilt": round(d.target_tilt, 1),
            "zoom": round(d.zoom, 2),
            "shot_type": d.shot_type,
            "reasoning": d.reasoning,
            "confidence": round(d.confidence, 2),
            "timestamp": d.timestamp,
        }

    def _run(self):
        """Main pipeline loop."""
        while self._running:
            try:
                self._capture_and_analyze()
            except Exception as e:
                logger.error("Pipeline error: %s", e)
                time.sleep(2)

    def _capture_and_analyze(self):
        """Capture one frame from phone and analyze it."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.phone_ip, self.port))
            sock.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n")

            # Read HTTP headers
            buf = b""
            while b"\r\n\r\n" not in buf:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buf += chunk

            header_end = buf.find(b"\r\n\r\n") + 4
            sock.close()

            # We got the headers but closed the connection — can't stream
            # Instead, connect fresh for each frame (simpler, works for now)
            self._capture_single_frame()

        except Exception as e:
            logger.debug("Capture error: %s", e)
            time.sleep(1)

    def _capture_single_frame(self):
        """Capture a single JPEG frame from the phone's MJPEG stream."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.phone_ip, self.port))
            sock.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n")

            # Read response — phone sends multipart MJPEG
            buf = b""
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                buf += chunk
                # Look for a complete JPEG frame between boundary markers
                # MJPEG format: --frame\r\nContent-Type: image/jpeg\r\nContent-Length: N\r\n\r\n<JPEG>\r\n
                if b"\xff\xd9" in buf:
                    break
            sock.close()

            if len(buf) < 100:
                return

            # Find JPEG data — look for Content-Length to extract exact frame
            header_end = buf.find(b"\r\n\r\n")
            if header_end < 0:
                return
            body = buf[header_end + 4:]

            # Try to parse Content-Length
            cl_marker = b"Content-Length:"
            cl_start = body.find(cl_marker)
            if cl_start >= 0:
                cl_end = body.find(b"\r\n", cl_start)
                if cl_end > cl_start:
                    try:
                        content_length = int(body[cl_start + len(cl_marker):cl_end].strip())
                        # Find the JPEG data after the second \r\n\r\n
                        data_start = body.find(b"\r\n\r\n", cl_start)
                        if data_start >= 0:
                            data_start += 4
                            jpeg_bytes = body[data_start:data_start + content_length]
                            if len(jpeg_bytes) > 500:
                                self._process_frame(jpeg_bytes)
                                return
                    except ValueError:
                        pass

            # Fallback: find JPEG start/end markers
            start = body.find(b'\xff\xd8')
            end = body.find(b'\xff\xd9', start)
            if start >= 0 and end >= 0:
                jpeg_bytes = body[start:end + 2]
                if len(jpeg_bytes) > 500:
                    self._process_frame(jpeg_bytes)

        except Exception as e:
            logger.debug("Frame capture error: %s", e)
            time.sleep(1)

    def _process_frame(self, jpeg_bytes: bytes):
        """Process a captured JPEG frame."""
        now = time.time()
        self._frame_times.append(now)
        self._frame_times = [t for t in self._frame_times if now - t < 2]

        detections = self._analyzer.analyze(jpeg_bytes)

        # Update tracking state
        self._tracking.frame_count += 1
        self._tracking.fps = len(self._frame_times)
        self._tracking.detections = detections
        self._tracking.player_count = len([d for d in detections if d.label == "motion"])
        self._tracking.last_update = now

        # Update director decision based on detections
        self._update_director(detections)

        # Publish events
        if self.event_bus:
            try:
                from app.core.events import EventType, Event
                self.event_bus.publish(Event(
                    type=EventType.TRACKING_UPDATED,
                    data=self.get_tracking(),
                ))
            except Exception:
                pass

        # Throttle — don't hammer the phone
        elapsed = time.time() - self._last_frame_time
        if elapsed < 0.1:
            time.sleep(0.1 - elapsed)
        self._last_frame_time = time.time()

    def _update_director(self, detections: List[Detection]):
        """Update director decision based on detections."""
        if not detections:
            self._decision.shot_type = "wide"
            self._decision.reasoning = "No motion detected — wide shot"
            self._decision.confidence = 0.5
            self._decision.target_pan = 90.0
            self._decision.target_tilt = 45.0
            return

        # Find the most significant detection (largest area)
        best = max(detections, key=lambda d: d.w * d.h)

        # Pan toward the action (0-1 → 0-180 degrees)
        target_pan = best.x * 180.0
        target_tilt = best.y * 90.0  # tilt range is smaller

        # Smooth transition
        alpha = 0.3
        self._decision.target_pan = self._decision.target_pan * (1 - alpha) + target_pan * alpha
        self._decision.target_tilt = self._decision.target_tilt * (1 - alpha) + target_tilt * alpha
        self._decision.target_pan = max(0, min(180, self._decision.target_pan))
        self._decision.target_tilt = max(0, min(90, self._decision.target_tilt))

        # Shot type based on detection density
        if len(detections) > 5:
            self._decision.shot_type = "wide"
            self._decision.zoom = 1.0
            self._decision.reasoning = f"{len(detections)} motion regions — wide shot"
        elif len(detections) > 2:
            self._decision.shot_type = "broadcast"
            self._decision.zoom = 1.5
            self._decision.reasoning = f"{len(detections)} motion regions — broadcast shot"
        else:
            self._decision.shot_type = "close"
            self._decision.zoom = 2.0
            self._decision.reasoning = f"Focused on motion — close shot"

        self._decision.confidence = min(1.0, best.confidence)
        self._decision.timestamp = time.time()
