#include "QueueManager.h"
#include "DebugConfig.h"

NozzleQueue activationQueue;

NozzleQueue::NozzleQueue() : currentSize(0) {
}

bool NozzleQueue::addNozzleRequest(uint8_t nozzleIndex) {
  if (isFull()) {
    DEBUG_PRINTLN("Queue is full, cannot add request");
    return false;
  }
  
  if (nozzleIndex >= NOZZLE_COUNT) {
    DEBUG_PRINTLN("Invalid nozzle index");
    return false;
  }
  
  queueItems[currentSize].scheduledTime = millis();
  queueItems[currentSize].nozzleIndex = nozzleIndex;
  currentSize++;
  
  DEBUG_PRINT("Added nozzle request #");
  DEBUG_PRINTLN(nozzleIndex);
  
  displayQueueStatus();
  return true;
}

void NozzleQueue::removeProcessedRequest(uint8_t index) {
  if (isEmpty() || index >= currentSize) {
    DEBUG_PRINTLN("Cannot remove: queue empty or invalid index");
    return;
  }
  
  for (uint8_t i = index; i < currentSize - 1; i++) {
    queueItems[i] = queueItems[i + 1];
  }
  
  currentSize--;
  displayQueueStatus();
}

void NozzleQueue::displayQueueStatus() {
  String message = "Queue size: " + String(currentSize);
  for (uint8_t i = 0; i < currentSize; i++) {
    message += "; Nozzle " + String(queueItems[i].nozzleIndex);
  }
  DEBUG_PRINTLN(message);
}

uint8_t NozzleQueue::getSize() const {
  return currentSize;
}

const NozzleActivationRequest& NozzleQueue::getRequest(uint8_t index) const {
  return queueItems[index];
}

bool NozzleQueue::isEmpty() const {
  return currentSize == 0;
}

bool NozzleQueue::isFull() const {
  return currentSize >= QUEUE_CAPACITY;
}

void initializeQueue() {
  activationQueue = NozzleQueue();
}
