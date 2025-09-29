#include "SpeedMeasurement.h"
#include "DebugConfig.h"

SpeedMeasurementSystem speedSystem;

SpeedMeasurementSystem::SpeedMeasurementSystem() 
  : segmentCounter(0), lastMeasurementTime(0), currentLaserState(false), 
    previousSensorResponse(false), sensorCalibrationMode(false) {
}

void SpeedMeasurementSystem::enableLaser() {
  currentLaserState = true;
  digitalWrite(PIN_LASER, HIGH);
}

void SpeedMeasurementSystem::disableLaser() {
  currentLaserState = false;
  digitalWrite(PIN_LASER, LOW);
}

bool SpeedMeasurementSystem::isLaserEnabled() const {
  return currentLaserState;
}

void SpeedMeasurementSystem::enableCalibration() {
  sensorCalibrationMode = true;
}

void SpeedMeasurementSystem::disableCalibration() {
  sensorCalibrationMode = false;
}

bool SpeedMeasurementSystem::isCalibrationEnabled() const {
  return sensorCalibrationMode;
}

void SpeedMeasurementSystem::updateSensorReading() {
  if (!isLaserEnabled()) {
    return;
  }
  
  uint16_t sensorValue = readLightSensorValue();
  bool currentResponse = checkObjectDetection(sensorValue);
  
  if (sensorCalibrationMode && calibrationDebugLimiter.shouldPrint()) {
    DEBUG_PRINTLN(sensorValue);
  }
  
  if (currentResponse && !previousSensorResponse) {
    segmentCounter++;
    processSpeedMeasurement();
  }
  
  previousSensorResponse = currentResponse;
}

bool SpeedMeasurementSystem::isSensorDetectingObject() const {
  return previousSensorResponse;
}

void SpeedMeasurementSystem::processSpeedMeasurement() {
  unsigned long currentTime = millis();
  unsigned long elapsedTime = currentTime - lastMeasurementTime;
  
  if (elapsedTime >= SPEED_MEASUREMENT_INTERVAL_MS) {
    unsigned long distanceMm = (segmentCounter * SEGMENT_LENGTH_MM) - ROLLER_SPACING_MM;
    unsigned long speedMmPerSec = (distanceMm * 1000) / elapsedTime;
    
    reportMeasuredSpeed(speedMmPerSec, elapsedTime);
    
    lastMeasurementTime = currentTime;
    segmentCounter = 0;
  }
}

void SpeedMeasurementSystem::resetMeasurementCounter() {
  segmentCounter = 0;
  lastMeasurementTime = millis();
}

uint16_t SpeedMeasurementSystem::readLightSensorValue() {
  return analogRead(PIN_LIGHT_SENSOR);
}

bool SpeedMeasurementSystem::checkObjectDetection(uint16_t sensorValue) {
  static bool detectionState = false;
  
  if (sensorValue < LIGHT_DETECTION_THRESHOLD) {
    detectionState = true;
  } else if (sensorValue > (LIGHT_DETECTION_THRESHOLD + LIGHT_HYSTERESIS)) {
    detectionState = false;
  }
  
  return detectionState;
}

void SpeedMeasurementSystem::reportMeasuredSpeed(unsigned long speedMmPerSec, unsigned long measurementDurationMs) {
  Serial.print(F("{\"speed\":"));
  Serial.print(speedMmPerSec);
  Serial.print(F(",\"segments\":"));
  Serial.print(segmentCounter);
  Serial.print(F(",\"duration\":"));
  Serial.print((float)(measurementDurationMs / 1000.0));
  Serial.println(F("}"));
}

void initializeSpeedMeasurement() {
  speedSystem = SpeedMeasurementSystem();
}
