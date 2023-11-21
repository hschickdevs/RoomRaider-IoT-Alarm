#include "M5StickCPlus.h"

void setup() {
  M5.begin();
  pinMode(26, INPUT_PULLUP); // Use internal pull-up resistor
  M5.Lcd.setRotation(3);
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setTextColor(WHITE);
  M5.Lcd.setTextSize(2);
}

void loop() {
  int sensorState = digitalRead(26);
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setCursor(0, 0);

  if (sensorState == HIGH) {
    // HIGH means the door is open
    M5.Lcd.println("Door Open");
  } else {
    // For NC sensor, LOW means the door is closed
    M5.Lcd.println("Door Closed");
  }
  delay(500);
}
