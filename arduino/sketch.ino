#include "M5StickCPlus.h"
#include <HTTPClient.h>
#include <WiFi.h>
#include <ArduinoJson.h>  // Needs to be installed by arduino library manager

// ------------------------ CONFIGURATION ------------------------- //

// UT wifi setup (REPLACE THESE WITH YOUR SETTINGS)
const char* SSID = "<YOUR_WIFI_SSID>"; 
const char* PASSWORD = "<YOUR_WIFI_PASSKEY>";
const char* WEBHOOK_URL = "https://<VPS_IP>:<VPS_PORT>/<TELEGRAM_BOT_TOKEN>/";
const char* LOCATION_NAME = "Bedroom Door"


// Function to setup the device on the utexas-iot wireless network
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


void sendPostRequest() {
  if(WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    http.begin(WEBHOOK_URL); // Specify your webhook URL here
    http.addHeader("Content-Type", "application/json");

    // Creating the JSON payload
    StaticJsonDocument<200> doc; // Adjust the size based on your payload
    doc["action"] = "sensor_event";
    doc["timestamp"] = (int)time(NULL); // Current timestamp
    doc["location"] = LOCATION_NAME;
    doc["sensor_status"] = "OPEN";

    String payload;
    serializeJson(doc, payload); // Serialize the JSON document to a string

    // Send POST request
    int httpResponseCode = http.POST(payload);

    // If you want to print the response
    if(httpResponseCode > 0) {
      String response = http.getString();
      M5.Lcd.print("Response: ");
      M5.Lcd.println(response);
    } else {
      M5.Lcd.print("Error on sending POST: ");
      M5.Lcd.println(httpResponseCode);
    }

    // Free resources
    http.end();
  } else {
    M5.Lcd.println("WiFi not connected!");
  }
}


// Setup function run when the program starts
// Sets up wifi and initializes the MQTT client
void setup() {
  delay(500);
  // When opening the Serial Monitor, select 9600 Baud
  M5.begin();
  delay(500);
  setup_wifi();
}


// Mainloop
void loop() {
  // Read the button state
  M5.update();
  
  // Check if button A was pressed for publishing
  if (M5.BtnA.wasPressed()) {
    sendPostRequest();
  }
}