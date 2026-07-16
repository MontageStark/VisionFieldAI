"""Tests for camera discovery service."""
import time
import pytest
from unittest.mock import MagicMock
from app.services.camera.discovery import CameraDiscovery
from app.services.camera.models import PhoneInfo


@pytest.fixture
def discovery():
    """Create a CameraDiscovery instance."""
    return CameraDiscovery(port=9999)


def test_discovery_initialization(discovery):
    """Test discovery service initialization."""
    assert discovery.port == 9999
    assert discovery.known_phones == []
    assert discovery.on_phone_found is None


def test_discovery_add_phone(discovery):
    """Test adding a phone to known list."""
    phone = PhoneInfo(
        name="Pixel 7 Pro",
        ip="192.168.1.5",
        port=8080,
        protocols=["mjpeg"],
        resolutions=["4k"]
    )
    discovery._add_phone(phone)
    assert len(discovery.known_phones) == 1
    assert discovery.known_phones[0].ip == "192.168.1.5"


def test_discovery_add_duplicate_phone(discovery):
    """Test adding same phone twice updates instead of duplicates."""
    phone1 = PhoneInfo(
        name="Pixel 7 Pro",
        ip="192.168.1.5",
        port=8080,
        protocols=["mjpeg"],
        resolutions=["4k"]
    )
    phone2 = PhoneInfo(
        name="Pixel 7 Pro",
        ip="192.168.1.5",
        port=8080,
        protocols=["h264", "mjpeg"],
        resolutions=["4k", "1080p"]
    )
    discovery._add_phone(phone1)
    discovery._add_phone(phone2)
    assert len(discovery.known_phones) == 1
    assert discovery.known_phones[0].protocols == ["h264", "mjpeg"]


def test_discovery_get_phones(discovery):
    """Test getting list of phones."""
    phone = PhoneInfo(
        name="Pixel 7 Pro",
        ip="192.168.1.5",
        port=8080,
        protocols=["mjpeg"],
        resolutions=["4k"]
    )
    discovery._add_phone(phone)
    phones = discovery.get_phones()
    assert len(phones) == 1
    assert phones[0].ip == "192.168.1.5"


def test_discovery_remove_stale_phones(discovery):
    """Test removing phones that haven't been seen."""
    phone = PhoneInfo(
        name="Pixel 7 Pro",
        ip="192.168.1.5",
        port=8080,
        protocols=["mjpeg"],
        resolutions=["4k"]
    )
    discovery._add_phone(phone)
    # Simulate timeout by setting timestamp in the past
    discovery._phone_timestamps[phone.ip] = time.time() - 100
    discovery._remove_stale_phones(timeout_seconds=50)
    assert len(discovery.known_phones) == 0


def test_discovery_callback(discovery):
    """Test callback is called when phone found."""
    callback = MagicMock()
    discovery.on_phone_found = callback
    
    phone = PhoneInfo(
        name="Pixel 7 Pro",
        ip="192.168.1.5",
        port=8080,
        protocols=["mjpeg"],
        resolutions=["4k"]
    )
    discovery._add_phone(phone)
    callback.assert_called_once_with(phone)
