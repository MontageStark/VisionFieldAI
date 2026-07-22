package com.fieldvision.camera.di

import android.content.Context
import com.fieldvision.camera.camera.CameraEngine
import com.fieldvision.camera.data.FieldVisionDatabase
import com.fieldvision.camera.device.DeviceTelemetryMonitor
import com.fieldvision.camera.discovery.DiscoveryService
import com.fieldvision.camera.network.NetworkMonitor
import com.fieldvision.camera.stream.StreamServer
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideStreamServer(): StreamServer = StreamServer()

    @Provides
    @Singleton
    fun provideDiscoveryService(): DiscoveryService = DiscoveryService()

    @Provides
    @Singleton
    fun provideNetworkMonitor(
        @ApplicationContext context: Context
    ): NetworkMonitor = NetworkMonitor(context)

    @Provides
    @Singleton
    fun provideCameraEngine(
        @ApplicationContext context: Context
    ): CameraEngine = CameraEngine(context)

    @Provides
    @Singleton
    fun provideDeviceTelemetryMonitor(
        @ApplicationContext context: Context
    ): DeviceTelemetryMonitor = DeviceTelemetryMonitor(context)

    @Provides
    @Singleton
    fun provideDatabase(
        @ApplicationContext context: Context
    ): FieldVisionDatabase = FieldVisionDatabase.create(context)
}
