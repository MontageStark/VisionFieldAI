package com.fieldvision.camera.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class CameraViewModel : ViewModel() {

    private val _uiState = MutableStateFlow(CameraUiState())
    val uiState: StateFlow<CameraUiState> = _uiState.asStateFlow()

    // Navigation
    fun navigateTo(screen: Screen) {
        _uiState.update { it.copy(currentScreen = screen) }
    }

    fun goLive() {
        _uiState.update {
            it.copy(
                currentScreen = Screen.Streaming,
                isStreaming = true,
            )
        }
    }

    fun stopLive() {
        _uiState.update {
            it.copy(
                isStreaming = false,
            )
        }
    }

    fun lockScreen() {
        _uiState.update {
            it.copy(
                currentScreen = Screen.LockMode,
                isLocked = true,
            )
        }
    }

    fun unlockScreen() {
        _uiState.update {
            it.copy(
                currentScreen = Screen.Streaming,
                isLocked = false,
            )
        }
    }

    // Camera Controls
    fun setResolution(resolution: Resolution) {
        _uiState.update { it.copy(resolution = resolution) }
    }

    fun setTargetFps(fps: Int) {
        _uiState.update { it.copy(targetFps = fps) }
    }

    fun setTargetBitrate(bitrate: Int) {
        _uiState.update { it.copy(targetBitrate = bitrate) }
    }

    fun setCodec(codec: Codec) {
        _uiState.update { it.copy(codec = codec) }
    }

    fun setLens(lens: Lens) {
        _uiState.update { it.copy(lens = lens) }
    }

    fun setExposure(mode: ExposureMode) {
        _uiState.update { it.copy(exposure = mode) }
    }

    fun setWhiteBalance(mode: WhiteBalanceMode) {
        _uiState.update { it.copy(whiteBalance = mode) }
    }

    fun setFocusMode(mode: FocusMode) {
        _uiState.update { it.copy(focusMode = mode) }
    }

    fun toggleHdr() {
        _uiState.update { it.copy(hdrEnabled = !it.hdrEnabled) }
    }

    fun toggleTorch() {
        _uiState.update { it.copy(torchEnabled = !it.torchEnabled) }
    }

    fun setZoom(level: Float) {
        _uiState.update { it.copy(zoomLevel = level.coerceIn(1.0f, 10.0f)) }
    }

    // Settings
    fun toggleKeepScreenAwake() {
        _uiState.update { it.copy(keepScreenAwake = !it.keepScreenAwake) }
    }

    fun toggleBatterySaver() {
        _uiState.update { it.copy(batterySaver = !it.batterySaver) }
    }

    fun toggleAutoReconnect() {
        _uiState.update { it.copy(autoReconnect = !it.autoReconnect) }
    }

    fun toggleStartOnBoot() {
        _uiState.update { it.copy(startOnBoot = !it.startOnBoot) }
    }

    fun toggleLockOrientation() {
        _uiState.update { it.copy(lockOrientation = !it.lockOrientation) }
    }

    // Streaming Settings
    fun setStreamMode(mode: StreamMode) {
        _uiState.update { it.copy(streamMode = mode) }
    }

    fun setServerAddress(address: String) {
        _uiState.update { it.copy(serverAddress = address) }
    }

    fun setServerPort(port: Int) {
        _uiState.update { it.copy(serverPort = port) }
    }

    // AI
    fun toggleAiOverlay() {
        _uiState.update { it.copy(aiOverlayEnabled = !it.aiOverlayEnabled) }
    }

    // Calibration
    fun startCalibration() {
        _uiState.update {
            it.copy(
                currentScreen = Screen.Calibration,
                calibrationStep = 1,
            )
        }
    }

    fun setCalibrationStep(step: Int) {
        _uiState.update { it.copy(calibrationStep = step) }
    }

    fun completeCalibration(
        leftGoal: Pair<Float, Float>,
        rightGoal: Pair<Float, Float>,
        center: Pair<Float, Float>,
    ) {
        _uiState.update {
            it.copy(
                isCalibrated = true,
                leftGoalPost = leftGoal,
                rightGoalPost = rightGoal,
                centerCircle = center,
                calibrationStep = 5,
            )
        }
    }

    // State updates from services
    fun updateCameraState(connected: Boolean) {
        _uiState.update { it.copy(isCameraConnected = connected) }
    }

    fun updateNetworkState(wifiConnected: Boolean, strength: Int, latency: Int) {
        _uiState.update {
            it.copy(
                isWifiConnected = wifiConnected,
                wifiStrength = strength,
                latency = latency,
            )
        }
    }

    fun updateDeviceState(battery: Int, temperature: Float, storage: Long) {
        _uiState.update {
            it.copy(
                batteryLevel = battery,
                temperature = temperature,
                storageAvailable = storage,
            )
        }
    }

    fun updateAiState(connected: Boolean, virtualCamera: Boolean, servo: Boolean) {
        _uiState.update {
            it.copy(
                aiConnected = connected,
                virtualCameraActive = virtualCamera,
                servoEnabled = servo,
            )
        }
    }

    fun updateStreamStats(fps: Int, bitrate: Int, droppedFrames: Int) {
        _uiState.update {
            it.copy(
                fps = fps,
                bitrate = bitrate,
                droppedFrames = droppedFrames,
            )
        }
    }

    // Connection lost
    fun onConnectionLost() {
        _uiState.update {
            it.copy(
                isConnectionLost = true,
                reconnecting = true,
                reconnectCountdown = 5,
            )
        }
    }

    fun updateReconnectCountdown(count: Int) {
        _uiState.update { it.copy(reconnectCountdown = count) }
    }

    fun onConnectionRestored() {
        _uiState.update {
            it.copy(
                isConnectionLost = false,
                reconnecting = false,
                reconnectCountdown = 0,
            )
        }
    }

    // Notifications
    fun addNotification(message: String, type: NotificationType) {
        val notification = Notification(
            id = System.currentTimeMillis().toString(),
            message = message,
            type = type,
        )
        _uiState.update {
            it.copy(notifications = it.notifications + notification)
        }
        viewModelScope.launch {
            kotlinx.coroutines.delay(3000)
            removeNotification(notification.id)
        }
    }

    fun removeNotification(id: String) {
        _uiState.update {
            it.copy(notifications = it.notifications.filter { n -> n.id != id })
        }
    }

    // Developer
    fun toggleDeveloperScreen() {
        _uiState.update {
            it.copy(showDeveloperScreen = !it.showDeveloperScreen)
        }
    }

    fun updateDeveloperInfo(encoder: String, cpu: Float, ram: Float, network: String) {
        _uiState.update {
            it.copy(
                encoderInfo = encoder,
                cpuUsage = cpu,
                ramUsage = ram,
                networkInfo = network,
            )
        }
    }
}
