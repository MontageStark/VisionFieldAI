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
    # Crop region for browser preview (normalized 0-1)
    crop_x: float = 0.0   # center x
    crop_y: float = 0.0   # center y
    crop_w: float = 1.0   # width (1.0 = full frame)
    crop_h: float = 1.0   # height (1.0 = full frame)


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
            gray = cv2.GaussianBlur(gray, (15, 15), 0)

            detections = []

            if self._prev_gray is not None:
                # Motion detection via frame differencing
                diff = cv2.absdiff(self._prev_gray, gray)
                # Lower threshold for better sensitivity
                thresh = cv2.threshold(diff, 15, 255, cv2.THRESH_BINARY)[1]
                thresh = cv2.dilate(thresh, None, iterations=3)

                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area < 200:  # lower threshold
                        continue
                    x, y, cw, ch = cv2.boundingRect(contour)
                    detections.append(Detection(
                        label="motion",
                        confidence=min(1.0, area / 3000),
                        x=(x + cw / 2) / w,
                        y=(y + ch / 2) / h,
                        w=cw / w,
                        h=ch / h,
                    ))

            self._prev_gray = gray
            self._frame_count += 1

            if detections:
                logger.debug("Detected %d motion regions", len(detections))

            return detections

        except ImportError:
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
            "crop_x": round(d.crop_x, 3),
            "crop_y": round(d.crop_y, 3),
            "crop_w": round(d.crop_w, 3),
            "crop_h": round(d.crop_h, 3),
        }

    def _run(self):
        """Main pipeline loop."""
        while self._running:
            try:
                self._capture_single_frame()
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
        """FIFA-style broadcast director.
        
        Finds the densest cluster of motion, creates a 16:9 crop that
        follows the action like a professional TV camera operator.
        The crop glides smoothly (gimbal-like) and changes size based
        on how concentrated the action is.
        """
        TARGET_RATIO = 16 / 9
        alpha = 0.12  # slow glide — smooth like a real camera operator

        if not detections:
            # No motion — slowly pull back to full frame
            self._decision.shot_type = "wide"
            self._decision.reasoning = "No motion — full frame"
            self._decision.confidence = 0.3
            alpha = 0.05  # very slow pullback
            target_x, target_y = 0.5, 0.5
            target_w, target_h = 1.0, 1.0
        else:
            # Find the densest cluster of motion
            target_x, target_y, target_w, target_h = self._find_best_cluster(detections)
            self._decision.confidence = min(1.0, max(d.confidence for d in detections))

        # Smooth transition (gimbal glide)
        self._decision.crop_x += (target_x - self._decision.crop_x) * alpha
        self._decision.crop_y += (target_y - self._decision.crop_y) * alpha
        self._decision.crop_w += (target_w - self._decision.crop_w) * alpha
        self._decision.crop_h += (target_h - self._decision.crop_h) * alpha

        # Enforce 16:9 ratio after smoothing
        self._enforce_16_9()

        # Zoom = inverse of crop size
        self._decision.zoom = round(1.0 / max(self._decision.crop_w, self._decision.crop_h), 2)

        # Shot type
        if self._decision.zoom < 1.3:
            self._decision.shot_type = "wide"
        elif self._decision.zoom < 2.0:
            self._decision.shot_type = "broadcast"
        else:
            self._decision.shot_type = "close"

        n = len(detections)
        self._decision.reasoning = f"{n} motion regions — {self._decision.shot_type} 16:9"
        self._decision.timestamp = time.time()

    def _find_best_cluster(self, detections: List[Detection]) -> tuple:
        """Find the densest cluster of motion and return a 16:9 crop for it.
        
        Strategy: for each detection, count how many other detections are
        within a radius. The detection with the most neighbors is the
        cluster center. The crop tightens around dense clusters.
        """
        TARGET_RATIO = 16 / 9

        if len(detections) <= 1:
            d = detections[0]
            # Single detection — tight crop around it
            crop_w = 0.45
            crop_h = crop_w / TARGET_RATIO
            return d.x, d.y, crop_w, crop_h

        # Find cluster density for each detection
        best_center = None
        best_count = 0

        for i, d in enumerate(detections):
            count = 0
            cx, cy = d.x, d.y
            for j, other in enumerate(detections):
                if i == j:
                    continue
                dist = ((other.x - cx) ** 2 + (other.y - cy) ** 2) ** 0.5
                if dist < 0.25:  # within 25% of frame
                    count += 1
            if count > best_count:
                best_count = count
                best_center = d

        if best_center is None:
            best_center = detections[0]

        # Calculate bounding box around the cluster
        cluster_dets = [best_center]
        for d in detections:
            dist = ((d.x - best_center.x) ** 2 + (d.y - best_center.y) ** 2) ** 0.5
            if dist < 0.25:
                cluster_dets.append(d)

        min_x = min(d.x - d.w / 2 for d in cluster_dets)
        max_x = max(d.x + d.w / 2 for d in cluster_dets)
        min_y = min(d.y - d.h / 2 for d in cluster_dets)
        max_y = max(d.y + d.h / 2 for d in cluster_dets)

        # Dynamic padding — less when action is concentrated
        concentration = len(cluster_dets) / max(1, len(detections))
        padding = 0.15 + (1 - concentration) * 0.15  # 15-30% based on density

        min_x = max(0, min_x - padding)
        max_x = min(1, max_x + padding)
        min_y = max(0, min_y - padding)
        max_y = min(1, max_y + padding)

        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        raw_w = max_x - min_x
        raw_h = max_y - min_y

        # Enforce 16:9
        current_ratio = raw_w / raw_h if raw_h > 0 else TARGET_RATIO
        if current_ratio > TARGET_RATIO:
            crop_w = raw_w
            crop_h = raw_w / TARGET_RATIO
        else:
            crop_h = raw_h
            crop_w = raw_h * TARGET_RATIO

        # Minimum crop — tighter when action is concentrated
        min_crop = 0.35 if concentration > 0.5 else 0.45
        crop_w = max(min_crop, min(1.0, crop_w))
        crop_h = max(min_crop / TARGET_RATIO, min(1.0, crop_h))

        return center_x, center_y, crop_w, crop_h

    def _enforce_16_9(self):
        """Enforce 16:9 aspect ratio on the current crop, clamping to frame bounds."""
        TARGET_RATIO = 16 / 9

        cx = self._decision.crop_x
        cy = self._decision.crop_y
        w = self._decision.crop_w
        h = self._decision.crop_h

        # Clamp to frame bounds first
        w = max(0.3, min(1.0, w))
        h = max(0.3 / TARGET_RATIO, min(1.0, h))

        # Enforce 16:9 — adjust the SMALLER dimension
        if w / h > TARGET_RATIO:
            # Too wide → shrink width
            w = h * TARGET_RATIO
        else:
            # Too tall → shrink height
            h = w / TARGET_RATIO

        # Final clamp (in case rounding pushed us over)
        w = min(w, 1.0)
        h = min(h, 1.0)

        # Keep center within frame
        half_w = w / 2
        half_h = h / 2
        cx = max(half_w, min(1 - half_w, cx))
        cy = max(half_h, min(1 - half_h, cy))

        self._decision.crop_w = w
        self._decision.crop_h = h
        self._decision.crop_x = cx
        self._decision.crop_y = cy
