package com.fieldvision.camera

import android.animation.ArgbEvaluator
import android.animation.ValueAnimator
import android.content.Context
import android.graphics.Bitmap
import android.graphics.ImageFormat
import android.graphics.Matrix
import android.graphics.SurfaceTexture
import android.graphics.YuvImage
import android.hardware.camera2.*
import android.media.ImageReader
import android.os.Bundle
import android.os.Handler
import android.os.HandlerThread
import android.view.Surface
import android.view.TextureView
import android.view.View
import android.view.WindowManager
import android.view.animation.OvershootInterpolator
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.fieldvision.camera.camera.CameraConfig
import com.fieldvision.camera.camera.Resolution
import com.fieldvision.camera.discovery.DiscoveryService
import com.fieldvision.camera.discovery.PhoneInfo
import com.fieldvision.camera.network.NetworkMonitor
import com.fieldvision.camera.stream.StreamServer
import com.google.android.material.button.MaterialButton
import com.google.android.material.card.MaterialCardView
import kotlinx.coroutines.*
import java.io.ByteArrayOutputStream
import java.net.Inet4Address
import java.net.NetworkInterface

class MainActivity : AppCompatActivity() {
    
    private var cameraDevice: CameraDevice? = null
    private var captureSession: CameraCaptureSession? = null
    private var cameraThread: HandlerThread? = null
    private var cameraHandler: Handler? = null
    private var imageReader: ImageReader? = null
    
    private lateinit var streamServer: StreamServer
    private lateinit var discoveryService: DiscoveryService
    private lateinit var networkMonitor: NetworkMonitor
    
    private lateinit var previewView: TextureView
    private lateinit var statusText: TextView
    private lateinit var statusDot: View
    private lateinit var liveIndicator: LinearLayout
    private lateinit var liveDot: View
    private lateinit var networkType: TextView
    private lateinit var networkBandwidth: TextView
    private lateinit var ipAddress: TextView
    private lateinit var resolutionBadge: TextView
    private lateinit var btnStream: MaterialButton
    
    private lateinit var resolutionButtons: List<MaterialButton>
    
    private var isStreaming = false
    private var currentResolution = Resolution.UHD_4K
    
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        window.statusBarColor = getColor(R.color.background_dark)
        
        initializeViews()
        
        streamServer = StreamServer()
        discoveryService = DiscoveryService()
        networkMonitor = NetworkMonitor(this)
        
        setupListeners()
        animateUIOnStart()
        displayIpAddress()
        
        cameraThread = HandlerThread("CameraThread").apply { start() }
        cameraHandler = Handler(cameraThread!!.looper)
        
        if (hasCameraPermission()) {
            initializeCamera()
        } else {
            requestCameraPermission()
        }
    }
    
    private fun initializeViews() {
        previewView = findViewById(R.id.previewView)
        statusText = findViewById(R.id.statusText)
        statusDot = findViewById(R.id.statusDot)
        liveIndicator = findViewById(R.id.liveIndicator)
        liveDot = findViewById(R.id.liveDot)
        networkType = findViewById(R.id.networkType)
        networkBandwidth = findViewById(R.id.networkBandwidth)
        ipAddress = findViewById(R.id.ipAddress)
        resolutionBadge = findViewById(R.id.resolutionBadge)
        btnStream = findViewById(R.id.btnStream)
        
        resolutionButtons = listOf(
            findViewById(R.id.btn4K),
            findViewById(R.id.btn1080p),
            findViewById(R.id.btn720p),
            findViewById(R.id.btnAuto)
        )
    }
    
    private fun displayIpAddress() {
        try {
            val ip = getDeviceIp()
            ipAddress.text = "IP: $ip"
            ipAddress.visibility = View.VISIBLE
        } catch (e: Exception) {
            ipAddress.text = "IP: unknown"
        }
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
        } catch (e: Exception) {
            // Ignore
        }
        return "unknown"
    }
    
    override fun onResume() {
        super.onResume()
    }
    
    override fun onPause() {
        super.onPause()
        if (isStreaming) {
            stopStreaming()
        }
        closeCamera()
    }
    
    override fun onDestroy() {
        super.onDestroy()
        closeCamera()
        streamServer.stop()
        discoveryService.stop()
        networkMonitor.stopMonitoring()
        cameraThread?.quitSafely()
        scope.cancel()
    }
    
    private fun setupListeners() {
        resolutionButtons.forEachIndexed { index, button ->
            button.setOnClickListener {
                val resolution = when (index) {
                    0 -> Resolution.UHD_4K
                    1 -> Resolution.FHD_1080P
                    2 -> Resolution.HD_720P
                    else -> null
                }
                setResolution(resolution)
                animateResolutionSelection(button)
            }
        }
        
        btnStream.setOnClickListener {
            if (isStreaming) {
                stopStreaming()
            } else {
                startStreaming()
            }
        }
        
        previewView.surfaceTextureListener = object : TextureView.SurfaceTextureListener {
            override fun onSurfaceTextureAvailable(surface: SurfaceTexture, width: Int, height: Int) {
                adjustPreviewRatio(width, height)
                initializeCamera()
            }
            
            override fun onSurfaceTextureSizeChanged(surface: SurfaceTexture, width: Int, height: Int) {
                adjustPreviewRatio(width, height)
            }
            
            override fun onSurfaceTextureDestroyed(surface: SurfaceTexture): Boolean = true
            override fun onSurfaceTextureUpdated(surface: SurfaceTexture) {}
        }
        
        discoveryService.onLaptopFound = { laptop ->
            scope.launch {
                updateStatus("Found: ${laptop.name}", StatusType.CONNECTING)
                Toast.makeText(this@MainActivity, "Connected to ${laptop.name}", Toast.LENGTH_SHORT).show()
            }
        }
        
        networkMonitor.onConnectionChanged = { connection ->
            scope.launch {
                networkType.text = connection.type.name
                networkBandwidth.text = "${connection.bandwidth.toInt()} Mbps"
                animateBandwidthUpdate()
            }
        }
    }
    
    private fun adjustPreviewRatio(viewWidth: Int, viewHeight: Int) {
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
        previewView.setTransform(matrix)
    }
    
    private fun initializeCamera() {
        if (!hasCameraPermission()) {
            updateStatus("Camera permission required", StatusType.ERROR)
            return
        }
        if (!previewView.isAvailable) {
            updateStatus("Initializing preview...", StatusType.CONNECTING)
            return
        }
        
        val manager = getSystemService(Context.CAMERA_SERVICE) as CameraManager
        
        try {
            val cameraId = getBackCameraId(manager) ?: run {
                updateStatus("No camera found", StatusType.ERROR)
                return
            }
            
            manager.openCamera(cameraId, object : CameraDevice.StateCallback() {
                override fun onOpened(camera: CameraDevice) {
                    cameraDevice = camera
                    createCaptureSession()
                }
                
                override fun onDisconnected(camera: CameraDevice) {
                    camera.close()
                    cameraDevice = null
                    runOnUiThread {
                        updateStatus("Camera disconnected", StatusType.ERROR)
                    }
                }
                
                override fun onError(camera: CameraDevice, error: Int) {
                    camera.close()
                    cameraDevice = null
                    runOnUiThread {
                        updateStatus("Camera error: $error", StatusType.ERROR)
                    }
                }
            }, cameraHandler)
        } catch (e: SecurityException) {
            updateStatus("Camera permission denied", StatusType.ERROR)
        } catch (e: CameraAccessException) {
            updateStatus("Camera access error", StatusType.ERROR)
        }
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
    
    private fun createCaptureSession() {
        val camera = cameraDevice ?: return
        
        val texture = previewView.surfaceTexture ?: return
        texture.setDefaultBufferSize(1920, 1080)
        val previewSurface = Surface(texture)
        
        // Full HD streaming
        val streamWidth = 1920
        val streamHeight = 1080
        
        // Use JPEG capture - camera ISP handles color conversion correctly
        imageReader = ImageReader.newInstance(streamWidth, streamHeight, ImageFormat.JPEG, 2)
        imageReader?.setOnImageAvailableListener({ reader ->
            val image = reader.acquireLatestImage() ?: return@setOnImageAvailableListener
            try {
                if (isStreaming) {
                    val buffer = image.planes[0].buffer
                    val bytes = ByteArray(buffer.remaining())
                    buffer.get(bytes)
                    
                    val bitmap = android.graphics.BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
                    if (bitmap != null) {
                        streamServer.sendFrame(bitmap)
                        bitmap.recycle()
                    }
                }
            } catch (e: Exception) {
                // Ignore frame errors
            } finally {
                image.close()
            }
        }, cameraHandler)
        
        val surfaces = mutableListOf(previewSurface)
        imageReader?.surface?.let { surfaces.add(it) }
        
        try {
            camera.createCaptureSession(
                surfaces,
                object : CameraCaptureSession.StateCallback() {
                    override fun onConfigured(session: CameraCaptureSession) {
                        captureSession = session
                        startStreamingCapture()
                        runOnUiThread {
                            updateStatus("Camera ready", StatusType.READY)
                        }
                        
                        discoveryService.start()
                        networkMonitor.startMonitoring()
                        
                        val phoneInfo = PhoneInfo(
                            name = android.os.Build.MODEL,
                            ip = getDeviceIp(),
                            port = 8080,
                            protocols = listOf("mjpeg"),
                            resolutions = listOf("4k", "1080p", "720p")
                        )
                        discoveryService.broadcastDiscovery(phoneInfo)
                    }
                    
                    override fun onConfigureFailed(session: CameraCaptureSession) {
                        runOnUiThread {
                            updateStatus("Session config failed", StatusType.ERROR)
                        }
                    }
                },
                cameraHandler
            )
        } catch (e: CameraAccessException) {
            runOnUiThread {
                updateStatus("Session error", StatusType.ERROR)
            }
        }
    }
    
    private fun startStreamingCapture() {
        val camera = cameraDevice ?: return
        val session = captureSession ?: return
        
        val streamWidth = 1920
        val streamHeight = 1080
        
        try {
            // Preview request at full resolution
            val previewBuilder = camera.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW)
            previewView.surfaceTexture?.let { texture ->
                texture.setDefaultBufferSize(streamWidth, streamHeight)
                previewBuilder.addTarget(Surface(texture))
            }
            previewBuilder.set(CaptureRequest.CONTROL_MODE, CaptureRequest.CONTROL_MODE_AUTO)
            
            // JPEG capture request for streaming
            val streamBuilder = camera.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE)
            imageReader?.surface?.let { streamBuilder.addTarget(it) }
            streamBuilder.set(CaptureRequest.CONTROL_MODE, CaptureRequest.CONTROL_MODE_AUTO)
            streamBuilder.set(CaptureRequest.JPEG_QUALITY, 70.toByte())
            
            // Set up repeating preview
            session.setRepeatingRequest(previewBuilder.build(), null, cameraHandler)
            
            val captureCallback = object : CameraCaptureSession.CaptureCallback() {
                override fun onCaptureCompleted(
                    session: CameraCaptureSession,
                    request: CaptureRequest,
                    result: TotalCaptureResult
                ) {
                    // Frame captured - ImageReader callback handles it
                }
            }
            
            // Capture at ~15fps for 1080p JPEG streaming (balance of quality and performance)
            scope.launch {
                while (isActive && captureSession != null) {
                    try {
                        session.capture(streamBuilder.build(), captureCallback, cameraHandler)
                    } catch (e: Exception) {
                        // Ignore capture errors
                    }
                    delay(67) // ~15fps
                }
            }
        } catch (e: CameraAccessException) {
            // Ignore
        }
    }
    
    private fun processYuvFrame(image: android.media.Image, width: Int, height: Int) {
        try {
            val yPlane = image.planes[0]
            val uPlane = image.planes[1]
            val vPlane = image.planes[2]
            
            val yRowStride = yPlane.rowStride
            val uvRowStride = uPlane.rowStride
            
            val ySize = width * height
            val nv21 = ByteArray(ySize + (ySize / 2))
            
            // Copy Y plane row by row (handle stride gaps)
            val yBuffer = yPlane.buffer
            var yPos = 0
            for (i in 0 until height) {
                val rowStart = i * yRowStride
                yBuffer.position(rowStart)
                val rowEnd = rowStart + width
                while (yBuffer.position() < rowEnd && yBuffer.hasRemaining()) {
                    nv21[yPos++] = yBuffer.get()
                }
            }
            
            // Build interleaved VU from U and V planes
            val yHalf = height / 2
            val uvWidth = width / 2
            val uBuffer = uPlane.buffer
            val vBuffer = vPlane.buffer
            
            var uvIndex = ySize
            for (i in 0 until yHalf) {
                val uvRowStart = i * uvRowStride
                for (j in 0 until uvWidth) {
                    val uPos = uvRowStart + j * 2 // U at even offset
                    val vPos = uvRowStart + j * 2 + 1 // V at odd offset
                    
                    // NV21: V first, then U
                    if (vPos < vBuffer.capacity()) {
                        nv21[uvIndex++] = vBuffer.get(vPos)
                    }
                    if (uPos < uBuffer.capacity()) {
                        nv21[uvIndex++] = uBuffer.get(uPos)
                    }
                }
            }
            
            // Convert NV21 to JPEG
            val yuvImage = YuvImage(nv21, ImageFormat.NV21, width, height, null)
            val out = ByteArrayOutputStream()
            yuvImage.compressToJpeg(android.graphics.Rect(0, 0, width, height), 50, out)
            val imageBytes = out.toByteArray()
            
            // Convert to bitmap
            val bitmap = android.graphics.BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.size)
            if (bitmap != null) {
                streamServer.sendFrame(bitmap)
                bitmap.recycle()
            }
        } catch (e: Exception) {
            // Ignore conversion errors
        }
    }
    
    private fun closeCamera() {
        try {
            captureSession?.close()
            captureSession = null
            cameraDevice?.close()
            cameraDevice = null
            imageReader?.close()
            imageReader = null
        } catch (e: Exception) {
            // Ignore
        }
    }
    
    private fun startStreaming() {
        isStreaming = true
        
        animateStreamButton(true)
        
        liveIndicator.visibility = View.VISIBLE
        liveIndicator.alpha = 0f
        liveIndicator.animate()
            .alpha(1f)
            .setDuration(300)
            .start()
        
        startLiveDotAnimation()
        updateStatus("Streaming on port 8080", StatusType.STREAMING)
        
        streamServer.start()
    }
    
    private fun stopStreaming() {
        isStreaming = false
        
        animateStreamButton(false)
        
        liveIndicator.animate()
            .alpha(0f)
            .setDuration(200)
            .withEndAction {
                liveIndicator.visibility = View.GONE
            }
            .start()
        
        updateStatus("Stream stopped", StatusType.READY)
        
        streamServer.stop()
    }
    
    private fun setResolution(resolution: Resolution?) {
        currentResolution = resolution ?: networkMonitor.getRecommendedResolution()
        resolutionBadge.text = when (currentResolution) {
            Resolution.UHD_4K -> "4K"
            Resolution.FHD_1080P -> "1080p"
            Resolution.HD_720P -> "720p"
            else -> "AUTO"
        }
        
        resolutionBadge.animate()
            .scaleX(1.2f)
            .scaleY(1.2f)
            .setDuration(150)
            .withEndAction {
                resolutionBadge.animate()
                    .scaleX(1f)
                    .scaleY(1f)
                    .setDuration(150)
                    .start()
            }
            .start()
    }
    
    private enum class StatusType {
        READY, STREAMING, CONNECTING, ERROR
    }
    
    private fun updateStatus(message: String, type: StatusType) {
        statusText.text = message
        
        val dotColor = when (type) {
            StatusType.READY -> getColor(R.color.status_idle)
            StatusType.STREAMING -> getColor(R.color.status_streaming)
            StatusType.CONNECTING -> getColor(R.color.status_connecting)
            StatusType.ERROR -> getColor(R.color.status_error)
        }
        
        val drawable = android.graphics.drawable.GradientDrawable().apply {
            shape = android.graphics.drawable.GradientDrawable.OVAL
            setColor(dotColor)
        }
        statusDot.background = drawable
    }
    
    // Animations
    private fun animateUIOnStart() {
        val controlPanel = findViewById<LinearLayout>(R.id.controlPanel)
        val statusCard = findViewById<MaterialCardView>(R.id.statusCard)
        
        controlPanel.alpha = 0f
        controlPanel.translationY = 100f
        controlPanel.animate()
            .alpha(1f)
            .translationY(0f)
            .setDuration(600)
            .setInterpolator(OvershootInterpolator(1.2f))
            .start()
        
        statusCard.alpha = 0f
        statusCard.translationX = -50f
        statusCard.animate()
            .alpha(1f)
            .translationX(0f)
            .setDuration(500)
            .setStartDelay(200)
            .start()
    }
    
    private fun animateResolutionSelection(selectedButton: MaterialButton) {
        resolutionButtons.forEach { button ->
            if (button == selectedButton) {
                button.backgroundTintList = ContextCompat.getColorStateList(this, R.color.primary)
                button.setTextColor(getColor(R.color.button_text_active))
                button.animate()
                    .scaleX(1.05f)
                    .scaleY(1.05f)
                    .setDuration(200)
                    .withEndAction {
                        button.animate()
                            .scaleX(1f)
                            .scaleY(1f)
                            .setDuration(150)
                            .start()
                    }
                    .start()
            } else {
                button.backgroundTintList = ContextCompat.getColorStateList(this, R.color.button_inactive)
                button.setTextColor(getColor(R.color.button_text_inactive))
            }
        }
    }
    
    private fun animateStreamButton(starting: Boolean) {
        btnStream.text = if (starting) "Stop Streaming" else "Start Streaming"
        btnStream.animate()
            .scaleX(0.95f)
            .scaleY(0.95f)
            .setDuration(100)
            .withEndAction {
                btnStream.animate()
                    .scaleX(1f)
                    .scaleY(1f)
                    .setDuration(100)
                    .start()
            }
            .start()
    }
    
    private fun startLiveDotAnimation() {
        scope.launch {
            while (isStreaming) {
                liveDot.animate()
                    .alpha(0.3f)
                    .setDuration(500)
                    .withEndAction {
                        liveDot.animate()
                            .alpha(1f)
                            .setDuration(500)
                            .start()
                    }
                    .start()
                delay(1000)
            }
        }
    }
    
    private fun animateBandwidthUpdate() {
        networkBandwidth.animate()
            .alpha(0.5f)
            .setDuration(100)
            .withEndAction {
                networkBandwidth.animate()
                    .alpha(1f)
                    .setDuration(100)
                    .start()
            }
            .start()
    }
    
    private fun hasCameraPermission(): Boolean {
        return ContextCompat.checkSelfPermission(this, android.Manifest.permission.CAMERA) == android.content.pm.PackageManager.PERMISSION_GRANTED
    }
    
    private fun requestCameraPermission() {
        androidx.core.app.ActivityCompat.requestPermissions(this, arrayOf(android.Manifest.permission.CAMERA), CAMERA_PERMISSION_CODE)
    }
    
    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        when (requestCode) {
            CAMERA_PERMISSION_CODE -> {
                if (grantResults.isNotEmpty() && grantResults[0] == android.content.pm.PackageManager.PERMISSION_GRANTED) {
                    initializeCamera()
                } else {
                    Toast.makeText(this, "Camera permission is required", Toast.LENGTH_LONG).show()
                    finish()
                }
            }
        }
    }
    
    companion object {
        private const val CAMERA_PERMISSION_CODE = 100
    }
}
