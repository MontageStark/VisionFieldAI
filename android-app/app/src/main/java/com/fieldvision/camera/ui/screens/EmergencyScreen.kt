package com.fieldvision.camera.ui.screens

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fieldvision.camera.ui.theme.*

@Composable
fun EmergencyScreen(
    reconnectCountdown: Int,
) {
    val pulseAnim = rememberInfiniteTransition(label = "pulse")
    val pulseAlpha by pulseAnim.animateFloat(
        initialValue = 1f,
        targetValue = 0.5f,
        animationSpec = infiniteRepeatable(
            animation = tween(500, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "pulseAlpha",
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(AccentError.copy(alpha = 0.9f)),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            Text(
                text = "⚠",
                fontSize = 64.sp,
            )
            Spacer(modifier = Modifier.height(24.dp))
            Text(
                text = "CONNECTION LOST",
                color = TextPrimary,
                fontSize = 32.sp,
                fontWeight = FontWeight.Bold,
            )
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "Reconnecting...",
                color = TextPrimary.copy(alpha = pulseAlpha),
                fontSize = 20.sp,
            )
            Spacer(modifier = Modifier.height(24.dp))
            if (reconnectCountdown > 0) {
                Text(
                    text = "$reconnectCountdown",
                    color = TextPrimary,
                    fontSize = 48.sp,
                    fontWeight = FontWeight.Bold,
                )
            }
        }
    }
}
