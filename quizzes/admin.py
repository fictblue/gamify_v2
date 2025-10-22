from django.contrib import admin
from .models import Question, AttemptLog

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin interface for Question model with Q-learning integration"""

    list_display = ('text', 'difficulty', 'format', 'curriculum_tag', 'created_at')
    list_filter = ('difficulty', 'format', 'curriculum_tag', 'created_at')
    search_fields = ('text', 'curriculum_tag', 'answer_key')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Question Content', {
            'fields': ('text', 'format', 'difficulty', 'curriculum_tag')
        }),
        ('Answer Configuration', {
            'fields': ('options', 'answer_key', 'explanation')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('attempt_logs')


@admin.register(AttemptLog)
class AttemptLogAdmin(admin.ModelAdmin):
    """Admin interface for AttemptLog model with Q-learning data"""

    list_display = ('user', 'question', 'is_correct', 'difficulty_attempted', 'time_spent', 'reward_numeric', 'created_at')
    list_filter = ('is_correct', 'difficulty_attempted', 'created_at')
    search_fields = ('user__username', 'question__text', 'chosen_answer')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Attempt Information', {
            'fields': ('user', 'question', 'chosen_answer', 'is_correct', 'difficulty_attempted')
        }),
        ('Performance Metrics', {
            'fields': ('time_spent', 'reward_numeric', 'hint_given')
        }),
        ('Q-Learning Data', {
            'fields': ('qtable_snapshot',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'question')
