from django.db import models
from django.conf import settings
from django.utils import timezone
import hashlib
import json

class QTableEntry(models.Model):
    """Q-Table entry for storing Q-values per user, state, and action"""

    ACTION_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='qtable_entries'
    )
    state_hash = models.CharField(
        max_length=32,
        help_text='Hash of the state tuple for efficient lookup'
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text='Action taken in this state'
    )
    q_value = models.FloatField(
        default=0.0,
        help_text='Q-value for this state-action pair'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.state_hash[:8]} - {self.action} = {self.q_value:.3f}"

    class Meta:
        verbose_name = 'Q-Table Entry'
        verbose_name_plural = 'Q-Table Entries'
        unique_together = ['user', 'state_hash', 'action']
        ordering = ['user', 'state_hash', 'action']

    @classmethod
    def get_or_create_entry(cls, user, state_hash, action):
        """Get or create a Q-table entry"""
        entry, created = cls.objects.get_or_create(
            user=user,
            state_hash=state_hash,
            action=action,
            defaults={'q_value': 0.0}
        )
        return entry


class QLearningLog(models.Model):
    """Log of Q-learning updates for analysis and debugging"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='qlearning_logs'
    )
    state_hash = models.CharField(
        max_length=32,
        help_text='Current state hash'
    )
    action = models.CharField(
        max_length=20,
        help_text='Action taken'
    )
    reward = models.FloatField(
        help_text='Reward received for this action'
    )
    q_value_before = models.FloatField(
        help_text='Q-value before update'
    )
    q_value_after = models.FloatField(
        help_text='Q-value after update'
    )
    next_state_hash = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        help_text='Next state hash (for Q-learning update)'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.state_hash[:8]} - {self.action} -> {self.q_value_after:.3f}"

    class Meta:
        verbose_name = 'Q-Learning Log'
        verbose_name_plural = 'Q-Learning Logs'
        ordering = ['-timestamp']

    def save(self, *args, **kwargs):
        # Ensure timestamp is set
        if not self.timestamp:
            self.timestamp = timezone.now()
        super().save(*args, **kwargs)


# Sprint 7 - Comprehensive Analytics Models

class UserEngagementLog(models.Model):
    """Track user engagement metrics"""

    SESSION_TYPE_CHOICES = [
        ('login', 'Login'),
        ('quiz_attempt', 'Quiz Attempt'),
        ('level_claim', 'Level Claim'),
        ('hint_usage', 'Hint Usage'),
        ('badge_claim', 'Badge Claim'),
        ('progress_complete', 'Progress Complete'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='engagement_logs'
    )
    session_type = models.CharField(
        max_length=20,
        choices=SESSION_TYPE_CHOICES,
        help_text='Type of engagement event'
    )
    session_id = models.CharField(
        max_length=64,
        help_text='Unique session identifier'
    )
    duration_seconds = models.PositiveIntegerField(
        help_text='Duration of the session in seconds'
    )
    questions_attempted = models.PositiveIntegerField(
        default=0,
        help_text='Number of questions attempted in this session'
    )
    hints_used = models.PositiveIntegerField(
        default=0,
        help_text='Number of hints used in this session'
    )
    gamification_interactions = models.PositiveIntegerField(
        default=0,
        help_text='Number of gamification interactions (badges, levels, etc.)'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(
        default=dict,
        help_text='Additional metadata for the session'
    )

    def __str__(self):
        return f"{self.user.username} - {self.session_type} - {self.duration_seconds}s"

    class Meta:
        verbose_name = 'User Engagement Log'
        verbose_name_plural = 'User Engagement Logs'
        ordering = ['-timestamp']


class SuccessRateLog(models.Model):
    """Track success rates and accuracy metrics"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='success_logs'
    )
    difficulty = models.CharField(
        max_length=20,
        help_text='Question difficulty level'
    )
    total_attempts = models.PositiveIntegerField(
        help_text='Total number of attempts'
    )
    correct_attempts = models.PositiveIntegerField(
        help_text='Number of correct attempts'
    )
    average_time_spent = models.FloatField(
        help_text='Average time spent per question in seconds'
    )
    accuracy_percentage = models.FloatField(
        help_text='Accuracy percentage (0-100)'
    )
    time_window_start = models.DateTimeField(
        help_text='Start of the time window for this log'
    )
    time_window_end = models.DateTimeField(
        help_text='End of the time window for this log'
    )
    metadata = models.JSONField(
        default=dict,
        help_text='Additional metadata'
    )

    def __str__(self):
        return f"{self.user.username} - {self.difficulty} - {self.accuracy_percentage:.1f}%"

    class Meta:
        verbose_name = 'Success Rate Log'
        verbose_name_plural = 'Success Rate Logs'
        ordering = ['-time_window_end']


class ResponseToAdaptationLog(models.Model):
    """Track user responses to system adaptations"""

    ADAPTATION_TYPE_CHOICES = [
        ('difficulty_transition', 'Difficulty Transition'),
        ('hint_adaptation', 'Hint Adaptation'),
        ('reward_response', 'Reward Response'),
        ('level_transition', 'Level Transition'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='adaptation_logs'
    )
    adaptation_type = models.CharField(
        max_length=25,
        choices=ADAPTATION_TYPE_CHOICES,
        help_text='Type of adaptation'
    )
    old_state = models.JSONField(
        help_text='State before adaptation'
    )
    new_state = models.JSONField(
        help_text='State after adaptation'
    )
    adaptation_details = models.JSONField(
        help_text='Details about the adaptation'
    )
    first_attempt_after = models.JSONField(
        null=True,
        blank=True,
        help_text='Result of first attempt after adaptation'
    )
    hint_usage_change = models.FloatField(
        default=0.0,
        help_text='Change in hint usage rate'
    )
    session_duration_change = models.FloatField(
        default=0.0,
        help_text='Change in session duration'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.adaptation_type}"

    class Meta:
        verbose_name = 'Response to Adaptation Log'
        verbose_name_plural = 'Response to Adaptation Logs'
        ordering = ['-timestamp']


class QLearningPerformanceLog(models.Model):
    """Track Q-Learning algorithm performance"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='qlearning_performance_logs'
    )
    state_hash = models.CharField(
        max_length=32,
        help_text='State hash for this log entry'
    )
    action_distribution = models.JSONField(
        help_text='Distribution of actions chosen by the agent'
    )
    optimal_action_frequency = models.FloatField(
        help_text='Frequency of choosing optimal actions (0-1)'
    )
    average_q_value = models.FloatField(
        help_text='Average Q-value across all states'
    )
    q_table_size = models.PositiveIntegerField(
        help_text='Number of entries in Q-table'
    )
    learning_progress = models.FloatField(
        help_text='Learning progress indicator'
    )
    snapshot_interval = models.PositiveIntegerField(
        help_text='Number of attempts since last snapshot'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(
        default=dict,
        help_text='Additional Q-Learning metadata'
    )

    def __str__(self):
        return f"{self.user.username} - Q-Learning Performance - {self.timestamp.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name = 'Q-Learning Performance Log'
        verbose_name_plural = 'Q-Learning Performance Logs'
        ordering = ['-timestamp']


class LevelTransitionLog(models.Model):
    """Track level transitions and their conditions"""

    TRANSITION_TYPE_CHOICES = [
        ('level_up_manual', 'Manual Level Up'),
        ('level_down_auto', 'Automatic Level Down'),
        ('level_reset', 'Level Reset'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='level_transition_logs'
    )
    transition_type = models.CharField(
        max_length=20,
        choices=TRANSITION_TYPE_CHOICES,
        help_text='Type of level transition'
    )
    old_level = models.CharField(
        max_length=20,
        help_text='Previous level'
    )
    new_level = models.CharField(
        max_length=20,
        help_text='New level'
    )
    transition_condition = models.JSONField(
        help_text='Conditions that triggered the transition'
    )
    performance_metrics = models.JSONField(
        help_text='Performance metrics at time of transition'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.old_level} → {self.new_level} ({self.transition_type})"

    class Meta:
        verbose_name = 'Level Transition Log'
        verbose_name_plural = 'Level Transition Logs'
        ordering = ['-timestamp']


class RewardIncentivesLog(models.Model):
    """Track reward and incentive effectiveness"""

    REWARD_TYPE_CHOICES = [
        ('points', 'Points'),
        ('streak_bonus', 'Streak Bonus'),
        ('level_up_bonus', 'Level Up Bonus'),
        ('hidden_reward', 'Hidden Reward'),
        ('badge', 'Badge'),
        ('progress_milestone', 'Progress Milestone'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reward_logs'
    )
    reward_type = models.CharField(
        max_length=20,
        choices=REWARD_TYPE_CHOICES,
        help_text='Type of reward given'
    )
    reward_value = models.FloatField(
        help_text='Numerical value of the reward'
    )
    trigger_condition = models.JSONField(
        help_text='What triggered this reward'
    )
    user_reaction = models.JSONField(
        help_text='User behavior after receiving reward'
    )
    session_continuation = models.BooleanField(
        help_text='Whether user continued the session after reward'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.reward_type} - {self.reward_value}"

    class Meta:
        verbose_name = 'Reward & Incentives Log'
        verbose_name_plural = 'Reward & Incentives Logs'
        ordering = ['-timestamp']


class GlobalSystemLog(models.Model):
    """Track global system statistics"""

    METRIC_TYPE_CHOICES = [
        ('accuracy_global', 'Global Accuracy'),
        ('engagement_daily', 'Daily Engagement'),
        ('hint_distribution', 'Hint Distribution'),
        ('leaderboard_snapshot', 'Leaderboard Snapshot'),
        ('qlearning_trend', 'Q-Learning Trend'),
        ('system_health', 'System Health'),
    ]

    metric_type = models.CharField(
        max_length=25,
        choices=METRIC_TYPE_CHOICES,
        help_text='Type of global metric'
    )
    metric_data = models.JSONField(
        help_text='The actual metric data'
    )
    time_window = models.CharField(
        max_length=20,
        help_text='Time window for this metric (daily, weekly, etc.)'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.metric_type} - {self.time_window} - {self.timestamp.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name = 'Global System Log'
        verbose_name_plural = 'Global System Logs'
        ordering = ['-timestamp']
