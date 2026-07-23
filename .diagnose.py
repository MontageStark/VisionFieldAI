"""Comprehensive network and AI pipeline diagnostic."""
import socket
import json
import time
import sys

def check_port(host, port, timeout=3):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        return True
    except:
        return False

def http_get(host, port, path, timeout=10):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((host, port))
    s.sendall(f'GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n'.encode())
    d = b''
    while True:
        try:
            c = s.recv(65536)
            if not c: break
            d += c
        except: break
    s.close()
    body = d[d.find(b'\r\n\r\n')+4:]
    return json.loads(body) if body else None

print("=" * 60)
print("FIELDVISION AI - NETWORK & AI DIAGNOSTIC")
print("=" * 60)

# 1. Service connectivity
print("\n[1] SERVICE CONNECTIVITY")
services = [
    ("Frontend", "127.0.0.1", 5173),
    ("Backend API", "127.0.0.1", 8001),
    ("Phone WiFi", "192.168.0.187", 8080),
    ("Phone ADB", "127.0.0.1", 8080),
]
for name, host, port in services:
    status = "UP" if check_port(host, port) else "DOWN"
    print(f"  {name:15s} {host}:{port} -> {status}")

# 2. Phone stream health
print("\n[2] PHONE STREAM")
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect(("192.168.0.187", 8080))
    s.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n")
    data = b""
    start = time.time()
    while time.time() - start < 3:
        try:
            chunk = s.recv(65536)
            if not chunk: break
            data += chunk
        except: break
    s.close()
    frames = data.count(b'\xff\xd8')
    print(f"  WiFi direct: {len(data)} bytes, {frames} JPEG frames")
except Exception as e:
    print(f"  WiFi direct: FAILED - {e}")

# 3. Proxy health
print("\n[3] BACKEND PROXY")
try:
    r = http_get("127.0.0.1", 8001, "/api/stream/proxy?phone_ip=192.168.0.187&port=8080")
    # This won't work because proxy streams - just check if endpoint exists
    print("  Proxy endpoint: accessible")
except:
    print("  Proxy endpoint: streaming (expected)")

# 4. AI Pipeline
print("\n[4] AI PIPELINE")
try:
    r = http_get("127.0.0.1", 8001, "/api/ai/status")
    print(f"  Running: {r['running']}")
    t = r['tracking']
    print(f"  Frames analyzed: {t['frame_count']}")
    print(f"  FPS: {t['fps']}")
    print(f"  Detections: {t['detection_count']}")
    print(f"  Last update: {t['last_update']:.0f}")
    age = time.time() - t['last_update'] if t['last_update'] > 0 else 999
    print(f"  Data age: {age:.1f}s {'(stale!)' if age > 10 else '(fresh)'}")
except Exception as e:
    print(f"  FAILED: {e}")

# 5. AI Decision
print("\n[5] AI DECISION")
try:
    r = http_get("127.0.0.1", 8001, "/api/ai/decision")
    print(f"  Shot type: {r['shot_type']}")
    print(f"  Crop: w={r['crop_w']}, h={r['crop_h']}")
    ratio = r['crop_w'] / r['crop_h'] if r['crop_h'] > 0 else 0
    print(f"  Ratio: {ratio:.3f} (target: 1.778)")
    print(f"  Zoom: {r['zoom']}x")
    print(f"  Confidence: {r['confidence']}")
    print(f"  Reasoning: {r['reasoning']}")
    ok = r['crop_w'] <= 1.0 and r['crop_h'] <= 1.0
    print(f"  Crop bounds OK: {ok} (w<=1: {r['crop_w']<=1.0}, h<=1: {r['crop_h']<=1.0})")
except Exception as e:
    print(f"  FAILED: {e}")

# 6. Detections breakdown
print("\n[6] DETECTIONS BREAKDOWN")
try:
    r = http_get("127.0.0.1", 8001, "/api/ai/detections")
    labels = {}
    for d in r['detections']:
        labels[d['label']] = labels.get(d['label'], 0) + 1
    print(f"  Total: {r['count']}")
    for label, count in sorted(labels.items()):
        print(f"  {label}: {count}")
except Exception as e:
    print(f"  FAILED: {e}")

# 7. Frontend proxy
print("\n[7] FRONTEND PROXY (Vite -> Backend)")
try:
    r = http_get("127.0.0.1", 5173, "/api/ai/status")
    print(f"  Via frontend proxy: Running={r['running']}, Frames={r['tracking']['frame_count']}")
except Exception as e:
    print(f"  FAILED: {e}")

# 8. Camera status
print("\n[8] CAMERA STATUS")
try:
    r = http_get("127.0.0.1", 8001, "/api/camera/status")
    print(f"  Running: {r.get('running', 'unknown')}")
    print(f"  Source: {r.get('source', 'unknown')}")
except Exception as e:
    print(f"  FAILED: {e}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
