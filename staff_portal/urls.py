from django.urls import path
from . import views
from staff_portal.views import device_verification_bridge

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('otp/', views.otp_view, name='otp'),
    path('dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('logout/', views.logout_view, name='logout'),
    path('api_check_device/', views.api_check_device, name='api_check_device'),
    path('device_verification_bridge/', device_verification_bridge, name='device_verification_bridge'),
    path('check_verification/', views.check_verification, name='check_verification'),

]
