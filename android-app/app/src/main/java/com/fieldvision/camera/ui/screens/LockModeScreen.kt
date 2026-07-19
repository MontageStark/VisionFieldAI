package com.fieldvision.camera.ui.screens

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fieldvision.camera.ui.CameraUiState
import com.fieldvision.camera.ui.theme.*

@Composable
fun LockModeScreen(
    uiState: CameraUiState,
    onUnlock: () -> Unit,
    onStopStreaming: () -> Unit,
) {
    val pulseAnim = rememberInfiniteTransition(label = "pulse")
    val pulseAlpha by pulseAnim.animateFloat(
        initialValue = 1f,
        targetValue = 0.3f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "pulseAlpha",
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
    ) {
        // Camera preview placeholder
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(DarkSurface),
        )

        // Minimal overlay — ONLY essential info
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            verticalArrangement = Arrangement.SpaceBetween,
        ) {
            // Top: LIVE + Battery + FPS
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Box(
                        modifier = Modifier
                            .size(10.dp)
                            .clip(CircleShape)
                            .background(LiveRed.copy(alpha = pulseAlpha)),
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "LIVE",
                        color = LiveRed,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                    )
                }

                Row(
                    horizontalArrangement = Arrangement.spacedBy(20.dp),
                ) {
                    LockStat("Battery", "${uiState.batteryLevel}%")
                    LockStat("FPS", "${uiState.fps}")
                }
            }

            // Center: Temperature + WiFi
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
            ) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(24.dp),
                ) {
                    LockStat("Temp", "${uiState.temperature.toInt()}°C")
                    LockStat("WiFi", if (uiState.wifiStrength > 70) "Excellent" else "Good")
                }
            }

            // Bottom: STOP only
            Button(
                onClick = onStopStreaming,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = AccentError,
                ),
            ) {
                Text(
                    text = "STOP",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold,
                )
            }
        }

        // Double-tap to unlock hint (invisible, covers full screen)
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(DarkBackground.copy(alpha = 0f)),
        )
    }
}

@Composable
private fun LockStat(label: String, value: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            text = value,
            color = TextPrimary,
            fontSize = 16.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.Monospace,
        )
        Text(
            text = label,
            color = TextMuted,
            fontSize = 10.sp,
        )
    }
}
