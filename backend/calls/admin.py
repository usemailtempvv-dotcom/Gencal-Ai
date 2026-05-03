"""
Admin configuration for calls app.
"""
from django.contrib import admin
from .models import CallLog, LearnedWebAnswer


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


@admin.register(LearnedWebAnswer)
class LearnedWebAnswerAdmin(admin.ModelAdmin):
    """Admin review workflow for auto-learned website answers."""

    list_display = [
        'short_question',
        'admin_verified',
        'times_used',
        'source_url',
        'updated_at',
        'created_at',
    ]
    list_filter = ['admin_verified', 'created_at', 'updated_at']
    search_fields = ['question_text', 'normalized_question', 'answer_text', 'source_url']
    list_editable = ['admin_verified']
    readonly_fields = ['normalized_question', 'times_used', 'last_used_at', 'created_at', 'updated_at']
    ordering = ['admin_verified', '-updated_at']

    def short_question(self, obj):
        return (obj.question_text[:80] + '...') if len(obj.question_text) > 80 else obj.question_text

    short_question.short_description = 'Question'
