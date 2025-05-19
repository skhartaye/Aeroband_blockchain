from django.contrib import admin
from .models import SensorReading

@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'temperature', 'humidity', 'pressure', 'gas_resistance', 
                   'ammonia', 'pm1_0', 'pm2_5', 'pm10')
    list_filter = ('timestamp',)
    ordering = ('-timestamp',)  # Show newest first
    readonly_fields = ('timestamp',)
    
    fieldsets = (
        ('Time Information', {
            'fields': ('timestamp',)
        }),
        ('BME680 Sensor', {
            'fields': ('temperature', 'humidity', 'pressure', 'gas_resistance')
        }),
        ('Air Quality Sensors', {
            'fields': ('ammonia', 'pm1_0', 'pm2_5', 'pm10')
        }),
    )
    
    def temperature(self, obj):
        return f"{obj.temperature:.1f}°C"
    temperature.short_description = "Temperature"
    
    def humidity(self, obj):
        return f"{obj.humidity:.1f}%"
    humidity.short_description = "Humidity"
    
    def pressure(self, obj):
        return f"{obj.pressure:.1f} hPa"
    pressure.short_description = "Pressure"
    
    def gas_resistance(self, obj):
        return f"{obj.gas_resistance:.1f} kΩ"
    gas_resistance.short_description = "Gas Resistance"
    
    def ammonia(self, obj):
        return f"{obj.ammonia:.2f} PPM"
    ammonia.short_description = "Ammonia"
    
    def pm1_0(self, obj):
        return f"{obj.pm1_0} μg/m³"
    pm1_0.short_description = "PM1.0"
    
    def pm2_5(self, obj):
        return f"{obj.pm2_5} μg/m³"
    pm2_5.short_description = "PM2.5"
    
    def pm10(self, obj):
        return f"{obj.pm10} μg/m³"
    pm10.short_description = "PM10" 