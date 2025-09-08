from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    """Custom user registration form with role selection"""
    
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, initial='student')
    university_id = forms.CharField(max_length=20, required=False, help_text="Student/Employee ID")
    department = forms.CharField(max_length=100, required=False)
    
    class Meta:
        model = User
        fields = ("username", "email", "role", "university_id", "department", "password1", "password2")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes for styling
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.role = self.cleaned_data["role"]
        user.university_id = self.cleaned_data["university_id"]
        user.department = self.cleaned_data["department"]
        if commit:
            user.save()
        return user