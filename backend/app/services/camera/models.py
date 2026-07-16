"""Data models for phone camera discovery and streaming."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PhoneInfo:
    """Information about a discovered phone camera."""
    name: str
    ip: str
    port: int
    protocols: list[str]
    resolutions: list[str]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "ip": self.ip,
            "port": self.port,
            "protocols": self.protocols,
            "resolutions": self.resolutions,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PhoneInfo:
        """Create from dictionary."""
        return cls(
            name=data["name"],
            ip=data["ip"],
            port=data["port"],
            protocols=data.get("protocols", []),
            resolutions=data.get("resolutions", []),
        )


@dataclass
class DiscoveryMessage:
    """UDP discovery message from phone."""
    type: str  # "discover" or "found"
    device: str
    ip: str
    ports: list[int]
    protocols: list[str]
    resolutions: list[str]
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "device": self.device,
            "ip": self.ip,
            "ports": self.ports,
            "protocols": self.protocols,
            "resolutions": self.resolutions,
        }
    
    @classmethod
    def from_json(cls, json_str: str) -> DiscoveryMessage:
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DiscoveryMessage:
        """Create from dictionary."""
        return cls(
            type=data["type"],
            device=data["device"],
            ip=data["ip"],
            ports=data.get("ports", [8080]),
            protocols=data.get("protocols", []),
            resolutions=data.get("resolutions", []),
        )
