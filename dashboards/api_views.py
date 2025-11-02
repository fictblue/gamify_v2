"""
API Views for Admin Dashboard
Provides JSON endpoints for dynamic data loading
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Avg, Count
from django.utils import timezone
from accounts.models import CustomUser
from quizzes.models import AttemptLog
from qlearning.models import QLearningDecisionLog


@login_required
@require_http_methods(["GET"])
def top_users_success_rate(request):
    """Get top 10 users by success rate"""
    
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get users with their success rates
    users_data = []
    
    for user in CustomUser.objects.filter(role='student', is_active=True):
        attempts = AttemptLog.objects.filter(user=user)
        if attempts.exists():
            total = attempts.count()
            correct = attempts.filter(is_correct=True).count()
            success_rate = (correct / total * 100) if total > 0 else 0
            
            users_data.append({
                'username': user.username,
                'success_rate': round(success_rate, 1),
                'total_attempts': total
            })
    
    # Sort by success rate and get top 10
    users_data.sort(key=lambda x: x['success_rate'], reverse=True)
    top_10 = users_data[:10]
    
    return JsonResponse({
        'usernames': [u['username'] for u in top_10],
        'success_rates': [u['success_rate'] for u in top_10],
        'total_attempts': [u['total_attempts'] for u in top_10]
    })


@login_required
@require_http_methods(["GET"])
def qlearning_logs_api(request):
    """Get Q-Learning decision logs with pagination"""
    
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    limit = int(request.GET.get('limit', 50))
    offset = int(request.GET.get('offset', 0))
    
    logs = QLearningDecisionLog.objects.select_related('user').order_by('-timestamp')[offset:offset+limit]
    
    logs_data = []
    for log in logs:
        logs_data.append({
            'user': log.user.username,
            'state_hash': log.state_hash,
            'action_chosen': log.action_chosen,
            'decision_type': log.decision_type,
            'q_value_chosen': float(log.q_value_chosen),
            'best_q_value': float(log.best_q_value),
            'is_optimal': log.is_optimal,
            'epsilon_value': float(log.epsilon_value),
            'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return JsonResponse({
        'logs': logs_data,
        'count': len(logs_data),
        'offset': offset,
        'limit': limit
    })


@login_required
@require_http_methods(["GET"])
def download_qtable(request):
    """Download complete Q-Table as JSON"""
    
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    from qlearning.models import QTableEntry
    
    qtable_data = []
    for entry in QTableEntry.objects.select_related('user').all():
        qtable_data.append({
            'user': entry.user.username,
            'state_hash': entry.state_hash,
            'action': entry.action,
            'q_value': float(entry.q_value),
            'updated_at': entry.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    response = JsonResponse({
        'qtable': qtable_data,
        'total_entries': len(qtable_data),
        'exported_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    # Set download headers
    response['Content-Disposition'] = f'attachment; filename="qtable_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
    
    return response
