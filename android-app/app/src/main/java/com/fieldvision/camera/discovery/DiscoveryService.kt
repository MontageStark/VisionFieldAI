package com.fieldvision.camera.discovery

import android.util.Log
import kotlinx.coroutines.*
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.net.NetworkInterface

class DiscoveryService(private val port: Int = 9999) {
    
    private var socket: DatagramSocket? = null
    private var discoveryJob: Job? = null
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    
    @Volatile
    var isRunning = false
        private set
    
    var onLaptopFound: ((LaptopInfo) -> Unit)? = null
    
    fun start() {
        if (isRunning) return
        
        discoveryJob = scope.launch {
            try {
                socket = DatagramSocket(null)
                socket?.reuseAddress = true
                socket?.bind(java.net.InetSocketAddress(port))
                isRunning = true
                
                Log.d(TAG, "Discovery service started on port $port")
                
                // Listen for responses
                while (isActive) {
                    val buffer = ByteArray(1024)
                    val packet = DatagramPacket(buffer, buffer.size)
                    socket?.receive(packet)
                    
                    val message = String(packet.data, 0, packet.length)
                    handleDiscoveryResponse(message, packet.address)
                }
            } catch (e: Exception) {
                Log.e(TAG, "Discovery error: ${e.message}")
            }
        }
    }
    
    fun stop() {
        isRunning = false
        discoveryJob?.cancel()
        socket?.close()
        scope.cancel()
    }
    
    fun broadcastDiscovery(phoneInfo: PhoneInfo) {
        scope.launch {
            try {
                val message = DiscoveryMessage(
                    type = "discover",
                    device = phoneInfo.name,
                    ip = phoneInfo.ip,
                    ports = listOf(phoneInfo.port),
                    protocols = phoneInfo.protocols,
                    resolutions = phoneInfo.resolutions
                ).toJson()
                
                val buffer = message.toByteArray()
                val packet = DatagramPacket(
                    buffer,
                    buffer.size,
                    InetAddress.getByName("255.255.255.255"),
                    port
                )
                
                socket?.send(packet)
                Log.d(TAG, "Discovery broadcast sent")
            } catch (e: Exception) {
                Log.e(TAG, "Broadcast error: ${e.message}")
            }
        }
    }
    
    private fun handleDiscoveryResponse(message: String, address: InetAddress) {
        try {
            val response = DiscoveryMessage.fromJson(message)
            if (response.type == "found") {
                val laptop = LaptopInfo(
                    name = response.device,
                    ip = address.hostAddress ?: response.ip,
                    apiPort = response.ports.firstOrNull() ?: 8001
                )
                onLaptopFound?.invoke(laptop)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Invalid discovery response: ${e.message}")
        }
    }
    
    fun getDeviceIp(): String? {
        try {
            val interfaces = NetworkInterface.getNetworkInterfaces()
            while (interfaces.hasMoreElements()) {
                val networkInterface = interfaces.nextElement()
                if (networkInterface.isLoopback || !networkInterface.isUp) continue
                
                val addresses = networkInterface.inetAddresses
                while (addresses.hasMoreElements()) {
                    val address = addresses.nextElement()
                    if (!address.isLoopbackAddress && address is java.net.Inet4Address) {
                        return address.hostAddress
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error getting IP: ${e.message}")
        }
        return null
    }
    
    data class LaptopInfo(
        val name: String,
        val ip: String,
        val apiPort: Int
    )
    
    companion object {
        private const val TAG = "DiscoveryService"
    }
}
