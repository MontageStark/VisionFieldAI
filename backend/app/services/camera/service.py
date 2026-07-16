"""Camera service for managing video sources."""
from __future__ import annotations

import logging
from typing import Any, Optional

from .http_source import HttpCameraSource
from .discovery import CameraDiscovery
from .video_source import VideoSource

logger = logging.getLogger(__name__)


class CameraService:
    """Manages camera sources and discovery."""
    
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.source = self._create_source()
        self.discovery = self._create_discovery()
    
    def _create_source(self) -> VideoSource:
        """Create video source based on config."""
        source_type = self.config.get("source_type", "auto")
        
        if source_type == "http":
            return HttpCameraSource(
                url=self.config.get("http_url", ""),
                protocol=self.config.get("http_protocol", "auto")
            )
        elif source_type == "device":
            # Would create OpenCVSource for USB camera
            raise NotImplementedError("Device source not yet implemented")
        elif source_type == "file":
            # Would create FileSource for simulation
            raise NotImplementedError("File source not yet implemented")
        else:  # auto
            # Default to HTTP for phone streaming
            return HttpCameraSource(
                url=self.config.get("http_url", ""),
                protocol=self.config.get("http_protocol", "auto")
            )
    
    def _create_discovery(self) -> Optional[CameraDiscovery]:
        """Create discovery service if enabled."""
        if self.config.get("discovery_enabled", False):
            return CameraDiscovery(
                port=self.config.get("discovery_port", 9999)
            )
        return None
    
    async def auto_connect(self) -> bool:
        """Auto-discover and connect to phone."""
        if not self.discovery:
            return False
        
        phones = self.discovery.get_phones()
        if phones:
            phone = phones[0]  # Connect to first found
            self.config["http_url"] = f"http://{phone.ip}:{phone.port}/video"
            self.source = self._create_source()
            return self.source.open()
        
        return False
