# FieldVision Camera App Design Spec v1.0

**Date:** 2026-07-15  
**Status:** Approved  
**Scope:** Android phone camera app + backend HTTP camera source + auto-discovery

---

## 1. Overview

The FieldVision Camera App is an Android application that captures 4K video from the phone's rear camera and streams it to the FieldVision AI backend over WiFi. The app features auto-discovery of laptops running the backend, three-tier protocol fallback (WebRTC → H.264 → MJPEG), and manual camera controls. Match info overlay is handled separately in OBS.

### 1.1 Goals
- Stream 4K@30fps video from phone to laptop with <100ms latency
- Auto-discover backend on same WiFi network (no manual IP entry)
- Auto-adapt resolution based on WiFi quality
- Support all connection scenarios (hotspot, router, WiFi Direct, venue WiFi)
- Manual camera controls for varying light conditions

### 1.2 Non-Goals (v1)
- Recording to phone storage
- Multiple camera angles from one phone
- Cloud streaming (all local WiFi)
- iOS support (Android only)
- Authentication/encryption (local network assumed safe)

---

## 2. Architecture

### 2.1 System Diagram

```
┌─────────────────┐      WiFi       ┌─────────────────┐
│  Android Phone  │ ──stream──────> │  FieldVision    │
│  Camera App     │   WebRTC/H264/  │  Backend        │
│                 │   MJPEG         │  (Python)       │
│  - Camera2 API  │                 │  - AI Pipeline  │
│  - HTTP Server  │ <──UDP─────── │  - Discovery    │
│  - Discovery    │   broadcast     │  - VirtualCam   │
└─────────────────┘                 │  Output        │
                                    └────────┬──────┘
                                             │
                                             ▼
                                      ┌──────────────┐
                                      │  OBS Studio  │
                                      │  + Overlay   │
                                      │  → YouTube   │
                                      └──────────────┘
```

### 2.2 Connection Modes

| Mode | Phone IP | Laptop IP | Use Case |
|------|----------|-----------|----------|
| Same WiFi | 192.168.1.x | 192.168.1.y | Home/office WiFi |
| Phone Hotspot | 192.168.43.x | 192.168.43.y | Field (no router) |
| WiFi Direct | 192.168.49.x | 192.168.49.y | Direct P2P |
| Venue WiFi | Dynamic | Dynamic | Stadium WiFi |
| Manual | Any | Any | Fallback |

---

## 3. Android App

### 3.1 Components

| Component | File | Purpose |
|-----------|------|---------|
| MainActivity | MainActivity.kt | UI: preview, resolution picker, status |
| CameraEngine | CameraEngine.kt | Camera2 API: capture at 4K/1080p/720p, manual controls |
| StreamServer | StreamServer.kt | HTTP server on port 8080, serves video stream |
| DiscoveryService | DiscoveryService.kt | UDP broadcast every 2s, listens for laptop responses |
| NetworkMonitor | NetworkMonitor.kt | Detects connection type, auto-downgrades quality |

### 3.2 UI Layout

```
┌─────────────────────────────────────────┐
│            FieldVision Camera           │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐    │
│  │                                 │    │
│  │       Camera Preview            │    │
│  │       (SurfaceView)             │    │
│  │                                 │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Resolution: [4K] [1080p] [720p] [Auto]│
│                                         │
│  Found: LAPTOP-ABC (192.168.1.10)      │
│  Protocol: H.264 | FPS: 30 | 8 Mbps   │
│                                         │
│  ┌─ Camera Controls ────────────────┐   │
│  │ Exposure: [-2] [====|====] [+2] │   │
│  │ WB: [Auto] [2500K] [5500K] [8K] │   │
│  │ Focus: [Auto] [Manual]          │   │
│  │ Torch: [On] [Off]               │   │
│  └──────────────────────────────────┘   │
│                                         │
│  [ Start Streaming ]  [ Settings ]      │
└─────────────────────────────────────────┘
```

### 3.3 Camera Controls

| Control | Range | Default | API |
|---------|-------|---------|-----|
| Exposure | -2.0 to +2.0 EV | 0.0 (auto) | CaptureRequest.CONTROL_AE_EXPOSURE_COMPENSATION |
| White Balance | 2000K-8000K / Auto | Auto | CaptureRequest.CONTROL_AWB_MODE |
| Focus | Auto / Manual (tap) | Auto | CaptureRequest.CONTROL_AF_MODE |
| Torch | On / Off | Off | CaptureRequest.FLASH_MODE |
| Resolution | 4K / 1080p / 720p / Auto | Auto | CameraCharacteristics |
| FPS | 30 / 24 / 15 | 30 | CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE |

### 3.4 Resolution Auto-Adapt

```
IF bandwidth > 20 Mbps:
    resolution = 4K (3840x2160)
ELIF bandwidth > 10 Mbps:
    resolution = 1080p (1920x1080)
ELSE:
    resolution = 720p (1280x720)

Bandwidth measured by:
- First 5 seconds of stream: count successful frames
- If frame drops > 10%: downgrade resolution
- If frame drops < 2% for 10s: try upgrade
```

---

## 4. Streaming Protocols

### 4.1 Three-Tier Fallback

| Priority | Protocol | Port | Format | Latency | Bandwidth (4K) |
|----------|----------|------|--------|---------|----------------|
| 1 | WebRTC | UDP | H.264 RTP | ~10ms | ~8 Mbps |
| 2 | H.264 | TCP 8080 | Raw H.264 | ~50ms | ~8 Mbps |
| 3 | MJPEG | TCP 8080 | JPEG frames | ~100ms | ~25 Mbps |

### 4.2 Protocol Negotiation

Phone broadcasts:
```json
{
  "type": "discover",
  "device": "Pixel 7 Pro",
  "ip": "192.168.1.5",
  "ports": [8080],
  "protocols": ["webrtc", "h264", "mjpeg"],
  "resolutions": ["4k", "1080p", "720p"]
}
```

Backend responds:
```json
{
  "type": "found",
  "name": "LAPTOP-ABC",
  "ip": "192.168.1.10",
  "api_port": 8001,
  "protocol": "h264",
  "resolution": "4k"
}
```

### 4.3 WebRTC Signaling

```
Phone                              Backend
  │  POST /webrtc/offer             │
  │  { sdp: "...", type: "offer" }  │
  │  ──────────────────────────────> │
  │                                 │
  │  POST /webrtc/answer            │
  │  { sdp: "...", type: "answer" } │
  │  <────────────────────────────── │
  │                                 │
  │  POST /webrtc/candidate         │
  │  { candidate: "..." }           │
  │  ──────────────────────────────> │
  │                                 │
  │  ( ICE connectivity check )     │
  │  <────────────────────────────> │
  │                                 │
  │  ( H.264 RTP stream begins )    │
  │  ══════════════════════════════> │
```

### 4.4 H.264 Stream Format

```
GET /video HTTP/1.1
Accept: video/mp4; codecs=avc1.4d401f

Response:
HTTP/1.1 200 OK
Content-Type: video/mp4; codecs=avc1.4d401f
Transfer-Encoding: chunked

[ H.264 NAL units streamed continuously ]
```

### 4.5 MJPEG Stream Format

```
GET /video HTTP/1.1
Accept: multipart/x-mixed-replace; boundary=frame

Response:
HTTP/1.1 200 OK
Content-Type: multipart/x-mixed-replace; boundary=frame

--frame
Content-Type: image/jpeg
Content-Length: 12345

[ JPEG frame data ]
--frame
Content-Type: image/jpeg
...
```

---

## 5. Backend Integration

### 5.1 New VideoSource Plugin

**File:** `backend/app/services/camera/http_source.py`

```python
class HttpCameraSource(VideoSource):
    """Receives video stream from phone app via HTTP/WebRTC."""
    
    def __init__(self, url: str, protocol: str = "auto"):
        self.url = url
        self.protocol = protocol
        self.cap = None
        self.connected = False
    
    def open(self) -> bool:
        """Connect to phone stream using best available protocol."""
        if self.protocol == "webrtc":
            return self._connect_webrtc()
        elif self.protocol == "h264":
            return self._connect_h264()
        elif self.protocol == "mjpeg":
            return self._connect_mjpeg()
        else:  # auto
            return self._auto_connect()
    
    def read(self) -> tuple[bool, np.ndarray | None]:
        """Read next frame from stream."""
        if not self.cap or not self.connected:
            return False, None
        return self.cap.read()
    
    def release(self) -> None:
        """Disconnect and cleanup."""
        if self.cap:
            self.cap.release()
        self.connected = False
    
    def _auto_connect(self) -> bool:
        """Try protocols in order: WebRTC > H.264 > MJPEG."""
        for protocol in ["webrtc", "h264", "mjpeg"]:
            self.protocol = protocol
            if self._try_connect():
                self.connected = True
                return True
        return False
    
    def _try_connect(self) -> bool:
        """Attempt connection with current protocol."""
        try:
            if self.protocol in ("h264", "mjpeg"):
                self.cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
                return self.cap.isOpened()
            elif self.protocol == "webrtc":
                return self._connect_webrtc()
        except Exception:
            return False
        return False
```

### 5.2 Discovery Service

**File:** `backend/app/services/camera/discovery.py`

```python
class CameraDiscovery:
    """Listen for phone camera broadcasts on UDP 9999."""
    
    def __init__(self):
        self.known_phones: list[PhoneInfo] = []
        self.on_phone_found: Callable | None = None
    
    def start(self):
        """Start listening for UDP broadcasts."""
        # Bind UDP 9999, listen for broadcasts
        # When phone found: add to known_phones, call callback
    
    def stop(self):
        """Stop listening."""
    
    def get_phones(self) -> list[PhoneInfo]:
        """Return list of discovered phones."""
        return self.known_phones
```

### 5.3 Updated Config

**File:** `configs/camera.yaml`

```yaml
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

### 5.4 Updated CameraService

```python
class CameraService:
    def __init__(self, config: CameraConfig):
        self.config = config
        self.source = self._create_source()
        self.discovery = CameraDiscovery() if config.discovery_enabled else None
    
    def _create_source(self) -> VideoSource:
        if self.config.source_type == "http":
            return HttpCameraSource(
                url=self.config.http_url,
                protocol=self.config.http_protocol
            )
        elif self.config.source_type == "device":
            return OpenCVSource(device_id=self.config.device_id)
        elif self.config.source_type == "file":
            return FileSource(path=self.config.file_path)
        else:  # auto
            # Try HTTP first (phone), then device (USB)
            return AutoSource(config=self.config)
    
    async def auto_connect(self):
        """Auto-discover and connect to phone."""
        if self.discovery:
            phones = self.discovery.get_phones()
            if phones:
                phone = phones[0]  # Connect to first found
                self.config.http_url = f"http://{phone.ip}:{phone.port}/video"
                self.source = self._create_source()
                await self.connect()
```

---

## 7. Error Handling

### 7.1 Connection Errors

| Error | Phone Behavior | Backend Behavior |
|-------|---------------|------------------|
| WiFi lost | Auto-reconnect every 2s | Enter reconnect loop |
| Protocol fails | Auto-downgrade (WebRTC→H264→MJPEG) | Accept fallback |
| Phone hotspot dies | Show "Connection lost" | Enter reconnect loop |
| Multiple phones | Show list, user picks | Connect to selected |

### 7.2 Quality Degradation

| Condition | Action |
|-----------|--------|
| FPS drops below 20 | Downgrade resolution |
| Bandwidth < 5 Mbps | Switch to MJPEG (larger but more reliable) |
| Latency > 500ms | Log warning, suggest closer WiFi |
| Phone battery < 15% | Show warning, suggest charging |

### 7.3 Recovery

```
If stream drops:
  1. Phone keeps capturing (preview still works)
  2. Backend enters reconnect state
  3. Phone re-broadcasts discovery every 2s
  4. Backend auto-reconnects when phone reappears
  5. No user intervention needed
```

---

## 8. Network Requirements

### 8.1 Bandwidth

| Resolution | Min WiFi | Recommended | Max Latency |
|-----------|----------|-------------|-------------|
| 720p@30fps | 5 Mbps | 10 Mbps | 150ms |
| 1080p@30fps | 10 Mbps | 20 Mbps | 100ms |
| 4K@30fps | 20 Mbps | 40 Mbps | 80ms |
| 4K@60fps | 40 Mbps | 80 Mbps | 50ms |

### 8.2 Port Requirements

| Port | Protocol | Direction | Purpose |
|------|----------|-----------|---------|
| 9999 | UDP | Broadcast | Device discovery |
| 8080 | TCP | Phone→Laptop | Video stream |
| 8081 | TCP | Phone→Laptop | WebRTC signaling |
| 8001 | TCP | Laptop→Phone | Backend API |

### 8.3 Firewall Rules

```bash
# Windows Firewall
netsh advfirewall firewall add rule name="FieldVision Discovery" dir=in action=allow protocol=UDP localport=9999
netsh advfirewall firewall add rule name="FieldVision Stream" dir=in action=allow protocol=TCP localport=8080-8081
```

---

## 9. Testing Plan

### 9.1 Unit Tests

- HttpCameraSource: connect, read, disconnect, fallback
- CameraDiscovery: broadcast, receive, timeout
- NetworkMonitor: bandwidth detection, resolution decision

### 9.2 Integration Tests

- Phone app → Backend: full stream pipeline
- Auto-discovery: phone found within 5 seconds
- Protocol fallback: WebRTC fails → H.264 works
- Resolution auto-adapt: 4K → 1080p on weak WiFi

### 9.3 Manual Tests

- Stream 10 minutes without drops
- Walk out of WiFi range, verify reconnection
- Switch from hotspot to router mid-stream
- Test all camera controls (exposure, WB, focus)

---

## 10. Build Order

1. **UDP Discovery** — phone broadcasts, backend listens
2. **MJPEG Stream** — simplest protocol, gets bytes flowing
3. **HTTP Camera Source** — backend receives MJPEG
4. **Camera2 Integration** — phone captures 4K@30fps
5. **H.264 Stream** — add efficient codec
6. **WebRTC Stream** — add lowest latency option
7. **Resolution Auto-Adapt** — bandwidth detection + switching
8. **Manual Controls** — exposure, WB, focus, torch
9. **Error Handling** — reconnect, fallback, recovery

---

## 11. Future Enhancements (v2)

- Recording to laptop storage (match replay)
- Multiple phone cameras (different angles)
- Cloud relay (stream from anywhere)
- iOS app (Swift + AVFoundation)
- Low-latency mode (WebRTC data channel for controls)
