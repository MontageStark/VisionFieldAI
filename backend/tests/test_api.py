"""Tests for FastAPI API endpoints."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api.deps import reset_services, get_state_machine
from backend.app.core.state import SystemState


@pytest.fixture(autouse=True)
def reset():
    reset_services()
    yield
    reset_services()


@pytest.fixture
def client():
    return TestClient(app)


class TestHealth:
    def test_health_check(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "0.1.0"


class TestSystem:
    def test_get_status(self, client):
        resp = client.get("/api/system/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "state" in data
        assert "valid_transitions" in data
        assert "history" in data

    def test_get_state(self, client):
        resp = client.get("/api/system/state")
        assert resp.status_code == 200
        data = resp.json()
        assert "state" in data
        assert "state_value" in data

    def test_transition_valid(self, client):
        resp = client.get("/api/system/state")
        current = resp.json()["state"]

        sm = get_state_machine()
        valid = sm.get_valid_transitions()
        assert len(valid) > 0

        target = valid[0]
        resp = client.post(f"/api/system/state/{target.name.lower()}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["state"] == target.name

    def test_transition_invalid(self, client):
        resp = client.post("/api/system/state/tracking")
        assert resp.status_code == 409

    def test_invalid_state_name(self, client):
        resp = client.post("/api/system/state/nonexistent")
        assert resp.status_code == 400


class TestCamera:
    def test_camera_status(self, client):
        resp = client.get("/api/camera/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "running" in data

    def test_camera_start_stop(self, client):
        resp = client.post("/api/camera/start")
        assert resp.status_code == 200
        assert resp.json()["status"] == "started"

        resp = client.get("/api/camera/status")
        assert resp.json()["running"] is True

        resp = client.post("/api/camera/stop")
        assert resp.status_code == 200
        assert resp.json()["status"] == "stopped"

    def test_camera_already_running(self, client):
        client.post("/api/camera/start")
        resp = client.post("/api/camera/start")
        assert resp.status_code == 200
        assert resp.json()["status"] == "already_running"


class TestServo:
    def test_servo_status(self, client):
        resp = client.get("/api/servo/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "pan_angle" in data
        assert "tilt_angle" in data

    def test_servo_command(self, client):
        resp = client.post("/api/servo/command", json={"pan": 45.0, "tilt": 60.0})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["pan"] == 45.0
        assert data["tilt"] == 60.0

    def test_servo_command_clamp(self, client):
        resp = client.post("/api/servo/command", json={"pan": 200.0, "tilt": -10.0})
        assert resp.status_code == 422

    def test_servo_home(self, client):
        client.post("/api/servo/command", json={"pan": 30.0, "tilt": 40.0})
        resp = client.post("/api/servo/home")
        assert resp.status_code == 200
        assert resp.json()["status"] == "homed"

    def test_servo_emergency(self, client):
        resp = client.post("/api/servo/emergency")
        assert resp.status_code == 200
        assert resp.json()["status"] == "emergency_stop_activated"

        resp = client.post("/api/servo/command", json={"pan": 90.0, "tilt": 90.0})
        assert resp.status_code == 409


class TestDirector:
    def test_director_status(self, client):
        resp = client.get("/api/director/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "mode" in data

    def test_director_set_mode(self, client):
        resp = client.post("/api/director/mode/aggressive")
        assert resp.status_code == 200
        assert resp.json()["mode"] == "aggressive"

    def test_director_invalid_mode(self, client):
        resp = client.post("/api/director/mode/invalid")
        assert resp.status_code == 400

    def test_director_decision(self, client):
        resp = client.post("/api/director/decision")
        assert resp.status_code == 200
        data = resp.json()
        assert "mode" in data
        assert "target" in data
        assert "confidence" in data


class TestStream:
    def test_stream_status(self, client):
        resp = client.get("/api/stream/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "streaming" in data

    def test_stream_start_stop(self, client):
        resp = client.post("/api/stream/start")
        assert resp.status_code == 200
        assert resp.json()["status"] == "started"

        resp = client.get("/api/stream/status")
        assert resp.json()["streaming"] is True

        resp = client.post("/api/stream/stop")
        assert resp.status_code == 200
        assert resp.json()["status"] == "stopped"

    def test_stream_already_streaming(self, client):
        client.post("/api/stream/start")
        resp = client.post("/api/stream/start")
        assert resp.status_code == 200
        assert resp.json()["status"] == "already_streaming"
