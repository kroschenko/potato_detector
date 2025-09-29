#include "SerialCommunication.h"
#include "QueueManager.h"
#include "SpeedMeasurement.h"
#include "SystemStatus.h"

SerialCommandProcessor commandProcessor;

SerialCommandProcessor::SerialCommandProcessor() : lastCommandReceivedTime(0) {
}

void SerialCommandProcessor::processIncomingCommands() {
  if (Serial.available() <= 0) {
    return;
  }
  
  String receivedInput = Serial.readStringUntil('\n');
  
  if (receivedInput.length() == 2) {
    char commandChar = receivedInput[0];
    bool commandState = (receivedInput[1] == '1');
    
    processValidCommand(commandChar, commandState);
  } else {
    reportInvalidCommandLength(receivedInput.length());
  }
}

void SerialCommandProcessor::updateCommandTimeout() {
  unsigned long currentTime = millis();
  bool timeoutActive = (currentTime - lastCommandReceivedTime) >= COMMUNICATION_TIMEOUT_MS;
  statusManager.handleCommunicationTimeout(timeoutActive);
}

bool SerialCommandProcessor::hasCommandTimedOut() const {
  unsigned long currentTime = millis();
  return (currentTime - lastCommandReceivedTime) >= COMMUNICATION_TIMEOUT_MS;
}

void SerialCommandProcessor::resetCommandTimeout() {
  lastCommandReceivedTime = millis();
  statusManager.handleCommunicationTimeout(false);
  statusManager.setStatusLed(false);
}

void SerialCommandProcessor::displaySystemConfiguration() {
  Serial.println(SYSTEM_TITLE);
  Serial.println(SYSTEM_VERSION);
  
  Serial.print(F("{\"segment\":"));
  Serial.print(SEGMENT_LENGTH_MM);
  Serial.print(F(",\"measurement_interval\":"));
  Serial.print(SPEED_MEASUREMENT_INTERVAL_MS / 1000);
  Serial.print(F(",\"pin_light_sensor\":"));
  Serial.print(PIN_LIGHT_SENSOR);
  Serial.print(F(",\"pin_status_led\":"));
  Serial.print(PIN_STATUS_LED);
  Serial.print(F(",\"pin_laser\":"));
  Serial.print(PIN_LASER);
  Serial.print(F(",\"pin_nozzle_top\":"));
  Serial.print(PIN_NOZZLE_RELAYS[0]);
  Serial.print(F(",\"pin_nozzle_bottom\":"));
  Serial.print(PIN_NOZZLE_RELAYS[1]);
  Serial.print(F(",\"relay_active_high\":"));
  Serial.print(RELAY_ACTIVE_HIGH);
  Serial.println(F(",\"commands\":\"R1/R0=nozzle top/bottom, S1/S0=speed on/off, H1=help, P1=ping, C1/C0=calibration on/off\"}"));
}

void SerialCommandProcessor::displaySystemVersion() {
  Serial.println(SYSTEM_VERSION);
}

void SerialCommandProcessor::processValidCommand(char commandChar, bool commandState) {
  bool commandProcessed = false;
  
  switch (commandChar) {
    case RELAY_CONTROL:
      handleRelayCommand(commandState);
      commandProcessed = true;
      break;
      
    case CALIBRATION_MODE:
      handleCalibrationCommand(commandState);
      commandProcessed = true;
      break;
      
    case SPEED_MEASUREMENT:
      handleSpeedMeasurementCommand(commandState);
      commandProcessed = true;
      break;
      
    case SYSTEM_INFO:
      handleSystemInfoCommand();
      commandProcessed = true;
      break;
      
    case PING_RESPONSE:
      handlePingCommand();
      commandProcessed = true;
      break;
      
    default:
      break;
  }
  
  if (commandProcessed) {
    sendCommandAcknowledgment(commandChar, commandState);
    resetCommandTimeout();
  }
}

void SerialCommandProcessor::sendCommandAcknowledgment(char commandChar, bool state) {
  Serial.print("{\"");
  Serial.print(commandChar);
  Serial.print("\":");
  Serial.print(state ? "true" : "false");
  Serial.println("}");
}

void SerialCommandProcessor::handleRelayCommand(bool activateTopNozzle) {
  uint8_t nozzleIndex = activateTopNozzle ? 0 : 1;
  activationQueue.addNozzleRequest(nozzleIndex);
}

void SerialCommandProcessor::handleCalibrationCommand(bool enableCalibration) {
  if (enableCalibration) {
    speedSystem.enableCalibration();
  } else {
    speedSystem.disableCalibration();
  }
}

void SerialCommandProcessor::handleSpeedMeasurementCommand(bool enableSpeed) {
  if (enableSpeed) {
    speedSystem.enableLaser();
  } else {
    speedSystem.disableLaser();
  }
}

void SerialCommandProcessor::handleSystemInfoCommand() {
  displaySystemConfiguration();
}

void SerialCommandProcessor::handlePingCommand() {
}

void SerialCommandProcessor::reportInvalidCommandLength(int receivedLength) {
  Serial.print(F("Invalid command length: "));
  Serial.println(receivedLength);
  displaySystemConfiguration();
}

void initializeSerialCommunication() {
  Serial.begin(SERIAL_BAUD_RATE);
  commandProcessor = SerialCommandProcessor();
  commandProcessor.displaySystemVersion();
}
