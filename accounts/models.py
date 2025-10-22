from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    """Custom user model with role field for gamification system"""

    ROLE_CHOICES = [
        ('student', 'Student'),
        ('admin', 'Admin'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student',
        help_text='User role in the gamification system'
    )

    # Avatar field for profile pictures
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text='User profile picture'
    )

    def __str__(self):
        return f"{self.username} ({self.role})"

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class StudentProfile(models.Model):
    """Profile model for students with gamification data"""

    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='beginner',
        help_text='Current skill level of the student'
    )
    points = models.PositiveIntegerField(
        default=0,
        help_text='Total points earned by the student'
    )
    xp = models.PositiveIntegerField(
        default=0,
        help_text='Experience points for current level'
    )
    total_xp = models.PositiveIntegerField(
        default=0,
        help_text='Total experience points earned'
    )
    streak_correct = models.PositiveIntegerField(
        default=0,
        help_text='Current streak of correct answers'
    )
    progress = models.PositiveIntegerField(
        default=0,
        help_text='Overall progress percentage'
    )
    last_difficulty = models.CharField(
        max_length=20,
        default='easy',
        help_text='Last difficulty level attempted'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    class Meta:
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'

    def get_xp_for_next_level(self):
        """Get XP required for next level"""
        level_thresholds = {
            'beginner': 200,     # Increased from 100 to 200
            'intermediate': 500, # Increased from 300 to 500
            'advanced': 800,    # Increased from 500 to 800
            'expert': 1000,
        }
        return level_thresholds.get(self.level, 1000)

    def get_xp_progress_percentage(self):
        """Get XP progress percentage for current level"""
        xp_for_next = self.get_xp_for_next_level()
        if xp_for_next == 0:
            return 100
        return min((self.xp / xp_for_next) * 100, 100)

    def can_level_up(self):
        """Check if student can level up"""
        return self.xp >= self.get_xp_for_next_level()

    def add_xp(self, amount):
        """Add XP and handle level ups"""
        self.xp += amount
        self.total_xp += amount

        # Ensure XP doesn't go negative
        if self.xp < 0:
            self.xp = 0

        leveled_up = False
        new_level = self.level
        old_level = self.level

        # Check for level ups
        if self.level == 'beginner' and self.xp >= 200:     # Updated from 100 to 200
            new_level = 'intermediate'
            leveled_up = True
        elif self.level == 'intermediate' and self.xp >= 500:  # Updated from 300 to 500
            new_level = 'advanced'
            leveled_up = True
        elif self.level == 'advanced' and self.xp >= 800:      # Updated from 500 to 800
            new_level = 'expert'
            leveled_up = True

        if leveled_up:
            self.level = new_level
            self.xp = 0  # Reset XP for new level

            # Log the level transition
            try:
                from qlearning.analytics import AnalyticsService
                AnalyticsService.log_level_transition(
                    user=self.user,
                    transition_type='level_up_manual',
                    old_level=old_level,
                    new_level=new_level,
                    transition_condition={
                        'xp_threshold': self.get_xp_for_next_level(),
                        'xp_earned': amount,
                        'total_xp': self.total_xp
                    },
                    performance_metrics={
                        'current_streak': self.streak_correct,
                        'total_attempts': 0,  # Will be updated by caller
                        'questions_attempted': 0  # Will be updated by caller
                    }
                )
            except ImportError:
                # Analytics service not available, skip logging
                pass

    def manual_level_up(self):
    # """Manual level up when user clicks level up button"""
    # Already at expert level, cannot level up
        if self.level == 'expert':
            return False, None
    
        leveled_up = False
        new_level = None
        old_level = self.level

        # Check for level ups based on XP thresholds
        if self.level == 'beginner' and self.xp >= 200:     # Updated from 100 to 200
            new_level = 'intermediate'
            leveled_up = True
        elif self.level == 'intermediate' and self.xp >= 500:  # Updated from 300 to 500
            new_level = 'advanced'
            leveled_up = True
        elif self.level == 'advanced' and self.xp >= 800:      # Updated from 500 to 800
            new_level = 'expert'
            leveled_up = True

        if leveled_up:
            self.level = new_level
            self.xp = 0  # Reset XP for new level

            # Log the level transition
            try:
                from qlearning.analytics import AnalyticsService
                AnalyticsService.log_level_transition(
                    user=self.user,
                    transition_type='level_up_manual',
                    old_level=old_level,
                    new_level=new_level,
                    transition_condition={
                        'xp_threshold': self.get_xp_for_next_level(),
                        'manual_level_up': True,
                        'total_xp': self.total_xp
                    },
                    performance_metrics={
                        'current_streak': self.streak_correct,
                        'total_attempts': 0,
                        'questions_attempted': 0
                    }
                )
            except ImportError:
                pass
        
            return True, new_level
    
        # Not enough XP to level up
        return False, None
