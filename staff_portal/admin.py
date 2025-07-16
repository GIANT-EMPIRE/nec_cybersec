from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Device, UnauthorizedAttempt

class CustomUserAdmin(UserAdmin):
     model = CustomUser
     list_display = ['username', 'email', 'is_staff', 'is_superuser']
     fieldsets = UserAdmin.fieldsets + (
         (None, {'fields': ('photo',)}),
     )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Device)
admin.site.register(UnauthorizedAttempt)
