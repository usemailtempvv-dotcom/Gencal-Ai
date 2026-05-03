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


class LearnedWebAnswer(models.Model):
    """Auto-learned answers from superior.edu.pk for unknown questions."""

    question_text = models.TextField(help_text='Original user question when answer was learned')
    normalized_question = models.CharField(max_length=400, unique=True, db_index=True)
    answer_text = models.TextField(help_text='Generated answer text saved for reuse')
    source_url = models.URLField(default='https://www.superior.edu.pk/')
    source_snippets = models.JSONField(default=list, blank=True)

    admin_verified = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True, default='')

    times_used = models.PositiveIntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        status = 'verified' if self.admin_verified else 'pending'
        return f"{self.normalized_question[:60]} ({status})"
