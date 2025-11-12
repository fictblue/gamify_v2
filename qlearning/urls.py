from django.urls import path
from . import views
from .api_views import LoginActivityAPI, check_new_logins, QLearningMetricsAPI

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

    # Login Activity API
    path('api/login-activity/', LoginActivityAPI.as_view(), name='login_activity'),
    path('api/check-new-logins/', check_new_logins, name='check_new_logins'),
    
    # Legacy endpoints (for backward compatibility)
    path('api/claim-level/', views.LevelUpClaimView.as_view(), name='api_claim_level'),
    
    # Q-Learning Metrics API
    path('api/metrics/', QLearningMetricsAPI.as_view(), name='qlearning_metrics'),
]
