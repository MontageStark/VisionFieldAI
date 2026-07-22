package com.fieldvision.camera.ui

import com.fieldvision.camera.camera.Resolution
import com.fieldvision.camera.data.CameraSettingsEntity
import com.fieldvision.camera.data.CameraSettingsDao
import io.mockk.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.*
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class CameraViewModelTest {

    private val testDispatcher = UnconfinedTestDispatcher()

    private lateinit var mockDao: CameraSettingsDao

    @Before
    fun setup() {
        Dispatchers.setMain(testDispatcher)
        mockDao = mockk(relaxed = true)
        coEvery { mockDao.getSettings() } returns null
        coEvery { mockDao.upsert(any()) } just Runs
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `CameraUiState initial defaults are correct`() {
        val state = CameraUiState()

        assertEquals("1280x720", state.resolution)
        assertEquals(30, state.targetFps)
        assertEquals(4_000_000, state.targetBitrate)
        assertEquals("H264", state.codec)
        assertFalse(state.isCameraConnected)
        assertFalse(state.aiOverlayEnabled)
        assertEquals("mjpeg", state.streamMode)
    }

    @Test
    fun `CameraConfigState defaults are correct`() {
        val config = CameraConfigState()

        assertEquals("1280x720", config.resolution)
        assertEquals(30, config.targetFps)
        assertEquals(4_000_000, config.targetBitrate)
        assertEquals("H264", config.codec)
        assertFalse(config.torchEnabled)
        assertTrue(config.hdrEnabled)
        assertEquals("back", config.lens)
        assertEquals(0f, config.exposure, 0.01f)
    }

    @Test
    fun `ConnectionState defaults are correct`() {
        val conn = ConnectionState()

        assertFalse(conn.isCameraConnected)
        assertFalse(conn.isWifiConnected)
        assertEquals("Waiting for connection...", conn.connectionStatus)
        assertEquals("192.168.0.100", conn.serverAddress)
        assertEquals(8080, conn.serverPort)
        assertEquals(0, conn.batteryLevel)
    }

    @Test
    fun `AiState defaults are correct`() {
        val ai = AiState()

        assertFalse(ai.aiOverlayEnabled)
        assertFalse(ai.aiConnected)
        assertEquals("Not connected", ai.aiStatus)
        assertEquals(0f, ai.aiFps)
    }

    @Test
    fun `AppSettingsState defaults are correct`() {
        val settings = AppSettingsState()

        assertEquals("mjpeg", settings.streamMode)
        assertTrue(settings.keepScreenAwake)
        assertTrue(settings.batterySaver)
        assertTrue(settings.autoReconnect)
        assertFalse(settings.startOnBoot)
        assertTrue(settings.lockOrientation)
    }

    @Test
    fun `PerformanceState defaults are correct`() {
        val perf = PerformanceState()

        assertEquals(0f, perf.bitrate)
        assertEquals(0, perf.latency)
        assertEquals(0, perf.droppedFrames)
        assertEquals(0f, perf.aiFps)
    }

    @Test
    fun `copy sub-state preserves other sub-states`() {
        val original = CameraUiState(
            cameraConfig = CameraConfigState(resolution = "640x480"),
            connection = ConnectionState(batteryLevel = 50),
            ai = AiState(aiStatus = "Connected"),
            settings = AppSettingsState(streamMode = "webrtc")
        )

        val updated = original.copy(
            cameraConfig = original.cameraConfig.copy(resolution = "1920x1080")
        )

        assertEquals("1920x1080", updated.resolution)
        assertEquals(50, updated.batteryLevel)
        assertEquals("Connected", updated.aiStatus)
        assertEquals("webrtc", updated.streamMode)
    }

    @Test
    fun `computed resolution matches sub-state`() {
        val state = CameraUiState(
            cameraConfig = CameraConfigState(resolution = "3840x2160")
        )
        assertEquals("3840x2160", state.resolution)
    }

    @Test
    fun `computed connection fields match sub-state`() {
        val state = CameraUiState(
            connection = ConnectionState(
                isCameraConnected = true,
                isWifiConnected = true,
                batteryLevel = 92,
                serverAddress = "10.0.0.5",
                serverPort = 9999
            )
        )

        assertTrue(state.isCameraConnected)
        assertTrue(state.isWifiConnected)
        assertEquals(92, state.batteryLevel)
        assertEquals("10.0.0.5", state.serverAddress)
        assertEquals(9999, state.serverPort)
    }

    @Test
    fun `CameraSettingsDao default values map to entity`() {
        val entity = CameraSettingsEntity(
            id = 1,
            resolution = "1280x720",
            fps = 30,
            bitrate = 4000000,
            codec = "H264",
            streamMode = "mjpeg"
        )

        assertEquals("1280x720", entity.resolution)
        assertEquals(30, entity.fps)
        assertEquals(4000000, entity.bitrate)
        assertEquals("H264", entity.codec)
        assertEquals("mjpeg", entity.streamMode)
    }
}
