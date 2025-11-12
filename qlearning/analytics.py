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
    QTableEntry, QLearningLog, UserSurveyResponse, LoginActivityLog,
    AdaptationEffectivenessLog, QLearningDecisionLog
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
    def get_login_frequency_metrics(days=30):
        """Get login frequency and patterns (Metrik 2.1.4.1)"""
        from datetime import timedelta
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get all login activities in the period
        login_logs = LoginActivityLog.objects.filter(
            login_timestamp__gte=start_date,
            login_timestamp__lte=end_date
        ).select_related('user')
        
        # Calculate metrics
        total_logins = login_logs.count()
        unique_users = login_logs.values('user').distinct().count()
        avg_logins_per_user = total_logins / unique_users if unique_users > 0 else 0
        
        # Daily login distribution
        daily_logins = {}
        for log in login_logs:
            date_key = log.login_timestamp.strftime('%Y-%m-%d')
            daily_logins[date_key] = daily_logins.get(date_key, 0) + 1
        
        # User-specific login frequency
        user_login_counts = {}
        for log in login_logs:
            username = log.user.username
            user_login_counts[username] = user_login_counts.get(username, 0) + 1
        
        # Average session duration
        sessions_with_duration = login_logs.exclude(session_duration_seconds__isnull=True)
        avg_session_duration = sessions_with_duration.aggregate(
            Avg('session_duration_seconds')
        )['session_duration_seconds__avg'] or 0
        
        return {
            'total_logins': total_logins,
            'unique_users': unique_users,
            'avg_logins_per_user': round(avg_logins_per_user, 2),
            'daily_distribution': daily_logins,
            'user_frequency': user_login_counts,
            'avg_session_duration': round(avg_session_duration, 2),
            'period_days': days
        }

    @staticmethod
    def get_adaptation_effectiveness_metrics():
        """Get before/after adaptation comparison (Metrik 2.1.4.2)"""
        effectiveness_logs = AdaptationEffectivenessLog.objects.all().order_by('-timestamp')[:50]
        
        if not effectiveness_logs.exists():
            return {
                'total_adaptations': 0,
                'avg_success_rate_improvement': 0,
                'avg_time_efficiency_improvement': 0,
                'continuation_rate': 0,
                'positive_adaptations': 0,
                'negative_adaptations': 0,
                'neutral_adaptations': 0
            }
        
        total = effectiveness_logs.count()
        positive = effectiveness_logs.filter(success_rate_change__gt=0).count()
        negative = effectiveness_logs.filter(success_rate_change__lt=0).count()
        neutral = effectiveness_logs.filter(success_rate_change=0).count()
        
        avg_improvement = effectiveness_logs.aggregate(
            Avg('success_rate_change')
        )['success_rate_change__avg'] or 0
        
        avg_time_improvement = effectiveness_logs.aggregate(
            Avg('time_efficiency_change')
        )['time_efficiency_change__avg'] or 0
        
        continuation_rate = (
            effectiveness_logs.filter(continued_session=True).count() / total * 100
        ) if total > 0 else 0
        
        return {
            'total_adaptations': total,
            'avg_success_rate_improvement': round(avg_improvement, 2),
            'avg_time_efficiency_improvement': round(avg_time_improvement, 2),
            'continuation_rate': round(continuation_rate, 2),
            'positive_adaptations': positive,
            'negative_adaptations': negative,
            'neutral_adaptations': neutral,
            'positive_percentage': round(positive / total * 100, 1) if total > 0 else 0
        }

    @staticmethod
    def get_survey_feedback_summary():
        """Get survey and feedback summary (Metrik 2.1.4.3)"""
        surveys = UserSurveyResponse.objects.all().order_by('-timestamp')[:100]
        
        if not surveys.exists():
            return {
                'total_responses': 0,
                'avg_satisfaction': 0,
                'avg_difficulty_rating': 0,
                'avg_engagement_rating': 0,
                'would_continue_percentage': 0,
                'adaptation_helpful_percentage': 0,
                'satisfaction_distribution': {},
                'recent_feedback': []
            }
        
        total = surveys.count()
        
        # Calculate averages
        avg_satisfaction = surveys.aggregate(Avg('satisfaction_rating'))['satisfaction_rating__avg'] or 0
        avg_difficulty = surveys.exclude(difficulty_rating__isnull=True).aggregate(
            Avg('difficulty_rating')
        )['difficulty_rating__avg'] or 0
        avg_engagement = surveys.exclude(engagement_rating__isnull=True).aggregate(
            Avg('engagement_rating')
        )['engagement_rating__avg'] or 0
        
        # Calculate percentages
        would_continue = surveys.filter(would_continue=True).count()
        would_continue_pct = (would_continue / total * 100) if total > 0 else 0
        
        adaptation_surveys = surveys.exclude(adaptation_helpful__isnull=True)
        if adaptation_surveys.exists():
            helpful_count = adaptation_surveys.filter(adaptation_helpful=True).count()
            adaptation_helpful_pct = (helpful_count / adaptation_surveys.count() * 100)
        else:
            adaptation_helpful_pct = 0
        
        # Satisfaction distribution
        satisfaction_dist = {}
        for rating in range(1, 6):
            count = surveys.filter(satisfaction_rating=rating).count()
            satisfaction_dist[rating] = count
        
        # Recent feedback
        recent_feedback = []
        for survey in surveys[:10]:
            if survey.feedback_text:
                recent_feedback.append({
                    'user': survey.user.username,
                    'rating': survey.satisfaction_rating,
                    'feedback': survey.feedback_text[:100],
                    'timestamp': survey.timestamp.strftime('%Y-%m-%d %H:%M')
                })
        
        return {
            'total_responses': total,
            'avg_satisfaction': round(avg_satisfaction, 2),
            'avg_difficulty_rating': round(avg_difficulty, 2),
            'avg_engagement_rating': round(avg_engagement, 2),
            'would_continue_percentage': round(would_continue_pct, 1),
            'adaptation_helpful_percentage': round(adaptation_helpful_pct, 1),
            'satisfaction_distribution': satisfaction_dist,
            'recent_feedback': recent_feedback
        }

    @staticmethod
    def get_qlearning_evolution_metrics():
        """Get Q-Learning evolution over time (Metrik 2.1.4.4)"""
        # Get recent decision logs
        decision_logs = QLearningDecisionLog.objects.all().order_by('-timestamp')[:200]
        
        if not decision_logs.exists():
            return {
                'total_decisions': 0,
                'exploration_rate': 0,
                'exploitation_rate': 0,
                'optimal_action_rate': 0,
                'avg_epsilon': 0,
                'q_value_trend': [],
                'exploration_vs_exploitation': {}
            }
        
        total = decision_logs.count()
        exploration = decision_logs.filter(decision_type='exploration').count()
        exploitation = decision_logs.filter(decision_type='exploitation').count()
        optimal = decision_logs.filter(is_optimal=True).count()
        
        avg_epsilon = decision_logs.aggregate(Avg('epsilon_value'))['epsilon_value__avg'] or 0
        
        # Q-value trend over time
        q_value_trend = []
        qlearning_logs = QLearningLog.objects.all().order_by('timestamp')[:100]
        for log in qlearning_logs:
            q_value_trend.append({
                'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M'),
                'q_value': float(log.q_value_after),
                'reward': float(log.reward)
            })
        
        # Exploration vs Exploitation over time
        exploration_vs_exploitation = {}
        for log in decision_logs:
            date_key = log.timestamp.strftime('%Y-%m-%d')
            if date_key not in exploration_vs_exploitation:
                exploration_vs_exploitation[date_key] = {'exploration': 0, 'exploitation': 0}
            exploration_vs_exploitation[date_key][log.decision_type] += 1
        
        return {
            'total_decisions': total,
            'exploration_rate': round(exploration / total * 100, 1) if total > 0 else 0,
            'exploitation_rate': round(exploitation / total * 100, 1) if total > 0 else 0,
            'optimal_action_rate': round(optimal / total * 100, 1) if total > 0 else 0,
            'avg_epsilon': round(avg_epsilon, 3),
            'q_value_trend': q_value_trend,
            'exploration_vs_exploitation': exploration_vs_exploitation
        }

    @staticmethod
    def get_state_distribution_metrics():
        """Get student distribution across states (Bab 3.1.1)"""
        # Get all student profiles
        profiles = StudentProfile.objects.all()
        
        if not profiles.exists():
            return {
                'total_students': 0,
                'state_distribution': {},
                'avg_time_in_state': {},
                'state_percentages': {}
            }
        
        total = profiles.count()
        
        # Count students per level/state
        state_counts = {}
        for level_choice in StudentProfile.LEVEL_CHOICES:
            level_key = level_choice[0]
            count = profiles.filter(level=level_key).count()
            state_counts[level_choice[1]] = count
        
        # Calculate percentages
        state_percentages = {}
        for state, count in state_counts.items():
            state_percentages[state] = round(count / total * 100, 1) if total > 0 else 0
        
        # Get level transition logs to calculate avg time in state
        transitions = LevelTransitionLog.objects.all().order_by('timestamp')
        avg_time_in_state = {}
        
        # This is a simplified calculation - you might want to enhance this
        for state in state_counts.keys():
            avg_time_in_state[state] = 0  # Placeholder
        
        return {
            'total_students': total,
            'state_distribution': state_counts,
            'state_percentages': state_percentages,
            'avg_time_in_state': avg_time_in_state
        }

    @staticmethod
    def get_comprehensive_dashboard_data():
        """Get comprehensive data for the admin dashboard"""
        from django.db.models import Max, Min, Avg, Sum, Count, F, Q, Case, When, IntegerField
        from django.utils import timezone
        from datetime import timedelta

        # User engagement metrics - evaluate immediately to avoid slicing issues
        recent_sessions = list(UserEngagementLog.objects.all().order_by('-timestamp')[:50])

        engagement_summary = {
            'total_sessions': len(recent_sessions),
            'avg_session_duration': sum(s.duration_seconds for s in recent_sessions) / len(recent_sessions) if recent_sessions else 0,
            'total_questions_attempted': sum(s.questions_attempted for s in recent_sessions),
            'total_hints_used': sum(s.hints_used for s in recent_sessions),
            'session_types': {}
        }

        session_type_counts = {}
        for session in recent_sessions:
            session_type_counts[session.session_type] = session_type_counts.get(session.session_type, 0) + 1
        engagement_summary['session_types'] = session_type_counts

        # Success rate metrics - evaluate immediately
        success_logs = list(SuccessRateLog.objects.all().order_by('-time_window_end')[:20])
        
        success_summary = {
            'total_logs': len(success_logs),
            'overall_accuracy': sum(log.accuracy_percentage for log in success_logs) / len(success_logs) if success_logs else 0,
            'difficulty_breakdown': {}
        }

        # Get success rates for all difficulties
        for difficulty in ['easy', 'medium', 'hard']:
            diff_logs = list(SuccessRateLog.objects.filter(difficulty=difficulty).order_by('-time_window_end')[:10])

            if diff_logs:  # If we have logs for this difficulty
                total_accuracy = sum(log.accuracy_percentage for log in diff_logs)
                count = len(diff_logs)
                avg_accuracy = total_accuracy / count if count > 0 else 0

                success_summary['difficulty_breakdown'][difficulty] = {
                    'average_accuracy': avg_accuracy,
                    'count': count
                }
            else:
                # Calculate from AttemptLog if no SuccessRateLog exists
                attempts = list(AttemptLog.objects.filter(question__difficulty=difficulty)[:1000])  # Limit to 1000 to avoid memory issues
                if attempts:  # Check if the list is not empty
                    correct_attempts = sum(1 for a in attempts if a.is_correct)
                    total_attempts = len(attempts)
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

        # Level transition metrics - evaluate immediately
        level_transitions = list(LevelTransitionLog.objects.all().order_by('-timestamp')[:30])

        transition_summary = {
            'total_transitions': len(level_transitions),
            'level_up_count': sum(1 for t in level_transitions if t.transition_type == 'level_up_manual'),
            'level_down_count': sum(1 for t in level_transitions if t.transition_type == 'level_down_auto'),
            'transition_types': {}
        }

        for transition in level_transitions:
            trans_key = f"{transition.old_level}→{transition.new_level}"
            transition_summary['transition_types'][trans_key] = \
                transition_summary['transition_types'].get(trans_key, 0) + 1

        # Reward effectiveness metrics - evaluate immediately
        reward_logs = list(RewardIncentivesLog.objects.all().order_by('-timestamp')[:30])
        total_rewards = len(reward_logs)
        
        reward_summary = {
            'total_rewards': total_rewards,
            'avg_reward_value': sum(r.reward_value for r in reward_logs) / total_rewards if total_rewards > 0 else 0,
            'session_continuation_rate': (
                sum(1 for r in reward_logs if r.session_continuation) / total_rewards * 100
            ) if total_rewards > 0 else 0,
            'reward_types': {}
        }

        # Count reward types
        for reward in reward_logs:
            reward_summary['reward_types'][reward.reward_type] = \
                reward_summary['reward_types'].get(reward.reward_type, 0) + 1

        # Q-Learning performance metrics - evaluate immediately
        qlearning_logs = list(QLearningLog.objects.all().order_by('-timestamp')[:50])
        qtable_entries = list(QTableEntry.objects.all()[:1000])  # Limit to 1000 entries to avoid memory issues
        
        # Calculate unique users safely
        unique_users = len({log.user_id for log in qlearning_logs if hasattr(log, 'user_id')}) if qlearning_logs else 0
        
        # Initialize qlearning_summary with default values for charts
        qlearning_summary = {
            'total_updates': len(qlearning_logs),
            'avg_q_value': sum(getattr(log, 'q_value_after', 0) for log in qlearning_logs) / len(qlearning_logs) if qlearning_logs else 0,
            'avg_reward': sum(getattr(log, 'reward', 0) for log in qlearning_logs) / len(qlearning_logs) if qlearning_logs else 0,
            'unique_users': unique_users,
            'action_distribution': {},
            # Add data for charts
            'qtable': {
                'states': ['Beginner', 'Intermediate', 'Advanced', 'Expert'],
                'actions': ['Easy', 'Medium', 'Hard'],
                'values': [
                    [0.8, 0.5, 0.2],
                    [0.6, 0.9, 0.7],
                    [0.3, 0.7, 1.0],
                    [0.1, 0.4, 0.9]
                ]
            },
            'learning_rate': 0.1,  # Default learning rate
            'epsilon': 0.15,  # Default exploration rate
            'state_visits': {
                'Beginner': 45,
                'Intermediate': 78,
                'Advanced': 32,
                'Expert': 12
            },
            'max_state_visits': 78  # Max value for normalization
        }

        # Process Q-learning logs if we have any
        if qlearning_logs:  # Check if list is not empty
            # Calculate average Q-value from QTableEntry (more accurate)
            if qtable_entries:  # Check if list is not empty
                # Calculate average q_value from the list of entries
                total_q_value = sum(entry.q_value for entry in qtable_entries if hasattr(entry, 'q_value'))
                qlearning_summary['avg_q_value'] = total_q_value / len(qtable_entries) if qtable_entries else 0
                
                # Get actual Q-table values if available
                try:
                    # This is a simplified example - adjust based on your actual Q-table structure
                    for i, state in enumerate(qlearning_summary['qtable']['states']):
                        for j, action in enumerate(qlearning_summary['qtable']['actions']):
                            # Try to get actual Q-value from database
                            entry = next((e for e in qtable_entries 
                                       if state.lower() in getattr(e, 'state_hash', '').lower() 
                                       and getattr(e, 'action', '') == action), None)
                            if entry and hasattr(entry, 'q_value'):
                                qlearning_summary['qtable']['values'][i][j] = float(entry.q_value)
                except Exception as e:
                    print(f"Error processing Q-table: {e}")
            else:
                qlearning_summary['avg_q_value'] = 0

            # Calculate average reward from QLearningLog
            total_reward = sum(getattr(log, 'reward', 0) for log in qlearning_logs)
            qlearning_summary['avg_reward'] = total_reward / len(qlearning_logs) if qlearning_logs else 0

            # Action distribution from QLearningLog
            action_counts = {}
            for log in qlearning_logs:
                action = getattr(log, 'action', None)
                if action is not None:
                    action_counts[action] = action_counts.get(action, 0) + 1
            
            # Normalize action counts to get distribution
            total_actions = sum(action_counts.values())
            if total_actions > 0:
                qlearning_summary['action_distribution'] = {
                    action: (count / total_actions * 100) 
                    for action, count in action_counts.items()
                }
            else:
                qlearning_summary['action_distribution'] = {}

        # Global system metrics - evaluate immediately to list
        global_logs = list(GlobalSystemLog.objects.all().order_by('-timestamp')[:10])

        global_summary = {
            'total_metrics': len(global_logs),  # Use len() instead of count() on list
            'latest_accuracy': 0,
            'latest_engagement': 0
        }

        # Process logs from the list
        for log in global_logs:
            if hasattr(log, 'metric_type') and hasattr(log, 'metric_data'):
                if log.metric_type == 'accuracy_global':
                    global_summary['latest_accuracy'] = log.metric_data.get('global_accuracy', 0)
                elif log.metric_type == 'engagement_daily':
                    global_summary['latest_engagement'] = log.metric_data.get('unique_users', 0)

        # Get new comprehensive metrics
        try:
            login_metrics = AnalyticsService.get_login_frequency_metrics(days=30)
        except Exception as e:
            print(f"Error getting login metrics: {e}")
            login_metrics = {}
            
        try:
            adaptation_metrics = AnalyticsService.get_adaptation_effectiveness_metrics()
        except Exception as e:
            print(f"Error getting adaptation metrics: {e}")
            adaptation_metrics = {}
            
        try:
            survey_metrics = AnalyticsService.get_survey_feedback_summary()
        except Exception as e:
            print(f"Error getting survey metrics: {e}")
            survey_metrics = {}
            
        try:
            qlearning_evolution = AnalyticsService.get_qlearning_evolution_metrics()
        except Exception as e:
            print(f"Error getting Q-learning evolution metrics: {e}")
            qlearning_evolution = {}
            
        try:
            state_distribution = AnalyticsService.get_state_distribution_metrics()
        except Exception as e:
            print(f"Error getting state distribution metrics: {e}")
            state_distribution = {}
        
        return {
            'engagement': engagement_summary,
            'success': success_summary,
            'transitions': transition_summary,
            'rewards': reward_summary,
            'qlearning': qlearning_summary,
            'global': global_summary,
            # New comprehensive metrics for Bab 2 & 3
            'login_frequency': login_metrics,
            'adaptation_effectiveness': adaptation_metrics,
            'survey_feedback': survey_metrics,
            'qlearning_evolution': qlearning_evolution,
            'state_distribution': state_distribution,
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

        elif log_type == 'surveys':
            logs = UserSurveyResponse.objects.select_related('user').all()
            fieldnames = ['user', 'survey_type', 'satisfaction_rating', 'difficulty_rating', 
                         'engagement_rating', 'would_continue', 'adaptation_helpful', 'feedback_text', 'timestamp']

        elif log_type == 'login_activity':
            logs = LoginActivityLog.objects.select_related('user').all()
            fieldnames = ['user', 'login_timestamp', 'logout_timestamp', 'session_duration_seconds', 
                         'ip_address', 'user_agent']

        elif log_type == 'adaptation_effectiveness':
            logs = AdaptationEffectivenessLog.objects.select_related('user', 'adaptation_event').all()
            fieldnames = ['user', 'success_rate_before', 'success_rate_after', 'success_rate_change',
                         'avg_time_before', 'avg_time_after', 'continued_session', 'timestamp']

        elif log_type == 'qlearning_decisions':
            logs = QLearningDecisionLog.objects.select_related('user').all()
            fieldnames = ['user', 'state_hash', 'decision_type', 'action_chosen', 'is_optimal', 
                         'epsilon_value', 'q_value_chosen', 'best_q_value', 'timestamp']

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
