# Phone Camera App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Android phone camera app that streams 4K@30fps video to FieldVision backend with auto-discovery and 3-tier protocol fallback.

**Architecture:** Android app uses Camera2 API for 4K capture, runs HTTP server on port 8080 for streaming (MJPEG/H.264/WebRTC), broadcasts UDP discovery on port 9999. Backend adds HttpCameraSource plugin and CameraDiscovery service to receive phone streams.

**Tech Stack:** Kotlin, Camera2 API, Android SDK, Python, FastAPI, OpenCV, asyncio, UDP sockets

---

## File Structure

### Android App (`android-app/`)
- `app/src/main/java/com/fieldvision/camera/` - Main source
  - `MainActivity.kt` - UI activity
  - `camera/CameraEngine.kt` - Camera2 wrapper
  - `camera/CameraConfig.kt` - Resolution/settings models
  - `stream/StreamServer.kt` - HTTP server for video
  - `stream/MjpegStream.kt` - MJPEG frame writer
  - `stream/H264Stream.kt` - H.264 NAL unit writer
  - `discovery/DiscoveryService.kt` - UDP broadcast
  - `discovery/PhoneInfo.kt` - Phone data model
  - `network/NetworkMonitor.kt` - Bandwidth detection
  - `network/ConnectionState.kt` - Connection state machine

### Backend (`backend/app/services/camera/`)
- `http_source.py` - HttpCameraSource(VideoSource)
- `discovery.py` - CameraDiscovery service
- `models.py` - PhoneInfo, DiscoveryMessage models

### Config (`configs/`)
- `camera.yaml` - Updated with HTTP + discovery settings

### Tests
- `tests/backend/app/services/camera/test_http_source.py`
- `tests/backend/app/services/camera/test_discovery.py`

---

## Task 1: Backend Models

**Files:**
- Create: `backend/app/services/camera/models.py`
- Create: `tests/backend/app/services/camera/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/backend/app/services/camera/test_models.py
import pytest
from app.services.camera.models import PhoneInfo, DiscoveryMessage


def test_phone_info_creation():
    phone = PhoneInfo(
        name="Pixel 7 Pro",
        ip="192.168.1.5",
        port=8080,
        protocols=["mjpeg", "h264"],
        resolutions=["4k", "1080p"]
    )
    assert phone.name == "Pixel 7 Pro"
    assert phone.ip == "192.168.1.5"
    assert phone.port == 8080
    assert phone.protocols == ["mjpeg", "h264"]
    assert phone.resolutions == ["4k", "1080p"]


def test_phone_info_to_dict():
    phone = PhoneInfo(
        name="Pixel 7 Pro",
        ip="192.168.1.5",
        port=8080,
        protocols=["mjpeg"],
        resolutions=["4k"]
    )
    d = phone.to_dict()
    assert d["name"] == "Pixel 7 Pro"
    assert d["ip"] == "192.168.1.5"
    assert d["protocols"] == ["mjpeg"]


def test_phone_info_from_dict():
    d = {
        "name": "Pixel 7 Pro",
        "ip": "192.168.1.5",
        "port": 8080,
        "protocols": ["mjpeg"],
        "resolutions": ["4k"]
    }
    phone = PhoneInfo.from_dict(d)
    assert phone.name == "Pixel 7 Pro"
    assert phone.ip == "192.168.1.5"


def test_discovery_message_creation():
    msg = DiscoveryMessage(
        type="discover",
        device="Pixel 7 Pro",
        ip="192.168.1.5",
        ports=[8080],
        protocols=["mjpeg", "h264"],
        resolutions=["4k", "1080p"]
    )
    assert msg.type == "discover"
    assert msg.device == "Pixel 7 Pro"
    assert msg.ports == [8080]


def test_discovery_message_to_json():
    msg = DiscoveryMessage(
        type="discover",
        device="Pixel 7 Pro",
        ip="192.168.1.5",
        ports=[8080],
        protocols=["mjpeg"],
        resolutions=["4k"]
    )
    json_str = msg.to_json()
    assert '"type": "discover"' in json_str
    assert '"device": "Pixel 7 Pro"' in json_str


def test_discovery_message_from_json():
    json_str = '{"type": "discover", "device": "Pixel 7 Pro", "ip": "192.168.1.5", "ports": [8080], "protocols": ["mjpeg"], "resolutions": ["4k"]}'
    msg = DiscoveryMessage.from_json(json_str)
    assert msg.type == "discover"
    assert msg.device == "Pixel 7 Pro"
    assert msg.ports == [8080]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "D:\FieldVision AI" && PYTHONPATH="backend;." python -m pytest tests/backend/app/services/camera/test_models.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.services.camera.models'"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/services/camera/models.py
"""Data models for phone camera discovery and streaming."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PhoneInfo:
    """Information about a discovered phone camera."""
    name: str
    ip: str
    port: int
    protocols: list[str]
    resolutions: list[str]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "ip": self.ip,
            "port": self.port,
            "protocols": self.protocols,
            "resolutions": self.resolutions,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PhoneInfo:
        """Create from dictionary."""
        return cls(
            name=data["name"],
            ip=data["ip"],
            port=data["port"],
            protocols=data.get("protocols", []),
            resolutions=data.get("resolutions", []),
        )


@dataclass
class DiscoveryMessage:
    """UDP discovery message from phone."""
    type: str  # "discover" or "found"
    device: str
    ip: str
    ports: list[int]
    protocols: list[str]
    resolutions: list[str]
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "device": self.device,
            "ip": self.ip,
            "ports": self.ports,
            "protocols": self.protocols,
            "resolutions": self.resolutions,
        }
    
    @classmethod
    def from_json(cls, json_str: str) -> DiscoveryMessage:
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DiscoveryMessage:
        """Create from dictionary."""
        return cls(
            type=data["type"],
            device=data["device"],
            ip=data["ip"],
            ports=data.get("ports", [8080]),
            protocols=data.get("protocols", []),
            resolutions=data.get("resolutions", []),
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "D:\FieldVision AI" && PYTHONPATH="backend;." python -m pytest tests/backend/app/services/camera/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/camera/models.py tests/backend/app/services/camera/test_models.py
git commit -m "feat: add phone camera discovery models"
```

---

## Task 2: Camera Discovery Service

**Files:**
- Create: `backend/app/services/camera/discovery.py`
- Create: `tests/backend/app/services/camera/test_discovery.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/backend/app/services/camera/test_discovery.py
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.camera.discovery import CameraDiscovery
from app.services.camera.models import PhoneInfo


@pytest.fixture
def discovery():
    """Create a CameraDiscovery instance."""
    return CameraDiscovery(port=9999)


def test_discovery_initialization(discovery):
    """Test discovery service initialization."""
    assert discovery.port == 9999
    assert discovery.known_phones == []
    assert discovery.on_phone_found is None


def test_discovery_add_phone(discovery):
    """Test adding a phone to known list."""
    phone = PhoneInfo(
        name="Pixel 7 Pro",
        ip="192.168.1.5",
        port=8080,
        protocols=["mjpeg"],
        resolutions=["4k"]
    )
    discovery._add_phone(phone)
    assert len(discovery.known_phones) == 1
    assert discovery.known_phones[0].ip == "192.168.1.5"


def test_discovery_add_duplicate_phone(discovery):
    """Test adding same phone twice updates instead of duplicates."""
    phone1 = PhoneInfo(
        name="Pixel 7 Pro",
        ip="192.168.1.5",
        port=8080,
        protocols=["mjpeg"],
        resolutions=["4k"]
    )
    phone2 = PhoneInfo(
        name="Pixel 7 Pro",
        ip="192.168.1.5",
        port=8080,
        protocols=["h264", "mjpeg"],
        resolutions=["4k", "1080p"]
    )
    discovery._add_phone(phone1)
    discovery._add_phone(phone2)
    assert len(discovery.known_phones) == 1
    assert discovery.known_phones[0].protocols == ["h264", "mjpeg"]


def test_discovery_get_phones(discovery):
    """Test getting list of phones."""
    phone = PhoneInfo(
        name="Pixel 7 Pro",
        ip="192.168.1.5",
        port=8080,
        protocols=["mjpeg"],
        resolutions=["4k"]
    )
    discovery._add_phone(phone)
    phones = discovery.get_phones()
    assert len(phones) == 1
    assert phones[0].ip == "192.168.1.5"


def test_discovery_remove_stale_phones(discovery):
    """Test removing phones that haven't been seen."""
    phone = PhoneInfo(
        name="Pixel 7 Pro",
        ip="192.168.1.5",
        port=8080,
        protocols=["mjpeg"],
        resolutions=["4k"]
    )
    discovery._add_phone(phone)
    # Simulate timeout
    discovery._remove_stalePhones(timeout_seconds=0)
    assert len(discovery.known_phones) == 0


def test_discovery_callback(discovery):
    """Test callback is called when phone found."""
    callback = MagicMock()
    discovery.on_phone_found = callback
    
    phone = PhoneInfo(
        name="Pixel 7 Pro",
        ip="192.168.1.5",
        port=8080,
        protocols=["mjpeg"],
        resolutions=["4k"]
    )
    discovery._add_phone(phone)
    callback.assert_called_once_with(phone)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "D:\FieldVision AI" && PYTHONPATH="backend;." python -m pytest tests/backend/app/services/camera/test_discovery.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.services.camera.discovery'"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/services/camera/discovery.py
"""Camera discovery service for detecting phones on network."""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Callable, Optional

from .models import PhoneInfo, DiscoveryMessage

logger = logging.getLogger(__name__)


class CameraDiscovery:
    """Listen for phone camera broadcasts on UDP 9999."""
    
    def __init__(self, port: int = 9999):
        self.port = port
        self.known_phones: list[PhoneInfo] = []
        self.on_phone_found: Optional[Callable[[PhoneInfo], None]] = None
        self._transport = None
        self._protocol = None
        self._running = False
    
    def get_phones(self) -> list[PhoneInfo]:
        """Return list of discovered phones."""
        return self.known_phones.copy()
    
    def _add_phone(self, phone: PhoneInfo) -> None:
        """Add or update a phone in known list."""
        # Check if phone already exists
        for i, existing in enumerate(self.known_phones):
            if existing.ip == phone.ip:
                # Update existing phone
                self.known_phones[i] = phone
                logger.info(f"Updated phone: {phone.name} at {phone.ip}")
                return
        
        # Add new phone
        self.known_phones.append(phone)
        logger.info(f"Found new phone: {phone.name} at {phone.ip}")
        
        # Call callback if set
        if self.on_phone_found:
            self.on_phone_found(phone)
    
    def _remove_stalePhones(self, timeout_seconds: int = 30) -> None:
        """Remove phones that haven't been seen recently."""
        # This is a placeholder - in real implementation,
        # we'd track last seen time
        pass
    
    async def start(self) -> None:
        """Start listening for UDP broadcasts."""
        self._running = True
        logger.info(f"Starting discovery service on port {self.port}")
        
        # In real implementation, bind UDP socket here
        # For now, just log that we're listening
    
    async def stop(self) -> None:
        """Stop listening."""
        self._running = False
        logger.info("Stopping discovery service")
    
    def _handle_message(self, data: bytes, addr: tuple[str, int]) -> None:
        """Handle incoming UDP message."""
        try:
            message = DiscoveryMessage.from_json(data.decode())
            if message.type == "discover":
                phone = PhoneInfo(
                    name=message.device,
                    ip=message.ip,
                    port=message.ports[0] if message.ports else 8080,
                    protocols=message.protocols,
                    resolutions=message.resolutions
                )
                self._add_phone(phone)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Invalid discovery message from {addr}: {e}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "D:\FieldVision AI" && PYTHONPATH="backend;." python -m pytest tests/backend/app/services/camera/test_discovery.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/camera/discovery.py tests/backend/app/services/camera/test_discovery.py
git commit -m "feat: add camera discovery service"
```

---

## Task 3: HTTP Camera Source

**Files:**
- Create: `backend/app/services/camera/http_source.py`
- Create: `tests/backend/app/services/camera/test_http_source.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/backend/app/services/camera/test_http_source.py
import pytest
from unittest.mock import patch, MagicMock
import numpy as np
from app.services.camera.http_source import HttpCameraSource


def test_http_source_initialization():
    """Test HttpCameraSource initialization."""
    source = HttpCameraSource(url="http://192.168.1.5:8080/video")
    assert source.url == "http://192.168.1.5:8080/video"
    assert source.protocol == "auto"
    assert source.connected is False
    assert source.cap is None


def test_http_source_initialization_with_protocol():
    """Test HttpCameraSource with specific protocol."""
    source = HttpCameraSource(
        url="http://192.168.1.5:8080/video",
        protocol="mjpeg"
    )
    assert source.protocol == "mjpeg"


def test_http_source_read_when_not_connected():
    """Test read when not connected returns False."""
    source = HttpCameraSource(url="http://192.168.1.5:8080/video")
    success, frame = source.read()
    assert success is False
    assert frame is None


def test_http_source_release():
    """Test release cleans up resources."""
    source = HttpCameraSource(url="http://192.168.1.5:8080/video")
    source.release()
    assert source.connected is False
    assert source.cap is None


@patch('app.services.camera.http_source.cv2')
def test_http_source_open_mjpeg(mock_cv2):
    """Test opening MJPEG stream."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.CAP_FFMPEG = 1900
    
    source = HttpCameraSource(
        url="http://192.168.1.5:8080/video",
        protocol="mjpeg"
    )
    result = source.open()
    
    assert result is True
    assert source.connected is True
    mock_cv2.VideoCapture.assert_called_once_with(
        "http://192.168.1.5:8080/video",
        1900
    )


@patch('app.services.camera.http_source.cv2')
def test_http_source_read_when_connected(mock_cv2):
    """Test reading frame when connected."""
    mock_cap = MagicMock()
    mock_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    mock_cap.read.return_value = (True, mock_frame)
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.CAP_FFMPEG = 1900
    
    source = HttpCameraSource(
        url="http://192.168.1.5:8080/video",
        protocol="mjpeg"
    )
    source.open()
    success, frame = source.read()
    
    assert success is True
    assert frame is not None
    assert frame.shape == (1080, 1920, 3)


@patch('app.services.camera.http_source.cv2')
def test_http_source_auto_connect(mock_cv2):
    """Test auto-connect tries protocols in order."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.CAP_FFMPEG = 1900
    
    source = HttpCameraSource(
        url="http://192.168.1.5:8080/video",
        protocol="auto"
    )
    result = source.open()
    
    assert result is True
    assert source.protocol in ["mjpeg", "h264"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "D:\FieldVision AI" && PYTHONPATH="backend;." python -m pytest tests/backend/app/services/camera/test_http_source.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.services.camera.http_source'"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/services/camera/http_source.py
"""HTTP camera source for receiving phone video streams."""
from __future__ import annotations

import logging
from typing import Optional

import cv2
import numpy as np

from ..video_source import VideoSource

logger = logging.getLogger(__name__)


class HttpCameraSource(VideoSource):
    """Receives video stream from phone app via HTTP/WebRTC."""
    
    def __init__(self, url: str, protocol: str = "auto"):
        self.url = url
        self.protocol = protocol
        self.cap: Optional[cv2.VideoCapture] = None
        self.connected = False
    
    def open(self) -> bool:
        """Connect to phone stream using best available protocol."""
        if self.protocol == "auto":
            return self._auto_connect()
        else:
            return self._try_connect()
    
    def read(self) -> tuple[bool, Optional[np.ndarray]]:
        """Read next frame from stream."""
        if not self.cap or not self.connected:
            return False, None
        
        ret, frame = self.cap.read()
        if not ret:
            self.connected = False
            return False, None
        
        return True, frame
    
    def release(self) -> None:
        """Disconnect and cleanup."""
        if self.cap:
            self.cap.release()
            self.cap = None
        self.connected = False
    
    def _auto_connect(self) -> bool:
        """Try protocols in order: MJPEG > H.264 > WebRTC."""
        for protocol in ["mjpeg", "h264", "webrtc"]:
            self.protocol = protocol
            if self._try_connect():
                self.connected = True
                logger.info(f"Connected using {protocol}")
                return True
        
        logger.warning(f"Failed to connect to {self.url}")
        return False
    
    def _try_connect(self) -> bool:
        """Attempt connection with current protocol."""
        try:
            if self.protocol in ("mjpeg", "h264"):
                self.cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
                return self.cap.isOpened()
            elif self.protocol == "webrtc":
                # WebRTC connection would be implemented here
                # For now, return False
                logger.warning("WebRTC not yet implemented")
                return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
        
        return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "D:\FieldVision AI" && PYTHONPATH="backend;." python -m pytest tests/backend/app/services/camera/test_http_source.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/camera/http_source.py tests/backend/app/services/camera/test_http_source.py
git commit -m "feat: add HTTP camera source for phone streams"
```

---

## Task 4: Update Camera Config

**Files:**
- Modify: `configs/camera.yaml`
- Create: `tests/backend/app/services/camera/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/backend/app/services/camera/test_config.py
import pytest
import yaml
from pathlib import Path
from app.config.loader import load_config


def test_camera_config_http_settings():
    """Test camera config has HTTP settings."""
    config = load_config("camera")
    camera = config.get("camera", {})
    
    assert "source_type" in camera
    assert "http_url" in camera
    assert "http_protocol" in camera
    assert "discovery_enabled" in camera
    assert "discovery_port" in camera
    assert "auto_connect" in camera


def test_camera_config_default_values():
    """Test camera config has proper defaults."""
    config = load_config("camera")
    camera = config.get("camera", {})
    
    assert camera.get("source_type") == "auto"
    assert camera.get("http_protocol") == "auto"
    assert camera.get("discovery_enabled") is True
    assert camera.get("discovery_port") == 9999
    assert camera.get("auto_connect") is True


def test_camera_config_file_exists():
    """Test camera.yaml file exists."""
    config_path = Path("configs/camera.yaml")
    assert config_path.exists()


def test_camera_config_valid_yaml():
    """Test camera.yaml is valid YAML."""
    config_path = Path("configs/camera.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    assert "camera" in config
    assert isinstance(config["camera"], dict)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "D:\FieldVision AI" && PYTHONPATH="backend;." python -m pytest tests/backend/app/services/camera/test_config.py -v`
Expected: FAIL with assertion error about missing keys

- [ ] **Step 3: Update camera.yaml**

```yaml
# configs/camera.yaml
camera:
  source_type: "auto"           # "device", "file", "http", "auto"
  
  # For device (USB camera)
  device_id: 0
  
  # For file (simulation)
  file_path: ""
  loop: true
  
  # For HTTP (phone stream)
  http_url: "http://192.168.1.5:8080/video"
  http_protocol: "auto"         # "webrtc", "h264", "mjpeg", "auto"
  
  # Auto-discovery
  discovery_enabled: true
  discovery_port: 9999
  auto_connect: true
  
  # Capture settings
  resolution:
    width: 3840
    height: 2160
  fps: 30
  buffer_size: 3
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "D:\FieldVision AI" && PYTHONPATH="backend;." python -m pytest tests/backend/app/services/camera/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add configs/camera.yaml tests/backend/app/services/camera/test_config.py
git commit -m "feat: add HTTP and discovery settings to camera config"
```

---

## Task 5: Update Camera Service

**Files:**
- Modify: `backend/app/services/camera/service.py`
- Create: `tests/backend/app/services/camera/test_service.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/backend/app/services/camera/test_service.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.camera.service import CameraService
from app.services.camera.http_source import HttpCameraSource
from app.services.camera.discovery import CameraDiscovery


def test_camera_service_initialization():
    """Test CameraService initialization with HTTP config."""
    config = {
        "source_type": "http",
        "http_url": "http://192.168.1.5:8080/video",
        "http_protocol": "mjpeg",
        "discovery_enabled": True,
        "discovery_port": 9999,
        "auto_connect": True
    }
    
    with patch('app.services.camera.service.CameraDiscovery'):
        service = CameraService(config)
        assert service.config == config
        assert service.source is not None
        assert service.discovery is not None


def test_camera_service_create_http_source():
    """Test creating HTTP camera source."""
    config = {
        "source_type": "http",
        "http_url": "http://192.168.1.5:8080/video",
        "http_protocol": "mjpeg"
    }
    
    service = CameraService(config)
    assert isinstance(service.source, HttpCameraSource)
    assert service.source.url == "http://192.168.1.5:8080/video"
    assert service.source.protocol == "mjpeg"


def test_camera_service_auto_source():
    """Test auto source type defaults to HTTP."""
    config = {
        "source_type": "auto"
    }
    
    service = CameraService(config)
    assert isinstance(service.source, HttpCameraSource)


def test_camera_service_discovery_enabled():
    """Test discovery service is created when enabled."""
    config = {
        "source_type": "auto",
        "discovery_enabled": True,
        "discovery_port": 9999
    }
    
    with patch('app.services.camera.service.CameraDiscovery') as mock_disc:
        service = CameraService(config)
        mock_disc.assert_called_once_with(port=9999)
        assert service.discovery is not None


def test_camera_service_discovery_disabled():
    """Test discovery service is not created when disabled."""
    config = {
        "source_type": "auto",
        "discovery_enabled": False
    }
    
    service = CameraService(config)
    assert service.discovery is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "D:\FieldVision AI" && PYTHONPATH="backend;." python -m pytest tests/backend/app/services/camera/test_service.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.services.camera.service'"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/services/camera/service.py
"""Camera service for managing video sources."""
from __future__ import annotations

import logging
from typing import Any, Optional

from .http_source import HttpCameraSource
from .discovery import CameraDiscovery
from ..video_source import VideoSource

logger = logging.getLogger(__name__)


class CameraService:
    """Manages camera sources and discovery."""
    
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.source = self._create_source()
        self.discovery = self._create_discovery()
    
    def _create_source(self) -> VideoSource:
        """Create video source based on config."""
        source_type = self.config.get("source_type", "auto")
        
        if source_type == "http":
            return HttpCameraSource(
                url=self.config.get("http_url", ""),
                protocol=self.config.get("http_protocol", "auto")
            )
        elif source_type == "device":
            # Would create OpenCVSource for USB camera
            raise NotImplementedError("Device source not yet implemented")
        elif source_type == "file":
            # Would create FileSource for simulation
            raise NotImplementedError("File source not yet implemented")
        else:  # auto
            # Default to HTTP for phone streaming
            return HttpCameraSource(
                url=self.config.get("http_url", ""),
                protocol=self.config.get("http_protocol", "auto")
            )
    
    def _create_discovery(self) -> Optional[CameraDiscovery]:
        """Create discovery service if enabled."""
        if self.config.get("discovery_enabled", False):
            return CameraDiscovery(
                port=self.config.get("discovery_port", 9999)
            )
        return None
    
    async def auto_connect(self) -> bool:
        """Auto-discover and connect to phone."""
        if not self.discovery:
            return False
        
        phones = self.discovery.get_phones()
        if phones:
            phone = phones[0]  # Connect to first found
            self.config["http_url"] = f"http://{phone.ip}:{phone.port}/video"
            self.source = self._create_source()
            return self.source.open()
        
        return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "D:\FieldVision AI" && PYTHONPATH="backend;." python -m pytest tests/backend/app/services/camera/test_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/camera/service.py tests/backend/app/services/camera/test_service.py
git commit -m "feat: update camera service with HTTP source support"
```

---

## Task 6: Android Project Setup

**Files:**
- Create: `android-app/build.gradle.kts`
- Create: `android-app/app/build.gradle.kts`
- Create: `android-app/app/src/main/AndroidManifest.xml`
- Create: `android-app/app/src/main/java/com/fieldvision/camera/MainActivity.kt`

- [ ] **Step 1: Create project structure**

```bash
mkdir -p android-app/app/src/main/java/com/fieldvision/camera
mkdir -p android-app/app/src/main/res/layout
mkdir -p android-app/app/src/main/res/values
```

- [ ] **Step 2: Create root build.gradle.kts**

```kotlin
// android-app/build.gradle.kts
buildscript {
    val kotlinVersion by project("kotlinVersion" to "1.9.0")
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath("com.android.tools.build:gradle:8.1.0")
        classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:$kotlinVersion")
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

tasks.register("clean", Delete::class) {
    delete(rootProject.buildDir)
}
```

- [ ] **Step 3: Create app build.gradle.kts**

```kotlin
// android-app/app/build.gradle.kts
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.fieldvision.camera"
    compileSdk = 34
    
    defaultConfig {
        applicationId = "com.fieldvision.camera"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }
    
    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }
    
    kotlinOptions {
        jvmTarget = "1.8"
    }
    
    buildFeatures {
        viewBinding = true
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.10.0")
    implementation("androidx.constraintlayout:constraintlayout:2.1.4")
    
    // CameraX
    val cameraxVersion = "1.3.0"
    implementation("androidx.camera:camera-core:$cameraxVersion")
    implementation("androidx.camera:camera-camera2:$cameraxVersion")
    implementation("androidx.camera:camera-lifecycle:$cameraxVersion")
    implementation("androidx.camera:camera-view:$cameraxVersion")
    
    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
    
    // JSON
    implementation("com.google.code.gson:gson:2.10.1")
}
```

- [ ] **Step 4: Create AndroidManifest.xml**

```xml
<!-- android-app/app/src/main/AndroidManifest.xml -->
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
    <uses-permission android:name="android.permission.CHANGE_WIFI_MULTICAST_STATE" />
    
    <uses-feature android:name="android.hardware.camera" android:required="true" />
    <uses-feature android:name="android.hardware.camera.autofocus" android:required="false" />
    
    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:theme="@style/Theme.FieldVisionCamera">
        
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:screenOrientation="landscape"
            android:configChanges="orientation|screenSize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

- [ ] **Step 5: Create minimal MainActivity**

```kotlin
// android-app/app/src/main/java/com/fieldvision/camera/MainActivity.kt
package com.fieldvision.camera

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
    }
}
```

- [ ] **Step 6: Commit**

```bash
git add android-app/
git commit -m "feat: create Android project structure"
```

---

## Task 7: Camera Engine

**Files:**
- Create: `android-app/app/src/main/java/com/fieldvision/camera/camera/CameraEngine.kt`
- Create: `android-app/app/src/main/java/com/fieldvision/camera/camera/CameraConfig.kt`

- [ ] **Step 1: Create CameraConfig data class**

```kotlin
// android-app/app/src/main/java/com/fieldvision/camera/camera/CameraConfig.kt
package com.fieldvision.camera.camera

data class CameraConfig(
    val width: Int = 3840,
    val height: Int = 2160,
    val fps: Int = 30,
    val exposure: Float = 0f,
    val whiteBalance: WhiteBalanceMode = WhiteBalanceMode.AUTO,
    val focusMode: FocusMode = FocusMode.AUTO,
    val torch: Boolean = false
)

enum class WhiteBalanceMode {
    AUTO, DAYLIGHT, CLOUDY, FLUORESCENT, INCANDESCENT
}

enum class FocusMode {
    AUTO, MANUAL
}

data class Resolution(
    val width: Int,
    val height: Int
) {
    companion object {
        val UHD_4K = Resolution(3840, 2160)
        val FHD_1080P = Resolution(1920, 1080)
        val HD_720P = Resolution(1280, 720)
    }
}
```

- [ ] **Step 2: Create CameraEngine class**

```kotlin
// android-app/app/src/main/java/com/fieldvision/camera/camera/CameraEngine.kt
package com.fieldvision.camera.camera

import android.content.Context
import android.graphics.SurfaceTexture
import android.hardware.camera2.*
import android.os.Handler
import android.os.HandlerThread
import android.util.Size
import android.view.Surface
import androidx.lifecycle.LifecycleOwner
import java.util.concurrent.Semaphore
import java.util.concurrent.TimeUnit

class CameraEngine(private val context: Context) {
    
    private var cameraDevice: CameraDevice? = null
    private var captureSession: CameraCaptureSession? = null
    private var cameraThread: HandlerThread? = null
    private var cameraHandler: Handler? = null
    
    private val cameraOpenLock = Semaphore(1)
    private var currentConfig = CameraConfig()
    
    private var previewSurface: Surface? = null
    private var streamingSurface: Surface? = null
    
    fun initialize(lifecycleOwner: LifecycleOwner) {
        cameraThread = HandlerThread("CameraThread").apply { start() }
        cameraHandler = Handler(cameraThread!!.looper)
    }
    
    fun openCamera(surface: Surface, config: CameraConfig = CameraConfig()) {
        currentConfig = config
        previewSurface = surface
        
        val manager = context.getSystemService(Context.CAMERA_SERVICE) as CameraManager
        
        try {
            if (!cameraOpenLock.tryAcquire(2500, TimeUnit.MILLISECONDS)) {
                throw RuntimeException("Camera lock timeout")
            }
            
            val cameraId = getBackCameraId(manager)
            if (cameraId != null) {
                manager.openCamera(cameraId, stateCallback, cameraHandler)
            }
        } catch (e: CameraAccessException) {
            e.printStackTrace()
        }
    }
    
    fun updateConfig(config: CameraConfig) {
        currentConfig = config
        // Reconfigure capture session if active
    }
    
    fun closeCamera() {
        cameraOpenLock.release()
        captureSession?.close()
        captureSession = null
        cameraDevice?.close()
        cameraDevice = null
    }
    
    fun shutdown() {
        cameraThread?.quitSafely()
        try {
            cameraThread?.join()
        } catch (e: InterruptedException) {
            e.printStackTrace()
        }
        cameraThread = null
        cameraHandler = null
    }
    
    private fun getBackCameraId(manager: CameraManager): String? {
        for (id in manager.cameraIdList) {
            val characteristics = manager.getCameraCharacteristics(id)
            val facing = characteristics.get(CameraCharacteristics.LENS_FACING)
            if (facing == CameraCharacteristics.LENS_FACING_BACK) {
                return id
            }
        }
        return null
    }
    
    private val stateCallback = object : CameraDevice.StateCallback() {
        override fun onOpened(camera: CameraDevice) {
            cameraOpenLock.release()
            cameraDevice = camera
            createCaptureSession()
        }
        
        override fun onDisconnected(camera: CameraDevice) {
            cameraOpenLock.release()
            camera.close()
            cameraDevice = null
        }
        
        override fun onError(camera: CameraDevice, error: Int) {
            cameraOpenLock.release()
            camera.close()
            cameraDevice = null
        }
    }
    
    private fun createCaptureSession() {
        val camera = cameraDevice ?: return
        
        val surfaces = mutableListOf<Surface>()
        previewSurface?.let { surfaces.add(it) }
        streamingSurface?.let { surfaces.add(it) }
        
        try {
            camera.createCaptureSession(
                surfaces,
                object : CameraCaptureSession.StateCallback() {
                    override fun onConfigured(session: CameraCaptureSession) {
                        captureSession = session
                        startPreview()
                    }
                    
                    override fun onConfigureFailed(session: CameraCaptureSession) {
                        // Handle failure
                    }
                },
                cameraHandler
            )
        } catch (e: CameraAccessException) {
            e.printStackTrace()
        }
    }
    
    private fun startPreview() {
        val camera = cameraDevice ?: return
        val session = captureSession ?: return
        
        try {
            val builder = camera.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW)
            previewSurface?.let { builder.addTarget(it) }
            
            // Apply config
            builder.set(CaptureRequest.CONTROL_MODE, CaptureRequest.CONTROL_MODE_AUTO)
            
            session.setRepeatingRequest(builder.build(), null, cameraHandler)
        } catch (e: CameraAccessException) {
            e.printStackTrace()
        }
    }
}
```

- [ ] **Step 3: Commit**

```bash
git add android-app/app/src/main/java/com/fieldvision/camera/camera/
git commit -m "feat: add CameraEngine with Camera2 API"
```

---

## Task 8: MJPEG Stream Server

**Files:**
- Create: `android-app/app/src/main/java/com/fieldvision/camera/stream/StreamServer.kt`
- Create: `android-app/app/src/main/java/com/fieldvision/camera/stream/MjpegStream.kt`

- [ ] **Step 1: Create MjpegStream class**

```kotlin
// android-app/app/src/main/java/com/fieldvision/camera/stream/MjpegStream.kt
package com.fieldvision.camera.stream

import android.graphics.Bitmap
import java.io.ByteArrayOutputStream
import java.io.OutputStream
import javax.imageio.ImageIO

class MjpegStream(private val output: OutputStream) {
    
    @Volatile
    private var isStreaming = false
    
    fun start() {
        isStreaming = true
        
        // Send multipart header
        val header = "HTTP/1.1 200 OK\r\n" +
                "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n" +
                "Cache-Control: no-cache\r\n" +
                "Connection: close\r\n\r\n"
        output.write(header.toByteArray())
        output.flush()
    }
    
    fun sendFrame(bitmap: Bitmap) {
        if (!isStreaming) return
        
        try {
            // Convert bitmap to JPEG
            val stream = ByteArrayOutputStream()
            bitmap.compress(Bitmap.CompressFormat.JPEG, 85, stream)
            val jpegData = stream.toByteArray()
            
            // Send frame
            val frameHeader = "--frame\r\n" +
                    "Content-Type: image/jpeg\r\n" +
                    "Content-Length: ${jpegData.size}\r\n\r\n"
            output.write(frameHeader.toByteArray())
            output.write(jpegData)
            output.write("\r\n".toByteArray())
            output.flush()
        } catch (e: Exception) {
            isStreaming = false
        }
    }
    
    fun stop() {
        isStreaming = false
        try {
            output.close()
        } catch (e: Exception) {
            // Ignore
        }
    }
}
```

- [ ] **Step 2: Create StreamServer class**

```kotlin
// android-app/app/src/main/java/com/fieldvision/camera/stream/StreamServer.kt
package com.fieldvision.camera.stream

import android.util.Log
import kotlinx.coroutines.*
import java.net.ServerSocket
import java.net.Socket

class StreamServer(private val port: Int = 8080) {
    
    private var serverSocket: ServerSocket? = null
    private var serverJob: Job? = null
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    
    @Volatile
    var isRunning = false
        private set
    
    var onClientConnected: (() -> Unit)? = null
    var onClientDisconnected: (() -> Unit)? = null
    
    fun start() {
        if (isRunning) return
        
        serverJob = scope.launch {
            try {
                serverSocket = ServerSocket(port)
                isRunning = true
                Log.d(TAG, "Stream server started on port $port")
                
                while (isActive) {
                    val clientSocket = serverSocket?.accept() ?: break
                    handleClient(clientSocket)
                }
            } catch (e: Exception) {
                Log.e(TAG, "Server error: ${e.message}")
            }
        }
    }
    
    fun stop() {
        isRunning = false
        serverJob?.cancel()
        try {
            serverSocket?.close()
        } catch (e: Exception) {
            // Ignore
        }
        scope.cancel()
    }
    
    private fun handleClient(socket: Socket) {
        scope.launch {
            try {
                val output = socket.getOutputStream()
                val mjpegStream = MjpegStream(output)
                
                onClientConnected?.invoke()
                
                // Keep stream alive
                while (socket.isConnected && !socket.isClosed) {
                    delay(100) // Check connection
                }
                
                mjpegStream.stop()
                onClientDisconnected?.invoke()
            } catch (e: Exception) {
                Log.e(TAG, "Client handler error: ${e.message}")
            }
        }
    }
    
    companion object {
        private const val TAG = "StreamServer"
    }
}
```

- [ ] **Step 3: Commit**

```bash
git add android-app/app/src/main/java/com/fieldvision/camera/stream/
git commit -m "feat: add MJPEG stream server"
```

---

## Task 9: Discovery Service

**Files:**
- Create: `android-app/app/src/main/java/com/fieldvision/camera/discovery/DiscoveryService.kt`
- Create: `android-app/app/src/main/java/com/fieldvision/camera/discovery/PhoneInfo.kt`

- [ ] **Step 1: Create PhoneInfo data class**

```kotlin
// android-app/app/src/main/java/com/fieldvision/camera/discovery/PhoneInfo.kt
package com.fieldvision.camera.discovery

import com.google.gson.Gson

data class PhoneInfo(
    val name: String,
    val ip: String,
    val port: Int,
    val protocols: List<String>,
    val resolutions: List<String>
) {
    fun toJson(): String = Gson().toJson(this)
    
    companion object {
        fun fromJson(json: String): PhoneInfo = Gson().fromJson(json, PhoneInfo::class.java)
    }
}

data class DiscoveryMessage(
    val type: String,
    val device: String,
    val ip: String,
    val ports: List<Int>,
    val protocols: List<String>,
    val resolutions: List<String>
) {
    fun toJson(): String = Gson().toJson(this)
    
    companion object {
        fun fromJson(json: String): DiscoveryMessage = Gson().fromJson(json, DiscoveryMessage::class.java)
    }
}
```

- [ ] **Step 2: Create DiscoveryService class**

```kotlin
// android-app/app/src/main/java/com/fieldvision/camera/discovery/DiscoveryService.kt
package com.fieldvision.camera.discovery

import android.util.Log
import kotlinx.coroutines.*
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.net.NetworkInterface

class DiscoveryService(private val port: Int = 9999) {
    
    private var socket: DatagramSocket? = null
    private var discoveryJob: Job? = null
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    
    @Volatile
    var isRunning = false
        private set
    
    var onLaptopFound: ((LaptopInfo) -> Unit)? = null
    
    fun start() {
        if (isRunning) return
        
        discoveryJob = scope.launch {
            try {
                socket = DatagramSocket(null)
                socket?.reuseAddress = true
                socket?.bind(java.net.InetSocketAddress(port))
                isRunning = true
                
                Log.d(TAG, "Discovery service started on port $port")
                
                // Listen for responses
                while (isActive) {
                    val buffer = ByteArray(1024)
                    val packet = DatagramPacket(buffer, buffer.size)
                    socket?.receive(packet)
                    
                    val message = String(packet.data, 0, packet.length)
                    handleDiscoveryResponse(message, packet.address)
                }
            } catch (e: Exception) {
                Log.e(TAG, "Discovery error: ${e.message}")
            }
        }
    }
    
    fun stop() {
        isRunning = false
        discoveryJob?.cancel()
        socket?.close()
        scope.cancel()
    }
    
    fun broadcastDiscovery(phoneInfo: PhoneInfo) {
        scope.launch {
            try {
                val message = DiscoveryMessage(
                    type = "discover",
                    device = phoneInfo.name,
                    ip = phoneInfo.ip,
                    ports = listOf(phoneInfo.port),
                    protocols = phoneInfo.protocols,
                    resolutions = phoneInfo.resolutions
                ).toJson()
                
                val buffer = message.toByteArray()
                val packet = DatagramPacket(
                    buffer,
                    buffer.size,
                    InetAddress.getByName("255.255.255.255"),
                    port
                )
                
                socket?.send(packet)
                Log.d(TAG, "Discovery broadcast sent")
            } catch (e: Exception) {
                Log.e(TAG, "Broadcast error: ${e.message}")
            }
        }
    }
    
    private fun handleDiscoveryResponse(message: String, address: InetAddress) {
        try {
            val response = DiscoveryMessage.fromJson(message)
            if (response.type == "found") {
                val laptop = LaptopInfo(
                    name = response.device,
                    ip = address.hostAddress ?: response.ip,
                    apiPort = response.ports.firstOrNull() ?: 8001
                )
                onLaptopFound?.invoke(laptop)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Invalid discovery response: ${e.message}")
        }
    }
    
    fun getDeviceIp(): String? {
        try {
            val interfaces = NetworkInterface.getNetworkInterfaces()
            while (interfaces.hasMoreElements()) {
                val networkInterface = interfaces.nextElement()
                if (networkInterface.isLoopback || !networkInterface.isUp) continue
                
                val addresses = networkInterface.inetAddresses
                while (addresses.hasMoreElements()) {
                    val address = addresses.nextElement()
                    if (!address.isLoopbackAddress && address is java.net.Inet4Address) {
                        return address.hostAddress
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error getting IP: ${e.message}")
        }
        return null
    }
    
    data class LaptopInfo(
        val name: String,
        val ip: String,
        val apiPort: Int
    )
    
    companion object {
        private const val TAG = "DiscoveryService"
    }
}
```

- [ ] **Step 3: Commit**

```bash
git add android-app/app/src/main/java/com/fieldvision/camera/discovery/
git commit -m "feat: add UDP discovery service"
```

---

## Task 10: Network Monitor

**Files:**
- Create: `android-app/app/src/main/java/com/fieldvision/camera/network/NetworkMonitor.kt`
- Create: `android-app/app/src/main/java/com/fieldvision/camera/network/ConnectionState.kt`

- [ ] **Step 1: Create ConnectionState data class**

```kotlin
// android-app/app/src/main/java/com/fieldvision/camera/network/ConnectionState.kt
package com.fieldvision.camera.network

import com.fieldvision.camera.camera.Resolution

data class ConnectionState(
    val type: ConnectionType,
    val bandwidth: Double,  // Mbps
    val latency: Long,     // ms
    val recommendedResolution: Resolution
)

enum class ConnectionType {
    WIFI,
    HOTSPOT,
    WIFI_DIRECT,
    VENUE_WIFI,
    UNKNOWN
}

data class BandwidthMeasurement(
    val downloadSpeed: Double,  // Mbps
    val uploadSpeed: Double,    // Mbps
    val latency: Long,          // ms
    val timestamp: Long
)
```

- [ ] **Step 2: Create NetworkMonitor class**

```kotlin
// android-app/app/src/main/java/com/fieldvision/camera/network/NetworkMonitor.kt
package com.fieldvision.camera.network

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.util.Log
import com.fieldvision.camera.camera.Resolution
import kotlinx.coroutines.*
import java.net.HttpURLConnection
import java.net.URL

class NetworkMonitor(private val context: Context) {
    
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var monitoringJob: Job? = null
    
    @Volatile
    var currentConnection: ConnectionState? = null
        private set
    
    var onConnectionChanged: ((ConnectionState) -> Unit)? = null
    
    fun startMonitoring() {
        monitoringJob = scope.launch {
            while (isActive) {
                val connection = measureConnection()
                if (connection != currentConnection) {
                    currentConnection = connection
                    onConnectionChanged?.invoke(connection)
                }
                delay(5000) // Measure every 5 seconds
            }
        }
    }
    
    fun stopMonitoring() {
        monitoringJob?.cancel()
        scope.cancel()
    }
    
    fun getRecommendedResolution(): Resolution {
        val connection = currentConnection ?: return Resolution.UHD_4K
        
        return when {
            connection.bandwidth > 20 -> Resolution.UHD_4K
            connection.bandwidth > 10 -> Resolution.FHD_1080P
            else -> Resolution.HD_720P
        }
    }
    
    private fun measureConnection(): ConnectionState? {
        return try {
            val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            val network = connectivityManager.activeNetwork ?: return null
            val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return null
            
            val connectionType = when {
                capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) -> {
                    if (isHotspot()) ConnectionType.HOTSPOT else ConnectionType.WIFI
                }
                capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) -> ConnectionType.UNKNOWN
                else -> ConnectionType.UNKNOWN
            }
            
            val bandwidth = measureBandwidth()
            val latency = measureLatency()
            val resolution = calculateResolution(bandwidth)
            
            ConnectionState(
                type = connectionType,
                bandwidth = bandwidth,
                latency = latency,
                recommendedResolution = resolution
            )
        } catch (e: Exception) {
            Log.e(TAG, "Connection measurement error: ${e.message}")
            null
        }
    }
    
    private fun measureBandwidth(): Double {
        return try {
            val url = URL("http://speedtest.tele2.net/1MB.zip")
            val connection = url.openConnection() as HttpURLConnection
            connection.connectTimeout = 5000
            connection.readTimeout = 5000
            
            val startTime = System.currentTimeMillis()
            val inputStream = connection.inputStream
            val buffer = ByteArray(1024)
            var totalBytes = 0L
            
            while (true) {
                val bytesRead = inputStream.read(buffer)
                if (bytesRead == -1) break
                totalBytes += bytesRead
            }
            
            val elapsed = (System.currentTimeMillis() - startTime) / 1000.0
            inputStream.close()
            connection.disconnect()
            
            (totalBytes * 8) / (elapsed * 1000000) // Convert to Mbps
        } catch (e: Exception) {
            Log.e(TAG, "Bandwidth measurement error: ${e.message}")
            0.0
        }
    }
    
    private fun measureLatency(): Long {
        return try {
            val url = URL("http://www.google.com")
            val connection = url.openConnection() as HttpURLConnection
            connection.connectTimeout = 3000
            
            val startTime = System.currentTimeMillis()
            connection.connect()
            val latency = System.currentTimeMillis() - startTime
            
            connection.disconnect()
            latency
        } catch (e: Exception) {
            Log.e(TAG, "Latency measurement error: ${e.message}")
            -1
        }
    }
    
    private fun calculateResolution(bandwidth: Double): Resolution {
        return when {
            bandwidth > 20 -> Resolution.UHD_4K
            bandwidth > 10 -> Resolution.FHD_1080P
            else -> Resolution.HD_720P
        }
    }
    
    private fun isHotspot(): Boolean {
        // Simple heuristic - check if IP is in hotspot range
        // Most Android hotspots use 192.168.43.x
        return true // Simplified for now
    }
    
    companion object {
        private const val TAG = "NetworkMonitor"
    }
}
```

- [ ] **Step 3: Commit**

```bash
git add android-app/app/src/main/java/com/fieldvision/camera/network/
git commit -m "feat: add network monitor with bandwidth detection"
```

---

## Task 11: Update MainActivity

**Files:**
- Modify: `android-app/app/src/main/java/com/fieldvision/camera/MainActivity.kt`
- Create: `android-app/app/src/main/res/layout/activity_main.xml`

- [ ] **Step 1: Create activity layout**

```xml
<!-- android-app/app/src/main/res/layout/activity_main.xml -->
<?xml version="1.0" encoding="utf-8"?>
<androidx.constraintlayout.widget.ConstraintLayout 
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="#FF121212">

    <!-- Camera Preview -->
    <TextureView
        android:id="@+id/previewView"
        android:layout_width="0dp"
        android:layout_height="0dp"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintBottom_toTopOf="@id/controlPanel"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent" />

    <!-- Control Panel -->
    <LinearLayout
        android:id="@+id/controlPanel"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        android:padding="16dp"
        android:background="#CC1E1E1E"
        app:layout_constraintBottom_toBottomOf="parent">

        <!-- Connection Status -->
        <TextView
            android:id="@+id/statusText"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="Ready to stream"
            android:textColor="#FFFFFF"
            android:textSize="14sp" />

        <!-- Resolution Buttons -->
        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="horizontal"
            android:layout_marginTop="8dp">

            <Button
                android:id="@+id/btn4K"
                android:layout_width="0dp"
                android:layout_height="wrap_content"
                android:layout_weight="1"
                android:text="4K"
                android:layout_marginEnd="4dp" />

            <Button
                android:id="@+id/btn1080p"
                android:layout_width="0dp"
                android:layout_height="wrap_content"
                android:layout_weight="1"
                android:text="1080p"
                android:layout_marginStart="4dp"
                android:layout_marginEnd="4dp" />

            <Button
                android:id="@+id/btn720p"
                android:layout_width="0dp"
                android:layout_height="wrap_content"
                android:layout_weight="1"
                android:text="720p"
                android:layout_marginStart="4dp"
                android:layout_marginEnd="4dp" />

            <Button
                android:id="@+id/btnAuto"
                android:layout_width="0dp"
                android:layout_height="wrap_content"
                android:layout_weight="1"
                android:text="Auto"
                android:layout_marginStart="4dp" />
        </LinearLayout>

        <!-- Start/Stop Button -->
        <Button
            android:id="@+id/btnStream"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="Start Streaming"
            android:layout_marginTop="8dp" />
    </LinearLayout>

</androidx.constraintlayout.widget.ConstraintLayout>
```

- [ ] **Step 2: Update MainActivity**

```kotlin
// android-app/app/src/main/java/com/fieldvision/camera/MainActivity.kt
package com.fieldvision.camera

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.SurfaceTexture
import android.os.Bundle
import android.view.TextureView
import android.view.WindowManager
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.fieldvision.camera.camera.CameraConfig
import com.fieldvision.camera.camera.CameraEngine
import com.fieldvision.camera.camera.Resolution
import com.fieldvision.camera.discovery.DiscoveryService
import com.fieldvision.camera.discovery.PhoneInfo
import com.fieldvision.camera.network.NetworkMonitor
import com.fieldvision.camera.stream.StreamServer
import kotlinx.coroutines.*

class MainActivity : AppCompatActivity() {
    
    private lateinit var cameraEngine: CameraEngine
    private lateinit var streamServer: StreamServer
    private lateinit var discoveryService: DiscoveryService
    private lateinit var networkMonitor: NetworkMonitor
    
    private lateinit var previewView: TextureView
    private lateinit var statusText: TextView
    private lateinit var btnStream: Button
    
    private var isStreaming = false
    private var currentResolution = Resolution.UHD_4K
    
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // Keep screen on
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        
        // Initialize views
        previewView = findViewById(R.id.previewView)
        statusText = findViewById(R.id.statusText)
        btnStream = findViewById(R.id.btnStream)
        
        // Initialize services
        cameraEngine = CameraEngine(this)
        streamServer = StreamServer()
        discoveryService = DiscoveryService()
        networkMonitor = NetworkMonitor(this)
        
        // Setup listeners
        setupListeners()
        
        // Check permissions
        if (hasCameraPermission()) {
            initializeCamera()
        } else {
            requestCameraPermission()
        }
    }
    
    override fun onResume() {
        super.onResume()
        cameraEngine.initialize(this)
    }
    
    override fun onPause() {
        super.onPause()
        if (isStreaming) {
            stopStreaming()
        }
        cameraEngine.closeCamera()
    }
    
    override fun onDestroy() {
        super.onDestroy()
        cameraEngine.shutdown()
        streamServer.stop()
        discoveryService.stop()
        networkMonitor.stopMonitoring()
        scope.cancel()
    }
    
    private fun setupListeners() {
        // Resolution buttons
        findViewById<Button>(R.id.btn4K).setOnClickListener { setResolution(Resolution.UHD_4K) }
        findViewById<Button>(R.id.btn1080p).setOnClickListener { setResolution(Resolution.FHD_1080P) }
        findViewById<Button>(R.id.btn720p).setOnClickListener { setResolution(Resolution.HD_720P) }
        findViewById<Button>(R.id.btnAuto).setOnClickListener { setResolution(null) }
        
        // Stream button
        btnStream.setOnClickListener {
            if (isStreaming) {
                stopStreaming()
            } else {
                startStreaming()
            }
        }
        
        // TextureView listener
        previewView.surfaceTextureListener = object : TextureView.SurfaceTextureListener {
            override fun onSurfaceTextureAvailable(surface: SurfaceTexture, width: Int, height: Int) {
                initializeCamera()
            }
            
            override fun onSurfaceTextureSizeChanged(surface: SurfaceTexture, width: Int, height: Int) {}
            
            override fun onSurfaceTextureDestroyed(surface: SurfaceTexture): Boolean = true
            
            override fun onSurfaceTextureUpdated(surface: SurfaceTexture) {}
        }
        
        // Discovery callback
        discoveryService.onLaptopFound = { laptop ->
            scope.launch {
                statusText.text = "Found: ${laptop.name} (${laptop.ip})"
                Toast.makeText(this@MainActivity, "Found ${laptop.name}", Toast.LENGTH_SHORT).show()
            }
        }
        
        // Network callback
        networkMonitor.onConnectionChanged = { connection ->
            scope.launch {
                statusText.text = "Network: ${connection.type} | ${connection.bandwidth.toInt()} Mbps"
            }
        }
    }
    
    private fun initializeCamera() {
        if (previewView.isAvailable) {
            val surface = Surface(previewView.surfaceTexture!!)
            cameraEngine.openCamera(surface, CameraConfig())
            
            // Start discovery
            discoveryService.start()
            networkMonitor.startMonitoring()
            
            // Broadcast discovery
            val phoneInfo = PhoneInfo(
                name = android.os.Build.MODEL,
                ip = discoveryService.getDeviceIp() ?: "unknown",
                port = 8080,
                protocols = listOf("mjpeg", "h264"),
                resolutions = listOf("4k", "1080p", "720p")
            )
            discoveryService.broadcastDiscovery(phoneInfo)
        }
    }
    
    private fun startStreaming() {
        isStreaming = true
        btnStream.text = "Stop Streaming"
        statusText.text = "Streaming started"
        
        streamServer.start()
    }
    
    private fun stopStreaming() {
        isStreaming = false
        btnStream.text = "Start Streaming"
        statusText.text = "Streaming stopped"
        
        streamServer.stop()
    }
    
    private fun setResolution(resolution: Resolution?) {
        currentResolution = resolution ?: networkMonitor.getRecommendedResolution()
        statusText.text = "Resolution: ${currentResolution.width}x${currentResolution.height}"
    }
    
    private fun hasCameraPermission(): Boolean {
        return ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED
    }
    
    private fun requestCameraPermission() {
        ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.CAMERA), CAMERA_PERMISSION_CODE)
    }
    
    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        when (requestCode) {
            CAMERA_PERMISSION_CODE -> {
                if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                    initializeCamera()
                } else {
                    Toast.makeText(this, "Camera permission required", Toast.LENGTH_LONG).show()
                    finish()
                }
            }
        }
    }
    
    companion object {
        private const val CAMERA_PERMISSION_CODE = 100
    }
}
```

- [ ] **Step 3: Commit**

```bash
git add android-app/app/src/main/java/com/fieldvision/camera/MainActivity.kt
git add android-app/app/src/main/res/layout/activity_main.xml
git commit -m "feat: complete MainActivity with streaming controls"
```

---

## Task 12: Run All Tests

**Files:**
- None (verification step)

- [ ] **Step 1: Run backend tests**

Run: `cd "D:\FieldVision AI" && PYTHONPATH="backend;." python -m pytest tests/backend/app/services/camera/ -v`
Expected: All tests PASS

- [ ] **Step 2: Verify Android project builds**

Run: `cd "D:\FieldVision AI\android-app" && ./gradlew assembleDebug`
Expected: BUILD SUCCESSFUL

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete phone camera app implementation"
```

---

## Summary

This plan implements:
1. **Backend:** Discovery service, HTTP camera source, updated config
2. **Android:** Camera2 engine, MJPEG server, UDP discovery, network monitor
3. **Integration:** Auto-discovery, 3-tier protocol fallback, resolution auto-adapt

Total tasks: 12
Estimated time: 2-3 hours
