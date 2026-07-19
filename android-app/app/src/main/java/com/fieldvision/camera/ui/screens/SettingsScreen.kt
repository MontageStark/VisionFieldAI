package com.fieldvision.camera.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fieldvision.camera.ui.*
import com.fieldvision.camera.ui.theme.*

@Composable
fun SettingsScreen(
    uiState: CameraUiState,
    onBack: () -> Unit,
    onResolutionChange: (Resolution) -> Unit,
    onFpsChange: (Int) -> Unit,
    onBitrateChange: (Int) -> Unit,
    onCodecChange: (Codec) -> Unit,
    onLensChange: (Lens) -> Unit,
    onExposureChange: (ExposureMode) -> Unit,
    onWhiteBalanceChange: (WhiteBalanceMode) -> Unit,
    onFocusModeChange: (FocusMode) -> Unit,
    onToggleHdr: () -> Unit,
    onStreamModeChange: (StreamMode) -> Unit,
    onServerAddressChange: (String) -> Unit,
    onServerPortChange: (Int) -> Unit,
    onToggleKeepScreenAwake: () -> Unit,
    onToggleBatterySaver: () -> Unit,
    onToggleAutoReconnect: () -> Unit,
    onToggleStartOnBoot: () -> Unit,
    onToggleLockOrientation: () -> Unit,
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
                text = "Settings",
                color = TextPrimary,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
            )
            Spacer(modifier = Modifier.width(64.dp))
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Scrollable content
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(scrollState),
            verticalArrangement = Arrangement.spacedBy(24.dp),
        ) {
            // VIDEO section
            SettingsSection(title = "Video") {
                // Resolution
                SettingsRow(label = "Resolution") {
                    SingleChoiceSegmentedButtonRow {
                        Resolution.entries.forEachIndexed { index, res ->
                            SegmentedButton(
                                selected = uiState.resolution == res,
                                onClick = { onResolutionChange(res) },
                                shape = SegmentedButtonDefaults.itemShape(
                                    index = index,
                                    count = Resolution.entries.size,
                                ),
                                colors = SegmentedButtonDefaults.colors(
                                    activeContainerColor = Primary500,
                                    inactiveContainerColor = DarkCard,
                                ),
                            ) {
                                Text(res.label, fontSize = 12.sp)
                            }
                        }
                    }
                }

                // FPS
                SettingsRow(label = "FPS") {
                    SingleChoiceSegmentedButtonRow {
                        listOf(30, 60).forEachIndexed { index, fps ->
                            SegmentedButton(
                                selected = uiState.targetFps == fps,
                                onClick = { onFpsChange(fps) },
                                shape = SegmentedButtonDefaults.itemShape(
                                    index = index,
                                    count = 2,
                                ),
                                colors = SegmentedButtonDefaults.colors(
                                    activeContainerColor = Primary500,
                                    inactiveContainerColor = DarkCard,
                                ),
                            ) {
                                Text("$fps", fontSize = 12.sp)
                            }
                        }
                    }
                }

                // Bitrate
                SettingsRow(label = "Bitrate") {
                    SingleChoiceSegmentedButtonRow {
                        listOf(10, 20, 30).forEachIndexed { index, bitrate ->
                            SegmentedButton(
                                selected = uiState.targetBitrate == bitrate,
                                onClick = { onBitrateChange(bitrate) },
                                shape = SegmentedButtonDefaults.itemShape(
                                    index = index,
                                    count = 3,
                                ),
                                colors = SegmentedButtonDefaults.colors(
                                    activeContainerColor = Primary500,
                                    inactiveContainerColor = DarkCard,
                                ),
                            ) {
                                Text("${bitrate}M", fontSize = 12.sp)
                            }
                        }
                    }
                }

                // Codec
                SettingsRow(label = "Codec") {
                    SingleChoiceSegmentedButtonRow {
                        Codec.entries.forEachIndexed { index, codec ->
                            SegmentedButton(
                                selected = uiState.codec == codec,
                                onClick = { onCodecChange(codec) },
                                shape = SegmentedButtonDefaults.itemShape(
                                    index = index,
                                    count = Codec.entries.size,
                                ),
                                colors = SegmentedButtonDefaults.colors(
                                    activeContainerColor = Primary500,
                                    inactiveContainerColor = DarkCard,
                                ),
                            ) {
                                Text(codec.label, fontSize = 12.sp)
                            }
                        }
                    }
                }
            }

            // STREAMING section
            SettingsSection(title = "Streaming") {
                // Stream Mode
                SettingsRow(label = "Mode") {
                    SingleChoiceSegmentedButtonRow {
                        StreamMode.entries.forEachIndexed { index, mode ->
                            SegmentedButton(
                                selected = uiState.streamMode == mode,
                                onClick = { onStreamModeChange(mode) },
                                shape = SegmentedButtonDefaults.itemShape(
                                    index = index,
                                    count = StreamMode.entries.size,
                                ),
                                colors = SegmentedButtonDefaults.colors(
                                    activeContainerColor = Primary500,
                                    inactiveContainerColor = DarkCard,
                                ),
                            ) {
                                Text(mode.label, fontSize = 11.sp)
                            }
                        }
                    }
                }

                // Server Address
                SettingsTextField(
                    label = "Server Address",
                    value = uiState.serverAddress,
                    onValueChange = onServerAddressChange,
                    placeholder = "192.168.1.15",
                )

                // Port
                SettingsTextField(
                    label = "Port",
                    value = uiState.serverPort.toString(),
                    onValueChange = { onServerPortChange(it.toIntOrNull() ?: 8554) },
                    placeholder = "8554",
                )

                // Test Connection button
                Button(
                    onClick = { /* Test connection */ },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = DarkCard,
                    ),
                ) {
                    Text("Test Connection", color = Primary500)
                }
            }

            // CAMERA CONTROLS section
            SettingsSection(title = "Camera Controls") {
                // Lens
                SettingsRow(label = "Lens") {
                    SingleChoiceSegmentedButtonRow {
                        Lens.entries.forEachIndexed { index, lens ->
                            SegmentedButton(
                                selected = uiState.lens == lens,
                                onClick = { onLensChange(lens) },
                                shape = SegmentedButtonDefaults.itemShape(
                                    index = index,
                                    count = Lens.entries.size,
                                ),
                                colors = SegmentedButtonDefaults.colors(
                                    activeContainerColor = Primary500,
                                    inactiveContainerColor = DarkCard,
                                ),
                            ) {
                                Text(lens.label, fontSize = 11.sp)
                            }
                        }
                    }
                }

                // Exposure
                SettingsRow(label = "Exposure") {
                    SingleChoiceSegmentedButtonRow {
                        ExposureMode.entries.forEachIndexed { index, mode ->
                            SegmentedButton(
                                selected = uiState.exposure == mode,
                                onClick = { onExposureChange(mode) },
                                shape = SegmentedButtonDefaults.itemShape(
                                    index = index,
                                    count = ExposureMode.entries.size,
                                ),
                                colors = SegmentedButtonDefaults.colors(
                                    activeContainerColor = Primary500,
                                    inactiveContainerColor = DarkCard,
                                ),
                            ) {
                                Text(mode.label, fontSize = 12.sp)
                            }
                        }
                    }
                }

                // White Balance
                SettingsRow(label = "White Balance") {
                    SingleChoiceSegmentedButtonRow {
                        WhiteBalanceMode.entries.forEachIndexed { index, mode ->
                            SegmentedButton(
                                selected = uiState.whiteBalance == mode,
                                onClick = { onWhiteBalanceChange(mode) },
                                shape = SegmentedButtonDefaults.itemShape(
                                    index = index,
                                    count = WhiteBalanceMode.entries.size,
                                ),
                                colors = SegmentedButtonDefaults.colors(
                                    activeContainerColor = Primary500,
                                    inactiveContainerColor = DarkCard,
                                ),
                            ) {
                                Text(mode.label, fontSize = 12.sp)
                            }
                        }
                    }
                }

                // Focus
                SettingsRow(label = "Focus") {
                    SingleChoiceSegmentedButtonRow {
                        FocusMode.entries.forEachIndexed { index, mode ->
                            SegmentedButton(
                                selected = uiState.focusMode == mode,
                                onClick = { onFocusModeChange(mode) },
                                shape = SegmentedButtonDefaults.itemShape(
                                    index = index,
                                    count = FocusMode.entries.size,
                                ),
                                colors = SegmentedButtonDefaults.colors(
                                    activeContainerColor = Primary500,
                                    inactiveContainerColor = DarkCard,
                                ),
                            ) {
                                Text(mode.label, fontSize = 12.sp)
                            }
                        }
                    }
                }

                // HDR
                SettingsToggleRow(
                    label = "HDR",
                    checked = uiState.hdrEnabled,
                    onToggle = onToggleHdr,
                )
            }

            // ADVANCED section
            SettingsSection(title = "Advanced") {
                SettingsToggleRow(
                    label = "Keep Screen Awake",
                    checked = uiState.keepScreenAwake,
                    onToggle = onToggleKeepScreenAwake,
                )
                SettingsToggleRow(
                    label = "Battery Saver",
                    checked = uiState.batterySaver,
                    onToggle = onToggleBatterySaver,
                )
                SettingsToggleRow(
                    label = "Auto Reconnect",
                    checked = uiState.autoReconnect,
                    onToggle = onToggleAutoReconnect,
                )
                SettingsToggleRow(
                    label = "Start Streaming On Boot",
                    checked = uiState.startOnBoot,
                    onToggle = onToggleStartOnBoot,
                )
                SettingsToggleRow(
                    label = "Lock Orientation",
                    checked = uiState.lockOrientation,
                    onToggle = onToggleLockOrientation,
                )
            }

            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

@Composable
private fun SettingsSection(
    title: String,
    content: @Composable ColumnScope.() -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text(
            text = title,
            color = Primary500,
            fontSize = 14.sp,
            fontWeight = FontWeight.Bold,
        )
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(
                containerColor = DarkCard,
            ),
            shape = RoundedCornerShape(12.dp),
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                content()
            }
        }
    }
}

@Composable
private fun SettingsRow(
    label: String,
    content: @Composable RowScope.() -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(
            text = label,
            color = TextSecondary,
            fontSize = 12.sp,
        )
        Row(content = content)
    }
}

@Composable
private fun SettingsToggleRow(
    label: String,
    checked: Boolean,
    onToggle: () -> Unit,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = label,
            color = TextPrimary,
            fontSize = 14.sp,
        )
        Switch(
            checked = checked,
            onCheckedChange = { onToggle() },
            colors = SwitchDefaults.colors(
                checkedThumbColor = TextPrimary,
                checkedTrackColor = Primary500,
                uncheckedThumbColor = TextMuted,
                uncheckedTrackColor = DarkSurface,
            ),
        )
    }
}

@Composable
private fun SettingsTextField(
    label: String,
    value: String,
    onValueChange: (String) -> Unit,
    placeholder: String,
) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(
            text = label,
            color = TextSecondary,
            fontSize = 12.sp,
        )
        OutlinedTextField(
            value = value,
            onValueChange = onValueChange,
            placeholder = { Text(placeholder, color = TextMuted) },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = Primary500,
                unfocusedBorderColor = DarkBorder,
                focusedTextColor = TextPrimary,
                unfocusedTextColor = TextPrimary,
            ),
        )
    }
}
