from django.db import models
from django.conf import settings
from django.utils import timezone

class Question(models.Model):
    """Question model for the gamification system with Q-learning integration"""

    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    FORMAT_CHOICES = [
        ('mcq_simple', 'Multiple Choice (Single Answer)'),
        ('mcq_complex', 'Multiple Choice (Multiple Answers)'),
        ('short_answer', 'Short Answer'),
    ]

    text = models.TextField(help_text='The question text')
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='easy',
        help_text='Question difficulty level'
    )
    format = models.CharField(
        max_length=20,
        choices=FORMAT_CHOICES,
        default='mcq_simple',
        help_text='Question format type'
    )
    options = models.JSONField(
        null=True,
        blank=True,
        help_text='JSON options for MCQ questions (e.g., {"A": "Option 1", "B": "Option 2"})'
    )
    answer_key = models.TextField(
        help_text='Correct answer(s) - JSON for MCQ, text for short answer'
    )
    curriculum_tag = models.CharField(
        max_length=100,
        blank=True,
        help_text='Curriculum topic/category tag'
    )
    explanation = models.TextField(
        blank=True,
        help_text='Explanation shown after answering'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.text[:50]}... ({self.get_difficulty_display()})"

    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['-created_at']


class AttemptLog(models.Model):
    """Attempt log for tracking individual question attempts with Q-learning data"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attempt_logs'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='attempt_logs'
    )
    chosen_answer = models.TextField(
        null=True,
        blank=True,
        help_text='Student\'s answer (JSON for MCQ, text for short answer)'
    )
    is_correct = models.BooleanField(
        default=False,
        help_text='Whether the answer was correct'
    )
    difficulty_attempted = models.CharField(
        max_length=20,
        choices=Question.DIFFICULTY_CHOICES,
        help_text='Difficulty level at time of attempt'
    )
    time_spent = models.FloatField(
        help_text='Time spent on question in seconds'
    )
    hint_given = models.TextField(
        null=True,
        blank=True,
        help_text='Hint provided to student (if any)'
    )
    reward_numeric = models.IntegerField(
        default=0,
        help_text='Numeric reward/penalty given for this attempt'
    )
    qtable_snapshot = models.JSONField(
        null=True,
        blank=True,
        help_text='Q-table snapshot at time of attempt for learning analysis'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.question.text[:30]}... ({self.is_correct})"

    class Meta:
        verbose_name = 'Attempt Log'
        verbose_name_plural = 'Attempt Logs'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Ensure difficulty_attempted matches question difficulty if not set
        if not self.difficulty_attempted:
            self.difficulty_attempted = self.question.difficulty
        super().save(*args, **kwargs)
