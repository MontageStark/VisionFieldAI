package com.fieldvision.camera.stream

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.net.wifi.WifiManager
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import android.util.Log
import androidx.core.app.NotificationCompat
import com.fieldvision.camera.MainActivity

class StreamingService : Service() {

    private var wifiLock: WifiManager.WifiLock? = null
    private var wakeLock: PowerManager.WakeLock? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        acquireLocks()
        Log.i(TAG, "StreamingService created — locks acquired")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startForeground(NOTIFICATION_ID, buildNotification("Streaming active"))
        Log.i(TAG, "StreamingService started — foreground notification shown")
        return START_STICKY
    }

    override fun onDestroy() {
        releaseLocks()
        Log.i(TAG, "StreamingService destroyed — locks released")
        super.onDestroy()
    }

    private fun acquireLocks() {
        // WiFi lock — prevents WiFi from sleeping when screen off
        val wifiManager = applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
        wifiLock = wifiManager.createWifiLock(WifiManager.WIFI_MODE_FULL_HIGH_PERF, "FieldVision:StreamLock")
        wifiLock?.acquire()
        Log.i(TAG, "WiFi lock acquired")

        // Wake lock — keeps CPU running when screen off
        val powerManager = applicationContext.getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock = powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "FieldVision:StreamWake")
        wakeLock?.acquire(12 * 60 * 60 * 1000L) // 12 hours max
        Log.i(TAG, "Wake lock acquired (12h max)")
    }

    private fun releaseLocks() {
        try { wifiLock?.release() } catch (_: Exception) {}
        wifiLock = null
        try { wakeLock?.release() } catch (_: Exception) {}
        wakeLock = null
        Log.i(TAG, "Locks released")
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Camera Streaming",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "FieldVision camera streaming active"
            }
            getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
        }
    }

    private fun buildNotification(text: String): Notification {
        val intent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_IMMUTABLE)

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("FieldVision AI")
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_menu_camera)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build()
    }

    companion object {
        private const val TAG = "StreamingService"
        private const val CHANNEL_ID = "fieldvision_stream"
        private const val NOTIFICATION_ID = 1001

        fun start(context: Context) {
            val intent = Intent(context, StreamingService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }

        fun stop(context: Context) {
            context.stopService(Intent(context, StreamingService::class.java))
        }
    }
}
