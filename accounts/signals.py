from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, StudentProfile

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
