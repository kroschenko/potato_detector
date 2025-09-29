#ifndef SPEED_MEASUREMENT_H
#define SPEED_MEASUREMENT_H

#include "Arduino.h"
#include "HardwareConfig.h"

class SpeedMeasurementSystem {
private:
  unsigned long segmentCounter;
  unsigned long lastMeasurementTime;
  bool currentLaserState;
  bool previousSensorResponse;
  bool sensorCalibrationMode;

public:
  SpeedMeasurementSystem();
  
  void enableLaser();
  void disableLaser();
  bool isLaserEnabled() const;
  
  void enableCalibration();
  void disableCalibration();
  bool isCalibrationEnabled() const;
  
  void updateSensorReading();
  bool isSensorDetectingObject() const;
  
  void processSpeedMeasurement();
  void resetMeasurementCounter();
  
private:
  uint16_t readLightSensorValue();
  bool checkObjectDetection(uint16_t sensorValue);
  void reportMeasuredSpeed(unsigned long speedMmPerSec, unsigned long measurementDurationMs);
};

extern SpeedMeasurementSystem speedSystem;

void initializeSpeedMeasurement();

#endif
