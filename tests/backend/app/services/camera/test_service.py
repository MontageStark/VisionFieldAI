"""Tests for camera service."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.camera.service import CameraService
from app.services.camera.http_source import HttpCameraSource
from app.services.camera.discovery import CameraDiscovery


def test_camera_service_initialization():
    """Test CameraService initialization with HTTP config."""
    config = {
        "source_type": "http",
        "http_url": "http://192.168.1.5:8080/video",
        "http_protocol": "mjpeg",
        "discovery_enabled": True,
        "discovery_port": 9999,
        "auto_connect": True
    }
    
    with patch('app.services.camera.service.CameraDiscovery'):
        service = CameraService(config)
        assert service.config == config
        assert service.source is not None
        assert service.discovery is not None


def test_camera_service_create_http_source():
    """Test creating HTTP camera source."""
    config = {
        "source_type": "http",
        "http_url": "http://192.168.1.5:8080/video",
        "http_protocol": "mjpeg"
    }
    
    service = CameraService(config)
    assert isinstance(service.source, HttpCameraSource)
    assert service.source.url == "http://192.168.1.5:8080/video"
    assert service.source.protocol == "mjpeg"


def test_camera_service_auto_source():
    """Test auto source type defaults to HTTP."""
    config = {
        "source_type": "auto"
    }
    
    service = CameraService(config)
    assert isinstance(service.source, HttpCameraSource)


def test_camera_service_discovery_enabled():
    """Test discovery service is created when enabled."""
    config = {
        "source_type": "auto",
        "discovery_enabled": True,
        "discovery_port": 9999
    }
    
    with patch('app.services.camera.service.CameraDiscovery') as mock_disc:
        service = CameraService(config)
        mock_disc.assert_called_once_with(port=9999)
        assert service.discovery is not None


def test_camera_service_discovery_disabled():
    """Test discovery service is not created when disabled."""
    config = {
        "source_type": "auto",
        "discovery_enabled": False
    }
    
    service = CameraService(config)
    assert service.discovery is None
