"""
Models for storing call logs and information.
"""
from django.db import models
from django.utils import timezone


class CallLog(models.Model):
    """
    Model to store call logs from Twilio.
    """
    call_sid = models.CharField(max_length=100, unique=True, help_text="Twilio Call SID")
    from_number = models.CharField(max_length=20, help_text="Caller's phone number")
    to_number = models.CharField(max_length=20, help_text="Called phone number")
    call_status = models.CharField(max_length=50, help_text="Status of the call")
    direction = models.CharField(max_length=20, help_text="Call direction (inbound/outbound)")
    timestamp = models.DateTimeField(default=timezone.now, help_text="Time of call")
    duration = models.IntegerField(null=True, blank=True, help_text="Call duration in seconds")
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"Call from {self.from_number} to {self.to_number} at {self.timestamp}"
