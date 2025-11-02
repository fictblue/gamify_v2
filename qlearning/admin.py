from django.contrib import admin
from .models import (
    QTableEntry, QLearningLog,
    UserEngagementLog, SuccessRateLog, ResponseToAdaptationLog,
    QLearningPerformanceLog, LevelTransitionLog, RewardIncentivesLog, GlobalSystemLog,
    UserSurveyResponse, LoginActivityLog, AdaptationEffectivenessLog, QLearningDecisionLog
)

@admin.register(QTableEntry)
class QTableEntryAdmin(admin.ModelAdmin):
    """Admin interface for Q-Table entries"""

    list_display = ('user', 'state_hash', 'action', 'q_value', 'updated_at')
    list_filter = ('action', 'updated_at')
    search_fields = ('user__username', 'state_hash')
    ordering = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Q-Table Entry', {
            'fields': ('user', 'state_hash', 'action', 'q_value')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(QLearningLog)
class QLearningLogAdmin(admin.ModelAdmin):
    """Admin interface for Q-Learning logs"""

    list_display = ('user', 'state_hash', 'action', 'reward', 'q_value_before', 'q_value_after', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'state_hash')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)

    fieldsets = (
        ('Learning Update', {
            'fields': ('user', 'state_hash', 'action', 'reward', 'q_value_before', 'q_value_after', 'next_state_hash')
        }),
        ('Metadata', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


# Sprint 7 - Analytics Admin Interfaces

@admin.register(UserEngagementLog)
class UserEngagementLogAdmin(admin.ModelAdmin):
    """Admin interface for user engagement logs"""

    list_display = ('user', 'session_type', 'duration_seconds', 'questions_attempted', 'hints_used', 'timestamp')
    list_filter = ('session_type', 'timestamp')
    search_fields = ('user__username', 'session_id')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)

    fieldsets = (
        ('Session Info', {
            'fields': ('user', 'session_type', 'session_id', 'duration_seconds')
        }),
        ('Activity Metrics', {
            'fields': ('questions_attempted', 'hints_used', 'gamification_interactions')
        }),
        ('Metadata', {
            'fields': ('timestamp', 'metadata'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(SuccessRateLog)
class SuccessRateLogAdmin(admin.ModelAdmin):
    """Admin interface for success rate logs"""

    list_display = ('user', 'difficulty', 'accuracy_percentage', 'total_attempts', 'time_window_end')
    list_filter = ('difficulty', 'time_window_end')
    search_fields = ('user__username',)
    ordering = ('-time_window_end',)
    readonly_fields = ('time_window_start', 'time_window_end')

    fieldsets = (
        ('Performance Data', {
            'fields': ('user', 'difficulty', 'total_attempts', 'correct_attempts', 'accuracy_percentage', 'average_time_spent')
        }),
        ('Time Window', {
            'fields': ('time_window_start', 'time_window_end'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(ResponseToAdaptationLog)
class ResponseToAdaptationLogAdmin(admin.ModelAdmin):
    """Admin interface for adaptation response logs"""

    list_display = ('user', 'adaptation_type', 'timestamp')
    list_filter = ('adaptation_type', 'timestamp')
    search_fields = ('user__username',)
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)

    fieldsets = (
        ('Adaptation Info', {
            'fields': ('user', 'adaptation_type', 'old_state', 'new_state')
        }),
        ('Details', {
            'fields': ('adaptation_details', 'first_attempt_after', 'hint_usage_change', 'session_duration_change')
        }),
        ('Metadata', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(QLearningPerformanceLog)
class QLearningPerformanceLogAdmin(admin.ModelAdmin):
    """Admin interface for Q-Learning performance logs"""

    list_display = ('user', 'optimal_action_frequency', 'average_q_value', 'q_table_size', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('user__username', 'state_hash')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)

    fieldsets = (
        ('Performance Metrics', {
            'fields': ('user', 'state_hash', 'optimal_action_frequency', 'average_q_value', 'q_table_size', 'learning_progress')
        }),
        ('Snapshot Info', {
            'fields': ('snapshot_interval', 'metadata')
        }),
        ('Metadata', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(LevelTransitionLog)
class LevelTransitionLogAdmin(admin.ModelAdmin):
    """Admin interface for level transition logs"""

    list_display = ('user', 'transition_type', 'old_level', 'new_level', 'timestamp')
    list_filter = ('transition_type', 'old_level', 'new_level', 'timestamp')
    search_fields = ('user__username',)
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)

    fieldsets = (
        ('Transition Info', {
            'fields': ('user', 'transition_type', 'old_level', 'new_level')
        }),
        ('Conditions', {
            'fields': ('transition_condition', 'performance_metrics')
        }),
        ('Metadata', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(RewardIncentivesLog)
class RewardIncentivesLogAdmin(admin.ModelAdmin):
    """Admin interface for reward and incentives logs"""

    list_display = ('user', 'reward_type', 'reward_value', 'session_continuation', 'timestamp')
    list_filter = ('reward_type', 'session_continuation', 'timestamp')
    search_fields = ('user__username',)
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)

    fieldsets = (
        ('Reward Info', {
            'fields': ('user', 'reward_type', 'reward_value')
        }),
        ('Trigger & Reaction', {
            'fields': ('trigger_condition', 'user_reaction', 'session_continuation')
        }),
        ('Metadata', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(GlobalSystemLog)
class GlobalSystemLogAdmin(admin.ModelAdmin):
    """Admin interface for global system logs"""

    list_display = ('metric_type', 'time_window', 'timestamp')
    list_filter = ('metric_type', 'time_window', 'timestamp')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)

    fieldsets = (
        ('Metric Info', {
            'fields': ('metric_type', 'time_window', 'metric_data')
        }),
        ('Metadata', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserSurveyResponse)
class UserSurveyResponseAdmin(admin.ModelAdmin):
    """Admin interface for user survey responses"""

    list_display = ('user', 'survey_type', 'satisfaction_rating', 'would_continue', 'timestamp')
    list_filter = ('survey_type', 'satisfaction_rating', 'would_continue', 'timestamp')
    search_fields = ('user__username', 'feedback_text')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)

    fieldsets = (
        ('Survey Info', {
            'fields': ('user', 'survey_type', 'timestamp')
        }),
        ('Ratings', {
            'fields': ('satisfaction_rating', 'difficulty_rating', 'engagement_rating', 'adaptation_helpful')
        }),
        ('Feedback', {
            'fields': ('feedback_text', 'would_continue')
        }),
        ('Context', {
            'fields': ('context_data',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(LoginActivityLog)
class LoginActivityLogAdmin(admin.ModelAdmin):
    """Admin interface for login activity logs"""

    list_display = ('user', 'login_timestamp', 'logout_timestamp', 'session_duration_seconds', 'ip_address')
    list_filter = ('login_timestamp',)
    search_fields = ('user__username', 'ip_address')
    ordering = ('-login_timestamp',)
    readonly_fields = ('login_timestamp',)

    fieldsets = (
        ('Session Info', {
            'fields': ('user', 'login_timestamp', 'logout_timestamp', 'session_duration_seconds')
        }),
        ('Connection Details', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Activities', {
            'fields': ('activities_performed',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(AdaptationEffectivenessLog)
class AdaptationEffectivenessLogAdmin(admin.ModelAdmin):
    """Admin interface for adaptation effectiveness logs"""

    list_display = ('user', 'success_rate_change', 'continued_session', 'timestamp')
    list_filter = ('continued_session', 'timestamp')
    search_fields = ('user__username',)
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)

    fieldsets = (
        ('Adaptation Reference', {
            'fields': ('user', 'adaptation_event', 'measurement_window_days')
        }),
        ('Before Metrics', {
            'fields': ('success_rate_before', 'avg_time_before', 'attempts_before')
        }),
        ('After Metrics', {
            'fields': ('success_rate_after', 'avg_time_after', 'attempts_after')
        }),
        ('Changes', {
            'fields': ('success_rate_change', 'time_efficiency_change')
        }),
        ('User Behavior', {
            'fields': ('continued_session', 'attempts_until_quit')
        }),
        ('Metadata', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'adaptation_event')


@admin.register(QLearningDecisionLog)
class QLearningDecisionLogAdmin(admin.ModelAdmin):
    """Admin interface for Q-Learning decision logs"""

    list_display = ('user', 'decision_type', 'action_chosen', 'is_optimal', 'epsilon_value', 'timestamp')
    list_filter = ('decision_type', 'is_optimal', 'timestamp')
    search_fields = ('user__username', 'state_hash')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)

    fieldsets = (
        ('Decision Info', {
            'fields': ('user', 'state_hash', 'decision_type', 'epsilon_value')
        }),
        ('Action Details', {
            'fields': ('action_chosen', 'q_value_chosen', 'best_q_value', 'is_optimal')
        }),
        ('Q-Values', {
            'fields': ('all_q_values',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
