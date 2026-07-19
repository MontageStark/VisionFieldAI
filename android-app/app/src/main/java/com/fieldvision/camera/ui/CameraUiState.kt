package com.fieldvision.camera.ui

data class CameraUiState(
    // Navigation
    val currentScreen: Screen = Screen.Home,
    val isLocked: Boolean = false,

    // Camera
    val isCameraConnected: Boolean = false,
    val isPreviewActive: Boolean = false,

    // Streaming
    val isStreaming: Boolean = false,
    val streamUrl: String = "",
    val bitrate: Int = 0,
    val fps: Int = 0,
    val droppedFrames: Int = 0,

    // Resolution
    val resolution: Resolution = Resolution.R720P,
    val targetFps: Int = 30,
    val targetBitrate: Int = 20,
    val codec: Codec = Codec.H264,

    // Connection
    val isWifiConnected: Boolean = false,
    val wifiStrength: Int = 0,
    val latency: Int = 0,

    // Device
    val batteryLevel: Int = 0,
    val temperature: Float = 0f,
    val storageAvailable: Long = 0,

    // AI
    val aiConnected: Boolean = false,
    val virtualCameraActive: Boolean = false,
    val servoEnabled: Boolean = false,
    val aiOverlayEnabled: Boolean = false,

    // Camera Controls
    val lens: Lens = Lens.WIDE,
    val exposure: ExposureMode = ExposureMode.AUTO,
    val whiteBalance: WhiteBalanceMode = WhiteBalanceMode.AUTO,
    val focusMode: FocusMode = FocusMode.AUTO,
    val hdrEnabled: Boolean = false,
    val torchEnabled: Boolean = false,
    val zoomLevel: Float = 1.0f,

    // Settings
    val keepScreenAwake: Boolean = true,
    val batterySaver: Boolean = false,
    val autoReconnect: Boolean = true,
    val startOnBoot: Boolean = false,
    val lockOrientation: Boolean = true,

    // Streaming Settings
    val streamMode: StreamMode = StreamMode.RTSP,
    val serverAddress: String = "",
    val serverPort: Int = 8554,

    // Calibration
    val calibrationStep: Int = 0,
    val isCalibrated: Boolean = false,
    val leftGoalPost: Pair<Float, Float>? = null,
    val rightGoalPost: Pair<Float, Float>? = null,
    val centerCircle: Pair<Float, Float>? = null,

    // Emergency
    val isConnectionLost: Boolean = false,
    val reconnecting: Boolean = false,
    val reconnectCountdown: Int = 0,

    // Notifications
    val notifications: List<Notification> = emptyList(),

    // Developer
    val showDeveloperScreen: Boolean = false,
    val encoderInfo: String = "",
    val cpuUsage: Float = 0f,
    val ramUsage: Float = 0f,
    val networkInfo: String = "",
)

enum class Screen {
    Home,
    Streaming,
    LockMode,
    Settings,
    Calibration,
    Developer,
}

enum class Resolution(val width: Int, val height: Int, val label: String) {
    R4K(3840, 2160, "4K"),
    R1080P(1920, 1080, "1080p"),
    R720P(1280, 720, "720p"),
}

enum class Codec(val label: String) {
    H264("H.264"),
    H265("H.265"),
}

enum class Lens(val label: String) {
    WIDE("Wide"),
    ULTRA_WIDE("Ultra Wide"),
}

enum class ExposureMode(val label: String) {
    AUTO("Auto"),
    MANUAL("Manual"),
}

enum class WhiteBalanceMode(val label: String) {
    AUTO("Auto"),
    MANUAL("Manual"),
}

enum class FocusMode(val label: String) {
    AUTO("Auto"),
    MANUAL("Manual"),
}

enum class StreamMode(val label: String) {
    RTSP("RTSP"),
    SRT("SRT"),
    USB("USB"),
    CUSTOM("Custom"),
}

data class Notification(
    val id: String,
    val message: String,
    val type: NotificationType,
    val timestamp: Long = System.currentTimeMillis(),
)

enum class NotificationType {
    SUCCESS,
    WARNING,
    ERROR,
}
