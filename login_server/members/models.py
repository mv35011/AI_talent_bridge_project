from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    objects = None
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

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)  # Added max_length here
    college_email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)
    skills = models.JSONField(default=list)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(default=0.0)

    def __str__(self):
        return self.user.username

    def update_score(self):
        try:
            from .ml_utils import ProfileScorer
            scorer = ProfileScorer()
            new_score = scorer.calculate_score(self)
            print(f"Calculated new score: {new_score}")  # Debug print
            self.score = new_score
            self.save()
        except Exception as e:
            print(f"Error in update_score: {e}")