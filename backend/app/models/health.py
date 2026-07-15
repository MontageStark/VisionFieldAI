"""Health monitoring models for FieldVision AI."""
from __future__ import annotations

from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    """Health status levels."""

    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class ComponentHealth(BaseModel):
    """Health status of a single component."""

    name: str = Field(..., min_length=1, description="Component name")
    status: HealthStatus = Field(..., description="Health status")
    message: str = Field(default="", description="Status message")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Component metrics")
    timestamp: float = Field(..., gt=0.0, description="Check timestamp")

    @property
    def is_healthy(self) -> bool:
        """Component is healthy if status is GREEN."""
        return self.status == HealthStatus.GREEN


class SystemHealth(BaseModel):
    """Overall system health summary."""

    status: HealthStatus = Field(..., description="Overall system status")
    components: Dict[str, ComponentHealth] = Field(
        default_factory=dict, description="Component health map"
    )
    timestamp: float = Field(..., gt=0.0, description="Summary timestamp")
    uptime: float = Field(default=0.0, ge=0.0, description="System uptime seconds")

    @property
    def unhealthy_components(self) -> list[str]:
        """List of components not in GREEN status."""
        return [name for name, comp in self.components.items() if comp.status != HealthStatus.GREEN]

    @property
    def critical_components(self) -> list[str]:
        """List of components in RED status."""
        return [name for name, comp in self.components.items() if comp.status == HealthStatus.RED]
