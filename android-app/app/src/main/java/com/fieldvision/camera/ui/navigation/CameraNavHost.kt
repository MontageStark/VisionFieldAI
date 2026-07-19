package com.fieldvision.camera.ui.navigation

import androidx.compose.runtime.*
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.fieldvision.camera.ui.CameraUiState
import com.fieldvision.camera.ui.CameraViewModel
import com.fieldvision.camera.ui.Screen
import com.fieldvision.camera.ui.screens.*

@Composable
fun CameraNavHost(
    viewModel: CameraViewModel = viewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()
    val navController = rememberNavController()

    // Sync navigation with ViewModel state
    LaunchedEffect(uiState.currentScreen) {
        when (uiState.currentScreen) {
            Screen.Home -> navController.navigate("home") {
                popUpTo("home") { inclusive = true }
            }
            Screen.Streaming -> navController.navigate("streaming") {
                popUpTo("home")
            }
            Screen.LockMode -> navController.navigate("lock") {
                popUpTo("streaming")
            }
            Screen.Settings -> navController.navigate("settings")
            Screen.Calibration -> navController.navigate("calibration")
            Screen.Developer -> navController.navigate("developer")
        }
    }

    NavHost(
        navController = navController,
        startDestination = "home",
    ) {
        composable("home") {
            HomeScreen(
                uiState = uiState,
                onGoLive = { viewModel.goLive() },
                onOpenSettings = { viewModel.navigateTo(Screen.Settings) },
                onStartCalibration = { viewModel.startCalibration() },
                onLongPressLogo = { viewModel.toggleDeveloperScreen() },
            )
        }

        composable("streaming") {
            StreamingScreen(
                uiState = uiState,
                onStopStreaming = {
                    viewModel.stopLive()
                    viewModel.navigateTo(Screen.Home)
                },
                onLockScreen = { viewModel.lockScreen() },
            )
        }

        composable("lock") {
            LockModeScreen(
                uiState = uiState,
                onUnlock = { viewModel.unlockScreen() },
                onStopStreaming = {
                    viewModel.stopLive()
                    viewModel.navigateTo(Screen.Home)
                },
            )
        }

        composable("settings") {
            SettingsScreen(
                uiState = uiState,
                onBack = { viewModel.navigateTo(Screen.Streaming) },
                onResolutionChange = { viewModel.setResolution(it) },
                onFpsChange = { viewModel.setTargetFps(it) },
                onBitrateChange = { viewModel.setTargetBitrate(it) },
                onCodecChange = { viewModel.setCodec(it) },
                onLensChange = { viewModel.setLens(it) },
                onExposureChange = { viewModel.setExposure(it) },
                onWhiteBalanceChange = { viewModel.setWhiteBalance(it) },
                onFocusModeChange = { viewModel.setFocusMode(it) },
                onToggleHdr = { viewModel.toggleHdr() },
                onStreamModeChange = { viewModel.setStreamMode(it) },
                onServerAddressChange = { viewModel.setServerAddress(it) },
                onServerPortChange = { viewModel.setServerPort(it) },
                onToggleKeepScreenAwake = { viewModel.toggleKeepScreenAwake() },
                onToggleBatterySaver = { viewModel.toggleBatterySaver() },
                onToggleAutoReconnect = { viewModel.toggleAutoReconnect() },
                onToggleStartOnBoot = { viewModel.toggleStartOnBoot() },
                onToggleLockOrientation = { viewModel.toggleLockOrientation() },
            )
        }

        composable("calibration") {
            CalibrationScreen(
                uiState = uiState,
                onBack = { viewModel.navigateTo(Screen.Home) },
                onNextStep = { viewModel.setCalibrationStep(it) },
                onComplete = { left, right, center ->
                    viewModel.completeCalibration(left, right, center)
                },
            )
        }

        composable("developer") {
            DeveloperScreen(
                uiState = uiState,
                onBack = { viewModel.toggleDeveloperScreen() },
            )
        }
    }
}
