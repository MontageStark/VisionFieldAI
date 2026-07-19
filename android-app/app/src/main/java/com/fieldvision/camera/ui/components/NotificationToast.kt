package com.fieldvision.camera.ui.components

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fieldvision.camera.ui.Notification
import com.fieldvision.camera.ui.NotificationType
import com.fieldvision.camera.ui.theme.*

@Composable
fun NotificationToast(
    notifications: List<Notification>,
    onDismiss: (String) -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        notifications.forEach { notification ->
            AnimatedVisibility(
                visible = true,
                enter = slideInHorizontally(initialOffsetX = { -it }) + fadeIn(),
                exit = slideOutHorizontally(targetOffsetX = { it }) + fadeOut(),
            ) {
                NotificationItem(
                    notification = notification,
                    onDismiss = { onDismiss(notification.id) },
                )
            }
        }
    }
}

@Composable
private fun NotificationItem(
    notification: Notification,
    onDismiss: () -> Unit,
) {
    val (icon, bgColor) = when (notification.type) {
        NotificationType.SUCCESS -> "✓" to AccentSuccess
        NotificationType.WARNING -> "⚠" to AccentWarning
        NotificationType.ERROR -> "✗" to AccentError
    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(bgColor.copy(alpha = 0.15f), RoundedCornerShape(8.dp))
            .padding(horizontal = 12.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = icon,
            color = bgColor,
            fontSize = 14.sp,
            fontWeight = FontWeight.Bold,
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = notification.message,
            color = TextPrimary,
            fontSize = 12.sp,
        )
    }
}
