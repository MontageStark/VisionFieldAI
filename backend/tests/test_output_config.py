from __future__ import annotations

from pathlib import Path

from app.config.loader import get_settings, reset_settings
from app.config.settings import Settings
from app.models.camera_state import OutputConfig, OutputMode

CONFIGS_DIR = Path(__file__).resolve().parent.parent.parent / "configs"


class TestOutputConfigDefaults:
    def test_default_mode(self):
        cfg = OutputConfig()
        assert cfg.mode == OutputMode.VIRTUAL

    def test_default_mode_value_string(self):
        cfg = OutputConfig()
        assert cfg.mode.value == "virtual"

    def test_default_virtual_camera(self):
        cfg = OutputConfig()
        assert cfg.virtual_camera.dead_zone == 0.05
        assert cfg.virtual_camera.safe_margin == 0.1
        assert cfg.virtual_camera.max_velocity == 1.0
        assert cfg.virtual_camera.smoothing_factor == 0.3
        assert cfg.virtual_camera.default_zoom == 1.5

    def test_default_servo(self):
        cfg = OutputConfig()
        assert cfg.servo.pan_min == 0.0
        assert cfg.servo.pan_max == 180.0
        assert cfg.servo.default_pan == 90.0
        assert cfg.servo.max_velocity == 90.0

    def test_default_ptz(self):
        cfg = OutputConfig()
        assert cfg.ptz.host == "192.168.1.100"
        assert cfg.ptz.port == 80
        assert cfg.ptz.username is None
        assert cfg.ptz.password is None


class TestOutputConfigFromYaml:
    def setup_method(self):
        reset_settings()

    def teardown_method(self):
        reset_settings()

    def test_output_field_exists(self):
        s = get_settings(configs_dir=CONFIGS_DIR, force_reload=True)
        assert hasattr(s, "output")
        assert isinstance(s.output, OutputConfig)

    def test_output_mode_from_yaml(self):
        s = get_settings(configs_dir=CONFIGS_DIR, force_reload=True)
        assert s.output.mode.value == "virtual"

    def test_output_virtual_camera_from_yaml(self):
        s = get_settings(configs_dir=CONFIGS_DIR, force_reload=True)
        assert s.output.virtual_camera.dead_zone == 0.05
        assert s.output.virtual_camera.max_velocity == 1.0

    def test_output_servo_from_yaml(self):
        s = get_settings(configs_dir=CONFIGS_DIR, force_reload=True)
        assert s.output.servo.pan_max == 180.0
        assert s.output.servo.max_acceleration == 200.0

    def test_output_ptz_from_yaml(self):
        s = get_settings(configs_dir=CONFIGS_DIR, force_reload=True)
        assert s.output.ptz.host == "192.168.1.100"
        assert s.output.ptz.port == 80

    def test_settings_from_dict_with_output(self):
        data = {
            "output": {
                "mode": "servo",
                "virtual_camera": {"dead_zone": 0.1},
            }
        }
        s = Settings(**data)
        assert s.output.mode.value == "servo"
        assert s.output.virtual_camera.dead_zone == 0.1
        assert s.output.servo.pan_max == 180.0  # default preserved
