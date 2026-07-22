package com.fieldvision.camera

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.graphics.Matrix
import android.graphics.SurfaceTexture
import android.hardware.camera2.*
import android.media.ImageReader
import android.os.Bundle
import android.os.Handler
import android.os.HandlerThread
import android.util.Log
import android.view.Surface
import android.view.TextureView
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import com.fieldvision.camera.camera.Resolution
import com.fieldvision.camera.discovery.DiscoveryService
import com.fieldvision.camera.discovery.PhoneInfo
import com.fieldvision.camera.network.NetworkMonitor
import com.fieldvision.camera.stream.StreamServer
import com.fieldvision.camera.ui.CameraViewModel
import com.fieldvision.camera.ui.navigation.CameraNavHost
import com.fieldvision.camera.ui.theme.FieldVisionTheme
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.*
import java.net.Inet4Address
import java.net.NetworkInterface
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    @Inject lateinit var streamServer: StreamServer
    @Inject lateinit var discoveryService: DiscoveryService
    @Inject lateinit var networkMonitor: NetworkMonitor

    private var cameraDevice: CameraDevice? = null
    private var captureSession: CameraCaptureSession? = null
    private var cameraThread: HandlerThread? = null
    private var cameraHandler: Handler? = null
    private var imageReader: ImageReader? = null
    private var previewSurface: Surface? = null
    private var isStreaming = false
    private var viewModel: CameraViewModel? = null
    private var frameCount = 0L
    private var cameraRetryCount = 0
    private val maxCameraRetries = 5
    private var errorFrameCount = 0
    private val maxErrorFrames = 10

    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())

    private val requestPermission = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) { /* camera will init via lifecycle */ }
        else {
            Toast.makeText(this, "Camera permission required", Toast.LENGTH_LONG).show()
            finish()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
            != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermission.launch(Manifest.permission.CAMERA)
        }

        cameraThread = HandlerThread("CameraThread").apply { start() }
        cameraHandler = Handler(cameraThread!!.looper)

        setContent {
            FieldVisionTheme {
                val vm: CameraViewModel = hiltViewModel()
                viewModel = vm
                val uiState by vm.uiState.collectAsState()

                // No-op: StreamServer auto-starts with camera and stops on ON_PAUSE/ON_DESTROY

                // Camera lifecycle
                val lifecycleOwner = LocalLifecycleOwner.current
                DisposableEffect(lifecycleOwner) {
                    val observer = LifecycleEventObserver { _, event ->
                        when (event) {
                            Lifecycle.Event.ON_RESUME -> {
                                Log.d("MainActivity", "ON_RESUME - preview=${previewSurface != null}, camera=${cameraDevice != null}")
                                if (hasCameraPermission() && previewSurface != null) initializeCamera()
                            }
                            Lifecycle.Event.ON_PAUSE -> {
                                Log.d("MainActivity", "ON_PAUSE - closing camera")
                                closeCamera()
                                if (isStreaming) stopStreamServer()
                            }
                            Lifecycle.Event.ON_DESTROY -> {
                                Log.d("MainActivity", "ON_DESTROY - cleanup all")
                                closeCamera()
                                streamServer.stop()
                                discoveryService.stop()
                                networkMonitor.stopMonitoring()
                                scope.cancel()
                            }
                            else -> {}
                        }
                    }
                    lifecycleOwner.lifecycle.addObserver(observer)
                    onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
                }

                Box(modifier = Modifier.fillMaxSize().background(Color.Black)) {
                    // Camera preview
                    AndroidView(
                        factory = { ctx ->
                            TextureView(ctx).apply {
                                surfaceTextureListener = object : TextureView.SurfaceTextureListener {
                                    override fun onSurfaceTextureAvailable(surfaceTexture: SurfaceTexture, w: Int, h: Int) {
                                        adjustPreviewRatio(this@apply, w, h)
                                        previewSurface = Surface(surfaceTexture)
                                        Log.i("MainActivity", "Preview surface available: ${w}x${h}")
                                        if (cameraDevice != null) {
                                            Log.i("MainActivity", "Camera already open, recreating session with preview surface")
                                            closeCamera()
                                            initializeCamera()
                                        } else {
                                            initializeCamera()
                                        }
                                    }
                                    override fun onSurfaceTextureSizeChanged(surfaceTexture: SurfaceTexture, w: Int, h: Int) {
                                        adjustPreviewRatio(this@apply, w, h)
                                    }
                                    override fun onSurfaceTextureDestroyed(surfaceTexture: SurfaceTexture): Boolean {
                                        previewSurface = null
                                        return true
                                    }
                                    override fun onSurfaceTextureUpdated(surfaceTexture: SurfaceTexture) {}
                                }
                            }
                        },
                        modifier = Modifier.fillMaxSize(),
                    )

                    // Compose UI overlay
                    CameraNavHost(viewModel = vm)
                }
            }
        }

        // Network monitoring
        networkMonitor.onConnectionChanged = { connection ->
            scope.launch {
                viewModel?.updateNetworkState(
                    wifiConnected = connection.type != com.fieldvision.camera.network.ConnectionType.UNKNOWN,
                    strength = connection.bandwidth.toInt(),
                    latency = connection.latency,
                )
            }
        }
        networkMonitor.startMonitoring()
        discoveryService.start()

        val phoneInfo = PhoneInfo(
            name = android.os.Build.MODEL,
            ip = getDeviceIp(),
            port = 8080,
            protocols = listOf("mjpeg"),
            resolutions = listOf("4k", "1080p", "720p"),
        )
        discoveryService.broadcastDiscovery(phoneInfo)
    }

    private fun adjustPreviewRatio(textureView: TextureView, viewWidth: Int, viewHeight: Int) {
        val previewRatio = 16.0f / 9.0f
        val viewRatio = viewWidth.toFloat() / viewHeight.toFloat()
        val matrix = Matrix()
        val scaleX: Float
        val scaleY: Float
        if (previewRatio > viewRatio) {
            scaleX = previewRatio / viewRatio
            scaleY = 1.0f
        } else {
            scaleX = 1.0f
            scaleY = viewRatio / previewRatio
        }
        matrix.setScale(scaleX, scaleY, viewWidth / 2.0f, viewHeight / 2.0f)
        textureView.setTransform(matrix)
    }

    private fun initializeCamera() {
        if (!hasCameraPermission()) {
            Log.w("MainActivity", "No camera permission")
            return
        }
        if (cameraDevice != null) {
            Log.d("MainActivity", "Camera already open, skipping")
            return
        }
        val manager = getSystemService(Context.CAMERA_SERVICE) as CameraManager
        try {
            val cameraId = getBackCameraId(manager) ?: run {
                Log.e("MainActivity", "No back camera found")
                return
            }
            Log.i("MainActivity", "Opening camera $cameraId")
            manager.openCamera(cameraId, object : CameraDevice.StateCallback() {
                override fun onOpened(camera: CameraDevice) {
                    cameraDevice = camera
                    cameraRetryCount = 0
                    errorFrameCount = 0
                    frameCount = 0
                    Log.i("MainActivity", "Camera opened successfully")
                    createCaptureSession()
                }
                override fun onDisconnected(camera: CameraDevice) {
                    Log.w("MainActivity", "Camera disconnected")
                    camera.close(); cameraDevice = null
                }
                override fun onError(camera: CameraDevice, error: Int) {
                    Log.w("MainActivity", "Camera error: $error (frameCount=$frameCount)")
                    camera.close()
                    cameraDevice = null
                    captureSession = null
                    val delay = if (error == 3) 1000L else (cameraRetryCount * 1000L).coerceAtMost(5000L)
                    if (cameraRetryCount < maxCameraRetries) {
                        cameraRetryCount++
                        Log.i("MainActivity", "Retrying camera in ${delay}ms (attempt $cameraRetryCount/$maxCameraRetries)")
                        scope.launch {
                            delay(delay)
                            if (hasCameraPermission() && previewSurface != null) {
                                initializeCamera()
                            }
                        }
                    } else {
                        Log.e("MainActivity", "Camera failed after $maxCameraRetries retries, will retry in 10s")
                        cameraRetryCount = 0
                        scope.launch {
                            delay(10000L)
                            if (hasCameraPermission() && previewSurface != null) {
                                initializeCamera()
                            }
                        }
                    }
                }
            }, cameraHandler)
        } catch (e: SecurityException) {
            Log.e("MainActivity", "Security exception opening camera: ${e.message}")
        } catch (e: CameraAccessException) {
            Log.e("MainActivity", "Camera access exception: ${e.message}")
        }
    }

    private fun createCaptureSession() {
        val camera = cameraDevice ?: run {
            Log.e("MainActivity", "createCaptureSession: cameraDevice is null")
            return
        }
        val streamWidth = 1280
        val streamHeight = 720

        imageReader = ImageReader.newInstance(streamWidth, streamHeight, android.graphics.ImageFormat.JPEG, 4)
        imageReader?.setOnImageAvailableListener({ reader ->
            val image = reader.acquireLatestImage() ?: return@setOnImageAvailableListener
            try {
                frameCount++
                if (isStreaming) {
                    val buffer = image.planes[0].buffer
                    val bytes = ByteArray(buffer.remaining())
                    buffer.get(bytes)
                    streamServer.sendFrameJpeg(bytes)
                    if (frameCount % 60 == 0L) {
                        Log.i("MainActivity", "Frame #$frameCount sent to StreamServer")
                    }
                }
            } catch (e: Exception) {
                Log.e("MainActivity", "Frame processing error: ${e.message}")
            } finally { image.close() }
        }, cameraHandler)

        val surfaces = mutableListOf<Surface>()
        previewSurface?.let {
            surfaces.add(it)
            Log.i("MainActivity", "Added preview surface to session")
        } ?: Log.w("MainActivity", "Preview surface is NULL - camera may not produce frames")
        imageReader?.surface?.let {
            surfaces.add(it)
            Log.i("MainActivity", "Added ImageReader surface to session")
        }

        if (surfaces.isEmpty()) {
            Log.e("MainActivity", "No surfaces available for capture session")
            return
        }

        try {
            camera.createCaptureSession(surfaces,
                object : CameraCaptureSession.StateCallback() {
                    override fun onConfigured(session: CameraCaptureSession) {
                        captureSession = session
                        Log.i("MainActivity", "Capture session configured with ${surfaces.size} surfaces, starting preview capture")
                        startPreviewCapture()
                    }
                    override fun onConfigureFailed(session: CameraCaptureSession) {
                        Log.e("MainActivity", "Capture session configuration FAILED")
                    }
                },
                cameraHandler
            )
        } catch (e: CameraAccessException) {
            Log.e("MainActivity", "Failed to create capture session: ${e.message}")
        }
    }

    private fun startPreviewCapture() {
        val camera = cameraDevice ?: return
        val session = captureSession ?: return
        try {
            val previewBuilder = camera.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW)
            previewSurface?.let {
                previewBuilder.addTarget(it)
                Log.i("MainActivity", "Added preview surface as capture target")
            }
            imageReader?.surface?.let { previewBuilder.addTarget(it) }
            previewBuilder.set(CaptureRequest.CONTROL_MODE, CaptureRequest.CONTROL_MODE_AUTO)
            previewBuilder.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_VIDEO)
            previewBuilder.set(CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE, android.util.Range(15, 30))

            val captureCallback = object : CameraCaptureSession.CaptureCallback() {
                override fun onCaptureFailed(session: CameraCaptureSession, request: CaptureRequest, failure: CaptureFailure) {
                    errorFrameCount++
                    if (errorFrameCount % 5 == 0) {
                        Log.w("MainActivity", "Capture failures: $errorFrameCount consecutive")
                    }
                    if (errorFrameCount >= maxErrorFrames) {
                        Log.e("MainActivity", "Too many capture failures ($errorFrameCount), reopening camera")
                        errorFrameCount = 0
                        scope.launch {
                            closeCamera()
                            delay(1000)
                            if (hasCameraPermission() && previewSurface != null) {
                                initializeCamera()
                            }
                        }
                    }
                }

                override fun onCaptureCompleted(session: CameraCaptureSession, request: CaptureRequest, result: TotalCaptureResult) {
                    errorFrameCount = 0
                }
            }

            session.setRepeatingRequest(previewBuilder.build(), captureCallback, cameraHandler)
            Log.i("MainActivity", "Preview capture started (repeating request)")

            if (!isStreaming) {
                startStreamServer()
            }
        } catch (e: CameraAccessException) {
            Log.e("MainActivity", "Failed to start preview capture: ${e.message}")
        }
    }

    private fun closeCamera() {
        try {
            Log.d("MainActivity", "Closing camera (session=${captureSession != null}, camera=${cameraDevice != null})")
            captureSession?.stopRepeating()
            captureSession?.close(); captureSession = null
            cameraDevice?.close(); cameraDevice = null
            imageReader?.close(); imageReader = null
        } catch (e: Exception) {
            Log.e("MainActivity", "Error closing camera: ${e.message}")
        }
    }

    private fun startStreamServer() {
        isStreaming = true
        frameCount = 0
        Log.i("MainActivity", "Starting StreamServer... (cameraDevice=${cameraDevice != null}, captureSession=${captureSession != null})")
        streamServer.start()
        Log.i("MainActivity", "StreamServer started, isRunning=${streamServer.isRunning}")
    }

    private fun stopStreamServer() {
        isStreaming = false
        Log.i("MainActivity", "Stopping StreamServer... (sent $frameCount frames)")
        streamServer.stop()
    }

    private fun getDeviceIp(): String {
        try {
            val interfaces = NetworkInterface.getNetworkInterfaces()
            while (interfaces.hasMoreElements()) {
                val networkInterface = interfaces.nextElement()
                val addresses = networkInterface.inetAddresses
                while (addresses.hasMoreElements()) {
                    val address = addresses.nextElement()
                    if (!address.isLoopbackAddress && address is Inet4Address) {
                        return address.hostAddress ?: "unknown"
                    }
                }
            }
        } catch (_: Exception) { }
        return "unknown"
    }

    private fun getBackCameraId(manager: CameraManager): String? {
        for (id in manager.cameraIdList) {
            val characteristics = manager.getCameraCharacteristics(id)
            if (characteristics.get(CameraCharacteristics.LENS_FACING) == CameraCharacteristics.LENS_FACING_BACK) {
                return id
            }
        }
        return null
    }

    private fun hasCameraPermission(): Boolean =
        ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED
}
