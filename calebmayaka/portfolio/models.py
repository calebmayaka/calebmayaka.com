from django.contrib.auth.models import User
from django.db import models


class Inquiry(models.Model):
    WEBSITE = 'website'
    BACKEND = 'backend'
    AI_AUTOMATION = 'ai_automation'
    CONSULTATION = 'consultation'
    OTHER = 'other'

    INQUIRY_TYPE_CHOICES = [
        (WEBSITE, 'Website or web app'),
        (BACKEND, 'Backend or API'),
        (AI_AUTOMATION, 'AI automation'),
        (CONSULTATION, 'Consultation'),
        (OTHER, 'Other'),
    ]

    email = models.EmailField()
    inquiry_type = models.CharField(max_length=40, choices=INQUIRY_TYPE_CHOICES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'inquiries'

    def __str__(self):
        return f'{self.get_inquiry_type_display()} from {self.email}'


class DashboardUserProfile(models.Model):
    ADMIN = 'admin'
    MANAGER = 'manager'
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (MANAGER, 'Manager'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dashboard_profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=MANAGER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__username']
        verbose_name = 'Dashboard user profile'
        verbose_name_plural = 'Dashboard user profiles'

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'
