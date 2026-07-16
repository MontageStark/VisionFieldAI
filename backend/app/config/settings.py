from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

from app.models.camera_state import OutputConfig


class CameraSettings(BaseModel):
    """Camera configuration settings."""

    source_type: str = Field(default="auto", description="Camera source type (device, file, http, auto)")
    device_id: int = Field(default=0, ge=0, description="Camera device ID")
    width: int = Field(default=1920, gt=0, le=7680, description="Capture width in pixels")
    height: int = Field(default=1080, gt=0, le=4320, description="Capture height in pixels")
    fps: int = Field(default=30, ge=1, le=120, description="Frames per second")
    buffer_size: int = Field(default=10, ge=1, le=100, description="Frame buffer size")
    
    # HTTP (phone stream) settings
    http_url: str = Field(default="http://192.168.1.5:8080/video", description="HTTP stream URL")
    http_protocol: str = Field(default="auto", description="HTTP protocol (webrtc, h264, mjpeg, auto)")
    
    # Auto-discovery settings
    discovery_enabled: bool = Field(default=True, description="Enable UDP discovery")
    discovery_port: int = Field(default=9999, ge=1, le=65535, description="Discovery UDP port")
    auto_connect: bool = Field(default=True, description="Auto-connect to discovered phones")
    
    # File source settings
    file_path: str = Field(default="", description="Path to video file")
    loop: bool = Field(default=True, description="Loop video file")


class ServoAxisSettings(BaseModel):
    """Settings for a single servo axis (pan or tilt)."""

    min_angle: float = Field(default=0.0, ge=-180.0, le=180.0, description="Minimum angle in degrees")
    max_angle: float = Field(default=180.0, ge=-180.0, le=180.0, description="Maximum angle in degrees")
    default_angle: float = Field(default=90.0, ge=-180.0, le=180.0, description="Default angle in degrees")
    speed_limit: float = Field(default=90.0, gt=0.0, le=360.0, description="Speed limit in degrees per second")

    @field_validator("max_angle")
    @classmethod
    def max_must_be_greater_than_min(cls, v: float, info) -> float:
        if "min_angle" in info.data and v < info.data["min_angle"]:
            raise ValueError("max_angle must be greater than or equal to min_angle")
        return v

    @field_validator("default_angle")
    @classmethod
    def default_must_be_in_range(cls, v: float, info) -> float:
        min_angle = info.data.get("min_angle", 0.0)
        max_angle = info.data.get("max_angle", 180.0)
        if not (min_angle <= v <= max_angle):
            raise ValueError(f"default_angle must be between {min_angle} and {max_angle}")
        return v


class ServoSettings(BaseModel):
    """Servo configuration settings."""

    pan: ServoAxisSettings = Field(default_factory=ServoAxisSettings)
    tilt: ServoAxisSettings = Field(default_factory=ServoAxisSettings)


class NetworkSettings(BaseModel):
    """Network configuration settings."""

    host: str = Field(default="0.0.0.0", description="Server host address")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins",
    )
    esp32_url: str = Field(
        default="ws://192.168.1.100:8080",
        description="WebSocket URL for ESP32 communication",
    )


class AISettings(BaseModel):
    """AI/ML configuration settings."""

    model_name: str = Field(default="yolo11n.pt", min_length=1, description="YOLO model filename")
    confidence_threshold: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Minimum confidence threshold"
    )
    device: str = Field(default="cuda", description="Compute device (cuda, cpu, mps)")
    max_detections: int = Field(default=100, ge=1, le=1000, description="Maximum detections per frame")

    @field_validator("device")
    @classmethod
    def validate_device(cls, v: str) -> str:
        valid_devices = {"cuda", "cpu", "mps"}
        if v not in valid_devices:
            raise ValueError(f"device must be one of {valid_devices}")
        return v


class StreamSettings(BaseModel):
    """Streaming configuration settings."""

    enabled: bool = Field(default=False, description="Enable streaming")
    youtube_key: str = Field(default="", description="YouTube stream key")
    output_width: int = Field(default=1920, gt=0, le=7680, description="Stream output width")
    output_height: int = Field(default=1080, gt=0, le=4320, description="Stream output height")
    bitrate: int = Field(default=4000000, gt=0, le=50000000, description="Stream bitrate in bps")
    fps: int = Field(default=30, ge=1, le=120, description="Stream frames per second")


class Settings(BaseSettings):
    """Main application settings with nested configuration models."""

    camera: CameraSettings = Field(default_factory=CameraSettings)
    servo: ServoSettings = Field(default_factory=ServoSettings)
    network: NetworkSettings = Field(default_factory=NetworkSettings)
    ai: AISettings = Field(default_factory=AISettings)
    stream: StreamSettings = Field(default_factory=StreamSettings)
    output: OutputConfig = Field(default_factory=OutputConfig)

    model_config = {
        "env_prefix": "",
        "env_nested_delimiter": "__",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }
