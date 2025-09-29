#ifndef DEBUG_CONFIG_H
#define DEBUG_CONFIG_H

#define DEBUG_MODE_ENABLED true
#define DEBUG_CALIBRATION_RATE_LIMIT 100

#if DEBUG_MODE_ENABLED
  #define DEBUG_PRINT(x) Serial.print(x)
  #define DEBUG_PRINTLN(x) Serial.println(x)
  #define DEBUG_PRINTF(format, ...) Serial.printf(format, __VA_ARGS__)
#else
  #define DEBUG_PRINT(x)
  #define DEBUG_PRINTLN(x)
  #define DEBUG_PRINTF(format, ...)
#endif

class RateLimitedDebug {
private:
  unsigned long lastPrintTime;
  unsigned int printCounter;
  unsigned int printInterval;

public:
  RateLimitedDebug(unsigned int interval = DEBUG_CALIBRATION_RATE_LIMIT) 
    : lastPrintTime(0), printCounter(0), printInterval(interval) {}
  
  bool shouldPrint() {
    printCounter++;
    if (printCounter >= printInterval) {
      printCounter = 0;
      return true;
    }
    return false;
  }
};

extern RateLimitedDebug calibrationDebugLimiter;

#endif
