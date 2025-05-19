# Aeroband 🏭

This project is for the Aeroband system, including ESP32 firmware, Django backend, and mobile web interface.

## Branch: WorkingEsp32

This branch contains the latest work for the ESP32 integration and related features.

## Features ✨
- ESP32 sensor data collection 📊
- Django backend API 🔄
- Mobile-friendly dashboard 📱
- Real-time sensor monitoring 📈
- Historical data tracking 📉
- Alert system for sensor thresholds ⚠️

## Software Requirements 💻
- Python 3.8+
- Django 4.2+
- ngrok
- Arduino IDE
- ESP32 Board Support Package

### Required Python Packages 📦
```
# Backend Requirements
djangorestframework>=3.16.0

# Mobile Requirements
bleak>=0.21.1
aiohttp>=3.9.1
asyncio>=3.4.3
```

## Setup and Operation 🚀

### 1. Backend Setup
```bash
# Clone and setup
git clone https://github.com/miiikunnn/Aeroband.git
cd Aeroband
python -m venv env
.\env\Scripts\activate  # Windows
pip install -r requirements.txt
pip install -r requirements_mobile.txt
python manage.py migrate
```

### 2. Run with ngrok
```bash
# Basic ngrok command
ngrok http 8000

# For a specific subdomain (requires paid plan)
ngrok http --subdomain=your-subdomain 8000

# For a specific region
ngrok http --region=us 8000

# For a specific authentication token (more secure)
ngrok http --authtoken=your-token 8000

# Combine options
ngrok http --subdomain=your-subdomain --region=us --authtoken=your-token 8000
```

#### Automatic ngrok URL Update 🔄
To automatically update Django settings when ngrok URL changes:

1. **Install Required Package**
   ```bash
   pip install requests
   ```

2. **Run the Update Script**
   ```bash
   # In a new terminal window
   python update_ngrok_url.py
   ```

3. **What the Script Does**
   - Monitors ngrok URL changes
   - Updates Django ALLOWED_HOSTS
   - Updates CORS settings
   - No manual settings changes needed

4. **Keep Running**
   - Keep this script running while developing
   - It will automatically update settings
   - No need to restart Django server

#### ngrok Configuration Options 🔧
1. **Basic Setup**
   - Free plan: Random URL each time
   - Example: `https://abc123.ngrok.io`

2. **Custom Subdomain** (Paid Plan)
   - Consistent URL every time
   - Example: `https://aeroband.ngrok.io`
   - Command: `ngrok http --subdomain=aeroband 8000`

3. **Region Selection**
   - Choose server location
   - Options: us, eu, ap, au, sa, jp, in
   - Example: `ngrok http --region=us 8000`

4. **Authentication**
   - Get token from ngrok dashboard
   - More secure connection
   - Example: `ngrok http --authtoken=your-token 8000`

5. **Configuration File**
   Create `ngrok.yml` in your home directory:
   ```yaml
   authtoken: your-token
   region: us
   subdomain: your-subdomain
   ```
   Then run: `ngrok start --config=ngrok.yml`

### 3. ESP32 Connection
1. Open `esp32_sensor/esp32_sensor.ino` in Arduino IDE
2. Upload to ESP32

### 4. Mobile Access
1. **Easy Access Method**
   - Open your computer's browser
   - Go to: `http://localhost:8000`
   - You'll see:
     - A QR code to scan with your phone
     - The current ngrok URL
     - Direct links to connect and dashboard
   - On your mobile:
     - Scan the QR code with your phone's camera
     - Or copy the URL shown on the page
     - Open the link in your mobile browser

2. **Direct Access** (Alternative)
   - Open your mobile browser
   - Go to: `https://your-ngrok-url/ble-bridge/`
   - Connect to ESP32 device
   - Access dashboard at: `https://your-ngrok-url/mobile/`

## Detailed Step-by-Step Guide 📝

### Prerequisites Check ✅
1. Make sure you have installed:
   - Python 3.8 or higher (check with `python --version`)
   - Arduino IDE (latest version)
   - ngrok (sign up at ngrok.com for free account)
   - Git (for cloning repository)
   - VSCode or Cursor IDE (recommended)

### Backend Setup (Detailed) 💻

#### Option 1: Using Terminal/Command Prompt
```bash
# Clone Repository
git clone https://github.com/miiikunnn/Aeroband.git
cd Aeroband

# Create Virtual Environment
python -m venv env
.\env\Scripts\activate  # Windows
source env/bin/activate  # Linux/Mac

# Install Dependencies
pip install -r requirements.txt
pip install -r requirements_mobile.txt

# Database Setup
python manage.py migrate
```

#### Option 2: Using VSCode/Cursor IDE
1. **Open Project**
   - Open VSCode/Cursor
   - Go to File > Open Folder
   - Select the Aeroband folder

2. **Open Terminal in IDE**
   - Press `` Ctrl + ` `` (backtick) to open integrated terminal
   - Or go to Terminal > New Terminal

3. **Run Setup Commands**
   - Copy and paste these commands into the terminal:
   ```bash
   python -m venv env
   .\env\Scripts\activate  # Windows
   pip install -r requirements.txt
   pip install -r requirements_mobile.txt
   python manage.py migrate
   ```

4. **Select Python Interpreter**
   - Press `Ctrl + Shift + P`
   - Type "Python: Select Interpreter"
   - Choose the interpreter from your `env` folder

### ESP32 Setup (Detailed) 🔧
1. **Install Required Libraries in Arduino IDE**
   - Open Arduino IDE
   - Go to Tools > Manage Libraries
   - Install these libraries:
     - Adafruit BME680
     - Adafruit Unified Sensor
     - ESP32 BLE Arduino

2. **Install ESP32 Board in Arduino IDE**
   - Go to File > Preferences
   - Add this URL to Additional Boards Manager URLs:
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Go to Tools > Board > Boards Manager
   - Search for "esp32" and install "ESP32 by Espressif Systems"

3. **Upload Code to ESP32**
   - Open `esp32_sensor/esp32_sensor.ino` in Arduino IDE
   - Select correct board: Tools > Board > ESP32 Arduino > ESP32 Dev Module
   - Select correct port: Tools > Port > (your ESP32 port)
   - Click Upload button (→) or press Ctrl+U
   - Wait for upload to complete

4. **Verify ESP32 Connection**
   - Open Serial Monitor (Tools > Serial Monitor)
   - Set baud rate to 115200
   - You should see these messages:
     ```
     [SYSTEM] Booting ESP32 MultiSensor BLE...
     [BLE] BLE device initialized and advertising
     ```

5. **Hardware Connections**
   - Connect sensors to ESP32:
     - BME680: SPI pins (MOSI, MISO, SCK) + CS on GPIO 5
     - MQ-137: Analog pin GPIO 34
     - PMS7003: UART pins GPIO 16 (RX) and 17 (TX)
     - LEDs: GPIO 2 (Connection) and GPIO 4 (Data)

### Running the System (Detailed) 🚀

#### Option 1: Using Terminal/Command Prompt
```bash
# Start Django Server
cd Aeroband
.\env\Scripts\activate  # Windows
python manage.py runserver

# In a new terminal window
ngrok http 8000
```

#### Option 2: Using VSCode/Cursor IDE
1. **Start Django Server**
   - Open terminal in IDE (`` Ctrl + ` ``)
   - Make sure virtual environment is activated
   - Run:
   ```bash
   python manage.py runserver
   ```

2. **Start ngrok**
   - Open a new terminal in IDE
   - Run:
   ```bash
   ngrok http 8000
   ```

3. **Mobile Access**
   - Open your mobile browser
   - Go to: `https://your-ngrok-url/ble-bridge/`
   - Allow Bluetooth access when prompted
   - Select your ESP32 device from the list
   - Wait for connection confirmation

4. **Access Dashboard**
   - Go to: `https://your-ngrok-url/mobile/`
   - You should see the sensor dashboard
   - Real-time data should start appearing

### Common Issues and Solutions 🔧
1. **ESP32 Not Found**
   - Check if ESP32 is properly connected
   - Verify correct COM port in Arduino IDE
   - Try resetting ESP32 (press reset button)

2. **Bluetooth Connection Issues**
   - Make sure Bluetooth is enabled on your phone
   - Check if ESP32 is in range
   - Try restarting the mobile browser
   - Clear browser cache and cookies

3. **No Data Showing**
   - Check ESP32 Serial Monitor for errors
   - Verify WiFi connection on ESP32
   - Check if Django server is running
   - Verify ngrok connection is active

4. **Server Connection Issues**
   - Check if Django server is running
   - Verify ngrok URL is correct
   - Make sure all dependencies are installed
   - Check internet connection

### Testing the System ✅
1. **Basic Functionality Test**
   - Verify ESP32 is sending data
   - Check if data appears on dashboard
   - Test alert system by changing thresholds

2. **Connection Stability Test**
   - Monitor connection for 5-10 minutes
   - Check for any disconnections
   - Verify data consistency

3. **Mobile Interface Test**
   - Test all dashboard features
   - Verify historical data view
   - Check alert settings

## Mobile Dashboard Features 📱
- Real-time sensor readings
- Device connection status
- Historical data view
- Alert settings

## Troubleshooting 🔧
- If ESP32 doesn't connect, check WiFi credentials
- If ngrok connection fails, restart ngrok
- If mobile dashboard doesn't load, clear browser cache

## Future Enhancements 🚀

### Mobile App Development 📱
- Native mobile apps for iOS and Android
- Push notifications for alerts
- Offline data storage
- Background sensor monitoring
- Customizable dashboard layouts

### Hardware Improvements 🔧
- Additional sensor support (CO2, VOC, etc.)
- Battery-powered operation
- Solar charging capability
- Waterproof enclosure design
- Multiple device synchronization

### Software Features 💻
- Machine learning for air quality prediction
- Automated reporting system
- Integration with smart home systems
- API for third-party applications
- Advanced data visualization
- Multi-language support

### Cloud Integration ☁️
- AWS/Azure cloud deployment
- Data backup and recovery
- Scalable infrastructure
- Global device management
- Advanced analytics dashboard

### Security Enhancements 🔒
- End-to-end encryption
- Two-factor authentication
- Role-based access control
- Regular security audits
- GDPR compliance features

### User Experience 🎯
- Voice control integration
- Gesture-based controls
- AR visualization of air quality
- Social sharing features
- Community data comparison

## License
This project is licensed under the MIT License - see the LICENSE file for details. 
