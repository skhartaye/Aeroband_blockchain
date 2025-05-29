# Aeroband Blockchain Integration

This module provides blockchain integration for the Aeroband sensor network using the Aptos blockchain.

## Features

- Sensor registration and ownership management
- Real-time sensor data submission to blockchain
- Secure data verification and validation
- Event-based sensor reading tracking
- Smart contract-based sensor management

## Setup

1. Install Dependencies:
```bash
pip install -r requirements.txt
```

2. Configure Environment:
- Copy `config.env.example` to `config.env`
- Update the following variables in `config.env`:
  - `APTOS_PRIVATE_KEY`: Your Aptos account private key
  - `MODULE_ADDRESS`: Your deployed module address
  - Other configuration variables as needed

3. Deploy Smart Contract:
```bash
# Install Aptos CLI
curl -fsSL "https://aptoslabs.com/scripts/install_cli.py" | python3

# Initialize Aptos project
aptos init

# Deploy the contract
aptos move publish
```

## Usage

### Python Integration

```python
from blockchain.aptos_integration import AptosSensorNetwork

# Initialize the sensor network
sensor_network = AptosSensorNetwork()

# Register a new sensor
sensor_id = "ESP32_001"
sensor_type = 1  # Environmental sensor
location = "Building A, Floor 1"
txn_hash = sensor_network.register_sensor(sensor_id, sensor_type, location)

# Submit sensor readings
readings = {
    "temperature": 25.5,
    "humidity": 60.0,
    "pressure": 1013.25,
    "air_quality": 85.0
}
txn_hash = sensor_network.submit_sensor_reading(sensor_id, readings)
```

### Smart Contract Functions

1. **Register Sensor**
```move
public entry fun register_sensor(
    account: &signer,
    sensor_id: String,
    sensor_type: u8,
    location: String
)
```

2. **Submit Reading**
```move
public entry fun submit_reading(
    account: &signer,
    sensor_id: String,
    temperature: u64,
    humidity: u64,
    pressure: u64,
    air_quality: u64
)
```

3. **Get Sensor Data**
```move
public fun get_sensor_data(account_addr: address): (String, address, u8, String, u64, u8)
```

4. **Update Sensor Status**
```move
public entry fun update_sensor_status(
    account: &signer,
    sensor_id: String,
    new_status: u8
)
```

## Security Considerations

1. **Private Key Management**
   - Never commit private keys to version control
   - Use environment variables for sensitive data
   - Consider using a key management service

2. **Transaction Security**
   - Validate all sensor readings before submission
   - Implement rate limiting for sensor submissions
   - Use appropriate gas limits and prices

3. **Data Validation**
   - Verify sensor ownership before data submission
   - Implement data range checks
   - Use appropriate data types and conversions

## Development

### Testing

```bash
# Run Move tests
aptos move test

# Run Python integration tests
python -m pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 