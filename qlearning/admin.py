from django.contrib import admin
from .models import (
    QTableEntry, QLearningLog,
    UserEngagementLog, SuccessRateLog, ResponseToAdaptationLog,
    QLearningPerformanceLog, LevelTransitionLog, RewardIncentivesLog, GlobalSystemLog
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
