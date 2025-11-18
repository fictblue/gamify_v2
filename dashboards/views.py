from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.db.models import Count, Q, F, Sum, Avg, Max, Min, Case, When, Value, IntegerField
from django.db.models.functions import TruncDate, TruncHour, TruncDay, TruncWeek, TruncMonth, TruncYear, ExtractWeekDay, ExtractHour
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.csrf import csrf_exempt
import json
import pandas as pd
import csv
from io import StringIO, BytesIO
import xlsxwriter
from datetime import datetime, timedelta

from accounts.models import CustomUser, StudentProfile
from quizzes.models import AttemptLog, Question
from .export_utils import export_research_data
from qlearning.models import (
    QLearningLog, LevelTransitionLog, UserEngagementLog, 
    SuccessRateLog, ResponseToAdaptationLog, QLearningPerformanceLog, 
    RewardIncentivesLog, GlobalSystemLog, UserSurveyResponse, 
    LoginActivityLog, AdaptationEffectivenessLog, QLearningDecisionLog
)

@method_decorator(login_required, name='dispatch')
class StudentDashboardView(View):
    """Student dashboard showing progress, stats, and available quizzes"""

    def get(self, request):
        if request.user.role != 'student':
            messages.error(request, 'Access denied. Student dashboard is for students only.')
            return redirect('accounts:login')

        try:
            profile = request.user.student_profile
        except StudentProfile.DoesNotExist:
            # Create profile if it doesn't exist
            profile = StudentProfile.objects.create(user=request.user)

        # Get quiz statistics for the student
        from quizzes.models import Question, AttemptLog
        total_attempts = AttemptLog.objects.filter(user=request.user).count()
        correct_attempts = AttemptLog.objects.filter(user=request.user, is_correct=True).count()
        success_rate = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0

        # Get recent attempts
        recent_attempts = AttemptLog.objects.filter(user=request.user).select_related('question').order_by('-created_at')[:5]

        # Get questions by difficulty preference
        from django.db.models import Count
        questions_by_difficulty = Question.objects.values('difficulty').annotate(count=Count('difficulty'))

        # Get available questions count
        total_available_questions = Question.objects.count()

        # XP and level-up information
        xp_for_next_level = profile.get_xp_for_next_level()
        xp_progress_percentage = profile.get_xp_progress_percentage()
        can_level_up = profile.can_level_up()

        context = {
            'profile': profile,
            'user': request.user,
            'level': profile.get_level_display(),
            'progress_percentage': min(profile.progress, 100),
            'xp': profile.total_xp,  # Use total_xp for consistency with navbar/sidebar
            'total_xp': profile.total_xp,
            'xp_for_next_level': xp_for_next_level,
            'xp_progress_percentage': xp_progress_percentage,
            'can_level_up': can_level_up,
            'recent_achievements': [],  # TODO: Implement achievements
            'upcoming_quizzes': [],     # TODO: Implement quiz system
            # Quiz statistics
            'total_attempts': total_attempts,
            'correct_attempts': correct_attempts,
            'success_rate': round(success_rate, 1),
            'recent_attempts': recent_attempts,
            'questions_by_difficulty': {item['difficulty']: item['count'] for item in questions_by_difficulty},
            'total_available_questions': total_available_questions,
        }

        return render(request, 'dashboards/student_dashboard.html', context)


@method_decorator(login_required, name='dispatch')
class AdminDashboardView(View):
    """Admin dashboard showing system statistics and management options"""

    def get(self, request):
        if request.user.role != 'admin':
            messages.error(request, 'Access denied. Admin dashboard is for administrators only.')
            return redirect('accounts:login')

        # Get system statistics
        total_students = CustomUser.objects.filter(role='student', is_active=True).count()
        total_profiles = StudentProfile.objects.count()
        avg_progress = StudentProfile.objects.aggregate(
            avg_progress=Avg('progress')
        )['avg_progress'] or 0

        # Get quiz statistics
        from quizzes.models import Question, AttemptLog
        total_questions = Question.objects.count()
        total_attempts = AttemptLog.objects.count()

        # Get recent attempts
        recent_attempts = AttemptLog.objects.select_related('user', 'question').order_by('-created_at')[:10]

        # Get question statistics by difficulty
        questions_by_difficulty = {
            'easy': Question.objects.filter(difficulty='easy').count(),
            'medium': Question.objects.filter(difficulty='medium').count(),
            'hard': Question.objects.filter(difficulty='hard').count(),
        }

        # Get attempt success rate
        correct_attempts = AttemptLog.objects.filter(is_correct=True).count()
        success_rate = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0

        # Get recent student registrations with profile data
        recent_registrations = list(CustomUser.objects.select_related('student_profile').filter(
            role='student',
            is_active=True  # Only count active students
        ).order_by('-date_joined')[:5])  # Convert to list to prevent multiple queries

        # Debug information to help identify discrepancies
        all_students = CustomUser.objects.filter(role='student')
        active_students = all_students.filter(is_active=True)
        inactive_students = all_students.filter(is_active=False)

        # Get comprehensive analytics data
        from qlearning.analytics import AnalyticsService
        analytics_data = AnalyticsService.get_comprehensive_dashboard_data()
        
        # Get user growth data (last 7 days)
        today = timezone.now().date()
        date_range = [today - timedelta(days=i) for i in range(6, -1, -1)]  # Last 7 days
        
        user_growth = []
        for date in date_range:
            next_day = date + timedelta(days=1)
            count = CustomUser.objects.filter(
                date_joined__date__gte=date,
                date_joined__date__lt=next_day,
                is_active=True  # Only count active users
            ).count()
            user_growth.append(count)
        
        # Prepare user growth data for the template
        user_growth_data = {
            'labels': [date.strftime('%a') for date in date_range],  # ['Mon', 'Tue', ...]
            'data': user_growth,  # [5, 8, 12, ...]
            'total_users': total_students,  # For verification
            'start_date': date_range[0].strftime('%Y-%m-%d'),
            'end_date': date_range[-1].strftime('%Y-%m-%d')
        }

        context = {
            'user': request.user,
            'total_students': total_students,
            'total_profiles': total_profiles,
            'avg_progress': round(avg_progress, 1),
            'recent_registrations': recent_registrations,
            # Quiz statistics
            'total_questions': total_questions,
            'total_attempts': total_attempts,
            'recent_attempts': recent_attempts,
            'questions_by_difficulty': questions_by_difficulty,
            'success_rate': round(success_rate, 1),
            # Debug info (remove in production)
            'debug_info': {
                'total_students_displayed': total_students,  # This should match the card
                'active_students_count': active_students.count(),
                'inactive_students_count': inactive_students.count(),
                'recent_registrations_count': len(recent_registrations),  # Use len() for list
            },
            # Analytics data
            'analytics': analytics_data,
            'user_growth_data_json': json.dumps(user_growth_data),
        }

        return render(request, 'dashboards/admin_dashboard.html', context)


import csv
from io import StringIO
from django.utils import timezone

@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class UserGrowthDataView(View):
    """API endpoint to fetch real-time user growth data"""
    
    def get(self, request):
        range_type = request.GET.get('range', 'week')  # week, month, year
        
        # Determine date range
        today = timezone.now().date()
        
        if range_type == 'month':
            days = 30
            date_format = '%b %d'
        elif range_type == 'year':
            days = 365
            date_format = '%b %Y'
        else:  # week (default)
            days = 7
            date_format = '%a'  # Mon, Tue, etc.
        
        # Generate date range
        date_range = [today - timedelta(days=i) for i in range(days-1, -1, -1)]
        labels = [date.strftime(date_format) for date in date_range]
        
        # Get user counts for each day
        user_counts = []
        
        for date in date_range:
            next_day = date + timedelta(days=1)
            count = CustomUser.objects.filter(
                date_joined__date__gte=date,
                date_joined__date__lt=next_day,
                is_active=True
            ).count()
            user_counts.append(count)
            
        total_users = CustomUser.objects.filter(is_active=True).count()
        
        return JsonResponse({
            'success': True,
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': 'New Users',
                    'data': user_counts,
                    'total_users': total_users,
                    'start_date': date_range[0].strftime('%Y-%m-%d'),
                    'end_date': date_range[-1].strftime('%Y-%m-%d')
                }]
            }
        })


class ResearchDataExportView(View):
    """View for exporting research data in various formats"""
    
    @method_decorator(login_required)
    def get(self, request, format='excel'):
        if not request.user.is_staff:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Get format from URL or query parameter
        export_format = request.GET.get('format', format).lower()
        
        # Use the export_research_data function
        from .export_utils import export_research_data
        
        try:
            return export_research_data(export_format)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'error': 'Failed to generate export',
                'details': str(e)
            }, status=500)
    
    def export_excel(self):
        """Export data to Excel format"""
        output = BytesIO()
        
        # Create a Pandas Excel writer using XlsxWriter as the engine
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        
        # Get and write each dataset to a different worksheet
        data = self.get_export_data()
        
        for sheet_name, df_data in data.items():
            if isinstance(df_data, dict):
                # Convert dict to DataFrame
                if 'data' in df_data and isinstance(df_data['data'], list):
                    df = pd.DataFrame(df_data['data'])
                    df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        
        # Save the Excel file
        writer.close()
        output.seek(0)
        
        # Create the response
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="research_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        return response
    
    def export_json(self):
        """Export data to JSON format"""
        data = self.get_export_data()
        response = JsonResponse(data, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = f'attachment; filename="research_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
        return response
    
    def export_csv(self):
        """Export data to CSV format"""
        data = self.get_export_data()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="research_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Write each dataset as a separate section
        for section, section_data in data.items():
            if isinstance(section_data, dict) and 'data' in section_data and isinstance(section_data['data'], list):
                writer.writerow([f'=== {section.upper()} ==='])
                df = pd.DataFrame(section_data['data'])
                writer.writerow(df.columns.tolist())  # Write headers
                for _, row in df.iterrows():
                    writer.writerow(row.tolist())
                writer.writerow([])  # Add empty row between sections
        
        return response
    
    def get_export_data(self):
        """Get all data for export"""
        from .export_utils import (
            get_user_engagement_metrics,
            get_success_rate_metrics,
            get_qlearning_performance_metrics,
            get_adaptation_effectiveness_metrics
        )
        
        # Get the data
        user_engagement = get_user_engagement_metrics()
        success_rates = get_success_rate_metrics()
        qlearning_performance = get_qlearning_performance_metrics()
        adaptation_effectiveness = get_adaptation_effectiveness_metrics()
        
        # Print debug info
        print("\n=== DEBUG: Export Data ===")
        print(f"User Engagement: {user_engagement}")
        print(f"Success Rates: {success_rates}")
        print(f"Q-Learning Performance: {qlearning_performance}")
        print(f"Adaptation Effectiveness: {adaptation_effectiveness}")
        
        return {
            'user_engagement': user_engagement,
            'success_rates': success_rates,
            'qlearning_performance': qlearning_performance,
            'adaptation_effectiveness': adaptation_effectiveness,
            'metadata': {
                'exported_at': timezone.now().isoformat(),
                'exported_by': self.request.user.username
            }
        }
    
    def export_logs_csv(self, log_type):
        """Export logs in CSV format based on log type"""
        from qlearning.models import (
            UserEngagementLog, SuccessRateLog, ResponseToAdaptationLog,
            QLearningPerformanceLog, LevelTransitionLog, RewardIncentivesLog,
            GlobalSystemLog, UserSurveyResponse, LoginActivityLog,
            AdaptationEffectivenessLog, QLearningDecisionLog
        )
        
        # Map log types to their models and fields
        LOG_MODELS = {
            # Existing log types
            'engagement': (UserEngagementLog.objects.all(), [
                'id', 'user__username', 'session_type', 'timestamp', 
                'duration_seconds', 'questions_attempted', 'hints_used',
                'gamification_interactions', 'metadata'
            ]),
            'success': (SuccessRateLog.objects.all(), [
                'id', 'user__username', 'difficulty', 'total_attempts',
                'correct_attempts', 'average_time_spent', 'accuracy_percentage',
                'time_window_start', 'time_window_end', 'metadata'
            ]),
            'qlearning': (QLearningPerformanceLog.objects.all(), [
                'id', 'user__username', 'state_hash', 'optimal_action_frequency',
                'average_q_value', 'q_table_size', 'learning_progress',
                'timestamp', 'metadata', 'action_distribution', 'snapshot_interval'
            ]),
            'transitions': (LevelTransitionLog.objects.all(), [
                'id', 'user__username', 'transition_type', 'old_level',
                'new_level', 'timestamp', 'transition_condition', 'performance_metrics'
            ]),
            'rewards': (RewardIncentivesLog.objects.all(), [
                'id', 'user__username', 'reward_type', 'reward_value',
                'session_continuation', 'timestamp', 'trigger_condition', 'user_reaction'
            ]),
            # New log types
            'surveys': (UserSurveyResponse.objects.all(), [
                'id', 'user__username', 'survey_type', 'satisfaction_rating',
                'difficulty_rating', 'engagement_rating', 'feedback_text',
                'would_continue', 'adaptation_helpful', 'timestamp', 'context_data'
            ]),
            'login_activity': (LoginActivityLog.objects.all(), [
                'id', 'user__username', 'login_timestamp', 'logout_timestamp',
                'session_duration_seconds', 'ip_address', 'user_agent',
                'activities_performed'
            ]),
            'adaptation_effectiveness': (AdaptationEffectivenessLog.objects.all(), [
                'id', 'user__username', 'adaptation_event_id', 'success_rate_before',
                'success_rate_after', 'success_rate_change', 'avg_time_before',
                'avg_time_after', 'attempts_before', 'attempts_after',
                'time_efficiency_change', 'continued_session', 'attempts_until_quit',
                'measurement_window_days', 'timestamp'
            ]),
            'qlearning_decisions': (QLearningDecisionLog.objects.all(), [
                'id', 'user__username', 'state_hash', 'decision_type',
                'epsilon_value', 'action_chosen', 'q_value_chosen', 'best_q_value',
                'all_q_values', 'is_optimal', 'timestamp'
            ])
        }
        
        if log_type not in LOG_MODELS:
            return JsonResponse({'error': f'Invalid log type: {log_type}'}, status=400)
        
        # Get the queryset and fields for this log type
        queryset, fields = LOG_MODELS[log_type]
        
        # Create a file-like buffer to receive CSV data
        buffer = StringIO()
        writer = csv.writer(buffer)
        
        # Write header
        writer.writerow([field.replace('__', ' ').replace('_', ' ').title() for field in fields])
        
        # Write data rows
        for item in queryset:
            row = []
            for field in fields:
                # Handle related fields (e.g., user__username)
                if '__' in field:
                    obj = item
                    for part in field.split('__'):
                        obj = getattr(obj, part, None)
                        if obj is None:
                            break
                    row.append(str(obj) if obj is not None else '')
                else:
                    value = getattr(item, field, '')
                    # Handle datetime fields
                    if hasattr(value, 'strftime'):
                        value = value.strftime('%Y-%m-%d %H:%M:%S')
                    row.append(str(value) if value is not None else '')
            writer.writerow(row)
        
        # Create the response with CSV data
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{log_type}_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        return response


class AdminDashboardAjaxView(View):
    """AJAX view for admin dashboard real-time data"""

    def get(self, request):
        if request.user.role != 'admin':
            return JsonResponse({'error': 'Access denied'}, status=403)

        action = request.GET.get('action')

        if action == 'get_attempt_detail':
            return self.get_attempt_detail(request)
        elif action == 'get_user_profile':
            return self.get_user_profile(request)
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)

    def get_attempt_detail(self, request):
        """Get detailed information about a specific attempt"""
        attempt_id = request.GET.get('attempt_id')
        if not attempt_id:
            return JsonResponse({'error': 'Attempt ID required'}, status=400)

        try:
            attempt = AttemptLog.objects.select_related('user', 'question').get(id=attempt_id)

            # Get question details
            question_data = {
                'text': attempt.question.text,
                'topic': attempt.question.curriculum_tag or 'General',
                'difficulty': attempt.question.get_difficulty_display(),
                'format': attempt.question.get_format_display(),
                'options': attempt.question.options if attempt.question.options else {},
                'answer_key': attempt.question.answer_key,
                'explanation': attempt.question.explanation or 'No explanation provided'
            }

            # Get attempt results
            attempt_data = {
                'id': attempt.id,
                'result_status': 'Correct' if attempt.is_correct else 'Incorrect',
                'time_spent': attempt.time_spent,
                'selected_answer': attempt.chosen_answer or 'No answer provided',
                'score': attempt.reward_numeric,
                'hints_used': attempt.hint_given or 'No hints used',
                'timestamp': attempt.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }

            return JsonResponse({
                'success': True,
                'question_details': question_data,
                'attempt_results': attempt_data
            })

        except AttemptLog.DoesNotExist:
            return JsonResponse({'error': 'Attempt not found'}, status=404)

    def get_user_profile(self, request):
        """Get detailed information about a specific user"""
        username = request.GET.get('username')
        if not username:
            return JsonResponse({'error': 'Username required'}, status=400)

        try:
            user = CustomUser.objects.select_related('student_profile').get(username=username, role='student')

            # Handle case where student_profile doesn't exist yet
            try:
                profile = user.student_profile
                level_display = profile.get_level_display()
            except StudentProfile.DoesNotExist:
                # Create default profile if it doesn't exist
                profile, created = StudentProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'level': 'beginner',
                        'points': 0,
                        'xp': 0,
                        'total_xp': 0,
                        'streak_correct': 0,
                        'progress': 0,
                        'last_difficulty': 'easy',
                    }
                )
                level_display = profile.get_level_display() if not created else 'Beginner'

            # Get student statistics
            total_attempts = AttemptLog.objects.filter(user=user).count()
            correct_attempts = AttemptLog.objects.filter(user=user, is_correct=True).count()
            avg_score = AttemptLog.objects.filter(user=user).aggregate(
                avg_score=Avg('reward_numeric')
            )['avg_score'] or 0

            student_data = {
                'username': user.username,
                'level': level_display,
                'email': user.email or 'No email provided',
                'join_date': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                'total_attempts': total_attempts,
                'average_score': round(avg_score, 2)
            }

            # Simulated real-time system performance data
            import time
            import random

            system_performance = {
                'response_time': f"{random.uniform(50, 200):.0f}ms",
                'server_location': 'Jakarta, Indonesia',
                'cache_status': random.choice(['Active', 'Stale', 'Refreshing']),
                'ai_confidence': f"{random.uniform(85, 98):.1f}%",
                'real_time_status': 'Connected' if random.random() > 0.1 else 'Reconnecting'
            }

            return JsonResponse({
                'success': True,
                'student_information': student_data,
                'system_performance': system_performance
            })

        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
