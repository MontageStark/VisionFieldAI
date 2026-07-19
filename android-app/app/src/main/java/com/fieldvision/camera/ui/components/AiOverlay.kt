package com.fieldvision.camera.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import com.fieldvision.camera.ui.theme.*

@Composable
fun AiOverlay(
    playerBoxes: List<Pair<Pair<Float, Float>, Pair<Float, Float>>> = emptyList(),
    ballPosition: Pair<Float, Float>? = null,
    showHorizon: Boolean = true,
    virtualCameraRect: Pair<Pair<Float, Float>, Pair<Float, Float>>? = null,
) {
    Canvas(modifier = Modifier.fillMaxSize()) {
        // Player boxes (green)
        playerBoxes.forEach { (topLeft, bottomRight) ->
            drawRect(
                color = AccentSuccess,
                topLeft = Offset(topLeft.first * size.width, topLeft.second * size.height),
                size = Size(
                    (bottomRight.first - topLeft.first) * size.width,
                    (bottomRight.second - topLeft.second) * size.height,
                ),
                style = Stroke(width = 3f),
            )
        }

        // Ball position (yellow circle)
        ballPosition?.let { (x, y) ->
            drawCircle(
                color = AccentWarning,
                radius = 12f,
                center = Offset(x * size.width, y * size.height),
            )
            drawCircle(
                color = AccentWarning,
                radius = 16f,
                center = Offset(x * size.width, y * size.height),
                style = Stroke(width = 2f),
            )
        }

        // Horizon line (cyan, dashed)
        if (showHorizon) {
            drawLine(
                color = AccentInfo,
                start = Offset(0f, size.height * 0.45f),
                end = Offset(size.width, size.height * 0.45f),
                strokeWidth = 2f,
            )
        }

        // Virtual camera rectangle (blue)
        virtualCameraRect?.let { (topLeft, bottomRight) ->
            drawRect(
                color = Primary500,
                topLeft = Offset(topLeft.first * size.width, topLeft.second * size.height),
                size = Size(
                    (bottomRight.first - topLeft.first) * size.width,
                    (bottomRight.second - topLeft.second) * size.height,
                ),
                style = Stroke(width = 3f),
            )
        }
    }
}
