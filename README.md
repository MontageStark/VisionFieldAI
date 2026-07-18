# FieldVision AI

**AI-powered robotic football camera system with auto-framing and virtual camera output.**

FieldVision AI uses a smartphone camera, YOLO11 object detection, ByteTrack multi-object tracking, and an intelligent Director engine to automatically frame football matches — outputting to either a software virtual crop (for OBS) or physical servo-mounted cameras via ESP32.

```
Phone Camera ──WiFi──► Python Backend ──► Virtual Camera (OLOBS)
                           │
                           └──WebSocket──► ESP32 ──► DS3235 Servos
```

---

## Features

- **AI Auto-Framing** — YOLO11 detects players, ball, goalkeeper, referee; Director engine composes cinematic shots
- **Virtual Camera** — Software crop/pan/zoom output directly to OBS virtual camera
- **Physical Servo Control** — DS3235 pan/tilt servos via ESP32 WebSocket
- **5 Director Modes** — Broadcast, Aggressive, Wide, Training, Manual Assist
- **Safety Layer** — Angle limits, jump limiting, watchdog timer, emergency stop, disconnect detection
- **Phone Streaming** — Camera2 API MJPEG streaming with UDP auto-discovery
- **Real-time Dashboard** — React frontend with live controls and monitoring
- **771 Tests** — Comprehensive test suite with 80%+ coverage

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, FastAPI, OpenCV, YOLO11 (ultralytics), ByteTrack, PyTorch CUDA |
| **Android** | Kotlin, Camera2 API, MJPEG streaming, PlatformIO |
| **Frontend** | React 18, TypeScript, Vite, Zustand, TailwindCSS |
| **Firmware** | C++ (Arduino/PlatformIO), ESP32, FreeRTOS |
| **Hardware** | DS3235 servos, ESP32, any Android phone |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- Android phone with Camera2 API
- ESP32 (optional, for servo control)
- NVIDIA GPU with CUDA (optional, for AI detection)

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Backend starts on `http://localhost:8000`. API docs at `/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard opens at `http://localhost:3000`.

### 3. Android App

```bash
cd android-app
./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

Grant camera permission. The app starts streaming MJPEG on port 8080 and broadcasts its IP via UDP port 9999.

### 4. ESP32 (Optional)

```bash
cd firmware
platformio run --target upload
```

ESP32 connects to WiFi, connects to backend via WebSocket, and waits for servo commands.

### 5. OBS Setup

1. Add "Video Capture Device" source
2. Select "OBS Virtual Camera"
3. Or add "Media Source" with URL `http://<phone-ip>:8080/video` for direct phone feed

---

## Project Structure

```
FieldVision AI/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app factory
│   │   ├── core/
│   │   │   ├── events.py           # EventBus (pub/sub, 23 event types)
│   │   │   ├── state.py            # SystemStateMachine (9 states)
│   │   │   └── logging.py          # Structured logging
│   │   ├── config/
│   │   │   ├── settings.py         # Pydantic Settings
│   │   │   └── loader.py           # YAML config loader
│   │   ├── models/                 # Pydantic data models
│   │   ├── services/
│   │   │   ├── camera/             # Phone/USB/file video sources
│   │   │   ├── vision/             # YOLO11 detection
│   │   │   ├── tracking/           # ByteTrack multi-object tracking
│   │   │   ├── prediction/         # Kalman ball trajectory
│   │   │   ├── director/           # Cinematic shot composition
│   │   │   ├── output/             # Virtual camera, servo, PTZ
│   │   │   ├── motion/             # Safety layer, motion planning
│   │   │   └── communication/      # ESP32 WebSocket client
│   │   └── api/                    # REST + WebSocket endpoints
│   └── tests/                      # 28 test files
├── android-app/
│   └── app/src/main/java/com/fieldvision/camera/
│       ├── MainActivity.kt         # Camera2 + streaming + UI
│       ├── camera/                 # Camera2 wrapper
│       ├── stream/                 # MJPEG server
│       ├── network/                # Bandwidth measurement
│       └── discovery/              # UDP auto-discovery
├── frontend/
│   └── src/
│       ├── App.tsx                 # React Router (13 routes)
│       ├── services/               # API + WebSocket clients
│       ├── stores/                 # Zustand state stores
│       ├── pages/                  # Dashboard, Camera, Servo, etc.
│       └── components/             # UI components
├── firmware/
│   └── src/
│       ├── main.cpp                # ESP32 main loop
│       ├── servo_controller.h      # DS3235 PWM control
│       ├── websocket_client.h      # Backend connection
│       ├── wifi_manager.h          # WiFi auto-reconnect
│       └── watchdog.h              # Task WDT
├── configs/
│   ├── camera.yaml                 # Camera source, resolution
│   ├── servo.yaml                  # Pan/tilt limits
│   ├── ai.yaml                     # YOLO model, confidence
│   ├── network.yaml                # Host, port, CORS
│   ├── output.yaml                 # Output mode, params
│   └── stream.yaml                 # YouTube stream settings
├── docs/                           # Design specs
├── rules/                          # Coding standards
├── tests/                          # Additional tests
├── scripts/                        # Utility scripts
├── arch-v1.md                      # In-depth architecture
└── AGENTS.md                       # AI agent instructions
```

---

## Architecture

See [arch-v1.md](./arch-v1.md) for the complete in-depth architecture document.

### Event-Driven Pipeline

All services communicate through a thread-safe EventBus. No direct coupling between components.

```
Phone → CameraService → VisionService → TrackingService → DirectorService → OutputManager
         (FRAME_CAPTURED)  (DETECTIONS)    (TRACKING)       (CAMERA_STATE)    (apply)
```

### State Machine

```
BOOTING → CONNECTING → IDLE → STREAMING → TRACKING
                                    ↓
                              EMERGENCY_STOP → BOOTING (reset)
```

9 states with explicit transition table. No boolean flags.

### Director Modes

| Mode | Style | Zoom | Use Case |
|------|-------|------|----------|
| `broadcast` | TV-style | 1.5x | Default, balanced framing |
| `aggressive` | Close-up | 2.0x | Tight on ball carrier |
| `wide` | Tactical | 1.2x | Full field view |
| `training` | Analysis | 1.8x | Steady for review |
| `manual_assist` | Hybrid | 1.5x | AI suggests, human overrides |

### Safety Layer

Every servo command passes through validation:
- **Angle limits:** 0-180° per axis
- **Jump limit:** Max 15° per command
- **Speed limit:** Max 120°/s
- **Watchdog:** 2s timeout triggers emergency stop
- **Disconnect safety:** ESP32 disconnect triggers emergency stop
- **Emergency stop:** Manual button or software trigger

---

## Configuration

All config in `configs/*.yaml`. No hardcoded values.

```yaml
# configs/camera.yaml
camera:
  source_type: "auto"
  discovery_enabled: true
  discovery_port: 9999
  resolution:
    width: 3840
    height: 2160
  fps: 30
```

Environment variables override YAML:
```bash
NETWORK__PORT=9000  # Overrides configs/network.yaml → port
```

---

## API Reference

**Base URL:** `http://localhost:8000`

### System
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/system/status` | GET | State machine status |
| `/api/system/state/{name}` | POST | Transition state |

### Camera
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/camera/status` | GET | Camera status |
| `/api/camera/start` | POST | Start capture |
| `/api/camera/stop` | POST | Stop capture |

### Servo
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/servo/status` | GET | Current angles |
| `/api/servo/command` | POST | Send pan/tilt |
| `/api/servo/home` | POST | Home to 90°, 90° |
| `/api/servo/emergency` | POST | Emergency stop |

### Director
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/director/status` | GET | Mode + last decision |
| `/api/director/mode/{mode}` | POST | Set mode |

### Output
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/output/mode` | GET/POST | Get/set output mode |
| `/api/output/state` | GET | Current output state |
| `/api/output/reset` | POST | Reset to defaults |

### WebSocket
| Endpoint | Protocol | Description |
|----------|----------|-------------|
| `/ws` | WebSocket | Real-time events |

---

## Phone Camera App

### Features
- Camera2 API with JPEG capture (correct colors from camera ISP)
- MJPEG streaming server on port 8080
- UDP auto-discovery on port 9999
- Resolution selector: 4K / 1080p / 720p / Auto
- Beautiful glass-morphism UI with gradient overlays
- Live connection status indicator
- Bandwidth measurement and resolution recommendation

### Streaming Protocol
1. Phone captures JPEG frames via Camera2 API
2. StreamServer sends MJPEG multipart response on port 8080
3. Backend's `HttpCameraSource` connects and reads frames
4. DiscoveryService broadcasts phone IP via UDP every 2 seconds

---

## ESP32 Firmware

### Pin Configuration
| GPIO | Function |
|------|----------|
| 25 | Emergency stop button (INPUT_PULLUP) |
| 26 | Manual override button (INPUT_PULLUP) |
| 13 | Pan servo (LEDC PWM) |
| 12 | Tilt servo (LEDC PWM) |
| 2 | Status LED |

### Safety Features
- Hardware watchdog (15s timeout)
- Debounced button inputs (250ms)
- Emergency stop bypasses all logic
- Auto-reconnect WiFi (10s interval)
- Servo easing for smooth motion

---

## Development

### Running Tests

```bash
cd backend
PYTHONPATH="D:\FieldVision AI;D:\FieldVision AI\backend" pytest tests/ -v
```

### Code Style
- **Python:** PEP 8, type hints, docstrings
- **Kotlin:** Android conventions, coroutines
- **TypeScript:** Strict mode, no `any`

### Architecture Rules
- No Docker, Flask, global variables, blocking loops
- All config in YAML, no hardcoded values
- Event-driven via EventBus, no direct service coupling
- AI outputs `CameraState` (normalized 0-1), never hardware commands
- All servo commands pass through SafetyLayer

---

## Design Decisions

### Why MJPEG over WebRTC?
MJPEG is simpler, works everywhere, and the phone is on the same WiFi network. WebRTC adds complexity (signaling server, ICE candidates) for minimal latency benefit on LAN.

### Why Normalized Coordinates?
The AI should not know about servo angles or pixel resolutions. `CameraState` uses 0-1 normalized coordinates so the same Director works with virtual crop, servo, or PTZ output.

### Why a Safety Layer?
Physical servos can damage themselves or injure someone. The SafetyLayer is a mandatory checkpoint between AI decisions and hardware commands. It validates angles, limits speed, and triggers emergency stop on disconnect.

### Why Event-Driven?
Services don't know about each other. The VisionService doesn't know who consumes its detections. This makes it easy to add new consumers (replay system, analytics) without modifying existing code.

---

## License

Private — FieldVision AI Team

---

*Built with ❤️ for automated sports broadcasting.*
