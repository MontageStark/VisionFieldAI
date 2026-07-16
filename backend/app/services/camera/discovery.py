"""Camera discovery service for detecting phones on network."""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Callable, Optional

from .models import PhoneInfo, DiscoveryMessage

logger = logging.getLogger(__name__)


class CameraDiscovery:
    """Listen for phone camera broadcasts on UDP 9999."""
    
    def __init__(self, port: int = 9999):
        self.port = port
        self.known_phones: list[PhoneInfo] = []
        self._phone_timestamps: dict[str, float] = {}
        self.on_phone_found: Optional[Callable[[PhoneInfo], None]] = None
        self._transport = None
        self._protocol = None
        self._running = False
    
    def get_phones(self) -> list[PhoneInfo]:
        """Return list of discovered phones."""
        return self.known_phones.copy()
    
    def _add_phone(self, phone: PhoneInfo) -> None:
        """Add or update a phone in known list."""
        # Check if phone already exists
        for i, existing in enumerate(self.known_phones):
            if existing.ip == phone.ip:
                # Update existing phone
                self.known_phones[i] = phone
                self._phone_timestamps[phone.ip] = time.time()
                logger.info(f"Updated phone: {phone.name} at {phone.ip}")
                return
        
        # Add new phone
        self.known_phones.append(phone)
        self._phone_timestamps[phone.ip] = time.time()
        logger.info(f"Found new phone: {phone.name} at {phone.ip}")
        
        # Call callback if set
        if self.on_phone_found:
            self.on_phone_found(phone)
    
    def _remove_stale_phones(self, timeout_seconds: int = 30) -> None:
        """Remove phones that haven't been seen recently."""
        current_time = time.time()
        stale_ips = [
            ip for ip, timestamp in self._phone_timestamps.items()
            if current_time - timestamp > timeout_seconds
        ]
        
        for ip in stale_ips:
            self.known_phones = [p for p in self.known_phones if p.ip != ip]
            del self._phone_timestamps[ip]
            logger.info(f"Removed stale phone at {ip}")
    
    async def start(self) -> None:
        """Start listening for UDP broadcasts."""
        self._running = True
        logger.info(f"Starting discovery service on port {self.port}")
        
        # In real implementation, bind UDP socket here
        # For now, just log that we're listening
    
    async def stop(self) -> None:
        """Stop listening."""
        self._running = False
        logger.info("Stopping discovery service")
    
    def _handle_message(self, data: bytes, addr: tuple[str, int]) -> None:
        """Handle incoming UDP message."""
        try:
            message = DiscoveryMessage.from_json(data.decode())
            if message.type == "discover":
                phone = PhoneInfo(
                    name=message.device,
                    ip=message.ip,
                    port=message.ports[0] if message.ports else 8080,
                    protocols=message.protocols,
                    resolutions=message.resolutions
                )
                self._add_phone(phone)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Invalid discovery message from {addr}: {e}")
