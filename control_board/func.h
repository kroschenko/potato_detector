#ifndef func_hpp
#define func_hpp
#include "Arduino.h" 

unsigned long counter = 0; // Counter rollers
extern uint8_t length_one_segment;
extern const long interval;
extern uint8_t pin_RED_LED;
extern uint8_t pin_LASER;
extern uint8_t pin_LDR;
extern uint8_t pin_RELAY[];
extern bool relay_high_level_trigger;

void show_speed(unsigned long speed, unsigned long T) {
  Serial.print(F("{\"speed\":"));
  Serial.print(speed);
  Serial.print(F(",\"breaks\":"));
  Serial.print(counter);
  Serial.print(F(",\"duration\":"));
  Serial.print((float)(T/1000));
  Serial.println(F("}"));
}

void show_config() {
  Serial.println(Title);
  Serial.println(Version);
  Serial.print(F("{\"segment\":"));
  Serial.print(length_one_segment);
  Serial.print(F(",\"T\":"));
  Serial.print(interval/1000);
  Serial.print(F(",\"pin_LDR\":"));
  Serial.print(pin_LDR);
  Serial.print(F(",\"pin_RED_LED\":"));
  Serial.print(pin_RED_LED);
  Serial.print(F(",\"pin_LASER\":"));
  Serial.print(pin_LASER);
  Serial.print(F(",\"pin_RELAY_TOP\":"));
  Serial.print(pin_RELAY[0]);
  Serial.print(F(",\"pin_RELAY_BOTTOM\":"));
  Serial.print(pin_RELAY[1]);
  Serial.print(F(",\"relay_high_level_trigger\":"));
  Serial.print(relay_high_level_trigger);

  Serial.println(F(",\"info\":\"T1/B1 - top/bottom relay on; S0/S1 - speed meter off/on; HI - show this info; P1 - ping for timeout control; C1 - calibration LDR ON, but need S1 ON;\"}"));  
}

#endif
