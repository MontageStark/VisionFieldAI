# FieldVision AI

**AI-powered robotic football camera system with auto-framing, WiFi streaming, and virtual camera output.**

FieldVision AI uses a smartphone camera, YOLO11 object detection, ByteTrack multi-object tracking, and an intelligent Director engine to automatically frame football matches — outputting to either a software virtual crop (for OBS) or physical servo-mounted cameras via ESP32.

```
Phone Camera ──WiFi/MJPEG──► Backend Proxy ──► React Frontend (live preview)
                                │
                                ├──► Virtual Camera (OBS)
                                └──WebSocket──► ESP32 ──► DS3235 Servos
```

---

## Features

- **WiFi Camera Streaming** — Phone streams MJPEG over WiFi, no USB cable needed
- **AI Auto-Framing** — YOLO11 detects players, ball, goalkeeper, referee; Director engine composes cinematic shots
- **Multi-Device Support** — Works with Poco M2 Pro, Redmi, and other Android devices
- **Virtual Camera** — Software crop/pan/zoom output directly to OBS virtual camera
- **Physical Servo Control** — DS3235 pan/tilt servos via ESP32 WebSocket
- **5 Director Modes** — Broadcast, Aggressive, Wide, Training, Manual Assist
- **Safety Layer** — Angle limits, jump limiting, watchdog timer, emergency stop, disconnect detection
- **Real-time Dashboard** — React frontend with live camera preview and controls

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, FastAPI, OpenCV, YOLO11 (ultralytics), ByteTrack, PyTorch CUDA |
| **Android** | Kotlin, Camera2 API, YUV_420_888→JPEG conversion, MJPEG streaming |
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
python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8001
```

Backend starts on `http://localhost:8001`. API docs at `/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard opens at `http://localhost:5173`.

### 3. Android App

```bash
cd android-app
./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

Grant camera permission. The app starts streaming MJPEG on port 8080.

### 4. ESP32 (Optional)

```bash
cd firmware
platformio run --target upload
```

ESP32 connects to WiFi, connects to backend via WebSocket, and waits for servo commands.

### 5. WiFi Streaming

1. Open `http://localhost:5173/stream`
2. Enter phone's WiFi IP (e.g., `192.168.0.187`)
3. Click **Go Live**
4. Camera feed appears in the browser

---

## Project Structure

```
FieldVision AI/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app factory
│   │   ├── core/
│   │   │   ├── events.py           # EventBus (pub/sub, 23 event types)
│   │   │   └── state.py            # SystemStateMachine (9 states)
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
│   │       ├── stream.py           # MJPEG proxy (/api/stream/proxy)
│   │       └── ...
│   └── tests/                      # Backend test suite
├── android-app/
│   └── app/src/main/java/com/fieldvision/camera/
│       ├── MainActivity.kt         # Camera2 + YUV conversion + streaming
│       ├── stream/
│       │   └── StreamServer.kt     # MJPEG TCP server on port 8080
│       ├── network/                # Network monitoring
│       ├── di/                     # Hilt dependency injection
│       ├── data/                   # Room database
│       └── device/                 # Device telemetry
├── frontend/
│   └── src/
│       ├── App.tsx                 # React Router
│       ├── services/               # API client layer
│       ├── stores/                 # Zustand state stores
│       ├── pages/
│       │   └── Streaming/
│       │       └── Streaming.tsx   # Live camera preview (<img> MJPEG)
│       └── components/             # UI components
├── firmware/                       # ESP32 servo controller
├── configs/                        # YAML configuration
├── arch-v1.md                      # In-depth architecture
└── AGENTS.md                       # AI agent instructions
```

---

## Architecture

See [arch-v1.md](./arch-v1.md) for the complete in-depth architecture document.

### Streaming Pipeline

```
Phone (Camera2 API)
  │
  ├─ YUV_420_888 → JPEG conversion (runtime)
  ├─ StreamServer (TCP port 8080, MJPEG multipart)
  │
  └──WiFi──► Backend Proxy (/api/stream/proxy?phone_ip=X&port=8080)
                │
                └──► Frontend <img> (multipart/x-mixed-replace)
```

**Phone → WiFi → Browser:** No USB cable required. Phone streams directly over WiFi.

### Camera Pipeline (Android)

```
Camera2 API (TEMPLATE_PREVIEW)
  │
  ├─ ImageReader (YUV_420_888, 1280x720, buffer=4)
  │    └─ onImageAvailable → yuv420ToJpeg() → StreamServer.sendFrameJpeg()
  │
  ├─ TextureView (preview surface)
  │
  └─ Frame Watchdog (5s timeout → auto-reopen camera)
```

**Why YUV_420_888?** Some devices (Poco M2 Pro) have broken JPEG encoders in Camera2 HAL. YUV conversion bypasses this.

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

---

## Configuration

All config in `configs/*.yaml`. No hardcoded values.

```yaml
# configs/camera.yaml
camera:
  source_type: "auto"
  http_url: "192.168.0.187:8080"
  resolution:
    width: 1280
    height: 720
  fps: 30
```

---

## API Reference

**Base URL:** `http://localhost:8001`

### Streaming
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stream/proxy` | GET | MJPEG proxy (phone_ip, port params) |
| `/api/stream/status` | GET | Stream status |

### System
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/system/status` | GET | State machine status |

### Camera
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/camera/status` | GET | Camera status |
| `/api/camera/start` | POST | Start capture |
| `/api/camera/stop` | POST | Stop capture |

### Director
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/director/status` | GET | Mode + last decision |
| `/api/director/mode/{mode}` | POST | Set mode |

---

## Phone Camera App

### Features
- Camera2 API with YUV_420_888 → JPEG conversion (cross-device compatible)
- MJPEG streaming server on port 8080
- WiFi streaming (no USB cable needed)
- Frame watchdog (auto-reopens camera on HAL error)
- Error code 3 recovery with unlimited retries
- Beautiful glass-morphism UI

### Streaming Protocol
1. Camera2 captures YUV_420_888 frames via ImageReader
2. Runtime converts YUV → JPEG using `YuvImage.compressToJpeg()`
3. StreamServer sends MJPEG multipart response on port 8080
4. Browser displays via `<img src="multipart/x-mixed-replace">`

---

## Design Decisions

### Why MJPEG over WebRTC?
MJPEG is simpler, works everywhere, and the phone is on the same WiFi network. WebRTC adds complexity (signaling server, ICE candidates) for minimal latency benefit on LAN.

### Why YUV_420_888 over JPEG?
Some Android devices (Poco M2 Pro) have broken JPEG encoders in Camera2 HAL. YUV_420_888 is universally supported and we convert to JPEG in Kotlin using `YuvImage.compressToJpeg()`.

### Why WiFi Streaming?
Eliminates USB cable dependency. Phone streams directly over WiFi to the backend proxy, which forwards to the browser.

---

## License

Private — FieldVision AI Team
