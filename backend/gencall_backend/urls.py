"""
URL configuration for gencall_backend project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/api/test/', permanent=False)),
    path('admin/', admin.site.urls),
    path('api/', include('calls.urls')),  # Include calls app URLs
]
