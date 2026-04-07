"""
URL configuration for calls app.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Twilio webhook endpoints
    path('incoming_call/', views.incoming_call, name='incoming_call'),
    path('outgoing_call/', views.outgoing_call, name='outgoing_call'),
    path('call_status/', views.call_status, name='call_status'),
    
    # API endpoints for frontend
    path('call_logs/', views.get_call_logs, name='get_call_logs'),
    path('generate_token/', views.generate_token, name='generate_token'),
    path('speech_to_text/', views.speech_to_text, name='speech_to_text'),
    path('text_to_speech/', views.text_to_speech, name='text_to_speech'),
    path('test/', views.test_endpoint, name='test_endpoint'),
    
    # Program query endpoints
    path('program_query/', views.program_query, name='program_query'),
    path('programs/list/', views.list_all_programs, name='list_all_programs'),
]
