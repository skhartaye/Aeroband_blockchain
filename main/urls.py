from django.urls import path
from . import views

urlpatterns = [
    # Admin routes
    path('', views.admin_dashboard, name='admin_dashboard'),  # Root path now points to admin dashboard
    path('data-management/', views.data_management, name='data_management'),
    path('sensor-graphs/', views.sensor_graphs, name='sensor_graphs'),  # New graphs page
    path('devices/', views.devices, name='devices'),
    path('users/', views.users, name='users'),
    path('settings/', views.settings, name='settings'),
    
    # Mobile routes
    path('ble-bridge/', views.ble_bridge, name='ble_bridge'),  # Mobile interface
    path('mobile/history/', views.mobile_history, name='mobile_history'),
    path('mobile/alerts/', views.mobile_alerts, name='mobile_alerts'),
    path('mobile/settings/', views.mobile_settings, name='mobile_settings'),
    
    # Redirect page
    path('redirect/', views.redirect_page, name='redirect_page'),
    
    # API routes
    path('api/sensor-data/', views.receive_sensor_data, name='receive_sensor_data'),
    path('api/get-sensor-data/', views.get_sensor_data, name='get_sensor_data'),
    path('api/latest-readings/', views.get_latest_readings, name='get_latest_readings'),
    path('api/latest-readings-json/', views.get_latest_readings_json, name='get_latest_readings_json'),
    path('api/latest-sensor-data/', views.latest_sensor_data, name='latest_sensor_data'),
    path('api/delete-all-data/', views.delete_all_data, name='delete_all_data'),
    path('api/sensor-records/', views.sensor_records, name='sensor_records'),
    path('api/sensor-record/<int:record_id>/', views.sensor_record_detail, name='sensor_record_detail'),
    path('api/export-sensor-data/', views.export_sensor_data, name='export_sensor_data'),
    path('api/sensor-graph-data/', views.sensor_graph_data, name='sensor_graph_data'),
] 