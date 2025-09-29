#include "SystemStatus.h"
#include "SpeedMeasurement.h"

SystemStatusManager statusManager;

SystemStatusManager::SystemStatusManager() 
  : statusLedState(false), communicationTimeoutActive(false) {
}

void SystemStatusManager::updateStatusIndicators() {
  bool ledShouldBeActive = shouldStatusLedBeActive();
  
  if (statusLedState != ledShouldBeActive) {
    statusLedState = ledShouldBeActive;
    updatePhysicalStatusLed();
  }
}

void SystemStatusManager::setStatusLed(bool ledOn) {
  statusLedState = ledOn;
  updatePhysicalStatusLed();
}

void SystemStatusManager::handleCommunicationTimeout(bool timeoutActive) {
  communicationTimeoutActive = timeoutActive;
}

bool SystemStatusManager::isStatusLedActive() const {
  return statusLedState;
}

bool SystemStatusManager::hasCommunicationTimeout() const {
  return communicationTimeoutActive;
}

void SystemStatusManager::updatePhysicalStatusLed() {
  digitalWrite(PIN_STATUS_LED, statusLedState ? HIGH : LOW);
}

bool SystemStatusManager::shouldStatusLedBeActive() const {
  if (communicationTimeoutActive) {
    return true;
  }
  
  if (speedSystem.isLaserEnabled() && speedSystem.isSensorDetectingObject()) {
    return true;
  }
  
  return statusLedState;
}

void initializeSystemStatus() {
  statusManager = SystemStatusManager();
  pinMode(PIN_STATUS_LED, OUTPUT);
  statusManager.setStatusLed(false);
}
