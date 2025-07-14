#define Version "\n{\"version\":\"SMnRC MVP.1, " __DATE__ "\",\"help\":\"send HI for info\"}"
#define Title "{\"title\":\"Speed Meter & Relays Control\"}"
uint8_t pin_RED_LED=2;
uint8_t pin_LASER=3;
uint8_t pin_LDR=A0;
uint8_t pin_RELAY_TOP=4;
uint8_t pin_RELAY_BOTTOM=5;
bool relay_high_level_trigger = false; // false for low level trigger;

uint16_t duration_nozzle_open = 363; // duration of open nozzle
const long interval = 5000;
const long timeout_interval = 25000; // wait ping interval;

uint16_t threshold_response = 120;
uint16_t hysteresis = 30;
uint8_t roller_width = 70; // D, mm
uint8_t space_between_rollers = 10; // mm
uint8_t length_one_segment = roller_width + space_between_rollers;

bool response = false;
bool previous_state = false;
unsigned long counter = 0; // Counter rollers
unsigned long previousMillis = 0;
unsigned long last_command_time = 0;
unsigned long nozzle_top_open = 0;
unsigned long nozzle_bottom_open = 0;
bool laser_state = 0;
bool relay_top_state = 0;
bool relay_bottom_state = 0;
bool red_LED = 0;
bool timeout = 0; 
bool calibration = false;

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
  Serial.print(pin_RELAY_TOP);
  Serial.print(F(",\"pin_RELAY_BOTTOM\":"));
  Serial.print(pin_RELAY_BOTTOM);
  Serial.print(F(",\"relay_high_level_trigger\":"));
  Serial.print(relay_high_level_trigger);

  Serial.println(F(",\"info\":\"T1/B1 - top/bottom relay on; S0/S1 - speed meter off/on; HI - show this info; P1 - ping for timeout control; C1 - calibration LDR ON, but need S1 ON;\"}"));  
}

void show_speed(unsigned long speed, unsigned long T) {
  Serial.print(F("{\"speed\":"));
  Serial.print(speed);
  Serial.print(F(",\"breaks\":"));
  Serial.print(counter);
  Serial.print(F(",\"duration\":"));
  Serial.print((float)(T/1000));
  Serial.println(F("}"));
}

void setup() {
  pinMode(pin_RED_LED, OUTPUT);
  pinMode(pin_LASER, OUTPUT);
  pinMode(pin_LDR, INPUT);
  pinMode(pin_RELAY_TOP, OUTPUT);
  pinMode(pin_RELAY_BOTTOM, OUTPUT);
  digitalWrite(pin_RED_LED, red_LED);
  digitalWrite(pin_LASER, laser_state);
  if (relay_high_level_trigger) {
    digitalWrite(pin_RELAY_TOP, relay_top_state);
    digitalWrite(pin_RELAY_BOTTOM, relay_bottom_state);
  } else {
    digitalWrite(pin_RELAY_TOP, !relay_top_state);
    digitalWrite(pin_RELAY_BOTTOM, !relay_bottom_state);
  }  
  Serial.begin(115200);
  Serial.println(Version);  
}

void loop() {
  // Serial command reader
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    if (input.length() == 2) {
      bool state = 0;
      bool set = 0;      
      if (input[1]=='1')
        state = 1;
        
      switch (input[0]) {
        case 'B': relay_top_state = true; set = 1; nozzle_top_open = millis(); break; // Reley Top
        case 'T': relay_bottom_state = true; set = 1; nozzle_bottom_open = millis(); break; // Relay Bottom
        case 'S': laser_state = state; set = 1; break; // Speed on/off
        case 'C': calibration = state; set = 1; break; // Calibration LDR
        case 'H': show_config(); set = 1; break; // Show configuration info (Help)
        case 'P': set = 1; break; // Ping received
        default:
        break;
      }
      
      // command accepted
      if (set) {
        Serial.print("{\"");
        Serial.print(input[0]);
        Serial.print("\":");
        Serial.print(state);
        Serial.println("}");
        digitalWrite(pin_LASER, laser_state);        
        last_command_time = millis();    
        timeout = 0;
        red_LED = false;
      }
    } else {
      Serial.print(F("Failed, length obtained: "));
      Serial.println(input.length());
      show_config();
    }
  } // finish: Serial command reader

  unsigned long currentMillis = millis();

  if ( (relay_top_state) && (currentMillis - nozzle_top_open >= duration_nozzle_open) )
      relay_top_state = false;

  if ( (relay_bottom_state) && (currentMillis - nozzle_bottom_open >= duration_nozzle_open) )
      relay_bottom_state = false;
          
  if (relay_high_level_trigger) {
    digitalWrite(pin_RELAY_TOP, relay_top_state);
    digitalWrite(pin_RELAY_BOTTOM, relay_bottom_state);
  } else {
    digitalWrite(pin_RELAY_TOP, !relay_top_state);
    digitalWrite(pin_RELAY_BOTTOM, !relay_bottom_state);
  }




  // Speed couunter, Laser ON
  if (laser_state) {
    int LDR_value = analogRead(pin_LDR);
    if (LDR_value < threshold_response) 
      response = true;
    // hysteresis    
    else if (LDR_value > (threshold_response + hysteresis)) {
      response = false;
    }
    red_LED = response;

    if (calibration) 
      Serial.println(LDR_value);

    // only when the laser signal reaches
    if ((response!=previous_state) && (response==true) ) {
      counter++;

      unsigned long T = currentMillis - previousMillis;
      if (T >= interval) {
        unsigned long Speed = ((counter * length_one_segment - space_between_rollers) * 1000) / T; // mm/s
        show_speed(Speed, T);
        
        previousMillis = currentMillis;
        counter = 0;
      }

    }
    previous_state = response;
  }

  if (currentMillis - last_command_time >= timeout_interval)
    timeout = 1;
  else 
    timeout = 0;
    
  if (timeout)
    red_LED = true;
    
  digitalWrite(pin_RED_LED, red_LED);
 
  delay(1);     
}
