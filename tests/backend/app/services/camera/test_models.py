"""Tests for phone camera discovery models."""
import pytest
from app.services.camera.models import PhoneInfo, DiscoveryMessage


def test_phone_info_creation():
    """Test PhoneInfo creation."""
    phone = PhoneInfo(
        name="Pixel 7 Pro",
        ip="192.168.1.5",
        port=8080,
        protocols=["mjpeg", "h264"],
        resolutions=["4k", "1080p"]
    )
    assert phone.name == "Pixel 7 Pro"
    assert phone.ip == "192.168.1.5"
    assert phone.port == 8080
    assert phone.protocols == ["mjpeg", "h264"]
    assert phone.resolutions == ["4k", "1080p"]


def test_phone_info_to_dict():
    """Test PhoneInfo to_dict."""
    phone = PhoneInfo(
        name="Pixel 7 Pro",
        ip="192.168.1.5",
        port=8080,
        protocols=["mjpeg"],
        resolutions=["4k"]
    )
    d = phone.to_dict()
    assert d["name"] == "Pixel 7 Pro"
    assert d["ip"] == "192.168.1.5"
    assert d["protocols"] == ["mjpeg"]


def test_phone_info_from_dict():
    """Test PhoneInfo from_dict."""
    d = {
        "name": "Pixel 7 Pro",
        "ip": "192.168.1.5",
        "port": 8080,
        "protocols": ["mjpeg"],
        "resolutions": ["4k"]
    }
    phone = PhoneInfo.from_dict(d)
    assert phone.name == "Pixel 7 Pro"
    assert phone.ip == "192.168.1.5"


def test_discovery_message_creation():
    """Test DiscoveryMessage creation."""
    msg = DiscoveryMessage(
        type="discover",
        device="Pixel 7 Pro",
        ip="192.168.1.5",
        ports=[8080],
        protocols=["mjpeg", "h264"],
        resolutions=["4k", "1080p"]
    )
    assert msg.type == "discover"
    assert msg.device == "Pixel 7 Pro"
    assert msg.ports == [8080]


def test_discovery_message_to_json():
    """Test DiscoveryMessage to_json."""
    msg = DiscoveryMessage(
        type="discover",
        device="Pixel 7 Pro",
        ip="192.168.1.5",
        ports=[8080],
        protocols=["mjpeg"],
        resolutions=["4k"]
    )
    json_str = msg.to_json()
    assert '"type": "discover"' in json_str
    assert '"device": "Pixel 7 Pro"' in json_str


def test_discovery_message_from_json():
    """Test DiscoveryMessage from_json."""
    json_str = '{"type": "discover", "device": "Pixel 7 Pro", "ip": "192.168.1.5", "ports": [8080], "protocols": ["mjpeg"], "resolutions": ["4k"]}'
    msg = DiscoveryMessage.from_json(json_str)
    assert msg.type == "discover"
    assert msg.device == "Pixel 7 Pro"
    assert msg.ports == [8080]
