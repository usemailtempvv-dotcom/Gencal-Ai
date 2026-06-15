"""
Models for storing call logs and information.
"""
from django.db import models
from django.utils import timezone


class CallLog(models.Model):
    """
    Model to store call logs from Twilio.
    """
    CALL_SOURCE_CHOICES = [
        ('twilio', 'Twilio'),
        ('browser', 'Browser'),
    ]

    call_sid = models.CharField(max_length=100, unique=True, help_text="Twilio Call SID")
    from_number = models.CharField(max_length=20, help_text="Caller's phone number")
    to_number = models.CharField(max_length=20, help_text="Called phone number")
    call_status = models.CharField(max_length=50, help_text="Status of the call")
    direction = models.CharField(max_length=20, help_text="Call direction (inbound/outbound)")
    call_source = models.CharField(
        max_length=20,
        choices=CALL_SOURCE_CHOICES,
        default='twilio',
        help_text='Where the call originated from',
    )
    timestamp = models.DateTimeField(default=timezone.now, help_text="Time of call")
    duration = models.IntegerField(null=True, blank=True, help_text="Call duration in seconds")
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"Call from {self.from_number} to {self.to_number} via {self.call_source} at {self.timestamp}"


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


class TwilioConfig(models.Model):
    """Store Twilio credentials and runtime options editable via Django admin.

    Only the most recently created/updated active config will be used by the views.
    """
    enabled = models.BooleanField(default=False, help_text='Enable Twilio incoming call handling')
    account_sid = models.CharField(max_length=128, blank=True, default='', help_text='Twilio Account SID')
    auth_token = models.CharField(max_length=128, blank=True, default='', help_text='Twilio Auth Token')
    phone_number = models.CharField(max_length=32, blank=True, default='', help_text='Twilio phone number (E.164)')
    twiml_app_sid = models.CharField(max_length=64, blank=True, default='', help_text='TwiML App SID for client tokens')
    api_key_sid = models.CharField(max_length=128, blank=True, default='', help_text='Twilio API Key SID (for client tokens)')
    api_key_secret = models.CharField(max_length=256, blank=True, default='', help_text='Twilio API Key Secret (for client tokens)')
    greeting_text = models.TextField(blank=True, default='Hello! This is GenCall AI speaking. Thank you for calling us. We are excited to assist you today.', help_text='Message to speak to inbound callers')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        status = 'enabled' if self.enabled else 'disabled'
        return f"Twilio config ({status}) updated {self.updated_at.isoformat()}"


def get_active_twilio_config():
    """Return dict of active Twilio config values, falling back to empty strings when missing.

    Prefers the most recently updated TwilioConfig instance. If none exist, return empty values.
    """
    try:
        cfg = TwilioConfig.objects.filter(enabled=True).order_by('-updated_at').first()
        if not cfg:
            cfg = TwilioConfig.objects.order_by('-updated_at').first()
        if not cfg:
            return {
                'enabled': False,
                'account_sid': '',
                'auth_token': '',
                'phone_number': '',
                'twiml_app_sid': '',
                'api_key_sid': '',
                'api_key_secret': '',
                'greeting_text': '',
            }

        return {
            'enabled': bool(cfg.enabled),
            'account_sid': cfg.account_sid or '',
            'auth_token': cfg.auth_token or '',
            'phone_number': cfg.phone_number or '',
            'twiml_app_sid': cfg.twiml_app_sid or '',
            'api_key_sid': cfg.api_key_sid or '',
            'api_key_secret': cfg.api_key_secret or '',
            'greeting_text': cfg.greeting_text or '',
        }
    except Exception:
        return {
            'enabled': False,
            'account_sid': '',
            'auth_token': '',
            'phone_number': '',
            'twiml_app_sid': '',
            'api_key_sid': '',
            'api_key_secret': '',
            'greeting_text': '',
        }
