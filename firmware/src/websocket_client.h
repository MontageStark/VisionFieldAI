#ifndef WEBSOCKET_CLIENT_H
#define WEBSOCKET_CLIENT_H

#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <functional>

class WebSocketClient {
public:
    using CommandCallback = std::function<void(const JsonDocument&)>;

    bool begin(const char* host, uint16_t port, const char* path = "/ws/esp32") {
        _host = host;
        _port = port;
        _path = path;

        _webSocket.begin(host, port, path);
        _webSocket.onEvent([this](WStype_t type, uint8_t* payload, size_t length) {
            _onEvent(type, payload, length);
        });
        _webSocket.setReconnectInterval(5000);
        _webSocket.enableHeartbeat(15000, 10000, 3);

        Serial.printf("[WS] Connecting to ws://%s:%d%s\n", host, port, path);
        return true;
    }

    void update() {
        _webSocket.loop();
    }

    void onCommand(CommandCallback callback) {
        _commandCallback = callback;
    }

    void sendMessage(const JsonDocument& doc) {
        if (_webSocket.isConnected()) {
            String json;
            serializeJson(doc, json);
            _webSocket.sendTXT(json);
        }
    }

    bool isConnected() const {
        return _webSocket.isConnected();
    }

    void disconnect() {
        _webSocket.disconnect();
    }

private:
    WebSocketsClient _webSocket;
    const char* _host = nullptr;
    uint16_t _port = 8080;
    const char* _path = "/ws/esp32";
    CommandCallback _commandCallback = nullptr;

    void _onEvent(WStype_t type, uint8_t* payload, size_t length) {
        switch (type) {
            case WStype_DISCONNECTED:
                Serial.println("[WS] Disconnected");
                break;

            case WStype_CONNECTED:
                Serial.println("[WS] Connected");
                _sendRegistration();
                break;

            case WStype_TEXT: {
                StaticJsonDocument<1024> doc;
                DeserializationError err = deserializeJson(doc, payload, length);
                if (err) {
                    Serial.printf("[WS] JSON parse error: %s\n", err.c_str());
                    return;
                }
                _handleMessage(doc);
                break;
            }

            case WStype_ERROR:
                Serial.printf("[WS] Error: %.*s\n", length, payload);
                break;

            default:
                break;
        }
    }

    void _handleMessage(const JsonDocument& doc) {
        const char* type = doc["type"];
        if (!type) return;

        if (strcmp(type, "servo_command") == 0) {
            if (_commandCallback) {
                _commandCallback(doc);
            }
        } else if (strcmp(type, "ping") == 0) {
            StaticJsonDocument<64> pong;
            pong["type"] = "pong";
            pong["timestamp"] = millis();
            sendMessage(pong);
        } else if (strcmp(type, "config_update") == 0) {
            Serial.printf("[WS] Config update received\n");
        }
    }

    void _sendRegistration() {
        StaticJsonDocument<128> reg;
        reg["type"] = "register";
        reg["device"] = "esp32";
        reg["firmware_version"] = "1.0.0";
        sendMessage(reg);
    }
};

#endif
