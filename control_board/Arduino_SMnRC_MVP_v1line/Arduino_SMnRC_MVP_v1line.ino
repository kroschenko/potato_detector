#define Version "\n{\"version\":\"SMnRC queue v.1, " __DATE__ "\", send HI for info\"}"
#define Title "{\"title\":\"Speed Meter & Relays Control\"}"
#include "func.h"
// config.h, function.h
// вывод сколько времени прошло от постановки в очередь и открытия.
// Конфигурация без прошивки
// Ближайший на сдув может быть 2м в очереди
// Переход millis через 0
//number_of_rollers = 46  // not used
//top_nozzle_distance = 315  // mm, near (left)
//bottom_nozzle_distance = top_nozzle_distance + 30  // mm, far (right)
//top_nozzle = top_nozzle_distance / speed
//bottom_nozzle = bottom_nozzle_distance / speed


uint8_t pin_RED_LED=2; // 10mA
uint8_t pin_LASER=3; // 20mA
uint8_t pin_LDR=A0; // 0.5mA
const uint8_t nozzle_relays = 2;
uint8_t pin_RELAY[nozzle_relays]={5,4}; // 9mA (solid state relay, not a coil ~70mA.)
bool relay_high_level_trigger = false; // false for low level trigger;
// board with chip ATmega328p (Nano, Pro mini) 19mA
// total 10+20+18 + 19 = 67mA
uint16_t duration_nozzle_open = 233; // duration of open nozzle 363
const long interval = 5000; // Speed test time
const long timeout_interval = 25000; // wait ping interval;

const uint8_t queue_size = 10;
uint8_t queue_index = 0;
uint16_t threshold_response = 120; // <120 Laser On
uint16_t hysteresis = 30;
uint8_t roller_width = 70; // D, mm
uint8_t space_between_rollers = 10; // mm
uint8_t length_one_segment = roller_width + space_between_rollers;

struct nozzle_item {
  unsigned long timestamp;
  uint8_t nozzle;
};
nozzle_item Nozzles_Q[queue_size];

bool response = false;  // laser response
bool previous_state = false;

unsigned long previousMillis = 0;
unsigned long last_command_time = 0;
unsigned long nozzle_open[nozzle_relays] = {0};
unsigned long nozzle_delay_before_open[nozzle_relays] = {1401,1950};
bool laser_state = 0;
bool relay_state[nozzle_relays] = {0};
bool red_LED = 0;
bool timeout = 0; 
bool calibration = false;

void push(uint8_t nozzle_index) {
  timeout = 0;
  Serial.print("Add nozzle #");
  Serial.println(nozzle_index);
  if (queue_index>queue_size) {
    Serial.println("queue_index>queue_size");
    return;
  }

  Nozzles_Q[queue_index].timestamp = millis();
  Nozzles_Q[queue_index].nozzle = nozzle_index; // 
  queue_index++;
  print_queue();
  return;
}

void print_queue() {
  Serial.print("Size:");
  Serial.print(queue_index);  
  for(uint8_t i=0;i<queue_index;i++) {
    Serial.print("; ");
    Serial.print(Nozzles_Q[i].nozzle);
  }
  Serial.println();
}

void pop(uint8_t index) {
  // pop last element (index = queue_index-1);
  if ((queue_index == 0) || (index > queue_index-1) ) {
    Serial.println("Queue empty or oversize index");
    return; // Queue empty or oversize index
  }
  for(uint8_t i = index;i < queue_index-1;i++) {
    Nozzles_Q[i].timestamp = Nozzles_Q[i+1].timestamp;
    Nozzles_Q[i].nozzle = Nozzles_Q[i+1].nozzle;
  }
  queue_index--;
  print_queue();  
  return;
}

void check_nozzle() {
  // Check duration nozzle status
  bool ch_state = false;
  unsigned long currentMillis = millis();  
  
  // closes open nozzles
  for(uint8_t i=0; i < nozzle_relays; i++ )
    if ( (relay_state[i]) && (currentMillis - nozzle_open[i] >= duration_nozzle_open) ) {
      relay_state[i] = false;
      ch_state = true;
      Serial.print("Nozzle close #");
      Serial.println(i);
      
    }

  // opens the nozzles
  for(uint8_t i=0; (i < nozzle_relays) && (i < queue_index); i++ )
//   uint8_t i=0;
   //if (queue_index>0)
    if (currentMillis - Nozzles_Q[i].timestamp > nozzle_delay_before_open[Nozzles_Q[i].nozzle]) {
      relay_state[Nozzles_Q[i].nozzle] = true;
      nozzle_open[Nozzles_Q[i].nozzle] = millis();
      ch_state = true;
      Serial.print("i: ");
      Serial.print(i);
      Serial.print(";  Nozzle open #");
      Serial.print(Nozzles_Q[i].nozzle);
      Serial.print("; delay: ");
      Serial.println(nozzle_delay_before_open[Nozzles_Q[i].nozzle]);      
      pop(i);
    }


//relay_state[0] = true; set = 1; nozzle_open[0] = millis();        

  // if there were changes, changes the physical state of the relay
  if (ch_state) {
    Serial.println("CH state.");
    for(uint8_t i=0;i<nozzle_relays;i++)
      digitalWrite(pin_RELAY[i], (relay_high_level_trigger) ? relay_state[i] : !relay_state[i] );      
  }
        
}

void setup() {
  pinMode(pin_RED_LED, OUTPUT);
  pinMode(pin_LASER, OUTPUT);
  pinMode(pin_LDR, INPUT);
  for(uint8_t i=0;i<nozzle_relays;i++) {
    pinMode(pin_RELAY[i], OUTPUT);
    digitalWrite(pin_RELAY[i], (relay_high_level_trigger) ? relay_state[i] : !relay_state[i] );
  }
  digitalWrite(pin_RED_LED, red_LED);
  digitalWrite(pin_LASER, laser_state);
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
        case 'R': if (state) push(0); // Reley 1
        else push(1); // Reley 2
        case 'C': calibration = state; set = 1; // Calibration LDR + Laser On/Off
        case 'S': laser_state = state; set = 1; break; // Speed on/off
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

  check_nozzle();
          

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
