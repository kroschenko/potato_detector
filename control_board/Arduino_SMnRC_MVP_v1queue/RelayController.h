#ifndef RELAY_CONTROLLER_H
#define RELAY_CONTROLLER_H

#include "Arduino.h"
#include "HardwareConfig.h"
#include "QueueManager.h"

class NozzleRelayController {
private:
  unsigned long nozzleOpenTimestamps[NOZZLE_COUNT];
  bool nozzleActiveStates[NOZZLE_COUNT];

public:
  NozzleRelayController();
  
  void processScheduledActivations();
  void updateNozzleStates();
  
  bool isNozzleActive(uint8_t nozzleIndex) const;
  void activateNozzle(uint8_t nozzleIndex);
  void deactivateNozzle(uint8_t nozzleIndex);
  
private:
  void updatePhysicalRelayState(uint8_t nozzleIndex);
  void closeExpiredNozzles();
  void openReadyNozzles();
  bool isNozzleReadyToOpen(const NozzleActivationRequest& request) const;
  bool hasNozzleTimedOut(uint8_t nozzleIndex) const;
};

extern NozzleRelayController relayController;

void initializeRelayController();

#endif
