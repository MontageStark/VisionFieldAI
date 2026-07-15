#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <WiFi.h>

class WiFiManager {
public:
    bool begin(const char* ssid, const char* password) {
        _ssid = ssid;
        _password = password;

        WiFi.mode(WIFI_STA);
        WiFi.setSleep(false);
        WiFi.setAutoReconnect(true);

        Serial.printf("[WiFi] Connecting to %s...\n", _ssid);
        WiFi.begin(_ssid, _password);

        uint32_t start = millis();
        while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) {
            delay(100);
        }

        if (WiFi.status() == WL_CONNECTED) {
            Serial.printf("[WiFi] Connected. IP: %s\n", WiFi.localIP().toString().c_str());
            return true;
        }

        Serial.println("[WiFi] Connection failed. Will retry in background.");
        return false;
    }

    bool isConnected() const {
        return WiFi.status() == WL_CONNECTED;
    }

    String localIP() const {
        return WiFi.localIP().toString();
    }

    void reconnect() {
        if (WiFi.status() != WL_CONNECTED) {
            Serial.println("[WiFi] Attempting reconnect...");
            WiFi.disconnect();
            delay(100);
            WiFi.begin(_ssid, _password);
        }
    }

    void update() {
        static uint32_t lastReconnectAttempt = 0;
        uint32_t now = millis();

        if (!isConnected() && (now - lastReconnectAttempt > 10000)) {
            lastReconnectAttempt = now;
            reconnect();
        }
    }

    int signalStrength() const {
        return WiFi.RSSI();
    }

private:
    const char* _ssid = nullptr;
    const char* _password = nullptr;
};

#endif
