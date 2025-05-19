from django.db import models
from django.utils import timezone

class SensorReading(models.Model):
    device_id = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # BME680 sensor values
    temperature = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    pressure = models.FloatField(null=True, blank=True)
    gas_resistance = models.FloatField(null=True, blank=True)
    
    # MQ-137 sensor value
    ammonia = models.FloatField(null=True, blank=True)
    
    # PMS7003 sensor values
    pm1_0 = models.IntegerField(null=True, blank=True)
    pm2_5 = models.IntegerField(null=True, blank=True)
    pm10 = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.device_id} - {self.timestamp}" 