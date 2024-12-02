#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <esp_now.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// LCD setup
LiquidCrystal_I2C lcd(0x27, 16, 2);
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27

// Select camera model
#define CAMERA_MODEL_AI_THINKER
#include "camera_pins.h"

// Wi-Fi credentials
const char* ssid = "Sigazen"; // Update if needed
const char* password = "00440044Cc"; // Update if needed

// Server URL for photo upload
const char* serverUrl = "http://10.201.135.36:8080/upload"; // Replace XXX with correct IP

void startCameraServer(); // Function prototype

void captureAndSendPhoto();
void capturePhoto();

// ESP-NOW callback
void onDataRecv(const esp_now_recv_info_t *recv_info, const uint8_t *data, int len) {
  String command = "";
  for (int i = 0; i < len; i++) {
    command += (char)data[i];
  }

  lcd.setCursor(0, 1);
  lcd.print("Cmd: " + command);

  if (command == "photo") {
    captureAndSendPhoto();
  } else {
    Serial.println("Unknown command received.");
  }
}

void setup() {
  Wire.begin(0, 2); // SDA on GPIO 0, SCL on GPIO 2
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Starting...");

  Serial.begin(115200);
  Serial.setDebugOutput(true);

  // Camera config
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if (psramFound()) {
    config.frame_size = FRAMESIZE_UXGA;
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  // Initialize camera
  if (esp_camera_init(&config) != ESP_OK) {
    lcd.setCursor(0, 1);
    lcd.print("Cam Init Fail");
    Serial.println("Camera init failed");
    return;
  }
  sensor_t *s = esp_camera_sensor_get();
  if (s == NULL) {
    Serial.println("Camera sensor not detected");
    lcd.print("No Sensor");
    while (1); // Halt if no sensor detected
  }
  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  lcd.setCursor(0, 1);
  lcd.print("Connecting...");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  lcd.clear();
  lcd.print("WiFi Ready");
  lcd.setCursor(0, 1);
  lcd.print(WiFi.localIP().toString());
  startCameraServer();
  Serial.print("Camera Ready! Use 'http://");
  Serial.print(WiFi.localIP());
  Serial.println("' to connect");
  // ESP-NOW init
  if (esp_now_init() != ESP_OK) {
    lcd.setCursor(0, 1);
    lcd.print("ESP-NOW Failed");
    Serial.println("Error initializing ESP-NOW");
    return;
  }

  esp_now_register_recv_cb(onDataRecv);
  lcd.setCursor(0, 1);
  lcd.print("ESP-NOW Ready");
}

void captureAndSendPhoto() {
  camera_fb_t *fb = esp_camera_fb_get();

  if (!fb) {
    lcd.setCursor(0, 1);
    lcd.print("Capture Fail");
    Serial.println("Camera capture failed");
    return;
  }

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "image/jpeg");

    int httpResponseCode = http.POST(fb->buf, fb->len);

    lcd.setCursor(0, 1);
    if (httpResponseCode > 0) {
      lcd.print("Upload: Success");
      Serial.println("Upload success!");
    } else {
      lcd.print("Upload: Failed");
      Serial.printf("Upload failed. HTTP code: %d\n", httpResponseCode);
    }
    http.end();
  } else {
    lcd.setCursor(0, 1);
    lcd.print("No WiFi");
    Serial.println("WiFi disconnected");
  }

  esp_camera_fb_return(fb);
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "photo") {
      captureAndSendPhoto();
    }
  }
  delay(1000); 
}
