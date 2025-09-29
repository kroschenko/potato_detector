#include "RelayController.h"
#include "DebugConfig.h"

NozzleRelayController relayController;

NozzleRelayController::NozzleRelayController() {
  for (uint8_t i = 0; i < NOZZLE_COUNT; i++) {
    nozzleOpenTimestamps[i] = 0;
    nozzleActiveStates[i] = false;
  }
}

void NozzleRelayController::processScheduledActivations() {
  closeExpiredNozzles();
  openReadyNozzles();
}

void NozzleRelayController::updateNozzleStates() {
  static bool previousStates[NOZZLE_COUNT] = {false};
  bool stateChanged = false;
  
  for (uint8_t i = 0; i < NOZZLE_COUNT; i++) {
    if (nozzleActiveStates[i] != previousStates[i]) {
      updatePhysicalRelayState(i);
      previousStates[i] = nozzleActiveStates[i];
      stateChanged = true;
    }
  }
  
  if (stateChanged) {
    DEBUG_PRINTLN("Nozzle states updated");
  }
}

bool NozzleRelayController::isNozzleActive(uint8_t nozzleIndex) const {
  if (nozzleIndex >= NOZZLE_COUNT) return false;
  return nozzleActiveStates[nozzleIndex];
}

void NozzleRelayController::activateNozzle(uint8_t nozzleIndex) {
  if (nozzleIndex >= NOZZLE_COUNT) return;
  
  nozzleActiveStates[nozzleIndex] = true;
  nozzleOpenTimestamps[nozzleIndex] = millis();
  
  DEBUG_PRINT("Nozzle activated #");
  DEBUG_PRINTLN(nozzleIndex);
}

void NozzleRelayController::deactivateNozzle(uint8_t nozzleIndex) {
  if (nozzleIndex >= NOZZLE_COUNT) return;
  
  nozzleActiveStates[nozzleIndex] = false;
  
  DEBUG_PRINT("Nozzle deactivated #");
  DEBUG_PRINTLN(nozzleIndex);
}

void NozzleRelayController::updatePhysicalRelayState(uint8_t nozzleIndex) {
  bool relaySignal = RELAY_ACTIVE_HIGH ? nozzleActiveStates[nozzleIndex] : !nozzleActiveStates[nozzleIndex];
  digitalWrite(PIN_NOZZLE_RELAYS[nozzleIndex], relaySignal);
}

void NozzleRelayController::closeExpiredNozzles() {
  for (uint8_t i = 0; i < NOZZLE_COUNT; i++) {
    if (nozzleActiveStates[i] && hasNozzleTimedOut(i)) {
      deactivateNozzle(i);
    }
  }
}

void NozzleRelayController::openReadyNozzles() {
  for (uint8_t i = 0; (i < NOZZLE_COUNT) && (i < activationQueue.getSize()); i++) {
    const NozzleActivationRequest& request = activationQueue.getRequest(i);
    
    if (isNozzleReadyToOpen(request)) {
      activateNozzle(request.nozzleIndex);
      activationQueue.removeProcessedRequest(i);
      break;
    }
  }
}

bool NozzleRelayController::isNozzleReadyToOpen(const NozzleActivationRequest& request) const {
  unsigned long currentTime = millis();
  unsigned long elapsedTime = currentTime - request.scheduledTime;
  return elapsedTime >= NOZZLE_DELAYS_MS[request.nozzleIndex];
}

bool NozzleRelayController::hasNozzleTimedOut(uint8_t nozzleIndex) const {
  unsigned long currentTime = millis();
  return (currentTime - nozzleOpenTimestamps[nozzleIndex]) >= NOZZLE_OPEN_DURATION_MS;
}

void initializeRelayController() {
  relayController = NozzleRelayController();
  
  for (uint8_t i = 0; i < NOZZLE_COUNT; i++) {
    pinMode(PIN_NOZZLE_RELAYS[i], OUTPUT);
    bool relaySignal = RELAY_ACTIVE_HIGH ? false : true;
    digitalWrite(PIN_NOZZLE_RELAYS[i], relaySignal);
  }
}
