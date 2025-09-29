#ifndef SERIAL_COMMUNICATION_H
#define SERIAL_COMMUNICATION_H

#include "Arduino.h"
#include "HardwareConfig.h"

enum CommandType {
  RELAY_CONTROL = 'R',
  CALIBRATION_MODE = 'C', 
  SPEED_MEASUREMENT = 'S',
  SYSTEM_INFO = 'H',
  PING_RESPONSE = 'P'
};

class SerialCommandProcessor {
private:
  unsigned long lastCommandReceivedTime;

public:
  SerialCommandProcessor();
  
  void processIncomingCommands();
  void updateCommandTimeout();
  
  bool hasCommandTimedOut() const;
  void resetCommandTimeout();
  
  void displaySystemConfiguration();
  void displaySystemVersion();

private:
  void processValidCommand(char commandChar, bool commandState);
  void sendCommandAcknowledgment(char commandChar, bool state);
  void handleRelayCommand(bool activateTopNozzle);
  void handleCalibrationCommand(bool enableCalibration);
  void handleSpeedMeasurementCommand(bool enableSpeed);
  void handleSystemInfoCommand();
  void handlePingCommand();
  void reportInvalidCommandLength(int receivedLength);
};

extern SerialCommandProcessor commandProcessor;

void initializeSerialCommunication();

#endif
