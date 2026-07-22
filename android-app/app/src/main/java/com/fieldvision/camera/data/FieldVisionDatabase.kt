package com.fieldvision.camera.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(
    entities = [CameraSettingsEntity::class],
    version = 1,
    exportSchema = false,
)
abstract class FieldVisionDatabase : RoomDatabase() {
    abstract fun cameraSettingsDao(): CameraSettingsDao

    companion object {
        fun create(context: Context): FieldVisionDatabase =
            Room.databaseBuilder(
                context.applicationContext,
                FieldVisionDatabase::class.java,
                "fieldvision.db",
            ).build()
    }
}
