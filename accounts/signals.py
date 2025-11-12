from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.signals import user_logged_in, user_logged_out
from .models import CustomUser, StudentProfile
from qlearning.models import LoginActivityLog

@receiver(post_save, sender=CustomUser)
def create_student_profile(sender, instance, created, **kwargs):
    """Create StudentProfile automatically when CustomUser is created"""
    if created and instance.role == 'student':
        StudentProfile.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_student_profile(sender, instance, **kwargs):
    """Save StudentProfile when CustomUser is saved"""
    if instance.role == 'student':
        try:
            instance.student_profile.save()
        except StudentProfile.DoesNotExist:
            # Profile doesn't exist, create it
            StudentProfile.objects.create(user=instance)

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log user login activity"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
    
    LoginActivityLog.objects.create(
        user=user,
        ip_address=ip,
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Update login activity log when user logs out"""
    if user.is_authenticated:
        # Get the most recent login activity that doesn't have a logout time
        login_activity = LoginActivityLog.objects.filter(
            user=user,
            logout_timestamp__isnull=True
        ).order_by('-login_timestamp').first()
        
        if login_activity:
            login_activity.logout_timestamp = timezone.now()
            if login_activity.login_timestamp:
                login_activity.session_duration_seconds = (
                    login_activity.logout_timestamp - login_activity.login_timestamp
                ).total_seconds()
            login_activity.save()
