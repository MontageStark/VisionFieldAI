"""Tests for camera config."""
import pytest
import yaml
from pathlib import Path
from app.config.loader import get_settings


def test_camera_config_http_settings():
    """Test camera config has HTTP settings."""
    settings = get_settings()
    camera = settings.camera
    
    assert hasattr(camera, 'source_type')
    assert hasattr(camera, 'http_url')
    assert hasattr(camera, 'http_protocol')
    assert hasattr(camera, 'discovery_enabled')
    assert hasattr(camera, 'discovery_port')
    assert hasattr(camera, 'auto_connect')


def test_camera_config_default_values():
    """Test camera config has proper defaults."""
    settings = get_settings()
    camera = settings.camera
    
    assert camera.source_type == "auto"
    assert camera.http_protocol == "auto"
    assert camera.discovery_enabled is True
    assert camera.discovery_port == 9999
    assert camera.auto_connect is True


def test_camera_config_file_exists():
    """Test camera.yaml file exists."""
    config_path = Path("configs/camera.yaml")
    assert config_path.exists()


def test_camera_config_valid_yaml():
    """Test camera.yaml is valid YAML."""
    config_path = Path("configs/camera.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    assert "camera" in config
    assert isinstance(config["camera"], dict)
