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


class UserSurveyResponse(models.Model):
    """Track user satisfaction surveys and feedback (Metrik 2.1.4.3)"""
    
    SURVEY_TYPE_CHOICES = [
        ('post_adaptation', 'Post Adaptation Survey'),
        ('session_end', 'Session End Survey'),
        ('weekly_feedback', 'Weekly Feedback'),
        ('difficulty_feedback', 'Difficulty Feedback'),
    ]
    
    SATISFACTION_CHOICES = [
        (1, 'Very Dissatisfied'),
        (2, 'Dissatisfied'),
        (3, 'Neutral'),
        (4, 'Satisfied'),
        (5, 'Very Satisfied'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='survey_responses'
    )
    survey_type = models.CharField(
        max_length=20,
        choices=SURVEY_TYPE_CHOICES,
        help_text='Type of survey'
    )
    satisfaction_rating = models.IntegerField(
        choices=SATISFACTION_CHOICES,
        help_text='Overall satisfaction rating (1-5)'
    )
    difficulty_rating = models.IntegerField(
        null=True,
        blank=True,
        help_text='Difficulty appropriateness rating (1-5)'
    )
    engagement_rating = models.IntegerField(
        null=True,
        blank=True,
        help_text='Engagement level rating (1-5)'
    )
    feedback_text = models.TextField(
        blank=True,
        help_text='Open-ended feedback from user'
    )
    would_continue = models.BooleanField(
        default=True,
        help_text='Would user continue using the system'
    )
    adaptation_helpful = models.BooleanField(
        null=True,
        blank=True,
        help_text='Was the adaptation helpful (for post-adaptation surveys)'
    )
    context_data = models.JSONField(
        default=dict,
        help_text='Context when survey was taken (level, difficulty, etc.)'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.survey_type} - Rating: {self.satisfaction_rating}/5"
    
    class Meta:
        verbose_name = 'User Survey Response'
        verbose_name_plural = 'User Survey Responses'
        ordering = ['-timestamp']


class LoginActivityLog(models.Model):
    """Track login frequency and patterns (Metrik 2.1.4.1)"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='login_activities'
    )
    login_timestamp = models.DateTimeField(auto_now_add=True)
    logout_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When user logged out or session ended'
    )
    session_duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Total session duration in seconds'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of login'
    )
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        help_text='Browser/device information'
    )
    activities_performed = models.JSONField(
        default=dict,
        help_text='Activities performed during this session'
    )
    
    def __str__(self):
        return f"{self.user.username} - {self.login_timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        verbose_name = 'Login Activity Log'
        verbose_name_plural = 'Login Activity Logs'
        ordering = ['-login_timestamp']


class AdaptationEffectivenessLog(models.Model):
    """Track effectiveness of adaptations - Before vs After comparison (Metrik 2.1.4.2)"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='adaptation_effectiveness_logs'
    )
    adaptation_event = models.ForeignKey(
        ResponseToAdaptationLog,
        on_delete=models.CASCADE,
        related_name='effectiveness_logs',
        help_text='The adaptation event being tracked'
    )
    
    # Before adaptation metrics
    success_rate_before = models.FloatField(
        help_text='Success rate before adaptation (percentage)'
    )
    avg_time_before = models.FloatField(
        help_text='Average time per question before adaptation (seconds)'
    )
    attempts_before = models.PositiveIntegerField(
        help_text='Number of attempts before adaptation'
    )
    
    # After adaptation metrics
    success_rate_after = models.FloatField(
        help_text='Success rate after adaptation (percentage)'
    )
    avg_time_after = models.FloatField(
        help_text='Average time per question after adaptation (seconds)'
    )
    attempts_after = models.PositiveIntegerField(
        help_text='Number of attempts after adaptation'
    )
    
    # Calculated improvements
    success_rate_change = models.FloatField(
        help_text='Change in success rate (percentage points)'
    )
    time_efficiency_change = models.FloatField(
        help_text='Change in time efficiency (percentage)'
    )
    
    # User behavior after adaptation
    continued_session = models.BooleanField(
        help_text='Did user continue session after adaptation'
    )
    attempts_until_quit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Number of attempts before quitting (if applicable)'
    )
    
    measurement_window_days = models.PositiveIntegerField(
        default=7,
        help_text='Days used for before/after comparison'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - Δ Success: {self.success_rate_change:+.1f}%"
    
    class Meta:
        verbose_name = 'Adaptation Effectiveness Log'
        verbose_name_plural = 'Adaptation Effectiveness Logs'
        ordering = ['-timestamp']


class QLearningState(models.Model):
    """Represents a state in the Q-Learning system"""
    STATE_TYPE_CHOICES = [
        ('initial', 'Initial State'),
        ('learning', 'Learning State'),
        ('mastered', 'Mastered State'),
        ('struggling', 'Struggling State'),
    ]
    
    state_id = models.CharField(max_length=50, unique=True, help_text='Unique identifier for the state')
    state_type = models.CharField(max_length=20, choices=STATE_TYPE_CHOICES, help_text='Type of learning state')
    difficulty = models.CharField(max_length=20, help_text='Difficulty level associated with this state')
    concept = models.CharField(max_length=100, help_text='Learning concept this state represents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, help_text='Additional metadata for the state')
    
    def __str__(self):
        return f"{self.state_type.capitalize()} - {self.concept} ({self.difficulty})"


class UserLearningState(models.Model):
    """Tracks a user's current learning state in the Q-Learning system"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learning_states'
    )
    state = models.ForeignKey(
        QLearningState,
        on_delete=models.CASCADE,
        related_name='user_states'
    )
    q_values = models.JSONField(
        default=dict,
        help_text='Q-values for each possible action in this state'
    )
    visit_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of times user has been in this state'
    )
    last_visited = models.DateTimeField(
        auto_now=True,
        help_text='When user was last in this state'
    )
    is_current = models.BooleanField(
        default=False,
        help_text='Whether this is the user\'s current state'
    )
    metadata = models.JSONField(
        default=dict,
        help_text='Additional learning state metadata'
    )
    
    class Meta:
        unique_together = ['user', 'state']
        ordering = ['-is_current', '-last_visited']
    
    def __str__(self):
        return f"{self.user.username} - {self.state} (Visits: {self.visit_count})"
    
    def save(self, *args, **kwargs):
        # Ensure only one current state per user
        if self.is_current:
            UserLearningState.objects.filter(
                user=self.user, 
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class QLearningDecisionLog(models.Model):
    """Track Q-Learning decision making process - Exploration vs Exploitation (Metrik 2.1.4.4)"""
    DECISION_TYPE_CHOICES = [
        ('exploitation', 'Exploitation (Best Q-value)'),
        ('exploration', 'Exploration (Random)'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='qlearning_decisions'
    )
    state_hash = models.CharField(
        max_length=32,
        help_text='Current state hash'
    )
    decision_type = models.CharField(
        max_length=15,
        choices=DECISION_TYPE_CHOICES,
        help_text='Was this exploration or exploitation'
    )
    epsilon_value = models.FloatField(
        help_text='Epsilon value at time of decision'
    )
    action_chosen = models.CharField(
        max_length=20,
        help_text='Action that was chosen'
    )
    q_value_chosen = models.FloatField(
        help_text='Q-value of chosen action'
    )
    best_q_value = models.FloatField(
        help_text='Best available Q-value'
    )
    all_q_values = models.JSONField(
        help_text='All Q-values for this state'
    )
    is_optimal = models.BooleanField(
        help_text='Was the optimal action chosen'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.decision_type} - {self.action_chosen}"
    
    class Meta:
        verbose_name = 'Q-Learning Decision Log'
        verbose_name_plural = 'Q-Learning Decision Logs'
        ordering = ['-timestamp']
