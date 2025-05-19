import os
import json
import requests
import time
from pathlib import Path

def get_ngrok_url():
    """Get the current ngrok URL from the ngrok API."""
    try:
        # Get ngrok API response
        response = requests.get("http://localhost:4040/api/tunnels")
        tunnels = response.json()["tunnels"]
        
        # Get the HTTPS URL
        for tunnel in tunnels:
            if tunnel["proto"] == "https":
                return tunnel["public_url"]
    except:
        return None

def update_django_settings(ngrok_url):
    """Update Django settings with new ngrok URL."""
    try:
        # Path to your Django settings file
        settings_path = Path("sensor_project/settings.py")
        
        # Read current settings
        with open(settings_path, 'r') as file:
            content = file.read()
        
        # Update ALLOWED_HOSTS
        if "ALLOWED_HOSTS" in content:
            # Find the ALLOWED_HOSTS line
            start = content.find("ALLOWED_HOSTS")
            end = content.find("]", start) + 1
            
            # Extract the current hosts
            hosts_line = content[start:end]
            hosts = eval(hosts_line.split("=")[1].strip())
            
            # Add ngrok URL without https://
            ngrok_domain = ngrok_url.replace("https://", "")
            if ngrok_domain not in hosts:
                hosts.append(ngrok_domain)
                new_hosts_line = f"ALLOWED_HOSTS = {hosts}"
                content = content.replace(hosts_line, new_hosts_line)
        
        # Update CORS settings if they exist
        if "CORS_ALLOWED_ORIGINS" in content:
            # Find the CORS_ALLOWED_ORIGINS line
            start = content.find("CORS_ALLOWED_ORIGINS")
            end = content.find("]", start) + 1
            
            # Extract the current origins
            origins_line = content[start:end]
            origins = eval(origins_line.split("=")[1].strip())
            
            # Add ngrok URL
            if ngrok_url not in origins:
                origins.append(ngrok_url)
                new_origins_line = f"CORS_ALLOWED_ORIGINS = {origins}"
                content = content.replace(origins_line, new_origins_line)
        
        # Write updated settings
        with open(settings_path, 'w') as file:
            file.write(content)
            
        print(f"✅ Updated Django settings with new ngrok URL: {ngrok_url}")
        return True
    except Exception as e:
        print(f"❌ Error updating Django settings: {str(e)}")
        return False

def main():
    print("🔄 Starting ngrok URL monitor...")
    last_url = None
    
    while True:
        current_url = get_ngrok_url()
        
        if current_url and current_url != last_url:
            print(f"🔄 New ngrok URL detected: {current_url}")
            if update_django_settings(current_url):
                last_url = current_url
                print("✅ Settings updated successfully")
            else:
                print("❌ Failed to update settings")
        
        time.sleep(5)  # Check every 5 seconds

if __name__ == "__main__":
    main() 