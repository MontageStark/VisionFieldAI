package com.fieldvision.camera.camera

import android.content.Context
import android.graphics.SurfaceTexture
import android.hardware.camera2.*
import android.os.Handler
import android.os.HandlerThread
import android.util.Size
import android.view.Surface
import androidx.lifecycle.LifecycleOwner
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
    
    fun initialize(lifecycleOwner: LifecycleOwner) {
        cameraThread = HandlerThread("CameraThread").apply { start() }
        cameraHandler = Handler(cameraThread!!.looper)
    }
    
    fun openCamera(surface: Surface, config: CameraConfig = CameraConfig()): Boolean {
        currentConfig = config
        previewSurface = surface
        
        val manager = context.getSystemService(Context.CAMERA_SERVICE) as CameraManager
        
        return try {
            if (!cameraOpenLock.tryAcquire(2500, TimeUnit.MILLISECONDS)) {
                return false
            }
            
            val cameraId = getBackCameraId(manager)
            if (cameraId != null) {
                manager.openCamera(cameraId, stateCallback, cameraHandler)
                true
            } else {
                false
            }
        } catch (e: SecurityException) {
            e.printStackTrace()
            false
        } catch (e: CameraAccessException) {
            e.printStackTrace()
            false
        }
    }
    
    fun updateConfig(config: CameraConfig) {
        currentConfig = config
        // Reconfigure capture session if active
    }
    
    fun closeCamera() {
        cameraOpenLock.release()
        captureSession?.close()
        captureSession = null
        cameraDevice?.close()
        cameraDevice = null
    }
    
    fun shutdown() {
        cameraThread?.quitSafely()
        try {
            cameraThread?.join()
        } catch (e: InterruptedException) {
            e.printStackTrace()
        }
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
            createCaptureSession()
        }
        
        override fun onDisconnected(camera: CameraDevice) {
            cameraOpenLock.release()
            camera.close()
            cameraDevice = null
        }
        
        override fun onError(camera: CameraDevice, error: Int) {
            cameraOpenLock.release()
            camera.close()
            cameraDevice = null
        }
    }
    
    private fun createCaptureSession() {
        val camera = cameraDevice ?: return
        
        val surfaces = mutableListOf<Surface>()
        previewSurface?.let { surfaces.add(it) }
        streamingSurface?.let { surfaces.add(it) }
        
        try {
            camera.createCaptureSession(
                surfaces,
                object : CameraCaptureSession.StateCallback() {
                    override fun onConfigured(session: CameraCaptureSession) {
                        captureSession = session
                        startPreview()
                    }
                    
                    override fun onConfigureFailed(session: CameraCaptureSession) {
                        // Handle failure
                    }
                },
                cameraHandler
            )
        } catch (e: CameraAccessException) {
            e.printStackTrace()
        }
    }
    
    private fun startPreview() {
        val camera = cameraDevice ?: return
        val session = captureSession ?: return
        
        try {
            val builder = camera.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW)
            previewSurface?.let { builder.addTarget(it) }
            
            // Apply config
            builder.set(CaptureRequest.CONTROL_MODE, CaptureRequest.CONTROL_MODE_AUTO)
            
            session.setRepeatingRequest(builder.build(), null, cameraHandler)
        } catch (e: CameraAccessException) {
            e.printStackTrace()
        }
    }
}
