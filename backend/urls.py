"""
Main URL configuration for GenCall AI backend.
Routes all API requests to appropriate handlers.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from calls import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('calls.urls')),
]
