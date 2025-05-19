from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),  # Django admin interface
    path('', include('main.urls')),   # Main application URLs
] 