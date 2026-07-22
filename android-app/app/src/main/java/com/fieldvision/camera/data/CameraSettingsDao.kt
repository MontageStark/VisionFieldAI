package com.fieldvision.camera.data

import androidx.room.Dao
import androidx.room.Query
import androidx.room.Upsert

@Dao
interface CameraSettingsDao {
    @Query("SELECT * FROM camera_settings WHERE id = 1")
    suspend fun getSettings(): CameraSettingsEntity?

    @Upsert
    suspend fun upsert(settings: CameraSettingsEntity)
}
