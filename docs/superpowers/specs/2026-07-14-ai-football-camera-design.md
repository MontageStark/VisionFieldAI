# FieldVision AI — Design Spec

**Version:** 3.0
**Date:** 2026-07-14
**Status:** Approved

---

## 1. Overview

FieldVision AI is an event-driven robotic football camera system that automatically tracks matches using a single Android phone mounted on a rotating platform. The phone streams video over WiFi to a Windows laptop running YOLO11 inference on a GTX 1650 GPU. The system uses a **Director Service** with selectable modes to decide where the audience should look — not just following the ball, but understanding play context, predicting movement, and producing cinematic camera motion. Commands are sent to an ESP32 over WebSockets, which rotates a DS3235 servo carrying the phone.

**Goal:** Produce smooth, cinematic camera movement suitable for live streaming to YouTube.

**Architecture Pattern:** Event-driven robotics system. Every service publishes events when done, subscribes to events it needs. No direct coupling between modules.

---

## 2. System Architecture

### 2.1 Three-Node Design

| Node | Role | Communication |
|------|------|---------------|
| Android Phone | Camera capture, RTSP stream | WiFi → Laptop |
| Windows Laptop | AI inference, Director, control logic, dashboard | WebSocket → ESP32 |
| ESP32 DevKit | Servo driver, motion execution | PWM → Servo |

### 2.2 Event-Driven Data Flow

```
Frame Captured (Camera Service)
    ↓ [event: frame.ready]
Vision Service (YOLO11 Detection)
    ↓ [event: detection.ready]
Tracking Service (ByteTrack)
    ↓ [event: track.ready]
Director Service (Decision Engine)
    ↓ [event: director.decision]
Motion Planner (Cinematic Trajectory)
    ↓ [event: motion.plan]
Servo Controller (PID + Safety)
    ↓ [event: servo.command]
ESP32 (PWM Execution)
```

Each service is independent. Publish an event when done. Subscribe to events you need. That's the entire architecture.

### 2.3 Monorepo Structure

```
FieldVision AI/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── state.py
│   │   │   ├── events.py
│   │   │   ├── logging.py
│   │   │   └── dependencies.py
│   │   ├── services/
│   │   │   ├── camera/
│   │   │   ├── vision/              # YOLO11 detection
│   │   │   ├── tracking/            # ByteTrack
│   │   │   ├── director/            # Decision engine
│   │   │   ├── prediction/          # Kalman, trajectory
│   │   │   ├── motion/
│   │   │   │   ├── planner/
│   │   │   │   ├── controller/
│   │   │   │   └── safety/
│   │   │   ├── calibration/
│   │   │   ├── communication/
│   │   │   ├── streaming/
│   │   │   ├── monitoring/
│   │   │   ├── replay/
│   │   │   └── analytics/
│   │   ├── models/
│   │   └── api/
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Camera.tsx
│   │   │   ├── Servo.tsx
│   │   │   ├── Director.tsx
│   │   │   ├── Calibration.tsx
│   │   │   ├── Streaming.tsx
│   │   │   ├── Replay.tsx
│   │   │   ├── Health.tsx
│   │   │   ├── Logs.tsx
│   │   │   └── Settings.tsx
│   │   ├── hooks/
│   │   ├── services/
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
├── firmware/
│   ├── src/
│   ├── platformio.ini
│   └── include/
├── configs/
├── profiles/
├── plugins/
├── models/
├── logs/
├── recordings/
├── scripts/
├── tests/
├── docs/
└── assets/
```

---

## 3. System State Machine

No booleans. Explicit states only.

### 3.1 States

```
BOOTING → CONNECTING → IDLE → STREAMING → TRACKING
                ↓                    ↓
             ERROR               MANUAL
                ↓                    ↓
          EMERGENCY_STOP ←────── HOMING
```

| State | Description |
|-------|-------------|
| `BOOTING` | System initializing, loading config |
| `CONNECTING` | Waiting for camera + ESP32 connection |
| `IDLE` | Connected but not capturing |
| `STREAMING` | Camera capturing, no AI tracking |
| `TRACKING` | Full AI pipeline active |
| `MANUAL` | User controlling servo via dashboard |
| `HOMING` | Servo returning to center position |
| `EMERGENCY_STOP` | Safety stop, servo locked |
| `ERROR` | Unrecoverable error, requires restart |

### 3.2 State Transitions

```python
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

VALID_TRANSITIONS = {
    SystemState.BOOTING: [SystemState.CONNECTING, SystemState.ERROR],
    SystemState.CONNECTING: [SystemState.IDLE, SystemState.ERROR],
    SystemState.IDLE: [SystemState.STREAMING, SystemState.CONNECTING, SystemState.ERROR],
    SystemState.STREAMING: [SystemState.TRACKING, SystemState.IDLE, SystemState.MANUAL, SystemState.ERROR],
    SystemState.TRACKING: [SystemState.STREAMING, SystemState.MANUAL, SystemState.HOMING, SystemState.EMERGENCY_STOP, SystemState.ERROR],
    SystemState.MANUAL: [SystemState.TRACKING, SystemState.HOMING, SystemState.EMERGENCY_STOP],
    SystemState.HOMING: [SystemState.IDLE, SystemState.TRACKING, SystemState.EMERGENCY_STOP],
    SystemState.EMERGENCY_STOP: [SystemState.IDLE, SystemState.HOMING],
    SystemState.ERROR: [SystemState.BOOTING],
}
```

---

## 4. Message Bus

All services communicate through an in-process event bus. No direct coupling.

### 4.1 Event Types

| Event | Publisher | Subscriber | Data |
|-------|-----------|------------|------|
| `frame.ready` | Camera | Vision | frame, timestamp |
| `detection.ready` | Vision | Tracking, Analytics | detections, frame_id |
| `track.ready` | Tracking | Director, Analytics | tracks, frame_id |
| `director.decision` | Director | Motion Planner | target_angle, mode, reasoning |
| `motion.plan` | Motion Planner | Servo Controller | angle, speed, accel |
| `servo.command` | Servo Controller | ESP32 | target_angle, mode |
| `servo.status` | ESP32 | Monitoring | current_angle, health |
| `state.changed` | State Machine | All | old_state, new_state |
| `alert` | Any | Dashboard, Logging | severity, message, source |
| `performance.warning` | Monitoring | Director | metric, value, threshold |
| `safety.trigger` | Safety Layer | All | violation_type, action |

### 4.2 Implementation

```python
class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}

    def subscribe(self, event: str, handler: Callable) -> None:
        self._subscribers.setdefault(event, []).append(handler)

    async def publish(self, event: str, data: Any) -> None:
        for handler in self._subscribers.get(event, []):
            await handler(data)
```

---

## 5. Director Service

The Director is the brain. It decides **where the audience should look**.

### 5.1 Director Modes

| Mode | Use Case | Behavior |
|------|----------|----------|
| `broadcast` | Normal match play | TV-style framing, balanced smoothness |
| `aggressive` | High-intensity moments | Follows action closely, faster response |
| `wide` | Tactical analysis | Keeps more field visible, slower movement |
| `training` | Coaching sessions | Focuses tightly on ball, minimal smoothing |
| `manual_assist` | Operator-assisted | AI suggests, operator can nudge |

### 5.2 What the Director Decides

- Should the camera move?
- Should it wait (ball is stationary)?
- Should it lead the ball (ball is moving fast)?
- Should it keep extra space ahead of an attacking player?
- Is the ball lost (occluded, off-screen)?
- Is this a goal kick (ball out of play)?
- Is play stopped (foul, injury)?
- Should it widen the frame (multiple players in view)?
- Which Director Mode to use (auto-switch based on context)?

### 5.3 Director Logic

```python
class DirectorDecision:
    target_x: float
    target_y: float
    confidence: float
    movement_type: str       # "static", "following", "leading", "wide", "searching"
    director_mode: str       # "broadcast", "aggressive", "wide", "training", "manual_assist"
    reasoning: str
    priority: int

class Director:
    async def decide(self, tracks: List[Track], context: PlayContext, mode: DirectorMode) -> DirectorDecision:
        # 1. Check for emergency conditions (ball lost, play stopped)
        # 2. Auto-switch mode if needed (e.g., goal scored → wide)
        # 3. Compute weighted centroid of relevant entities
        # 4. Apply mode-specific behavior
        # 5. Apply field zone priorities
        # 6. Return decision with reasoning
```

### 5.4 Movement Types

| Type | When | Behavior |
|------|------|----------|
| `static` | Ball stationary, no movement | Hold position |
| `following` | Ball moving, close range | Track ball directly |
| `leading` | Ball moving fast, long range | Lead the ball by predicted position |
| `wide` | Multiple players, loose ball | Wider view to capture context |
| `searching` | Ball lost/occluded | Scan last known area |

### 5.5 Play Context

```python
@dataclass
class PlayContext:
    ball_speed: float
    ball_trajectory: Trajectory
    player_count: int
    nearest_player_distance: float
    in_penalty_area: bool
    in_goal_area: bool
    play_intensity: float
    time_since_last_touch: float
```

---

## 6. AI Services (Modular)

### 6.1 Vision Service

- YOLO11 nano model (`yolo11n.pt`) — 2.6M params, ~15ms on GTX 1650
- Classes: ball (0), player (1), goalkeeper (2)
- Confidence threshold: configurable
- Input resolution: 640x640 (letterboxed)
- Publishes: `detection.ready`

### 6.2 Tracking Service

- ByteTrack for multi-object tracking
- IOU matching with configurable threshold
- Track persistence: 30 frames (1 second at 30fps)
- Assigns stable IDs to players and ball across frames
- Publishes: `track.ready`

### 6.3 Director Service

- See Section 5 above
- Subscribes to: `track.ready`
- Publishes: `director.decision`

### 6.4 Prediction Service

- Kalman filter for position smoothing
- State: [x, y, vx, vy] (position + velocity)
- Predicts next position 1 frame ahead
- Trajectory extrapolation for leading shots
- Subscribes to: `track.ready`
- Publishes: `prediction.ready`

### 6.5 Analytics Service

- Player density heatmaps
- Ball possession tracking
- Movement speed statistics
- Play intensity scoring
- Subscribes to: `track.ready`, `detection.ready`
- Publishes: `analytics.update`

---

## 7. Motion Planner

Creates cinematic movement, not robotic tracking.

### 7.1 Trajectory Generation

Instead of jumping between angles:
```
90° → 95° → 83° → 97°
```

Generate smooth trajectories:
```
90 → 91 → 92 → 93 → 94 → 95
```

### 7.2 Cinematic Rules

- **Ease-in/ease-out:** Smooth acceleration and deceleration
- **Look-ahead:** Camera leads the action by 0.3 seconds
- **Damping:** Reduce oscillation near target
- **Dead zone:** Ignore movements <1.5°
- **Speed limit:** Max 120°/s (servo capability)
- **Acceleration limit:** Max 200°/s²

### 7.3 Motion Profiles

| Profile | Use Case | Speed | Smoothness |
|---------|----------|-------|------------|
| `broadcast` | Normal play | Medium | High |
| `fast_break` | Counter-attack | Fast | Medium |
| `set_piece` | Corner, free kick | Slow | Very High |
| `goal_celebration` | Goal scored | Slow | High |

---

## 8. Safety Layer

Never allow unsafe commands. Always keep the watchdog running.

### 8.1 Safety Rules

| Rule | Description | Action |
|------|-------------|--------|
| Angle limits | Servo must never exceed min/max angles | Clamp to limits |
| Jump limit | No sudden movement >45° in one command | Split into steps |
| Speed limit | Max 120°/s | Clamp speed |
| Disconnect safety | No commands when ESP32 disconnected | Hold position |
| Watchdog | No command for 15s → auto-stop | Emergency stop |
| Emergency button | Physical button on GPIO 25 | Immediate stop |
| Temperature | Servo temperature >60°C | Reduce speed |
| Current | Servo current >4A sustained | Emergency stop |

### 8.2 Safety Implementation

```python
class SafetyLayer:
    def validate_command(self, command: ServoCommand, state: SystemState) -> ServoCommand:
        # 1. Check state allows movement
        # 2. Clamp angle to limits
        # 3. Limit speed to max
        # 4. Split large jumps into steps
        # 5. Check ESP32 connection
        # 6. Check watchdog status
        # 7. Return validated (or rejected) command
```

### 8.3 Safety Events

| Event | Severity | Action |
|-------|----------|--------|
| `SAFETY_ANGLE_EXCEEDED` | WARNING | Command clamped |
| `SAFETY_JUMP_LIMIT` | WARNING | Command split into steps |
| `SAFETY_DISCONNECT` | ERROR | Command rejected, hold position |
| `SAFETY_WATCHDOG` | CRITICAL | Emergency stop |
| `SAFETY_EMERGENCY_BUTTON` | CRITICAL | Emergency stop |
| `SAFETY_OVERCURRENT` | CRITICAL | Emergency stop, alert |

---

## 9. PID Controller

- Proportional: Kp=1.2 — responds to current error
- Integral: Ki=0.01 — eliminates steady-state error
- Derivative: Kd=0.3 — dampens oscillation
- Output limit: 120°/s (matches servo max speed)
- Anti-windup: clamp integral term
- Auto-tuning via Ziegler-Nichols method

---

## 10. Performance Manager

Automatically adapts to GPU/CPU load.

### 10.1 Resolution Scaling

```
FPS > 25: 1080p (full quality)
FPS 20-25: 720p (balanced)
FPS 15-20: 540p (performance)
FPS < 15: Alert + pause tracking
```

### 10.2 Model Scaling

```
GPU memory < 60%: YOLO11s (best accuracy)
GPU memory 60-80%: YOLO11n (balanced)
GPU memory > 80%: YOLO11n + reduced input
GPU unavailable: CPU fallback (YOLO11n)
```

### 10.3 Health Monitor

Real-time system health with green/yellow/red indicators.

| Metric | Green | Yellow | Red |
|--------|-------|--------|-----|
| FPS | >25 | 15-25 | <15 |
| GPU Usage | <60% | 60-85% | >85% |
| GPU Temperature | <70°C | 70-85°C | >85°C |
| CPU Usage | <60% | 60-85% | >85% |
| RAM Usage | <60% | 60-85% | >85% |
| WiFi Latency | <20ms | 20-50ms | >50ms |
| ESP32 Heartbeat | <5s | 5-10s | >10s |
| Camera Latency | <100ms | 100-200ms | >200ms |

Dashboard shows color-coded status for each metric.

---

## 11. Calibration Profiles

Support multiple venue configurations.

### 11.1 Profile Structure

```yaml
# profiles/church_ground.yaml
name: "Church Ground"
venue: "St Mary's Church Field"
date: "2026-07-14"

servo:
  min_angle: 5.0
  max_angle: 175.0
  center_angle: 90.0
  dead_zone: 1.5

camera:
  horizontal_fov: 62.5
  vertical_fov: 38.0
  distortion_coefficients: [0.0, 0.0, 0.0, 0.0, 0.0]
  pixel_to_angle_lut: "profiles/church_ground_lut.npy"

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

### 11.2 Calibration Wizard

Step-by-step calibration via dashboard. No YAML editing required.

```
Calibration Wizard
    ↓
Step 1: Center Servo (move to 90°, confirm)
    ↓
Step 2: Set Left Limit (move to left extreme, confirm)
    ↓
Step 3: Set Right Limit (move to right extreme, confirm)
    ↓
Step 4: Measure FOV (show test pattern, user inputs angle)
    ↓
Step 5: Generate LUT (pixel-to-angle lookup table)
    ↓
Step 6: Save Profile (name it, store to profiles/)
```

### 11.3 Profile Selection

- Default profile loaded at startup
- Switch via dashboard or API
- Last-used profile remembered
- One-click switch between profiles

---

## 12. Simulation Mode

Develop and test without hardware.

### 12.1 Simulation Sources

- Video file (MP4, AVI, MKV)
- Image sequence folder
- Synthetic frame generator (test patterns)
- Network stream (simulated RTSP)

### 12.2 Simulation Behavior

```
video.mp4 → Camera Service → Vision → Tracking → Director → Motion Planner
                                                                    ↓
                                                          Virtual Servo (log only)
                                                                    ↓
                                                          Dashboard (live view)
```

- No ESP32 required
- No real servo
- Servo commands logged to file
- Dashboard shows simulated angles
- FPS measured same as real mode

### 12.3 Activation

```yaml
# configs/simulation.yaml
enabled: true
source_type: "video"
source_path: "recordings/match_sample.mp4"
loop: true
speed: 1.0
```

---

## 13. Replay System

Record every frame for later analysis.

### 13.1 What's Saved

Per frame:
- Frame image (compressed JPEG)
- YOLO detections (bounding boxes, classes, confidence)
- ByteTrack assignments (track IDs, positions)
- Director decision (target, movement type, reasoning)
- Servo angle (current + target)
- Inference time
- Timestamp

### 13.2 Storage Format

```
recordings/
├── 2026-07-14_match_001/
│   ├── metadata.json
│   ├── frames/
│   │   ├── 000001.jpg
│   │   ├── 000002.jpg
│   │   └── ...
│   ├── detections.jsonl
│   ├── tracks.jsonl
│   ├── director_decisions.jsonl
│   ├── servo_log.jsonl
│   ├── performance_log.jsonl
│   └── replay_index.json
```

### 13.3 Replay Viewer

- Load a recording in the dashboard
- Step through frame by frame
- See what the AI saw (detections overlay)
- See what the Director decided
- See servo angle over time
- Export clips

### 13.4 Event Timeline

During replay, show timeline of events:

| Timestamp | Event | Details |
|-----------|-------|---------|
| 00:05:23 | `BALL_LOST` | Ball occluded by player |
| 00:05:25 | `BALL_FOUND` | Ball re-acquired at (450, 320) |
| 00:12:45 | `GOAL_SCORED` | Ball crossed goal line |
| 00:15:02 | `CAMERA_RECONNECT` | Camera reconnected after 2s |
| 00:20:15 | `LOW_FPS` | FPS dropped to 18 |

---

## 14. Plugin Architecture

Extensible without touching core code.

### 14.1 Plugin Interface

```python
class Plugin(ABC):
    name: str
    version: str

    @abstractmethod
    async def initialize(self, config: dict, event_bus: EventBus) -> None: ...

    @abstractmethod
    async def shutdown(self) -> None: ...

    @abstractmethod
    def get_subscribed_events(self) -> List[str]: ...

    @abstractmethod
    async def handle_event(self, event: str, data: Any) -> Optional[Any]: ...
```

### 14.2 Plugin Discovery

- Plugins live in `plugins/` directory
- Each plugin has `plugin.yaml` manifest
- Auto-discovered at startup
- Loaded based on config enable/disable

### 14.3 Example Plugins

| Plugin | Description |
|--------|-------------|
| `goal_detection` | Detects goals, triggers highlight |
| `highlights` | Auto-generates highlight reel |
| `analytics` | Advanced player analytics |
| `whistle_detection` | Audio-based play detection |
| `offside_detector` | Offside line overlay |
| `commentary` | AI-generated commentary |
| `telegram_alerts` | Sends alerts to Telegram |
| `discord_bot` | Posts updates to Discord |

---

## 15. Configuration

All configuration lives in `configs/*.yaml`. No hardcoded values.

### 15.1 camera.yaml

```yaml
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

### 15.2 servo.yaml

```yaml
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

### 15.3 network.yaml

```yaml
wifi_ssid: "FieldVision"
wifi_password: ""
websocket_port: 0
heartbeat_interval: 5.0
watchdog_timeout: 15.0
```

### 15.4 ai.yaml

```yaml
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

### 15.5 stream.yaml

```yaml
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

### 15.6 dashboard.yaml

```yaml
host: "127.0.0.1"
port: 0
log_level: "info"
refresh_rate: 1000
metrics_history: 3600
```

### 15.7 simulation.yaml

```yaml
enabled: false
source_type: "video"
source_path: ""
loop: false
speed: 1.0
```

---

## 16. Resource Isolation

The system must not interfere with other applications.

### 16.1 GPU Isolation

- GTX 1650 has 4GB VRAM
- Reserve max 2GB for YOLO11 inference
- Use `torch.cuda.set_device(0)` and `torch.cuda.memory.set_per_process_memory_fraction(0.5)`
- Fallback to CPU if GPU is unavailable or overloaded

### 16.2 CPU Isolation

- Cap inference threads to 2 cores
- Environment variables: `OMP_NUM_THREADS=2`, `MKL_NUM_THREADS=2`
- Use `torch.set_num_threads(2)`
- Frame grabber runs in a separate thread with lower priority

### 16.3 Memory Isolation

- YOLO11 nano model: ~3GB RAM
- FastAPI + services: ~200MB
- React dashboard: ~150MB
- Total peak: ~3.5GB
- Monitor via `psutil` and log warnings above 4GB

### 16.4 Network Isolation

- RTSP stream capped at 5Mbps (configurable)
- WebSocket traffic <50KB/s
- Dashboard served on localhost only
- No external network calls except OBS WebSocket and YouTube RTMP

### 16.5 Port Discovery

- All ports auto-discovered via `socket.bind(0)` — no fixed ports
- Backend writes assigned port to `configs/ports.yaml` at startup
- ESP32 reads port from backend status endpoint
- Dashboard proxy uses the discovered port

### 16.6 Process Safety

- No background services or daemons
- Clean shutdown via SIGINT/SIGTERM handlers
- No global mutable state
- SQLite uses WAL mode for concurrent reads
- No file locks — use atomic writes where needed

---

## 17. Structured Event Logging

### 17.1 Event Types

| Event | Category | Severity | Description |
|-------|----------|----------|-------------|
| `GOAL_SCORED` | match | INFO | Goal detected |
| `BALL_LOST` | tracking | WARNING | Ball not detected for >2s |
| `BALL_FOUND` | tracking | INFO | Ball re-acquired |
| `CAMERA_RECONNECT` | camera | INFO | Camera reconnected after disconnect |
| `CAMERA_DISCONNECT` | camera | ERROR | Camera connection lost |
| `ESP32_RECONNECT` | comm | INFO | ESP32 reconnected |
| `ESP32_DISCONNECT` | comm | ERROR | ESP32 connection lost |
| `SERVO_SATURATED` | servo | WARNING | Servo at max speed, can't keep up |
| `SERVO_ERROR` | servo | ERROR | Servo hardware error |
| `EMERGENCY_STOP` | safety | CRITICAL | Emergency stop triggered |
| `SAFETY_ANGLE_EXCEEDED` | safety | WARNING | Command clamped to limits |
| `SAFETY_JUMP_LIMIT` | safety | WARNING | Large jump split into steps |
| `SAFETY_WATCHDOG` | safety | CRITICAL | Watchdog timeout |
| `HIGH_CPU` | perf | WARNING | CPU usage >80% |
| `HIGH_GPU_TEMP` | perf | WARNING | GPU temperature >85°C |
| `LOW_FPS` | perf | WARNING | FPS dropped below threshold |
| `DROPPED_FRAME` | perf | INFO | Frame skipped due to load |
| `MODEL_SWITCH` | ai | INFO | Switched YOLO model due to load |
| `RESOLUTION_SWITCH` | ai | INFO | Changed resolution due to FPS |
| `DIRECTOR_DECISION` | ai | DEBUG | Director reasoning logged |
| `DIRECTOR_MODE_SWITCH` | ai | INFO | Director mode changed |
| `STATE_CHANGE` | system | INFO | System state transition |
| `CONFIG_CHANGE` | system | INFO | Configuration updated |
| `PLUGIN_LOADED` | system | INFO | Plugin loaded successfully |
| `PLUGIN_ERROR` | system | ERROR | Plugin failed to load |
| `PROFILE_LOADED` | calibration | INFO | Calibration profile loaded |
| `PROFILE_SWITCHED` | calibration | INFO | Profile changed |

### 17.2 Log Storage

- SQLite `logs/events.db` for structured queries
- Text files for real-time debugging:
  - `logs/servo.log`
  - `logs/camera.log`
  - `logs/tracking.log`
  - `logs/stream.log`
  - `logs/errors.log`
  - `logs/performance.log`

### 17.3 Log Rotation

- Text logs rotate daily, keep 7 days
- SQLite logs auto-archive after 30 days

---

## 18. Communication Protocol

### 18.1 Laptop → ESP32 (WebSocket)

```json
{
  "target_angle": 93.4,
  "mode": "AUTO",
  "timestamp": 1720000000000,
  "sequence": 1234
}
```

### 18.2 ESP32 → Laptop (WebSocket)

```json
{
  "current_angle": 93.2,
  "status": "OK",
  "mode": "AUTO",
  "uptime": 3600,
  "free_heap": 180000,
  "sequence": 1234
}
```

### 18.3 Heartbeat

- ESP32 sends heartbeat every 5 seconds
- Laptop expects heartbeat within 15 seconds
- Missing heartbeat triggers auto-stop on ESP32

---

## 19. Backend (FastAPI)

### 19.1 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System status, state, FPS, angles |
| `/api/camera/start` | POST | Start camera capture |
| `/api/camera/stop` | POST | Stop camera capture |
| `/api/camera/preview` | GET | MJPEG preview stream |
| `/api/servo/mode` | POST | Set mode (AUTO/MANUAL/HOME/STOP) |
| `/api/servo/angle` | POST | Set manual angle |
| `/api/calibration/wizard/start` | POST | Start calibration wizard |
| `/api/calibration/wizard/step` | POST | Submit wizard step |
| `/api/calibration/profile` | GET/PUT | Get/set calibration profile |
| `/api/calibration/profiles` | GET | List available profiles |
| `/api/ai/config` | GET/PUT | Get/update AI parameters |
| `/api/ai/detections` | GET | Current frame detections |
| `/api/ai/director` | GET | Director decision + reasoning |
| `/api/ai/mode` | GET/PUT | Get/set Director mode |
| `/api/stream/start` | POST | Start OBS stream |
| `/api/stream/stop` | POST | Stop OBS stream |
| `/api/record/start` | POST | Start recording |
| `/api/record/stop` | POST | Stop recording |
| `/api/replay/recordings` | GET | List recordings |
| `/api/replay/load` | POST | Load recording for review |
| `/api/replay/frame` | GET | Get specific frame data |
| `/api/health` | GET | System health (green/yellow/red) |
| `/api/logs` | GET | Query structured events |
| `/api/settings` | GET/PUT | Get/update settings |
| `/api/plugins` | GET | List plugins |
| `/api/simulation/start` | POST | Start simulation mode |
| `/api/simulation/stop` | POST | Stop simulation mode |
| `/ws` | WS | Real-time updates to dashboard |

### 19.2 WebSocket Server

- Broadcasts real-time metrics to connected dashboards
- Updates at 10Hz (100ms intervals)
- Messages: metrics, detections, director decisions, servo status, health, alerts

---

## 20. Frontend (Dashboard)

### 20.1 Pages

| Page | Description |
|------|-------------|
| Dashboard | Overview: state, FPS, latency, angles, connections, health |
| Camera | Live preview, stream health, frame stats |
| Servo | Angle display, manual control |
| Director | Director mode selector, decision breakdown, reasoning |
| Calibration | Calibration Wizard, profile management |
| Streaming | OBS controls, stream status, record |
| Replay | Load recordings, step through frames, event timeline |
| Health | System health overview (green/yellow/red) |
| Plugins | Enable/disable plugins, plugin status |
| Logs | Searchable structured event viewer |
| Settings | All configuration editors |

### 20.2 Real-Time Metrics Displayed

- System state (from state machine)
- FPS (capture + inference)
- Latency (capture to servo)
- Current servo angle / target angle
- Director mode + decision + reasoning
- Tracking confidence
- Detected players count
- Ball confidence
- Connection status (camera, ESP32, OBS)
- GPU usage / temperature
- CPU usage
- RAM usage
- WiFi latency
- Active profile name
- Health status (green/yellow/red per metric)

### 20.3 Tech Stack

- React 18 with TypeScript
- Vite for build
- TailwindCSS for styling
- Recharts for metrics charts
- WebSocket client for real-time data

---

## 21. OBS Integration

### 21.1 WebSocket Commands

- Start/stop streaming
- Start/stop recording
- Switch scenes
- Toggle overlay visibility
- Set lower third text

### 21.2 Stream Output

- RTMP to YouTube Live
- Configurable bitrate (default 4500kbps)
- 1080p30 output
- Hardware encoding via NVENC if available

---

## 22. Error Handling

| Error | Recovery |
|-------|----------|
| Camera disconnect | Auto-reconnect with backoff, log `CAMERA_DISCONNECT`, alert dashboard |
| ESP32 disconnect | Stop servo, hold position, log `ESP32_DISCONNECT`, alert dashboard |
| WiFi disconnect | ESP32 watchdog triggers auto-stop |
| OBS disconnect | Retry 3x, then alert, continue local recording |
| Servo failure | Emergency stop, log `SERVO_ERROR`, alert, manual intervention |
| Low FPS (<15) | Performance Manager scales down resolution/model, log `LOW_FPS` |
| Model failure | Fallback to CPU, reduce input size, alert |
| GPU OOM | Switch to CPU mode, log, alert |
| Ball lost >2s | Director enters `searching` mode, log `BALL_LOST` |
| State invalid transition | Log error, stay in current state |

---

## 23. Testing Strategy

### 23.1 Unit Tests

- Director decision logic (known tracks → expected decisions)
- Director mode switching (context → mode selection)
- Safety layer (command validation, clamping, jump splitting)
- Motion planner (trajectory generation, easing)
- PID controller (step response, overshoot, settling time)
- Kalman filter (synthetic trajectories)
- Pixel-to-angle mapper (known calibration → expected output)
- State machine (valid/invalid transitions)
- Event bus (publish/subscribe)
- Configuration loader (YAML validation)
- Performance manager (resolution/model switching logic)

### 23.2 Integration Tests

- Mock ESP32 WebSocket server
- Mock camera (video file → frame sequence)
- Mock OBS WebSocket
- End-to-end: video file → detections → Director → motion plan → servo command
- Dashboard renders without errors
- Plugin loading and event handling
- Simulation mode full pipeline
- Calibration wizard flow

### 23.3 Manual Tests

- Real camera stream → full pipeline
- Servo responds to AI commands
- Dashboard shows real-time metrics
- OBS streaming works
- Emergency stop works
- Calibration profile switching
- Replay recording and playback
- Director mode switching

---

## 24. Development Phases

| Phase | Scope | Dependencies |
|-------|-------|--------------|
| 1 | Project scaffold, config, state machine, event bus, logging, FastAPI, React, ESP32, WebSocket | None |
| 2 | Video capture, camera service, FPS monitor, simulation mode (video file) | Phase 1 |
| 3 | YOLO11 vision service, ByteTrack tracking service | Phase 1 |
| 4 | Director Service (all modes), Prediction Service, Kalman filter | Phase 3 |
| 5 | Motion Planner, PID controller, Safety Layer | Phase 4 |
| 6 | Communication service, servo control, ESP32 firmware | Phase 5 |
| 7 | Dashboard pages, OBS integration, manual/auto modes | Phase 6 |
| 8 | Performance Manager, Health Monitor, calibration profiles, Calibration Wizard | Phase 7 |
| 9 | Replay system, event timeline, plugin architecture | Phase 8 |
| 10 | Optimization, tests, documentation | Phase 9 |

**Rule:** Each phase must build and run before proceeding to the next.

---

## 25. Non-Goals (YAGNI for v1)

- Multi-camera support
- Tilt control (pan only for v1)
- Team logo detection
- Score overlay automation
- Mobile app (dashboard is web-based)
- Cloud deployment
- User authentication

---

## 26. Success Criteria

1. Camera tracks football matches automatically for 30+ minutes without manual intervention
2. Servo movement is smooth and cinematic (no jitter, no sudden jumps)
3. Director makes intelligent decisions with selectable modes
4. Safety layer prevents all unsafe commands
5. System runs at 20+ FPS inference speed
6. Dashboard shows real-time health with green/yellow/red indicators
7. OBS stream is stable at 1080p30
8. Emergency stop works within 100ms
9. System recovers from camera disconnect within 5 seconds
10. No interference with other system processes
11. Simulation mode works without any hardware
12. Calibration wizard works without YAML editing
13. Replay system captures full context for post-match analysis
14. Plugins can extend functionality without core code changes
15. Event timeline shows all events during replay
