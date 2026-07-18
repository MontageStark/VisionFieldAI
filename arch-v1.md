# FieldVision AI — Architecture v1

**Version:** 1.1.0
**Last Updated:** 2026-07-17

## Table of Contents

- [System Overview](#system-overview)
- [Design Principles](#design-principles)
- [High-Level Architecture](#high-level-architecture)
- [Component Deep Dive](#component-deep-dive)
  - [Event Bus](#event-bus)
  - [State Machine](#state-machine)
  - [Camera Pipeline](#camera-pipeline)
  - [Vision Pipeline](#vision-pipeline)
  - [Tracking Pipeline](#tracking-pipeline)
  - [Prediction Pipeline](#prediction-pipeline)
  - [Director Engine](#director-engine)
  - [Output System](#output-system)
  - [Motion & Safety](#motion--safety)
  - [Communication Layer](#communication-layer)
  - [Configuration System](#configuration-system)
- [Data Flow](#data-flow)
- [Data Models](#data-models)
- [API Surface](#api-surface)
- [Android App Architecture](#android-app-architecture)
- [ESP32 Firmware Architecture](#esp32-firmware-architecture)
- [Frontend Architecture](#frontend-architecture)
- [Testing Strategy](#testing-strategy)
- [Deployment](#deployment)
- [Performance Constraints](#performance-constraints)
- [Security Model](#security-model)
- [Future Extensions](#future-extensions)

---

## System Overview

FieldVision AI is an AI-powered robotic football camera system. A smartphone captures live video, streams it over WiFi to a Python backend running YOLO11 object detection and ByteTrack multi-object tracking. An AI "Director" composes cinematic shots and routes them to either a software virtual crop (for OBS) or physical DS3235 servos via an ESP32 microcontroller.

```
┌──────────────┐     WiFi MJPEG      ┌──────────────────┐     WebSocket     ┌─────────┐
│ Phone Camera │ ──────────────────► │  Python Backend   │ ───────────────► │  ESP32   │
│ (Camera2 API)│    UDP discovery    │  YOLO11 + ByteTrack│    Servo cmds    │ DS3235   │
└──────────────┘                     │  Director Engine   │                  └─────────┘
                                     └──────────────────┘
                                            │
                                            ▼
                                     ┌──────────────────┐
                                     │  React Frontend   │
                                     │  Control Dashboard│
                                     └──────────────────┘
```

## Design Principles

| Principle | Implementation |
|-----------|---------------|
| **No Docker** | Native Windows execution |
| **No Flask** | FastAPI only (async, type-safe) |
| **No global variables** | Event-driven via singleton EventBus |
| **No blocking loops** | async/await, threaded capture loops |
| **No hardcoded values** | All config in `configs/*.yaml` |
| **No spaghetti code** | Clean modular service architecture |
| **Immutability** | New objects, never mutate in place |
| **Safety first** | Hardware commands pass through SafetyLayer |
| **AI outputs coordinates** | CameraState is normalized (0-1), never hardware-specific |

## High-Level Architecture

```
backend/
  app/
    main.py                     # FastAPI app factory, lifespan, middleware
    core/
      events.py                 # EventBus singleton (pub/sub, wildcard, thread-safe)
      state.py                  # SystemStateMachine (9 states, transition table)
      logging.py                # StructuredLogger, JSON formatter, perf timers
    config/
      settings.py               # Pydantic Settings with nested models
      loader.py                 # YAML merger, env-var overrides, singleton
    models/                     # Pydantic data models (all immutable)
    services/
      camera/                   # Phone/USB/file video sources
      vision/                   # YOLO11 detection
      tracking/                 # ByteTrack multi-object tracking
      prediction/               # Kalman filter ball trajectory
      director/                 # Cinematic shot composition
      output/                   # Virtual camera, servo, PTZ plugins
      motion/                   # Safety layer, motion planning, smoothing
      communication/            # ESP32 WebSocket client, protocol
    api/                        # FastAPI routes, dependency injection
  tests/                        # 28 test files, 771 tests

android-app/                    # Kotlin Camera2 app
firmware/                       # ESP32 PlatformIO firmware
frontend/                       # React 18 + TypeScript + Vite
configs/                        # YAML configuration files
```

## Component Deep Dive

### Event Bus

**File:** `backend/app/core/events.py`

The EventBus is the nervous system of FieldVision. Every service communicates exclusively through events — no direct method calls between services.

```python
class EventBus:
    """
    Thread-safe pub/sub event bus.

    Features:
    - Event type filtering (23 event types)
    - Wildcard subscriptions ("*" receives all events)
    - Event history (last 100 events, deque-backed)
    - Sync and async publishing
    - Priority levels (NORMAL, HIGH, CRITICAL)
    - Async wait_for() with timeout
    """
```

**Event Types (23 total):**

| Category | Events |
|----------|--------|
| System | `STATE_CHANGED`, `ERROR_OCCURRED`, `HEALTH_CHECK` |
| Camera | `FRAME_CAPTURED`, `CAMERA_CONNECTED`, `CAMERA_DISCONNECTED` |
| Vision | `DETECTIONS_COMPLETE` |
| Tracking | `TRACKING_UPDATED` |
| Prediction | `PREDICTION_UPDATED` |
| Director | `DIRECTOR_DECISION`, `CAMERA_STATE_UPDATED`, `CAMERA_MOVE` |
| Servo | `SERVO_COMMAND`, `SERVO_POSITION`, `SERVO_ERROR` |
| Streaming | `STREAM_STARTED`, `STREAM_STOPPED`, `STREAM_ERROR` |

**Thread Safety:** All operations protected by `threading.RLock`. Publish is synchronous (handlers run in caller thread). `publish_async()` schedules via `asyncio.create_task()` or falls back to sync.

**Singleton Access:**
```python
bus = get_event_bus()        # Global singleton
bus.subscribe(EventType.FRAME_CAPTURED, my_handler)
bus.publish(EventType.FRAME_CAPTURED, data={"frame": frame})
```

### State Machine

**File:** `backend/app/core/state.py`

Explicit state machine with 9 states and validated transitions. No boolean flags — the system is always in exactly one state.

```
BOOTING ──► CONNECTING ──► IDLE ──► STREAMING ──► TRACKING
                │            │          │              │
                ▼            ▼          ▼              ▼
              ERROR    EMERGENCY_STOP  IDLE      STREAMING/IDLE
                         │
                         ▼
                      BOOTING (reset)
```

**States:**

| State | Value | Meaning |
|-------|-------|---------|
| `BOOTING` | 0 | System initializing |
| `CONNECTING` | 1 | Connecting to camera/ESP32 |
| `IDLE` | 2 | Connected, waiting for stream |
| `STREAMING` | 3 | Camera streaming, no tracking |
| `TRACKING` | 4 | AI tracking active |
| `MANUAL` | 5 | Manual servo control |
| `HOMING` | 6 | Servos returning to default position |
| `EMERGENCY_STOP` | 7 | Safety stop triggered |
| `ERROR` | 8 | unrecoverable error |

**Transition Table:**
```python
VALID_TRANSITIONS = {
    BOOTING:      [CONNECTING, ERROR],
    CONNECTING:   [IDLE, ERROR],
    IDLE:         [STREAMING, MANUAL, HOMING, EMERGENCY_STOP, ERROR],
    STREAMING:    [TRACKING, IDLE, EMERGENCY_STOP, ERROR],
    TRACKING:     [STREAMING, IDLE, EMERGENCY_STOP, ERROR],
    MANUAL:       [IDLE, EMERGENCY_STOP, ERROR],
    HOMING:       [IDLE, EMERGENCY_STOP, ERROR],
    EMERGENCY_STOP: [BOOTING, ERROR],
    ERROR:        [BOOTING],
}
```

**Callbacks:** `on_enter(state, callback)` and `on_exit(state, callback)` for reactive behavior. History tracks last 10 transitions with timestamps.

### Camera Pipeline

**Files:** `backend/app/services/camera/`

The camera subsystem abstracts video sources behind a common interface and handles discovery, connection, and frame capture.

**VideoSource ABC:**
```python
class VideoSource(ABC):
    @abstractmethod
    def open(self) -> bool: ...
    @abstractmethod
    def read(self) -> Optional[np.ndarray]: ...
    @abstractmethod
    def release(self) -> None: ...
    @abstractmethod
    def is_opened(self) -> bool: ...
    @property
    @abstractmethod
    def fps(self) -> float: ...
    @property
    @abstractmethod
    def resolution(self) -> Tuple[int, int]: ...
```

**Implementations:**

| Source | Use Case | Protocol |
|--------|----------|----------|
| `HttpCameraSource` | Phone streaming | HTTP MJPEG on port 8080 |
| `OpenCVSource` | USB camera | OpenCV VideoCapture |
| `FileSource` | Simulation/dev | Video file playback |

**CameraService:** Threaded capture loop with auto-reconnect. Publishes `FRAME_CAPTURED` events containing the numpy frame. Reconnects on failure with exponential backoff.

**Discovery:** UDP broadcast on port 9999. Phone sends `DiscoveryMessage` JSON every 2 seconds containing name, IP, port, supported protocols, and resolutions. Backend auto-removes stale phones after 30 seconds.

**Phone Discovery Protocol:**
```json
{
  "name": "Pixel 7",
  "ip": "192.168.0.187",
  "port": 8080,
  "protocols": ["mjpeg"],
  "resolutions": ["1920x1080", "1280x720"]
}
```

### Vision Pipeline

**Files:** `backend/app/services/vision/`

YOLO11 object detection with GPU acceleration and memory limits.

**YOLO11Detector:**
- Model: `yolo11n.pt` (nano, fast)
- Device: CUDA with 2GB VRAM cap
- Preprocessing: Letterbox resize to model input size
- Classes detected: person, ball, goalkeeper, referee (football-specific)
- Confidence threshold: 0.5 (configurable)
- Max detections: 100

**Flow:**
1. Receives `FRAME_CAPTURED` event with numpy frame
2. Letterbox preprocessing (preserve aspect ratio)
3. GPU inference via ultralytics
4. Postprocessing: NMS, confidence filtering
5. Publishes `DETECTIONS_COMPLETE` with list of `Detection` objects

**Simulation Mode:** When YOLO model is unavailable (e.g., no GPU), returns empty detections. System still runs through the pipeline for testing.

### Tracking Pipeline

**Files:** `backend/app/services/tracking/`

ByteTrack-inspired multi-object tracking with Kalman filters.

**ByteTrackSort Algorithm:**
1. **Predict** all existing tracks forward using Kalman filter
2. **First association:** Match high-confidence detections (≥0.5) to tracks using IOU distance + Hungarian algorithm
3. **Second association:** Match remaining low-confidence detections to unmatched tracks with relaxed IOU threshold
4. **Create** new tracks for unmatched high-confidence detections
5. **Cull** tracks that exceed `max_time_lost` (30 frames)

**KalmanBoxTracker:**
- 8-state vector: `[x, y, aspect_ratio, height, vx, vy, va, vh]`
- Constant velocity motion model
- Confidence-weighted measurement noise
- Predict → Update cycle per frame

**Track State Machine:**
```
TENTATIVE ──(3 hits)──► CONFIRMED ──(30 frames no update)──► LOST
```

**IOU Distance:** `1 - IoU` matrix computed between all detection-track pairs. Hungarian algorithm (`scipy.optimize.linear_sum_assignment`) finds optimal assignment.

### Prediction Pipeline

**Files:** `backend/app/services/prediction/`

Ball trajectory prediction using a dedicated Kalman filter.

**KalmanFilter2D:**
- 4-state vector: `[x, y, vx, vy]`
- Constant velocity model
- Confidence-weighted updates
- Future position prediction (configurable time horizon)
- Gap filling when detections miss

**Focus:** Tracks `sports_ball` class specifically. Predicts where the ball will be, enabling the Director to frame ahead of the action.

### Director Engine

**Files:** `backend/app/services/director/`

The cinematic brain of the system. Takes tracking data and produces normalized camera framing instructions.

**Director Modes:**

| Mode | Style | Base Zoom | Behavior |
|------|-------|-----------|----------|
| `broadcast` | TV-style | 1.5x | Balanced, follows ball weighted centroid |
| `aggressive` | Close-up | 2.0x | Tight on ball carrier, quick cuts |
| `wide` | Tactical | 1.2x | Shows full field, minimal zoom |
| `training` | Analysis | 1.8x | Steady framing for review |
| `manual_assist` | Hybrid | 1.5x | AI suggests, human overrides |

**ShotComposer:**
```python
CLASS_WEIGHTS = {
    "ball": 2.5,        # Ball is primary focus
    "goalkeeper": 1.3,  # Goalkeeper slightly weighted
    "person": 1.0,      # Players standard weight
    "referee": 0.8,     # Referees de-emphasized
}
```

**Weighted Centroid Calculation:**
1. For each tracked object, compute center (x, y) from bounding box
2. Multiply by class weight × confidence
3. Weighted average gives target point
4. Normalize to 0-1 range

**Field Zone Detection:**
```
┌─────────┬─────────┬─────────┐
│  LEFT   │ CENTER  │  RIGHT  │
├─────────┼─────────┼─────────┤
│ OFFENSE │ CENTER  │ DEFENSE │
├─────────┼─────────┼─────────┤
│         │  GOAL   │         │
└─────────┴─────────┴─────────┘
```

Zone determines zoom level (goal = tighter zoom) and shot type selection.

**Shot Types:**

| Shot | Description | When Used |
|------|-------------|-----------|
| `close_up` | Tight on single player | Ball carrier in aggressive mode |
| `medium` | 2-3 players visible | Standard broadcast |
| `wide` | Full field view | Many players, wide mode |
| `over_shoulder` | Behind player perspective | Medium player count |
| `tracking` | Following movement | Ball in motion |
| `static` | No movement | No tracks detected |

**Smoothing:** Exponential interpolation (factor 0.3) prevents jerky camera movement. Previous composition blended with new target.

**Output:** `ShotComposition` dataclass with normalized `center_x`, `center_y` (0-1), `zoom` (1-4x), `action`, `shot_type`, `confidence`.

### Output System

**Files:** `backend/app/services/output/`

Plugin-based output system. All outputs implement the same interface — the AI only produces `CameraState`, never hardware commands.

**OutputPlugin ABC:**
```python
class OutputPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    @abstractmethod
    def apply(self, state: CameraState) -> None: ...
    @abstractmethod
    def get_state(self) -> Optional[CameraState]: ...
    @abstractmethod
    def reset(self) -> None: ...
    @abstractmethod
    def is_available(self) -> bool: ...
```

**Plugins:**

| Plugin | What It Does |
|--------|-------------|
| `VirtualCameraOutput` | Crops/pans/zooms frames in software (for OBS virtual camera) |
| `ServoOutput` | Maps normalized CameraState → servo angles via MotionPlanner |
| `PTZOutput` | Stub for IP PTZ cameras (not yet implemented) |

**VirtualCameraOutput Details:**
- Dead zone: Ignores movement < 5% to prevent jitter
- Safe margin: Keeps action away from frame edges (10%)
- Crop window computed from center_x, center_y, zoom
- `cv2.resize` with LANCZOS4 interpolation
- Output frame same dimensions as input

**OutputManager:** Singleton that routes `CameraState` to the active plugin. Supports hot-swapping between modes via API.

### Motion & Safety

**Files:** `backend/app/services/motion/`

The safety layer is the last line of defense between AI decisions and physical hardware.

**SafetyLayer:**
```python
class SafetyLayer:
    """
    Features:
    - Per-axis angle validation (0-180°)
    - Jump limiting (max 15° per command)
    - Speed limiting (max 120°/s)
    - Watchdog timer (2s timeout → emergency stop)
    - Disconnect safety (ESP32 disconnect → emergency stop)
    - Emergency stop handling
    """
```

**Validation Chain:**
1. `validate_jump(axis, current, target)` — Is the angle change safe?
2. `validate_angle(axis, target)` — Is the target within bounds?
3. `validate_command(axis, current, target, speed)` — Full validation
4. If any check fails → clamp to safe value, publish `SAFETY_VIOLATION`

**MotionPlanner:**
- Trapezoidal velocity profiles (accelerate → cruise → decelerate)
- Easing functions: `ease_in_out`, `ease_in`, `ease_out`, `ease_out_elastic`
- Homing sequence: Smooth return to default position (90°, 90°)
- Velocity limiting: Max 90°/s pan, 90°/s tilt

**Emergency Stop:**
- Triggered by: watchdog timeout, ESP32 disconnect, manual button, safety violation
- Action: All motion commands blocked, servos hold position
- Recovery: Requires explicit reset via API

### Communication Layer

**Files:** `backend/app/services/communication/`

**ESP32 Protocol:**

| Command | Direction | Payload |
|---------|-----------|---------|
| `pan_tilt` | Backend → ESP32 | `{pan: 0-180, tilt: 0-180, transition: "smooth"}` |
| `home` | Backend → ESP32 | `{}` (return to 90,90) |
| `heartbeat` | Both ways | `{}` (ping/pong) |
| `position_feedback` | ESP32 → Backend | `{pan: 45.2, tilt: 87.1}` |
| `device_status` | ESP32 → Backend | `{uptime: 12345, free_heap: 45000}` |

**ESP32Client:**
- WebSocket connection with auto-reconnect
- Exponential backoff: 1s → 2s → 4s → ... → 60s max
- Heartbeat every 5s (detects dead connections)
- Async context manager for clean lifecycle

### Configuration System

**Files:** `backend/app/config/`

All configuration lives in `configs/*.yaml`. No hardcoded values anywhere.

**YAML Files:**

| File | Controls |
|------|----------|
| `camera.yaml` | Source type, resolution, FPS, discovery |
| `servo.yaml` | Pan/tilt limits, default angles, speed |
| `ai.yaml` | YOLO model, confidence, device |
| `network.yaml` | Host, port, CORS, ESP32 URL |
| `output.yaml` | Mode, virtual camera params, servo params |
| `stream.yaml` | YouTube stream settings |

**Loading Order:** Files merged alphabetically. Environment variables override with `__` as nested delimiter:
```bash
NETWORK__PORT=9000  # Overrides network.yaml → port
```

**Pydantic Settings:** Type-safe, validated at startup. Nested models for each subsystem.

## Data Flow

### Complete Pipeline (per frame)

```
1. Phone Camera (Camera2 API)
   │  JPEG capture at 720p, 15fps
   │  MJPEG multipart stream on port 8080
   ▼
2. HttpCameraSource (Backend)
   │  HTTP GET → parse multipart boundary
   │  Decode JPEG → numpy array (BGR)
   ▼
3. CameraService (Threaded Loop)
   │  read() → frame
   │  Publish: FRAME_CAPTURED {frame, timestamp}
   ▼
4. VisionService (Event Subscriber)
   │  Letterbox preprocess → GPU inference
   │  NMS → filter by confidence
   │  Publish: DETECTIONS_COMPLETE {detections[]}
   ▼
5. TrackingService (Event Subscriber)
   │  ByteTrackSort.update(detections)
   │  Kalman predict → associate → update
   │  Track state machine: tentative→confirmed→lost
   │  Publish: TRACKING_UPDATED {tracks[]}
   ▼
6. PredictionService (Event Subscriber)
   │  Filter for sports_ball tracks
   │  KalmanFilter2D predict future position
   │  Publish: PREDICTION_UPDATED {predicted_positions[]}
   ▼
7. DirectorService (Event Subscriber)
   │  ShotComposer.compose_shot(tracks, frame_dims)
   │  Weighted centroid → field zone → zoom → shot type
   │  Exponential smoothing
   │  Publish: DIRECTOR_DECISION {decision}
   │  Publish: CAMERA_STATE_UPDATED {CameraState}
   ▼
8. OutputManager (Event Subscriber)
   │  Routes CameraState to active plugin
   ├─► VirtualCameraOutput: crop/pan/zoom frame → OBS
   └─► ServoOutput: CameraState → MotionPlanner → SafetyLayer
                          │
                          ▼
                     ESP32Client → WebSocket → ESP32 → DS3235 Servos
```

### CameraState (The Universal Output)

```python
@dataclass
class CameraState:
    center_x: float          # 0.0 (left) to 1.0 (right)
    center_y: float          # 0.0 (top) to 1.0 (bottom)
    zoom: float              # 1.0 (wide) to 4.0 (telephoto)
    motion_profile: str      # "broadcast", "fast_break", etc.
    tracking_mode: str       # "ball", "player", "area"
    confidence: float        # 0.0 to 1.0
    timestamp: float         # time.time()
```

This is the ONLY output from the AI. All renderers (virtual camera, servo, PTZ) translate these normalized coordinates to their device-specific values.

## Data Models

**File:** `backend/app/models/`

All models are Pydantic `BaseModel` or Python `dataclass`. Immutable by convention.

| Model | Purpose |
|-------|---------|
| `CameraState` | Normalized camera framing instruction |
| `OutputConfig` | Output mode and plugin parameters |
| `Detection` | Single YOLO detection (bbox, class, confidence) |
| `BoundingBox` | (x1, y1, x2, y2) pixel coordinates |
| `Track` | Tracked object with state machine |
| `DirectorDecision` | Shot composition result |
| `ServoCommand` | Pan/tilt command with transition type |
| `MotionPlan` | Waypoint sequence for smooth motion |
| `SafetyCheck` | Validation result (pass/fail + clamped value) |
| `SafetyViolation` | Violation record with severity |
| `EmergencyStop` | Emergency stop event data |
| `HealthStatus` | Component health report |

## API Surface

**Base URL:** `http://localhost:8000`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check |
| `/api/health/system` | GET | Full component health |
| `/api/system/status` | GET | State machine status + history |
| `/api/system/state` | GET | Current state name |
| `/api/system/state/{name}` | POST | Transition to new state |
| `/api/camera/status` | GET | Camera connection status |
| `/api/camera/start` | POST | Start camera capture |
| `/api/camera/stop` | POST | Stop camera capture |
| `/api/servo/status` | GET | Current servo angles + emergency state |
| `/api/servo/command` | POST | Send pan/tilt command |
| `/api/servo/home` | POST | Home servos to 90°, 90° |
| `/api/servo/emergency` | POST | Trigger emergency stop |
| `/api/director/status` | GET | Director mode + last decision |
| `/api/director/mode/{mode}` | POST | Set director mode |
| `/api/stream/status` | GET | Streaming status |
| `/api/stream/start` | POST | Start YouTube stream |
| `/api/stream/stop` | POST | Stop stream |
| `/api/output/mode` | GET/POST | Get/set output mode |
| `/api/output/state` | GET | Current output state |
| `/api/output/reset` | POST | Reset output to defaults |
| `/ws` | WebSocket | Real-time updates (ping/subscribe) |

## Android App Architecture

**Package:** `com.fieldvision.camera`

```
com.fieldvision.camera/
  MainActivity.kt           # Camera2 init, streaming, UI
  camera/
    CameraEngine.kt         # Camera2 wrapper (open/close/configure)
    CameraConfig.kt         # Resolution, FPS, exposure data classes
  stream/
    StreamServer.kt         # HTTP MJPEG server (port 8080)
    MjpegStream.kt          # MJPEG frame writer
  network/
    NetworkMonitor.kt       # Bandwidth/latency measurement
    ConnectionState.kt      # Connection type enum
  discovery/
    DiscoveryService.kt     # UDP broadcast (port 9999)
    PhoneInfo.kt            # Phone metadata for discovery
```

**Camera2 Pipeline:**
1. Open rear camera (lensFacing = BACK)
2. Configure preview surface (TextureView)
3. Configure JPEG ImageReader (720p or 1080p)
4. Create capture session with both surfaces
5. Repeat capture request (TEMPLATE_PREVIEW)
6. On JPEG available → encode to MJPEG → send to StreamServer clients

**UI Features:**
- Glass-morphism cards with gradient overlays
- Resolution selector (4K / 1080p / 720p / Auto)
- Live indicator with pulse animation
- IP address display for streaming connection
- Connection status dot (green = ready, yellow = connecting, red = error)

## ESP32 Firmware Architecture

**Platform:** ESP32 (FreeRTOS)

```
firmware/src/
  main.cpp                  # Main loop, ISR handlers
  servo_controller.h        # DS3235 servo control (LEDC PWM)
  websocket_client.h        # WebSocket to backend
  wifi_manager.h            # WiFi STA + auto-reconnect
  watchdog.h                # Task WDT (15s timeout)
```

**Main Loop:**
1. Check for emergency stop button (GPIO 25, debounced 250ms)
2. Check for manual override button (GPIO 26, debounced 250ms)
3. Process incoming WebSocket commands
4. Send position feedback (every 100ms)
5. Send device status (every 1s)
6. Feed watchdog

**Servo Control:**
- DS3235: 500-2500μs pulse width, 180° range
- LEDC PWM channels for pan and tilt
- Ease-in-out interpolation for smooth motion
- Emergency stop: immediately halt all movement

## Frontend Architecture

**Stack:** React 18, TypeScript, Vite, Zustand, Axios

```
frontend/src/
  App.tsx                   # React Router (13 routes)
  services/
    api.ts                  # Axios client (typed endpoints)
    websocket.ts            # Auto-reconnect WebSocket
  stores/
    appStore.ts             # Output mode, last state
    systemStore.ts          # System state, health, WS status
  pages/                    # Dashboard, Camera, Servo, Director, etc.
  components/               # AppLayout, Sidebar, Header, etc.
```

**Routes:**
- `/` — Dashboard (overview)
- `/camera` — Camera controls
- `/servo` — Servo manual control
- `/director` — Director mode selection
- `/streaming` — Stream start/stop
- `/output` — Output mode switching
- `/virtual-camera` — Virtual camera view
- `/hardware` — ESP32 status
- `/health` — System health
- `/logs` — Event log
- `/plugins` — Plugin management
- `/calibration` — Servo calibration
- `/settings` — Configuration

## Testing Strategy

**Framework:** pytest
**Coverage Target:** 80%+
**Total Tests:** 771

**Test Types:**

| Type | Count | What |
|------|-------|------|
| Unit | ~600 | Individual functions, models, utilities |
| Integration | ~150 | Service interactions, API endpoints |
| E2E | ~21 | Full pipeline flows |

**Test Categories:**
- `test_api.py` — All REST endpoints
- `test_camera.py` — Camera service, sources, discovery
- `test_config.py` — YAML loading, env overrides
- `test_director.py` — Shot composition, modes
- `test_events.py` — EventBus pub/sub
- `test_motion.py` — Safety layer, motion planning
- `test_output.py` — Output plugins, manager
- `test_state.py` — State machine transitions
- `test_tracking.py` — ByteTrack, Kalman filter
- `test_vision.py` — YOLO detection
- `test_prediction.py` — Ball trajectory prediction
- `test_safety.py` — Safety validation

## Deployment

**No Docker.** Native execution on Windows.

**Start Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Start Frontend:**
```bash
cd frontend
npm install
npm run dev  # Vite dev server on port 3000
```

**Android App:**
```bash
cd android-app
./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

**ESP32 Firmware:**
```bash
cd firmware
platformio run --target upload
```

## Performance Constraints

| Resource | Limit |
|----------|-------|
| GPU VRAM | 2GB cap |
| CPU cores | 2 cores max |
| Auto port discovery | 8000-9999 range |
| Camera FPS | 15fps (720p JPEG over WiFi) |
| Tracking latency | ~50ms per frame |
| Safety watchdog | 2s timeout |
| ESP32 heartbeat | 5s interval |
| Event history | Last 100 events |
| State history | Last 10 transitions |

## Security Model

- No hardcoded secrets (API keys, passwords, tokens)
- All user inputs validated at boundaries
- Camera permissions handled gracefully (Android)
- Network discovery validated
- CORS configured for frontend origin only
- WebSocket connections authenticated (planned)
- Safety layer prevents hardware damage
- Emergency stop always available

## Future Extensions

| Feature | Status | Notes |
|---------|--------|-------|
| WebRTC streaming | Planned | Replace MJPEG for lower latency |
| H.264 encoding | Planned | Hardware encoder on phone |
| Replay system | Planned | Record and playback highlights |
| YouTube integration | Stub | `stream.yaml` configured |
| PTZ camera output | Stub | `PTZOutput.is_available() = False` |
| Player identification | Planned | Jersey number recognition |
| Tactical analysis | Planned | Formation detection |
| Multi-camera | Planned | Multiple phone feeds |
| Mobile dashboard | Planned | React Native companion app |

---

*This document is the authoritative architecture reference for FieldVision AI. Update it when adding new services, changing data flow, or modifying the event contract.*
