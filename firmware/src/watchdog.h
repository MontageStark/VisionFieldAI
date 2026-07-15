#ifndef WATCHDOG_H
#define WATCHDOG_H

#include <esp_task_wdt.h>

class Watchdog {
public:
    bool begin(uint32_t timeout_seconds = 15) {
        esp_task_wdt_config_t wdt_config = {
            .timeout_ms = timeout_seconds * 1000,
            .idle_core_mask = 0,
            .trigger_panic = true
        };
        esp_err_t err = esp_task_wdt_reconfigure(&wdt_config);
        if (err != ESP_OK) {
            err = esp_task_wdt_init(&wdt_config);
        }
        if (err == ESP_OK) {
            err = esp_task_wdt_add(NULL);
        }
        _initialized = (err == ESP_OK);
        return _initialized;
    }

    void feed() {
        if (_initialized) {
            esp_task_wdt_reset();
        }
    }

    bool isInitialized() const { return _initialized; }

private:
    bool _initialized = false;
};

#endif
