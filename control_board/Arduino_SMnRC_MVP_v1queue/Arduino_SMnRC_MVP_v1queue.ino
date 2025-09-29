#include "HardwareConfig.h"
#include "QueueManager.h"
#include "SpeedMeasurement.h"
#include "RelayController.h"
#include "SerialCommunication.h"
#include "SystemStatus.h"
#include "DebugConfig.h"


void setup() {
  initializeHardwarePins();
  initializeQueue();
  initializeSpeedMeasurement();
  initializeRelayController();
  initializeSerialCommunication();
  initializeSystemStatus();
}

void loop() {
  commandProcessor.processIncomingCommands();
  commandProcessor.updateCommandTimeout();
  
  relayController.processScheduledActivations();
  relayController.updateNozzleStates();
  
  speedSystem.updateSensorReading();
  
  statusManager.updateStatusIndicators();
  
  delay(1);
}
