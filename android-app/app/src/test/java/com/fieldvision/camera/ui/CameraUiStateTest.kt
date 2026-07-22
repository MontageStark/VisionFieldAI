package com.fieldvision.camera.ui

import org.junit.Assert.*
import org.junit.Test

class CameraUiStateTest {

    @Test
    fun `initial state has correct defaults`() {
        val state = CameraUiState()

        // CameraConfig defaults
        assertEquals("1280x720", state.resolution)
        assertEquals(30, state.targetFps)
        assertEquals(4_000_000, state.targetBitrate)
        assertEquals("H264", state.codec)
        assertTrue(state.torchEnabled)

        // ConnectionState defaults
        assertFalse(state.isCameraConnected)
        assertFalse(state.isWifiConnected)
        assertEquals("Waiting for connection...", state.connectionStatus)
        assertEquals("192.168.0.100", state.serverAddress)
        assertEquals(8080, state.serverPort)
        assertEquals(0, state.batteryLevel)

        // AiState defaults
        assertFalse(state.aiOverlayEnabled)
        assertFalse(state.aiConnected)
        assertEquals("Not connected", state.aiStatus)

        // Performance defaults
        assertEquals(0f, state.bitrate)
        assertEquals(0, state.latency)
        assertEquals(0, state.droppedFrames)

        // AppSettings defaults
        assertEquals("mjpeg", state.streamMode)
        assertTrue(state.hdrEnabled)
        assertTrue(state.keepScreenAwake)
        assertTrue(state.batterySaver)
        assertTrue(state.autoReconnect)
        assertFalse(state.startOnBoot)
        assertTrue(state.lockOrientation)
    }

    @Test
    fun `computed properties delegate to sub-states`() {
        val state = CameraUiState(
            cameraConfig = CameraConfigState(
                resolution = "1920x1080",
                targetFps = 60,
                targetBitrate = 8_000_000,
                codec = "H265",
                torchEnabled = false,
                hdrEnabled = false,
                lens = "front",
                exposure = 1.5f,
                whiteBalance = 5000,
                focusMode = "manual"
            ),
            connection = ConnectionState(
                isCameraConnected = true,
                isWifiConnected = true,
                connectionStatus = "Connected",
                serverAddress = "192.168.0.1",
                serverPort = 9090,
                batteryLevel = 75
            ),
            ai = AiState(
                aiOverlayEnabled = true,
                aiConnected = true,
                aiStatus = "Connected"
            ),
            performance = PerformanceState(
                bitrate = 50f,
                latency = 15,
                droppedFrames = 3
            ),
            settings = AppSettingsState(
                streamMode = "webrtc",
                keepScreenAwake = false,
                batterySaver = false,
                autoReconnect = false,
                startOnBoot = true,
                lockOrientation = false
            )
        )

        // Computed properties should reflect sub-state values
        assertEquals("1920x1080", state.resolution)
        assertEquals(60, state.targetFps)
        assertEquals(8_000_000, state.targetBitrate)
        assertEquals("H265", state.codec)
        assertFalse(state.torchEnabled)

        assertTrue(state.isCameraConnected)
        assertTrue(state.isWifiConnected)
        assertEquals("Connected", state.connectionStatus)
        assertEquals("192.168.0.1", state.serverAddress)
        assertEquals(9090, state.serverPort)
        assertEquals(75, state.batteryLevel)

        assertTrue(state.aiOverlayEnabled)
        assertTrue(state.aiConnected)
        assertEquals("Connected", state.aiStatus)

        assertEquals(50f, state.bitrate, 0.01f)
        assertEquals(15, state.latency)
        assertEquals(3, state.droppedFrames)

        assertEquals("webrtc", state.streamMode)
        assertFalse(state.keepScreenAwake)
        assertFalse(state.batterySaver)
        assertFalse(state.autoReconnect)
        assertTrue(state.startOnBoot)
        assertFalse(state.lockOrientation)
    }

    @Test
    fun `copy with sub-state preserves other sub-states`() {
        val original = CameraUiState(
            cameraConfig = CameraConfigState(resolution = "640x480"),
            connection = ConnectionState(batteryLevel = 50),
            ai = AiState(aiStatus = "Connected")
        )

        val updated = original.copy(
            cameraConfig = original.cameraConfig.copy(resolution = "1920x1080")
        )

        assertEquals("1920x1080", updated.resolution)
        assertEquals(50, updated.batteryLevel)
        assertEquals("Connected", updated.aiStatus)
    }

    @Test
    fun `toDebugString contains key fields`() {
        val state = CameraUiState(
            cameraConfig = CameraConfigState(resolution = "1280x720"),
            connection = ConnectionState(
                isCameraConnected = true,
                isWifiConnected = true,
                batteryLevel = 80
            )
        )

        val debug = state.toDebugString()

        assertTrue(debug.contains("1280x720"))
        assertTrue(debug.contains("camera=true"))
        assertTrue(debug.contains("wifi=true"))
        assertTrue(debug.contains("battery=80"))
    }
}
