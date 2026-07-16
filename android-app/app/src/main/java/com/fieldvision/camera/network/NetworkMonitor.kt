package com.fieldvision.camera.network

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.util.Log
import com.fieldvision.camera.camera.Resolution
import kotlinx.coroutines.*
import java.net.HttpURLConnection
import java.net.URL

class NetworkMonitor(private val context: Context) {
    
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var monitoringJob: Job? = null
    
    @Volatile
    var currentConnection: ConnectionState? = null
        private set
    
    var onConnectionChanged: ((ConnectionState) -> Unit)? = null
    
    fun startMonitoring() {
        monitoringJob = scope.launch {
            while (isActive) {
                val connection = measureConnection()
                if (connection != currentConnection) {
                    currentConnection = connection
                    onConnectionChanged?.invoke(connection)
                }
                delay(5000) // Measure every 5 seconds
            }
        }
    }
    
    fun stopMonitoring() {
        monitoringJob?.cancel()
        scope.cancel()
    }
    
    fun getRecommendedResolution(): Resolution {
        val connection = currentConnection ?: return Resolution.UHD_4K
        
        return when {
            connection.bandwidth > 20 -> Resolution.UHD_4K
            connection.bandwidth > 10 -> Resolution.FHD_1080P
            else -> Resolution.HD_720P
        }
    }
    
    private fun measureConnection(): ConnectionState? {
        return try {
            val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            val network = connectivityManager.activeNetwork ?: return null
            val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return null
            
            val connectionType = when {
                capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) -> {
                    if (isHotspot()) ConnectionType.HOTSPOT else ConnectionType.WIFI
                }
                capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) -> ConnectionType.UNKNOWN
                else -> ConnectionType.UNKNOWN
            }
            
            val bandwidth = measureBandwidth()
            val latency = measureLatency()
            val resolution = calculateResolution(bandwidth)
            
            ConnectionState(
                type = connectionType,
                bandwidth = bandwidth,
                latency = latency,
                recommendedResolution = resolution
            )
        } catch (e: Exception) {
            Log.e(TAG, "Connection measurement error: ${e.message}")
            null
        }
    }
    
    private fun measureBandwidth(): Double {
        return try {
            val url = URL("http://speedtest.tele2.net/1MB.zip")
            val connection = url.openConnection() as HttpURLConnection
            connection.connectTimeout = 5000
            connection.readTimeout = 5000
            
            val startTime = System.currentTimeMillis()
            val inputStream = connection.inputStream
            val buffer = ByteArray(1024)
            var totalBytes = 0L
            
            while (true) {
                val bytesRead = inputStream.read(buffer)
                if (bytesRead == -1) break
                totalBytes += bytesRead
            }
            
            val elapsed = (System.currentTimeMillis() - startTime) / 1000.0
            inputStream.close()
            connection.disconnect()
            
            (totalBytes * 8) / (elapsed * 1000000) // Convert to Mbps
        } catch (e: Exception) {
            Log.e(TAG, "Bandwidth measurement error: ${e.message}")
            0.0
        }
    }
    
    private fun measureLatency(): Long {
        return try {
            val url = URL("http://www.google.com")
            val connection = url.openConnection() as HttpURLConnection
            connection.connectTimeout = 3000
            
            val startTime = System.currentTimeMillis()
            connection.connect()
            val latency = System.currentTimeMillis() - startTime
            
            connection.disconnect()
            latency
        } catch (e: Exception) {
            Log.e(TAG, "Latency measurement error: ${e.message}")
            -1
        }
    }
    
    private fun calculateResolution(bandwidth: Double): Resolution {
        return when {
            bandwidth > 20 -> Resolution.UHD_4K
            bandwidth > 10 -> Resolution.FHD_1080P
            else -> Resolution.HD_720P
        }
    }
    
    private fun isHotspot(): Boolean {
        // Simple heuristic - check if IP is in hotspot range
        // Most Android hotspots use 192.168.43.x
        return true // Simplified for now
    }
    
    companion object {
        private const val TAG = "NetworkMonitor"
    }
}
