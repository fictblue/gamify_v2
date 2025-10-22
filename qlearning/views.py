from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from accounts.models import StudentProfile
from qlearning.policies import LevelTransitionPolicy


class LevelUpClaimView(View):
    """API endpoint for students to claim level up"""

    @method_decorator(login_required)
    def post(self, request):
        """Handle level up claim request"""
        # Ensure only students can access this endpoint
        if request.user.role != 'student':
            return JsonResponse({
                'success': False,
                'error': 'Only students can claim level ups'
            }, status=403)

        try:
            profile = request.user.student_profile
        except StudentProfile.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Student profile not found'
            }, status=404)

        with transaction.atomic():
            # Check if user can level up
            can_level_up, target_level = LevelTransitionPolicy.can_level_up(profile)

            if not can_level_up or not target_level:
                return JsonResponse({
                    'success': False,
                    'error': 'Level up requirements not met',
                    'current_level': profile.level,
                    'can_level_up': False
                }, status=400)

            # Perform manual level up
            old_level = profile.level  # Store before update
            leveled_up, new_level = profile.manual_level_up()

            if not leveled_up:
                return JsonResponse({
                    'success': False,
                    'error': 'Level up failed',
                    'current_level': profile.level
                }, status=400)

            # Save the profile
            profile.save()

            # Get updated statistics
            level_progress = LevelTransitionPolicy.calculate_level_progress(profile)
            user_stats = LevelTransitionPolicy.get_user_statistics(request.user)

            return JsonResponse({
                'success': True,
                'message': f'Successfully leveled up from {old_level} to {new_level}!',
                'old_level': old_level,
                'new_level': new_level,
                'new_progress': profile.progress,
                'level_progress': level_progress,
                'user_stats': user_stats
            })

    def get(self, request):
        """Get level up status for the current user"""
        if request.user.role != 'student':
            return JsonResponse({
                'success': False,
                'error': 'Only students can check level up status'
            }, status=403)

        try:
            profile = request.user.student_profile
        except StudentProfile.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Student profile not found'
            }, status=404)

        can_level_up, target_level = LevelTransitionPolicy.can_level_up(profile)
        level_progress = LevelTransitionPolicy.calculate_level_progress(profile)
        user_stats = LevelTransitionPolicy.get_user_statistics(request.user)

        return JsonResponse({
            'success': True,
            'can_level_up': can_level_up,
            'target_level': target_level,
            'current_level': profile.level,
            'level_progress': level_progress,
            'user_stats': user_stats
        })


@require_http_methods(['GET', 'POST'])
@login_required
def level_up_status(request):
    """Legacy function-based view for level up status (for backward compatibility)"""
    if request.user.role != 'student':
        return JsonResponse({
            'success': False,
            'error': 'Only students can check level up status'
        }, status=403)

    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student profile not found'
        }, status=404)

    can_level_up, target_level = LevelTransitionPolicy.can_level_up(profile)
    level_progress = LevelTransitionPolicy.calculate_level_progress(profile)

    return JsonResponse({
        'success': True,
        'can_level_up': can_level_up,
        'target_level': target_level,
        'current_level': profile.level,
        'level_progress': level_progress
    })


# Sprint 7 - CSV Export Views

@csrf_exempt
@login_required
def export_engagement_logs(request):
    """Export user engagement logs to CSV"""
    from qlearning.models import UserEngagementLog
    import csv
    from io import StringIO

    logs = UserEngagementLog.objects.select_related('user').all()
    fieldnames = ['user', 'session_type', 'session_id', 'duration_seconds',
                 'questions_attempted', 'hints_used', 'gamification_interactions', 'timestamp']

    # Create CSV content
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    writer.writeheader()
    for log in logs:
        row = {}
        for field in fieldnames:
            value = getattr(log, field, '')
            if hasattr(value, 'strftime'):
                row[field] = value.strftime('%Y-%m-%d %H:%M:%S')
            else:
                row[field] = str(value)
        writer.writerow(row)

    output.seek(0)
    response = HttpResponse(output.read(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="engagement_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    return response


@csrf_exempt
@login_required
def export_success_logs(request):
    """Export success rate logs to CSV"""
    from qlearning.models import SuccessRateLog
    import csv
    from io import StringIO

    logs = SuccessRateLog.objects.select_related('user').all()
    fieldnames = ['user', 'difficulty', 'total_attempts', 'correct_attempts',
                 'accuracy_percentage', 'average_time_spent', 'time_window_start', 'time_window_end']

    # Create CSV content
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    writer.writeheader()
    for log in logs:
        row = {}
        for field in fieldnames:
            value = getattr(log, field, '')
            if hasattr(value, 'strftime'):
                row[field] = value.strftime('%Y-%m-%d %H:%M:%S')
            else:
                row[field] = str(value)
        writer.writerow(row)

    output.seek(0)
    response = HttpResponse(output.read(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="success_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    return response


@csrf_exempt
@login_required
def export_transition_logs(request):
    """Export level transition logs to CSV"""
    from qlearning.models import LevelTransitionLog
    import csv
    from io import StringIO

    logs = LevelTransitionLog.objects.select_related('user').all()
    fieldnames = ['user', 'transition_type', 'old_level', 'new_level', 'timestamp']

    # Create CSV content
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    writer.writeheader()
    for log in logs:
        row = {}
        for field in fieldnames:
            value = getattr(log, field, '')
            if hasattr(value, 'strftime'):
                row[field] = value.strftime('%Y-%m-%d %H:%M:%S')
            else:
                row[field] = str(value)
        writer.writerow(row)

    output.seek(0)
    response = HttpResponse(output.read(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="transition_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    return response


@csrf_exempt
@login_required
def export_reward_logs(request):
    """Export reward and incentives logs to CSV"""
    from qlearning.models import RewardIncentivesLog
    import csv
    from io import StringIO

    logs = RewardIncentivesLog.objects.select_related('user').all()
    fieldnames = ['user', 'reward_type', 'reward_value', 'session_continuation', 'timestamp']

    # Create CSV content
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    writer.writeheader()
    for log in logs:
        row = {}
        for field in fieldnames:
            value = getattr(log, field, '')
            if hasattr(value, 'strftime'):
                row[field] = value.strftime('%Y-%m-%d %H:%M:%S')
            else:
                row[field] = str(value)
        writer.writerow(row)

    output.seek(0)
    response = HttpResponse(output.read(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="reward_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    return response


@csrf_exempt
@login_required
def export_qlearning_logs(request):
    """Export Q-Learning logs to CSV"""
    from qlearning.models import QLearningLog
    import csv
    from io import StringIO

    logs = QLearningLog.objects.select_related('user').all()
    fieldnames = ['user', 'state_hash', 'action', 'reward', 'q_value_before', 'q_value_after', 'timestamp']

    # Create CSV content
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    writer.writeheader()
    for log in logs:
        row = {}
        for field in fieldnames:
            value = getattr(log, field, '')
            if hasattr(value, 'strftime'):
                row[field] = value.strftime('%Y-%m-%d %H:%M:%S')
            else:
                row[field] = str(value)
        writer.writerow(row)

    output.seek(0)
    response = HttpResponse(output.read(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="qlearning_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    return response


@csrf_exempt
@login_required
def export_qlearning_performance_logs(request):
    """Export Q-Learning performance logs to CSV"""
    from qlearning.models import QLearningPerformanceLog
    import csv
    from io import StringIO

    logs = QLearningPerformanceLog.objects.select_related('user').all()
    fieldnames = ['user', 'state_hash', 'optimal_action_frequency', 'average_q_value', 'q_table_size', 'timestamp']

    # Create CSV content
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    writer.writeheader()
    for log in logs:
        row = {}
        for field in fieldnames:
            value = getattr(log, field, '')
            if hasattr(value, 'strftime'):
                row[field] = value.strftime('%Y-%m-%d %H:%M:%S')
            else:
                row[field] = str(value)
        writer.writerow(row)

    output.seek(0)
    response = HttpResponse(output.read(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="qlearning_performance_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    return response


@csrf_exempt
@login_required
def export_global_logs(request):
    """Export global system logs to CSV"""
    from qlearning.models import GlobalSystemLog
    import csv
    from io import StringIO

    logs = GlobalSystemLog.objects.all()
    fieldnames = ['metric_type', 'time_window', 'timestamp']

    # Create CSV content
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    writer.writeheader()
    for log in logs:
        row = {}
        for field in fieldnames:
            value = getattr(log, field, '')
            if field == 'metric_data':
                row[field] = str(value)
            elif hasattr(value, 'strftime'):
                row[field] = value.strftime('%Y-%m-%d %H:%M:%S')
            else:
                row[field] = str(value)
        writer.writerow(row)

    output.seek(0)
    response = HttpResponse(output.read(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="global_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    return response
