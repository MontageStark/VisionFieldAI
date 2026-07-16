"""Tests for HTTP camera source."""
import pytest
from unittest.mock import patch, MagicMock
import numpy as np
from app.services.camera.http_source import HttpCameraSource


def test_http_source_initialization():
    """Test HttpCameraSource initialization."""
    source = HttpCameraSource(url="http://192.168.1.5:8080/video")
    assert source.url == "http://192.168.1.5:8080/video"
    assert source.protocol == "auto"
    assert source.is_opened() is False
    assert source.cap is None


def test_http_source_initialization_with_protocol():
    """Test HttpCameraSource with specific protocol."""
    source = HttpCameraSource(
        url="http://192.168.1.5:8080/video",
        protocol="mjpeg"
    )
    assert source.protocol == "mjpeg"


def test_http_source_read_when_not_connected():
    """Test read when not connected returns False."""
    source = HttpCameraSource(url="http://192.168.1.5:8080/video")
    success, frame = source.read()
    assert success is False
    assert frame is None


def test_http_source_release():
    """Test release cleans up resources."""
    source = HttpCameraSource(url="http://192.168.1.5:8080/video")
    source.release()
    assert source.is_opened() is False
    assert source.cap is None


@patch('app.services.camera.http_source.cv2')
def test_http_source_open_mjpeg(mock_cv2):
    """Test opening MJPEG stream."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.CAP_FFMPEG = 1900
    
    source = HttpCameraSource(
        url="http://192.168.1.5:8080/video",
        protocol="mjpeg"
    )
    result = source.open()
    
    assert result is True
    assert source.is_opened() is True
    mock_cv2.VideoCapture.assert_called_once_with(
        "http://192.168.1.5:8080/video",
        1900
    )


@patch('app.services.camera.http_source.cv2')
def test_http_source_read_when_connected(mock_cv2):
    """Test reading frame when connected."""
    mock_cap = MagicMock()
    mock_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    mock_cap.read.return_value = (True, mock_frame)
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.CAP_FFMPEG = 1900
    
    source = HttpCameraSource(
        url="http://192.168.1.5:8080/video",
        protocol="mjpeg"
    )
    source.open()
    success, frame = source.read()
    
    assert success is True
    assert frame is not None
    assert frame.shape == (1080, 1920, 3)


@patch('app.services.camera.http_source.cv2')
def test_http_source_auto_connect(mock_cv2):
    """Test auto-connect tries protocols in order."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.CAP_FFMPEG = 1900
    
    source = HttpCameraSource(
        url="http://192.168.1.5:8080/video",
        protocol="auto"
    )
    result = source.open()
    
    assert result is True
    assert source.protocol in ["mjpeg", "h264"]


@patch('app.services.camera.http_source.cv2')
def test_http_source_fps(mock_cv2):
    """Test fps property."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.get.return_value = 30.0
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.CAP_FFMPEG = 1900
    mock_cv2.CAP_PROP_FPS = 5
    
    source = HttpCameraSource(
        url="http://192.168.1.5:8080/video",
        protocol="mjpeg"
    )
    source.open()
    
    assert source.fps == 30.0


@patch('app.services.camera.http_source.cv2')
def test_http_source_resolution(mock_cv2):
    """Test resolution property."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.get.side_effect = lambda x: 1920 if x == 3 else 1080
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.CAP_FFMPEG = 1900
    mock_cv2.CAP_PROP_FRAME_WIDTH = 3
    mock_cv2.CAP_PROP_FRAME_HEIGHT = 4
    
    source = HttpCameraSource(
        url="http://192.168.1.5:8080/video",
        protocol="mjpeg"
    )
    source.open()
    
    assert source.resolution == (1920, 1080)
