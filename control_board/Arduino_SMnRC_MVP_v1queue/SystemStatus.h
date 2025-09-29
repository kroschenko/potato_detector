#ifndef SYSTEM_STATUS_H
#define SYSTEM_STATUS_H

#include "Arduino.h"
#include "HardwareConfig.h"

class SystemStatusManager {
private:
  bool statusLedState;
  bool communicationTimeoutActive;

public:
  SystemStatusManager();
  
  void updateStatusIndicators();
  void setStatusLed(bool ledOn);
  void handleCommunicationTimeout(bool timeoutActive);
  
  bool isStatusLedActive() const;
  bool hasCommunicationTimeout() const;

private:
  void updatePhysicalStatusLed();
  bool shouldStatusLedBeActive() const;
};

extern SystemStatusManager statusManager;

void initializeSystemStatus();

#endif
