#!/usr/bin/env python
"""
Simple backfill script that can be run directly
"""

import os
import sys
import django
from datetime import datetime, timedelta
from collections import defaultdict

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamify_ai.settings')
django.setup()

from django.db import transaction
from django.utils import timezone
from accounts.models import StudentProfile
from quizzes.models import AttemptLog, Question
from qlearning.models import (
    UserEngagementLog, SuccessRateLog, LevelTransitionLog,
    RewardIncentivesLog, QLearningPerformanceLog, ResponseToAdaptationLog,
    GlobalSystemLog, QTableEntry
)


def simple_backfill():
    """Simple backfill of key logs from existing data"""
    print("🚀 Simple Q-Learning Log Backfill")
    print("=" * 50)

    with transaction.atomic():
        # 1. User Engagement Logs
        print("📊 Creating User Engagement Logs...")
        engagement_count = 0

        for attempt in AttemptLog.objects.select_related('user', 'question'):
            try:
                UserEngagementLog.objects.create(
                    user=attempt.user,
                    session_type='quiz_attempt',
                    session_id=f"simple_backfill_{attempt.id}",
                    duration_seconds=int(attempt.time_spent),
                    questions_attempted=1,
                    hints_used=0,  # Not available in old data
                    gamification_interactions=0,
                    metadata={
                        'backfilled': True,
                        'question_difficulty': attempt.difficulty_attempted,
                        'is_correct': attempt.is_correct,
                        'xp_earned': attempt.reward_numeric
                    }
                )
                engagement_count += 1
            except Exception as e:
                print(f"Error creating engagement log for attempt {attempt.id}: {e}")
                continue

        print(f"✅ Created {engagement_count} engagement logs")

        # 2. Success Rate Logs
        print("📈 Creating Success Rate Logs...")
        success_count = 0

        # Group by user and difficulty
        user_difficulty_stats = defaultdict(lambda: {'attempts': 0, 'correct': 0, 'total_time': 0})

        for attempt in AttemptLog.objects.select_related('user'):
            key = (attempt.user, attempt.difficulty_attempted)
            user_difficulty_stats[key]['attempts'] += 1
            user_difficulty_stats[key]['total_time'] += attempt.time_spent
            if attempt.is_correct:
                user_difficulty_stats[key]['correct'] += 1

        for (user, difficulty), stats in user_difficulty_stats.items():
            avg_time = stats['total_time'] / stats['attempts'] if stats['attempts'] > 0 else 0
            accuracy = (stats['correct'] / stats['attempts'] * 100) if stats['attempts'] > 0 else 0

            # Create daily log (use today's date for simplicity)
            today = timezone.now().date()
            today_start = timezone.datetime.combine(today, timezone.datetime.min.time())
            today_end = today_start + timedelta(days=1)

            SuccessRateLog.objects.create(
                user=user,
                difficulty=difficulty,
                total_attempts=stats['attempts'],
                correct_attempts=stats['correct'],
                average_time_spent=avg_time,
                accuracy_percentage=accuracy,
                time_window_start=today_start,
                time_window_end=today_end,
                metadata={'backfilled': True}
            )
            success_count += 1

        print(f"✅ Created {success_count} success rate logs")

        # 3. Reward Logs
        print("🎁 Creating Reward Logs...")
        reward_count = 0

        for attempt in AttemptLog.objects.filter(reward_numeric__gt=0):
            reward_type = 'points'
            # Check if user leveled up (simplified check)
            try:
                if hasattr(attempt, 'leveled_up') and getattr(attempt, 'leveled_up', False):
                    reward_type = 'level_up_bonus'
            except:
                pass

            RewardIncentivesLog.objects.create(
                user=attempt.user,
                reward_type=reward_type,
                reward_value=attempt.reward_numeric,
                trigger_condition={
                    'backfilled': True,
                    'question_difficulty': attempt.difficulty_attempted,
                    'is_correct': attempt.is_correct,
                    'time_spent': attempt.time_spent
                },
                user_reaction={'will_continue_session': True, 'engagement_score': 1.0},
                session_continuation=True
            )
            reward_count += 1

        print(f"✅ Created {reward_count} reward logs")

        # 4. Level Transition Logs (for users who have leveled up)
        print("🏆 Creating Level Transition Logs...")
        transition_count = 0

        for profile in StudentProfile.objects.exclude(level='beginner'):
            try:
                LevelTransitionLog.objects.create(
                    user=profile.user,
                    transition_type='level_up_auto',
                    old_level='beginner' if profile.level in ['intermediate', 'advanced', 'expert'] else profile.level,
                    new_level=profile.level,
                    transition_condition={'backfilled': True, 'estimated_from_profile': True},
                    performance_metrics={'level': profile.level, 'xp': profile.xp}
                )
                transition_count += 1
            except Exception as e:
                print(f"Error creating transition log for user {profile.user.username}: {e}")
                continue

        print(f"✅ Created {transition_count} level transition logs")

        # 5. Global System Logs
        print("🌍 Creating Global System Logs...")
        global_count = 0

        total_attempts = AttemptLog.objects.count()
        total_correct = AttemptLog.objects.filter(is_correct=True).count()
        total_users = StudentProfile.objects.count()

        if total_attempts > 0:
            global_accuracy = (total_correct / total_attempts) * 100

            GlobalSystemLog.objects.create(
                metric_type='engagement_daily',
                metric_data={
                    'backfilled': True,
                    'total_users': total_users,
                    'total_attempts': total_attempts,
                    'correct_attempts': total_correct,
                    'global_accuracy': round(global_accuracy, 2)
                },
                time_window='daily'
            )
            global_count += 1

        print(f"✅ Created {global_count} global system logs")

    print("\n" + "=" * 50)
    print("🎉 SIMPLE BACKFILL COMPLETED!")
    print("=" * 50)
    print(f"📊 Total logs created: {engagement_count + success_count + reward_count + transition_count + global_count}")
    print("\n✅ Check your Django admin interface - logs should now be populated!")
    print("📈 You can analyze historical data from student3, student5, etc.")


if __name__ == '__main__':
    simple_backfill()
