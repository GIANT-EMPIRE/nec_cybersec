from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    is_admin = models.BooleanField(default=False)
    staff_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    image = models.ImageField(upload_to='staff_photos/', blank=True, null=True)
    face_encoding = models.BinaryField(blank=True, null=True)

class Device(models.Model):
    serial_bios = models.CharField(max_length=100)
    serial_baseboard = models.CharField(max_length=100)
    registered_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)

class UnauthorizedAttempt(models.Model):
    bios = models.CharField(max_length=100)
    baseboard = models.CharField(max_length=100)
    attempted_at = models.DateTimeField(auto_now_add=True)

class PendingAccess(models.Model):
    username = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
