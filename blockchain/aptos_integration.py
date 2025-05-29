from aptos_sdk.account import Account
from aptos_sdk.client import RestClient
from aptos_sdk.transactions import EntryFunction, TransactionArgument
from aptos_sdk.type_tag import TypeTag, StructTag
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

class AptosSensorNetwork:
    def __init__(self):
        self.client = RestClient(os.getenv('APTOS_NODE_URL', 'https://fullnode.mainnet.aptoslabs.com'))
        self.account = Account.load_key(os.getenv('APTOS_PRIVATE_KEY'))
        self.module_address = os.getenv('MODULE_ADDRESS')
        
    def register_sensor(self, sensor_id: str, sensor_type: int, location: str) -> str:
        """Register a new sensor on the blockchain"""
        try:
            payload = {
                "function": f"{self.module_address}::sensor_network::register_sensor",
                "type_arguments": [],
                "arguments": [
                    sensor_id,
                    sensor_type,
                    location
                ]
            }
            
            txn_hash = self.client.submit_transaction(self.account, payload)
            self.client.wait_for_transaction(txn_hash)
            return txn_hash
            
        except Exception as e:
            print(f"Error registering sensor: {str(e)}")
            raise

    def submit_sensor_reading(self, sensor_id: str, readings: dict) -> str:
        """Submit sensor readings to the blockchain"""
        try:
            # Convert readings to blockchain format
            timestamp = int(datetime.now().timestamp())
            payload = {
                "function": f"{self.module_address}::sensor_network::submit_reading",
                "type_arguments": [],
                "arguments": [
                    sensor_id,
                    timestamp,
                    int(readings.get('temperature', 0) * 100),  # Convert to integer (2 decimal places)
                    int(readings.get('humidity', 0) * 100),
                    int(readings.get('pressure', 0) * 100),
                    int(readings.get('air_quality', 0) * 100)
                ]
            }
            
            txn_hash = self.client.submit_transaction(self.account, payload)
            self.client.wait_for_transaction(txn_hash)
            return txn_hash
            
        except Exception as e:
            print(f"Error submitting sensor reading: {str(e)}")
            raise

    def get_sensor_data(self, sensor_id: str) -> dict:
        """Retrieve sensor data from the blockchain"""
        try:
            resource = self.client.account_resource(
                self.module_address,
                f"{self.module_address}::sensor_network::Sensor"
            )
            
            # Parse and return sensor data
            return {
                "sensor_id": resource["data"]["id"],
                "owner": resource["data"]["owner"],
                "sensor_type": resource["data"]["sensor_type"],
                "location": resource["data"]["location"],
                "last_reading": resource["data"]["last_reading"],
                "status": resource["data"]["status"]
            }
            
        except Exception as e:
            print(f"Error getting sensor data: {str(e)}")
            raise

    def verify_sensor_ownership(self, sensor_id: str, address: str) -> bool:
        """Verify if an address owns a specific sensor"""
        try:
            sensor_data = self.get_sensor_data(sensor_id)
            return sensor_data["owner"] == address
        except Exception as e:
            print(f"Error verifying sensor ownership: {str(e)}")
            return False

# Example usage
if __name__ == "__main__":
    # Initialize the sensor network
    sensor_network = AptosSensorNetwork()
    
    # Example sensor registration
    try:
        sensor_id = "ESP32_001"
        sensor_type = 1  # 1 for environmental sensor
        location = "Building A, Floor 1"
        
        txn_hash = sensor_network.register_sensor(sensor_id, sensor_type, location)
        print(f"Sensor registered successfully. Transaction hash: {txn_hash}")
        
        # Example sensor reading submission
        readings = {
            "temperature": 25.5,
            "humidity": 60.0,
            "pressure": 1013.25,
            "air_quality": 85.0
        }
        
        txn_hash = sensor_network.submit_sensor_reading(sensor_id, readings)
        print(f"Sensor reading submitted successfully. Transaction hash: {txn_hash}")
        
    except Exception as e:
        print(f"Error in example usage: {str(e)}") 