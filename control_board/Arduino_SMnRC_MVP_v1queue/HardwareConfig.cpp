#include "HardwareConfig.h"

void initializeHardwarePins() {
  pinMode(PIN_STATUS_LED, OUTPUT);
  pinMode(PIN_LASER, OUTPUT);
  pinMode(PIN_LIGHT_SENSOR, INPUT);
  
  for (uint8_t i = 0; i < NOZZLE_COUNT; i++) {
    pinMode(PIN_NOZZLE_RELAYS[i], OUTPUT);
  }
  
  digitalWrite(PIN_STATUS_LED, LOW);
  digitalWrite(PIN_LASER, LOW);
  
  for (uint8_t i = 0; i < NOZZLE_COUNT; i++) {
    bool initialState = RELAY_ACTIVE_HIGH ? LOW : HIGH;
    digitalWrite(PIN_NOZZLE_RELAYS[i], initialState);
  }
}
