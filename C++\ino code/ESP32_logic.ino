#include <ESP32Servo.h>
#include <Wire.h>


Servo gate, bottom;

const int gate_pin = 14;    // we must assign a GPIO pin number here
const int bottom_pin = 27;  // same here

#define trigPin 26         //same
#define echoPin 25         //same

unsigned long detectStartTime = 0;
bool objectPresent = false;
bool autoTriggered = false;


void setup() {
  Serial.begin(115200);  //must be the same in python
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  // Initialize the servos at base 
  gate.attach(gate_pin);
  bottom.attach(bottom_pin);
  gate.write(90);
  bottom.write(140);
  delay(500);

}

void loop() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH);

  float distance = duration * 0.034 / 2;



  if (distance <= 45) { 
    // Check if a character has been sent to the Serial Monitor from the laptop

    if (!objectPresent) {
      objectPresent = true;
      detectStartTime = millis();
      autoTriggered = false;
    }
    if (!autoTriggered && (millis() - detectStartTime >= 8000)) {
      gate.attach(gate_pin);
      gate.write(25);
      delay(5000);

      gate.write(90);
      delay(500);
      autoTriggered = true; // Prevent looping while object is still present
    }
    if (Serial.available() > 0) {
      char command = Serial.read();

      if (command == 'G') {
        gate.attach(gate_pin);
        gate.write(25);
        delay(5000);

        gate.write(90);
        delay(500);
        //gate.detach();
      } else if (command == 'P') {
        bottom.write(140);
        delay(2000);
        gate.write(180);
        delay(3000);

        gate.write(90);
        delay(500);
      } else if (command == 'C') {
        bottom.write(25);
        delay(2000);
        gate.write(180);
        delay(5000);
        // RESET AFTER USE
        gate.write(90);
        delay(500);
      }
      autoTriggered = true;
    }
  }
  else {
    // Object left the sensor range
    objectPresent = false;
    autoTriggered = false;
  }
}