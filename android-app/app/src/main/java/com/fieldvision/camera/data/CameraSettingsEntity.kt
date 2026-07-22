package com.fieldvision.camera.data

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.fieldvision.camera.ui.Codec
import com.fieldvision.camera.ui.Resolution
import com.fieldvision.camera.ui.StreamMode

@Entity(tableName = "camera_settings")
data class CameraSettingsEntity(
    @PrimaryKey val id: Int = 1,
    val resolutionName: String = "R720P",
    val targetFps: Int = 30,
    val targetBitrate: Int = 20,
    val codecName: String = "H264",
    val keepScreenAwake: Boolean = true,
    val batterySaver: Boolean = false,
    val autoReconnect: Boolean = true,
    val streamModeName: String = "RTSP",
) {
    val resolution: Resolution
        get() = Resolution.valueOf(resolutionName)

    val codec: Codec
        get() = Codec.valueOf(codecName)

    val streamMode: StreamMode
        get() = StreamMode.valueOf(streamModeName)
}
