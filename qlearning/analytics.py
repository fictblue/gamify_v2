import json
import uuid
from datetime import timedelta
from typing import Dict, List, Tuple
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum, Max, Min
from django.contrib.auth import get_user_model

from accounts.models import StudentProfile
from quizzes.models import Question, AttemptLog
from qlearning.models import (
    UserEngagementLog, SuccessRateLog, ResponseToAdaptationLog,
    QLearningPerformanceLog, LevelTransitionLog, RewardIncentivesLog, GlobalSystemLog,
    QTableEntry, QLearningLog
)

User = get_user_model()


class AnalyticsService:
    """
    Comprehensive analytics service for the gamification system.

    Handles logging and analysis for:
    - User engagement metrics
    - Success rates and accuracy
    - Response to system adaptations
    - Q-Learning performance
    - Level transitions
    - Reward effectiveness
    - Global system statistics
    """

    @staticmethod
    def log_user_engagement(
        user,
        session_type: str,
        duration_seconds: int,
        questions_attempted: int = 0,
        hints_used: int = 0,
        gamification_interactions: int = 0,
        metadata: dict = None
    ):
        """Log user engagement session"""
        if metadata is None:
            metadata = {}

        session_id = str(uuid.uuid4())[:8]

        UserEngagementLog.objects.create(
            user=user,
            session_type=session_type,
            session_id=session_id,
            duration_seconds=duration_seconds,
            questions_attempted=questions_attempted,
            hints_used=hints_used,
            gamification_interactions=gamification_interactions,
            metadata=metadata
        )

    @staticmethod
    def log_success_rate(user, difficulty: str, time_window_days: int = 7):
        """Log success rate for a user in a specific difficulty"""
        from django.utils import timezone
        from datetime import timedelta

        end_time = timezone.now()
        start_time = end_time - timedelta(days=time_window_days)

        attempts = AttemptLog.objects.filter(
            user=user,
            question__difficulty=difficulty,
            created_at__gte=start_time,
            created_at__lte=end_time
        )

        total_attempts = attempts.count()
        if total_attempts == 0:
            return  # No data to log

        correct_attempts = attempts.filter(is_correct=True).count()
        average_time = attempts.aggregate(Avg('time_spent'))['time_spent__avg'] or 0
        accuracy = (correct_attempts / total_attempts) * 100

        # Convert datetime objects to strings for JSON serialization
        attempts_detail = []
        for attempt in attempts:
            attempt_dict = {
                'id': attempt.id,
                'is_correct': attempt.is_correct,
                'time_spent': attempt.time_spent,
                'difficulty': attempt.question.difficulty,
                'created_at': attempt.created_at.strftime('%Y-%m-%d %H:%M:%S') if attempt.created_at else None
            }
            attempts_detail.append(attempt_dict)

        SuccessRateLog.objects.create(
            user=user,
            difficulty=difficulty,
            total_attempts=total_attempts,
            correct_attempts=correct_attempts,
            average_time_spent=average_time,
            accuracy_percentage=accuracy,
            time_window_start=start_time,
            time_window_end=end_time,
            metadata={
                'attempts_detail': attempts_detail
            }
        )

    @staticmethod
    def log_adaptation_response(
        user,
        adaptation_type: str,
        old_state: dict,
        new_state: dict,
        adaptation_details: dict,
        first_attempt_after: dict = None
    ):
        """Log user response to system adaptation"""
        ResponseToAdaptationLog.objects.create(
            user=user,
            adaptation_type=adaptation_type,
            old_state=old_state,
            new_state=new_state,
            adaptation_details=adaptation_details,
            first_attempt_after=first_attempt_after,
            hint_usage_change=0.0,  # TODO: Calculate from actual data
            session_duration_change=0.0  # TODO: Calculate from actual data
        )

    @staticmethod
    def log_qlearning_performance(user):
        """Log Q-Learning performance metrics"""
        qtable_entries = QTableEntry.objects.filter(user=user)
        qlearning_logs = QLearningLog.objects.filter(user=user)

        if not qtable_entries:
            return  # No data to log

        # Calculate action distribution
        action_counts = {}
        for entry in qtable_entries:
            action_counts[entry.action] = action_counts.get(entry.action, 0) + 1

        total_actions = sum(action_counts.values())
        action_distribution = {
            action: count / total_actions for action, count in action_counts.items()
        }

        # Calculate optimal action frequency
        optimal_actions = 0
        for log in qlearning_logs:
            # Find the action with highest Q-value for this state
            best_action = max(
                (entry.action for entry in qtable_entries.filter(state_hash=log.state_hash)),
                key=lambda a: next(
                    (e.q_value for e in qtable_entries.filter(state_hash=log.state_hash, action=a)),
                    0
                )
            )
            if log.action == best_action:
                optimal_actions += 1

        optimal_frequency = optimal_actions / len(qlearning_logs) if qlearning_logs else 0

        # Calculate average Q-value
        avg_q_value = qtable_entries.aggregate(Avg('q_value'))['q_value__avg'] or 0

        QLearningPerformanceLog.objects.create(
            user=user,
            state_hash='global',  # Global snapshot
            action_distribution=action_distribution,
            optimal_action_frequency=optimal_frequency,
            average_q_value=avg_q_value,
            q_table_size=qtable_entries.count(),
            learning_progress=0.0,  # TODO: Calculate learning progress
            snapshot_interval=len(qlearning_logs),
            metadata={
                'total_qlogs': len(qlearning_logs),
                'qtable_summary': {
                    'total_entries': qtable_entries.count(),
                    'avg_q_value': avg_q_value,
                    'max_q_value': qtable_entries.aggregate(max_q=Max('q_value'))['max_q'],
                    'min_q_value': qtable_entries.aggregate(min_q=Min('q_value'))['min_q']
                }
            }
        )

    @staticmethod
    def log_level_transition(
        user,
        transition_type: str,
        old_level: str,
        new_level: str,
        transition_condition: dict,
        performance_metrics: dict = None
    ):
        """Log level transition event"""
        if performance_metrics is None:
            performance_metrics = {}

        LevelTransitionLog.objects.create(
            user=user,
            transition_type=transition_type,
            old_level=old_level,
            new_level=new_level,
            transition_condition=transition_condition,
            performance_metrics=performance_metrics
        )

    @staticmethod
    def log_reward_incentive(
        user,
        reward_type: str,
        reward_value: float,
        trigger_condition: dict,
        user_reaction: dict = None,
        session_continuation: bool = True
    ):
        """Log reward and incentive event"""
        if user_reaction is None:
            user_reaction = {}

        RewardIncentivesLog.objects.create(
            user=user,
            reward_type=reward_type,
            reward_value=reward_value,
            trigger_condition=trigger_condition,
            user_reaction=user_reaction,
            session_continuation=session_continuation
        )

    @staticmethod
    def log_global_system_metrics(metric_type: str, time_window: str = 'daily'):
        """Log global system statistics"""
        from django.db.models import Max, Min

        if metric_type == 'accuracy_global':
            # Global accuracy across all users and difficulties
            all_attempts = AttemptLog.objects.all()
            total_attempts = all_attempts.count()
            correct_attempts = all_attempts.filter(is_correct=True).count()
            global_accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0

            # Accuracy per difficulty
            difficulty_accuracy = {}
            for difficulty in ['easy', 'medium', 'hard']:
                diff_attempts = all_attempts.filter(question__difficulty=difficulty)
                diff_total = diff_attempts.count()
                diff_correct = diff_attempts.filter(is_correct=True).count()
                difficulty_accuracy[difficulty] = {
                    'total': diff_total,
                    'correct': diff_correct,
                    'accuracy': (diff_correct / diff_total * 100) if diff_total > 0 else 0
                }

            metric_data = {
                'global_accuracy': global_accuracy,
                'total_attempts': total_attempts,
                'correct_attempts': correct_attempts,
                'difficulty_breakdown': difficulty_accuracy
            }

        elif metric_type == 'engagement_daily':
            # Daily engagement metrics
            today = timezone.now().date()
            daily_attempts = AttemptLog.objects.filter(created_at__date=today)
            daily_users = User.objects.filter(
                role='student',
                attempt_logs__created_at__date=today
            ).distinct()

            metric_data = {
                'date': today.strftime('%Y-%m-%d'),
                'total_attempts': daily_attempts.count(),
                'unique_users': daily_users.count(),
                'avg_attempts_per_user': daily_attempts.count() / daily_users.count() if daily_users.count() > 0 else 0
            }

        elif metric_type == 'hint_distribution':
            # Hint usage distribution
            hint_attempts = AttemptLog.objects.exclude(hint_given__isnull=True)
            total_with_hints = hint_attempts.count()
            total_without_hints = AttemptLog.objects.filter(hint_given__isnull=True).count()

            # Hint types distribution
            hint_types = {}
            for attempt in hint_attempts:
                if attempt.hint_given:
                    hint_type = attempt.hint_given[:20]  # First 20 chars as hint type
                    hint_types[hint_type] = hint_types.get(hint_type, 0) + 1

            metric_data = {
                'total_attempts': total_with_hints + total_without_hints,
                'attempts_with_hints': total_with_hints,
                'attempts_without_hints': total_without_hints,
                'hint_usage_rate': (total_with_hints / (total_with_hints + total_without_hints) * 100) if (total_with_hints + total_without_hints) > 0 else 0,
                'hint_types': hint_types
            }

        elif metric_type == 'qlearning_trend':
            # Q-Learning trends
            recent_qlogs = QLearningLog.objects.all().order_by('-timestamp')[:100]  # Last 100 updates

            avg_q_value = recent_qlogs.aggregate(Avg('q_value_after'))['q_value_after__avg'] or 0
            avg_reward = recent_qlogs.aggregate(Avg('reward'))['reward__avg'] or 0

            # Action distribution
            action_counts = {}
            for log in recent_qlogs:
                action_counts[log.action] = action_counts.get(log.action, 0) + 1

            metric_data = {
                'total_q_updates': len(recent_qlogs),
                'average_q_value': avg_q_value,
                'average_reward': avg_reward,
                'action_distribution': action_counts,
                'unique_states': QTableEntry.objects.values('state_hash').distinct().count(),
                'total_q_entries': QTableEntry.objects.count()
            }

        else:
            metric_data = {}

        GlobalSystemLog.objects.create(
            metric_type=metric_type,
            metric_data=metric_data,
            time_window=time_window
        )

    @staticmethod
    def get_comprehensive_dashboard_data():
        """Get comprehensive data for the admin dashboard"""
        from django.db.models import Max, Min

        # User engagement metrics
        recent_sessions = UserEngagementLog.objects.all().order_by('-timestamp')[:50]

        engagement_summary = {
            'total_sessions': recent_sessions.count(),
            'avg_session_duration': recent_sessions.aggregate(Avg('duration_seconds'))['duration_seconds__avg'] or 0,
            'total_questions_attempted': recent_sessions.aggregate(Sum('questions_attempted'))['questions_attempted__sum'] or 0,
            'total_hints_used': recent_sessions.aggregate(Sum('hints_used'))['hints_used__sum'] or 0,
            'session_types': {}
        }

        for session in recent_sessions:
            engagement_summary['session_types'][session.session_type] = \
                engagement_summary['session_types'].get(session.session_type, 0) + 1

        # Success rate metrics
        success_logs = SuccessRateLog.objects.all().order_by('-time_window_end')[:20]

        success_summary = {
            'total_logs': success_logs.count(),
            'overall_accuracy': success_logs.aggregate(Avg('accuracy_percentage'))['accuracy_percentage__avg'] or 0,
            'difficulty_breakdown': {}
        }

        # Get success rates for all difficulties
        for difficulty in ['easy', 'medium', 'hard']:
            diff_logs = SuccessRateLog.objects.filter(difficulty=difficulty).order_by('-time_window_end')[:10]

            if diff_logs.exists():
                total_accuracy = sum(log.accuracy_percentage for log in diff_logs)
                count = diff_logs.count()
                avg_accuracy = total_accuracy / count

                success_summary['difficulty_breakdown'][difficulty] = {
                    'average_accuracy': avg_accuracy,
                    'count': count
                }
            else:
                # Calculate from AttemptLog if no SuccessRateLog exists
                attempts = AttemptLog.objects.filter(question__difficulty=difficulty)
                if attempts.exists():
                    correct_attempts = attempts.filter(is_correct=True).count()
                    total_attempts = attempts.count()
                    accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0

                    success_summary['difficulty_breakdown'][difficulty] = {
                        'average_accuracy': accuracy,
                        'count': 1  # Direct calculation
                    }
                else:
                    success_summary['difficulty_breakdown'][difficulty] = {
                        'average_accuracy': 0,
                        'count': 0
                    }

        # Add easy access properties for template
        success_summary['easy_accuracy'] = success_summary['difficulty_breakdown'].get('easy', {}).get('average_accuracy', 0)
        success_summary['medium_accuracy'] = success_summary['difficulty_breakdown'].get('medium', {}).get('average_accuracy', 0)
        success_summary['hard_accuracy'] = success_summary['difficulty_breakdown'].get('hard', {}).get('average_accuracy', 0)

        # Level transition metrics
        level_transitions = LevelTransitionLog.objects.all().order_by('-timestamp')[:30]

        transition_summary = {
            'total_transitions': level_transitions.count(),
            'level_up_count': LevelTransitionLog.objects.filter(transition_type='level_up_manual').count(),
            'level_down_count': LevelTransitionLog.objects.filter(transition_type='level_down_auto').count(),
            'transition_types': {}
        }

        for transition in level_transitions:
            trans_key = f"{transition.old_level}→{transition.new_level}"
            transition_summary['transition_types'][trans_key] = \
                transition_summary['transition_types'].get(trans_key, 0) + 1

        # Reward effectiveness metrics
        reward_logs = RewardIncentivesLog.objects.all().order_by('-timestamp')[:30]

        reward_summary = {
            'total_rewards': reward_logs.count(),
            'avg_reward_value': reward_logs.aggregate(Avg('reward_value'))['reward_value__avg'] or 0,
            'session_continuation_rate': (
                RewardIncentivesLog.objects.filter(session_continuation=True).count() / RewardIncentivesLog.objects.count() * 100
            ) if RewardIncentivesLog.objects.count() > 0 else 0,
            'reward_types': {}
        }

        for reward in reward_logs:
            reward_summary['reward_types'][reward.reward_type] = \
                reward_summary['reward_types'].get(reward.reward_type, 0) + 1

        # Q-Learning performance metrics
        qlearning_logs = QLearningLog.objects.all().order_by('-timestamp')[:50]

        qlearning_summary = {
            'total_updates': qlearning_logs.count(),
            'avg_q_value': 0,
            'avg_reward': 0,
            'unique_users': QLearningLog.objects.values('user').distinct().count(),
            'action_distribution': {}
        }

        if qlearning_logs.exists():
            # Calculate average Q-value from QTableEntry (more accurate)
            qtable_entries = QTableEntry.objects.all()
            if qtable_entries.exists():
                qlearning_summary['avg_q_value'] = qtable_entries.aggregate(Avg('q_value'))['q_value__avg'] or 0
            else:
                qlearning_summary['avg_q_value'] = 0

            # Calculate average reward from QLearningLog
            qlearning_summary['avg_reward'] = qlearning_logs.aggregate(Avg('reward'))['reward__avg'] or 0

            # Action distribution from QLearningLog
            for log in qlearning_logs:
                qlearning_summary['action_distribution'][log.action] = \
                    qlearning_summary['action_distribution'].get(log.action, 0) + 1

        # Global system metrics
        global_logs = GlobalSystemLog.objects.all().order_by('-timestamp')[:10]

        global_summary = {
            'total_metrics': global_logs.count(),
            'latest_accuracy': 0,
            'latest_engagement': 0
        }

        for log in global_logs:
            if log.metric_type == 'accuracy_global':
                global_summary['latest_accuracy'] = log.metric_data.get('global_accuracy', 0)
            elif log.metric_type == 'engagement_daily':
                global_summary['latest_engagement'] = log.metric_data.get('unique_users', 0)

        return {
            'engagement': engagement_summary,
            'success': success_summary,
            'transitions': transition_summary,
            'rewards': reward_summary,
            'qlearning': qlearning_summary,
            'global': global_summary,
            'last_updated': timezone.now()
        }

    @staticmethod
    def export_logs_to_csv(log_type: str, filename: str = None):
        """Export logs to CSV format"""
        import csv
        from django.http import HttpResponse

        if log_type == 'engagement':
            logs = UserEngagementLog.objects.select_related('user').all()
            fieldnames = ['user', 'session_type', 'session_id', 'duration_seconds',
                         'questions_attempted', 'hints_used', 'gamification_interactions', 'timestamp']

        elif log_type == 'success':
            logs = SuccessRateLog.objects.select_related('user').all()
            fieldnames = ['user', 'difficulty', 'total_attempts', 'correct_attempts',
                         'accuracy_percentage', 'average_time_spent', 'time_window_start', 'time_window_end']

        elif log_type == 'transitions':
            logs = LevelTransitionLog.objects.select_related('user').all()
            fieldnames = ['user', 'transition_type', 'old_level', 'new_level', 'timestamp']

        elif log_type == 'rewards':
            logs = RewardIncentivesLog.objects.select_related('user').all()
            fieldnames = ['user', 'reward_type', 'reward_value', 'session_continuation', 'timestamp']

        elif log_type == 'qlearning':
            logs = QLearningLog.objects.select_related('user').all()
            fieldnames = ['user', 'state_hash', 'action', 'reward', 'q_value_before', 'q_value_after', 'timestamp']

        elif log_type == 'qlearning_performance':
            logs = QLearningPerformanceLog.objects.select_related('user').all()
            fieldnames = ['user', 'state_hash', 'optimal_action_frequency', 'average_q_value', 'q_table_size', 'timestamp']

        elif log_type == 'global':
            logs = GlobalSystemLog.objects.all()
            fieldnames = ['metric_type', 'time_window', 'timestamp', 'metric_data']

        else:
            raise ValueError(f"Unknown log type: {log_type}")

        if filename is None:
            filename = f"{log_type}_logs_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"

        # Create CSV content
        output = []
        for log in logs:
            row = {}
            for field in fieldnames:
                value = getattr(log, field, '')
                if isinstance(value, dict):
                    row[field] = json.dumps(value)
                else:
                    row[field] = str(value)
            output.append(row)

        return output, fieldnames, filename
