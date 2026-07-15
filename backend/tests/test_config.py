from __future__ import annotations

import os
from pathlib import Path

import pytest

from backend.app.config.loader import (
    _apply_env_overrides,
    _coerce_env_value,
    _load_all_yaml_configs,
    _load_yaml_file,
    get_settings,
    load_settings,
    reset_settings,
)
from backend.app.config.settings import (
    AISettings,
    CameraSettings,
    NetworkSettings,
    ServoAxisSettings,
    ServoSettings,
    Settings,
    StreamSettings,
)

CONFIGS_DIR = Path(__file__).resolve().parent.parent.parent / "configs"


class TestCameraSettings:
    def test_defaults(self):
        s = CameraSettings()
        assert s.device_id == 0
        assert s.width == 1920
        assert s.height == 1080
        assert s.fps == 30
        assert s.buffer_size == 10

    def test_custom_values(self):
        s = CameraSettings(device_id=1, width=640, height=480, fps=60, buffer_size=5)
        assert s.device_id == 1
        assert s.width == 640
        assert s.height == 480
        assert s.fps == 60
        assert s.buffer_size == 5

    def test_invalid_fps_zero(self):
        with pytest.raises(Exception):
            CameraSettings(fps=0)

    def test_invalid_fps_negative(self):
        with pytest.raises(Exception):
            CameraSettings(fps=-1)

    def test_invalid_fps_too_high(self):
        with pytest.raises(Exception):
            CameraSettings(fps=200)

    def test_invalid_width_zero(self):
        with pytest.raises(Exception):
            CameraSettings(width=0)

    def test_invalid_height_zero(self):
        with pytest.raises(Exception):
            CameraSettings(height=0)

    def test_invalid_device_id_negative(self):
        with pytest.raises(Exception):
            CameraSettings(device_id=-1)

    def test_invalid_buffer_size_zero(self):
        with pytest.raises(Exception):
            CameraSettings(buffer_size=0)


class TestServoAxisSettings:
    def test_defaults(self):
        s = ServoAxisSettings()
        assert s.min_angle == 0.0
        assert s.max_angle == 180.0
        assert s.default_angle == 90.0
        assert s.speed_limit == 90.0

    def test_custom_values(self):
        s = ServoAxisSettings(min_angle=-45, max_angle=135, default_angle=0, speed_limit=120)
        assert s.min_angle == -45
        assert s.max_angle == 135
        assert s.default_angle == 0
        assert s.speed_limit == 120

    def test_max_less_than_min(self):
        with pytest.raises(Exception):
            ServoAxisSettings(min_angle=90, max_angle=10)

    def test_default_out_of_range(self):
        with pytest.raises(Exception):
            ServoAxisSettings(min_angle=0, max_angle=90, default_angle=100)

    def test_speed_limit_zero(self):
        with pytest.raises(Exception):
            ServoAxisSettings(speed_limit=0)

    def test_speed_limit_negative(self):
        with pytest.raises(Exception):
            ServoAxisSettings(speed_limit=-10)


class TestServoSettings:
    def test_defaults(self):
        s = ServoSettings()
        assert isinstance(s.pan, ServoAxisSettings)
        assert isinstance(s.tilt, ServoAxisSettings)
        assert s.pan.default_angle == 90.0
        assert s.tilt.default_angle == 90.0

    def test_custom_pan_tilt(self):
        s = ServoSettings(
            pan=ServoAxisSettings(min_angle=-90, max_angle=90, default_angle=0),
            tilt=ServoAxisSettings(min_angle=-45, max_angle=45, default_angle=0),
        )
        assert s.pan.min_angle == -90
        assert s.tilt.max_angle == 45


class TestNetworkSettings:
    def test_defaults(self):
        s = NetworkSettings()
        assert s.host == "0.0.0.0"
        assert s.port == 8000
        assert s.cors_origins == ["http://localhost:3000"]
        assert s.esp32_url == "ws://192.168.1.100:8080"

    def test_custom_port(self):
        s = NetworkSettings(port=3000)
        assert s.port == 3000

    def test_invalid_port_zero(self):
        with pytest.raises(Exception):
            NetworkSettings(port=0)

    def test_invalid_port_too_high(self):
        with pytest.raises(Exception):
            NetworkSettings(port=70000)


class TestAISettings:
    def test_defaults(self):
        s = AISettings()
        assert s.model_name == "yolo11n.pt"
        assert s.confidence_threshold == 0.5
        assert s.device == "cuda"
        assert s.max_detections == 100

    def test_custom_values(self):
        s = AISettings(model_name="yolov8.pt", confidence_threshold=0.7, device="cpu", max_detections=50)
        assert s.model_name == "yolov8.pt"
        assert s.confidence_threshold == 0.7
        assert s.device == "cpu"
        assert s.max_detections == 50

    def test_invalid_device(self):
        with pytest.raises(Exception):
            AISettings(device="tpu")

    def test_invalid_confidence_negative(self):
        with pytest.raises(Exception):
            AISettings(confidence_threshold=-0.1)

    def test_invalid_confidence_above_one(self):
        with pytest.raises(Exception):
            AISettings(confidence_threshold=1.5)

    def test_invalid_max_detections_zero(self):
        with pytest.raises(Exception):
            AISettings(max_detections=0)


class TestStreamSettings:
    def test_defaults(self):
        s = StreamSettings()
        assert s.enabled is False
        assert s.youtube_key == ""
        assert s.output_width == 1920
        assert s.output_height == 1080
        assert s.bitrate == 4000000
        assert s.fps == 30

    def test_custom_values(self):
        s = StreamSettings(enabled=True, youtube_key="abc123", output_width=1280, output_height=720)
        assert s.enabled is True
        assert s.youtube_key == "abc123"
        assert s.output_width == 1280
        assert s.output_height == 720

    def test_invalid_bitrate_zero(self):
        with pytest.raises(Exception):
            StreamSettings(bitrate=0)

    def test_invalid_fps_zero(self):
        with pytest.raises(Exception):
            StreamSettings(fps=0)


class TestSettings:
    def test_defaults(self):
        s = Settings()
        assert isinstance(s.camera, CameraSettings)
        assert isinstance(s.servo, ServoSettings)
        assert isinstance(s.network, NetworkSettings)
        assert isinstance(s.ai, AISettings)
        assert isinstance(s.stream, StreamSettings)

    def test_nested_access(self):
        s = Settings()
        assert s.camera.width == 1920
        assert s.servo.pan.default_angle == 90.0
        assert s.network.port == 8000
        assert s.ai.device == "cuda"
        assert s.stream.bitrate == 4000000

    def test_from_dict(self):
        data = {
            "camera": {"device_id": 2, "fps": 60},
            "ai": {"device": "cpu"},
        }
        s = Settings(**data)
        assert s.camera.device_id == 2
        assert s.camera.fps == 60
        assert s.ai.device == "cpu"
        assert s.camera.width == 1920  # default preserved


class TestCoerceEnvValue:
    def test_true_values(self):
        for v in ["true", "True", "TRUE", "yes", "Yes", "1"]:
            assert _coerce_env_value(v) is True

    def test_false_values(self):
        for v in ["false", "False", "FALSE", "no", "No", "0"]:
            assert _coerce_env_value(v) is False

    def test_none_values(self):
        for v in ["none", "None", "null", ""]:
            assert _coerce_env_value(v) == ""

    def test_integer(self):
        assert _coerce_env_value("42") == 42

    def test_float(self):
        assert _coerce_env_value("3.14") == 3.14

    def test_string(self):
        assert _coerce_env_value("hello") == "hello"


class TestEnvOverrides:
    def test_single_override(self, monkeypatch):
        monkeypatch.setenv("AI__DEVICE", "cpu")
        data = _apply_env_overrides({})
        assert data["ai"]["device"] == "cpu"

    def test_nested_override(self, monkeypatch):
        monkeypatch.setenv("CAMERA__FPS", "60")
        monkeypatch.setenv("CAMERA__WIDTH", "640")
        data = _apply_env_overrides({})
        assert data["camera"]["fps"] == 60
        assert data["camera"]["width"] == 640

    def test_bool_override(self, monkeypatch):
        monkeypatch.setenv("STREAM__ENABLED", "true")
        data = _apply_env_overrides({})
        assert data["stream"]["enabled"] is True

    def test_network_port_override(self, monkeypatch):
        monkeypatch.setenv("NETWORK__PORT", "3000")
        data = _apply_env_overrides({})
        assert data["network"]["port"] == 3000


class TestLoadYamlFile:
    def test_load_valid_yaml(self, tmp_path):
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("key: value\nnumber: 42\n")
        result = _load_yaml_file(yaml_file)
        assert result == {"key": "value", "number": 42}

    def test_load_nonexistent_file(self, tmp_path):
        result = _load_yaml_file(tmp_path / "missing.yaml")
        assert result == {}


class TestLoadAllYamlConfigs:
    def test_load_all_configs(self):
        data = _load_all_yaml_configs(CONFIGS_DIR)
        assert "camera" in data
        assert "servo" in data
        assert "network" in data
        assert "ai" in data
        assert "stream" in data

    def test_camera_values_from_yaml(self):
        data = _load_all_yaml_configs(CONFIGS_DIR)
        assert data["camera"]["device_id"] == 0
        assert data["camera"]["width"] == 1920
        assert data["camera"]["height"] == 1080
        assert data["camera"]["fps"] == 30

    def test_ai_values_from_yaml(self):
        data = _load_all_yaml_configs(CONFIGS_DIR)
        assert data["ai"]["model_name"] == "yolo11n.pt"
        assert data["ai"]["confidence_threshold"] == 0.5
        assert data["ai"]["device"] == "cuda"

    def test_nonexistent_dir(self, tmp_path):
        data = _load_all_yaml_configs(tmp_path / "nonexistent")
        assert data == {}


class TestLoadSettings:
    def test_load_from_yaml(self):
        s = load_settings(configs_dir=CONFIGS_DIR, use_env_overrides=False)
        assert isinstance(s, Settings)
        assert s.camera.width == 1920
        assert s.ai.device == "cuda"
        assert s.network.port == 8000

    def test_load_with_env_override(self, monkeypatch):
        monkeypatch.setenv("AI__DEVICE", "cpu")
        s = load_settings(configs_dir=CONFIGS_DIR, use_env_overrides=True)
        assert s.ai.device == "cpu"
        assert s.camera.width == 1920  # YAML value preserved

    def test_load_empty_dir(self, tmp_path):
        s = load_settings(configs_dir=tmp_path, use_env_overrides=False)
        assert isinstance(s, Settings)
        assert s.camera.device_id == 0  # defaults


class TestGetSettingsSingleton:
    def setup_method(self):
        reset_settings()

    def teardown_method(self):
        reset_settings()

    def test_singleton_returns_same_instance(self):
        s1 = get_settings(configs_dir=CONFIGS_DIR)
        s2 = get_settings(configs_dir=CONFIGS_DIR)
        assert s1 is s2

    def test_force_reload(self):
        s1 = get_settings(configs_dir=CONFIGS_DIR)
        s2 = get_settings(configs_dir=CONFIGS_DIR, force_reload=True)
        assert s1 is not s2  # new instance
        assert s1.camera.width == s2.camera.width  # same values

    def test_reset(self):
        s1 = get_settings(configs_dir=CONFIGS_DIR)
        reset_settings()
        s2 = get_settings(configs_dir=CONFIGS_DIR)
        assert s1 is not s2
