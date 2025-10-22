from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.shortcuts import redirect
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from accounts.models import StudentProfile, CustomUser
from quizzes.models import AttemptLog, Question
import json

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
            'xp': profile.xp,
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

        # Get recent student registrations (ensure consistency)
        recent_registrations = CustomUser.objects.filter(
            role='student',
            is_active=True  # Only count active students
        ).order_by('-date_joined')[:5]

        # Debug information to help identify discrepancies
        all_students = CustomUser.objects.filter(role='student')
        active_students = all_students.filter(is_active=True)
        inactive_students = all_students.filter(is_active=False)

        # Get comprehensive analytics data
        from qlearning.analytics import AnalyticsService
        analytics_data = AnalyticsService.get_comprehensive_dashboard_data()

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
                'recent_registrations_count': recent_registrations.count(),
            },
            # Analytics data
            'analytics': analytics_data,
        }

        return render(request, 'dashboards/admin_dashboard.html', context)


@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
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
