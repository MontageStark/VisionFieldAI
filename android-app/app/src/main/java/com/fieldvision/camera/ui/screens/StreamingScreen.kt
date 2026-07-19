package com.fieldvision.camera.ui.screens

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fieldvision.camera.ui.CameraUiState
import com.fieldvision.camera.ui.theme.*

@Composable
fun StreamingScreen(
    uiState: CameraUiState,
    onStopStreaming: () -> Unit,
    onLockScreen: () -> Unit,
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
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = "CAMERA PREVIEW",
                color = TextMuted,
                fontSize = 14.sp,
            )
        }

        // Top gradient
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(80.dp)
                .background(
                    Brush.verticalGradient(
                        colors = listOf(DarkBackground, DarkBackground.copy(alpha = 0f))
                    )
                )
        )

        // Bottom gradient
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(120.dp)
                .align(Alignment.BottomCenter)
                .background(
                    Brush.verticalGradient(
                        colors = listOf(DarkBackground.copy(alpha = 0f), DarkBackground)
                    )
                )
        )

        // LIVE indicator (top left)
        Row(
            modifier = Modifier
                .padding(16.dp)
                .align(Alignment.TopStart),
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
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold,
            )
        }

        // Stats bar (top right)
        Row(
            modifier = Modifier
                .padding(16.dp)
                .align(Alignment.TopEnd),
            horizontalArrangement = Arrangement.spacedBy(16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            StatBadge("4K ${uiState.targetFps}FPS")
            StatBadge("Battery ${uiState.batteryLevel}%")
            StatBadge("WiFi ${if (uiState.wifiStrength > 70) "Excellent" else if (uiState.wifiStrength > 40) "Good" else "Weak"}")
        }

        // Bottom stats
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp)
                .align(Alignment.BottomCenter)
                .padding(bottom = 80.dp),
            horizontalArrangement = Arrangement.SpaceEvenly,
        ) {
            BottomStat("Bitrate", "${uiState.bitrate} Mbps")
            BottomStat("Latency", "${uiState.latency} ms")
            BottomStat("AI", if (uiState.aiConnected) "Connected" else "Disconnected")
        }

        // Floating controls area (bottom)
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp, vertical = 16.dp)
                .align(Alignment.BottomCenter),
            horizontalArrangement = Arrangement.SpaceEvenly,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            // Lock button
            FloatingActionButton(
                onClick = onLockScreen,
                modifier = Modifier.size(48.dp),
                containerColor = DarkCard,
                contentColor = TextPrimary,
                shape = CircleShape,
            ) {
                Text("🔒", fontSize = 20.sp)
            }

            // Focus
            FloatingActionButton(
                onClick = { /* Auto focus */ },
                modifier = Modifier.size(48.dp),
                containerColor = DarkCard,
                contentColor = TextPrimary,
                shape = CircleShape,
            ) {
                Text("📷", fontSize = 20.sp)
            }

            // Torch
            FloatingActionButton(
                onClick = { /* Toggle torch */ },
                modifier = Modifier.size(48.dp),
                containerColor = if (uiState.torchEnabled) Primary500 else DarkCard,
                contentColor = TextPrimary,
                shape = CircleShape,
            ) {
                Text("⚡", fontSize = 20.sp)
            }

            // Mic
            FloatingActionButton(
                onClick = { /* Toggle mic */ },
                modifier = Modifier.size(48.dp),
                containerColor = DarkCard,
                contentColor = TextPrimary,
                shape = CircleShape,
            ) {
                Text("🎤", fontSize = 20.sp)
            }

            // Stop
            Button(
                onClick = onStopStreaming,
                modifier = Modifier
                    .height(48.dp)
                    .width(100.dp),
                shape = RoundedCornerShape(24.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = AccentError,
                ),
            ) {
                Text("STOP", fontWeight = FontWeight.Bold)
            }
        }
    }
}

@Composable
private fun StatBadge(text: String) {
    Text(
        text = text,
        color = TextPrimary,
        fontSize = 11.sp,
        fontWeight = FontWeight.Medium,
        fontFamily = FontFamily.Monospace,
        modifier = Modifier
            .background(DarkCard.copy(alpha = 0.8f), RoundedCornerShape(4.dp))
            .padding(horizontal = 8.dp, vertical = 4.dp),
    )
}

@Composable
private fun BottomStat(label: String, value: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            text = value,
            color = TextPrimary,
            fontSize = 14.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.Monospace,
        )
        Text(
            text = label,
            color = TextSecondary,
            fontSize = 10.sp,
        )
    }
}
