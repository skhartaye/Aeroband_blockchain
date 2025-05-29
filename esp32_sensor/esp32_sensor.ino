#include <SPI.h>
#include <Adafruit_Sensor.h>
#include "Adafruit_BME680.h"
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <esp_bt.h>
#include <esp_gap_ble_api.h>
#include <esp_gatts_api.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
// BLE Service and Characteristic UUIDs
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

// LED pins (optional, for status)
#define CONNECTION_LED 2  // Built-in LED
#define DATA_LED 4        // External LED for data transmission indication

// MQ-137 setup (Ammonia Sensor)
const int mq137AnalogPin = 34;  // GPIO 34 = Analog input
const float RL = 10.0;          // Load resistance in kOhms
const float R0 = 20.0;          // Sensor resistance in clean air (calibrate this value)
const float a = 102.2;          // NH3 curve parameter
const float b = -2.473;         // NH3 curve slope

// BME680 SPI setup
#define BME_CS 5 // Chip Select for BME680
Adafruit_BME680 bme(BME_CS); // Uses default SPI pins for MOSI, MISO, SCK

// PMS7003 UART pins
#define PMS7003_RX 16
#define PMS7003_TX 17
HardwareSerial pmsSerial(1); // UART1 for PMS7003

// BLE variables
BLEServer* pServer = NULL;
BLECharacteristic* pCharacteristic = NULL;
bool deviceConnected = false;
bool oldDeviceConnected = false; // To detect changes in connection state

// For OLED page switching
unsigned long lastPageSwitch = 0;
const unsigned long pageInterval = 5000; // 5 seconds per page
int displayPage = 0;
const int totalPages = 6; // Updated to 6 pages to match all sensor displays

// OLED config
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1  // Reset pin # (or -1 if sharing Arduino reset pin)
#define OLED_SDA      21  // ESP32 default SDA pin
#define OLED_SCL      22  // ESP32 default SCL pin

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Global sensor variables
float temperature = NAN;
float humidity = NAN;
float pressure = NAN;
float gas_resistance = NAN;
float ammoniaPPM = 0.0;
unsigned int pm1_0_val = 0;
unsigned int pm2_5_val = 0;
unsigned int pm10_val = 0;
int rawValue = 0;
float voltage = 0.0;

// For HTTP requests
unsigned long lastHttpRequest = 0;
const unsigned long httpInterval = 10000; // Changed from 2000 to 10000 (10 seconds)

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServerInstance) {
        deviceConnected = true;
        digitalWrite(CONNECTION_LED, HIGH);
        Serial.println("[BLE] Client connected");
        Serial.println("[BLE] Device is advertising as: ESP32-MultiSensor");
        Serial.println("[BLE] Waiting for data transmission...");
        Serial.println("[BLE] Note: Cannot retrieve client (phone) address using Arduino BLE library.");
    };

    void onDisconnect(BLEServer* pServerInstance) {
        deviceConnected = false;
        digitalWrite(CONNECTION_LED, LOW);
        Serial.println("[BLE] Client disconnected");
        Serial.println("[BLE] Restarting advertising...");
    }
};

void setup() {
    Serial.begin(115200);
    delay(1000);

    pinMode(CONNECTION_LED, OUTPUT);
    pinMode(DATA_LED, OUTPUT);
    digitalWrite(CONNECTION_LED, LOW);
    digitalWrite(DATA_LED, LOW);

    Serial.println("[SYSTEM] Booting ESP32 MultiSensor BLE...");

    // Initialize OLED
    Wire.begin(OLED_SDA, OLED_SCL);
    if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
        Serial.println(F("[OLED] SSD1306 allocation failed"));
        while(1);
    }
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0,0);
    display.println("ESP32 MultiSensor");
    display.display();
    delay(2000);

    // Initialize MQ-137 (No specific init needed for analog read)
    analogReadResolution(10); // Set ADC resolution (10-bit for 0-1023)

    // Initialize BME680
    if (!bme.begin()) {
        Serial.println("Could not find a valid BME680 sensor, check wiring!");
        while (1); // Halt
    }
    bme.setTemperatureOversampling(BME680_OS_8X);
    bme.setHumidityOversampling(BME680_OS_2X);
    bme.setPressureOversampling(BME680_OS_4X);
    bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
    bme.setGasHeater(320, 150); // 320*C for 150ms

    // Initialize PMS7003
    pmsSerial.begin(9600, SERIAL_8N1, PMS7003_RX, PMS7003_TX);

    // Initialize BLE
    BLEDevice::init("ESP32-MultiSensor");
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    BLEService *pService = pServer->createService(SERVICE_UUID);
    pCharacteristic = pService->createCharacteristic(
                        CHARACTERISTIC_UUID,
                        BLECharacteristic::PROPERTY_READ |
                        BLECharacteristic::PROPERTY_NOTIFY
                      );
    pCharacteristic->addDescriptor(new BLE2902());

    pService->start();
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(0x06);
    pAdvertising->setMinPreferred(0x12);
    BLEDevice::startAdvertising();
    Serial.println("[BLE] BLE device initialized and advertising");
}

void loop() {
    // Variables for text positioning
    int16_t x1, y1;
    uint16_t w, h;

    if (deviceConnected) {
        digitalWrite(DATA_LED, HIGH);
        
        // MQ-137 Data
        rawValue = analogRead(mq137AnalogPin);
        voltage = rawValue * (3.3 / 1023.0);
        float RS = (voltage == 0) ? 1000000.0 : ((3.3 * RL) / voltage) - RL;
        float rsRatio = RS / R0;
        ammoniaPPM = 0.0;
        
        // Only calculate PPM if we have a valid resistance ratio
        if (rsRatio > 0 && !isnan(rsRatio) && !isinf(rsRatio)) {
            ammoniaPPM = a * pow(rsRatio, b);
            // Validate the calculated PPM
            if (ammoniaPPM < 0 || isnan(ammoniaPPM) || isinf(ammoniaPPM)) {
                ammoniaPPM = 0.0;  // Invalid reading
            }
        }

        // BME680 Data
        if (bme.performReading()) {
            temperature = bme.temperature;
            humidity = bme.humidity;
            pressure = bme.pressure / 100.0; // Convert Pa to hPa
            gas_resistance = bme.gas_resistance / 1000.0; // Convert Ohms to kOhms
        } else {
            Serial.println("Failed to perform BME680 reading");
        }

        // PMS7003 Data
        byte pmsBuffer[32];
        int pmsCount = 0;
        unsigned long pmsStartTime = millis();
        while (pmsSerial.available() && (millis() - pmsStartTime < 1000)) { // Read with 1s timeout
            if (pmsCount < 32) pmsBuffer[pmsCount++] = pmsSerial.read();
            else pmsSerial.read(); // Discard extra bytes if buffer is full
        }

        if (pmsCount == 32 && pmsBuffer[0] == 0x42 && pmsBuffer[1] == 0x4D) {
            pm1_0_val = (pmsBuffer[10] << 8) | pmsBuffer[11];
            pm2_5_val = (pmsBuffer[12] << 8) | pmsBuffer[13];
            pm10_val = (pmsBuffer[14] << 8) | pmsBuffer[15];
        }

        // Construct JSON payload
        char jsonData[350]; 
        snprintf(jsonData, sizeof(jsonData),
                 "{\"temperature\":%.2f,\"humidity\":%.2f,\"pressure\":%.2f,\"gas_resistance\":%.2f,\"ammonia\":%.2f,\"pm1_0\":%u,\"pm2_5\":%u,\"pm10\":%u}",
                 isnan(temperature) ? 0.00 : temperature, 
                 isnan(humidity) ? 0.00 : humidity, 
                 isnan(pressure) ? 0.00 : pressure, 
                 isnan(gas_resistance) ? 0.00 : gas_resistance,
                 ammoniaPPM, pm1_0_val, pm2_5_val, pm10_val);
        
        Serial.print("[BLE] Sending data to connected device: ");
        Serial.println(jsonData);
        
        pCharacteristic->setValue(jsonData);
        pCharacteristic->notify();
        digitalWrite(DATA_LED, LOW);
        Serial.println("[BLE] Data sent and DATA_LED toggled");
    }

    if (!deviceConnected && oldDeviceConnected) {
        delay(500);
        BLEDevice::startAdvertising();
        Serial.println("[BLE] Advertising restarted after disconnect");
        oldDeviceConnected = deviceConnected;
    }
    if (deviceConnected && !oldDeviceConnected) {
        Serial.println("[BLE] Device reconnected");
        oldDeviceConnected = deviceConnected;
    }
    
    delay(5000);

    // For OLED page switching
    unsigned long currentMillis = millis();
    if (currentMillis - lastPageSwitch > pageInterval) {
        lastPageSwitch = currentMillis;
        displayPage++;
        if (displayPage >= totalPages) displayPage = 0;
    }

    display.clearDisplay();  // Clear the display before drawing new content
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0,0);

    // Page content switching
    switch(displayPage) {
        case 0: {
            display.setTextSize(2);
            String tempStr = "Temp:" + String(temperature, 1) + "C";
            display.getTextBounds(tempStr, 0, 0, &x1, &y1, &w, &h);
            display.setCursor((SCREEN_WIDTH - w) / 2, 20);
            display.print(tempStr);
            break;
        }
        case 1: {
            display.setTextSize(2);
            String humStr = "Humi:" + String(humidity, 1) + "%";
            display.getTextBounds(humStr, 0, 0, &x1, &y1, &w, &h);
            display.setCursor((SCREEN_WIDTH - w) / 2, 20);
            display.print(humStr);
            break;
        }
        case 2: {
            display.setTextSize(2);
            String pressStr = "Pres:" + String(pressure, 1) + "hPa";
            display.getTextBounds(pressStr, 0, 0, &x1, &y1, &w, &h);
            display.setCursor((SCREEN_WIDTH - w) / 2, 20);
            display.print(pressStr);
            break;
        }
        case 3: {
            display.setTextSize(2);
            String gasStr = "Gas:" + String(gas_resistance, 1) + "kOhm";
            display.getTextBounds(gasStr, 0, 0, &x1, &y1, &w, &h);
            display.setCursor((SCREEN_WIDTH - w) / 2, 20);
            display.print(gasStr);
            break;
        }
        case 4: {
            display.setTextSize(2);
            String amStr = "NH3:" + String(ammoniaPPM, 2) + "ppm";
            display.getTextBounds(amStr, 0, 0, &x1, &y1, &w, &h);
            display.setCursor((SCREEN_WIDTH - w) / 2, 20);
            display.print(amStr);
            break;
        }
        case 5: {
            display.setTextSize(2);
            String pmStr = "PM2.5:" + String(pm2_5_val);
            display.getTextBounds(pmStr, 0, 0, &x1, &y1, &w, &h);
            display.setCursor((SCREEN_WIDTH - w) / 2, 20);
            display.print(pmStr);
            break;
        }
    }
    display.display();  // Update the display with new content
} 