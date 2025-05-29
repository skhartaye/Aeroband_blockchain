module sensor_network {
    use std::signer;
    use std::string::{Self, String};
    use aptos_framework::account;
    use aptos_framework::timestamp;
    use aptos_framework::event::{Self, EventHandle};

    // Error codes
    const ENOT_AUTHORIZED: u64 = 1;
    const ESENSOR_NOT_FOUND: u64 = 2;
    const EINVALID_SENSOR_TYPE: u64 = 3;
    const EINVALID_READING: u64 = 4;

    // Sensor types
    const SENSOR_TYPE_ENVIRONMENTAL: u8 = 1;
    const SENSOR_TYPE_AIR_QUALITY: u8 = 2;
    const SENSOR_TYPE_TEMPERATURE: u8 = 3;

    // Sensor status
    const STATUS_ACTIVE: u8 = 1;
    const STATUS_INACTIVE: u8 = 2;
    const STATUS_MAINTENANCE: u8 = 3;

    struct Sensor has key {
        id: String,
        owner: address,
        sensor_type: u8,
        location: String,
        last_reading: u64,
        status: u8,
        reading_events: EventHandle<SensorReading>
    }

    struct SensorReading has store, drop, copy {
        sensor_id: String,
        timestamp: u64,
        temperature: u64,  // Stored as integer (multiplied by 100)
        humidity: u64,     // Stored as integer (multiplied by 100)
        pressure: u64,     // Stored as integer (multiplied by 100)
        air_quality: u64   // Stored as integer (multiplied by 100)
    }

    // Events
    struct RegisterSensorEvent has drop, store {
        sensor_id: String,
        owner: address,
        sensor_type: u8,
        location: String
    }

    struct SubmitReadingEvent has drop, store {
        sensor_id: String,
        timestamp: u64,
        temperature: u64,
        humidity: u64,
        pressure: u64,
        air_quality: u64
    }

    // Initialize the module
    public entry fun initialize(account: &signer) {
        let account_addr = signer::address_of(account);
        move_to(account, Sensor {
            id: string::utf8(b"INIT"),
            owner: account_addr,
            sensor_type: 0,
            location: string::utf8(b"INIT"),
            last_reading: 0,
            status: STATUS_INACTIVE,
            reading_events: account::new_event_handle<SensorReading>(account)
        });
    }

    // Register a new sensor
    public entry fun register_sensor(
        account: &signer,
        sensor_id: String,
        sensor_type: u8,
        location: String
    ) acquires Sensor {
        let account_addr = signer::address_of(account);
        
        // Validate sensor type
        assert!(sensor_type > 0 && sensor_type <= SENSOR_TYPE_TEMPERATURE, EINVALID_SENSOR_TYPE);
        
        // Create new sensor
        move_to(account, Sensor {
            id: sensor_id,
            owner: account_addr,
            sensor_type,
            location,
            last_reading: 0,
            status: STATUS_ACTIVE,
            reading_events: account::new_event_handle<SensorReading>(account)
        });

        // Emit registration event
        event::emit_event(
            &mut borrow_global_mut<Sensor>(account_addr).reading_events,
            RegisterSensorEvent {
                sensor_id,
                owner: account_addr,
                sensor_type,
                location
            }
        );
    }

    // Submit a sensor reading
    public entry fun submit_reading(
        account: &signer,
        sensor_id: String,
        temperature: u64,
        humidity: u64,
        pressure: u64,
        air_quality: u64
    ) acquires Sensor {
        let account_addr = signer::address_of(account);
        let sensor = borrow_global_mut<Sensor>(account_addr);
        
        // Verify ownership
        assert!(sensor.owner == account_addr, ENOT_AUTHORIZED);
        assert!(sensor.id == sensor_id, ESENSOR_NOT_FOUND);
        
        // Validate readings
        assert!(temperature <= 10000 && humidity <= 10000 && 
                pressure <= 200000 && air_quality <= 10000, EINVALID_READING);
        
        let timestamp = timestamp::now_seconds();
        
        // Update sensor
        sensor.last_reading = timestamp;
        
        // Create reading event
        let reading = SensorReading {
            sensor_id,
            timestamp,
            temperature,
            humidity,
            pressure,
            air_quality
        };
        
        // Emit reading event
        event::emit_event(&mut sensor.reading_events, reading);
    }

    // Get sensor data
    public fun get_sensor_data(account_addr: address): (String, address, u8, String, u64, u8) acquires Sensor {
        let sensor = borrow_global<Sensor>(account_addr);
        (
            sensor.id,
            sensor.owner,
            sensor.sensor_type,
            sensor.location,
            sensor.last_reading,
            sensor.status
        )
    }

    // Update sensor status
    public entry fun update_sensor_status(
        account: &signer,
        sensor_id: String,
        new_status: u8
    ) acquires Sensor {
        let account_addr = signer::address_of(account);
        let sensor = borrow_global_mut<Sensor>(account_addr);
        
        // Verify ownership
        assert!(sensor.owner == account_addr, ENOT_AUTHORIZED);
        assert!(sensor.id == sensor_id, ESENSOR_NOT_FOUND);
        
        // Update status
        sensor.status = new_status;
    }
} 