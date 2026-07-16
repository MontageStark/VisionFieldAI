package com.fieldvision.camera.stream

import android.util.Log
import kotlinx.coroutines.*
import java.net.ServerSocket
import java.net.Socket

class StreamServer(private val port: Int = 8080) {
    
    private var serverSocket: ServerSocket? = null
    private var serverJob: Job? = null
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    
    @Volatile
    var isRunning = false
        private set
    
    var onClientConnected: (() -> Unit)? = null
    var onClientDisconnected: (() -> Unit)? = null
    
    fun start() {
        if (isRunning) return
        
        serverJob = scope.launch {
            try {
                serverSocket = ServerSocket(port)
                isRunning = true
                Log.d(TAG, "Stream server started on port $port")
                
                while (isActive) {
                    val clientSocket = serverSocket?.accept() ?: break
                    handleClient(clientSocket)
                }
            } catch (e: Exception) {
                Log.e(TAG, "Server error: ${e.message}")
            }
        }
    }
    
    fun stop() {
        isRunning = false
        serverJob?.cancel()
        try {
            serverSocket?.close()
        } catch (e: Exception) {
            // Ignore
        }
        scope.cancel()
    }
    
    private fun handleClient(socket: Socket) {
        scope.launch {
            try {
                val output = socket.getOutputStream()
                val mjpegStream = MjpegStream(output)
                
                onClientConnected?.invoke()
                
                // Keep stream alive
                while (socket.isConnected && !socket.isClosed) {
                    delay(100) // Check connection
                }
                
                mjpegStream.stop()
                onClientDisconnected?.invoke()
            } catch (e: Exception) {
                Log.e(TAG, "Client handler error: ${e.message}")
            }
        }
    }
    
    companion object {
        private const val TAG = "StreamServer"
    }
}
