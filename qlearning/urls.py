from django.urls import path
from . import views

app_name = 'qlearning'

urlpatterns = [
    # Level up API endpoints
    path('student/claim-level/', views.LevelUpClaimView.as_view(), name='claim_level'),
    path('student/level-status/', views.level_up_status, name='level_status'),

    # CSV Export endpoints
    path('export-engagement-logs/', views.export_engagement_logs, name='export_engagement'),
    path('export-success-logs/', views.export_success_logs, name='export_success'),
    path('export-transition-logs/', views.export_transition_logs, name='export_transitions'),
    path('export-reward-logs/', views.export_reward_logs, name='export_rewards'),
    path('export-qlearning-logs/', views.export_qlearning_logs, name='export_qlearning'),
    path('export-qlearning-performance-logs/', views.export_qlearning_performance_logs, name='export_qlearning_performance'),
    path('export-global-logs/', views.export_global_logs, name='export_global'),

    # Legacy endpoints (for backward compatibility)
    path('api/claim-level/', views.LevelUpClaimView.as_view(), name='api_claim_level'),
]
