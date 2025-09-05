// =====================================================
// Project: Speed Meter & Relays Control
// Version: v.1, compiled on __DATE__
// =====================================================
//
// This sketch controls:
//   - A laser + light sensor (LDR) to measure object speed
//   - Two nozzles that can be opened after a programmable delay
//   - A small queue system to remember nozzle actions
//
// Communication is over Serial. Commands are simple:
//   "R0" / "R1" = add nozzle to queue
//   "C0" / "C1" = calibration mode OFF / ON
//   "S0" / "S1" = stop / start laser speed meter
//   "H0"        = show help/config
//   "P0"        = ping (keep alive)
//
// =====================================================

#define Version "\n{\"version\":\"SMnRC queue v.1, " __DATE__ "\", send HI for info\"}"
#define Title   "{\"title\":\"Speed Meter & Relays Control\"}"

#include "func.h"   // extra helpers: config.h, function.h

// -----------------------------------------------------
// SECTION 1. HARDWARE PINS
// -----------------------------------------------------
const uint8_t PIN_LED   = 2;        // Red LED indicator
const uint8_t PIN_LASER = 3;        // Laser diode
const uint8_t PIN_LDR   = A0;       // Light sensor

const uint8_t NOZZLE_COUNT = 2;
const uint8_t PIN_NOZZLE[NOZZLE_COUNT] = {5, 4};   // Relays for nozzles
const bool RELAY_ACTIVE_HIGH = false;              // false = active LOW trigger

// -----------------------------------------------------
// SECTION 2. TIMING AND PARAMETERS
// -----------------------------------------------------
const uint16_t NOZZLE_OPEN_TIME     = 233;   // ms nozzle stays open
const unsigned long SPEED_INTERVAL  = 5000;  // ms window for speed calculation
const unsigned long PING_TIMEOUT    = 25000; // ms max silence before timeout

const uint8_t QUEUE_CAPACITY        = 10;

const uint16_t LDR_THRESHOLD        = 120;   // Sensor cutoff for "beam broken"
const uint16_t LDR_HYSTERESIS       = 30;    // Prevents flicker

const uint8_t ROLLER_WIDTH_MM       = 70;    // mm
const uint8_t GAP_BETWEEN_ROLLERS   = 10;    // mm
const uint8_t SEGMENT_LENGTH_MM     = ROLLER_WIDTH_MM + GAP_BETWEEN_ROLLERS;

// -----------------------------------------------------
// SECTION 3. QUEUE STRUCTURE
// -----------------------------------------------------
struct QueueItem {
  unsigned long timestamp;   // when event was queued
  uint8_t nozzle;            // which nozzle (0 or 1)
};

QueueItem nozzleQueue[QUEUE_CAPACITY];
uint8_t queueSize = 0;

// -----------------------------------------------------
// SECTION 4. SYSTEM STATE VARIABLES
// -----------------------------------------------------
bool laserOn        = false;
bool relayState[NOZZLE_COUNT] = {false};
bool ledOn          = false;
bool timeoutActive  = false;
bool calibrationMode= false;

bool sensorTriggered     = false;
bool lastSensorTriggered = false;

unsigned long lastSpeedCheckTime = 0;
unsigned long lastCommandTime    = 0;

unsigned long nozzleOpenSince[NOZZLE_COUNT] = {0};
unsigned long nozzleDelay[NOZZLE_COUNT]     = {1401, 1950};

unsigned long counter = 0; // for speed measurement

// =====================================================
// SECTION 5. QUEUE FUNCTIONS
// =====================================================
void queuePush(uint8_t nozzle) {
  if (queueSize >= QUEUE_CAPACITY) {
    Serial.println("⚠ Queue full, cannot add nozzle");
    return;
  }
  nozzleQueue[queueSize++] = {millis(), nozzle};

  Serial.print("✅ Added nozzle #");
  Serial.println(nozzle);

  queuePrint();
}

void queuePop(uint8_t index) {
  if (queueSize == 0 || index >= queueSize) {
    Serial.println("⚠ Queue empty or index invalid");
    return;
  }
  for (uint8_t i = index; i < queueSize - 1; i++) {
    nozzleQueue[i] = nozzleQueue[i + 1];
  }
  queueSize--;

  queuePrint();
}

void queuePrint() {
  Serial.print("Queue size = ");
  Serial.print(queueSize);

  for (uint8_t i = 0; i < queueSize; i++) {
    Serial.print(" | nozzle ");
    Serial.print(nozzleQueue[i].nozzle);
  }
  Serial.println();
}

// =====================================================
// SECTION 6. NOZZLE CONTROL
// =====================================================
void updateNozzles() {
  unsigned long now = millis();
  bool changed = false;

  // --- Close expired nozzles ---
  for (uint8_t i = 0; i < NOZZLE_COUNT; i++) {
    if (relayState[i] && (now - nozzleOpenSince[i] >= NOZZLE_OPEN_TIME)) {
      relayState[i] = false;
      changed = true;
      Serial.print("🔒 Nozzle closed #");
      Serial.println(i);
    }
  }

  // --- Open nozzles if ready in queue ---
  for (uint8_t i = 0; i < NOZZLE_COUNT && i < queueSize; i++) {
    if (now - nozzleQueue[i].timestamp > nozzleDelay[nozzleQueue[i].nozzle]) {
      uint8_t noz = nozzleQueue[i].nozzle;
      relayState[noz] = true;
      nozzleOpenSince[noz] = now;
      changed = true;

      Serial.print("🔓 Nozzle open #");
      Serial.print(noz);
      Serial.print(" after delay ");
      Serial.println(nozzleDelay[noz]);

      queuePop(i);
    }
  }

  // --- Apply relay states ---
  if (changed) {
    for (uint8_t i = 0; i < NOZZLE_COUNT; i++) {
      digitalWrite(PIN_NOZZLE[i],
                   RELAY_ACTIVE_HIGH ? relayState[i] : !relayState[i]);
    }
  }
}

// =====================================================
// SECTION 7. SENSOR & SPEED
// =====================================================
void updateSensorAndSpeed() {
  if (!laserOn) return;

  int LDR_value = analogRead(PIN_LDR);

  // Detect beam break with hysteresis
  if (LDR_value < LDR_THRESHOLD) sensorTriggered = true;
  else if (LDR_value > LDR_THRESHOLD + LDR_HYSTERESIS) sensorTriggered = false;

  ledOn = sensorTriggered;

  if (calibrationMode) {
    Serial.println(LDR_value);
  }

  // Count rollers only when beam goes from OFF → ON
  if (sensorTriggered && !lastSensorTriggered) {
    counter++;
    unsigned long now = millis();
    unsigned long elapsed = now - lastSpeedCheckTime;

    if (elapsed >= SPEED_INTERVAL) {
      unsigned long speed_mm_per_s =
        ((counter * SEGMENT_LENGTH_MM - GAP_BETWEEN_ROLLERS) * 1000) / elapsed;

      show_speed(speed_mm_per_s, elapsed);

      lastSpeedCheckTime = now;
      counter = 0;
    }
  }
  lastSensorTriggered = sensorTriggered;
}

// =====================================================
// SECTION 8. SERIAL COMMANDS
// =====================================================
void handleSerial() {
  if (Serial.available() == 0) return;

  String input = Serial.readStringUntil('\n');
  if (input.length() != 2) {
    Serial.print("⚠ Invalid input length: ");
    Serial.println(input.length());
    show_config();
    return;
  }

  bool state = (input[1] == '1');
  bool accepted = false;

  switch (input[0]) {
    case 'R': queuePush(state ? 0 : 1); break;   // relay request
    case 'C': calibrationMode = state; accepted = true; break;
    case 'S': laserOn = state; accepted = true; break;
    case 'H': show_config(); accepted = true; break;
    case 'P': accepted = true; break;            // ping
    default: break;
  }

  if (accepted) {
    Serial.print("{\"");
    Serial.print(input[0]);
    Serial.print("\":");
    Serial.print(state);
    Serial.println("}");

    digitalWrite(PIN_LASER, laserOn);
    lastCommandTime = millis();
    timeoutActive = false;
    ledOn = false;
  }
}

// =====================================================
// SECTION 9. SETUP & LOOP
// =====================================================
void setup() {
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_LASER, OUTPUT);
  pinMode(PIN_LDR, INPUT);

  for (uint8_t i = 0; i < NOZZLE_COUNT; i++) {
    pinMode(PIN_NOZZLE[i], OUTPUT);
    digitalWrite(PIN_NOZZLE[i],
                 RELAY_ACTIVE_HIGH ? relayState[i] : !relayState[i]);
  }

  digitalWrite(PIN_LED, ledOn);
  digitalWrite(PIN_LASER, laserOn);

  Serial.begin(115200);
  Serial.println(Version);
}

void loop() {
  unsigned long now = millis();

  handleSerial();          // process incoming commands
  updateNozzles();         // open/close nozzles as needed
  updateSensorAndSpeed();  // update speed measurement

  // --- timeout check ---
  timeoutActive = (now - lastCommandTime >= PING_TIMEOUT);
  if (timeoutActive) ledOn = true;

  // --- update LED indicator ---
  digitalWrite(PIN_LED, ledOn);

  delay(1); // short pause for stability
}
