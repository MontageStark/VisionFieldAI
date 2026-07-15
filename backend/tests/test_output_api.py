"""Tests for output API endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_get_output_mode():
    response = client.get("/api/output/mode")
    assert response.status_code == 200
    data = response.json()
    assert "mode" in data
    assert data["mode"] in ("virtual", "servo", "hybrid", "ptz")


def test_set_output_mode_to_servo():
    response = client.post("/api/output/mode", json={"mode": "servo"})
    assert response.status_code == 200
    assert response.json()["mode"] == "servo"
    # Reset back
    client.post("/api/output/mode", json={"mode": "virtual"})


def test_set_output_mode_invalid():
    response = client.post("/api/output/mode", json={"mode": "invalid"})
    assert response.status_code == 400


def test_get_output_state():
    response = client.get("/api/output/state")
    assert response.status_code == 200
    data = response.json()
    assert "center_x" in data
    assert "center_y" in data
    assert "zoom" in data
    assert "mode" in data


def test_reset_output():
    response = client.post("/api/output/reset")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
