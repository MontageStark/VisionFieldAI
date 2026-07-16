package com.fieldvision.camera.network

import com.fieldvision.camera.camera.Resolution

data class ConnectionState(
    val type: ConnectionType,
    val bandwidth: Double,  // Mbps
    val latency: Long,     // ms
    val recommendedResolution: Resolution
)

enum class ConnectionType {
    WIFI,
    HOTSPOT,
    WIFI_DIRECT,
    VENUE_WIFI,
    UNKNOWN
}

data class BandwidthMeasurement(
    val downloadSpeed: Double,  // Mbps
    val uploadSpeed: Double,    // Mbps
    val latency: Long,          // ms
    val timestamp: Long
)
