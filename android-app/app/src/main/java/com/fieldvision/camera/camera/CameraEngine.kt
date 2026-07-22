package com.fieldvision.camera.camera

import android.content.Context
import android.hardware.camera2.*
import android.os.Handler
import android.os.HandlerThread
import android.util.Log
import android.view.Surface
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.concurrent.Semaphore
import java.util.concurrent.TimeUnit

class CameraEngine(private val context: Context) {

    private var cameraDevice: CameraDevice? = null
    private var captureSession: CameraCaptureSession? = null
    private var cameraThread: HandlerThread? = null
    private var cameraHandler: Handler? = null

    private val cameraOpenLock = Semaphore(1)
    private var currentConfig = CameraConfig()

    private var previewSurface: Surface? = null
    private var streamingSurface: Surface? = null

    private val _state = MutableStateFlow<EngineState>(EngineState.Closed)
    val state: StateFlow<EngineState> = _state.asStateFlow()

    fun initialize() {
        cameraThread = HandlerThread("CameraThread").apply { start() }
        cameraHandler = Handler(cameraThread!!.looper)
        _state.value = EngineState.Closed
    }

    fun openCamera(surface: Surface, config: CameraConfig = CameraConfig()): Boolean {
        currentConfig = config
        previewSurface = surface

        if (_state.value is EngineState.Open || _state.value is EngineState.Previewing) {
            return true
        }

        val manager = context.getSystemService(Context.CAMERA_SERVICE) as CameraManager

        return try {
            if (!cameraOpenLock.tryAcquire(2500, TimeUnit.MILLISECONDS)) {
                Log.e(TAG, "Camera open lock timeout")
                return false
            }

            _state.value = EngineState.Opening

            val cameraId = getBackCameraId(manager)
            if (cameraId != null) {
                manager.openCamera(cameraId, stateCallback, cameraHandler)
                true
            } else {
                _state.value = EngineState.Error("No back camera found")
                false
            }
        } catch (e: SecurityException) {
            Log.e(TAG, "Camera permission denied", e)
            _state.value = EngineState.Error("Permission denied")
            false
        } catch (e: CameraAccessException) {
            Log.e(TAG, "Camera access error", e)
            _state.value = EngineState.Error("Access error")
            false
        }
    }

    fun updateConfig(config: CameraConfig) {
        currentConfig = config
    }

    fun closeCamera() {
        // Close session and device FIRST, then release semaphore
        try {
            captureSession?.close()
        } catch (e: Exception) {
            Log.e(TAG, "Error closing session", e)
        }
        captureSession = null

        try {
            cameraDevice?.close()
        } catch (e: Exception) {
            Log.e(TAG, "Error closing camera", e)
        }
        cameraDevice = null

        _state.value = EngineState.Closed

        // Release semaphore AFTER cleanup
        if (cameraOpenLock.availablePermits() == 0) {
            cameraOpenLock.release()
        }
    }

    fun shutdown() {
        closeCamera()
        cameraThread?.quitSafely()
        try { cameraThread?.join(1000) } catch (_: InterruptedException) { }
        cameraThread = null
        cameraHandler = null
    }

    private fun getBackCameraId(manager: CameraManager): String? {
        for (id in manager.cameraIdList) {
            val characteristics = manager.getCameraCharacteristics(id)
            val facing = characteristics.get(CameraCharacteristics.LENS_FACING)
            if (facing == CameraCharacteristics.LENS_FACING_BACK) {
                return id
            }
        }
        return null
    }

    private val stateCallback = object : CameraDevice.StateCallback() {
        override fun onOpened(camera: CameraDevice) {
            cameraOpenLock.release()
            cameraDevice = camera
            _state.value = EngineState.Open
            createCaptureSession()
        }

        override fun onDisconnected(camera: CameraDevice) {
            cameraOpenLock.release()
            camera.close()
            cameraDevice = null
            _state.value = EngineState.Closed
        }

        override fun onError(camera: CameraDevice, error: Int) {
            cameraOpenLock.release()
            camera.close()
            cameraDevice = null
            _state.value = EngineState.Error("Camera error: $error")
        }
    }

    private fun createCaptureSession() {
        val camera = cameraDevice ?: return

        val surfaces = mutableListOf<Surface>()
        previewSurface?.let { surfaces.add(it) }
        streamingSurface?.let { surfaces.add(it) }

        if (surfaces.isEmpty()) {
            _state.value = EngineState.Error("No surfaces")
            return
        }

        try {
            camera.createCaptureSession(
                surfaces,
                object : CameraCaptureSession.StateCallback() {
                    override fun onConfigured(session: CameraCaptureSession) {
                        captureSession = session
                        startPreview()
                    }

                    override fun onConfigureFailed(session: CameraCaptureSession) {
                        _state.value = EngineState.Error("Session config failed")
                    }
                },
                cameraHandler
            )
        } catch (e: CameraAccessException) {
            Log.e(TAG, "Session creation error", e)
            _state.value = EngineState.Error("Session error")
        }
    }

    private fun startPreview() {
        val camera = cameraDevice ?: return
        val session = captureSession ?: return

        try {
            val builder = camera.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW)
            previewSurface?.let { builder.addTarget(it) }

            builder.set(CaptureRequest.CONTROL_MODE, CaptureRequest.CONTROL_MODE_AUTO)

            session.setRepeatingRequest(builder.build(), null, cameraHandler)
            _state.value = EngineState.Previewing
        } catch (e: CameraAccessException) {
            Log.e(TAG, "Preview error", e)
            _state.value = EngineState.Error("Preview error")
        }
    }

    companion object {
        private const val TAG = "CameraEngine"
    }
}

sealed class EngineState {
    data object Closed : EngineState()
    data object Opening : EngineState()
    data object Open : EngineState()
    data object Previewing : EngineState()
    data class Error(val message: String) : EngineState()
}
