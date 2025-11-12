import logging
import traceback
import json
from collections import defaultdict
from django.views import View
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Max, Min, Avg, Count, F, Q, Sum, FloatField, ExpressionWrapper, Case, When, Value, IntegerField
from django.db.models.functions import TruncDate
from datetime import timedelta

from .models import LoginActivityLog, QLearningState, UserLearningState
from quizzes.models import AttemptLog, Question
from accounts.models import CustomUser, StudentProfile

logger = logging.getLogger(__name__)

class LoginActivityAPI(View):
    def get(self, request, *args, **kwargs):
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        # Get total count and paginated activities
        total_activities = LoginActivityLog.objects.count()
        activities = LoginActivityLog.objects.select_related('user').order_by('-login_timestamp')[start:end]
        
        # Serialize the data
        data = [{
            'username': log.user.username,
            'login_time': log.login_timestamp.isoformat(),
            'logout_time': log.logout_timestamp.isoformat() if log.logout_timestamp else None,
            'duration': log.session_duration_seconds,
            'ip_address': log.ip_address
        } for log in activities]
        
        return JsonResponse({
            'activities': data,
            'total': total_activities,
            'page': page,
            'page_size': page_size,
            'has_next': end < total_activities
        })

def check_new_logins(request):
    from django.utils.dateparse import parse_datetime
    import json
    
    # Get the timestamp of the last update from the request
    last_update_str = request.GET.get('last_update')
    last_update = None
    
    if last_update_str:
        try:
            last_update = parse_datetime(last_update_str)
        except (ValueError, TypeError):
            pass
    
    # Query for login activities
    if last_update:
        activities = LoginActivityLog.objects.filter(
            login_timestamp__gt=last_update
        ).order_by('-login_timestamp')
    else:
        # If no last_update, get the 10 most recent activities
        activities = LoginActivityLog.objects.all().order_by('-login_timestamp')[:10]
    
    # Get the latest timestamp for the response
    latest_timestamp = timezone.now()
    if activities.exists():
        latest_timestamp = activities[0].login_timestamp
    
    # Serialize the data
    data = [{
        'username': log.user.username,
        'login_time': log.login_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'logout_time': log.logout_timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.logout_timestamp else None,
        'duration': log.session_duration_seconds,
        'ip_address': log.ip_address or 'N/A'
    } for log in activities]
    
    return JsonResponse({
        'activities': data,
        'last_update': latest_timestamp.isoformat(),
        'count': len(data),
        'status': 'success'
    })


class QLearningMetricsAPI(View):
    """API for Q-Learning metrics and analytics"""
    
    def get(self, request, *args, **kwargs):
        try:
            logger.info("QLearningMetricsAPI called")
            
            # Get time range from query params (default to 7 days)
            try:
                days = int(request.GET.get('days', 7))
                end_date = timezone.now()
                start_date = end_date - timedelta(days=days)
                logger.info(f"Fetching metrics for {days} days, from {start_date} to {end_date}")
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid days parameter: {request.GET.get('days')}")
                return JsonResponse({'error': 'Invalid days parameter'}, status=400)
            
            try:
                # Get all metrics
                metrics = {
                    'user_engagement': self.get_user_engagement_metrics(start_date, end_date),
                    'success_rates': self.get_success_rate_metrics(start_date, end_date) or [],
                    'adaptation': self.get_adaptation_metrics(start_date, end_date) or {},
                    'q_learning': self.get_q_learning_metrics(start_date, end_date),
                    'user_states': self.get_user_state_analysis(start_date, end_date),
                    'action_distribution': self.get_action_distribution(start_date, end_date),
                    'reward_analysis': self.get_reward_analysis(start_date, end_date),
                    'qtable_analysis': self.get_qtable_analysis(start_date, end_date),
                    'validation': self.get_validation_feedback(start_date, end_date)
                }
                
                logger.info("Successfully generated metrics")
                return JsonResponse(metrics)
                
            except Exception as e:
                logger.error(f"Error generating metrics: {str(e)}")
                logger.error(traceback.format_exc())
                return JsonResponse({'error': str(e)}, status=500)
                
        except Exception as e:
            logger.critical(f"Unexpected error in QLearningMetricsAPI: {str(e)}")
            logger.critical(traceback.format_exc())
            return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

    def get_q_learning_metrics(self, start_date, end_date):
        """Get Q-Learning specific metrics"""
        try:
            # Get Q-Table state distribution
            state_distribution = list(QLearningState.objects.values('state_type').annotate(
                count=Count('id')
            ).order_by('-count'))
            
            # Get learning progress over time with state_type mapped to numeric values
            learning_progress = list(UserLearningState.objects.filter(
                last_visited__range=(start_date, end_date)
            ).annotate(
                date=TruncDate('last_visited'),
                # Map state_type to numeric values for averaging
                state_numeric=Case(
                    When(state__state_type='initial', then=Value(1)),
                    When(state__state_type='struggling', then=Value(2)),
                    When(state__state_type='learning', then=Value(3)),
                    When(state__state_type='mastered', then=Value(4)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).values('date').annotate(
                avg_state=Avg('state_numeric'),
                count=Count('id')
            ).order_by('date'))
            
            return {
                'state_distribution': state_distribution or [],
                'learning_progress': learning_progress or []
            }
            
        except Exception as e:
            logger.error(f"Error in get_q_learning_metrics: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'state_distribution': [],
                'learning_progress': []
            }
    
    def get_user_engagement_metrics(self, start_date, end_date):
        """Get user engagement metrics"""
        try:
            # Daily active users
            daily_active = list(LoginActivityLog.objects.filter(
                login_timestamp__range=(start_date, end_date)
            ).annotate(
                date=TruncDate('login_timestamp')
            ).values('date').annotate(
                count=Count('user_id', distinct=True)
            ).order_by('date'))
            
            # Format dates to strings for JSON serialization
            for item in daily_active:
                if 'date' in item and item['date']:
                    item['date'] = item['date'].strftime('%Y-%m-%d')
            
            # Session duration
            session_duration = LoginActivityLog.objects.filter(
                login_timestamp__range=(start_date, end_date),
                session_duration_seconds__isnull=False
            ).aggregate(
                avg_duration=Avg('session_duration_seconds') or 0,
                total_sessions=Count('id')
            )
            
            return {
                'daily_active_users': daily_active or [],
                'session_duration': session_duration or {}
            }
            
        except Exception as e:
            logger.error(f"Error in get_user_engagement_metrics: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'daily_active_users': [],
                'session_duration': {}
            }
    
    def get_success_rate_metrics(self, start_date, end_date):
        """Get success rate metrics by difficulty level"""
        from django.db.models import FloatField
        from django.db.models.functions import Cast
        
        attempts = AttemptLog.objects.filter(
            created_at__range=(start_date, end_date)
        ).values('question__difficulty').annotate(
            total=Count('id'),
            correct=Count('id', filter=Q(is_correct=True)),
            success_rate=ExpressionWrapper(
                Cast(Count('id', filter=Q(is_correct=True)), FloatField()) * 100.0 / 
                Cast(Count('id'), FloatField()),
                output_field=FloatField()
            )
        ).order_by('question__difficulty')
        
        # Convert Decimal to float for JSON serialization
        result = []
        for item in attempts:
            item_dict = {
                'question__difficulty': item['question__difficulty'],
                'total': item['total'],
                'correct': item['correct'],
                'success_rate': float(item['success_rate']) if item['success_rate'] is not None else 0.0
            }
            result.append(item_dict)
            
        return result
    
    def get_adaptation_metrics(self, start_date, end_date):
        """Get adaptation effectiveness metrics"""
        try:
            # Get state transitions
            transitions = list(UserLearningState.objects.filter(
                last_visited__range=(start_date, end_date)
            ).order_by('user', 'last_visited'))
            
            # Calculate state transition matrix
            transition_matrix = defaultdict(lambda: defaultdict(int))
            for i in range(len(transitions) - 1):
                if transitions[i].user_id == transitions[i+1].user_id:
                    from_state = getattr(transitions[i].state, 'state_type', 'unknown')
                    to_state = getattr(transitions[i+1].state, 'state_type', 'unknown')
                    if from_state and to_state:  # Hanya proses jika kedua state valid
                        transition_matrix[from_state][to_state] += 1
            
            # Convert to serializable format
            transition_data = [
                {'from': k1, 'to': k2, 'count': v2} 
                for k1, v1 in transition_matrix.items()
                for k2, v2 in v1.items()
            ]
            
            return {
                'transitions': transition_data or [],
                'total_transitions': len(transition_data)
            }
            
        except Exception as e:
            logger.error(f"Error in get_adaptation_metrics: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'transitions': [],
                'total_transitions': 0
            }
    
    def get_system_health_metrics(self):
        """Get system health metrics"""
        try:
            # Get recent login activities (last 24 hours)
            recent_activities = list(LoginActivityLog.objects.filter(
                login_timestamp__gte=timezone.now() - timedelta(hours=24)
            ).order_by('-login_timestamp')[:10])
            
            # Get system load (requests per minute for the last hour)
            from django.db.models.functions import TruncMinute
            one_hour_ago = timezone.now() - timedelta(hours=1)
            request_stats = list(LoginActivityLog.objects.filter(
                login_timestamp__gte=one_hour_ago
            ).annotate(
                minute=TruncMinute('login_timestamp')
            ).values('minute').annotate(
                count=Count('id')
            ).order_by('minute'))
            
            # Format dates for JSON serialization
            for stat in request_stats:
                if 'minute' in stat and stat['minute']:
                    stat['minute'] = stat['minute'].strftime('%Y-%m-%dT%H:%M:%S')
            
            return {
                'recent_activities': list(recent_activities.values('user__username', 'login_timestamp')),
                'request_stats': request_stats or [],
                'server_time': timezone.now().isoformat(),
                'status': 'operational'
            }
            
        except Exception as e:
            logger.error(f"Error in get_system_health_metrics: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'recent_activities': [],
                'request_stats': [],
                'server_time': timezone.now().isoformat(),
                'status': 'error'
            }
            
    def get_user_state_analysis(self, start_date, end_date):
        """Get user state distribution and transitions"""
        from collections import defaultdict
        
        try:
            # Get current state distribution
            states = UserLearningState.objects.filter(
                is_current=True,
                last_visited__range=(start_date, end_date)
            ).values(
                'state__state_type'
            ).annotate(
                count=Count('id')
            ).order_by('-count')

            # Get state transitions
            transitions = UserLearningState.objects.filter(
                last_visited__range=(start_date, end_date)
            ).select_related('state').order_by('user', 'last_visited')

            transition_matrix = defaultdict(lambda: defaultdict(int))
            for i in range(len(transitions) - 1):
                if (transitions[i].user_id == transitions[i+1].user_id and 
                    transitions[i].state_id != transitions[i+1].state_id):
                    from_state = transitions[i].state.state_type if transitions[i].state else 'unknown'
                    to_state = transitions[i+1].state.state_type if transitions[i+1].state else 'unknown'
                    transition_matrix[from_state][to_state] += 1

            return {
                'state_distribution': list(states),
                'transition_matrix': [
                    {'from': k1, 'to': k2, 'count': v2} 
                    for k1, v1 in transition_matrix.items()
                    for k2, v2 in v1.items()
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in get_user_state_analysis: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'state_distribution': [],
                'transition_matrix': []
            }
            
    def get_action_distribution(self, start_date, end_date):
        """Get distribution of actions taken by the Q-learning agent"""
        try:
            from qlearning.models import QLearningDecisionLog
            
            actions = QLearningDecisionLog.objects.filter(
                timestamp__range=(start_date, end_date)
            ).values(
                'action_chosen'
            ).annotate(
                count=Count('id')
            ).order_by('-count')

            total_actions = sum(a['count'] for a in actions)
            exploration_count = QLearningDecisionLog.objects.filter(
                timestamp__range=(start_date, end_date),
                decision_type='exploration'
            ).count()

            return {
                'actions': list(actions),
                'exploration_rate': (exploration_count / total_actions) if total_actions > 0 else 0,
                'total_actions': total_actions
            }
            
        except Exception as e:
            logger.error(f"Error in get_action_distribution: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'actions': [],
                'exploration_rate': 0,
                'total_actions': 0
            }
            
    def get_reward_analysis(self, start_date, end_date):
        """Get reward distribution and statistics"""
        try:
            from qlearning.models import QLearningLog
            
            # Ensure we have the required imports
            from django.db.models import Max, Min, Avg, Count
            
            rewards = QLearningLog.objects.filter(
                timestamp__range=(start_date, end_date)
            ).aggregate(
                avg_reward=Avg('reward'),
                max_reward=Max('reward'),
                min_reward=Min('reward'),
                total_rewards=Count('id')
            )

            reward_distribution = QLearningLog.objects.filter(
                timestamp__range=(start_date, end_date)
            ).values(
                'reward'
            ).annotate(
                count=Count('id')
            ).order_by('reward')

            return {
                'stats': {k: float(v) if v is not None else 0 for k, v in rewards.items()},
                'distribution': list(reward_distribution)
            }
            
        except Exception as e:
            logger.error(f"Error in get_reward_analysis: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'stats': {
                    'avg_reward': 0,
                    'max_reward': 0,
                    'min_reward': 0,
                    'total_rewards': 0
                },
                'distribution': []
            }
            
    def get_qtable_analysis(self, start_date, end_date):
        """Get Q-Table analysis and state-action values"""
        try:
            from qlearning.models import QTableEntry
            from django.db.models import Max, Min, Avg, Count
            
            # Get Q-value statistics
            q_stats = QTableEntry.objects.filter(
                updated_at__range=(start_date, end_date)
            ).aggregate(
                avg_q=Avg('q_value'),
                max_q=Max('q_value'),
                min_q=Min('q_value'),
                total_entries=Count('id')
            )

            # Get top state-action pairs by Q-value
            top_actions = list(QTableEntry.objects.filter(
                updated_at__range=(start_date, end_date)
            ).order_by('-q_value')[:10].values(
                'state_hash', 'action', 'q_value'
            ))

            return {
                'stats': {k: float(v) if v is not None else 0 for k, v in q_stats.items()},
                'top_actions': top_actions
            }
            
        except Exception as e:
            logger.error(f"Error in get_qtable_analysis: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'stats': {
                    'avg_q': 0,
                    'max_q': 0,
                    'min_q': 0,
                    'total_entries': 0
                },
                'top_actions': []
            }
            
    def get_validation_feedback(self, start_date, end_date):
        """Get expert validation and user feedback"""
        try:
            from qlearning.models import UserSurveyResponse
            
            # Calculate average satisfaction ratings
            satisfaction = UserSurveyResponse.objects.filter(
                timestamp__range=(start_date, end_date)
            ).aggregate(
                avg_satisfaction=Avg('satisfaction_rating'),
                avg_difficulty=Avg('difficulty_rating'),
                total_responses=Count('id')
            )

            # Get feedback distribution
            feedback_dist = UserSurveyResponse.objects.filter(
                timestamp__range=(start_date, end_date)
            ).values(
                'satisfaction_rating'
            ).annotate(
                count=Count('id')
            ).order_by('satisfaction_rating')

            return {
                'satisfaction': {k: float(v) if v is not None else 0 for k, v in satisfaction.items()},
                'feedback_distribution': list(feedback_dist)
            }
            
        except Exception as e:
            logger.error(f"Error in get_validation_feedback: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'satisfaction': {
                    'avg_satisfaction': 0,
                    'avg_difficulty': 0,
                    'total_responses': 0
                },
                'feedback_distribution': []
            }
