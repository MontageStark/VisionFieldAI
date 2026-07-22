package com.fieldvision.camera.ui

data class CameraUiState(
    val cameraConfig: CameraConfigState = CameraConfigState(),
    val connection: ConnectionState = ConnectionState(),
    val ai: AiState = AiState(),
    val performance: PerformanceState = PerformanceState(),
    val settings: AppSettingsState = AppSettingsState(),
    val navigation: NavigationState = NavigationState(),
    val calibration: CalibrationState = CalibrationState(),
    val emergency: EmergencyState = EmergencyState(),
    val notifications: List<Notification> = emptyList(),
    val developer: DeveloperState = DeveloperState(),
) {
    // Backward-compat computed properties for screens that haven't migrated
    val currentScreen get() = navigation.currentScreen
    val isLocked get() = navigation.isLocked
    val isStreaming get() = cameraConfig.isStreaming
    val isCameraConnected get() = connection.isCameraConnected
    val isWifiConnected get() = connection.isWifiConnected
    val resolution get() = cameraConfig.resolution
    val targetFps get() = cameraConfig.targetFps
    val targetBitrate get() = cameraConfig.targetBitrate
    val codec get() = cameraConfig.codec
    val fps get() = performance.fps
    val bitrate get() = performance.bitrate
    val droppedFrames get() = performance.droppedFrames
    val aiOverlayEnabled get() = ai.overlayEnabled
    val aiConnected get() = ai.connected
    val keepScreenAwake get() = settings.keepScreenAwake
    val batterySaver get() = settings.batterySaver
    val autoReconnect get() = settings.autoReconnect
    val streamMode get() = settings.streamMode

    // Connection sub-state compat
    val wifiStrength get() = connection.wifiStrength
    val latency get() = connection.latency
    val batteryLevel get() = connection.batteryLevel
    val temperature get() = connection.temperature
    val serverAddress get() = connection.serverAddress
    val serverPort get() = connection.serverPort

    // CameraConfig sub-state compat
    val torchEnabled get() = cameraConfig.torchEnabled
    val lens get() = cameraConfig.lens
    val exposure get() = cameraConfig.exposure
    val whiteBalance get() = cameraConfig.whiteBalance
    val focusMode get() = cameraConfig.focusMode
    val hdrEnabled get() = cameraConfig.hdrEnabled

    // Settings sub-state compat
    val startOnBoot get() = settings.startOnBoot
    val lockOrientation get() = settings.lockOrientation

    // Calibration sub-state compat
    val calibrationStep get() = calibration.step

    // Developer sub-state compat
    val cpuUsage get() = developer.cpuUsage
    val ramUsage get() = developer.ramUsage
    val isPreviewActive get() = false
}

data class CameraConfigState(
    val isStreaming: Boolean = false,
    val resolution: Resolution = Resolution.R720P,
    val targetFps: Int = 30,
    val targetBitrate: Int = 20,
    val codec: Codec = Codec.H264,
    val lens: Lens = Lens.WIDE,
    val exposure: ExposureMode = ExposureMode.AUTO,
    val whiteBalance: WhiteBalanceMode = WhiteBalanceMode.AUTO,
    val focusMode: FocusMode = FocusMode.AUTO,
    val hdrEnabled: Boolean = false,
    val torchEnabled: Boolean = false,
    val zoomLevel: Float = 1.0f,
)

data class ConnectionState(
    val isCameraConnected: Boolean = false,
    val isWifiConnected: Boolean = false,
    val wifiStrength: Int = 0,
    val latency: Int = 0,
    val batteryLevel: Int = 0,
    val temperature: Float = 0f,
    val storageAvailable: Long = 0,
    val serverAddress: String = "",
    val serverPort: Int = 8554,
)

data class AiState(
    val connected: Boolean = false,
    val virtualCameraActive: Boolean = false,
    val servoEnabled: Boolean = false,
    val overlayEnabled: Boolean = false,
)

data class PerformanceState(
    val fps: Int = 0,
    val bitrate: Int = 0,
    val droppedFrames: Int = 0,
)

data class AppSettingsState(
    val keepScreenAwake: Boolean = true,
    val batterySaver: Boolean = false,
    val autoReconnect: Boolean = true,
    val startOnBoot: Boolean = false,
    val lockOrientation: Boolean = true,
    val streamMode: StreamMode = StreamMode.RTSP,
)

data class NavigationState(
    val currentScreen: Screen = Screen.Home,
    val isLocked: Boolean = false,
)

data class CalibrationState(
    val step: Int = 0,
    val isCalibrated: Boolean = false,
    val leftGoalPost: Pair<Float, Float>? = null,
    val rightGoalPost: Pair<Float, Float>? = null,
    val centerCircle: Pair<Float, Float>? = null,
)

data class EmergencyState(
    val isConnectionLost: Boolean = false,
    val reconnecting: Boolean = false,
    val reconnectCountdown: Int = 0,
)

data class DeveloperState(
    val showScreen: Boolean = false,
    val encoderInfo: String = "",
    val cpuUsage: Float = 0f,
    val ramUsage: Float = 0f,
    val networkInfo: String = "",
)

enum class Screen {
    Home, Streaming, LockMode, Settings, Calibration, Developer,
}

enum class Resolution(val width: Int, val height: Int, val label: String) {
    R4K(3840, 2160, "4K"),
    R1080P(1920, 1080, "1080p"),
    R720P(1280, 720, "720p"),
}

enum class Codec(val label: String) { H264("H.264"), H265("H.265") }
enum class Lens(val label: String) { WIDE("Wide"), ULTRA_WIDE("Ultra Wide") }
enum class ExposureMode(val label: String) { AUTO("Auto"), MANUAL("Manual") }
enum class WhiteBalanceMode(val label: String) { AUTO("Auto"), MANUAL("Manual") }
enum class FocusMode(val label: String) { AUTO("Auto"), MANUAL("Manual") }
enum class StreamMode(val label: String) { RTSP("RTSP"), SRT("SRT"), USB("USB"), CUSTOM("Custom") }

data class Notification(
    val id: String,
    val message: String,
    val type: NotificationType,
    val timestamp: Long = System.currentTimeMillis(),
)

enum class NotificationType { SUCCESS, WARNING, ERROR }
