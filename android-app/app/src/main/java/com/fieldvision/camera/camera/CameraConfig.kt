package com.fieldvision.camera.camera

data class CameraConfig(
    val width: Int = 3840,
    val height: Int = 2160,
    val fps: Int = 30,
    val exposure: Float = 0f,
    val whiteBalance: WhiteBalanceMode = WhiteBalanceMode.AUTO,
    val focusMode: FocusMode = FocusMode.AUTO,
    val torch: Boolean = false
)

enum class WhiteBalanceMode {
    AUTO, DAYLIGHT, CLOUDY, FLUORESCENT, INCANDESCENT
}

enum class FocusMode {
    AUTO, MANUAL
}

data class Resolution(
    val width: Int,
    val height: Int
) {
    companion object {
        val UHD_4K = Resolution(3840, 2160)
        val FHD_1080P = Resolution(1920, 1080)
        val HD_720P = Resolution(1280, 720)
    }
}
