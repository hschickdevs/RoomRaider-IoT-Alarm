#include "M5StickCPlus.h"
#include <HTTPClient.h>
#include <WiFi.h>
#include <ArduinoJson.h>  // Needs to be installed via Arduino library manager

// Configuration
const char* SSID = "<YOUR_WIFI_SSID>"; 
const char* PASSWORD = "<YOUR_WIFI_PASSKEY>";
const char* WEBHOOK_URL = "https://<VPS_IP>:<VPS_PORT>/<TELEGRAM_BOT_TOKEN>/";
const char* LOCATION_NAME = "Bedroom Door";
const int POLLING_PERIOD = 1000; // Polling period in milliseconds between sensor updates 1000 = 1 second

// Function to setup the device on the wireless network
void setup_wifi() {
  delay(10);
  // We start by connecting to a WiFi network
  M5.Lcd.println();
  M5.Lcd.print("Connecting to ");
  M5.Lcd.println(SSID);

  //WiFi.mode(WIFI_STA);
  WiFi.begin(SSID, PASSWORD);

  // Print "." until the network is connected for better UX
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    M5.Lcd.print(".");
  }

  // Print the local IP of the device once connected to the network
  M5.Lcd.println("");
  M5.Lcd.println("WiFi connected");
  M5.Lcd.println("IP address: ");
  M5.Lcd.println(WiFi.localIP());
}

bool checkWifiConnection() {
  if (WiFi.status() != WL_CONNECTED) {
    M5.Lcd.println("Reconnecting to WiFi...");
    setup_wifi();
    return WiFi.status() == WL_CONNECTED;
  }
  return true;
}

void sendPostRequest(const char* sensorStatus) {
  if (checkWifiConnection()) {
    HTTPClient http;
    http.begin(WEBHOOK_URL); // Webhook URL
    http.addHeader("Content-Type", "application/json");

    StaticJsonDocument<200> doc;
    doc["action"] = "sensor_event";
    doc["timestamp"] = (int)time(NULL); // Current timestamp
    doc["location"] = LOCATION_NAME;
    doc["sensor_status"] = sensorStatus;

    String payload;
    serializeJson(doc, payload);

    int httpResponseCode = http.POST(payload);

    // Print the response on the LCD
    M5.Lcd.fillScreen(BLACK);
    M5.Lcd.setCursor(0, 0);
    if(httpResponseCode > 0) {
      String response = http.getString();
      M5.Lcd.println(response);
    } else {
      M5.Lcd.println("POST Error: " + String(httpResponseCode));
    }

    http.end();
  } else {
    M5.Lcd.println("Failed to Connect WiFi");
  }
}

void setup() {
  M5.begin();
  pinMode(26, INPUT_PULLUP);
  M5.Lcd.setRotation(3);
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setTextColor(WHITE);
  M5.Lcd.setTextSize(2);
  setup_wifi();
}

void loop() {
  static int lastState = -1; // To store the last state
  int sensorState = digitalRead(26);

  if (sensorState != lastState) {
    lastState = sensorState;
    if (sensorState == HIGH) {
      M5.Lcd.println("Door Open");
      sendPostRequest("OPEN");
    } else {
      M5.Lcd.println("Door Closed");
      sendPostRequest("CLOSED");
    }
  }
  delay(POLLING_PERIOD);
}