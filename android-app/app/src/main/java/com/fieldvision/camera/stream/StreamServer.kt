package com.fieldvision.camera.stream

import android.graphics.Bitmap
import android.util.Log
import kotlinx.coroutines.*
import java.io.ByteArrayOutputStream
import java.net.ServerSocket
import java.net.Socket

class StreamServer(private val port: Int = 8080) {
    
    private var serverSocket: ServerSocket? = null
    private var serverJob: Job? = null
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    
    private val connectedClients = mutableListOf<Socket>()
    private val clientLock = Object()
    
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
                Log.i(TAG, "Stream server started on port $port")
                
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
        
        synchronized(clientLock) {
            connectedClients.forEach { client ->
                try { client.close() } catch (e: Exception) { }
            }
            connectedClients.clear()
        }
        
        scope.cancel()
    }
    
    fun sendFrame(bitmap: Bitmap) {
        if (!isRunning || connectedClients.isEmpty()) return
        
        // Convert bitmap to JPEG
        val stream = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, 80, stream)
        val jpegData = stream.toByteArray()
        
        val frameHeader = "--frame\r\n" +
                "Content-Type: image/jpeg\r\n" +
                "Content-Length: ${jpegData.size}\r\n\r\n"
        val frameBytes = frameHeader.toByteArray() + jpegData + "\r\n".toByteArray()
        
        synchronized(clientLock) {
            val iterator = connectedClients.iterator()
            while (iterator.hasNext()) {
                val client = iterator.next()
                try {
                    if (!client.isClosed) {
                        client.getOutputStream().write(frameBytes)
                        client.getOutputStream().flush()
                    } else {
                        iterator.remove()
                    }
                } catch (e: Exception) {
                    iterator.remove()
                    try { client.close() } catch (ex: Exception) { }
                }
            }
        }
    }
    
    private fun handleClient(socket: Socket) {
        scope.launch {
            try {
                val output = socket.getOutputStream()
                
                // Send HTTP response header
                val header = "HTTP/1.1 200 OK\r\n" +
                        "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n" +
                        "Cache-Control: no-cache\r\n" +
                        "Connection: close\r\n\r\n"
                output.write(header.toByteArray())
                output.flush()
                
                synchronized(clientLock) {
                    connectedClients.add(socket)
                }
                
                onClientConnected?.invoke()
                Log.i(TAG, "Client connected: ${socket.inetAddress}")
                
                // Keep connection alive until client disconnects
                while (socket.isConnected && !socket.isClosed) {
                    try {
                        val buffer = ByteArray(1)
                        val read = socket.getInputStream().read(buffer)
                        if (read == -1) break
                    } catch (e: Exception) {
                        break
                    }
                }
                
                synchronized(clientLock) {
                    connectedClients.remove(socket)
                }
                
                onClientDisconnected?.invoke()
                Log.d(TAG, "Client disconnected: ${socket.inetAddress}")
            } catch (e: Exception) {
                Log.e(TAG, "Client handler error: ${e.message}")
            }
        }
    }
    
    companion object {
        private const val TAG = "StreamServer"
    }
}
