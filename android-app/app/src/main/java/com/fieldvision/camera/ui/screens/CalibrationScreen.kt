package com.fieldvision.camera.ui.screens

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
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fieldvision.camera.ui.CameraUiState
import com.fieldvision.camera.ui.theme.*

@Composable
fun CalibrationScreen(
    uiState: CameraUiState,
    onBack: () -> Unit,
    onNextStep: (Int) -> Unit,
    onComplete: (Pair<Float, Float>, Pair<Float, Float>, Pair<Float, Float>) -> Unit,
) {
    val steps = listOf(
        CalibrationStep("Mount Phone", "Securely mount your phone at midfield, facing the pitch."),
        CalibrationStep("Level Camera", "Ensure the phone is level. Use a spirit level if available."),
        CalibrationStep("Left Goal Post", "Tap the LEFT goal post on the camera preview."),
        CalibrationStep("Right Goal Post", "Tap the RIGHT goal post on the camera preview."),
        CalibrationStep("Center Circle", "Tap the CENTER of the pitch (center circle)."),
    )

    val currentStep = uiState.calibrationStep.coerceIn(0, 4)

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
                text = "Field Calibration",
                color = TextPrimary,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
            )
            Spacer(modifier = Modifier.width(64.dp))
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Step indicator
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center,
        ) {
            steps.forEachIndexed { index, _ ->
                Box(
                    modifier = Modifier
                        .size(12.dp)
                        .clip(CircleShape)
                        .background(
                            if (index <= currentStep) Primary500 else DarkBorder
                        )
                )
                if (index < steps.lastIndex) {
                    Box(
                        modifier = Modifier
                            .width(24.dp)
                            .height(2.dp)
                            .background(
                                if (index < currentStep) Primary500 else DarkBorder
                            )
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(32.dp))

        // Current step content
        if (currentStep < 5) {
            val step = steps[currentStep]

            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = DarkCard),
                shape = RoundedCornerShape(16.dp),
            ) {
                Column(
                    modifier = Modifier.padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Text(
                        text = "Step ${currentStep + 1}",
                        color = Primary500,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium,
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = step.title,
                        color = TextPrimary,
                        fontSize = 24.sp,
                        fontWeight = FontWeight.Bold,
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        text = step.description,
                        color = TextSecondary,
                        fontSize = 14.sp,
                        textAlign = TextAlign.Center,
                    )
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Camera preview area (for tapping goal posts)
            if (currentStep >= 2) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(200.dp)
                        .clip(RoundedCornerShape(12.dp))
                        .background(DarkSurface)
                        .clickable {
                            // Simulate tap position
                            onNextStep(currentStep + 1)
                        },
                    contentAlignment = Alignment.Center,
                ) {
                    Text(
                        text = "Tap on camera preview",
                        color = TextMuted,
                        fontSize = 14.sp,
                    )
                }
            }

            Spacer(modifier = Modifier.weight(1f))

            // Next/Complete button
            Button(
                onClick = {
                    if (currentStep < 4) {
                        onNextStep(currentStep + 1)
                    } else {
                        onComplete(
                            Pair(0.1f, 0.5f), // Simulated left goal
                            Pair(0.9f, 0.5f), // Simulated right goal
                            Pair(0.5f, 0.5f), // Simulated center
                        )
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                shape = RoundedCornerShape(16.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Primary500),
            ) {
                Text(
                    text = if (currentStep < 4) "Next Step" else "Save Calibration",
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold,
                )
            }
        } else {
            // Calibration complete
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = DarkCard),
                shape = RoundedCornerShape(16.dp),
            ) {
                Column(
                    modifier = Modifier.padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Text("✓", fontSize = 48.sp)
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        text = "Calibration Complete",
                        color = AccentSuccess,
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Bold,
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "Your field geometry has been saved. The AI will use this for smarter tracking and framing.",
                        color = TextSecondary,
                        fontSize = 14.sp,
                        textAlign = TextAlign.Center,
                    )
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            Button(
                onClick = onBack,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                shape = RoundedCornerShape(16.dp),
                colors = ButtonDefaults.buttonColors(containerColor = AccentSuccess),
            ) {
                Text("Done", fontSize = 16.sp, fontWeight = FontWeight.Bold)
            }
        }
    }
}

private data class CalibrationStep(
    val title: String,
    val description: String,
)
