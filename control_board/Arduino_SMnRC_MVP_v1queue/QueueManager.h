#ifndef QUEUE_MANAGER_H
#define QUEUE_MANAGER_H

#include "Arduino.h"
#include "HardwareConfig.h"

struct NozzleActivationRequest {
  unsigned long scheduledTime;
  uint8_t nozzleIndex;
};

class NozzleQueue {
private:
  NozzleActivationRequest queueItems[QUEUE_CAPACITY];
  uint8_t currentSize;

public:
  NozzleQueue();
  
  bool addNozzleRequest(uint8_t nozzleIndex);
  void removeProcessedRequest(uint8_t index);
  void displayQueueStatus();
  
  uint8_t getSize() const;
  const NozzleActivationRequest& getRequest(uint8_t index) const;
  bool isEmpty() const;
  bool isFull() const;
};

extern NozzleQueue activationQueue;

void initializeQueue();

#endif
