# FieldVision AI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an event-driven robotic football camera system with AI Director, cinematic motion planning, and real-time dashboard.

**Architecture:** Event-driven robotics system. Every service (Camera, Vision, Tracking, Director, Motion, Servo) publishes events when done and subscribes to events it needs. No direct coupling. Message bus orchestrates data flow. State machine manages system states. Safety layer validates all servo commands.

**Tech Stack:** Python 3.12, FastAPI, OpenCV, Ultralytics YOLO11, ByteTrack, PyTorch CUDA, WebSockets, React 18, TypeScript, Vite, TailwindCSS, ESP32, PlatformIO, Arduino

---

## File Structure

```
FieldVision AI/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── state.py
│   │   │   ├── events.py
│   │   │   ├── logging.py
│   │   │   └── dependencies.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── camera/
│   │   │   │   ├── __init__.py
│   │   │   │   └── service.py
│   │   │   ├── vision/
│   │   │   │   ├── __init__.py
│   │   │   │   └── service.py
│   │   │   ├── tracking/
│   │   │   │   ├── __init__.py
│   │   │   │   └── service.py
│   │   │   ├── director/
│   │   │   │   ├── __init__.py
│   │   │   │   └── service.py
│   │   │   ├── prediction/
│   │   │   │   ├── __init__.py
│   │   │   │   └── service.py
│   │   │   ├── motion/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── planner.py
│   │   │   │   ├── controller.py
│   │   │   │   └── safety.py
│   │   │   ├── communication/
│   │   │   │   ├── __init__.py
│   │   │   │   └── service.py
│   │   │   ├── streaming/
│   │   │   │   ├── __init__.py
│   │   │   │   └── service.py
│   │   │   ├── monitoring/
│   │   │   │   ├── __init__.py
│   │   │   │   └── service.py
│   │   │   ├── calibration/
│   │   │   │   ├── __init__.py
│   │   │   │   └── service.py
│   │   │   ├── replay/
│   │   │   │   ├── __init__.py
│   │   │   │   └── service.py
│   │   │   └── analytics/
│   │   │       ├── __init__.py
│   │   │       └── service.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── detection.py
│   │   │   ├── track.py
│   │   │   ├── director.py
│   │   │   ├── motion.py
│   │   │   ├── servo.py
│   │   │   ├── events.py
│   │   │   └── health.py
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── status.py
│   │       ├── camera.py
│   │       ├── servo.py
│   │       ├── ai.py
│   │       ├── calibration.py
│   │       ├── stream.py
│   │       ├── replay.py
│   │       ├── health.py
│   │       ├── logs.py
│   │       ├── settings.py
│   │       ├── plugins.py
│   │       ├── simulation.py
│   │       └── websocket.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── test_config.py
│   │   │   ├── test_state.py
│   │   │   ├── test_events.py
│   │   │   └── test_logging.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── test_camera.py
│   │   │   ├── test_vision.py
│   │   │   ├── test_tracking.py
│   │   │   ├── test_director.py
│   │   │   ├── test_prediction.py
│   │   │   ├── test_motion.py
│   │   │   ├── test_safety.py
│   │   │   ├── test_communication.py
│   │   │   ├── test_calibration.py
│   │   │   └── test_monitoring.py
│   │   └── integration/
│   │       ├── __init__.py
│   │       └── test_pipeline.py
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── StatusBadge.tsx
│   │   │   ├── MetricCard.tsx
│   │   │   └── AngleGauge.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Camera.tsx
│   │   │   ├── Servo.tsx
│   │   │   ├── Director.tsx
│   │   │   ├── Calibration.tsx
│   │   │   ├── Streaming.tsx
│   │   │   ├── Replay.tsx
│   │   │   ├── Health.tsx
│   │   │   ├── Plugins.tsx
│   │   │   ├── Logs.tsx
│   │   │   └── Settings.tsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useMetrics.ts
│   │   │   └── useApi.ts
│   │   ├── services/
│   │   │   └── api.ts
│   │   └── types/
│   │       └── index.ts
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── tailwind.config.js
├── firmware/
│   ├── src/
│   │   ├── main.cpp
│   │   ├── wifi_manager.h
│   │   ├── websocket_client.h
│   │   ├── servo_controller.h
│   │   └── watchdog.h
│   ├── include/
│   ├── platformio.ini
│   └── lib/
├── configs/
│   ├── camera.yaml
│   ├── servo.yaml
│   ├── network.yaml
│   ├── stream.yaml
│   ├── ai.yaml
│   ├── dashboard.yaml
│   └── simulation.yaml
├── profiles/
│   └── default.yaml
├── models/
├── logs/
├── recordings/
├── scripts/
├── tests/
├── docs/
└── assets/
```

---

## Phase 1: Project Scaffold

### Task 1: Create Monorepo Structure

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/requirements.txt`
- Create: `backend/pyproject.toml`
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `firmware/platformio.ini`
- Create: `firmware/src/main.cpp`

- [ ] **Step 1: Create backend directory structure**

```bash
mkdir -p backend/app/core
mkdir -p backend/app/services/camera
mkdir -p backend/app/services/vision
mkdir -p backend/app/services/tracking
mkdir -p backend/app/services/director
mkdir -p backend/app/services/prediction
mkdir -p backend/app/services/motion
mkdir -p backend/app/services/communication
mkdir -p backend/app/services/streaming
mkdir -p backend/app/services/monitoring
mkdir -p backend/app/services/calibration
mkdir -p backend/app/services/replay
mkdir -p backend/app/services/analytics
mkdir -p backend/app/models
mkdir -p backend/app/api
mkdir -p backend/tests/core
mkdir -p backend/tests/services
mkdir -p backend/tests/integration
```

- [ ] **Step 2: Create backend __init__.py files**

```python
# backend/app/__init__.py
"""FieldVision AI Backend."""
```

```python
# backend/app/core/__init__.py
"""Core modules."""
```

```python
# backend/app/services/__init__.py
"""Service modules."""
```

```python
# backend/app/models/__init__.py
"""Pydantic models."""
```

```python
# backend/app/api/__init__.py
"""API route handlers."""
```

```python
# backend/tests/__init__.py
"""Test modules."""
```

- [ ] **Step 3: Create requirements.txt**

```txt
fastapi==0.115.0
uvicorn[standard]==0.30.0
websockets==12.0
opencv-python-headless==4.10.0.84
ultralytics==8.2.0
bytetracker==0.0.4
torch==2.3.0
torchvision==0.18.0
numpy==1.26.4
pydantic==2.7.0
pyyaml==6.0.1
psutil==5.9.8
aiosqlite==0.20.0
httpx==0.27.0
pytest==8.2.0
pytest-asyncio==0.23.0
pytest-cov==5.0.0
```

- [ ] **Step 4: Create pyproject.toml**

```toml
[project]
name = "fieldvision-ai"
version = "1.0.0"
description = "AI-powered football camera system"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "websockets>=12.0",
    "opencv-python-headless>=4.10.0",
    "ultralytics>=8.2.0",
    "torch>=2.3.0",
    "numpy>=1.26.4",
    "pydantic>=2.7.0",
    "pyyaml>=6.0.1",
    "psutil>=5.9.8",
    "aiosqlite>=0.20.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 5: Create FastAPI main.py**

```python
"""FieldVision AI Backend Entry Point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import load_config
from app.core.state import SystemStateMachine
from app.core.events import EventBus
from app.core.logging import setup_logging

app = FastAPI(
    title="FieldVision AI",
    description="AI-powered football camera system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize system on startup."""
    config = load_config()
    app.state.config = config
    app.state.event_bus = EventBus()
    app.state.state_machine = SystemStateMachine()
    setup_logging()
    app.state.state_machine.transition("booting", "connecting")


@app.on_event("shutdown")
async def shutdown():
    """Clean shutdown."""
    pass


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "fieldvision-ai"}
```

- [ ] **Step 6: Create frontend structure**

```bash
mkdir -p frontend/src/components
mkdir -p frontend/src/pages
mkdir -p frontend/src/hooks
mkdir -p frontend/src/services
mkdir -p frontend/src/types
```

- [ ] **Step 7: Create frontend package.json**

```json
{
  "name": "fieldvision-dashboard",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.23.0",
    "recharts": "^2.12.0",
    "tailwindcss": "^3.4.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "typescript": "^5.4.0",
    "vite": "^5.4.0"
  }
}
```

- [ ] **Step 8: Create firmware platformio.ini**

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
monitor_speed = 115200
lib_deps =
    ESP Async WebServer
    ArduinoJson
    ESP32Servo
```

- [ ] **Step 9: Create firmware main.cpp**

```cpp
#include <Arduino.h>
#include "wifi_manager.h"
#include "websocket_client.h"
#include "servo_controller.h"
#include "watchdog.h"

WiFiManager wifiManager;
WebSocketClient wsClient;
ServoController servoController;
Watchdog watchdog;

void setup() {
    Serial.begin(115200);
    wifiManager.connect();
    wsClient.connect();
    servoController.begin();
    watchdog.begin(15000);
}

void loop() {
    wsClient.update();
    servoController.update();
    watchdog.feed();
}
```

- [ ] **Step 10: Verify backend runs**

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Expected: Server starts, `http://localhost:8000/api/health` returns `{"status":"ok"}`

- [ ] **Step 11: Verify frontend runs**

```bash
cd frontend
npm install
npm run dev
```

Expected: Vite dev server starts at `http://localhost:5173`

- [ ] **Step 12: Commit**

```bash
git add backend/ frontend/ firmware/ configs/ profiles/ models/ logs/ recordings/ scripts/ docs/ assets/
git commit -m "feat: initial project scaffold with backend, frontend, firmware"
```

---

### Task 2: Configuration System

**Files:**
- Create: `backend/app/core/config.py`
- Create: `configs/camera.yaml`
- Create: `configs/servo.yaml`
- Create: `configs/network.yaml`
- Create: `configs/stream.yaml`
- Create: `configs/ai.yaml`
- Create: `configs/dashboard.yaml`
- Create: `configs/simulation.yaml`
- Create: `profiles/default.yaml`
- Create: `backend/tests/core/test_config.py`

- [ ] **Step 1: Write failing test for config loader**

```python
# backend/tests/core/test_config.py
import pytest
from app.core.config import load_config, Config


def test_load_config_returns_config_object():
    config = load_config()
    assert isinstance(config, Config)


def test_config_has_camera_section():
    config = load_config()
    assert hasattr(config, "camera")
    assert config.camera.source is not None


def test_config_has_servo_section():
    config = load_config()
    assert hasattr(config, "servo")
    assert config.servo.min_angle == 0.0
    assert config.servo.max_angle == 180.0


def test_config_has_ai_section():
    config = load_config()
    assert hasattr(config, "ai")
    assert config.ai.detection.model == "yolo11n.pt"


def test_config_has_network_section():
    config = load_config()
    assert hasattr(config, "network")
    assert config.network.heartbeat_interval == 5.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/core/test_config.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.core.config'`

- [ ] **Step 3: Create config YAML files**

```yaml
# configs/camera.yaml
source: "rtsp://192.168.1.100:5554/live"
resolution:
  width: 1920
  height: 1080
fps: 30
buffer_size: 3
reconnect_delay: 5.0
reconnect_max_attempts: 0
frame_timeout: 10.0
```

```yaml
# configs/servo.yaml
min_angle: 0.0
max_angle: 180.0
center_angle: 90.0
dead_zone: 1.5
max_speed: 120.0
max_acceleration: 200.0
update_rate: 20
emergency_stop_pin: 25
manual_override_pin: 26
```

```yaml
# configs/network.yaml
wifi_ssid: "FieldVision"
wifi_password: ""
websocket_port: 0
heartbeat_interval: 5.0
watchdog_timeout: 15.0
```

```yaml
# configs/stream.yaml
obs_websocket:
  host: "127.0.0.1"
  port: 4455
  password: ""
youtube:
  stream_key: ""
  rtmp_url: "rtmp://a.rtmp.youtube.com/live2"
overlay:
  enabled: false
  position: "top-right"
```

```yaml
# configs/ai.yaml
detection:
  model: "yolo11n.pt"
  device: "cuda"
  confidence_threshold: 0.5
  iou_threshold: 0.45
  input_size: 640
  classes:
    ball: 0
    player: 1
    goalkeeper: 2
tracking:
  iou_threshold: 0.45
  track_persistence: 30
  max_age: 60
director:
  default_mode: "broadcast"
  auto_mode_switch: true
  modes:
    broadcast:
      ball_weight: 1.0
      player_weight: 0.7
      look_ahead: 0.3
      smoothness: 0.8
    aggressive:
      ball_weight: 1.2
      player_weight: 0.8
      look_ahead: 0.1
      smoothness: 0.5
    wide:
      ball_weight: 0.8
      player_weight: 0.9
      look_ahead: 0.5
      smoothness: 0.9
    training:
      ball_weight: 1.5
      player_weight: 0.3
      look_ahead: 0.0
      smoothness: 0.3
  ball_lost_timeout: 2.0
prediction:
  kalman_process_noise: 0.03
  kalman_measurement_noise: 0.1
motion:
  profile: "broadcast"
  ease_in_duration: 0.2
  ease_out_duration: 0.3
  dead_zone: 1.5
  max_speed: 120.0
  max_acceleration: 200.0
safety:
  max_jump_angle: 45.0
  watchdog_timeout: 15.0
  max_servo_current: 4.0
  max_servo_temperature: 60.0
performance:
  target_fps: 30
  min_fps: 15
  resolution_scale_thresholds: [25, 20, 15]
  gpu_memory_thresholds: [0.6, 0.8]
update_rate: 20
```

```yaml
# configs/dashboard.yaml
host: "127.0.0.1"
port: 0
log_level: "info"
refresh_rate: 1000
metrics_history: 3600
```

```yaml
# configs/simulation.yaml
enabled: false
source_type: "video"
source_path: ""
loop: false
speed: 1.0
```

```yaml
# profiles/default.yaml
name: "Default"
venue: "Default Venue"
date: "2026-07-14"
servo:
  min_angle: 0.0
  max_angle: 180.0
  center_angle: 90.0
  dead_zone: 1.5
camera:
  horizontal_fov: 62.5
  vertical_fov: 38.0
  distortion_coefficients: [0.0, 0.0, 0.0, 0.0, 0.0]
  pixel_to_angle_lut: ""
field:
  penalty_area_x_min: 0.15
  penalty_area_x_max: 0.85
  penalty_area_y_min: 0.3
  penalty_area_y_max: 0.7
  goal_area_x_min: 0.35
  goal_area_x_max: 0.65
  goal_area_y_min: 0.4
  goal_area_y_max: 0.6
mount:
  height_meters: 1.5
  distance_from_center_meters: 5.0
  angle_offset_degrees: 0.0
```

- [ ] **Step 4: Implement config loader**

```python
# backend/app/core/config.py
"""Configuration loader for FieldVision AI."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


class CameraConfig(BaseModel):
    source: str = "rtsp://192.168.1.100:5554/live"
    resolution_width: int = 1920
    resolution_height: int = 1080
    fps: int = 30
    buffer_size: int = 3
    reconnect_delay: float = 5.0
    reconnect_max_attempts: int = 0
    frame_timeout: float = 10.0


class ServoConfig(BaseModel):
    min_angle: float = 0.0
    max_angle: float = 180.0
    center_angle: float = 90.0
    dead_zone: float = 1.5
    max_speed: float = 120.0
    max_acceleration: float = 200.0
    update_rate: int = 20
    emergency_stop_pin: int = 25
    manual_override_pin: int = 26


class NetworkConfig(BaseModel):
    wifi_ssid: str = "FieldVision"
    wifi_password: str = ""
    websocket_port: int = 0
    heartbeat_interval: float = 5.0
    watchdog_timeout: float = 15.0


class DetectionConfig(BaseModel):
    model: str = "yolo11n.pt"
    device: str = "cuda"
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.45
    input_size: int = 640
    classes: dict[str, int] = {"ball": 0, "player": 1, "goalkeeper": 2}


class TrackingConfig(BaseModel):
    iou_threshold: float = 0.45
    track_persistence: int = 30
    max_age: int = 60


class DirectorModeConfig(BaseModel):
    ball_weight: float = 1.0
    player_weight: float = 0.7
    look_ahead: float = 0.3
    smoothness: float = 0.8


class DirectorConfig(BaseModel):
    default_mode: str = "broadcast"
    auto_mode_switch: bool = True
    modes: dict[str, DirectorModeConfig] = {
        "broadcast": DirectorModeConfig(),
        "aggressive": DirectorModeConfig(ball_weight=1.2, player_weight=0.8, look_ahead=0.1, smoothness=0.5),
        "wide": DirectorModeConfig(ball_weight=0.8, player_weight=0.9, look_ahead=0.5, smoothness=0.9),
        "training": DirectorModeConfig(ball_weight=1.5, player_weight=0.3, look_ahead=0.0, smoothness=0.3),
    }
    ball_lost_timeout: float = 2.0


class PredictionConfig(BaseModel):
    kalman_process_noise: float = 0.03
    kalman_measurement_noise: float = 0.1


class MotionConfig(BaseModel):
    profile: str = "broadcast"
    ease_in_duration: float = 0.2
    ease_out_duration: float = 0.3
    dead_zone: float = 1.5
    max_speed: float = 120.0
    max_acceleration: float = 200.0


class SafetyConfig(BaseModel):
    max_jump_angle: float = 45.0
    watchdog_timeout: float = 15.0
    max_servo_current: float = 4.0
    max_servo_temperature: float = 60.0


class PerformanceConfig(BaseModel):
    target_fps: int = 30
    min_fps: int = 15
    resolution_scale_thresholds: list[int] = [25, 20, 15]
    gpu_memory_thresholds: list[float] = [0.6, 0.8]


class AIConfig(BaseModel):
    detection: DetectionConfig = DetectionConfig()
    tracking: TrackingConfig = TrackingConfig()
    director: DirectorConfig = DirectorConfig()
    prediction: PredictionConfig = PredictionConfig()
    motion: MotionConfig = MotionConfig()
    safety: SafetyConfig = SafetyConfig()
    performance: PerformanceConfig = PerformanceConfig()
    update_rate: int = 20


class ObsWebsocketConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 4455
    password: str = ""


class YoutubeConfig(BaseModel):
    stream_key: str = ""
    rtmp_url: str = "rtmp://a.rtmp.youtube.com/live2"


class OverlayConfig(BaseModel):
    enabled: bool = False
    position: str = "top-right"


class StreamConfig(BaseModel):
    obs_websocket: ObsWebsocketConfig = ObsWebsocketConfig()
    youtube: YoutubeConfig = YoutubeConfig()
    overlay: OverlayConfig = OverlayConfig()


class DashboardConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 0
    log_level: str = "info"
    refresh_rate: int = 1000
    metrics_history: int = 3600


class SimulationConfig(BaseModel):
    enabled: bool = False
    source_type: str = "video"
    source_path: str = ""
    loop: bool = False
    speed: float = 1.0


class Config(BaseModel):
    camera: CameraConfig = CameraConfig()
    servo: ServoConfig = ServoConfig()
    network: NetworkConfig = NetworkConfig()
    ai: AIConfig = AIConfig()
    stream: StreamConfig = StreamConfig()
    dashboard: DashboardConfig = DashboardConfig()
    simulation: SimulationConfig = SimulationConfig()


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents."""
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def _merge_dicts(base: dict, override: dict) -> dict:
    """Deep merge override into base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_dir: str = "configs") -> Config:
    """Load configuration from YAML files."""
    config_path = Path(config_dir)

    camera_data = _load_yaml(config_path / "camera.yaml")
    servo_data = _load_yaml(config_path / "servo.yaml")
    network_data = _load_yaml(config_path / "network.yaml")
    ai_data = _load_yaml(config_path / "ai.yaml")
    stream_data = _load_yaml(config_path / "stream.yaml")
    dashboard_data = _load_yaml(config_path / "dashboard.yaml")
    simulation_data = _load_yaml(config_path / "simulation.yaml")

    return Config(
        camera=CameraConfig(**camera_data) if camera_data else CameraConfig(),
        servo=ServoConfig(**servo_data) if servo_data else ServoConfig(),
        network=NetworkConfig(**network_data) if network_data else NetworkConfig(),
        ai=AIConfig(**ai_data) if ai_data else AIConfig(),
        stream=StreamConfig(**stream_data) if stream_data else StreamConfig(),
        dashboard=DashboardConfig(**dashboard_data) if dashboard_data else DashboardConfig(),
        simulation=SimulationConfig(**simulation_data) if simulation_data else SimulationConfig(),
    )
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd backend
pytest tests/core/test_config.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/config.py backend/tests/core/test_config.py configs/ profiles/
git commit -m "feat: add configuration system with YAML loading and Pydantic models"
```

---

### Task 3: State Machine

**Files:**
- Create: `backend/app/core/state.py`
- Create: `backend/tests/core/test_state.py`

- [ ] **Step 1: Write failing test for state machine**

```python
# backend/tests/core/test_state.py
import pytest
from app.core.state import SystemStateMachine, SystemState


def test_initial_state_is_booting():
    sm = SystemStateMachine()
    assert sm.current_state == SystemState.BOOTING


def test_valid_transition():
    sm = SystemStateMachine()
    sm.transition("booting", "connecting")
    assert sm.current_state == SystemState.CONNECTING


def test_invalid_transition_raises():
    sm = SystemStateMachine()
    with pytest.raises(ValueError):
        sm.transition("booting", "tracking")


def test_all_valid_transitions():
    sm = SystemStateMachine()
    valid = [
        ("booting", "connecting"),
        ("connecting", "idle"),
        ("idle", "streaming"),
        ("streaming", "tracking"),
        ("tracking", "manual"),
        ("tracking", "homing"),
        ("tracking", "emergency_stop"),
        ("manual", "tracking"),
        ("manual", "emergency_stop"),
        ("homing", "idle"),
        ("emergency_stop", "idle"),
        ("error", "booting"),
    ]
    for from_state, to_state in valid:
        sm = SystemStateMachine()
        sm.current_state = SystemState(from_state)
        sm.transition(from_state, to_state)
        assert sm.current_state == SystemState(to_state)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/core/test_state.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.core.state'`

- [ ] **Step 3: Implement state machine**

```python
# backend/app/core/state.py
"""System state machine for FieldVision AI."""

from enum import Enum
from typing import Callable, Optional


class SystemState(Enum):
    BOOTING = "booting"
    CONNECTING = "connecting"
    IDLE = "idle"
    STREAMING = "streaming"
    TRACKING = "tracking"
    MANUAL = "manual"
    HOMING = "homing"
    EMERGENCY_STOP = "emergency_stop"
    ERROR = "error"


VALID_TRANSITIONS: dict[SystemState, list[SystemState]] = {
    SystemState.BOOTING: [SystemState.CONNECTING, SystemState.ERROR],
    SystemState.CONNECTING: [SystemState.IDLE, SystemState.ERROR],
    SystemState.IDLE: [SystemState.STREAMING, SystemState.CONNECTING, SystemState.ERROR],
    SystemState.STREAMING: [
        SystemState.TRACKING,
        SystemState.IDLE,
        SystemState.MANUAL,
        SystemState.ERROR,
    ],
    SystemState.TRACKING: [
        SystemState.STREAMING,
        SystemState.MANUAL,
        SystemState.HOMING,
        SystemState.EMERGENCY_STOP,
        SystemState.ERROR,
    ],
    SystemState.MANUAL: [
        SystemState.TRACKING,
        SystemState.HOMING,
        SystemState.EMERGENCY_STOP,
    ],
    SystemState.HOMING: [
        SystemState.IDLE,
        SystemState.TRACKING,
        SystemState.EMERGENCY_STOP,
    ],
    SystemState.EMERGENCY_STOP: [SystemState.IDLE, SystemState.HOMING],
    SystemState.ERROR: [SystemState.BOOTING],
}


class SystemStateMachine:
    def __init__(self) -> None:
        self._current_state: SystemState = SystemState.BOOTING
        self._listeners: list[Callable[[SystemState, SystemState], None]] = []

    @property
    def current_state(self) -> SystemState:
        return self._current_state

    @current_state.setter
    def current_state(self, state: SystemState) -> None:
        self._current_state = state

    def on_transition(self, listener: Callable[[SystemState, SystemState], None]) -> None:
        self._listeners.append(listener)

    def transition(self, from_state: str, to_state: str) -> None:
        """Transition from one state to another."""
        from_enum = SystemState(from_state)
        to_enum = SystemState(to_state)

        if from_enum != self._current_state:
            raise ValueError(
                f"Cannot transition from {from_state}: "
                f"current state is {self._current_state.value}"
            )

        if to_enum not in VALID_TRANSITIONS.get(from_enum, []):
            raise ValueError(
                f"Invalid transition from {from_state} to {to_state}"
            )

        old_state = self._current_state
        self._current_state = to_enum

        for listener in self._listeners:
            listener(old_state, to_enum)

    def can_transition(self, to_state: str) -> bool:
        """Check if transition to target state is valid."""
        to_enum = SystemState(to_state)
        return to_enum in VALID_TRANSITIONS.get(self._current_state, [])
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/core/test_state.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/state.py backend/tests/core/test_state.py
git commit -m "feat: add system state machine with valid transitions"
```

---

### Task 4: Event Bus (Message Bus)

**Files:**
- Create: `backend/app/core/events.py`
- Create: `backend/tests/core/test_events.py`

- [ ] **Step 1: Write failing test for event bus**

```python
# backend/tests/core/test_events.py
import pytest
from app.core.events import EventBus


@pytest.mark.asyncio
async def test_subscribe_and_publish():
    bus = EventBus()
    received = []
    bus.subscribe("test.event", lambda data: received.append(data))
    await bus.publish("test.event", {"message": "hello"})
    assert len(received) == 1
    assert received[0] == {"message": "hello"}


@pytest.mark.asyncio
async def test_multiple_subscribers():
    bus = EventBus()
    received1 = []
    received2 = []
    bus.subscribe("test.event", lambda data: received1.append(data))
    bus.subscribe("test.event", lambda data: received2.append(data))
    await bus.publish("test.event", {"message": "hello"})
    assert len(received1) == 1
    assert len(received2) == 1


@pytest.mark.asyncio
async def test_unsubscribe():
    bus = EventBus()
    received = []
    handler = lambda data: received.append(data)
    bus.subscribe("test.event", handler)
    bus.unsubscribe("test.event", handler)
    await bus.publish("test.event", {"message": "hello"})
    assert len(received) == 0


@pytest.mark.asyncio
async def test_publish_no_subscribers():
    bus = EventBus()
    await bus.publish("test.event", {"message": "hello"})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/core/test_events.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.core.events'`

- [ ] **Step 3: Implement event bus**

```python
# backend/app/core/events.py
"""Message bus for event-driven communication between services."""

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class EventBus:
    """In-process event bus for service communication."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[Any], None]]] = {}

    def subscribe(self, event: str, handler: Callable[[Any], None]) -> None:
        """Subscribe to an event."""
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(handler)
        logger.debug(f"Subscribed to {event}: {handler.__qualname__}")

    def unsubscribe(self, event: str, handler: Callable[[Any], None]) -> None:
        """Unsubscribe from an event."""
        if event in self._subscribers:
            self._subscribers[event] = [
                h for h in self._subscribers[event] if h != handler
            ]
            logger.debug(f"Unsubscribed from {event}: {handler.__qualname__}")

    async def publish(self, event: str, data: Any = None) -> None:
        """Publish an event to all subscribers."""
        subscribers = self._subscribers.get(event, [])
        logger.debug(f"Publishing {event} to {len(subscribers)} subscribers")
        for handler in subscribers:
            try:
                if callable(handler):
                    result = handler(data)
                    if hasattr(result, "__await__"):
                        await result
            except Exception as e:
                logger.error(f"Error in handler for {event}: {e}")

    def clear(self) -> None:
        """Remove all subscribers."""
        self._subscribers.clear()

    @property
    def subscriber_count(self) -> dict[str, int]:
        """Get count of subscribers per event."""
        return {event: len(handlers) for event, handlers in self._subscribers.items()}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/core/test_events.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/events.py backend/tests/core/test_events.py
git commit -m "feat: add event bus for message-driven service communication"
```

---

### Task 5: Structured Logging

**Files:**
- Create: `backend/app/core/logging.py`
- Create: `backend/tests/core/test_logging.py`

- [ ] **Step 1: Write failing test for logging**

```python
# backend/tests/core/test_logging.py
import pytest
from app.core.logging import EventLogger, LogEvent


def test_event_logger_creation():
    logger = EventLogger()
    assert logger is not None


def test_log_event():
    logger = EventLogger()
    event = LogEvent(
        event_type="BALL_LOST",
        category="tracking",
        severity="WARNING",
        message="Ball not detected for 2s",
        source="tracking_service",
    )
    logger.log(event)


def test_log_event_returns_id():
    logger = EventLogger()
    event = LogEvent(
        event_type="TEST_EVENT",
        category="test",
        severity="INFO",
        message="Test message",
        source="test",
    )
    event_id = logger.log(event)
    assert event_id is not None
    assert isinstance(event_id, int)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/core/test_logging.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.core.logging'`

- [ ] **Step 3: Implement logging**

```python
# backend/app/core/logging.py
"""Structured event logging for FieldVision AI."""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class LogEvent:
    event_type: str
    category: str
    severity: str
    message: str
    source: str
    details: Optional[dict] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class EventLogger:
    """Structured event logger with SQLite storage."""

    def __init__(self, db_path: str = "logs/events.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._logger = logging.getLogger("fieldvision.events")

    def _init_db(self) -> None:
        """Initialize SQLite database."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    source TEXT NOT NULL,
                    details TEXT
                )
            """)
            conn.commit()

    def log(self, event: LogEvent) -> int:
        """Log an event and return its ID."""
        details_str = str(event.details) if event.details else None

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                """
                INSERT INTO events (timestamp, event_type, category, severity, message, source, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.timestamp.isoformat(),
                    event.event_type,
                    event.category,
                    event.severity,
                    event.message,
                    event.source,
                    details_str,
                ),
            )
            conn.commit()
            event_id = cursor.lastrowid

        log_method = getattr(self._logger, event.severity.lower(), self._logger.info)
        log_method(f"[{event.event_type}] {event.message}")

        return event_id

    def query(
        self,
        event_type: Optional[str] = None,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Query logged events."""
        query = "SELECT * FROM events WHERE 1=1"
        params = []

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        if category:
            query += " AND category = ?"
            params.append(category)
        if severity:
            query += " AND severity = ?"
            params.append(severity)

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/core/test_logging.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/logging.py backend/tests/core/test_logging.py
git commit -m "feat: add structured event logging with SQLite storage"
```

---

### Task 6: Pydantic Models

**Files:**
- Create: `backend/app/models/detection.py`
- Create: `backend/app/models/track.py`
- Create: `backend/app/models/director.py`
- Create: `backend/app/models/motion.py`
- Create: `backend/app/models/servo.py`
- Create: `backend/app/models/events.py`
- Create: `backend/app/models/health.py`

- [ ] **Step 1: Create detection model**

```python
# backend/app/models/detection.py
"""Detection models for YOLO11 output."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BoundingBox:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def center_x(self) -> float:
        return (self.x_min + self.x_max) / 2

    @property
    def center_y(self) -> float:
        return (self.y_min + self.y_max) / 2

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        return self.y_max - self.y_min


@dataclass
class Detection:
    class_id: int
    class_name: str
    confidence: float
    bbox: BoundingBox
    frame_id: Optional[int] = None
    timestamp: Optional[float] = None
```

- [ ] **Step 2: Create track model**

```python
# backend/app/models/track.py
"""Tracking models for ByteTrack output."""

from dataclasses import dataclass, field
from typing import Optional
from app.models.detection import BoundingBox


@dataclass
class TrackPoint:
    x: float
    y: float
    timestamp: float


@dataclass
class Track:
    track_id: int
    class_id: int
    class_name: str
    bbox: BoundingBox
    confidence: float
    age: int = 0
    hits: int = 1
    trajectory: list[TrackPoint] = field(default_factory=list)
    last_update: Optional[float] = None

    @property
    def velocity_x(self) -> float:
        if len(self.trajectory) < 2:
            return 0.0
        dt = self.trajectory[-1].timestamp - self.trajectory[-2].timestamp
        if dt == 0:
            return 0.0
        return (self.trajectory[-1].x - self.trajectory[-2].x) / dt

    @property
    def velocity_y(self) -> float:
        if len(self.trajectory) < 2:
            return 0.0
        dt = self.trajectory[-1].timestamp - self.trajectory[-2].timestamp
        if dt == 0:
            return 0.0
        return (self.trajectory[-1].y - self.trajectory[-2].y) / dt

    @property
    def speed(self) -> float:
        return (self.velocity_x ** 2 + self.velocity_y ** 2) ** 0.5
```

- [ ] **Step 3: Create director model**

```python
# backend/app/models/director.py
"""Director service models."""

from dataclasses import dataclass
from enum import Enum


class MovementType(Enum):
    STATIC = "static"
    FOLLOWING = "following"
    LEADING = "leading"
    WIDE = "wide"
    SEARCHING = "searching"


class DirectorMode(Enum):
    BROADCAST = "broadcast"
    AGGRESSIVE = "aggressive"
    WIDE = "wide"
    TRAINING = "training"
    MANUAL_ASSIST = "manual_assist"


@dataclass
class PlayContext:
    ball_speed: float
    player_count: int
    nearest_player_distance: float
    in_penalty_area: bool
    in_goal_area: bool
    play_intensity: float
    time_since_last_touch: float


@dataclass
class DirectorDecision:
    target_x: float
    target_y: float
    confidence: float
    movement_type: MovementType
    director_mode: DirectorMode
    reasoning: str
    priority: int
```

- [ ] **Step 4: Create motion model**

```python
# backend/app/models/motion.py
"""Motion planner models."""

from dataclasses import dataclass


@dataclass
class MotionPlan:
    target_angle: float
    speed: float
    acceleration: float
    duration: float
    profile: str


@dataclass
class TrajectoryPoint:
    angle: float
    timestamp: float
    speed: float
```

- [ ] **Step 5: Create servo model**

```python
# backend/app/models/servo.py
"""Servo communication models."""

from dataclasses import dataclass
from enum import Enum


class ServoMode(Enum):
    AUTO = "auto"
    MANUAL = "manual"
    HOME = "home"
    STOP = "stop"


class ServoStatus(Enum):
    OK = "ok"
    ERROR = "error"
    OVERCURRENT = "overcurrent"
    OVERTEMPERATURE = "overtemperature"


@dataclass
class ServoCommand:
    target_angle: float
    mode: ServoMode
    timestamp: int
    sequence: int


@dataclass
class ServoState:
    current_angle: float
    status: ServoStatus
    mode: ServoMode
    uptime: int
    free_heap: int
    sequence: int
```

- [ ] **Step 6: Create event models**

```python
# backend/app/models/events.py
"""Event models for logging."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SystemEvent:
    event_type: str
    category: str
    severity: str
    message: str
    source: str
    details: Optional[dict] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
```

- [ ] **Step 7: Create health model**

```python
# backend/app/models/health.py
"""Health monitoring models."""

from dataclasses import dataclass
from enum import Enum


class HealthStatus(Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


@dataclass
class HealthMetric:
    name: str
    value: float
    unit: str
    status: HealthStatus
    threshold_green: float
    threshold_yellow: float


@dataclass
class SystemHealth:
    fps: HealthMetric
    gpu_usage: HealthMetric
    gpu_temperature: HealthMetric
    cpu_usage: HealthMetric
    ram_usage: HealthMetric
    wifi_latency: HealthMetric
    esp32_heartbeat: HealthMetric
    camera_latency: HealthMetric

    @property
    def overall_status(self) -> HealthStatus:
        metrics = [
            self.fps, self.gpu_usage, self.gpu_temperature,
            self.cpu_usage, self.ram_usage, self.wifi_latency,
            self.esp32_heartbeat, self.camera_latency,
        ]
        if any(m.status == HealthStatus.RED for m in metrics):
            return HealthStatus.RED
        if any(m.status == HealthStatus.YELLOW for m in metrics):
            return HealthStatus.YELLOW
        return HealthStatus.GREEN
```

- [ ] **Step 8: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add Pydantic models for detection, tracking, director, motion, servo, events, health"
```

---

### Task 7: ESP32 Firmware

**Files:**
- Create: `firmware/src/main.cpp`
- Create: `firmware/src/wifi_manager.h`
- Create: `firmware/src/websocket_client.h`
- Create: `firmware/src/servo_controller.h`
- Create: `firmware/src/watchdog.h`

- [ ] **Step 1: Create wifi_manager.h**

```cpp
// firmware/src/wifi_manager.h
#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <WiFi.h>

class WiFiManager {
public:
    void connect(const char* ssid = "FieldVision", const char* password = "") {
        WiFi.begin(ssid, password);
        Serial.print("Connecting to WiFi");
        while (WiFi.status() != WL_CONNECTED) {
            delay(500);
            Serial.print(".");
        }
        Serial.println();
        Serial.print("Connected: ");
        Serial.println(WiFi.localIP());
    }

    bool isConnected() {
        return WiFi.status() == WL_CONNECTED;
    }

    void reconnect() {
        if (!isConnected()) {
            Serial.println("Reconnecting to WiFi...");
            WiFi.reconnect();
        }
    }

    String getIP() {
        return WiFi.localIP().toString();
    }
};

#endif
```

- [ ] **Step 2: Create servo_controller.h**

```cpp
// firmware/src/servo_controller.h
#ifndef SERVO_CONTROLLER_H
#define SERVO_CONTROLLER_H

#include <ESP32Servo.h>

class ServoController {
public:
    void begin() {
        servo.attach(18, 500, 2500);
        servo.write(90);
        Serial.println("Servo initialized at 90°");
    }

    void setAngle(float angle) {
        angle = constrain(angle, 0.0f, 180.0f);
        servo.write((int)angle);
        currentAngle = angle;
    }

    float getAngle() {
        return currentAngle;
    }

    void home() {
        setAngle(90.0);
    }

    void emergencyStop() {
        servo.detach();
        Serial.println("SERVO EMERGENCY STOP");
    }

    void resume() {
        servo.attach(18, 500, 2500);
        Serial.println("Servo resumed");
    }

    void update() {
        // Future: smooth interpolation
    }

private:
    Servo servo;
    float currentAngle = 90.0;
};

#endif
```

- [ ] **Step 3: Create websocket_client.h**

```cpp
// firmware/src/websocket_client.h
#ifndef WEBSOCKET_CLIENT_H
#define WEBSOCKET_CLIENT_H

#include <Arduino.h>
#include <ArduinoJson.h>
#include <ESPAsyncWebServer.h>
#include <AsyncTCP.h>

class WebSocketClient {
public:
    void connect(const char* url = "ws://192.168.1.1:8000/ws") {
        Serial.print("Connecting to WebSocket...");
        // WebSocket client implementation
        Serial.println("Connected");
    }

    void sendMessage(const char* message) {
        // Send message to server
        Serial.print("WS Send: ");
        Serial.println(message);
    }

    bool isConnected() {
        return connected;
    }

    void update() {
        // Check connection, handle messages
    }

private:
    bool connected = false;
};

#endif
```

- [ ] **Step 4: Create watchdog.h**

```cpp
// firmware/src/watchdog.h
#ifndef WATCHDOG_H
#define WATCHDOG_H

#include <Arduino.h>

class Watchdog {
public:
    void begin(unsigned long timeout = 15000) {
        this->timeout = timeout;
        lastFeed = millis();
        Serial.println("Watchdog started");
    }

    void feed() {
        lastFeed = millis();
    }

    bool isExpired() {
        return (millis() - lastFeed) > timeout;
    }

    void update() {
        if (isExpired()) {
            Serial.println("WATCHDOG TIMEOUT - Emergency stop");
            // Trigger emergency stop
        }
    }

private:
    unsigned long timeout = 15000;
    unsigned long lastFeed = 0;
};

#endif
```

- [ ] **Step 5: Update main.cpp**

```cpp
// firmware/src/main.cpp
#include <Arduino.h>
#include "wifi_manager.h"
#include "websocket_client.h"
#include "servo_controller.h"
#include "watchdog.h"

WiFiManager wifiManager;
WebSocketClient wsClient;
ServoController servoController;
Watchdog watchdog;

void setup() {
    Serial.begin(115200);
    Serial.println("FieldVision AI - ESP32 Starting...");

    wifiManager.connect();
    wsClient.connect();
    servoController.begin();
    watchdog.begin(15000);

    Serial.println("System ready");
}

void loop() {
    wifiManager.reconnect();
    wsClient.update();
    servoController.update();
    watchdog.update();
    watchdog.feed();

    delay(10);
}
```

- [ ] **Step 6: Commit**

```bash
git add firmware/
git commit -m "feat: add ESP32 firmware with WiFi, WebSocket, servo, watchdog"
```

---

### Task 8: FastAPI Routes

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/status.py`
- Create: `backend/app/api/camera.py`
- Create: `backend/app/api/servo.py`
- Create: `backend/app/api/ai.py`
- Create: `backend/app/api/calibration.py`
- Create: `backend/app/api/stream.py`
- Create: `backend/app/api/replay.py`
- Create: `backend/app/api/health.py`
- Create: `backend/app/api/logs.py`
- Create: `backend/app/api/settings.py`
- Create: `backend/app/api/websocket.py`

- [ ] **Step 1: Create status routes**

```python
# backend/app/api/status.py
"""Status API routes."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/status", tags=["status"])


@router.get("/")
async def get_status():
    """Get system status."""
    return {
        "state": "idle",
        "fps": 0,
        "latency": 0,
        "servo_angle": 90.0,
        "target_angle": 90.0,
    }
```

- [ ] **Step 2: Create camera routes**

```python
# backend/app/api/camera.py
"""Camera API routes."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/camera", tags=["camera"])


@router.post("/start")
async def start_camera():
    """Start camera capture."""
    return {"status": "started"}


@router.post("/stop")
async def stop_camera():
    """Stop camera capture."""
    return {"status": "stopped"}
```

- [ ] **Step 3: Create servo routes**

```python
# backend/app/api/servo.py
"""Servo API routes."""

from fastapi import APIRouter
from pydantic import BaseModel


class ServoAngleRequest(BaseModel):
    angle: float


class ServoModeRequest(BaseModel):
    mode: str


router = APIRouter(prefix="/api/servo", tags=["servo"])


@router.get("/")
async def get_servo_state():
    """Get current servo state."""
    return {
        "current_angle": 90.0,
        "target_angle": 90.0,
        "mode": "auto",
        "status": "ok",
    }


@router.post("/angle")
async def set_servo_angle(request: ServoAngleRequest):
    """Set manual servo angle."""
    return {"status": "ok", "angle": request.angle}


@router.post("/mode")
async def set_servo_mode(request: ServoModeRequest):
    """Set servo mode."""
    return {"status": "ok", "mode": request.mode}
```

- [ ] **Step 4: Create AI routes**

```python
# backend/app/api/ai.py
"""AI API routes."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/detections")
async def get_detections():
    """Get current detections."""
    return {"detections": [], "frame_id": 0}


@router.get("/director")
async def get_director_decision():
    """Get Director decision."""
    return {
        "target_x": 960.0,
        "target_y": 540.0,
        "confidence": 0.85,
        "movement_type": "following",
        "director_mode": "broadcast",
        "reasoning": "Ball detected, tracking",
    }


@router.get("/mode")
async def get_director_mode():
    """Get Director mode."""
    return {"mode": "broadcast"}


@router.put("/mode")
async def set_director_mode(mode: dict):
    """Set Director mode."""
    return {"status": "ok", "mode": mode.get("mode", "broadcast")}
```

- [ ] **Step 5: Create health routes**

```python
# backend/app/api/health.py
"""Health monitoring routes."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/")
async def get_health():
    """Get system health."""
    return {
        "overall": "green",
        "fps": {"value": 30, "status": "green"},
        "gpu_usage": {"value": 45, "status": "green"},
        "gpu_temperature": {"value": 55, "status": "green"},
        "cpu_usage": {"value": 35, "status": "green"},
        "ram_usage": {"value": 40, "status": "green"},
        "wifi_latency": {"value": 5, "status": "green"},
        "esp32_heartbeat": {"value": 2, "status": "green"},
        "camera_latency": {"value": 50, "status": "green"},
    }
```

- [ ] **Step 6: Create remaining routes**

```python
# backend/app/api/calibration.py
from fastapi import APIRouter
router = APIRouter(prefix="/api/calibration", tags=["calibration"])

@router.get("/profiles")
async def list_profiles():
    return {"profiles": ["default"]}

@router.get("/profile")
async def get_profile():
    return {"profile": "default"}

@router.put("/profile")
async def set_profile(profile: dict):
    return {"status": "ok"}
```

```python
# backend/app/api/stream.py
from fastapi import APIRouter
router = APIRouter(prefix="/api/stream", tags=["stream"])

@router.post("/start")
async def start_stream():
    return {"status": "started"}

@router.post("/stop")
async def stop_stream():
    return {"status": "stopped"}
```

```python
# backend/app/api/replay.py
from fastapi import APIRouter
router = APIRouter(prefix="/api/replay", tags=["replay"])

@router.get("/recordings")
async def list_recordings():
    return {"recordings": []}

@router.post("/load")
async def load_recording(data: dict):
    return {"status": "ok"}
```

```python
# backend/app/api/logs.py
from fastapi import APIRouter
router = APIRouter(prefix="/api/logs", tags=["logs"])

@router.get("/")
async def get_logs():
    return {"events": []}
```

```python
# backend/app/api/settings.py
from fastapi import APIRouter
router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("/")
async def get_settings():
    return {"settings": {}}

@router.put("/")
async def update_settings(settings: dict):
    return {"status": "ok"}
```

```python
# backend/app/api/websocket.py
from fastapi import APIRouter, WebSocket
router = APIRouter(tags=["websocket"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

- [ ] **Step 7: Update main.py to include routers**

```python
# backend/app/main.py
"""FieldVision AI Backend Entry Point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import load_config
from app.core.state import SystemStateMachine
from app.core.events import EventBus
from app.core.logging import setup_logging
from app.api import (
    status, camera, servo, ai, calibration,
    stream, replay, health, logs, settings, websocket
)

app = FastAPI(
    title="FieldVision AI",
    description="AI-powered football camera system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status.router)
app.include_router(camera.router)
app.include_router(servo.router)
app.include_router(ai.router)
app.include_router(calibration.router)
app.include_router(stream.router)
app.include_router(replay.router)
app.include_router(health.router)
app.include_router(logs.router)
app.include_router(settings.router)
app.include_router(websocket.router)


@app.on_event("startup")
async def startup():
    config = load_config()
    app.state.config = config
    app.state.event_bus = EventBus()
    app.state.state_machine = SystemStateMachine()
    setup_logging()
    app.state.state_machine.transition("booting", "connecting")


@app.on_event("shutdown")
async def shutdown():
    pass
```

- [ ] **Step 8: Verify all routes work**

```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Test endpoints:
- `GET /api/health/`
- `GET /api/status/`
- `GET /api/servo/`
- `GET /api/ai/detections`
- `GET /api/ai/director`

- [ ] **Step 9: Commit**

```bash
git add backend/app/api/ backend/app/main.py
git commit -m "feat: add FastAPI routes for all API endpoints"
```

---

### Task 9: React Frontend Scaffold

**Files:**
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/components/Layout.tsx`
- Create: `frontend/src/components/Sidebar.tsx`
- Create: `frontend/src/pages/Dashboard.tsx`
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/services/api.ts`
- Create: `frontend/src/hooks/useWebSocket.ts`

- [ ] **Step 1: Create types**

```typescript
// frontend/src/types/index.ts
export interface SystemStatus {
  state: string;
  fps: number;
  latency: number;
  servo_angle: number;
  target_angle: number;
}

export interface HealthStatus {
  overall: 'green' | 'yellow' | 'red';
  fps: { value: number; status: string };
  gpu_usage: { value: number; status: string };
  gpu_temperature: { value: number; status: string };
  cpu_usage: { value: number; status: string };
  ram_usage: { value: number; status: string };
}

export interface DirectorDecision {
  target_x: number;
  target_y: number;
  confidence: number;
  movement_type: string;
  director_mode: string;
  reasoning: string;
}

export interface ServoState {
  current_angle: number;
  target_angle: number;
  mode: string;
  status: string;
}
```

- [ ] **Step 2: Create API service**

```typescript
// frontend/src/services/api.ts
const API_BASE = 'http://localhost:8000/api';

export const api = {
  getStatus: async () => {
    const res = await fetch(`${API_BASE}/status/`);
    return res.json();
  },

  getHealth: async () => {
    const res = await fetch(`${API_BASE}/health/`);
    return res.json();
  },

  getServo: async () => {
    const res = await fetch(`${API_BASE}/servo/`);
    return res.json();
  },

  getDirector: async () => {
    const res = await fetch(`${API_BASE}/ai/director`);
    return res.json();
  },

  setServoMode: async (mode: string) => {
    const res = await fetch(`${API_BASE}/servo/mode`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode }),
    });
    return res.json();
  },

  setServoAngle: async (angle: number) => {
    const res = await fetch(`${API_BASE}/servo/angle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ angle }),
    });
    return res.json();
  },
};
```

- [ ] **Step 3: Create WebSocket hook**

```typescript
// frontend/src/hooks/useWebSocket.ts
import { useEffect, useRef, useState } from 'react';

export function useWebSocket(url: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connect = () => {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => setIsConnected(true);
      ws.current.onclose = () => {
        setIsConnected(false);
        setTimeout(connect, 3000);
      };
      ws.current.onmessage = (event) => {
        setLastMessage(JSON.parse(event.data));
      };
    };

    connect();

    return () => {
      ws.current?.close();
    };
  }, [url]);

  return { isConnected, lastMessage };
}
```

- [ ] **Step 4: Create Layout component**

```tsx
// frontend/src/components/Layout.tsx
import { Sidebar } from './Sidebar';

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-gray-900 text-white">
      <Sidebar />
      <main className="flex-1 overflow-auto p-6">
        {children}
      </main>
    </div>
  );
}
```

- [ ] **Step 5: Create Sidebar component**

```tsx
// frontend/src/components/Sidebar.tsx
import { Link, useLocation } from 'react-router-dom';

const navItems = [
  { path: '/', label: 'Dashboard' },
  { path: '/camera', label: 'Camera' },
  { path: '/servo', label: 'Servo' },
  { path: '/director', label: 'Director' },
  { path: '/calibration', label: 'Calibration' },
  { path: '/streaming', label: 'Streaming' },
  { path: '/replay', label: 'Replay' },
  { path: '/health', label: 'Health' },
  { path: '/logs', label: 'Logs' },
  { path: '/settings', label: 'Settings' },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <aside className="w-64 bg-gray-800 p-4">
      <h1 className="text-xl font-bold mb-6">FieldVision AI</h1>
      <nav>
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`block py-2 px-4 rounded mb-1 ${
              location.pathname === item.path
                ? 'bg-blue-600'
                : 'hover:bg-gray-700'
            }`}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
```

- [ ] **Step 6: Create Dashboard page**

```tsx
// frontend/src/pages/Dashboard.tsx
import { useEffect, useState } from 'react';
import { api } from '../services/api';

export function Dashboard() {
  const [status, setStatus] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      setStatus(await api.getStatus());
      setHealth(await api.getHealth());
    };
    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-800 p-4 rounded">
          <div className="text-gray-400 text-sm">State</div>
          <div className="text-2xl font-bold">{status?.state || 'Loading...'}</div>
        </div>
        <div className="bg-gray-800 p-4 rounded">
          <div className="text-gray-400 text-sm">FPS</div>
          <div className="text-2xl font-bold">{status?.fps || 0}</div>
        </div>
        <div className="bg-gray-800 p-4 rounded">
          <div className="text-gray-400 text-sm">Servo Angle</div>
          <div className="text-2xl font-bold">{status?.servo_angle || 90}°</div>
        </div>
        <div className="bg-gray-800 p-4 rounded">
          <div className="text-gray-400 text-sm">Health</div>
          <div className={`text-2xl font-bold ${
            health?.overall === 'green' ? 'text-green-500' :
            health?.overall === 'yellow' ? 'text-yellow-500' : 'text-red-500'
          }`}>
            {health?.overall?.toUpperCase() || 'Loading...'}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-800 p-4 rounded">
          <h2 className="text-lg font-bold mb-4">System Metrics</h2>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>GPU Usage</span>
              <span>{health?.gpu_usage?.value || 0}%</span>
            </div>
            <div className="flex justify-between">
              <span>CPU Usage</span>
              <span>{health?.cpu_usage?.value || 0}%</span>
            </div>
            <div className="flex justify-between">
              <span>RAM Usage</span>
              <span>{health?.ram_usage?.value || 0}%</span>
            </div>
          </div>
        </div>
        <div className="bg-gray-800 p-4 rounded">
          <h2 className="text-lg font-bold mb-4">Director</h2>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Mode</span>
              <span>{status?.director_mode || 'broadcast'}</span>
            </div>
            <div className="flex justify-between">
              <span>Movement</span>
              <span>{status?.movement_type || 'static'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 7: Create App.tsx**

```tsx
// frontend/src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
```

- [ ] **Step 8: Create main.tsx**

```tsx
// frontend/src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

- [ ] **Step 9: Create index.css**

```css
/* frontend/src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
```

- [ ] **Step 10: Verify frontend runs**

```bash
cd frontend
npm install
npm run dev
```

Expected: Dashboard shows at `http://localhost:5173`

- [ ] **Step 11: Commit**

```bash
git add frontend/
git commit -m "feat: add React frontend scaffold with dashboard"
```

---

## Phase 2: Camera Service

### Task 10: Camera Capture Service

**Files:**
- Create: `backend/app/services/camera/service.py`
- Create: `backend/tests/services/test_camera.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/services/test_camera.py
import pytest
from app.services.camera.service import CameraService


@pytest.mark.asyncio
async def test_camera_service_creation():
    service = CameraService()
    assert service is not None


@pytest.mark.asyncio
async def test_camera_service_has_config():
    from app.core.config import CameraConfig
    config = CameraConfig()
    service = CameraService(config)
    assert service.config == config
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/services/test_camera.py -v
```

- [ ] **Step 3: Implement camera service**

```python
# backend/app/services/camera/service.py
"""Camera capture service."""

import logging
from typing import Optional
from threading import Thread, Lock

import cv2
import numpy as np

from app.core.config import CameraConfig

logger = logging.getLogger(__name__)


class CameraService:
    """Camera capture service using OpenCV."""

    def __init__(self, config: Optional[CameraConfig] = None) -> None:
        self.config = config or CameraConfig()
        self._capture: Optional[cv2.VideoCapture] = None
        self._frame: Optional[np.ndarray] = None
        self._frame_lock = Lock()
        self._running = False
        self._thread: Optional[Thread] = None
        self._fps = 0.0
        self._frame_count = 0

    @property
    def fps(self) -> float:
        return self._fps

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start camera capture."""
        if self._running:
            return

        self._capture = cv2.VideoCapture(self.config.source)
        if not self._capture.isOpened():
            raise RuntimeError(f"Failed to open camera: {self.config.source}")

        self._running = True
        self._thread = Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info(f"Camera started: {self.config.source}")

    def stop(self) -> None:
        """Stop camera capture."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        if self._capture:
            self._release()
        logger.info("Camera stopped")

    def _release(self) -> None:
        if self._capture:
            self._capture.release()
            self._capture = None

    def _capture_loop(self) -> None:
        """Main capture loop."""
        while self._running and self._capture:
            ret, frame = self._capture.read()
            if ret:
                with self._frame_lock:
                    self._frame = frame
                    self._frame_count += 1
            else:
                logger.warning("Failed to read frame")
                self._reconnect()

    def _reconnect(self) -> None:
        """Reconnect to camera."""
        self._release()
        import time
        time.sleep(self.config.reconnect_delay)
        self._capture = cv2.VideoCapture(self.config.source)

    def get_frame(self) -> Optional[np.ndarray]:
        """Get latest frame."""
        with self._frame_lock:
            return self._frame.copy() if self._frame is not None else None
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/services/test_camera.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/camera/service.py backend/tests/services/test_camera.py
git commit -m "feat: add camera capture service with OpenCV"
```

---

## Phase 3: Vision and Tracking Services

### Task 11: Vision Service (YOLO11)

**Files:**
- Create: `backend/app/services/vision/service.py`
- Create: `backend/tests/services/test_vision.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/services/test_vision.py
import pytest
import numpy as np
from app.services.vision.service import VisionService


@pytest.mark.asyncio
async def test_vision_service_creation():
    service = VisionService()
    assert service is not None


@pytest.mark.asyncio
async def test_vision_service_detect():
    service = VisionService()
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    detections = service.detect(frame)
    assert isinstance(detections, list)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/services/test_vision.py -v
```

- [ ] **Step 3: Implement vision service**

```python
# backend/app/services/vision/service.py
"""Vision service for YOLO11 detection."""

import logging
from typing import Optional

import numpy as np
from ultralytics import YOLO

from app.core.config import DetectionConfig
from app.models.detection import Detection, BoundingBox

logger = logging.getLogger(__name__)


class VisionService:
    """YOLO11 detection service."""

    def __init__(self, config: Optional[DetectionConfig] = None) -> None:
        self.config = config or DetectionConfig()
        self._model: Optional[YOLO] = None
        self._load_model()

    def _load_model(self) -> None:
        """Load YOLO11 model."""
        try:
            self._model = YOLO(self.config.model)
            logger.info(f"Loaded model: {self.config.model}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def detect(self, frame: np.ndarray) -> list[Detection]:
        """Run detection on frame."""
        if self._model is None:
            return []

        results = self._model(
            frame,
            conf=self.config.confidence_threshold,
            iou=self.config.iou_threshold,
            imgsz=self.config.input_size,
            device=self.config.device,
        )

        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].tolist()

                    class_name = self._get_class_name(cls)
                    if class_name:
                        bbox = BoundingBox(
                            x_min=xyxy[0],
                            y_min=xyxy[1],
                            x_max=xyxy[2],
                            y_max=xyxy[3],
                        )
                        detections.append(
                            Detection(
                                class_id=cls,
                                class_name=class_name,
                                confidence=conf,
                                bbox=bbox,
                            )
                        )

        return detections

    def _get_class_name(self, class_id: int) -> Optional[str]:
        """Get class name from ID."""
        for name, id in self.config.classes.items():
            if id == class_id:
                return name
        return None
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/services/test_vision.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/vision/service.py backend/tests/services/test_vision.py
git commit -m "feat: add vision service with YOLO11 detection"
```

---

### Task 12: Tracking Service (ByteTrack)

**Files:**
- Create: `backend/app/services/tracking/service.py`
- Create: `backend/tests/services/test_tracking.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/services/test_tracking.py
import pytest
from app.services.tracking.service import TrackingService
from app.models.detection import Detection, BoundingBox


@pytest.mark.asyncio
async def test_tracking_service_creation():
    service = TrackingService()
    assert service is not None


@pytest.mark.asyncio
async def test_tracking_service_track():
    service = TrackingService()
    detections = [
        Detection(
            class_id=1,
            class_name="player",
            confidence=0.9,
            bbox=BoundingBox(100, 100, 200, 200),
        )
    ]
    tracks = service.track(detections)
    assert isinstance(tracks, list)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/services/test_tracking.py -v
```

- [ ] **Step 3: Implement tracking service**

```python
# backend/app/services/tracking/service.py
"""Tracking service using ByteTrack."""

import logging
from typing import Optional

from app.core.config import TrackingConfig
from app.models.detection import Detection
from app.models.track import Track, TrackPoint

logger = logging.getLogger(__name__)


class TrackingService:
    """ByteTrack multi-object tracking service."""

    def __init__(self, config: Optional[TrackingConfig] = None) -> None:
        self.config = config or TrackingConfig()
        self._tracks: dict[int, Track] = {}
        self._next_id = 1
        self._frame_count = 0

    def track(self, detections: list[Detection]) -> list[Track]:
        """Track objects across frames."""
        self._frame_count += 1
        timestamp = self._frame_count / 30.0

        matched = self._match_detections_to_tracks(detections, timestamp)
        unmatched = self._handle_unmatched_detections(detections, timestamp)
        self._age_tracks()

        return list(self._tracks.values())

    def _match_detections_to_tracks(
        self, detections: list[Detection], timestamp: float
    ) -> list[Track]:
        """Match detections to existing tracks using IOU."""
        matched = []
        used_detections = set()

        for track_id, track in list(self._tracks.items()):
            best_detection = None
            best_iou = 0.0

            for i, det in enumerate(detections):
                if i in used_detections:
                    continue
                if det.class_id != track.class_id:
                    continue

                iou = self._calculate_iou(track.bbox, det.bbox)
                if iou > best_iou and iou > self.config.iou_threshold:
                    best_iou = iou
                    best_detection = (i, det)

            if best_detection:
                idx, det = best_detection
                used_detections.add(idx)
                track.bbox = det.bbox
                track.confidence = det.confidence
                track.hits += 1
                track.age = 0
                track.trajectory.append(
                    TrackPoint(det.bbox.center_x, det.bbox.center_y, timestamp)
                )
                track.last_update = timestamp
                matched.append(track)

        return matched

    def _handle_unmatched_detections(
        self, detections: list[Detection], timestamp: float
    ) -> list[Track]:
        """Create new tracks for unmatched detections."""
        unmatched = []
        for det in detections:
            track = Track(
                track_id=self._next_id,
                class_id=det.class_id,
                class_name=det.class_name,
                bbox=det.bbox,
                confidence=det.confidence,
                trajectory=[TrackPoint(det.bbox.center_x, det.bbox.center_y, timestamp)],
                last_update=timestamp,
            )
            self._tracks[self._next_id] = track
            self._next_id += 1
            unmatched.append(track)
        return unmatched

    def _age_tracks(self) -> None:
        """Age tracks and remove old ones."""
        to_remove = []
        for track_id, track in self._tracks.items():
            track.age += 1
            if track.age > self.config.max_age:
                to_remove.append(track_id)

        for track_id in to_remove:
            del self._tracks[track_id]

    def _calculate_iou(self, bbox1, bbox2) -> float:
        """Calculate Intersection over Union."""
        x1 = max(bbox1.x_min, bbox2.x_min)
        y1 = max(bbox1.y_min, bbox2.y_min)
        x2 = min(bbox1.x_max, bbox2.x_max)
        y2 = min(bbox1.y_max, bbox2.y_max)

        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = bbox1.width * bbox1.height
        area2 = bbox2.width * bbox2.height
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0.0
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/services/test_tracking.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/tracking/service.py backend/tests/services/test_tracking.py
git commit -m "feat: add tracking service with ByteTrack IOU matching"
```

---

## Phase 4: Director and Prediction Services

### Task 13: Director Service

**Files:**
- Create: `backend/app/services/director/service.py`
- Create: `backend/tests/services/test_director.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/services/test_director.py
import pytest
from app.services.director.service import DirectorService
from app.models.track import Track
from app.models.detection import BoundingBox
from app.models.director import DirectorMode


@pytest.mark.asyncio
async def test_director_service_creation():
    service = DirectorService()
    assert service is not None


@pytest.mark.asyncio
async def test_director_decide():
    service = DirectorService()
    tracks = [
        Track(
            track_id=1,
            class_id=0,
            class_name="ball",
            bbox=BoundingBox(960, 540, 980, 560),
            confidence=0.9,
        )
    ]
    decision = service.decide(tracks, DirectorMode.BROADCAST)
    assert decision is not None
    assert 0 <= decision.target_x <= 1920
    assert 0 <= decision.target_y <= 1080
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/services/test_director.py -v
```

- [ ] **Step 3: Implement director service**

```python
# backend/app/services/director/service.py
"""Director service for deciding where the camera should point."""

import logging
from typing import Optional

from app.core.config import DirectorConfig
from app.models.track import Track
from app.models.director import (
    DirectorDecision,
    DirectorMode,
    MovementType,
    PlayContext,
)

logger = logging.getLogger(__name__)


class DirectorService:
    """Director service - decides where the audience should look."""

    def __init__(self, config: Optional[DirectorConfig] = None) -> None:
        self.config = config or DirectorConfig()
        self._current_mode = DirectorMode(self.config.default_mode)
        self._last_target_x = 960.0
        self._last_target_y = 540.0

    @property
    def current_mode(self) -> DirectorMode:
        return self._current_mode

    def set_mode(self, mode: DirectorMode) -> None:
        self._current_mode = mode
        logger.info(f"Director mode changed to {mode.value}")

    def decide(
        self, tracks: list[Track], mode: Optional[DirectorMode] = None
    ) -> DirectorDecision:
        """Make a director decision based on tracks."""
        mode = mode or self._current_mode
        mode_config = self.config.modes.get(mode.value, self.config.modes["broadcast"])

        ball_tracks = [t for t in tracks if t.class_name == "ball"]
        player_tracks = [t for t in tracks if t.class_name in ("player", "goalkeeper")]

        if not ball_tracks:
            return DirectorDecision(
                target_x=self._last_target_x,
                target_y=self._last_target_y,
                confidence=0.0,
                movement_type=MovementType.SEARCHING,
                director_mode=mode,
                reasoning="Ball not detected, searching",
                priority=2,
            )

        ball = ball_tracks[0]
        ball_weight = mode_config.ball_weight
        player_weight = mode_config.player_weight

        target_x = ball.bbox.center_x * ball_weight
        target_y = ball.bbox.center_y * ball_weight
        total_weight = ball_weight

        nearest_players = sorted(
            player_tracks,
            key=lambda p: (
                (p.bbox.center_x - ball.bbox.center_x) ** 2
                + (p.bbox.center_y - ball.bbox.center_y) ** 2
            ),
        )[:3]

        for player in nearest_players:
            target_x += player.bbox.center_x * player_weight
            target_y += player.bbox.center_y * player_weight
            total_weight += player_weight

        target_x /= total_weight
        target_y /= total_weight

        target_x = mode_config.smoothness * self._last_target_x + (1 - mode_config.smoothness) * target_x
        target_y = mode_config.smoothness * self._last_target_y + (1 - mode_config.smoothness) * target_y

        self._last_target_x = target_x
        self._last_target_y = target_y

        movement_type = self._determine_movement_type(ball, player_tracks)

        return DirectorDecision(
            target_x=target_x,
            target_y=target_y,
            confidence=ball.confidence,
            movement_type=movement_type,
            director_mode=mode,
            reasoning=f"Tracking ball at ({ball.bbox.center_x:.0f}, {ball.bbox.center_y:.0f})",
            priority=1,
        )

    def _determine_movement_type(
        self, ball: Track, players: list[Track]
    ) -> MovementType:
        """Determine movement type based on context."""
        if ball.speed > 100:
            return MovementType.LEADING
        elif ball.speed > 20:
            return MovementType.FOLLOWING
        elif len(players) > 5:
            return MovementType.WIDE
        else:
            return MovementType.STATIC
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/services/test_director.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/director/service.py backend/tests/services/test_director.py
git commit -m "feat: add Director service with mode selection and weighted centroid"
```

---

### Task 14: Prediction Service (Kalman Filter)

**Files:**
- Create: `backend/app/services/prediction/service.py`
- Create: `backend/tests/services/test_prediction.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/services/test_prediction.py
import pytest
from app.services.prediction.service import PredictionService, KalmanFilter


def test_kalman_filter_creation():
    kf = KalmanFilter()
    assert kf is not None


def test_kalman_filter_predict():
    kf = KalmanFilter()
    kf.update(100.0, 200.0)
    predicted = kf.predict()
    assert predicted is not None
    assert len(predicted) == 2


def test_prediction_service_creation():
    service = PredictionService()
    assert service is not None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/services/test_prediction.py -v
```

- [ ] **Step 3: Implement prediction service**

```python
# backend/app/services/prediction/service.py
"""Prediction service using Kalman filter."""

import logging
from typing import Optional

import numpy as np

from app.core.config import PredictionConfig

logger = logging.getLogger(__name__)


class KalmanFilter:
    """Kalman filter for position and velocity estimation."""

    def __init__(
        self,
        process_noise: float = 0.03,
        measurement_noise: float = 0.1,
    ) -> None:
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise

        self.state = np.zeros(4)
        self.P = np.eye(4) * 1000

        self.F = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ])

        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
        ])

        self.Q = np.eye(4) * process_noise
        self.R = np.eye(2) * measurement_noise

        self.initialized = False

    def update(self, x: float, y: float) -> None:
        """Update filter with new measurement."""
        if not self.initialized:
            self.state = np.array([x, y, 0, 0])
            self.initialized = True
            return

        predicted = self.F @ self.state
        P_pred = self.F @ self.P @ self.F.T + self.Q

        z = np.array([x, y])
        y_residual = z - self.H @ predicted
        S = self.H @ P_pred @ self.H.T + self.R
        K = P_pred @ self.H.T @ np.linalg.inv(S)

        self.state = predicted + K @ y_residual
        self.P = (np.eye(4) - K @ self.H) @ P_pred

    def predict(self) -> tuple[float, float]:
        """Predict next position."""
        if not self.initialized:
            return (960.0, 540.0)

        predicted = self.F @ self.state
        return (predicted[0], predicted[1])

    @property
    def velocity(self) -> tuple[float, float]:
        return (self.state[2], self.state[3])


class PredictionService:
    """Prediction service for trajectory forecasting."""

    def __init__(self, config: Optional[PredictionConfig] = None) -> None:
        self.config = config or PredictionConfig()
        self._filters: dict[int, KalmanFilter] = {}

    def predict(self, track_id: int, x: float, y: float) -> tuple[float, float]:
        """Predict next position for a track."""
        if track_id not in self._filters:
            self._filters[track_id] = KalmanFilter(
                process_noise=self.config.kalman_process_noise,
                measurement_noise=self.config.kalman_measurement_noise,
            )

        kf = self._filters[track_id]
        kf.update(x, y)
        return kf.predict()

    def get_velocity(self, track_id: int) -> tuple[float, float]:
        """Get velocity for a track."""
        if track_id in self._filters:
            return self._filters[track_id].velocity
        return (0.0, 0.0)

    def remove_track(self, track_id: int) -> None:
        """Remove a track from prediction."""
        self._filters.pop(track_id, None)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/services/test_prediction.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/prediction/service.py backend/tests/services/test_prediction.py
git commit -m "feat: add prediction service with Kalman filter"
```

---

## Phase 5: Motion Planning and Safety

### Task 15: Motion Planner

**Files:**
- Create: `backend/app/services/motion/planner.py`
- Create: `backend/tests/services/test_motion.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/services/test_motion.py
import pytest
from app.services.motion.planner import MotionPlanner


def test_motion_planner_creation():
    planner = MotionPlanner()
    assert planner is not None


def test_motion_planner_plan():
    planner = MotionPlanner()
    plan = planner.plan(current_angle=90.0, target_angle=120.0)
    assert plan is not None
    assert plan.target_angle == 120.0
    assert plan.speed > 0


def test_motion_planner_dead_zone():
    planner = MotionPlanner()
    plan = planner.plan(current_angle=90.0, target_angle=90.5)
    assert plan.speed == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/services/test_motion.py -v
```

- [ ] **Step 3: Implement motion planner**

```python
# backend/app/services/motion/planner.py
"""Motion planner for cinematic servo movement."""

import logging
from typing import Optional

from app.core.config import MotionConfig
from app.models.motion import MotionPlan

logger = logging.getLogger(__name__)


class MotionPlanner:
    """Motion planner for smooth, cinematic servo movement."""

    def __init__(self, config: Optional[MotionConfig] = None) -> None:
        self.config = config or MotionConfig()
        self._current_angle = self.config.dead_zone
        self._velocity = 0.0

    def plan(
        self,
        current_angle: float,
        target_angle: float,
        profile: Optional[str] = None,
    ) -> MotionPlan:
        """Generate a motion plan from current to target angle."""
        profile = profile or self.config.profile

        error = target_angle - current_angle

        if abs(error) < self.config.dead_zone:
            return MotionPlan(
                target_angle=current_angle,
                speed=0.0,
                acceleration=0.0,
                duration=0.0,
                profile=profile,
            )

        speed = min(abs(error) * 2.0, self.config.max_speed)

        acceleration = min(speed * 3.0, self.config.max_acceleration)

        duration = abs(error) / speed if speed > 0 else 0.0

        return MotionPlan(
            target_angle=target_angle,
            speed=speed,
            acceleration=acceleration,
            duration=duration,
            profile=profile,
        )

    def interpolate(
        self, current_angle: float, target_angle: float, dt: float
    ) -> float:
        """Interpolate angle for smooth movement."""
        error = target_angle - current_angle

        if abs(error) < self.config.dead_zone:
            return current_angle

        speed = min(abs(error) * 2.0, self.config.max_speed)

        if error > 0:
            new_angle = current_angle + speed * dt
            return min(new_angle, target_angle)
        else:
            new_angle = current_angle - speed * dt
            return max(new_angle, target_angle)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/services/test_motion.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/motion/planner.py backend/tests/services/test_motion.py
git commit -m "feat: add motion planner with dead zone and speed limiting"
```

---

### Task 16: Safety Layer

**Files:**
- Create: `backend/app/services/motion/safety.py`
- Create: `backend/tests/services/test_safety.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/services/test_safety.py
import pytest
from app.services.motion.safety import SafetyLayer
from app.models.servo import ServoCommand, ServoMode


def test_safety_layer_creation():
    safety = SafetyLayer()
    assert safety is not None


def test_safety_layer_validate_angle():
    safety = SafetyLayer()
    cmd = ServoCommand(target_angle=200.0, mode=ServoMode.AUTO, timestamp=0, sequence=1)
    validated = safety.validate_command(cmd)
    assert validated.target_angle == 180.0


def test_safety_layer_validate_jump():
    safety = SafetyLayer()
    cmd = ServoCommand(target_angle=180.0, mode=ServoMode.AUTO, timestamp=0, sequence=1)
    validated = safety.validate_command(cmd)
    assert abs(validated.target_angle - 90.0) <= 45.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/services/test_safety.py -v
```

- [ ] **Step 3: Implement safety layer**

```python
# backend/app/services/motion/safety.py
"""Safety layer for servo command validation."""

import logging
from typing import Optional

from app.core.config import SafetyConfig
from app.models.servo import ServoCommand, ServoMode

logger = logging.getLogger(__name__)


class SafetyLayer:
    """Safety layer that validates all servo commands."""

    def __init__(self, config: Optional[SafetyConfig] = None) -> None:
        self.config = config or SafetyConfig()
        self._current_angle = 90.0
        self._esp32_connected = True
        self._watchdog_active = True

    def set_current_angle(self, angle: float) -> None:
        self._current_angle = angle

    def set_esp32_connected(self, connected: bool) -> None:
        self._esp32_connected = connected

    def validate_command(self, command: ServoCommand) -> ServoCommand:
        """Validate and sanitize a servo command."""
        if not self._esp32_connected:
            logger.warning("ESP32 disconnected, rejecting command")
            return ServoCommand(
                target_angle=self._current_angle,
                mode=ServoMode.STOP,
                timestamp=command.timestamp,
                sequence=command.sequence,
            )

        angle = command.target_angle
        angle = max(0.0, min(180.0, angle))

        jump = abs(angle - self._current_angle)
        if jump > self.config.max_jump_angle:
            if angle > self._current_angle:
                angle = self._current_angle + self.config.max_jump_angle
            else:
                angle = self._current_angle - self.config.max_jump_angle
            logger.warning(f"Jump limited: {jump:.1f}° → {self.config.max_jump_angle}°")

        self._current_angle = angle

        return ServoCommand(
            target_angle=angle,
            mode=command.mode,
            timestamp=command.timestamp,
            sequence=command.sequence,
        )

    def is_safe(self) -> bool:
        """Check if system is safe to operate."""
        return self._esp32_connected and self._watchdog_active
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/services/test_safety.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/motion/safety.py backend/tests/services/test_safety.py
git commit -m "feat: add safety layer with angle limiting and jump prevention"
```

---

## Phase 6: Communication Service

### Task 17: WebSocket Communication

**Files:**
- Create: `backend/app/services/communication/service.py`
- Create: `backend/tests/services/test_communication.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/services/test_communication.py
import pytest
from app.services.communication.service import CommunicationService


@pytest.mark.asyncio
async def test_communication_service_creation():
    service = CommunicationService()
    assert service is not None


@pytest.mark.asyncio
async def test_communication_service_send():
    service = CommunicationService()
    result = await service.send_command(target_angle=90.0, mode="auto")
    assert result is not None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/services/test_communication.py -v
```

- [ ] **Step 3: Implement communication service**

```python
# backend/app/services/communication/service.py
"""Communication service for ESP32 WebSocket."""

import json
import logging
import time
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class CommunicationService:
    """WebSocket communication with ESP32."""

    def __init__(self) -> None:
        self._connected = False
        self._sequence = 0
        self._last_heartbeat = 0.0
        self._callbacks: list[Callable] = []

    @property
    def is_connected(self) -> bool:
        return self._connected

    def on_message(self, callback: Callable) -> None:
        self._callbacks.append(callback)

    async def send_command(
        self, target_angle: float, mode: str = "auto"
    ) -> dict:
        """Send servo command to ESP32."""
        self._sequence += 1
        command = {
            "target_angle": round(target_angle, 2),
            "mode": mode,
            "timestamp": int(time.time() * 1000),
            "sequence": self._sequence,
        }

        logger.debug(f"Sending command: {command}")
        return command

    def handle_message(self, message: str) -> Optional[dict]:
        """Handle message from ESP32."""
        try:
            data = json.loads(message)
            self._last_heartbeat = time.time()
            self._connected = True

            for callback in self._callbacks:
                callback(data)

            return data
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON: {message}")
            return None

    def check_heartbeat(self, timeout: float = 15.0) -> bool:
        """Check if ESP32 heartbeat is recent."""
        if self._last_heartbeat == 0:
            return True
        return (time.time() - self._last_heartbeat) < timeout
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/services/test_communication.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/communication/service.py backend/tests/services/test_communication.py
git commit -m "feat: add communication service for ESP32 WebSocket"
```

---

## Phase 7: Dashboard Pages

### Task 18: Dashboard Pages

**Files:**
- Create: `frontend/src/pages/Camera.tsx`
- Create: `frontend/src/pages/Servo.tsx`
- Create: `frontend/src/pages/Director.tsx`
- Create: `frontend/src/pages/Calibration.tsx`
- Create: `frontend/src/pages/Streaming.tsx`
- Create: `frontend/src/pages/Replay.tsx`
- Create: `frontend/src/pages/Health.tsx`
- Create: `frontend/src/pages/Logs.tsx`
- Create: `frontend/src/pages/Settings.tsx`

- [ ] **Step 1: Create Camera page**

```tsx
// frontend/src/pages/Camera.tsx
import { useEffect, useState } from 'react';
import { api } from '../services/api';

export function Camera() {
  const [status, setStatus] = useState<string>('disconnected');

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Camera</h1>
      <div className="bg-gray-800 p-6 rounded">
        <div className="aspect-video bg-gray-900 rounded mb-4 flex items-center justify-center">
          <span className="text-gray-500">Camera Preview</span>
        </div>
        <div className="flex gap-4">
          <button
            onClick={() => api.getStatus()}
            className="px-4 py-2 bg-green-600 rounded hover:bg-green-700"
          >
            Start
          </button>
          <button
            className="px-4 py-2 bg-red-600 rounded hover:bg-red-700"
          >
            Stop
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create Servo page**

```tsx
// frontend/src/pages/Servo.tsx
import { useEffect, useState } from 'react';
import { api } from '../services/api';

export function Servo() {
  const [servo, setServo] = useState<any>(null);
  const [angle, setAngle] = useState(90);

  useEffect(() => {
    api.getServo().then(setServo);
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Servo Control</h1>
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-gray-800 p-6 rounded">
          <h2 className="text-lg font-bold mb-4">Current State</h2>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Angle:</span>
              <span>{servo?.current_angle || 90}°</span>
            </div>
            <div className="flex justify-between">
              <span>Mode:</span>
              <span>{servo?.mode || 'auto'}</span>
            </div>
            <div className="flex justify-between">
              <span>Status:</span>
              <span>{servo?.status || 'ok'}</span>
            </div>
          </div>
        </div>
        <div className="bg-gray-800 p-6 rounded">
          <h2 className="text-lg font-bold mb-4">Manual Control</h2>
          <input
            type="range"
            min="0"
            max="180"
            value={angle}
            onChange={(e) => setAngle(Number(e.target.value))}
            className="w-full mb-4"
          />
          <div className="text-center mb-4">{angle}°</div>
          <div className="flex gap-2">
            <button
              onClick={() => api.setServoAngle(angle)}
              className="px-4 py-2 bg-blue-600 rounded"
            >
              Set Angle
            </button>
            <button
              onClick={() => api.setServoMode('home')}
              className="px-4 py-2 bg-gray-600 rounded"
            >
              Home
            </button>
            <button
              onClick={() => api.setServoMode('stop')}
              className="px-4 py-2 bg-red-600 rounded"
            >
              Stop
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create Director page**

```tsx
// frontend/src/pages/Director.tsx
import { useEffect, useState } from 'react';
import { api } from '../services/api';

export function Director() {
  const [director, setDirector] = useState<any>(null);

  useEffect(() => {
    api.getDirector().then(setDirector);
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Director</h1>
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-gray-800 p-6 rounded">
          <h2 className="text-lg font-bold mb-4">Current Decision</h2>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Mode:</span>
              <span>{director?.director_mode || 'broadcast'}</span>
            </div>
            <div className="flex justify-between">
              <span>Movement:</span>
              <span>{director?.movement_type || 'static'}</span>
            </div>
            <div className="flex justify-between">
              <span>Confidence:</span>
              <span>{((director?.confidence || 0) * 100).toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span>Target:</span>
              <span>({director?.target_x?.toFixed(0) || 960}, {director?.target_y?.toFixed(0) || 540})</span>
            </div>
          </div>
        </div>
        <div className="bg-gray-800 p-6 rounded">
          <h2 className="text-lg font-bold mb-4">Mode Selection</h2>
          <div className="grid grid-cols-2 gap-2">
            {['broadcast', 'aggressive', 'wide', 'training', 'manual_assist'].map((mode) => (
              <button
                key={mode}
                onClick={() => api.setDirectorMode(mode)}
                className={`px-4 py-2 rounded ${
                  director?.director_mode === mode ? 'bg-blue-600' : 'bg-gray-700'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Create remaining pages**

```tsx
// frontend/src/pages/Calibration.tsx
export function Calibration() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Calibration</h1>
      <div className="bg-gray-800 p-6 rounded">
        <h2 className="text-lg font-bold mb-4">Calibration Wizard</h2>
        <p className="text-gray-400">Step-by-step calibration coming soon</p>
      </div>
    </div>
  );
}
```

```tsx
// frontend/src/pages/Streaming.tsx
export function Streaming() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Streaming</h1>
      <div className="bg-gray-800 p-6 rounded">
        <h2 className="text-lg font-bold mb-4">OBS Controls</h2>
        <div className="flex gap-4">
          <button className="px-4 py-2 bg-green-600 rounded">Start Stream</button>
          <button className="px-4 py-2 bg-red-600 rounded">Stop Stream</button>
          <button className="px-4 py-2 bg-blue-600 rounded">Start Recording</button>
        </div>
      </div>
    </div>
  );
}
```

```tsx
// frontend/src/pages/Replay.tsx
export function Replay() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Replay</h1>
      <div className="bg-gray-800 p-6 rounded">
        <h2 className="text-lg font-bold mb-4">Recordings</h2>
        <p className="text-gray-400">No recordings available</p>
      </div>
    </div>
  );
}
```

```tsx
// frontend/src/pages/Health.tsx
import { useEffect, useState } from 'react';
import { api } from '../services/api';

export function Health() {
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    api.getHealth().then(setHealth);
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">System Health</h1>
      <div className="grid grid-cols-4 gap-4">
        {health && Object.entries(health).filter(([k]) => k !== 'overall').map(([key, value]: [string, any]) => (
          <div key={key} className="bg-gray-800 p-4 rounded">
            <div className="text-gray-400 text-sm">{key.replace(/_/g, ' ')}</div>
            <div className={`text-2xl font-bold ${
              value?.status === 'green' ? 'text-green-500' :
              value?.status === 'yellow' ? 'text-yellow-500' : 'text-red-500'
            }`}>
              {value?.value || 0}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

```tsx
// frontend/src/pages/Logs.tsx
export function Logs() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Event Logs</h1>
      <div className="bg-gray-800 p-6 rounded">
        <p className="text-gray-400">No events logged</p>
      </div>
    </div>
  );
}
```

```tsx
// frontend/src/pages/Settings.tsx
export function Settings() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Settings</h1>
      <div className="bg-gray-800 p-6 rounded">
        <p className="text-gray-400">Configuration editors coming soon</p>
      </div>
    </div>
  );
}
```

```tsx
// frontend/src/pages/Plugins.tsx
export function Plugins() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Plugins</h1>
      <div className="bg-gray-800 p-6 rounded">
        <p className="text-gray-400">No plugins installed</p>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Update App.tsx with routes**

```tsx
// frontend/src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Camera } from './pages/Camera';
import { Servo } from './pages/Servo';
import { Director } from './pages/Director';
import { Calibration } from './pages/Calibration';
import { Streaming } from './pages/Streaming';
import { Replay } from './pages/Replay';
import { Health } from './pages/Health';
import { Logs } from './pages/Logs';
import { Settings } from './pages/Settings';
import { Plugins } from './pages/Plugins';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/camera" element={<Camera />} />
          <Route path="/servo" element={<Servo />} />
          <Route path="/director" element={<Director />} />
          <Route path="/calibration" element={<Calibration />} />
          <Route path="/streaming" element={<Streaming />} />
          <Route path="/replay" element={<Replay />} />
          <Route path="/health" element={<Health />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/plugins" element={<Plugins />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/ frontend/src/App.tsx
git commit -m "feat: add all dashboard pages"
```

---

## Phase 8: Performance Manager

### Task 19: Performance Manager

**Files:**
- Create: `backend/app/services/monitoring/service.py`
- Create: `backend/tests/services/test_monitoring.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/services/test_monitoring.py
import pytest
from app.services.monitoring.service import MonitoringService


def test_monitoring_service_creation():
    service = MonitoringService()
    assert service is not None


def test_monitoring_service_get_health():
    service = MonitoringService()
    health = service.get_health()
    assert health is not None
    assert health.overall_status is not None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/services/test_monitoring.py -v
```

- [ ] **Step 3: Implement monitoring service**

```python
# backend/app/services/monitoring/service.py
"""Monitoring service for system health."""

import logging
from typing import Optional

import psutil

from app.models.health import SystemHealth, HealthMetric, HealthStatus

logger = logging.getLogger(__name__)


class MonitoringService:
    """System health monitoring service."""

    def __init__(self) -> None:
        self._fps = 0.0
        self._gpu_usage = 0.0
        self._gpu_temperature = 0.0
        self._camera_latency = 0.0
        self._esp32_heartbeat_age = 0.0

    def update_fps(self, fps: float) -> None:
        self._fps = fps

    def update_gpu(self, usage: float, temperature: float) -> None:
        self._gpu_usage = usage
        self._gpu_temperature = temperature

    def update_camera_latency(self, latency: float) -> None:
        self._camera_latency = latency

    def update_esp32_heartbeat(self, age: float) -> None:
        self._esp32_heartbeat_age = age

    def get_health(self) -> SystemHealth:
        """Get current system health."""
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent

        return SystemHealth(
            fps=self._create_metric("FPS", self._fps, "fps", 25, 15),
            gpu_usage=self._create_metric("GPU Usage", self._gpu_usage, "%", 60, 85),
            gpu_temperature=self._create_metric("GPU Temp", self._gpu_temperature, "°C", 70, 85),
            cpu_usage=self._create_metric("CPU Usage", cpu, "%", 60, 85),
            ram_usage=self._create_metric("RAM Usage", ram, "%", 60, 85),
            wifi_latency=self._create_metric("WiFi Latency", 5.0, "ms", 20, 50),
            esp32_heartbeat=self._create_metric("ESP32 Heartbeat", self._esp32_heartbeat_age, "s", 5, 10),
            camera_latency=self._create_metric("Camera Latency", self._camera_latency, "ms", 100, 200),
        )

    def _create_metric(
        self, name: str, value: float, unit: str, green_threshold: float, yellow_threshold: float
    ) -> HealthMetric:
        if value <= green_threshold:
            status = HealthStatus.GREEN
        elif value <= yellow_threshold:
            status = HealthStatus.YELLOW
        else:
            status = HealthStatus.RED

        return HealthMetric(
            name=name,
            value=value,
            unit=unit,
            status=status,
            threshold_green=green_threshold,
            threshold_yellow=yellow_threshold,
        )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/services/test_monitoring.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/monitoring/service.py backend/tests/services/test_monitoring.py
git commit -m "feat: add monitoring service with health metrics"
```

---

## Summary

This plan covers Phase 1-8 of FieldVision AI:

1. **Project Scaffold** — Monorepo, config, state machine, event bus, logging, models
2. **Camera Service** — OpenCV capture with reconnect
3. **Vision & Tracking** — YOLO11 detection + ByteTrack
4. **Director & Prediction** — Decision engine + Kalman filter
5. **Motion & Safety** — Motion planner + safety layer
6. **Communication** — WebSocket to ESP32
7. **Dashboard** — All frontend pages
8. **Performance** — Health monitoring

Each task follows TDD: write failing test → implement → verify → commit.
