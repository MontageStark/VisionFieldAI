package com.fieldvision.camera.network

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.Build
import android.util.Log
import com.fieldvision.camera.camera.Resolution
import kotlinx.coroutines.*

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
                    connection?.let { onConnectionChanged?.invoke(it) }
                }
                delay(5000)
            }
        }
    }

    fun stopMonitoring() {
        monitoringJob?.cancel()
        scope.cancel()
    }

    fun getRecommendedResolution(): Resolution {
        val connection = currentConnection ?: return Resolution.HD_720P
        return when {
            connection.bandwidth > 20 -> Resolution.UHD_4K
            connection.bandwidth > 10 -> Resolution.FHD_1080P
            else -> Resolution.HD_720P
        }
    }

    private fun measureConnection(): ConnectionState? {
        return try {
            val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            val network = cm.activeNetwork ?: return null
            val caps = cm.getNetworkCapabilities(network) ?: return null

            val type = when {
                caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) -> ConnectionType.WIFI
                caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) -> ConnectionType.CELLULAR
                caps.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET) -> ConnectionType.WIFI
                else -> ConnectionType.UNKNOWN
            }

            val bandwidth = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                caps.linkUpstreamBandwidthKbps / 1000.0 // Convert kbps to Mbps
            } else {
                // Fallback estimates for older APIs
                when (type) {
                    ConnectionType.WIFI -> 50.0
                    ConnectionType.CELLULAR -> 10.0
                    else -> 0.0
                }
            }

            ConnectionState(type = type, bandwidth = bandwidth, latency = 0)
        } catch (e: Exception) {
            Log.e(TAG, "Connection measurement error: ${e.message}")
            null
        }
    }

    companion object {
        private const val TAG = "NetworkMonitor"
    }
}
