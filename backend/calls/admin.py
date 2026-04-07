"""
Admin configuration for calls app.
"""
from django.contrib import admin
from .models import CallLog


@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    """
    Admin interface for CallLog model.
    """
    list_display = ['call_sid', 'from_number', 'to_number', 'call_status', 'direction', 'timestamp', 'duration']
    list_filter = ['call_status', 'direction', 'timestamp']
    search_fields = ['call_sid', 'from_number', 'to_number']
    readonly_fields = ['call_sid', 'timestamp']
    ordering = ['-timestamp']
