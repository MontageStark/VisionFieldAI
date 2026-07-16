package com.fieldvision.camera.stream

import android.graphics.Bitmap
import java.io.ByteArrayOutputStream
import java.io.OutputStream

class MjpegStream(private val output: OutputStream) {
    
    @Volatile
    private var isStreaming = false
    
    fun start() {
        isStreaming = true
        
        // Send multipart header
        val header = "HTTP/1.1 200 OK\r\n" +
                "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n" +
                "Cache-Control: no-cache\r\n" +
                "Connection: close\r\n\r\n"
        output.write(header.toByteArray())
        output.flush()
    }
    
    fun sendFrame(bitmap: Bitmap) {
        if (!isStreaming) return
        
        try {
            // Convert bitmap to JPEG
            val stream = ByteArrayOutputStream()
            bitmap.compress(Bitmap.CompressFormat.JPEG, 85, stream)
            val jpegData = stream.toByteArray()
            
            // Send frame
            val frameHeader = "--frame\r\n" +
                    "Content-Type: image/jpeg\r\n" +
                    "Content-Length: ${jpegData.size}\r\n\r\n"
            output.write(frameHeader.toByteArray())
            output.write(jpegData)
            output.write("\r\n".toByteArray())
            output.flush()
        } catch (e: Exception) {
            isStreaming = false
        }
    }
    
    fun stop() {
        isStreaming = false
        try {
            output.close()
        } catch (e: Exception) {
            // Ignore
        }
    }
}
