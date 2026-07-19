package com.fieldvision.camera.network

data class ConnectionState(
    val type: ConnectionType,
    val bandwidth: Double,
    val latency: Long,
)

enum class ConnectionType {
    WIFI,
    CELLULAR,
    UNKNOWN
}
