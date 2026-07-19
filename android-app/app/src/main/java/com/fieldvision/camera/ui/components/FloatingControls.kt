package com.fieldvision.camera.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fieldvision.camera.ui.theme.*

@Composable
fun FloatingControls(
    isTorchEnabled: Boolean,
    onLockClick: () -> Unit,
    onFocusClick: () -> Unit,
    onTorchClick: () -> Unit,
    onMicClick: () -> Unit,
    onSettingsClick: () -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 24.dp, vertical = 16.dp),
        horizontalArrangement = Arrangement.SpaceEvenly,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        ControlButton(icon = "🔒", label = "Lock", onClick = onLockClick)
        ControlButton(icon = "📷", label = "Focus", onClick = onFocusClick)
        ControlButton(
            icon = "⚡",
            label = "Torch",
            onClick = onTorchClick,
            isActive = isTorchEnabled,
        )
        ControlButton(icon = "🎤", label = "Mic", onClick = onMicClick)
        ControlButton(icon = "⚙️", label = "Settings", onClick = onSettingsClick)
    }
}

@Composable
private fun ControlButton(
    icon: String,
    label: String,
    onClick: () -> Unit,
    isActive: Boolean = false,
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier.clickable { onClick() },
    ) {
        Box(
            modifier = Modifier
                .size(48.dp)
                .clip(CircleShape)
                .background(if (isActive) Primary500 else DarkCard),
            contentAlignment = Alignment.Center,
        ) {
            Text(icon, fontSize = 20.sp)
        }
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = label,
            color = TextMuted,
            fontSize = 10.sp,
        )
    }
}
