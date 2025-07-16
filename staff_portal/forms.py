from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class StaffRegisterForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['staff_id', 'username', 'password1', 'password2', 'image']

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if len(password) < 8 or not any(char in '!@#$%^&*()' for char in password):
            raise forms.ValidationError("Password must be >7 characters and include special character.")
        return password
