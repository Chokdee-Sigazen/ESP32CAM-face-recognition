# ESP32-CAM Face Recognition System

## Overview
A face recognition attendance system using ESP32-CAM and Python server that:
- Captures photos when detecting a person
- Recognizes faces and records attendance
- Integrates with Google Sheets
- Includes a web dashboard

## Hardware Requirements
- ESP32-CAM
- DHT22 temperature sensor
- LCD I2C Display
- Servo motor
- LED indicator

## Software Requirements
- Arduino IDE
- Python 3.x
- Required Python packages:
  ```
  pip install flask opencv-python numpy gspread oauth2client
  ```

## Setup

### ESP32-CAM
1. Connect components:
   - LCD: SDA -> GPIO13, SCL -> GPIO15
   - DHT22: Data -> GPIO14
   - Servo: Signal -> GPIO16
   - LED: GPIO2

2. Upload ESP32-CAM code

### Python Server
1. Set up Google Sheets API:
   - Create project in Google Cloud Console
   - Enable Google Sheets API
   - Create service account credentials
   - Save as `credentials.json`

2. Configure Google Sheet:
   - Create sheet with "Employees" and "Attendance" worksheets
   - Share with service account email

3. Run server:
   ```bash
   python server.py
   ```

## Usage
1. Add new employee photos using menu option 2
2. System automatically detects and records attendance
3. View attendance through dashboard

## Features
- Face detection and recognition
- Temperature monitoring
- Attendance tracking in Google Sheets
- Real-time dashboard
- LED status indicators

## Configuration
Edit these variables:
- WiFi credentials in ESP32 code
- Server IP/port
- Google Sheet ID

## Troubleshooting
- Check camera focus and lighting
- Verify WiFi connection
- Ensure Google Sheet permissions
- Monitor serial output for errors

## Known Issues
- Face detection may require proper positioning
- Initial camera connection can sometimes fail
