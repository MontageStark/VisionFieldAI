"""Output plugin system for FieldVision AI."""
from app.services.output.base import OutputPlugin, OutputPluginError
from app.services.output.manager import OutputManager
from app.services.output.virtual_camera import VirtualCameraOutput
from app.services.output.servo import ServoOutput
from app.services.output.ptz import PTZOutput

__all__ = [
    "OutputPlugin",
    "OutputPluginError",
    "OutputManager",
    "VirtualCameraOutput",
    "ServoOutput",
    "PTZOutput",
]
