# FieldVision AI — Complete System Documentation

**Version:** 1.1.0
**Date:** July 2026
**Repository:** https://github.com/MontageStark/VisionFieldAI

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Backend (Python/FastAPI)](#3-backend-pythonfastapi)
4. [Frontend (React/TypeScript)](#4-frontend-reacttypescript)
5. [Android App (Kotlin/Camera2)](#5-android-app-kotlincamera2)
6. [ESP32 Firmware (C++/Arduino)](#6-esp32-firmware-carduino)
7. [Streaming Pipeline](#7-streaming-pipeline)
8. [Configuration System](#8-configuration-system)
9. [API Reference](#9-api-reference)
10. [Event System](#10-event-system)
11. [State Machine](#11-state-machine)
12. [Safety System](#12-safety-system)
13. [Testing](#13-testing)
14. [Getting Started](#14-getting-started)
15. [Deployment](#15-deployment)

---

## 1. System Overview

FieldVision AI is an AI-powered sports broadcasting platform that provides automatic camera framing and virtual camera control for football (soccer) matches. It uses a phone as the camera, a Python backend for AI processing, and drives either a virtual camera (for OBS) or physical servo motors (via ESP32) for automatic pan/tilt tracking.

### Core Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Phone Camera App** | Kotlin, Camera2 API, MJPEG | Capture and stream video |
| **Backend** | Python 3.12, FastAPI, OpenCV, YOLO11, ByteTrack | AI detection, tracking, shot composition |
| **Web Dashboard** | React 18, TypeScript, Vite, TailwindCSS | Monitoring and control interface |
| **ESP32 Firmware** | C++, Arduino, PlatformIO | Physical servo motor control |
| **Configuration** | YAML files, Pydantic Settings | All system parameters |

### Design Principles

- **No Docker** — Runs natively on Windows
- **No Flask** — FastAPI only
- **No global variables** — Event-driven via message bus
- **No blocking loops** — Async/await everywhere
- **No hardcoded values** — All config in YAML files
- **No spaghetti code** — Clean, modular architecture

---

## 2. Architecture

### High-Level Data Flow

```
┌─────────────────────┐
│   Phone Camera App  │
│  (Camera2 + MJPEG)  │
│  Port 8080, UDP 9999│
└─────────┬───────────┘
          │ HTTP MJPEG Stream
          ▼
┌─────────────────────┐
│    HttpCameraSource  │
│  (Auto-connect:     │
│   MJPEG→H264→WebRTC)│
└─────────┬───────────┘
          │ FRAME_CAPTURED event
          ▼
┌─────────────────────┐
│    VisionService     │
│  (YOLO11 GPU infer) │
└─────────┬───────────┘
          │ DETECTIONS_COMPLETE event
          ▼
┌─────────────────────┐
│   TrackingService    │
│  (ByteTrackSort)    │
└─────────┬───────────┘
          │ TRACKING_UPDATED event
          ▼
┌─────────────────────┐     ┌─────────────────────┐
│   DirectorService    │────▶│   PredictionService  │
│  (ShotComposer)     │     │  (KalmanFilter2D)   │
└─────────┬───────────┘     └─────────────────────┘
          │ CAMERA_STATE_UPDATED event
          ▼
┌─────────────────────┐
│    OutputManager     │
│  ┌───────┬───────┐  │
│  │Virtual│ Servo │  │
│  │Camera │ Output│  │
│  └───┬───┴───┬───┘  │
└──────┼───────┼──────┘
       │       │
       ▼       ▼
     OBS     ESP32
           (Servos)
```

### Key Architectural Decision

The AI outputs only `CameraState` with **normalized 0-1 coordinates** (center_x, center_y, zoom). No hardware knowledge leaks into the AI layer. All renderers translate this to device-specific commands.

### Project Structure

```
FieldVision AI/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── core/              # EventBus, StateMachine, Logger
│   │   ├── config/            # YAML loader, Pydantic Settings
│   │   ├── models/            # Pydantic data models
│   │   ├── services/          # 15 service modules
│   │   │   ├── camera/        # Video sources, discovery
│   │   │   ├── vision/        # YOLO11 detection
│   │   │   ├── tracking/      # ByteTrack multi-object tracker
│   │   │   ├── prediction/    # Kalman ball trajectory
│   │   │   ├── director/      # AI shot composition
│   │   │   ├── output/        # Virtual camera, servo, PTZ
│   │   │   ├── motion/        # Safety layer, motion planner
│   │   │   ├── communication/ # ESP32 WebSocket client
│   │   │   └── monitoring/    # Performance manager
│   │   └── api/               # FastAPI routes + DI
│   └── tests/                 # 30+ test files
├── frontend/                   # React 18 dashboard
│   └── src/
│       ├── components/        # Layout, controls, notifications
│       ├── pages/             # 13 page components
│       ├── hooks/             # useApiPolling, useWebSocket
│       ├── services/          # API client, WebSocket client
│       ├── stores/            # Zustand state stores
│       └── types/             # TypeScript interfaces
├── android-app/               # Kotlin Camera2 app
│   └── app/src/main/
│       ├── java/com/fieldvision/camera/
│       │   ├── MainActivity.kt    # Hybrid XML+Compose
│       │   ├── camera/            # Camera2 engine
│       │   ├── ui/                # Compose screens + components
│       │   ├── stream/            # MJPEG server
│       │   ├── network/           # Bandwidth monitor
│       │   └── discovery/         # UDP device discovery
│       └── res/                   # XML layouts, drawables
├── firmware/                   # ESP32 PlatformIO firmware
│   └── src/
│       ├── main.cpp            # Main loop, WebSocket handler
│       ├── servo_controller.h  # DS3235 servo PWM control
│       ├── websocket_client.h  # Backend connection
│       ├── wifi_manager.h      # WiFi STA mode
│       └── watchdog.h          # Hardware watchdog
├── configs/                    # 6 YAML configuration files
│   ├── camera.yaml
│   ├── ai.yaml
│   ├── network.yaml
│   ├── servo.yaml
│   ├── output.yaml
│   └── stream.yaml
├── start.bat                   # One-click launcher
├── opencode.json               # ECC agent configuration
├── AGENTS.md                   # AI agent instructions
├── arch-v1.md                  # Architecture document
└── README.md                   # Project overview
```

---

## 3. Backend (Python/FastAPI)

### Tech Stack

- **Python:** 3.12
- **Framework:** FastAPI with uvicorn
- **AI:** YOLO11 (ultralytics), CUDA GPU
- **Tracking:** ByteTrack (custom implementation with Kalman filter + Hungarian algorithm)
- **Computer Vision:** OpenCV
- **Config:** Pydantic Settings + YAML
- **Testing:** pytest

### Core Layer (`app/core/`)

#### EventBus (`events.py`)
- Pub/sub event system with wildcard support
- Thread-safe (RLock)
- Event history (last 100 events)
- Sync and async publish
- Singleton via `get_event_bus()`

#### StateMachine (`state.py`)
- 9 states: BOOTING → CONNECTING → IDLE → STREAMING → TRACKING → MANUAL → HOMING → EMERGENCY_STOP → ERROR
- Thread-safe (RLock)
- Validated transitions with enter/exit callbacks
- Transition history (last 10)

#### StructuredLogger (`logging.py`)
- JSON formatter for production
- Console formatter with ANSI colors
- Correlation IDs for request tracing
- PerformanceTimer context manager

### Config Layer (`app/config/`)

#### YAML Loader (`loader.py`)
- Merges all `configs/*.yaml` files alphabetically
- Environment variable overrides: `AI__DEVICE=cpu` overrides `ai.device`
- Type coercion: "true"/"false" to bool, numeric strings to int/float
- Thread-safe singleton

#### Settings (`settings.py`)
```python
Settings
├── CameraSettings (source_type, device_id, http_url, resolution, fps, ...)
├── ServoSettings
│   ├── ServoAxisSettings (pan: min/max/default/speed_limit)
│   └── ServoAxisSettings (tilt: min/max/default/speed_limit)
├── NetworkSettings (host, port, cors_origins, esp32_url)
├── AISettings (model_name, confidence, device, max_detections)
├── StreamSettings (enabled, youtube_key, resolution, bitrate, fps)
└── OutputConfig
    ├── VirtualCameraConfig (dead_zone, safe_margin, max_velocity, smoothing)
    ├── ServoOutputConfig (pan/tilt ranges, velocity, acceleration)
    └── PTZOutputConfig (host, port, credentials)
```

### Services Layer (`app/services/`)

#### Camera Services
| Service | File | Purpose |
|---------|------|---------|
| `VideoSource` (ABC) | `video_source.py` | Abstract interface: open/read/release/is_opened/fps/resolution |
| `OpenCVSource` | `opencv_source.py` | USB camera via cv2.VideoCapture, thread-safe |
| `HttpCameraSource` | `http_source.py` | Phone stream via HTTP (MJPEG/H.264/WebRTC auto-negotiation) |
| `FileSource` | `file_source.py` | Video file playback with optional loop |
| `CameraService` | `service.py` | Simple source factory + discovery + auto-connect |
| `CameraService` (threaded) | `camera_service.py` | Background capture loop, latest-frame buffer, auto-reconnect |
| `CameraDiscovery` | `discovery.py` | UDP listener for phone broadcasts on port 9999 |

#### Vision Services
| Service | File | Purpose |
|---------|------|---------|
| `YOLO11Detector` | `detector.py` | YOLO11 model with letterbox preprocessing, GPU memory limits (2GB), simulation mode |
| `VisionService` | `vision_service.py` | Subscribes to FRAME_CAPTURED, runs detection, publishes DETECTIONS_COMPLETE |

#### Tracking Services
| Service | File | Purpose |
|---------|------|---------|
| `ByteTrackSort` | `sorter.py` | ByteTrack: Kalman filter (8-state bbox), two-stage IOU association, Hungarian algorithm |
| `TrackingService` | `tracking_service.py` | Subscribes to DETECTIONS_COMPLETE, runs ByteTrack, publishes TRACKING_UPDATED |

#### Director Services
| Service | File | Purpose |
|---------|------|---------|
| `ShotComposer` | `shot_composer.py` | Rule-based cinematography: weighted centroid, field zones, zoom, shot types |
| `DirectorService` | `director_service.py` | Subscribes to TRACKING_UPDATED, composes shots, publishes CAMERA_STATE_UPDATED |

#### Output Services
| Service | File | Purpose |
|---------|------|---------|
| `OutputPlugin` (ABC) | `base.py` | Interface: apply(CameraState), get_state(), reset(), is_available() |
| `OutputManager` | `manager.py` | Singleton plugin router, hot-swappable modes |
| `VirtualCameraOutput` | `virtual_camera.py` | Software crop/pan/zoom with dead zone filtering, LANCZOS4 interpolation |
| `ServoOutput` | `servo.py` | Normalized coords → pan/tilt angles, trapezoidal velocity profiles |
| `PTZOutput` | `ptz.py` | Stub (not implemented) |

#### Motion Services
| Service | File | Purpose |
|---------|------|---------|
| `smooth.py` | `smooth.py` | Math utilities: easing, lerp, smoothstep, trapezoidal velocity profile |
| `SafetyLayer` | `safety.py` | Angle/jump/speed validation, watchdog, disconnect detection, emergency stop |
| `MotionPlanner` | `motion_planner.py` | Smooth motion plans with velocity limiting, safety validation |

#### Prediction Services
| Service | File | Purpose |
|---------|------|---------|
| `KalmanFilter2D` | `kalman_filter.py` | 4-state (x,y,vx,vy) for ball trajectory, confidence-weighted updates |
| `PredictionService` | `prediction_service.py` | Subscribes to TRACKING_UPDATED, predicts future ball positions |

#### Communication Services
| Service | File | Purpose |
|---------|------|---------|
| `protocol.py` | `protocol.py` | ESP32 command/response serialization (pan/tilt/zoom/heartbeat/home) |
| `ESP32Client` | `esp32_client.py` | Async WebSocket client with auto-reconnect, heartbeat, position feedback |

#### Monitoring Services
| Service | File | Purpose |
|---------|------|---------|
| `PerformanceManager` | `performance_manager.py` | FPS tracking, GPU monitoring, auto-resolution scaling, CPU limiting |

### API Layer (`app/api/`)

21 endpoints total (18 HTTP + 2 health + 1 WebSocket). See [Section 9: API Reference](#9-api-reference) for full details.

### Dependency Injection (`deps.py`)

Four adapter classes wrap real services with mock fallbacks:
- `CameraServiceAdapter` — wraps `camera.service.CameraService`
- `ServoServiceAdapter` — wraps `output.servo.ServoOutput`
- `DirectorServiceAdapter` — wraps `director.director_service.DirectorService`
- `StreamServiceAdapter` — wraps `output.manager.OutputManager`

Each reports `source: "real"` or `source: "mock"` in status.

---

## 4. Frontend (React/TypeScript)

### Tech Stack

- **React:** 18.3.1
- **Language:** TypeScript (strict mode)
- **Build:** Vite 5.3
- **Styling:** TailwindCSS 3.4 (dark mode, custom design tokens)
- **State:** Zustand 4.5
- **Routing:** React Router 6.26
- **HTTP:** Axios
- **Testing:** Vitest + React Testing Library

### Design System

| Token | Value | Usage |
|-------|-------|-------|
| Background | `#0B0F14` | Main app background |
| Surface | `#151A22` | Card backgrounds |
| Card | `#1C2330` | Elevated surfaces |
| Border | `#2A3344` | Dividers |
| Primary | `#3B82F6` | Buttons, links, active states |
| Success | `#10B981` | Online, active, recording |
| Warning | `#F59E0B` | Caution states |
| Error | `#EF4444` | Stopped, emergency |
| Font (sans) | Inter | Body text |
| Font (mono) | JetBrains Mono | Code, logs |

### Layout

```
+------------------+------------------------------------------+
|                  |              Header (h-16)                |
|    Sidebar       |  Page title | LIVE badge | State | API | WS |
|    (w-60)        +------------------------------------------+
|                  |                                          |
|  [FV logo]       |          Main Content Area               |
|  - Dashboard     |          (flex-1, overflow-auto)         |
|  - Camera        |          padding: p-6                    |
|  - AI Director   |          bg-slate-950                    |
|  - Streaming     |                                          |
|  - Hardware      |          <Outlet /> renders              |
|  - Replay        |          current route's page            |
|  - Settings      |                                          |
|  - Logs          |                                          |
|                  |                                          |
|  v1.0.0 footer   |                                          |
+------------------+------------------------------------------+
```

### Pages (13 routes)

| Route | Page | Description | API Status |
|-------|------|-------------|------------|
| `/` | Dashboard | Live camera feed, AI Director panel, 4 metric cards | Mock data |
| `/camera` | Camera | Camera info cards, feed placeholder, action buttons | Mock data |
| `/director` | Director | AI Director control, mode selector (5 modes) | Mock data |
| `/streaming` | Streaming | Stream destinations (RTSP/OBS/YouTube), metrics | Mock data |
| `/servo` | Servo | Pan/tilt display, calibration, emergency stop | **Real API** |
| `/health` | Health | System health monitoring | Placeholder |
| `/logs` | Logs | Log viewer with level/component/search filters | Mock data |
| `/plugins` | Plugins | Plugin marketplace | Placeholder |
| `/calibration` | Calibration | Calibration wizard | Placeholder |
| `/settings` | Settings | 8 tabs (General, Camera, AI, Virtual Camera, Servo, Streaming, OBS, Notifications) | Partial |
| `/virtual-camera` | VirtualCamera | Interactive frame visualization with zoom/dead-zone/motion sliders | Mock data |
| `/hardware` | Hardware | Servo card (polled 1s), PTZ card | **Real API** |
| `*` | — | Redirects to `/` | — |

### Components

| Component | Location | Description |
|-----------|----------|-------------|
| `AppLayout` | `components/layout/` | Shell: sidebar + header + outlet |
| `Header` | `components/layout/` | Top bar with page title, LIVE indicator, system state, connection dots |
| `Sidebar` | `components/layout/` | Left nav with 11 links, FV logo, version footer |
| `FloatingControls` | `components/controls/` | 5-button toolbar (Start/Stop/Snapshot/Record/Settings) |
| `NotificationCenter` | `components/notifications/` | Bell icon with dropdown notification list |
| `ErrorBoundary` | `components/` | Class component catch-all error handler |
| `PagePlaceholder` | `components/common/` | Reusable placeholder for unimplemented pages |

### Hooks

| Hook | File | Description |
|------|------|-------------|
| `useApiPolling` | `hooks/useApiPolling.ts` | Generic polling hook with enable/disable, manual refetch |
| `useWebSocket` | `hooks/useWebSocket.ts` | WebSocket with auto-reconnect (exponential backoff) |

### Services

| Service | File | Description |
|---------|------|-------------|
| `api.ts` | `services/api.ts` | Axios client with 6 namespace objects (systemApi, cameraApi, servoApi, directorApi, streamApi, outputApi) |
| `wsClient` | `services/websocket.ts` | Singleton WebSocket client with reconnect, heartbeat, topic subscription |

### State Stores (Zustand)

| Store | File | State |
|-------|------|-------|
| `useAppStore` | `stores/appStore.ts` | outputMode, lastOutputState, setOutputMode(), fetchOutputState() |
| `useSystemStore` | `stores/systemStore.ts` | apiConnected, wsStatus, systemState, validTransitions, healthStatus |

### TypeScript Types

Key interfaces in `types/api.ts`:
- `SystemState` — Union of 9 state strings
- `HealthStatus` — `'green' | 'yellow' | 'red'`
- `DirectorMode` — 5 mode strings
- `DirectorDecision` — mode, target (CameraAction), reasoning, confidence, timestamp
- `CameraAction` — pan_angle, tilt_angle, zoom, transition_time
- `ServoStatus`, `StreamStatus`, `ComponentHealth`, `SystemHealth`

### Test Coverage

| Metric | Value |
|--------|-------|
| Test files | 15 |
| Total tests | 82 |
| Statement coverage | 97.2% |
| Branch coverage | 90.1% |
| Function coverage | 93.0% |
| Line coverage | 97.8% |

---

## 5. Android App (Kotlin/Camera2)

### Tech Stack

- **Language:** Kotlin 1.9.22
- **UI:** Hybrid XML (TextureView) + Jetpack Compose (ComposeView overlay)
- **Camera:** Camera2 API (raw, not CameraX)
- **Navigation:** Jetpack Navigation Compose
- **State:** ViewModel + StateFlow
- **Streaming:** HTTP MJPEG server (port 8080)
- **Discovery:** UDP broadcast (port 9999)
- **Build:** Gradle 8.8, AGP 8.1.0, compileSdk 34

### Camera2 Pipeline

```
1. initializeCamera()
   → CameraManager.openCamera(backCameraId)

2. createCaptureSession()
   → Preview buffer: 1920x1080
   → ImageReader: 1280x720 JPEG, capacity 2
   → Dual-surface: TextureView + ImageReader

3. startStreamingCapture()
   → Preview: TEMPLATE_PREVIEW, repeating request
   → JPEG loop: 67ms delay (~15fps), TEMPLATE_STILL_CAPTURE
   → JPEG quality: 70

4. Frame Processing
   → ImageReader callback → JPEG bytes → Bitmap
   → streamServer.sendFrame(bitmap) → multipart boundary
   → bitmap.recycle()
```

### Resolution Support

| Resolution | Dimensions | UI Available | Actual Streaming |
|-----------|-----------|-------------|-----------------|
| UHD 4K | 3840×2160 | Yes | No |
| FHD 1080p | 1920×1080 | Yes | No |
| HD 720p | 1280×720 | Yes | **Yes (hardcoded)** |

### MJPEG Server (`StreamServer.kt`)

- TCP server on port 8080
- Multi-client support (synchronized client list)
- HTTP multipart/x-mixed-replace format
- Frame format: `--frame\r\nContent-Type: image/jpeg\r\nContent-Length: N\r\n\r\n[JPEG bytes]\r\n`
- JPEG quality: 80 (compression), 85 (MjpegStream)

### UI Screens (7 screens)

| Screen | File | Key Features |
|--------|------|-------------|
| **Home** | `HomeScreen.kt` | Camera preview, "FIELDVISION AI" logo (long-press → dev screen), status indicators, "GO LIVE" button |
| **Streaming** | `StreamingScreen.kt` | LIVE indicator (pulsing), stat badges (FPS/Battery/WiFi), floating controls, STOP button |
| **Lock Mode** | `LockModeScreen.kt` | Minimal UI: LIVE dot, Battery %, FPS, Temp, WiFi, STOP only |
| **Settings** | `SettingsScreen.kt` | Video (Resolution/FPS/Bitrate/Codec), Streaming (Mode/Server/Port), Camera Controls (Lens/Exposure/WB/Focus/HDR), Advanced toggles |
| **Calibration** | `CalibrationScreen.kt` | 5-step wizard: Mount, Level, Left Goal, Right Goal, Center Circle |
| **Emergency** | `EmergencyScreen.kt` | Full-screen red overlay, "CONNECTION LOST", reconnecting countdown |
| **Developer** | `DeveloperScreen.kt` | Encoder stats, CPU/RAM bars, Network stats, Camera2 API status |

### Compose Components (5 components)

| Component | Description |
|-----------|-------------|
| `FloatingControls` | 5 circular buttons: Lock, Focus, Torch, Mic, Settings |
| `StatusBar` | Horizontal bar: Battery %, FPS, Temp, WiFi, Bitrate, Latency |
| `AiStatusPanel` | AI connection status: Virtual Camera, Servo, Streaming (active/disabled dots) |
| `NotificationToast` | Animated slide-in toasts with color coding (success/warning/error) |
| `AiOverlay` | Canvas overlay: green player boxes, yellow ball circle, cyan horizon, blue virtual camera rect |

### ViewModel (`CameraViewModel.kt`)

Single `MutableStateFlow<CameraUiState>` with 40+ state update methods covering:
- Navigation, Camera, Streaming, Resolution, Connection, Device
- AI, Camera Controls, Settings, Streaming Settings
- Calibration, Emergency, Notifications, Developer

### Networking

| Component | Protocol | Port | Purpose |
|-----------|----------|------|---------|
| `StreamServer` | TCP/HTTP MJPEG | 8080 | Video stream to backend |
| `NetworkMonitor` | HTTP | — | Bandwidth/latency measurement (5s polling) |
| `DiscoveryService` | UDP broadcast | 9999 | Auto-discover backend on LAN |

### Build Configuration

| Setting | Value |
|---------|-------|
| compileSdk | 34 |
| minSdk | 26 |
| targetSdk | 34 |
| Kotlin | 1.9.22 |
| Compose BOM | 2024.02.00 |
| AGP | 8.1.0 |
| Gradle | 8.8 |
| APK Size | ~13 MB (debug) |

### Permissions

| Permission | Purpose |
|-----------|---------|
| `CAMERA` | Camera2 API access |
| `INTERNET` | Stream server, network monitoring |
| `ACCESS_NETWORK_STATE` | Network type detection |
| `ACCESS_WIFI_STATE` | WiFi signal strength |
| `CHANGE_WIFI_MULTICAST_STATE` | UDP discovery broadcast |

---

## 6. ESP32 Firmware (C++/Arduino)

### PlatformIO Configuration

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
monitor_speed = 115200
upload_speed = 921600
lib_deps = WebSockets@^2.4.0, ArduinoJson@^6.21.0
```

### Pin Configuration

| GPIO | Function |
|------|----------|
| 25 | Emergency stop button (INPUT_PULLUP, ISR debounced 250ms) |
| 26 | Manual override button (INPUT_PULLUP, ISR debounced 250ms) |
| 13 | Pan servo (LEDC PWM, DS3235) |
| 12 | Tilt servo (LEDC PWM, DS3235) |
| 2 | Status LED |

### Servo Control (`servo_controller.h`)

- Pulse width: 500–2500 microseconds
- LEDC PWM channels for pan/tilt
- Ease-in-out interpolation for smooth transitions
- Emergency stop freezes current position
- Angle-to-duty-cycle: `(pulseUs * 65535) / 20000`

### WebSocket Client (`websocket_client.h`)

- Auto-reconnect: 5s interval
- Heartbeat: 15s ping, 10s pong timeout, 3 retries
- Register message: `{type: "register", device: "esp32", firmware_version: "1.0.0"}`
- Handles: `servo_command`, `ping`, `config_update`

### Communication Protocol

| Command Type | Direction | Payload |
|-------------|-----------|---------|
| `servo_command` | Backend→ESP32 | `{pan_angle, tilt_angle, transition_time}` |
| `position_feedback` | ESP32→Backend | `{pan_angle, tilt_angle, timestamp}` |
| `device_status` | ESP32→Backend | `{wifi_rssi, uptime, free_heap, connection_state}` |
| `heartbeat` | Both ways | Ping/pong |
| `emergency_stop` | Button→ESP32 | GPIO 25 ISR |

### Safety Features

- Hardware watchdog: 15s timeout → ESP32 reset
- Emergency stop button: freezes servos immediately
- Manual override button: switches to manual control
- WiFi auto-reconnect: 10s interval
- Position feedback: every 100ms
- Device status: every 1s

---

## 7. Streaming Pipeline

### End-to-End Frame Flow

```
Frame N:
  Phone Camera (Camera2, 1280×720 JPEG @15fps)
    │
    ▼
  StreamServer (TCP port 8080, MJPEG multipart)
    │
    ▼
  HttpCameraSource (Python, HTTP GET, parse boundary)
    │  → numpy BGR array
    ▼
  CameraService (threaded capture loop, latest frame buffer)
    │  → FRAME_CAPTURED event
    ▼
  VisionService (YOLO11 letterbox preprocess, GPU inference, NMS)
    │  → DETECTIONS_COMPLETE event (list of Detection)
    ▼
  TrackingService (ByteTrackSort: Kalman predict → Hungarian associate → update)
    │  → TRACKING_UPDATED event (list of Track)
    ▼
  DirectorService (ShotComposer: weighted centroid → field zone → zoom → shot type → smooth)
    │  → CAMERA_STATE_UPDATED event (CameraState: center_x=0.65, center_y=0.45, zoom=1.8)
    ▼
  OutputManager
    ├→ VirtualCameraOutput: crop/resize frame → OBS virtual camera
    ├→ ServoOutput: normalize → angles → MotionPlanner → SafetyLayer → ESP32 WebSocket
    └→ PTZOutput: (stub)
```

### Detection Pipeline Detail

1. **Preprocessing:** Letterbox resize (640×640) preserving aspect ratio
2. **Inference:** YOLO11 nano model on CUDA GPU (2GB VRAM cap)
3. **Postprocessing:** NMS + confidence filtering (threshold 0.5)
4. **Output:** List of `Detection` objects with label, bbox (normalized), confidence

### Tracking Pipeline Detail

1. **Kalman Prediction:** Predict next bbox from previous state
2. **IOU Distance Matrix:** Compute 1-IOU for all detection-track pairs
3. **High-Confidence Association:** Match detections (conf ≥ 0.5) with IOU threshold 0.3
4. **Low-Confidence Association:** Match remaining with relaxed IOU threshold 0.5
5. **Hungarian Algorithm:** Optimal assignment via `scipy.optimize.linear_sum_assignment`
6. **Track Update:** Kalman update with matched detections
7. **Track Lifecycle:** tentative (3 hits) → confirmed → lost (30 frames)

### Director Modes

| Mode | Behavior | Shot Types |
|------|----------|------------|
| `broadcast` | Professional TV-style | Medium (≤3 players), Over-shoulder (4-6), Wide (7+) |
| `aggressive` | Tight on ball carrier | Close-up (has ball), Tracking (no ball) |
| `wide` | Full field overview | Always Wide |
| `training` | Educational formations | Medium (≤4), Over-shoulder (5+) |
| `manual_assist` | Semi-auto with override | Medium (≤5), Wide (6+) |

### Weighted Centroid Calculation

```
weight = object_weight × confidence
ball:       2.5 × confidence
goalkeeper: 1.3 × confidence
player:     1.0 × confidence
referee:    0.8 × confidence

centroid_x = Σ(weight × bbox_center_x) / Σ(weight)
centroid_y = Σ(weight × bbox_center_y) / Σ(weight)
```

---

## 8. Configuration System

### YAML Files

#### camera.yaml
```yaml
camera:
  source_type: "auto"          # "device", "file", "http", "auto"
  device_id: 0                 # USB camera index
  http_url: "http://192.168.1.5:8080/video"
  http_protocol: "auto"        # webrtc, h264, mjpeg
  discovery_enabled: true
  discovery_port: 9999
  auto_connect: true
  resolution:
    width: 3840
    height: 2160
  fps: 30
  buffer_size: 3
```

#### ai.yaml
```yaml
ai:
  model_name: "yolo11n.pt"
  confidence: 0.5
  device: "cuda"               # "cuda", "cpu"
  max_detections: 100
```

#### network.yaml
```yaml
network:
  host: "0.0.0.0"
  port: 8000
  cors_origins:
    - "http://localhost:3000"
  esp32_url: "ws://192.168.1.100:8080"
```

#### servo.yaml
```yaml
servo:
  pan:
    min: 0
    max: 180
    default: 90
    speed_limit: 90
  tilt:
    min: 0
    max: 180
    default: 90
    speed_limit: 90
```

#### output.yaml
```yaml
output:
  mode: "virtual"              # "virtual", "servo", "hybrid", "ptz"
  virtual_camera:
    dead_zone: 0.05
    safe_margin: 0.1
    max_velocity: 1.0
    smoothing_factor: 0.3
    default_zoom: 1.5
  servo:
    pan_min: 0
    pan_max: 180
    pan_default: 90
    tilt_min: 0
    tilt_max: 180
    tilt_default: 90
    max_velocity: 90
    max_acceleration: 200
  ptz:
    host: "192.168.1.100"
    port: 80
```

#### stream.yaml
```yaml
stream:
  enabled: false
  youtube_key: ""
  resolution:
    width: 1920
    height: 1080
  bitrate: 4000000
  fps: 30
```

### Environment Variable Overrides

Use double-underscore delimiter to override any YAML value:
```bash
AI__DEVICE=cpu              # overrides ai.device
CAMERA__SOURCE_TYPE=file    # overrides camera.source_type
NETWORK__PORT=9000          # overrides network.port
```

---

## 9. API Reference

### Health Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Basic health check |
| GET | `/api/health/system` | System component health |

### System Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/system/status` | Current state, valid transitions, history |
| GET | `/api/system/state` | Current state name and value |
| POST | `/api/system/state/{state_name}` | Transition to named state |

### Camera Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/camera/status` | Camera running status, uptime, source type |
| POST | `/api/camera/start` | Start camera capture |
| POST | `/api/camera/stop` | Stop camera capture |

### Servo Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/servo/status` | Pan/tilt angles, emergency state |
| POST | `/api/servo/command` | Set pan/tilt (body: `{pan, tilt}` 0-180) |
| POST | `/api/servo/home` | Return servos to 90°/90° |
| POST | `/api/servo/emergency` | Activate emergency stop |

### Director Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/director/status` | Current mode and last decision |
| POST | `/api/director/mode/{mode}` | Set mode (broadcast/aggressive/wide/training/manual_assist) |
| POST | `/api/director/decision` | Get a director decision |

### Stream Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/stream/status` | Streaming status, uptime, active mode |
| POST | `/api/stream/start` | Start streaming |
| POST | `/api/stream/stop` | Stop streaming |

### Output Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/output/mode` | Get active output mode |
| POST | `/api/output/mode` | Switch output mode |
| GET | `/api/output/state` | Get last CameraState sent to output |
| POST | `/api/output/reset` | Reset all output plugins |

### WebSocket

| Protocol | Path | Description |
|----------|------|-------------|
| WebSocket | `/ws` | Real-time updates (ping/pong, subscribe) |

### Response Formats

**Success:**
```json
{
  "status": "ok",
  "pan": 45.0,
  "tilt": 120.0,
  "source": "real"
}
```

**Error:**
```json
{
  "status": "error",
  "message": "Invalid mode"
}
```

---

## 10. Event System

### Event Types

| Category | Event | Topic | Description |
|----------|-------|-------|-------------|
| System | STATE_CHANGED | `state.changed` | State machine transition |
| System | ERROR_OCCURRED | `error.occurred` | Error event |
| System | HEALTH_CHECK | `health.check` | Health check |
| Camera | FRAME_CAPTURED | `camera.frame_captured` | New frame captured |
| Camera | CAMERA_CONNECTED | `camera.connected` | Camera connected |
| Camera | CAMERA_DISCONNECTED | `camera.disconnected` | Camera disconnected |
| Vision | DETECTIONS_COMPLETE | `vision.detections_complete` | Detection results ready |
| Tracking | TRACKING_UPDATED | `tracking.updated` | Tracking results ready |
| Prediction | PREDICTION_UPDATED | `prediction.prediction_updated` | Prediction results ready |
| Director | DIRECTOR_DECISION | `director.decision` | Director made a decision |
| Director | CAMERA_STATE_UPDATED | `director.camera_state_updated` | Camera state output ready |
| Servo | SERVO_COMMAND | `servo.command` | Servo command issued |
| Servo | SERVO_POSITION | `servo.position` | Servo position update |
| Servo | SERVO_ERROR | `servo.error` | Servo error |
| Stream | STREAM_STARTED | `stream.started` | Stream started |
| Stream | STREAM_STOPPED | `stream.stopped` | Stream stopped |
| Stream | STREAM_ERROR | `stream.error` | Stream error |
| Safety | SAFETY_VIOLATION | `safety.violation` | Safety rule violated |
| Safety | EMERGENCY_STOP | `safety.emergency_stop` | Emergency stop triggered |

### Event Priorities

| Priority | Value | Usage |
|----------|-------|-------|
| NORMAL | 0 | Default |
| HIGH | 1 | Servo commands, camera states, safety violations |
| CRITICAL | 2 | Emergency stop |

### Event Flow Diagram

```
CameraService ──FRAME_CAPTURED──▶ VisionService
                                      │
                              DETECTIONS_COMPLETE
                                      │
                                      ▼
                               TrackingService
                                      │
                                TRACKING_UPDATED
                                      │
                        ┌─────────────┼─────────────┐
                        ▼             ▼             ▼
                 DirectorService  PredictionService  (consumers)
                        │
              DIRECTOR_DECISION
              CAMERA_STATE_UPDATED
                        │
                        ▼
                  OutputManager
                  ┌─────┼─────┐
                  ▼     ▼     ▼
               Virtual Servo  PTZ
```

---

## 11. State Machine

### States

| State | Value | Description |
|-------|-------|-------------|
| BOOTING | 0 | System initializing |
| CONNECTING | 1 | Connecting to camera/hardware |
| IDLE | 2 | Connected but not active |
| STREAMING | 3 | Capturing video frames |
| TRACKING | 4 | Running AI detection + tracking |
| MANUAL | 5 | Manual servo control |
| HOMING | 6 | Returning servos to default position |
| EMERGENCY_STOP | 7 | Emergency stop active |
| ERROR | 8 | System error |

### Valid Transitions

```
BOOTING       → CONNECTING, ERROR
CONNECTING    → IDLE, ERROR
IDLE          → STREAMING, MANUAL, HOMING, EMERGENCY_STOP, ERROR
STREAMING     → TRACKING, IDLE, EMERGENCY_STOP, ERROR
TRACKING      → STREAMING, IDLE, EMERGENCY_STOP, ERROR
MANUAL        → IDLE, EMERGENCY_STOP, ERROR
HOMING        → IDLE, EMERGENCY_STOP, ERROR
EMERGENCY_STOP → BOOTING, ERROR
ERROR         → BOOTING
```

---

## 12. Safety System

### SafetyLayer Checks

| Check | Description |
|-------|-------------|
| **Angle limits** | Per-axis min/max validation (0-180°) |
| **Jump limiting** | Max 15° per command |
| **Speed limiting** | Max 120°/s per axis |
| **Watchdog timer** | 2s timeout → emergency stop |
| **Disconnect safety** | ESP32 disconnect → emergency stop |
| **Emergency stop** | Immediate freeze, blocks all commands |

### Violation Types

| Type | Severity |
|------|----------|
| ANGLE_EXCEEDED | warning |
| JUMP_EXCEEDED | error |
| SPEED_EXCEEDED | error |
| WATCHDOG_TIMEOUT | critical |
| DISCONNECT | critical |
| EMERGENCY_STOP | critical |
| INVALID_COMMAND | warning |
| CALIBRATION_ERROR | warning |

---

## 13. Testing

### Backend Tests

| Category | Test Files | Count |
|----------|-----------|-------|
| Camera | test_config, test_discovery, test_http_source, test_service, test_models | 30 |
| API | test_api, test_output_api | 10+ |
| Vision | test_vision | 5+ |
| Tracking | test_tracking | 8+ |
| Director | test_director | 6+ |
| Motion | test_motion, test_safety | 10+ |
| Output | test_output, test_output_config, test_output_wiring, test_servo_output, test_virtual_camera | 15+ |
| Prediction | test_prediction | 5+ |
| Core | test_events, test_state, test_logging | 10+ |
| Config | test_config | 5+ |
| Models | test_models, test_camera_state | 10+ |
| Communication | test_communication | 5+ |
| **Total** | | **771+** |

### Frontend Tests

| Metric | Value |
|--------|-------|
| Framework | Vitest + React Testing Library |
| Test files | 15 |
| Total tests | 82 |
| Statement coverage | 97.2% |
| Branch coverage | 90.1% |
| Function coverage | 93.0% |
| Line coverage | 97.8% |

### Running Tests

```bash
# Backend
cd backend
PYTHONPATH="D:\FieldVision AI;D:\FieldVision AI\backend" pytest tests/ -v

# Frontend
cd frontend
npm run test           # single run
npm run test:watch     # watch mode
npm run test:coverage  # with coverage
```

---

## 14. Getting Started

### Prerequisites

- Python 3.12
- Node.js 18+
- Java 17 (for Android builds)
- Android SDK (platform 34, build-tools 34)
- NVIDIA GPU with CUDA (optional, for AI inference)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/MontageStark/VisionFieldAI.git
cd "FieldVision AI"

# Install backend dependencies
cd backend
pip install fastapi uvicorn opencv-python ultralytics pydantic-settings pyyaml scipy websockets

# Install frontend dependencies
cd ../frontend
npm install

# Start everything
cd ..
start.bat
```

### Manual Start

```bash
# Backend (terminal 1)
cd backend
set PYTHONPATH=D:\FieldVision AI;D:\FieldVision AI\backend
python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload

# Frontend (terminal 2)
cd frontend
npm run dev
```

### Android APK

```bash
cd android-app
.\gradlew.bat assembleDebug
# APK at: app/build/outputs/apk/debug/app-debug.apk
```

### URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| WebSocket | ws://localhost:8000/ws |

---

## 15. Deployment

### LAN Setup (Phone → Laptop)

1. Connect phone and laptop to same Wi-Fi network
2. Find laptop IP: `ipconfig` → IPv4 Address (e.g., `192.168.1.100`)
3. In Android app Settings → Streaming → Server Address: `http://192.168.1.100:8000`
4. Ensure firewall allows incoming connections on ports 8000, 8080, 9999
5. Start backend and frontend
6. Open app → tap "GO LIVE"

### OBS Integration

1. Start the backend with `output.mode: virtual`
2. In OBS → Add Source → Window Capture → select the Virtual Camera output
3. Or use the MJPEG stream URL: `http://<laptop-ip>:8000/stream.mjpeg`

### Production Considerations

- Change `network.cors_origins` to include production domains
- Set `AI__DEVICE=cpu` if no GPU available
- Configure `stream.youtube_key` for YouTube Live streaming
- Set `servo.*` limits based on physical hardware constraints
- Enable `camera.discovery_enabled: false` for fixed camera setups

---

*Document generated from FieldVision AI codebase. For architecture decisions and design rationale, see `arch-v1.md`.*
