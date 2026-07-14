#include <Arduino.h>
#include "wifi_manager.h"
#include "websocket_client.h"
#include "servo_controller.h"
#include "watchdog.h"
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

// Configuration
#define WIFI_SSID         "YOUR_WIFI_SSID"
#define WIFI_PASSWORD     "YOUR_WIFI_PASSWORD"
#define WS_HOST           "192.168.1.100"
#define WS_PORT           8080
#define WS_PATH           "/ws/esp32"

#define PIN_PAN_SERVO     13
#define PIN_TILT_SERVO    12
#define PIN_EMERGENCY_STOP 25
#define PIN_MANUAL_OVERRIDE 26

#define SERIAL_BAUD       115200
#define WATCHDOG_TIMEOUT  15
#define STATUS_INTERVAL   1000
#define FEEDBACK_INTERVAL 100
#define DEBOUNCE_INTERVAL_MS 250
#define EMERGENCY_LOG_INTERVAL_MS 500

// Global objects
WiFiManager wifiManager;
WebSocketClient wsClient;
ServoController servoController;
Watchdog watchdog;

// State
volatile bool emergencyStopPressed = false;
volatile bool manualOverrideActive = false;
volatile uint32_t lastEmergencyPress = 0;
volatile uint32_t lastOverridePress = 0;
uint32_t lastStatusTime = 0;
uint32_t lastFeedbackTime = 0;
bool configured = false;
bool servoSafeMode = false;

// ISR: Emergency stop button
void IRAM_ATTR emergencyStopISR() {
    uint32_t now = millis();
    if (now - lastEmergencyPress > DEBOUNCE_INTERVAL_MS) {
        emergencyStopPressed = !emergencyStopPressed;
        lastEmergencyPress = now;
    }
}

// ISR: Manual override button
void IRAM_ATTR manualOverrideISR() {
    uint32_t now = millis();
    if (now - lastOverridePress > DEBOUNCE_INTERVAL_MS) {
        manualOverrideActive = !manualOverrideActive;
        lastOverridePress = now;
    }
}

// WebSocket command handler
void handleServoCommand(const JsonDocument& doc) {
    if (servoSafeMode) {
        Serial.println("[Main] Servo safe mode active, ignoring command");
        return;
    }
    if (manualOverrideActive) {
        Serial.println("[Main] Manual override active, ignoring command");
        return;
    }
    if (emergencyStopPressed) {
        Serial.println("[Main] Emergency stop active, ignoring command");
        return;
    }

    float panAngle = doc["pan_angle"] | 90.0f;
    float tiltAngle = doc["tilt_angle"] | 90.0f;
    float transitionTime = doc["transition_time"] | 0.5f;

    Serial.printf("[Main] Command: pan=%.1f tilt=%.1f t=%.2f\n",
                  panAngle, tiltAngle, transitionTime);

    servoController.setAngles(panAngle, tiltAngle, transitionTime);
}

// Send position feedback
void sendPositionFeedback() {
    StaticJsonDocument<128> feedback;
    feedback["type"] = "servo_position";
    servoController.getPosition(feedback);
    wsClient.sendMessage(feedback);
}

// Send periodic status
void sendStatus() {
    StaticJsonDocument<256> status;
    status["type"] = "device_status";
    status["wifi_rssi"] = wifiManager.signalStrength();
    status["ws_connected"] = wsClient.isConnected();
    status["emergency_stop"] = emergencyStopPressed;
    status["manual_override"] = manualOverrideActive;
    status["uptime_ms"] = millis();
    status["free_heap"] = ESP.getFreeHeap();
    wsClient.sendMessage(status);
}

void setup() {
    Serial.begin(SERIAL_BAUD);
    delay(100);

    Serial.println("\n========================================");
    Serial.println("  FieldVision AI - ESP32 Firmware v1.0.0");
    Serial.println("========================================\n");

    // Initialize watchdog
    if (!watchdog.begin(WATCHDOG_TIMEOUT)) {
        Serial.println("[Main] WARNING: Watchdog init failed!");
    }

    // Configure button pins
    pinMode(PIN_EMERGENCY_STOP, INPUT_PULLUP);
    pinMode(PIN_MANUAL_OVERRIDE, INPUT_PULLUP);

    // Attach ISRs
    attachInterrupt(digitalPinToInterrupt(PIN_EMERGENCY_STOP), emergencyStopISR, FALLING);
    attachInterrupt(digitalPinToInterrupt(PIN_MANUAL_OVERRIDE), manualOverrideISR, FALLING);

    // Initialize servo controller
    if (!servoController.begin(PIN_PAN_SERVO, PIN_TILT_SERVO)) {
        Serial.println("[Main] ERROR: Servo init failed! Entering safe mode.");
        servoSafeMode = true;
    }

    // Connect WiFi
    if (!wifiManager.begin(WIFI_SSID, WIFI_PASSWORD)) {
        Serial.println("[Main] WiFi connection pending...");
    }

    // Initialize WebSocket
    wsClient.begin(WS_HOST, WS_PORT, WS_PATH);
    wsClient.onCommand(handleServoCommand);

    Serial.println("[Main] Setup complete. Entering main loop.\n");
}

void loop() {
    uint32_t now = millis();

    // Feed watchdog
    watchdog.feed();

    // Update components
    wifiManager.update();
    wsClient.update();
    if (!servoSafeMode) {
        servoController.update();
    }

    // Handle emergency stop
    if (emergencyStopPressed) {
        servoController.emergencyStop();
        if (now - lastStatusTime > EMERGENCY_LOG_INTERVAL_MS) {
            Serial.println("[Main] EMERGENCY STOP ACTIVE");
        }
    } else if (servoController.isEmergencyStopped()) {
        servoController.clearEmergencyStop();
        Serial.println("[Main] Emergency stop released");
    }

    // Send position feedback
    if (now - lastFeedbackTime >= FEEDBACK_INTERVAL) {
        lastFeedbackTime = now;
        sendPositionFeedback();
    }

    // Send periodic status
    if (now - lastStatusTime >= STATUS_INTERVAL) {
        lastStatusTime = now;
        sendStatus();
    }

    // Log manual override state changes
    static bool lastOverride = false;
    if (manualOverrideActive != lastOverride) {
        lastOverride = manualOverrideActive;
        Serial.printf("[Main] Manual override %s\n",
                      manualOverrideActive ? "ACTIVATED" : "deactivated");
    }

    vTaskDelay(pdMS_TO_TICKS(1));
}
