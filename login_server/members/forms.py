from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

class UserProfileForm(forms.ModelForm):
    DEPARTMENT_CHOICES = [
        ('CSE', 'Computer Science'),
        ('ECE', 'Electronics'),
        ('ME', 'Mechanical'),
        ('IT', 'Information Technology'),
        ('Other', 'Other')
    ]

    SKILLS_CHOICES = [
        ('AI_ML', 'AI/ML'),
        ('WEB_DEV', 'Web Development'),
        ('ANDROID', 'Android Development'),
    ]

    full_name = forms.CharField(max_length=100)
    college_email = forms.EmailField()
    phone_number = forms.CharField(max_length=15)
    department = forms.ChoiceField(choices=DEPARTMENT_CHOICES)
    skills = forms.MultipleChoiceField(
        choices=SKILLS_CHOICES,
        widget=forms.CheckboxSelectMultiple
    )
    resume = forms.FileField(required=False)
    profile_photo = forms.ImageField(required=False)

    class Meta:
        model = UserProfile
        fields = ['full_name', 'college_email', 'phone_number',
                 'department', 'skills', 'resume', 'profile_photo']