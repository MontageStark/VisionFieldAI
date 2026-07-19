package com.fieldvision.camera.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fieldvision.camera.ui.theme.*

@Composable
fun StatusBar(
    batteryLevel: Int,
    fps: Int,
    temperature: Float,
    wifiStrength: Int,
    bitrate: Int,
    latency: Int,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(DarkCard.copy(alpha = 0.9f), RoundedCornerShape(8.dp))
            .padding(horizontal = 12.dp, vertical = 8.dp),
        horizontalArrangement = Arrangement.SpaceEvenly,
    ) {
        StatItem("Battery", "$batteryLevel%")
        StatItem("FPS", "$fps")
        StatItem("Temp", "${temperature.toInt()}°C")
        StatItem("WiFi", if (wifiStrength > 70) "Excellent" else "Good")
        StatItem("Bitrate", "${bitrate}M")
        StatItem("Latency", "${latency}ms")
    }
}

@Composable
private fun StatItem(label: String, value: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            text = value,
            color = TextPrimary,
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.Monospace,
        )
        Text(
            text = label,
            color = TextMuted,
            fontSize = 9.sp,
        )
    }
}
