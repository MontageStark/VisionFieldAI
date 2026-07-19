package com.fieldvision.camera.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fieldvision.camera.ui.CameraUiState
import com.fieldvision.camera.ui.theme.*

@Composable
fun DeveloperScreen(
    uiState: CameraUiState,
    onBack: () -> Unit,
) {
    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
            .padding(16.dp),
    ) {
        // Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            TextButton(onClick = onBack) {
                Text("← Back", color = Primary500)
            }
            Text(
                text = "Developer",
                color = AccentWarning,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
            )
            Spacer(modifier = Modifier.width(64.dp))
        }

        Spacer(modifier = Modifier.height(16.dp))

        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(scrollState),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // Encoder Info
            DeveloperCard(title = "Encoder") {
                DevRow("Resolution", "${uiState.resolution.width}x${uiState.resolution.height}")
                DevRow("FPS", "${uiState.targetFps}")
                DevRow("Bitrate", "${uiState.targetBitrate} Mbps")
                DevRow("Codec", uiState.codec.label)
                DevRow("Dropped Frames", "${uiState.droppedFrames}")
            }

            // CPU
            DeveloperCard(title = "CPU") {
                DevRow("Usage", "${uiState.cpuUsage.toInt()}%")
                LinearProgressIndicator(
                    progress = { uiState.cpuUsage / 100f },
                    modifier = Modifier.fillMaxWidth(),
                    color = if (uiState.cpuUsage > 80) AccentError else Primary500,
                    trackColor = DarkSurface,
                )
            }

            // RAM
            DeveloperCard(title = "RAM") {
                DevRow("Usage", "${uiState.ramUsage.toInt()}%")
                LinearProgressIndicator(
                    progress = { uiState.ramUsage / 100f },
                    modifier = Modifier.fillMaxWidth(),
                    color = if (uiState.ramUsage > 80) AccentError else Primary500,
                    trackColor = DarkSurface,
                )
            }

            // Network
            DeveloperCard(title = "Network") {
                DevRow("Type", if (uiState.isWifiConnected) "WiFi" else "Disconnected")
                DevRow("Strength", "${uiState.wifiStrength}%")
                DevRow("Latency", "${uiState.latency}ms")
                DevRow("Stream Mode", uiState.streamMode.label)
            }

            // Camera API
            DeveloperCard(title = "Camera2 API") {
                DevRow("Status", if (uiState.isCameraConnected) "Connected" else "Disconnected")
                DevRow("Preview", if (uiState.isPreviewActive) "Active" else "Inactive")
                DevRow("Streaming", if (uiState.isStreaming) "Active" else "Inactive")
            }

            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

@Composable
private fun DeveloperCard(
    title: String,
    content: @Composable ColumnScope.() -> Unit,
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = DarkCard),
        shape = RoundedCornerShape(12.dp),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(
                text = title,
                color = AccentWarning,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold,
            )
            content()
        }
    }
}

@Composable
private fun DevRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(
            text = label,
            color = TextSecondary,
            fontSize = 12.sp,
        )
        Text(
            text = value,
            color = TextPrimary,
            fontSize = 12.sp,
            fontFamily = FontFamily.Monospace,
        )
    }
}
