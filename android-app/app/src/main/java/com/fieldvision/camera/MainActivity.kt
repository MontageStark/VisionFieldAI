package com.fieldvision.camera

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.SurfaceTexture
import android.os.Bundle
import android.view.TextureView
import android.view.WindowManager
import android.widget.Button
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
import kotlinx.coroutines.*

class MainActivity : AppCompatActivity() {
    
    private lateinit var cameraEngine: CameraEngine
    private lateinit var streamServer: StreamServer
    private lateinit var discoveryService: DiscoveryService
    private lateinit var networkMonitor: NetworkMonitor
    
    private lateinit var previewView: TextureView
    private lateinit var statusText: TextView
    private lateinit var btnStream: Button
    
    private var isStreaming = false
    private var currentResolution = Resolution.UHD_4K
    
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // Keep screen on
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        
        // Initialize views
        previewView = findViewById(R.id.previewView)
        statusText = findViewById(R.id.statusText)
        btnStream = findViewById(R.id.btnStream)
        
        // Initialize services
        cameraEngine = CameraEngine(this)
        streamServer = StreamServer()
        discoveryService = DiscoveryService()
        networkMonitor = NetworkMonitor(this)
        
        // Setup listeners
        setupListeners()
        
        // Check permissions
        if (hasCameraPermission()) {
            initializeCamera()
        } else {
            requestCameraPermission()
        }
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
        // Resolution buttons
        findViewById<Button>(R.id.btn4K).setOnClickListener { setResolution(Resolution.UHD_4K) }
        findViewById<Button>(R.id.btn1080p).setOnClickListener { setResolution(Resolution.FHD_1080P) }
        findViewById<Button>(R.id.btn720p).setOnClickListener { setResolution(Resolution.HD_720P) }
        findViewById<Button>(R.id.btnAuto).setOnClickListener { setResolution(null) }
        
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
                initializeCamera()
            }
            
            override fun onSurfaceTextureSizeChanged(surface: SurfaceTexture, width: Int, height: Int) {}
            
            override fun onSurfaceTextureDestroyed(surface: SurfaceTexture): Boolean = true
            
            override fun onSurfaceTextureUpdated(surface: SurfaceTexture) {}
        }
        
        // Discovery callback
        discoveryService.onLaptopFound = { laptop ->
            scope.launch {
                statusText.text = "Found: ${laptop.name} (${laptop.ip})"
                Toast.makeText(this@MainActivity, "Found ${laptop.name}", Toast.LENGTH_SHORT).show()
            }
        }
        
        // Network callback
        networkMonitor.onConnectionChanged = { connection ->
            scope.launch {
                statusText.text = "Network: ${connection.type} | ${connection.bandwidth.toInt()} Mbps"
            }
        }
    }
    
    private fun initializeCamera() {
        if (previewView.isAvailable) {
            val surface = Surface(previewView.surfaceTexture!!)
            cameraEngine.openCamera(surface, CameraConfig())
            
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
        }
    }
    
    private fun startStreaming() {
        isStreaming = true
        btnStream.text = "Stop Streaming"
        statusText.text = "Streaming started"
        
        streamServer.start()
    }
    
    private fun stopStreaming() {
        isStreaming = false
        btnStream.text = "Start Streaming"
        statusText.text = "Streaming stopped"
        
        streamServer.stop()
    }
    
    private fun setResolution(resolution: Resolution?) {
        currentResolution = resolution ?: networkMonitor.getRecommendedResolution()
        statusText.text = "Resolution: ${currentResolution.width}x${currentResolution.height}"
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
                    Toast.makeText(this, "Camera permission required", Toast.LENGTH_LONG).show()
                    finish()
                }
            }
        }
    }
    
    companion object {
        private const val CAMERA_PERMISSION_CODE = 100
    }
}
