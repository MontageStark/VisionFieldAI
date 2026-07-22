package com.fieldvision.camera.device

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import android.os.Environment
import android.os.StatFs
import android.util.Log
import kotlinx.coroutines.*
import java.io.File

class DeviceTelemetryMonitor(private val context: Context) {

    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var pollingJob: Job? = null

    var onTelemetryChanged: ((battery: Int, temperature: Float, storage: Long) -> Unit)? = null

    fun startMonitoring(intervalMs: Long = 5000) {
        pollingJob = scope.launch {
            while (isActive) {
                val telemetry = readTelemetry()
                onTelemetryChanged?.invoke(telemetry.battery, telemetry.temperature, telemetry.storageFree)
                delay(intervalMs)
            }
        }
    }

    fun stopMonitoring() {
        pollingJob?.cancel()
        scope.cancel()
    }

    private data class Telemetry(val battery: Int, val temperature: Float, val storageFree: Long)

    private fun readTelemetry(): Telemetry {
        return Telemetry(
            battery = readBatteryPercent(),
            temperature = readCpuTemperature(),
            storageFree = readStorageFreeBytes(),
        )
    }

    private fun readBatteryPercent(): Int {
        return try {
            val bm = context.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
            bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        } catch (e: Exception) {
            Log.w(TAG, "Battery read failed: ${e.message}")
            -1
        }
    }

    private fun readCpuTemperature(): Float {
        return try {
            val zone = File("/sys/class/thermal/thermal_zone0/temp")
            if (zone.exists() && zone.canRead()) {
                val raw = zone.readText().trim().toFloatOrNull() ?: return 0f
                raw / 1000f
            } else {
                0f
            }
        } catch (e: Exception) {
            0f
        }
    }

    private fun readStorageFreeBytes(): Long {
        return try {
            val path = Environment.getDataDirectory()
            val stats = StatFs(path.absolutePath)
            stats.availableBytes
        } catch (e: Exception) {
            0L
        }
    }

    companion object {
        private const val TAG = "DeviceTelemetry"
    }
}
