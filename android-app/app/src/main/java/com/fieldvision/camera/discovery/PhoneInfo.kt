package com.fieldvision.camera.discovery

import com.google.gson.Gson

data class PhoneInfo(
    val name: String,
    val ip: String,
    val port: Int,
    val protocols: List<String>,
    val resolutions: List<String>
) {
    fun toJson(): String = Gson().toJson(this)
    
    companion object {
        fun fromJson(json: String): PhoneInfo = Gson().fromJson(json, PhoneInfo::class.java)
    }
}

data class DiscoveryMessage(
    val type: String,
    val device: String,
    val ip: String,
    val ports: List<Int>,
    val protocols: List<String>,
    val resolutions: List<String>
) {
    fun toJson(): String = Gson().toJson(this)
    
    companion object {
        fun fromJson(json: String): DiscoveryMessage = Gson().fromJson(json, DiscoveryMessage::class.java)
    }
}
