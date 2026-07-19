package com.fieldvision.camera.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fieldvision.camera.ui.theme.*

@Composable
fun AiStatusPanel(
    aiConnected: Boolean,
    virtualCameraActive: Boolean,
    servoEnabled: Boolean,
    streamingActive: Boolean,
) {
    Column(
        modifier = Modifier
            .background(DarkCard, RoundedCornerShape(12.dp))
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(
            text = "AI Connection",
            color = TextSecondary,
            fontSize = 10.sp,
            fontWeight = FontWeight.Medium,
        )
        StatusRow("Virtual Camera", virtualCameraActive)
        StatusRow("Servo", servoEnabled)
        StatusRow("Streaming", streamingActive)
    }
}

@Composable
private fun StatusRow(label: String, active: Boolean) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = label,
            color = TextPrimary,
            fontSize = 12.sp,
        )
        Row(
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                modifier = Modifier
                    .size(8.dp)
                    .clip(CircleShape)
                    .background(if (active) AccentSuccess else TextMuted),
            )
            Spacer(modifier = Modifier.width(6.dp))
            Text(
                text = if (active) "Active" else "Disabled",
                color = if (active) AccentSuccess else TextMuted,
                fontSize = 11.sp,
            )
        }
    }
}
