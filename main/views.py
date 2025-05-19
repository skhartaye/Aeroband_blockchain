from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import SensorReading
import json
from django.utils import timezone
from datetime import timedelta, datetime
import re
import requests
import qrcode
import base64
from io import BytesIO
import csv

def is_mobile(request):
    """Check if the request is from a mobile device"""
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'windows phone']
    return any(keyword in user_agent for keyword in mobile_keywords)

def get_device_type(request):
    """Determine the type of device based on user agent and request data"""
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    # Check for mobile app
    if 'sensorrelay' in user_agent:
        return 'mobile_app'
    
    # Check for regular mobile browser
    if is_mobile(request):
        return 'mobile_browser'
    
    # Check for ESP32 or other IoT devices
    if 'esp32' in user_agent or 'arduino' in user_agent:
        return 'iot_device'
    
    return 'desktop'

def home(request):
    """View for the home page - redirects based on device type"""
    device_type = get_device_type(request)
    
    if device_type in ['mobile_app', 'mobile_browser']:
        return mobile_view(request)
    return admin_dashboard(request)

def admin_dashboard(request):
    """Admin dashboard view showing latest sensor readings and statistics."""
    # Get the latest reading
    latest = SensorReading.objects.order_by('-timestamp').first()
    
    # Get the second latest reading for comparison
    previous = SensorReading.objects.order_by('-timestamp')
    if previous.count() > 1:
        previous = previous[1]
    else:
        previous = None # No previous reading available

    # Prepare data including status and percent change
    sensor_data = {
        'temperature': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'humidity': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'pressure': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'gas_resistance': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'ammonia': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'pm1_0': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'pm2_5': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'pm10': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
    }
    
    if latest:
        # Define example thresholds for status (adjust as needed)
        # Format: 'sensor_name': {'warning': (upper_threshold, lower_threshold), 'alert': (upper_threshold, lower_threshold)}
        # Use None for no upper or lower bound
        thresholds = {
            'temperature': {'warning': (30, 0), 'alert': (35, -10)},
            'humidity': {'warning': (70, 20), 'alert': (80, 10)},
            'pressure': {'warning': (1020, 1000), 'alert': (1030, 990)},
            'gas_resistance': {'warning': (200, 50), 'alert': (500, 20)},
            'ammonia': {'warning': (1, 0.1), 'alert': (2, 0.05)},
            'pm1_0': {'warning': (20, None), 'alert': (50, None)},
            'pm2_5': {'warning': (30, None), 'alert': (75, None)},
            'pm10': {'warning': (50, None), 'alert': (150, None)},
        }
        
        for field in sensor_data.keys():
            latest_value = getattr(latest, field, None)
            if latest_value is not None:
                sensor_data[field]['value'] = latest_value
                # Create a user-friendly display name
                sensor_data[field]['display_name'] = field.replace('_', ' ').title()
                
                # Determine Status
                status = 'Normal'
                if field in thresholds:
                    field_thresholds = thresholds[field]
                    
                    # Check Alert thresholds
                    if 'alert' in field_thresholds:
                        upper, lower = field_thresholds['alert']
                        if (upper is not None and latest_value > upper) or (lower is not None and latest_value < lower):
                            status = 'Alert'
                            
                    # Check Warning thresholds if not already Alert
                    if status != 'Alert' and 'warning' in field_thresholds:
                         upper, lower = field_thresholds['warning']
                         if (upper is not None and latest_value > upper) or (lower is not None and latest_value < lower):
                             status = 'Warning'
                            
                sensor_data[field]['status'] = status
                
                # Calculate Percent Change
                if previous:
                    previous_value = getattr(previous, field, None)
                    if previous_value is not None:
                        if previous_value != 0:
                            change = latest_value - previous_value
                            change_percent = (change / previous_value) * 100
                            sensor_data[field]['change'] = f"{change:+.1f}" # Format with sign and one decimal
                            sensor_data[field]['change_percent'] = f"{change_percent:+.1f}%" # Format with sign, one decimal, and percent sign
                        elif latest_value != 0:
                            # Handle case where previous was 0 and current is not
                            sensor_data[field]['change'] = f"{latest_value:+.1f}"
                            sensor_data[field]['change_percent'] = "> +1000%" # Indicate a significant increase from zero
                        else:
                            # Both are zero, no change
                            sensor_data[field]['change'] = "0.0"
                            sensor_data[field]['change_percent'] = "0.0%"
                    else:
                        # Previous value is None
                        sensor_data[field]['change'] = 'N/A'
                        sensor_data[field]['change_percent'] = 'N/A'
                else:
                    sensor_data[field]['change'] = 'N/A'
                    sensor_data[field]['change_percent'] = 'N/A'
    else:
        # No sensor readings available - don't attempt to access field variable here
        pass
    
    context = {
        'sensor_data': sensor_data,
        'latest_timestamp': latest.timestamp if latest else None
    }
    return render(request, 'main/admin_dashboard.html', context)

def data_management(request):
    """View for data management page"""
    # Get all readings from the last 24 hours
    time_threshold = timezone.now() - timedelta(hours=24)
    readings = SensorReading.objects.filter(timestamp__gte=time_threshold).order_by('timestamp')
    
    # Count total readings
    total_readings = readings.count()
    
    # Determine interval based on data volume
    # If more than 180 readings (3 readings per minute for 1 hour), use 3-minute intervals
    # Otherwise use 1-minute intervals
    interval_minutes = 3 if total_readings > 180 else 1
    
    # Aggregate readings by time interval
    aggregated_readings = []
    current_interval = None
    interval_data = {
        'timestamp': None,
        'temperature': [],
        'humidity': [],
        'pressure': [],
        'gas_resistance': [],
        'ammonia': [],
        'pm1_0': [],
        'pm2_5': [],
        'pm10': []
    }
    
    for reading in readings:
        # Round timestamp to nearest interval
        reading_time = reading.timestamp.replace(second=0, microsecond=0)
        interval_time = reading_time - timedelta(
            minutes=reading_time.minute % interval_minutes,
            seconds=reading_time.second,
            microseconds=reading_time.microsecond
        )
        
        if current_interval != interval_time:
            # Save previous interval if exists
            if current_interval is not None:
                aggregated_readings.append({
                    'timestamp': current_interval,
                    'temperature': sum(interval_data['temperature']) / len(interval_data['temperature']) if interval_data['temperature'] else None,
                    'humidity': sum(interval_data['humidity']) / len(interval_data['humidity']) if interval_data['humidity'] else None,
                    'pressure': sum(interval_data['pressure']) / len(interval_data['pressure']) if interval_data['pressure'] else None,
                    'gas_resistance': sum(interval_data['gas_resistance']) / len(interval_data['gas_resistance']) if interval_data['gas_resistance'] else None,
                    'ammonia': sum(interval_data['ammonia']) / len(interval_data['ammonia']) if interval_data['ammonia'] else None,
                    'pm1_0': sum(interval_data['pm1_0']) / len(interval_data['pm1_0']) if interval_data['pm1_0'] else None,
                    'pm2_5': sum(interval_data['pm2_5']) / len(interval_data['pm2_5']) if interval_data['pm2_5'] else None,
                    'pm10': sum(interval_data['pm10']) / len(interval_data['pm10']) if interval_data['pm10'] else None
                })
            
            # Start new interval
            current_interval = interval_time
            interval_data = {
                'timestamp': interval_time,
                'temperature': [],
                'humidity': [],
                'pressure': [],
                'gas_resistance': [],
                'ammonia': [],
                'pm1_0': [],
                'pm2_5': [],
                'pm10': []
            }
        
        # Add reading to current interval - check for None values
        interval_data['temperature'].append(reading.temperature if reading.temperature is not None else 0)
        interval_data['humidity'].append(reading.humidity if reading.humidity is not None else 0)
        interval_data['pressure'].append(reading.pressure if reading.pressure is not None else 0)
        interval_data['gas_resistance'].append(reading.gas_resistance if reading.gas_resistance is not None else 0)
        interval_data['ammonia'].append(reading.ammonia if reading.ammonia is not None else 0)
        interval_data['pm1_0'].append(reading.pm1_0 if reading.pm1_0 is not None else 0)
        interval_data['pm2_5'].append(reading.pm2_5 if reading.pm2_5 is not None else 0)
        interval_data['pm10'].append(reading.pm10 if reading.pm10 is not None else 0)
    
    # Add the last interval if it exists
    if current_interval is not None:
        aggregated_readings.append({
            'timestamp': current_interval,
            'temperature': sum(interval_data['temperature']) / len(interval_data['temperature']) if interval_data['temperature'] else None,
            'humidity': sum(interval_data['humidity']) / len(interval_data['humidity']) if interval_data['humidity'] else None,
            'pressure': sum(interval_data['pressure']) / len(interval_data['pressure']) if interval_data['pressure'] else None,
            'gas_resistance': sum(interval_data['gas_resistance']) / len(interval_data['gas_resistance']) if interval_data['gas_resistance'] else None,
            'ammonia': sum(interval_data['ammonia']) / len(interval_data['ammonia']) if interval_data['ammonia'] else None,
            'pm1_0': sum(interval_data['pm1_0']) / len(interval_data['pm1_0']) if interval_data['pm1_0'] else None,
            'pm2_5': sum(interval_data['pm2_5']) / len(interval_data['pm2_5']) if interval_data['pm2_5'] else None,
            'pm10': sum(interval_data['pm10']) / len(interval_data['pm10']) if interval_data['pm10'] else None
        })
    
    # Prepare data for charts
    chart_data_dict = {
        'timestamps': [r['timestamp'].strftime('%Y-%m-%d %H:%M:%S') for r in aggregated_readings],
        'temperature': [r['temperature'] for r in aggregated_readings],
        'humidity': [r['humidity'] for r in aggregated_readings],
        'pressure': [r['pressure'] for r in aggregated_readings],
        'gas_resistance': [r['gas_resistance'] for r in aggregated_readings],
        'ammonia': [r['ammonia'] for r in aggregated_readings],
        'pm1_0': [r['pm1_0'] for r in aggregated_readings],
        'pm2_5': [r['pm2_5'] for r in aggregated_readings],
        'pm10': [r['pm10'] for r in aggregated_readings]
    }
    
    context = {
        'readings': aggregated_readings,
        'interval_minutes': interval_minutes,
        'total_readings': total_readings,
        'chart_data': chart_data_dict
    }
    return render(request, 'main/data_management.html', context)

def devices(request):
    """View for devices management page"""
    # Get unique devices and their latest readings
    devices = []
    unique_devices = SensorReading.objects.values('device_id').distinct()
    
    for device in unique_devices:
        device_id = device['device_id']
        latest_reading = SensorReading.objects.filter(device_id=device_id).order_by('-timestamp').first()
        
        if latest_reading:
            # Determine device type based on the device_id pattern
            device_type = 'unknown'
            if 'mobile' in device_id.lower():
                device_type = 'mobile_app'
            elif 'esp32' in device_id.lower() or 'arduino' in device_id.lower():
                device_type = 'iot_device'
            
            devices.append({
                'device_id': device_id,
                'device_type': device_type,
                'last_seen': latest_reading.timestamp,
                'temperature': latest_reading.temperature,
                'humidity': latest_reading.humidity,
                'pressure': latest_reading.pressure,
                'gas_resistance': latest_reading.gas_resistance,
                'ammonia': latest_reading.ammonia,
                'pm1_0': latest_reading.pm1_0,
                'pm2_5': latest_reading.pm2_5,
                'pm10': latest_reading.pm10,
                'is_online': (timezone.now() - latest_reading.timestamp) < timedelta(minutes=5)
            })
    
    return render(request, 'main/devices.html', {'devices': devices})

def users(request):
    """View for users management page"""
    return render(request, 'main/users.html')

def settings(request):
    """View for settings page"""
    return render(request, 'main/settings.html')

def sensor_graphs(request):
    """View for sensor graphs page showing historical sensor data"""
    # Get readings from the last 24 hours by default
    try:
        time_filter = int(request.GET.get('time_filter', 24))
    except (ValueError, TypeError):
        # Handle invalid input by defaulting to 24 hours
        time_filter = 24
    
    # Make sure time_filter is within reasonable bounds
    allowed_filters = [1, 6, 12, 24, 72, 168]
    if time_filter not in allowed_filters:
        time_filter = 24
    
    time_threshold = timezone.now() - timedelta(hours=time_filter)
    
    # Get sensor readings
    readings = SensorReading.objects.filter(
        timestamp__gte=time_threshold
    ).order_by('timestamp')
    
    # Count total readings (for display purposes)
    readings_count = readings.count()
    
    # Set a fixed 3-minute interval for aggregation
    interval_minutes = 3
    
    # Aggregate readings by 3-minute intervals
    aggregated_readings = []
    current_interval = None
    interval_data = {
        'timestamp': None,
        'temperature': [],
        'humidity': [],
        'pressure': [],
        'gas_resistance': [],
        'ammonia': [],
        'pm1_0': [],
        'pm2_5': [],
        'pm10': []
    }
    
    for reading in readings:
        # Round timestamp to nearest 3-minute interval
        reading_time = reading.timestamp.replace(second=0, microsecond=0)
        interval_time = reading_time - timedelta(
            minutes=reading_time.minute % interval_minutes,
            seconds=reading_time.second,
            microseconds=reading_time.microsecond
        )
        
        if current_interval != interval_time:
            # Save previous interval if exists
            if current_interval is not None:
                aggregated_readings.append({
                    'timestamp': current_interval,
                    'temperature': sum(interval_data['temperature']) / len(interval_data['temperature']) if interval_data['temperature'] else None,
                    'humidity': sum(interval_data['humidity']) / len(interval_data['humidity']) if interval_data['humidity'] else None,
                    'pressure': sum(interval_data['pressure']) / len(interval_data['pressure']) if interval_data['pressure'] else None,
                    'gas_resistance': sum(interval_data['gas_resistance']) / len(interval_data['gas_resistance']) if interval_data['gas_resistance'] else None,
                    'ammonia': sum(interval_data['ammonia']) / len(interval_data['ammonia']) if interval_data['ammonia'] else None,
                    'pm1_0': sum(interval_data['pm1_0']) / len(interval_data['pm1_0']) if interval_data['pm1_0'] else None,
                    'pm2_5': sum(interval_data['pm2_5']) / len(interval_data['pm2_5']) if interval_data['pm2_5'] else None,
                    'pm10': sum(interval_data['pm10']) / len(interval_data['pm10']) if interval_data['pm10'] else None
                })
            
            # Start new interval
            current_interval = interval_time
            interval_data = {
                'timestamp': interval_time,
                'temperature': [],
                'humidity': [],
                'pressure': [],
                'gas_resistance': [],
                'ammonia': [],
                'pm1_0': [],
                'pm2_5': [],
                'pm10': []
            }
        
        # Add reading to current interval
        interval_data['temperature'].append(reading.temperature if reading.temperature is not None else 0)
        interval_data['humidity'].append(reading.humidity if reading.humidity is not None else 0)
        interval_data['pressure'].append(reading.pressure if reading.pressure is not None else 0)
        interval_data['gas_resistance'].append(reading.gas_resistance if reading.gas_resistance is not None else 0)
        interval_data['ammonia'].append(reading.ammonia if reading.ammonia is not None else 0)
        interval_data['pm1_0'].append(reading.pm1_0 if reading.pm1_0 is not None else 0)
        interval_data['pm2_5'].append(reading.pm2_5 if reading.pm2_5 is not None else 0)
        interval_data['pm10'].append(reading.pm10 if reading.pm10 is not None else 0)
    
    # Add the last interval if it exists
    if current_interval is not None:
        aggregated_readings.append({
            'timestamp': current_interval,
            'temperature': sum(interval_data['temperature']) / len(interval_data['temperature']) if interval_data['temperature'] else None,
            'humidity': sum(interval_data['humidity']) / len(interval_data['humidity']) if interval_data['humidity'] else None,
            'pressure': sum(interval_data['pressure']) / len(interval_data['pressure']) if interval_data['pressure'] else None,
            'gas_resistance': sum(interval_data['gas_resistance']) / len(interval_data['gas_resistance']) if interval_data['gas_resistance'] else None,
            'ammonia': sum(interval_data['ammonia']) / len(interval_data['ammonia']) if interval_data['ammonia'] else None,
            'pm1_0': sum(interval_data['pm1_0']) / len(interval_data['pm1_0']) if interval_data['pm1_0'] else None,
            'pm2_5': sum(interval_data['pm2_5']) / len(interval_data['pm2_5']) if interval_data['pm2_5'] else None,
            'pm10': sum(interval_data['pm10']) / len(interval_data['pm10']) if interval_data['pm10'] else None
        })
    
    # Format data for charts
    chart_data = {
        'timestamps': json.dumps([reading['timestamp'].strftime('%H:%M') for reading in aggregated_readings]),
        'temperature': json.dumps([reading['temperature'] for reading in aggregated_readings]),
        'humidity': json.dumps([reading['humidity'] for reading in aggregated_readings]),
        'pressure': json.dumps([reading['pressure'] for reading in aggregated_readings]),
        'gas_resistance': json.dumps([reading['gas_resistance'] for reading in aggregated_readings]),
        'ammonia': json.dumps([reading['ammonia'] for reading in aggregated_readings]),
        'pm1_0': json.dumps([reading['pm1_0'] for reading in aggregated_readings]),
        'pm2_5': json.dumps([reading['pm2_5'] for reading in aggregated_readings]),
        'pm10': json.dumps([reading['pm10'] for reading in aggregated_readings]),
    }
    
    # Prepare context with chart data and time filter options
    context = {
        'chart_data': chart_data,
        'time_filter': time_filter,
        'readings_count': readings_count,
        'aggregated_count': len(aggregated_readings),
        'interval_minutes': interval_minutes
    }
    
    return render(request, 'main/sensor_graphs.html', context)

def mobile_view(request):
    """View for the mobile interface"""
    # Get the latest reading
    latest = SensorReading.objects.order_by('-timestamp').first()
    
    # Get the second latest reading for comparison
    previous = SensorReading.objects.order_by('-timestamp')
    if previous.count() > 1:
        previous = previous[1]
    else:
        previous = None # No previous reading available

    # Prepare data including status and percent change
    sensor_data = {
        'temperature': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'humidity': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'pressure': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'gas_resistance': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'ammonia': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'pm1_0': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'pm2_5': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'pm10': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
    }
    
    if latest:
        # Define example thresholds for status (adjust as needed)
        # Format: 'sensor_name': {'warning': (upper_threshold, lower_threshold), 'alert': (upper_threshold, lower_threshold)}
        # Use None for no upper or lower bound
        thresholds = {
            'temperature': {'warning': (30, 0), 'alert': (35, -10)},
            'humidity': {'warning': (70, 20), 'alert': (80, 10)},
            'pressure': {'warning': (1020, 1000), 'alert': (1030, 990)},
            'gas_resistance': {'warning': (200, 50), 'alert': (500, 20)},
            'ammonia': {'warning': (1, 0.1), 'alert': (2, 0.05)},
            'pm1_0': {'warning': (20, None), 'alert': (50, None)},
            'pm2_5': {'warning': (30, None), 'alert': (75, None)},
            'pm10': {'warning': (50, None), 'alert': (150, None)},
        }
        
        for field in sensor_data.keys():
            latest_value = getattr(latest, field, None)
            if latest_value is not None:
                sensor_data[field]['value'] = latest_value
                # Create a user-friendly display name
                sensor_data[field]['display_name'] = field.replace('_', ' ').title()
                
                # Determine Status
                status = 'Normal'
                if field in thresholds:
                    field_thresholds = thresholds[field]
                    
                    # Check Alert thresholds
                    if 'alert' in field_thresholds:
                        upper, lower = field_thresholds['alert']
                        if (upper is not None and latest_value > upper) or (lower is not None and latest_value < lower):
                            status = 'Alert'
                            
                    # Check Warning thresholds if not already Alert
                    if status != 'Alert' and 'warning' in field_thresholds:
                         upper, lower = field_thresholds['warning']
                         if (upper is not None and latest_value > upper) or (lower is not None and latest_value < lower):
                             status = 'Warning'
                            
                sensor_data[field]['status'] = status
                
                # Calculate Percent Change
                if previous:
                    previous_value = getattr(previous, field, None)
                    if previous_value is not None:
                        if previous_value != 0:
                            change = latest_value - previous_value
                            change_percent = (change / previous_value) * 100
                            sensor_data[field]['change'] = f"{change:+.1f}" # Format with sign and one decimal
                            sensor_data[field]['change_percent'] = f"{change_percent:+.1f}%" # Format with sign, one decimal, and percent sign
                        elif latest_value != 0:
                            # Handle case where previous was 0 and current is not
                            sensor_data[field]['change'] = f"{latest_value:+.1f}"
                            sensor_data[field]['change_percent'] = "> +1000%" # Indicate a significant increase from zero
                        else:
                            # Both are zero, no change
                            sensor_data[field]['change'] = "0.0"
                            sensor_data[field]['change_percent'] = "0.0%"
                    else:
                        # Previous value is None
                        sensor_data[field]['change'] = 'N/A'
                        sensor_data[field]['change_percent'] = 'N/A'
                else:
                    sensor_data[field]['change'] = 'N/A'
                    sensor_data[field]['change_percent'] = 'N/A'

    context = {
        'sensor_data': sensor_data,
        'latest_timestamp': latest.timestamp if latest else None
    }
    return render(request, 'main/mobile_view.html', context)

def mobile_history(request):
    """View for mobile history page"""
    return redirect('ble_bridge')

def mobile_alerts(request):
    """View for mobile alerts page"""
    return redirect('ble_bridge')

def mobile_settings(request):
    """View for mobile settings page"""
    return redirect('ble_bridge')

def ble_bridge(request):
    """Mobile dashboard view showing latest sensor readings and statistics."""
    # Get the latest reading
    latest = SensorReading.objects.order_by('-timestamp').first()
    
    # Get the second latest reading for comparison
    previous = SensorReading.objects.order_by('-timestamp')
    if previous.count() > 1:
        previous = previous[1]
    else:
        previous = None

    # Prepare data including status and percent change
    sensor_data = {
        'temperature': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'humidity': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'pressure': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'gas_resistance': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'ammonia': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'pm1_0': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'pm2_5': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
        'pm10': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A'},
    }
    
    if latest:
        # Define thresholds for status
        thresholds = {
            'temperature': {'warning': (30, 0), 'alert': (35, -10)},
            'humidity': {'warning': (70, 20), 'alert': (80, 10)},
            'pressure': {'warning': (1020, 1000), 'alert': (1030, 990)},
            'gas_resistance': {'warning': (200, 50), 'alert': (500, 20)},
            'ammonia': {'warning': (1, 0.1), 'alert': (2, 0.05)},
            'pm1_0': {'warning': (20, None), 'alert': (50, None)},
            'pm2_5': {'warning': (30, None), 'alert': (75, None)},
            'pm10': {'warning': (50, None), 'alert': (150, None)},
        }
        
        for field in sensor_data.keys():
            latest_value = getattr(latest, field, None)
            if latest_value is not None:
                sensor_data[field]['value'] = latest_value
                sensor_data[field]['display_name'] = field.replace('_', ' ').title()
                
                # Determine Status
                status = 'Normal'
                if field in thresholds:
                    field_thresholds = thresholds[field]
                    
                    if 'alert' in field_thresholds:
                        upper, lower = field_thresholds['alert']
                        if (upper is not None and latest_value > upper) or (lower is not None and latest_value < lower):
                            status = 'Alert'
                            
                    if status != 'Alert' and 'warning' in field_thresholds:
                         upper, lower = field_thresholds['warning']
                         if (upper is not None and latest_value > upper) or (lower is not None and latest_value < lower):
                             status = 'Warning'
                            
                sensor_data[field]['status'] = status
                
                # Calculate Percent Change
                if previous:
                    previous_value = getattr(previous, field, None)
                    if previous_value is not None:
                        if previous_value != 0:
                            change = latest_value - previous_value
                            change_percent = (change / previous_value) * 100
                            sensor_data[field]['change'] = f"{change:+.1f}"
                            sensor_data[field]['change_percent'] = f"{change_percent:+.1f}%"
                        elif latest_value != 0:
                            sensor_data[field]['change'] = f"{latest_value:+.1f}"
                            sensor_data[field]['change_percent'] = "> +1000%"
                        else:
                            sensor_data[field]['change'] = "0.0"
                            sensor_data[field]['change_percent'] = "0.0%"
                    else:
                        sensor_data[field]['change'] = 'N/A'
                        sensor_data[field]['change_percent'] = 'N/A'
                else:
                    sensor_data[field]['change'] = 'N/A'
                    sensor_data[field]['change_percent'] = 'N/A'
    
    context = {
        'sensor_data': sensor_data,
        'latest_timestamp': latest.timestamp if latest else None
    }
    return render(request, 'main/ble_bridge.html', context)

@csrf_exempt
def receive_sensor_data(request):
    """API endpoint to receive sensor data from mobile device."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(f"[API] Received data from device: {data}")
            
            # Create new sensor reading
            reading = SensorReading.objects.create(
                device_id=data.get('device_id', 'unknown'),  # Add device_id with a default value
                temperature=data.get('temperature'),
                humidity=data.get('humidity'),
                pressure=data.get('pressure'),
                gas_resistance=data.get('gas_resistance'),
                ammonia=data.get('ammonia'),
                pm1_0=data.get('pm1_0'),
                pm2_5=data.get('pm2_5'),
                pm10=data.get('pm10')
            )
            
            return JsonResponse({
                'status': 'success',
                'timestamp': reading.timestamp.isoformat()
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)

def get_sensor_data(request):
    """API endpoint to get latest and recent sensor readings."""
    try:
        # Get the latest reading
        latest = SensorReading.objects.order_by('-timestamp').first()
        
        # Get recent readings (last 10)
        recent = list(SensorReading.objects.order_by('-timestamp')[:10].values())
        
        return JsonResponse({
            'status': 'success',
            'latest': {
                'temperature': latest.temperature,
                'humidity': latest.humidity,
                'pressure': latest.pressure,
                'gas_resistance': latest.gas_resistance,
                'ammonia': latest.ammonia,
                'pm1_0': latest.pm1_0,
                'pm2_5': latest.pm2_5,
                'pm10': latest.pm10,
                'timestamp': latest.timestamp.isoformat()
            } if latest else None,
            'recent': recent
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@require_http_methods(["GET"])
def get_latest_readings(request):
    """API endpoint to get latest sensor readings"""
    try:
        # Get readings from the last 24 hours
        time_threshold = timezone.now() - timedelta(hours=24)
        readings = SensorReading.objects.filter(
            timestamp__gte=time_threshold
        ).order_by('-timestamp')
        
        data = [{
            'device_id': r.device_id,
            'temperature': r.temperature,
            'humidity': r.humidity,
            'pressure': r.pressure,
            'gas_resistance': r.gas_resistance,
            'ammonia': r.ammonia,
            'pm1_0': r.pm1_0,
            'pm2_5': r.pm2_5,
            'pm10': r.pm10,
            'timestamp': r.timestamp.isoformat()
        } for r in readings]
        
        return JsonResponse({
            'status': 'success',
            'readings': data
        })
        
    except Exception as e:
        print(f"[API] Error getting latest readings: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@require_http_methods(["GET"])
def get_latest_readings_json(request):
    """API endpoint to get latest sensor readings with status and percent change as JSON."""
    try:
        # Get the latest reading
        latest = SensorReading.objects.order_by('-timestamp').first()
        
        # Get the second latest reading for comparison
        previous = SensorReading.objects.order_by('-timestamp')
        if previous.count() > 1:
            previous = previous[1]
        else:
            previous = None # No previous reading available

        # Prepare data including status and percent change (same logic as admin_dashboard view)
        sensor_data = {
            'temperature': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A', 'display_name': 'Temperature'},
            'humidity': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A', 'display_name': 'Humidity'},
            'pressure': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A', 'display_name': 'Pressure'},
            'gas_resistance': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A', 'display_name': 'Gas Resistance'},
            'ammonia': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A', 'display_name': 'Ammonia'},
            'pm1_0': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A', 'display_name': 'Pm1 0'},
            'pm2_5': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A', 'display_name': 'Pm2 5'},
            'pm10': {'value': None, 'status': 'N/A', 'change': 'N/A', 'change_percent': 'N/A', 'display_name': 'Pm10'},
        }
        
        if latest:
            # Define example thresholds for status (adjust as needed)
            thresholds = {
                'temperature': {'warning': (30, 0), 'alert': (35, -10)},
                'humidity': {'warning': (70, 20), 'alert': (80, 10)},
                'pressure': {'warning': (1020, 1000), 'alert': (1030, 990)},
                'gas_resistance': {'warning': (200, 50), 'alert': (500, 20)},
                'ammonia': {'warning': (1, 0.1), 'alert': (2, 0.05)},
                'pm1_0': {'warning': (20, None), 'alert': (50, None)},
                'pm2_5': {'warning': (30, None), 'alert': (75, None)},
                'pm10': {'warning': (50, None), 'alert': (150, None)},
            }

            for field in sensor_data.keys():
                 latest_value = getattr(latest, field, None)
                 if latest_value is not None:
                     sensor_data[field]['value'] = latest_value
                     sensor_data[field]['display_name'] = field.replace('_', ' ').title()

                     # Determine Status
                     status = 'Normal'
                     if field in thresholds:
                         field_thresholds = thresholds[field]
                         if 'alert' in field_thresholds:
                             upper, lower = field_thresholds['alert']
                             if (upper is not None and latest_value > upper) or (lower is not None and latest_value < lower):
                                 status = 'Alert'
                         if status != 'Alert' and 'warning' in field_thresholds:
                             upper, lower = field_thresholds['warning']
                             if (upper is not None and latest_value > upper) or (lower is not None and latest_value < lower):
                                 status = 'Warning'
                     sensor_data[field]['status'] = status

                     # Calculate Percent Change
                     if previous:
                         previous_value = getattr(previous, field, None)
                         if previous_value is not None:
                             if previous_value != 0:
                                 change = latest_value - previous_value
                                 change_percent = (change / previous_value) * 100
                                 sensor_data[field]['change'] = f"{change:+.1f}"
                                 sensor_data[field]['change_percent'] = f"{change_percent:+.1f}%"
                             elif latest_value != 0:
                                 sensor_data[field]['change'] = f"{latest_value:+.1f}"
                                 sensor_data[field]['change_percent'] = "> +1000%"
                             else:
                                 sensor_data[field]['change'] = "0.0"
                                 sensor_data[field]['change_percent'] = "0.0%"
                         else:
                             sensor_data[field]['change'] = 'N/A'
                             sensor_data[field]['change_percent'] = 'N/A'
                     else:
                         sensor_data[field]['change'] = 'N/A'
                         sensor_data[field]['change_percent'] = 'N/A'

        return JsonResponse({
            'status': 'success',
            'sensor_data': sensor_data,
            'latest_timestamp': latest.timestamp.isoformat() if latest else None
        })

    except Exception as e:
        print(f"[API] Error getting latest readings JSON: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@require_http_methods(["GET"])
def latest_readings_json(request):
    latest_reading = SensorReading.objects.order_by('-timestamp').first()
    if latest_reading:
        data = {
            'temperature': latest_reading.temperature,
            'humidity': latest_reading.humidity,
            'pressure': latest_reading.pressure,
            'gas_resistance': latest_reading.gas_resistance,
            'ammonia': latest_reading.ammonia,
            'pm1_0': latest_reading.pm1_0,
            'pm2_5': latest_reading.pm2_5,
            'pm10': latest_reading.pm10,
            'timestamp': latest_reading.timestamp.isoformat()
        }
        response = JsonResponse(data)
        response['Content-Type'] = 'application/json'
        return response
    return JsonResponse({'error': 'No readings available'}, status=404)

@require_http_methods(["GET"])
def latest_sensor_data(request):
    """API endpoint to get the latest sensor data for AJAX updates."""
    try:
        # Get the latest reading
        latest_reading = SensorReading.objects.latest('timestamp')
        
        # Get the previous reading for calculating changes
        try:
            previous_reading = SensorReading.objects.filter(
                timestamp__lt=latest_reading.timestamp
            ).latest('timestamp')
        except SensorReading.DoesNotExist:
            previous_reading = None

        # Define consistent thresholds for status - same as in other functions
        thresholds = {
            'temperature': {'warning': (30, 0), 'alert': (35, -10)},
            'humidity': {'warning': (70, 20), 'alert': (80, 10)},
            'pressure': {'warning': (1020, 1000), 'alert': (1030, 990)},
            'gas_resistance': {'warning': (200, 50), 'alert': (500, 20)},
            'ammonia': {'warning': (1, 0.1), 'alert': (2, 0.05)},
            'pm1_0': {'warning': (20, None), 'alert': (50, None)},
            'pm2_5': {'warning': (30, None), 'alert': (75, None)},
            'pm10': {'warning': (50, None), 'alert': (150, None)},
        }

        # Prepare sensor data
        sensor_data = {}
        for field in ['temperature', 'humidity', 'pressure', 'gas_resistance', 'ammonia', 'pm1_0', 'pm2_5', 'pm10']:
            value = getattr(latest_reading, field)
            if value is not None:
                # Calculate change if we have a previous reading
                if previous_reading:
                    prev_value = getattr(previous_reading, field)
                    if prev_value is not None and prev_value != 0:
                        change = value - prev_value
                        change_percent = (change / prev_value) * 100
                        change_str = f"{change:+.1f}"
                        change_percent_str = f"{'+' if change_percent > 0 else ''}{change_percent:.1f}%"
                    elif prev_value == 0 and value != 0:
                        change_str = f"{value:+.1f}"
                        change_percent_str = "> +1000%"
                    else:
                        change_str = "0.0"
                        change_percent_str = "0.0%"
                else:
                    change_str = 'N/A'
                    change_percent_str = 'N/A'

                # Determine status based on thresholds
                status = 'Normal'
                if field in thresholds:
                    field_thresholds = thresholds[field]
                    # Check Alert thresholds
                    if 'alert' in field_thresholds:
                        upper, lower = field_thresholds['alert']
                        if (upper is not None and value > upper) or (lower is not None and value < lower):
                            status = 'Alert'
                    # Check Warning thresholds if not already Alert
                    if status != 'Alert' and 'warning' in field_thresholds:
                        upper, lower = field_thresholds['warning']
                        if (upper is not None and value > upper) or (lower is not None and value < lower):
                            status = 'Warning'

                sensor_data[field] = {
                    'value': value,
                    'change': change_str,
                    'change_percent': change_percent_str,
                    'status': status,
                    'display_name': field.replace('_', ' ').title()
                }

        response = JsonResponse({
            'timestamp': latest_reading.timestamp.isoformat(),
            'sensor_data': sensor_data
        })
        response['Content-Type'] = 'application/json'
        return response
    except SensorReading.DoesNotExist:
        response = JsonResponse({
            'timestamp': timezone.now().isoformat(),
            'sensor_data': {}
        })
        response['Content-Type'] = 'application/json'
        return response
    except Exception as e:
        response = JsonResponse({
            'error': str(e)
        }, status=500)
        response['Content-Type'] = 'application/json'
        return response

@require_http_methods(["POST"])
@csrf_exempt
def delete_all_data(request):
    """API endpoint to delete all sensor readings"""
    try:
        # Delete all records
        SensorReading.objects.all().delete()
        return JsonResponse({
            'status': 'success',
            'message': 'All data deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def get_ngrok_url():
    """Get the current ngrok URL."""
    try:
        response = requests.get("http://localhost:4040/api/tunnels")
        tunnels = response.json()["tunnels"]
        
        for tunnel in tunnels:
            if tunnel["proto"] == "https":
                return tunnel["public_url"]
    except:
        return None

@require_http_methods(["GET"])
def sensor_records(request):
    """API endpoint to get sensor records for data management page with filtering, pagination and sorting."""
    try:
        # Get parameters from request
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 20))
        sort_field = request.GET.get('sort_field', 'timestamp')
        sort_dir = request.GET.get('sort_dir', 'desc')
        status_filter = request.GET.get('status', 'all')
        time_filter = int(request.GET.get('time_filter', 24))
        
        # Calculate time threshold based on filter
        time_threshold = timezone.now() - timedelta(hours=time_filter)
        
        # Start with base query
        query = SensorReading.objects.filter(timestamp__gte=time_threshold)
        
        # Apply status filter if not 'all'
        if status_filter != 'all':
            status_readings = []
            for reading in query:
                if get_overall_status(reading).lower() == status_filter.lower():
                    status_readings.append(reading.id)
            query = query.filter(id__in=status_readings)
        
        # Count total matching records for pagination
        total_count = query.count()
        
        # Apply sorting
        if sort_field == 'timestamp':
            sort_prefix = '-' if sort_dir == 'desc' else ''
            query = query.order_by(f'{sort_prefix}timestamp')
        else:
            # For other fields, we need to sort after fetching
            query = query.order_by('-timestamp')  # Default sort for now
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query[offset:offset + limit]
        
        # Format results
        records = []
        for reading in query:
            overall_status = get_overall_status(reading)
            record = {
                'id': reading.id,
                'timestamp': reading.timestamp.isoformat(),
                'sensor': 'Multiple Sensors',
                'value': f"Temp: {reading.temperature}°C, Humidity: {reading.humidity}%",
                'status': overall_status
            }
            records.append(record)
        
        return JsonResponse({
            'status': 'success',
            'records': records,
            'total': total_count,
            'page': page,
            'limit': limit
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def export_sensor_data(request):
    """API endpoint to export sensor data as CSV or JSON."""
    try:
        # Get parameters
        format_type = request.GET.get('format', 'csv')
        time_filter = int(request.GET.get('time_filter', 24))
        status_filter = request.GET.get('status', 'all')
        
        # Calculate time threshold
        time_threshold = timezone.now() - timedelta(hours=time_filter)
        
        # Get readings
        readings = SensorReading.objects.filter(timestamp__gte=time_threshold)
        
        # Apply status filter if not 'all'
        if status_filter != 'all':
            status_readings = []
            for reading in readings:
                if get_overall_status(reading).lower() == status_filter.lower():
                    status_readings.append(reading.id)
            readings = readings.filter(id__in=status_readings)
        
        # Sort by timestamp descending
        readings = readings.order_by('-timestamp')
        
        if format_type == 'csv':
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="sensor_data.csv"'
            
            writer = csv.writer(response)
            # Write header
            writer.writerow(['Timestamp', 'Device ID', 'Temperature', 'Humidity', 'Pressure', 
                           'Gas Resistance', 'Ammonia', 'PM1.0', 'PM2.5', 'PM10', 'Status'])
            
            # Write data rows
            for reading in readings:
                writer.writerow([
                    reading.timestamp,
                    reading.device_id,
                    reading.temperature,
                    reading.humidity,
                    reading.pressure,
                    reading.gas_resistance,
                    reading.ammonia,
                    reading.pm1_0,
                    reading.pm2_5,
                    reading.pm10,
                    get_overall_status(reading)
                ])
                
            return response
        else:
            # JSON format
            data = [{
                'timestamp': reading.timestamp.isoformat(),
                'device_id': reading.device_id,
                'temperature': reading.temperature,
                'humidity': reading.humidity,
                'pressure': reading.pressure,
                'gas_resistance': reading.gas_resistance,
                'ammonia': reading.ammonia,
                'pm1_0': reading.pm1_0,
                'pm2_5': reading.pm2_5,
                'pm10': reading.pm10,
                'status': get_overall_status(reading)
            } for reading in readings]
            
            response = JsonResponse(data, safe=False)
            response['Content-Disposition'] = 'attachment; filename="sensor_data.json"'
            return response
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def generate_qr_code(url):
    """Generate QR code for the given URL."""
    try:
        print("Attempting to import required packages...")
        import qrcode
        print("Successfully imported qrcode")
        # Attempting to import PyPNG image backend
        from qrcode.image.pure import PyPNGImage
        print("Successfully imported qrcode.image.pure.PyPNGImage")
        from io import BytesIO
        import base64
        print("Successfully imported all required packages")

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url + '/ble-bridge/')
        qr.make(fit=True)

        # Use PyPNGImage as the image factory
        img = qr.make_image(image_factory=PyPNGImage, fill_color="black", back_color="white")
        buffered = BytesIO()
        # PyPNGImage save method takes the stream and optional kind
        img.save(buffered, kind='PNG') # Explicitly save as PNG
        return base64.b64encode(buffered.getvalue()).decode()
    except ImportError as e:
        missing_package = str(e).split("'")[1] if "'" in str(e) else "unknown"
        print(f"Required package not available: {missing_package}")
        print(f"Full error: {str(e)}")
        print("Please install required packages: pip install qrcode pypng")
        return None
    except Exception as e:
        print(f"Error generating QR code: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None

def redirect_page(request):
    """Render the redirect page."""
    ngrok_url = get_ngrok_url()
    qr_code = generate_qr_code(ngrok_url) if ngrok_url else None
    
    return render(request, 'main/redirect.html', {
        'ngrok_url': ngrok_url,
        'qr_code': qr_code
    })

@require_http_methods(["GET"])
def sensor_record_detail(request, record_id):
    """API endpoint to get detailed information about a specific sensor record."""
    try:
        reading = SensorReading.objects.get(id=record_id)
        
        # Get statuses for each sensor value
        temperature_status = get_sensor_status('temperature', reading.temperature)
        humidity_status = get_sensor_status('humidity', reading.humidity)
        pressure_status = get_sensor_status('pressure', reading.pressure)
        
        data = {
            'id': reading.id,
            'timestamp': reading.timestamp.isoformat(),
            'sensor': 'Multiple Sensors',
            'temperature': {
                'value': reading.temperature,
                'status': temperature_status,
                'unit': '°C'
            },
            'humidity': {
                'value': reading.humidity,
                'status': humidity_status,
                'unit': '%'
            },
            'pressure': {
                'value': reading.pressure,
                'status': pressure_status,
                'unit': 'hPa'
            }
        }
        
        # Add other sensor values if they exist
        if reading.gas_resistance is not None:
            data['gas_resistance'] = {
                'value': reading.gas_resistance,
                'status': get_sensor_status('gas_resistance', reading.gas_resistance),
                'unit': 'Ohms'
            }
            
        if reading.ammonia is not None:
            data['ammonia'] = {
                'value': reading.ammonia,
                'status': get_sensor_status('ammonia', reading.ammonia),
                'unit': 'ppm'
            }
            
        if reading.pm1_0 is not None:
            data['pm1_0'] = {
                'value': reading.pm1_0,
                'status': get_sensor_status('pm1_0', reading.pm1_0),
                'unit': 'μg/m³'
            }
            
        if reading.pm2_5 is not None:
            data['pm2_5'] = {
                'value': reading.pm2_5,
                'status': get_sensor_status('pm2_5', reading.pm2_5),
                'unit': 'μg/m³'
            }
            
        if reading.pm10 is not None:
            data['pm10'] = {
                'value': reading.pm10,
                'status': get_sensor_status('pm10', reading.pm10),
                'unit': 'μg/m³'
            }
        
        return JsonResponse(data)
    except SensorReading.DoesNotExist:
        return JsonResponse({'error': 'Record not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_sensor_status(sensor_type, value):
    """Helper function to determine sensor status based on thresholds."""
    if value is None:
        return 'N/A'
        
    thresholds = {
        'temperature': {'warning': (30, 0), 'alert': (35, -10)},
        'humidity': {'warning': (70, 20), 'alert': (80, 10)},
        'pressure': {'warning': (1020, 1000), 'alert': (1030, 990)},
        'gas_resistance': {'warning': (200, 50), 'alert': (500, 20)},
        'ammonia': {'warning': (1, 0.1), 'alert': (2, 0.05)},
        'pm1_0': {'warning': (20, None), 'alert': (50, None)},
        'pm2_5': {'warning': (30, None), 'alert': (75, None)},
        'pm10': {'warning': (50, None), 'alert': (150, None)},
    }
    
    if sensor_type in thresholds:
        # Check Alert thresholds
        upper, lower = thresholds[sensor_type]['alert']
        if (upper is not None and value > upper) or (lower is not None and value < lower):
            return 'Alert'
            
        # Check Warning thresholds
        upper, lower = thresholds[sensor_type]['warning']
        if (upper is not None and value > upper) or (lower is not None and value < lower):
            return 'Warning'
    
    return 'Normal'

def get_overall_status(reading):
    """Helper function to determine overall status for a reading."""
    statuses = []
    
    for field in ['temperature', 'humidity', 'pressure', 'gas_resistance', 'ammonia', 'pm1_0', 'pm2_5', 'pm10']:
        value = getattr(reading, field, None)
        if value is not None:
            statuses.append(get_sensor_status(field, value))
    
    if 'Alert' in statuses:
        return 'Alert'
    elif 'Warning' in statuses:
        return 'Warning'
    else:
        return 'Normal'

@require_http_methods(["GET"])
def sensor_graph_data(request):
    """API endpoint to get data for sensor graphs with time filtering."""
    try:
        # Get readings from the last 24 hours by default
        try:
            time_filter = int(request.GET.get('time_filter', 24))
        except (ValueError, TypeError):
            # Handle invalid input by defaulting to 24 hours
            time_filter = 24
        
        # Make sure time_filter is within reasonable bounds
        allowed_filters = [1, 6, 12, 24, 72, 168]
        if time_filter not in allowed_filters:
            time_filter = 24
        
        time_threshold = timezone.now() - timedelta(hours=time_filter)
        
        # Get sensor readings
        readings = SensorReading.objects.filter(
            timestamp__gte=time_threshold
        ).order_by('timestamp')
        
        # Count total readings (for display purposes)
        readings_count = readings.count()
        
        # Set interval for aggregation based on time filter or user preference
        try:
            interval_minutes = int(request.GET.get('interval', 0))
        except (ValueError, TypeError):
            interval_minutes = 0
            
        # Set appropriate interval based on time filter if not specified
        if interval_minutes <= 0:
            if time_filter <= 1:  # 1 hour
                interval_minutes = 1
            elif time_filter <= 6:  # 6 hours
                interval_minutes = 3
            elif time_filter <= 24:  # 24 hours
                interval_minutes = 5
            elif time_filter <= 72:  # 3 days
                interval_minutes = 15
            else:  # week or more
                interval_minutes = 30
        
        # Aggregate readings by intervals
        aggregated_readings = []
        current_interval = None
        interval_data = {
            'timestamp': None,
            'temperature': [],
            'humidity': [],
            'pressure': [],
            'gas_resistance': [],
            'ammonia': [],
            'pm1_0': [],
            'pm2_5': [],
            'pm10': []
        }
        
        for reading in readings:
            # Round timestamp to nearest interval
            reading_time = reading.timestamp.replace(second=0, microsecond=0)
            interval_time = reading_time - timedelta(
                minutes=reading_time.minute % interval_minutes,
                seconds=reading_time.second,
                microseconds=reading_time.microsecond
            )
            
            if current_interval != interval_time:
                # Save previous interval if exists
                if current_interval is not None:
                    aggregated_readings.append({
                        'timestamp': current_interval,
                        'temperature': sum(interval_data['temperature']) / len(interval_data['temperature']) if interval_data['temperature'] else None,
                        'humidity': sum(interval_data['humidity']) / len(interval_data['humidity']) if interval_data['humidity'] else None,
                        'pressure': sum(interval_data['pressure']) / len(interval_data['pressure']) if interval_data['pressure'] else None,
                        'gas_resistance': sum(interval_data['gas_resistance']) / len(interval_data['gas_resistance']) if interval_data['gas_resistance'] else None,
                        'ammonia': sum(interval_data['ammonia']) / len(interval_data['ammonia']) if interval_data['ammonia'] else None,
                        'pm1_0': sum(interval_data['pm1_0']) / len(interval_data['pm1_0']) if interval_data['pm1_0'] else None,
                        'pm2_5': sum(interval_data['pm2_5']) / len(interval_data['pm2_5']) if interval_data['pm2_5'] else None,
                        'pm10': sum(interval_data['pm10']) / len(interval_data['pm10']) if interval_data['pm10'] else None
                    })
                
                # Start new interval
                current_interval = interval_time
                interval_data = {
                    'timestamp': interval_time,
                    'temperature': [],
                    'humidity': [],
                    'pressure': [],
                    'gas_resistance': [],
                    'ammonia': [],
                    'pm1_0': [],
                    'pm2_5': [],
                    'pm10': []
                }
            
            # Add reading to current interval
            interval_data['temperature'].append(reading.temperature if reading.temperature is not None else 0)
            interval_data['humidity'].append(reading.humidity if reading.humidity is not None else 0)
            interval_data['pressure'].append(reading.pressure if reading.pressure is not None else 0)
            interval_data['gas_resistance'].append(reading.gas_resistance if reading.gas_resistance is not None else 0)
            interval_data['ammonia'].append(reading.ammonia if reading.ammonia is not None else 0)
            interval_data['pm1_0'].append(reading.pm1_0 if reading.pm1_0 is not None else 0)
            interval_data['pm2_5'].append(reading.pm2_5 if reading.pm2_5 is not None else 0)
            interval_data['pm10'].append(reading.pm10 if reading.pm10 is not None else 0)
        
        # Add the last interval if it exists
        if current_interval is not None:
            aggregated_readings.append({
                'timestamp': current_interval,
                'temperature': sum(interval_data['temperature']) / len(interval_data['temperature']) if interval_data['temperature'] else None,
                'humidity': sum(interval_data['humidity']) / len(interval_data['humidity']) if interval_data['humidity'] else None,
                'pressure': sum(interval_data['pressure']) / len(interval_data['pressure']) if interval_data['pressure'] else None,
                'gas_resistance': sum(interval_data['gas_resistance']) / len(interval_data['gas_resistance']) if interval_data['gas_resistance'] else None,
                'ammonia': sum(interval_data['ammonia']) / len(interval_data['ammonia']) if interval_data['ammonia'] else None,
                'pm1_0': sum(interval_data['pm1_0']) / len(interval_data['pm1_0']) if interval_data['pm1_0'] else None,
                'pm2_5': sum(interval_data['pm2_5']) / len(interval_data['pm2_5']) if interval_data['pm2_5'] else None,
                'pm10': sum(interval_data['pm10']) / len(interval_data['pm10']) if interval_data['pm10'] else None
            })
        
        # Format data for charts
        # Add full timestamp format for tooltip display
        timestamp_labels = [reading['timestamp'].strftime('%H:%M') for reading in aggregated_readings]
        full_timestamps = [reading['timestamp'].strftime('%Y-%m-%d %H:%M') for reading in aggregated_readings]
        
        chart_data = {
            'timestamps': timestamp_labels,
            'full_timestamps': full_timestamps,
            'temperature': [reading['temperature'] for reading in aggregated_readings],
            'humidity': [reading['humidity'] for reading in aggregated_readings],
            'pressure': [reading['pressure'] for reading in aggregated_readings],
            'gas_resistance': [reading['gas_resistance'] for reading in aggregated_readings],
            'ammonia': [reading['ammonia'] for reading in aggregated_readings],
            'pm1_0': [reading['pm1_0'] for reading in aggregated_readings],
            'pm2_5': [reading['pm2_5'] for reading in aggregated_readings],
            'pm10': [reading['pm10'] for reading in aggregated_readings],
        }
        
        # Include metadata
        response_data = {
            'chart_data': chart_data,
            'time_filter': time_filter,
            'readings_count': readings_count,
            'aggregated_count': len(aggregated_readings),
            'interval_minutes': interval_minutes
        }
        
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500) 