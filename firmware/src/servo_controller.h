#ifndef SERVO_CONTROLLER_H
#define SERVO_CONTROLLER_H

#include <Arduino.h>
#include <ArduinoJson.h>

// DS3235 servo calibration constants
#define DS3235_MIN_PULSE_US 500
#define DS3235_MAX_PULSE_US 2500
#define DS3235_MIN_ANGLE 0.0f
#define DS3235_MAX_ANGLE 180.0f

struct ServoState {
    float currentAngle = 90.0f;
    float targetAngle = 90.0f;
    float minAngle = DS3235_MIN_ANGLE;
    float maxAngle = DS3235_MAX_ANGLE;
    int minPulseUs = DS3235_MIN_PULSE_US;
    int maxPulseUs = DS3235_MAX_PULSE_US;
    int gpioPin = 0;
};

class ServoController {
public:
    bool begin(int panPin = 13, int tiltPin = 12) {
        _pan.gpioPin = panPin;
        _tilt.gpioPin = tiltPin;

        _pan.minAngle = DS3235_MIN_ANGLE;
        _pan.maxAngle = DS3235_MAX_ANGLE;
        _pan.targetAngle = 90.0f;
        _pan.currentAngle = 90.0f;

        _tilt.minAngle = DS3235_MIN_ANGLE;
        _tilt.maxAngle = DS3235_MAX_ANGLE;
        _tilt.targetAngle = 90.0f;
        _tilt.currentAngle = 90.0f;

        ledcAttach(panPin, 50, 16);
        ledcAttach(tiltPin, 50, 16);

        _writeServo(_pan);
        _writeServo(_tilt);

        Serial.printf("[Servo] Initialized pan=GPIO%d tilt=GPIO%d\n", panPin, tiltPin);
        return true;
    }

    void setAngles(float panAngle, float tiltAngle, float transitionTime = 0.5f) {
        _pan.targetAngle = constrain(panAngle, _pan.minAngle, _pan.maxAngle);
        _tilt.targetAngle = constrain(tiltAngle, _tilt.minAngle, _tilt.maxAngle);
        _transitionTimeMs = (uint32_t)(transitionTime * 1000.0f);
        _transitionStartMs = millis();
        _panStartAngle = _pan.currentAngle;
        _tiltStartAngle = _tilt.currentAngle;
    }

    void emergencyStop() {
        _pan.targetAngle = _pan.currentAngle;
        _tilt.targetAngle = _tilt.currentAngle;
        _emergencyStopped = true;
    }

    void clearEmergencyStop() {
        _emergencyStopped = false;
    }

    bool isEmergencyStopped() const {
        return _emergencyStopped;
    }

    void update() {
        if (_emergencyStopped) return;

        if (_transitionTimeMs > 0) {
            uint32_t elapsed = millis() - _transitionStartMs;
            float progress = min(1.0f, (float)elapsed / (float)_transitionTimeMs);
            float eased = _easeInOutQuad(progress);

            _pan.currentAngle = _panStartAngle + (_pan.targetAngle - _panStartAngle) * eased;
            _tilt.currentAngle = _tiltStartAngle + (_tilt.targetAngle - _tiltStartAngle) * eased;

            if (progress >= 1.0f) {
                _transitionTimeMs = 0;
            }
        } else {
            _pan.currentAngle = _pan.targetAngle;
            _tilt.currentAngle = _tilt.targetAngle;
        }

        _writeServo(_pan);
        _writeServo(_tilt);
    }

    void getPosition(JsonDocument& doc) {
        doc["pan_angle"] = round(_pan.currentAngle * 10.0f) / 10.0f;
        doc["tilt_angle"] = round(_tilt.currentAngle * 10.0f) / 10.0f;
        doc["timestamp"] = millis();
    }

    float getPanAngle() const { return _pan.currentAngle; }
    float getTiltAngle() const { return _tilt.currentAngle; }

private:
    ServoState _pan;
    ServoState _tilt;

    uint32_t _transitionTimeMs = 0;
    uint32_t _transitionStartMs = 0;
    float _panStartAngle = 90.0f;
    float _tiltStartAngle = 90.0f;
    bool _emergencyStopped = false;

    float _easeInOutQuad(float t) {
        return t < 0.5f ? 2.0f * t * t : 1.0f - (-2.0f * t + 2.0f) * (-2.0f * t + 2.0f) / 2.0f;
    }

    void _writeServo(ServoState& servo) {
        float angle = constrain(servo.currentAngle, servo.minAngle, servo.maxAngle);
        uint32_t pulseUs = servo.minPulseUs +
            (uint32_t)((angle - servo.minAngle) / (servo.maxAngle - servo.minAngle) *
                       (servo.maxPulseUs - servo.minPulseUs));

        uint32_t duty = (pulseUs * 65535UL) / 20000UL;
        ledcWrite(servo.gpioPin, duty);
    }
};

#endif
