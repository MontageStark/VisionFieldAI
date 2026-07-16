package com.fieldvision.camera

import android.Manifest
import android.animation.ArgbEvaluator
import android.animation.ValueAnimator
import android.content.pm.PackageManager
import android.graphics.SurfaceTexture
import android.graphics.Matrix
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.view.Surface
import android.view.TextureView
import android.view.View
import android.view.WindowManager
import android.view.animation.OvershootInterpolator
import android.widget.Button
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.fieldvision.camera.camera.CameraConfig
import com.fieldvision.camera.camera.CameraEngine
import com.fieldvision.camera.camera.Resolution
import com.fieldvision.camera.discovery.DiscoveryService
import com.fieldvision.camera.discovery.PhoneInfo
import com.fieldvision.camera.network.NetworkMonitor
import com.fieldvision.camera.stream.StreamServer
import com.google.android.material.button.MaterialButton
import kotlinx.coroutines.*

class MainActivity : AppCompatActivity() {
    
    private lateinit var cameraEngine: CameraEngine
    private lateinit var streamServer: StreamServer
    private lateinit var discoveryService: DiscoveryService
    private lateinit var networkMonitor: NetworkMonitor
    
    private lateinit var previewView: TextureView
    private lateinit var statusText: TextView
    private lateinit var statusDot: ImageView
    private lateinit var liveIndicator: LinearLayout
    private lateinit var liveDot: View
    private lateinit var networkType: TextView
    private lateinit var networkBandwidth: TextView
    private lateinit var resolutionBadge: TextView
    private lateinit var btnStream: MaterialButton
    
    private lateinit var resolutionButtons: List<MaterialButton>
    
    private var isStreaming = false
    private var currentResolution = Resolution.UHD_4K
    
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // Keep screen on
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        
        // Make status bar transparent
        window.statusBarColor = getColor(R.color.background_dark)
        
        // Initialize views
        initializeViews()
        
        // Initialize services
        cameraEngine = CameraEngine(this)
        streamServer = StreamServer()
        discoveryService = DiscoveryService()
        networkMonitor = NetworkMonitor(this)
        
        // Setup listeners
        setupListeners()
        
        // Animate UI on start
        animateUIOnStart()
        
        // Check permissions
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
        resolutionBadge = findViewById(R.id.resolutionBadge)
        btnStream = findViewById(R.id.btnStream)
        
        // Collect resolution buttons
        resolutionButtons = listOf(
            findViewById(R.id.btn4K),
            findViewById(R.id.btn1080p),
            findViewById(R.id.btn720p),
            findViewById(R.id.btnAuto)
        )
    }
    
    override fun onResume() {
        super.onResume()
        cameraEngine.initialize(this)
    }
    
    override fun onPause() {
        super.onPause()
        if (isStreaming) {
            stopStreaming()
        }
        cameraEngine.closeCamera()
    }
    
    override fun onDestroy() {
        super.onDestroy()
        cameraEngine.shutdown()
        streamServer.stop()
        discoveryService.stop()
        networkMonitor.stopMonitoring()
        scope.cancel()
    }
    
    private fun setupListeners() {
        // Resolution buttons with animation
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
        
        // Stream button
        btnStream.setOnClickListener {
            if (isStreaming) {
                stopStreaming()
            } else {
                startStreaming()
            }
        }
        
        // TextureView listener
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
        
        // Discovery callback
        discoveryService.onLaptopFound = { laptop ->
            scope.launch {
                updateStatus("Found: ${laptop.name}", StatusType.CONNECTING)
                Toast.makeText(this@MainActivity, "Connected to ${laptop.name}", Toast.LENGTH_SHORT).show()
            }
        }
        
        // Network callback
        networkMonitor.onConnectionChanged = { connection ->
            scope.launch {
                networkType.text = connection.type
                networkBandwidth.text = "${connection.bandwidth.toInt()} Mbps available"
                
                // Animate bandwidth update
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
        
        val texture = previewView.surfaceTexture ?: run {
            updateStatus("Surface not ready", StatusType.CONNECTING)
            return
        }
        val surface = Surface(texture)
        val opened = cameraEngine.openCamera(surface, CameraConfig())
        
        if (opened) {
            updateStatus("Camera ready", StatusType.READY)
            
            // Start discovery
            discoveryService.start()
            networkMonitor.startMonitoring()
            
            // Broadcast discovery
            val phoneInfo = PhoneInfo(
                name = android.os.Build.MODEL,
                ip = discoveryService.getDeviceIp() ?: "unknown",
                port = 8080,
                protocols = listOf("mjpeg", "h264"),
                resolutions = listOf("4k", "1080p", "720p")
            )
            discoveryService.broadcastDiscovery(phoneInfo)
        } else {
            updateStatus("Camera unavailable", StatusType.ERROR)
        }
    }
    
    private fun startStreaming() {
        isStreaming = true
        
        // Animate button
        animateStreamButton(true)
        
        // Show live indicator
        liveIndicator.visibility = View.VISIBLE
        liveIndicator.alpha = 0f
        liveIndicator.animate()
            .alpha(1f)
            .setDuration(300)
            .start()
        
        // Pulse live dot
        startLiveDotAnimation()
        
        updateStatus("Streaming", StatusType.STREAMING)
        
        streamServer.start()
    }
    
    private fun stopStreaming() {
        isStreaming = false
        
        // Animate button
        animateStreamButton(false)
        
        // Hide live indicator
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
        
        // Animate badge update
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
        
        val drawable = statusDot.background as? GradientDrawable
        drawable?.setColor(dotColor)
    }
    
    // Animations
    private fun animateUIOnStart() {
        val controlPanel = findViewById<LinearLayout>(R.id.controlPanel)
        val statusCard = findViewById<com.google.android.material.card.MaterialCardView>(R.id.statusCard)
        
        // Fade in and slide up control panel
        controlPanel.alpha = 0f
        controlPanel.translationY = 100f
        controlPanel.animate()
            .alpha(1f)
            .translationY(0f)
            .setDuration(600)
            .setInterpolator(OvershootInterpolator(1.2f))
            .start()
        
        // Fade in status card
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
        val colorFrom = if (starting) getColor(R.color.primary) else getColor(R.color.status_error)
        val colorTo = if (starting) getColor(R.color.status_error) else getColor(R.color.primary)
        
        val colorAnimation = ValueAnimator.ofObject(ArgbEvaluator(), colorFrom, colorTo)
        colorAnimation.duration = 300
        colorAnimation.addUpdateListener { animator ->
            btnStream.backgroundTintList = 
                ContextCompat.getColorStateList(this, R.color.primary)
        }
        colorAnimation.start()
        
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
        return ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED
    }
    
    private fun requestCameraPermission() {
        ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.CAMERA), CAMERA_PERMISSION_CODE)
    }
    
    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        when (requestCode) {
            CAMERA_PERMISSION_CODE -> {
                if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
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
