#include <WiFi.h>
#include <HTTPClient.h>

// WiFi credentials
const char* ssid = "Sigazen";
const char* password = "00440044Cc";

// ESP32-CAM IP address
const char* receiverIP = "192.168.40.19";  // Replace with ESP32-CAM's IP
const int receiverPort = 8080;

// Ultrasonic sensor pins
const int trigPin = 33;  // Adjust these pins according to your wiring
const int echoPin = 32;


long duration, distance;

// Distance threshold (in cm)
const int THRESHOLD = 50;  // Adjust this value based on your needs
const int MIN_DISTANCE = 20;  // Minimum distance to prevent false triggers

// Timing control
unsigned long lastTriggerTime = 0;
const unsigned long TRIGGER_DELAY = 2000; // 2 seconds between triggers

void setup() {
  Serial.begin(115200);
  
  // Setup ultrasonic sensor pins
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

int getDistance() {
  // Trigger ultrasonic pulse
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  // Read the response
  long duration = pulseIn(echoPin, HIGH);
  
  // Calculate distance in centimeters
  int distance = (duration/2) / 29.1;
  
  return distance;
}

void sendPhotoCommand() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = "http://" + String(receiverIP) + ":" + String(receiverPort) + "/take_photo";
    
    http.begin(url);
    int httpResponseCode = http.GET();
    
    if (httpResponseCode > 0) {
      Serial.println("Photo command sent successfully");
    } else {
      Serial.print("Error sending command: ");
      Serial.println(httpResponseCode);
    }
    
    http.end();
  }
}

void loop() {
  int distance = getDistance();
  unsigned long currentTime = millis();
  
  // Print distance for debugging
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");

  // Check if someone is in range and enough time has passed since last trigger
  if (distance < THRESHOLD && distance > MIN_DISTANCE && 
      (currentTime - lastTriggerTime > TRIGGER_DELAY)) {
    Serial.println("Person detected! Triggering camera...");
    sendPhotoCommand();
    lastTriggerTime = currentTime;
  }
  
  delay(100);  // Small delay between readings
}