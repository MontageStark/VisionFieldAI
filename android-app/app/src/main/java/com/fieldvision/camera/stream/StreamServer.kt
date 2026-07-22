package com.fieldvision.camera.stream

import android.util.Log
import kotlinx.coroutines.*
import java.net.ServerSocket
import java.net.Socket

class StreamServer(private val port: Int = 8080) {

    private var serverSocket: ServerSocket? = null
    private var serverJob: Job? = null
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    private val connectedClients = mutableListOf<Socket>()
    private val clientLock = Any()

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
        try { serverSocket?.close() } catch (_: Exception) { }

        synchronized(clientLock) {
            connectedClients.forEach { client ->
                try { client.close() } catch (_: Exception) { }
            }
            connectedClients.clear()
        }

        scope.cancel()
    }

    fun sendFrameJpeg(jpegData: ByteArray) {
        if (!isRunning) return

        val clients: List<Socket>
        synchronized(clientLock) {
            connectedClients.removeAll { it.isClosed || it.isOutputShutdown }
            clients = connectedClients.toList()
        }
        if (clients.isEmpty()) return

        val frameHeader = "--frame\r\n" +
                "Content-Type: image/jpeg\r\n" +
                "Content-Length: ${jpegData.size}\r\n\r\n"
        val frameBytes = frameHeader.toByteArray() + jpegData + "\r\n".toByteArray()

        val deadClients = mutableListOf<Socket>()
        for (client in clients) {
            try {
                if (!client.isClosed) {
                    client.getOutputStream().write(frameBytes)
                    client.getOutputStream().flush()
                } else {
                    deadClients.add(client)
                }
            } catch (_: Exception) {
                deadClients.add(client)
            }
        }

        if (deadClients.isNotEmpty()) {
            synchronized(clientLock) {
                connectedClients.removeAll(deadClients)
            }
            deadClients.forEach { try { it.close() } catch (_: Exception) { } }
        }
    }

    private fun handleClient(socket: Socket) {
        scope.launch {
            try {
                val output = socket.getOutputStream()

                val header = "HTTP/1.1 200 OK\r\n" +
                        "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n" +
                        "Cache-Control: no-cache\r\n" +
                        "Access-Control-Allow-Origin: *\r\n" +
                        "Connection: keep-alive\r\n\r\n"
                output.write(header.toByteArray())
                output.flush()
                Log.i(TAG, "Client connected, headers sent: ${socket.inetAddress}")

                synchronized(clientLock) {
                    connectedClients.add(socket)
                }

                onClientConnected?.invoke()

                // Keep client alive until disconnected or error
                try {
                    while (socket.isConnected && !socket.isClosed) {
                        Thread.sleep(1000)
                        // Check if still connected by peeking at input
                        if (socket.getInputStream().available() > 0) {
                            val buf = ByteArray(1)
                            val read = socket.getInputStream().read(buf)
                            if (read == -1) break
                        }
                    }
                } catch (_: Exception) { }

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
