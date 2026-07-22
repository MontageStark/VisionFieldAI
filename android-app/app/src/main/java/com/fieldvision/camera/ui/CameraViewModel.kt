package com.fieldvision.camera.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.fieldvision.camera.data.FieldVisionDatabase
import com.fieldvision.camera.device.DeviceTelemetryMonitor
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class CameraViewModel @Inject constructor(
    private val database: FieldVisionDatabase,
    private val telemetryMonitor: DeviceTelemetryMonitor,
) : ViewModel() {

    private val _uiState = MutableStateFlow(CameraUiState())
    val uiState: StateFlow<CameraUiState> = _uiState.asStateFlow()

    init {
        loadSavedSettings()
        startTelemetry()
    }

    private fun startTelemetry() {
        telemetryMonitor.onTelemetryChanged = { battery, temperature, storage ->
            _uiState.update { st ->
                st.copy(connection = st.connection.copy(
                    batteryLevel = battery.coerceAtLeast(0),
                    temperature = temperature,
                    storageAvailable = storage,
                ))
            }
        }
        telemetryMonitor.startMonitoring()
    }

    override fun onCleared() {
        telemetryMonitor.stopMonitoring()
        super.onCleared()
    }

    private fun loadSavedSettings() {
        viewModelScope.launch {
            val s = database.cameraSettingsDao().getSettings() ?: return@launch
            _uiState.update { st ->
                st.copy(
                    cameraConfig = st.cameraConfig.copy(
                        resolution = s.resolution,
                        targetFps = s.targetFps,
                        targetBitrate = s.targetBitrate,
                        codec = s.codec,
                    ),
                    settings = st.settings.copy(
                        keepScreenAwake = s.keepScreenAwake,
                        batterySaver = s.batterySaver,
                        autoReconnect = s.autoReconnect,
                        streamMode = s.streamMode,
                    ),
                )
            }
        }
    }

    private fun saveSettings() {
        viewModelScope.launch {
            val st = _uiState.value
            database.cameraSettingsDao().upsert(
                com.fieldvision.camera.data.CameraSettingsEntity(
                    id = 1,
                    resolutionName = st.cameraConfig.resolution.name,
                    targetFps = st.cameraConfig.targetFps,
                    targetBitrate = st.cameraConfig.targetBitrate,
                    codecName = st.cameraConfig.codec.name,
                    keepScreenAwake = st.settings.keepScreenAwake,
                    batterySaver = st.settings.batterySaver,
                    autoReconnect = st.settings.autoReconnect,
                    streamModeName = st.settings.streamMode.name,
                )
            )
        }
    }

    // Navigation
    fun navigateTo(screen: Screen) = _uiState.update { it.copy(navigation = it.navigation.copy(currentScreen = screen)) }
    fun goLive() = _uiState.update { it.copy(navigation = it.navigation.copy(currentScreen = Screen.Streaming), cameraConfig = it.cameraConfig.copy(isStreaming = true)) }
    fun stopLive() = _uiState.update { it.copy(cameraConfig = it.cameraConfig.copy(isStreaming = false)) }
    fun lockScreen() = _uiState.update { it.copy(navigation = NavigationState(currentScreen = Screen.LockMode, isLocked = true)) }
    fun unlockScreen() = _uiState.update { it.copy(navigation = NavigationState(currentScreen = Screen.Streaming, isLocked = false)) }

    // Camera Config
    fun setResolution(resolution: Resolution) { _uiState.update { it.copy(cameraConfig = it.cameraConfig.copy(resolution = resolution)) }; saveSettings() }
    fun setTargetFps(fps: Int) { _uiState.update { it.copy(cameraConfig = it.cameraConfig.copy(targetFps = fps)) }; saveSettings() }
    fun setTargetBitrate(bitrate: Int) { _uiState.update { it.copy(cameraConfig = it.cameraConfig.copy(targetBitrate = bitrate)) }; saveSettings() }
    fun setCodec(codec: Codec) { _uiState.update { it.copy(cameraConfig = it.cameraConfig.copy(codec = codec)) }; saveSettings() }
    fun setLens(lens: Lens) = _uiState.update { it.copy(cameraConfig = it.cameraConfig.copy(lens = lens)) }
    fun setExposure(mode: ExposureMode) = _uiState.update { it.copy(cameraConfig = it.cameraConfig.copy(exposure = mode)) }
    fun setWhiteBalance(mode: WhiteBalanceMode) = _uiState.update { it.copy(cameraConfig = it.cameraConfig.copy(whiteBalance = mode)) }
    fun setFocusMode(mode: FocusMode) = _uiState.update { it.copy(cameraConfig = it.cameraConfig.copy(focusMode = mode)) }
    fun toggleHdr() = _uiState.update { it.copy(cameraConfig = it.cameraConfig.copy(hdrEnabled = !it.cameraConfig.hdrEnabled)) }
    fun toggleTorch() = _uiState.update { it.copy(cameraConfig = it.cameraConfig.copy(torchEnabled = !it.cameraConfig.torchEnabled)) }
    fun setZoom(level: Float) = _uiState.update { it.copy(cameraConfig = it.cameraConfig.copy(zoomLevel = level.coerceIn(1f, 10f))) }

    // Settings
    fun toggleKeepScreenAwake() { _uiState.update { it.copy(settings = it.settings.copy(keepScreenAwake = !it.settings.keepScreenAwake)) }; saveSettings() }
    fun toggleBatterySaver() { _uiState.update { it.copy(settings = it.settings.copy(batterySaver = !it.settings.batterySaver)) }; saveSettings() }
    fun toggleAutoReconnect() { _uiState.update { it.copy(settings = it.settings.copy(autoReconnect = !it.settings.autoReconnect)) }; saveSettings() }
    fun toggleStartOnBoot() = _uiState.update { it.copy(settings = it.settings.copy(startOnBoot = !it.settings.startOnBoot)) }
    fun toggleLockOrientation() = _uiState.update { it.copy(settings = it.settings.copy(lockOrientation = !it.settings.lockOrientation)) }
    fun setStreamMode(mode: StreamMode) { _uiState.update { it.copy(settings = it.settings.copy(streamMode = mode)) }; saveSettings() }
    fun setServerAddress(address: String) = _uiState.update { it.copy(connection = it.connection.copy(serverAddress = address)) }
    fun setServerPort(port: Int) = _uiState.update { it.copy(connection = it.connection.copy(serverPort = port)) }

    // AI
    fun toggleAiOverlay() = _uiState.update { it.copy(ai = it.ai.copy(overlayEnabled = !it.ai.overlayEnabled)) }

    // Calibration
    fun startCalibration() = _uiState.update { it.copy(navigation = it.navigation.copy(currentScreen = Screen.Calibration), calibration = it.calibration.copy(step = 1)) }
    fun setCalibrationStep(step: Int) = _uiState.update { it.copy(calibration = it.calibration.copy(step = step)) }
    fun completeCalibration(left: Pair<Float, Float>, right: Pair<Float, Float>, center: Pair<Float, Float>) =
        _uiState.update { it.copy(calibration = CalibrationState(step = 5, isCalibrated = true, leftGoalPost = left, rightGoalPost = right, centerCircle = center)) }

    // Service state updates
    fun updateCameraState(connected: Boolean) = _uiState.update { it.copy(connection = it.connection.copy(isCameraConnected = connected)) }
    fun updateNetworkState(wifiConnected: Boolean, strength: Int, latency: Int) = _uiState.update { it.copy(connection = it.connection.copy(isWifiConnected = wifiConnected, wifiStrength = strength, latency = latency)) }
    fun updateDeviceState(battery: Int, temperature: Float, storage: Long) = _uiState.update { it.copy(connection = it.connection.copy(batteryLevel = battery, temperature = temperature, storageAvailable = storage)) }
    fun updateAiState(connected: Boolean, virtualCamera: Boolean, servo: Boolean) = _uiState.update { it.copy(ai = AiState(connected = connected, virtualCameraActive = virtualCamera, servoEnabled = servo, overlayEnabled = it.ai.overlayEnabled)) }
    fun updateStreamStats(fps: Int, bitrate: Int, droppedFrames: Int) = _uiState.update { it.copy(performance = PerformanceState(fps, bitrate, droppedFrames)) }

    // Emergency
    fun onConnectionLost() = _uiState.update { it.copy(emergency = EmergencyState(isConnectionLost = true, reconnecting = true, reconnectCountdown = 5)) }
    fun updateReconnectCountdown(count: Int) = _uiState.update { it.copy(emergency = it.emergency.copy(reconnectCountdown = count)) }
    fun onConnectionRestored() = _uiState.update { it.copy(emergency = EmergencyState()) }

    // Notifications
    fun addNotification(message: String, type: NotificationType) {
        val n = Notification(id = System.currentTimeMillis().toString(), message = message, type = type)
        _uiState.update { it.copy(notifications = it.notifications + n) }
        viewModelScope.launch { kotlinx.coroutines.delay(3000); removeNotification(n.id) }
    }
    fun removeNotification(id: String) = _uiState.update { it.copy(notifications = it.notifications.filter { n -> n.id != id }) }

    // Developer
    fun toggleDeveloperScreen() = _uiState.update { it.copy(developer = it.developer.copy(showScreen = !it.developer.showScreen)) }
    fun updateDeveloperInfo(encoder: String, cpu: Float, ram: Float, network: String) =
        _uiState.update { it.copy(developer = DeveloperState(showScreen = it.developer.showScreen, encoderInfo = encoder, cpuUsage = cpu, ramUsage = ram, networkInfo = network)) }
}
