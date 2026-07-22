package com.fieldvision.camera.ui.screens

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fieldvision.camera.ui.CameraUiState
import com.fieldvision.camera.ui.theme.*

@Composable
fun HomeScreen(
    uiState: CameraUiState,
    onGoLive: () -> Unit,
    onOpenSettings: () -> Unit,
    onStartCalibration: () -> Unit,
    onLongPressLogo: () -> Unit,
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
    ) {
        // Camera preview placeholder (will be TextureView in integration)
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(DarkSurface),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = "LIVE PREVIEW",
                color = TextMuted,
                fontSize = 14.sp,
                fontWeight = FontWeight.Medium,
            )
        }

        // Top gradient overlay
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(120.dp)
                .background(
                    Brush.verticalGradient(
                        colors = listOf(DarkBackground, DarkBackground.copy(alpha = 0f))
                    )
                )
        )

        // Bottom gradient overlay
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(200.dp)
                .align(Alignment.BottomCenter)
                .background(
                    Brush.verticalGradient(
                        colors = listOf(DarkBackground.copy(alpha = 0f), DarkBackground)
                    )
                )
        )

        // Top bar
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 12.dp)
                .align(Alignment.TopCenter),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            // Logo (long press for developer screen)
            Text(
                text = "FIELDVISION AI",
                color = TextPrimary,
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.pointerInput(Unit) {
                    detectTapGestures(
                        onLongPress = { onLongPressLogo() },
                    )
                },
            )

            Text(
                text = "AI Broadcast Camera",
                color = TextSecondary,
                fontSize = 12.sp,
            )
        }

        // Bottom section
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .align(Alignment.BottomCenter)
                .padding(horizontal = 24.dp, vertical = 32.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // Status indicators
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly,
            ) {
                StatusIndicator(
                    label = "Camera",
                    connected = uiState.isCameraConnected,
                )
                StatusIndicator(
                    label = "WiFi",
                    connected = uiState.isWifiConnected,
                )
                StatusIndicator(
                    label = "Battery ${uiState.batteryLevel}%",
                    connected = uiState.batteryLevel > 20,
                )
            }

            Spacer(modifier = Modifier.height(8.dp))

            // GO LIVE button
            Button(
                onClick = onGoLive,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                shape = RoundedCornerShape(16.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Primary500,
                ),
                enabled = true,
            ) {
                Box(
                    modifier = Modifier
                        .size(12.dp)
                        .clip(CircleShape)
                        .background(LiveRed),
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "GO LIVE",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold,
                )
            }

            // Quick actions
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly,
            ) {
                TextButton(onClick = onOpenSettings) {
                    Text("Settings", color = TextSecondary)
                }
                TextButton(onClick = onStartCalibration) {
                    Text("Calibrate", color = TextSecondary)
                }
            }
        }
    }
}

@Composable
private fun StatusIndicator(
    label: String,
    connected: Boolean,
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Box(
            modifier = Modifier
                .size(8.dp)
                .clip(CircleShape)
                .background(if (connected) AccentSuccess else AccentError),
        )
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = label,
            color = TextSecondary,
            fontSize = 11.sp,
        )
    }
}
