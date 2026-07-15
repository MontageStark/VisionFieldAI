"""YOLO11 detector wrapper with GPU resource isolation."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """A single object detection result."""

    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[float, float, float, float]
    track_id: Optional[int] = None


class YOLO11Detector:
    """YOLO11 object detector with configurable GPU resources.

    Wraps ultralytics YOLO11 model with frame preprocessing and
    GPU resource isolation support.
    """

    def __init__(
        self,
        model_name: str = "yolo11n.pt",
        confidence_threshold: float = 0.5,
        device: str = "cuda",
        max_detections: int = 100,
        simulation_mode: bool = False,
        max_vram_gb: float = 2.0,
    ) -> None:
        """Initialize the YOLO11 detector.

        Args:
            model_name: YOLO model filename (e.g. yolo11n.pt)
            confidence_threshold: Minimum confidence for detections
            device: Compute device (cuda, cpu, mps)
            max_detections: Maximum detections per frame
            simulation_mode: If True, skip model loading and return empty detections
            max_vram_gb: GPU memory limit in GB (for resource isolation)
        """
        self._model_name = model_name
        self._confidence_threshold = confidence_threshold
        self._device = device
        self._max_detections = max_detections
        self._simulation_mode = simulation_mode
        self._max_vram_gb = max_vram_gb
        self._model: Any = None
        self._stride: int = 32
        self._input_size: Tuple[int, int] = (640, 640)

        if not simulation_mode:
            self._load_model()

    def _load_model(self) -> None:
        """Load the YOLO11 model from disk."""
        try:
            from ultralytics import YOLO
        except ImportError:
            logger.warning(
                "ultralytics not installed, using simulation mode"
            )
            self._simulation_mode = True
            return

        try:
            self._model = YOLO(self._model_name)
            self._model.to(self._device)

            if self._device == "cuda":
                self._apply_gpu_limits()

            logger.info(
                "YOLO11 model '%s' loaded on %s",
                self._model_name,
                self._device,
            )
        except Exception as exc:
            logger.warning(
                "Failed to load YOLO model '%s' on %s: %s",
                self._model_name,
                self._device,
                exc,
            )
            self._simulation_mode = True

    def _apply_gpu_limits(self) -> None:
        """Apply GPU memory limits for resource isolation."""
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.set_per_process_memory_fraction(
                    self._max_vram_gb / float(torch.cuda.get_device_properties(0).total_memory_gb)
                    if torch.cuda.get_device_properties(0).total_memory_gb > 0
                    else 0.5,
                    device=0,
                )
                logger.info(
                    "GPU memory limit set to %.1f GB",
                    self._max_vram_gb,
                )
        except Exception as exc:
            logger.debug("Could not apply GPU memory limits: %s", exc)

    def preprocess(self, image: np.ndarray) -> Tuple[np.ndarray, dict]:
        """Preprocess a frame for YOLO inference.

        Applies letterbox padding to maintain aspect ratio.

        Args:
            image: Input image as RGB uint8 numpy array (H, W, 3)

        Returns:
            Tuple of (preprocessed image batch, letterbox metadata)
        """
        import cv2

        h, w = image.shape[:2]
        target_h, target_w = self._input_size

        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)

        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        resized = np.array(resized, dtype=np.float32)

        padded = np.zeros((target_h, target_w, 3), dtype=np.float32)
        pad_top = (target_h - new_h) // 2
        pad_left = (target_w - new_w) // 2
        padded[pad_top : pad_top + new_h, pad_left : pad_left + new_w] = resized

        normalized = padded / 255.0

        batch = np.expand_dims(normalized, axis=0)

        meta = {
            "scale": scale,
            "pad_top": pad_top,
            "pad_left": pad_left,
            "original_shape": (h, w),
        }
        return batch, meta

    @staticmethod
    def _letterbox_resize(
        image: np.ndarray, target_size: Tuple[int, int]
    ) -> np.ndarray:
        """Resize image with letterbox padding to target size."""
        h, w = image.shape[:2]
        target_w, target_h = target_size

        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)

        import cv2

        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        return resized

    def detect(self, image: np.ndarray) -> List[Detection]:
        """Run object detection on a frame.

        Args:
            image: Input image as RGB uint8 numpy array (H, W, 3)

        Returns:
            List of Detection objects
        """
        if self._simulation_mode:
            return []

        preprocessed, meta = self.preprocess(image)

        try:
            results = self._model.predict(
                preprocessed,
                conf=self._confidence_threshold,
                max_det=self._max_detections,
                verbose=False,
                device=self._device,
            )
        except Exception as exc:
            logger.error("YOLO inference failed: %s", exc)
            return []

        if not results or len(results) == 0:
            return []

        result = results[0]
        if result.boxes is None or len(result.boxes) == 0:
            return []

        detections = []
        scale = meta.get("scale", 1.0)
        pad_top = meta.get("pad_top", 0)
        pad_left = meta.get("pad_left", 0)

        for box in result.boxes:
            conf = float(box.conf.cpu().numpy()[0])
            cls_id = int(box.cls.cpu().numpy()[0])
            xyxy = box.xyxy.cpu().numpy()[0]

            x1, y1, x2, y2 = xyxy

            x1 = (x1 - pad_left) / scale
            y1 = (y1 - pad_top) / scale
            x2 = (x2 - pad_left) / scale
            y2 = (y2 - pad_top) / scale

            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(meta["original_shape"][1], x2)
            y2 = min(meta["original_shape"][0], y2)

            cls_name = result.names.get(cls_id, str(cls_id))

            detections.append(
                Detection(
                    class_id=cls_id,
                    class_name=cls_name,
                    confidence=conf,
                    bbox=(float(x1), float(y1), float(x2), float(y2)),
                )
            )

        return detections

    @property
    def simulation_mode(self) -> bool:
        return self._simulation_mode

    @property
    def device(self) -> str:
        return self._device

    @property
    def confidence_threshold(self) -> float:
        return self._confidence_threshold

    def update_confidence(self, threshold: float) -> None:
        """Update confidence threshold at runtime."""
        self._confidence_threshold = max(0.0, min(1.0, threshold))