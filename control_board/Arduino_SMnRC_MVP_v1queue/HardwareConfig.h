#ifndef HARDWARE_CONFIG_H
#define HARDWARE_CONFIG_H

#include "Arduino.h"

const char* const SYSTEM_VERSION = "\n{\"version\":\"SMnRC queue v.1, " __DATE__ "\", send HI for info\"}";
const char* const SYSTEM_TITLE = "{\"title\":\"Speed Meter & Relays Control\"}";

const uint8_t PIN_STATUS_LED = 2;
const uint8_t PIN_LASER = 3;
const uint8_t PIN_LIGHT_SENSOR = A0;

const uint8_t NOZZLE_COUNT = 2;
const uint8_t PIN_NOZZLE_RELAYS[NOZZLE_COUNT] = {5, 4};
const bool RELAY_ACTIVE_HIGH = false;

const uint16_t NOZZLE_OPEN_DURATION_MS = 100;
const uint16_t NOZZLE_DELAY_TOP_MS = 460;
const uint16_t NOZZLE_DELAY_BOTTOM_MS = 690;
const uint16_t NOZZLE_DELAYS_MS[NOZZLE_COUNT] = {NOZZLE_DELAY_TOP_MS, NOZZLE_DELAY_BOTTOM_MS};

const uint16_t LIGHT_DETECTION_THRESHOLD = 120;
const uint16_t LIGHT_HYSTERESIS = 30;

const uint8_t ROLLER_WIDTH_MM = 70;
const uint8_t ROLLER_SPACING_MM = 10;
const uint8_t SEGMENT_LENGTH_MM = ROLLER_WIDTH_MM + ROLLER_SPACING_MM;

const unsigned long SPEED_MEASUREMENT_INTERVAL_MS = 5000;
const unsigned long COMMUNICATION_TIMEOUT_MS = 25000;

const uint8_t QUEUE_CAPACITY = 20;

const uint32_t SERIAL_BAUD_RATE = 115200;

void initializeHardwarePins();

#endif
