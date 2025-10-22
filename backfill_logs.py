#!/usr/bin/env python
"""
Backfill script to populate Q-Learning logs from existing AttemptLog data.
This script reads historical quiz attempts and creates corresponding analytics logs.

Usage:
    python manage.py runscript backfill_logs
    OR
    python backfill_logs.py

Author: System Administrator
"""

import os
import sys
import django
from datetime import datetime, timedelta
from collections import defaultdict

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamify_v2.settings')
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


class LogBackfiller:
    """Backfill Q-Learning logs from existing AttemptLog data"""

    def __init__(self):
        self.total_processed = 0
        self.logs_created = {
            'engagement': 0,
            'success_rate': 0,
            'level_transition': 0,
            'reward': 0,
            'qlearning_performance': 0,
            'global_system': 0,
            'response_adaptation': 0
        }

    def run_backfill(self):
        """Main backfill process"""
        print("🚀 Starting Q-Learning Log Backfill...")
        print("=" * 60)

        with transaction.atomic():
            self.backfill_user_engagement_logs()
            self.backfill_success_rate_logs()
            self.backfill_level_transition_logs()
            self.backfill_reward_logs()
            self.backfill_qlearning_performance_logs()
            self.backfill_global_system_logs()
            self.backfill_response_adaptation_logs()

        self.print_summary()

    def backfill_user_engagement_logs(self):
        """Create UserEngagementLog entries from AttemptLog data"""
        print("📊 Backfilling User Engagement Logs...")

        # Group attempts by user and date for session aggregation
        user_daily_attempts = defaultdict(list)

        for attempt in AttemptLog.objects.select_related('user', 'question').order_by('created_at'):
            date_key = attempt.created_at.date()
            user_daily_attempts[(attempt.user, date_key)].append(attempt)

        for (user, date), attempts in user_daily_attempts.items():
            # Create one engagement log per day per user
            total_duration = sum(a.time_spent for a in attempts)
            total_questions = len(attempts)
            total_hints = sum(getattr(a, 'hints_used', 0) for a in attempts)

            # Check if user leveled up on this day
            leveled_up = any(getattr(a, 'leveled_up', False) for a in attempts)

            UserEngagementLog.objects.create(
                user=user,
                session_type='quiz_attempt',
                session_id=f"backfill_{user.id}_{date.strftime('%Y%m%d')}",
                duration_seconds=int(total_duration),
                questions_attempted=total_questions,
                hints_used=total_hints,
                gamification_interactions=1 if leveled_up else 0,
                metadata={
                    'backfilled': True,
                    'attempts_count': total_questions,
                    'date': date.strftime('%Y-%m-%d'),
                    'leveled_up': leveled_up
                }
            )
            self.logs_created['engagement'] += 1
            self.total_processed += total_questions

        print(f"  ✅ Created {self.logs_created['engagement']} engagement logs")

    def backfill_success_rate_logs(self):
        """Create SuccessRateLog entries from AttemptLog data"""
        print("📈 Backfilling Success Rate Logs...")

        # Group attempts by user, difficulty, and date
        user_difficulty_daily = defaultdict(list)

        for attempt in AttemptLog.objects.select_related('user', 'question').order_by('created_at'):
            date_key = attempt.created_at.date()
            user_difficulty_daily[(attempt.user, attempt.difficulty_attempted, date_key)].append(attempt)

        for (user, difficulty, date), attempts in user_difficulty_daily.items():
            today_start = timezone.datetime.combine(date, timezone.datetime.min.time())
            today_end = today_start + timedelta(days=1)

            # Calculate metrics
            total_attempts = len(attempts)
            correct_attempts = sum(1 for a in attempts if a.is_correct)
            avg_time = sum(a.time_spent for a in attempts) / total_attempts if total_attempts > 0 else 0
            accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0

            SuccessRateLog.objects.create(
                user=user,
                difficulty=difficulty,
                total_attempts=total_attempts,
                correct_attempts=correct_attempts,
                average_time_spent=avg_time,
                accuracy_percentage=accuracy,
                time_window_start=today_start,
                time_window_end=today_end,
                metadata={
                    'backfilled': True,
                    'date': date.strftime('%Y-%m-%d')
                }
            )
            self.logs_created['success_rate'] += 1

        print(f"  ✅ Created {self.logs_created['success_rate']} success rate logs")

    def backfill_level_transition_logs(self):
        """Create LevelTransitionLog entries from StudentProfile changes"""
        print("🏆 Backfilling Level Transition Logs...")

        # Find users who have leveled up by checking current level vs initial level
        for profile in StudentProfile.objects.select_related('user').filter(level__in=['intermediate', 'advanced', 'expert']):
            user = profile.user

            # Look for level transitions in attempt logs (where leveled_up would be True)
            attempts_with_levelup = AttemptLog.objects.filter(
                user=user,
                created_at__gte=timezone.now() - timedelta(days=30)  # Last 30 days
            ).order_by('created_at')

            for attempt in attempts_with_levelup:
                # Check if this attempt might have caused a level up
                # (This is approximate - we don't have the exact level up data)
                if hasattr(attempt, 'leveled_up') and getattr(attempt, 'leveled_up', False):
                    # Determine old and new level (approximate)
                    old_level = 'beginner' if profile.level in ['intermediate', 'advanced', 'expert'] else profile.level
                    new_level = profile.level

                    LevelTransitionLog.objects.create(
                        user=user,
                        transition_type='level_up_auto',
                        old_level=old_level,
                        new_level=new_level,
                        transition_condition={
                            'backfilled': True,
                            'xp_threshold': 200 if new_level == 'intermediate' else 500 if new_level == 'advanced' else 800,
                            'estimated_from_attempt': attempt.id
                        },
                        performance_metrics={
                            'question_difficulty': attempt.difficulty_attempted,
                            'is_correct': attempt.is_correct,
                            'time_spent': attempt.time_spent,
                            'reward_earned': attempt.reward_numeric
                        }
                    )
                    self.logs_created['level_transition'] += 1

        print(f"  ✅ Created {self.logs_created['level_transition']} level transition logs")

    def backfill_reward_logs(self):
        """Create RewardIncentivesLog entries from AttemptLog rewards"""
        print("🎁 Backfilling Reward Logs...")

        for attempt in AttemptLog.objects.select_related('user', 'question').filter(reward_numeric__gt=0):
            reward_type = 'points'

            # Check if this attempt might have caused a level up
            try:
                profile = attempt.user.student_profile
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
                    'time_spent': attempt.time_spent,
                    'attempt_id': attempt.id
                },
                user_reaction={
                    'will_continue_session': True,
                    'engagement_score': 1.0 if attempt.reward_numeric > 0 else 0.5
                },
                session_continuation=True
            )
            self.logs_created['reward'] += 1

        print(f"  ✅ Created {self.logs_created['reward']} reward logs")

    def backfill_qlearning_performance_logs(self):
        """Create QLearningPerformanceLog entries from Q-Table data"""
        print("🧠 Backfilling Q-Learning Performance Logs...")

        # Group Q-table entries by user for performance analysis
        for user in StudentProfile.objects.values_list('user', flat=True):
            from django.contrib.auth.models import User
            user_obj = User.objects.get(id=user)

            q_entries = QTableEntry.objects.filter(user=user_obj)
            total_entries = q_entries.count()

            if total_entries > 0 and total_entries % 5 == 0:  # Every 5 entries
                # Calculate performance metrics
                avg_q_value = sum(entry.q_value for entry in q_entries) / total_entries

                # Action distribution
                action_counts = {'easy': 0, 'medium': 0, 'hard': 0}
                for entry in q_entries:
                    if entry.action in action_counts:
                        action_counts[entry.action] += 1

                total_actions = sum(action_counts.values())
                action_distribution = {
                    action: count / total_actions if total_actions > 0 else 0
                    for action, count in action_counts.items()
                }

                optimal_frequency = max(action_distribution.values()) if action_distribution else 0

                QLearningPerformanceLog.objects.create(
                    user=user_obj,
                    state_hash='backfill_performance',
                    action_distribution=action_distribution,
                    optimal_action_frequency=optimal_frequency,
                    average_q_value=avg_q_value,
                    q_table_size=total_entries,
                    learning_progress=min(1.0, total_entries / 50),
                    snapshot_interval=5,
                    metadata={
                        'backfilled': True,
                        'total_q_entries': total_entries
                    }
                )
                self.logs_created['qlearning_performance'] += 1

        print(f"  ✅ Created {self.logs_created['qlearning_performance']} Q-Learning performance logs")

    def backfill_global_system_logs(self):
        """Create GlobalSystemLog entries from overall statistics"""
        print("🌍 Backfilling Global System Logs...")

        # Calculate daily global statistics
        daily_stats = defaultdict(lambda: {'attempts': 0, 'correct': 0, 'users': set()})

        for attempt in AttemptLog.objects.select_related('user').order_by('created_at'):
            date_key = attempt.created_at.date()
            daily_stats[date_key]['attempts'] += 1
            daily_stats[date_key]['users'].add(attempt.user.id)
            if attempt.is_correct:
                daily_stats[date_key]['correct'] += 1

        for date, stats in daily_stats.items():
            if stats['attempts'] > 0:
                today_start = timezone.datetime.combine(date, timezone.datetime.min.time())
                today_end = today_start + timedelta(days=1)

                accuracy = (stats['correct'] / stats['attempts']) * 100

                GlobalSystemLog.objects.create(
                    metric_type='engagement_daily',
                    metric_data={
                        'backfilled': True,
                        'total_users': len(stats['users']),
                        'total_attempts': stats['attempts'],
                        'correct_attempts': stats['correct'],
                        'global_accuracy': round(accuracy, 2),
                        'active_users': len(stats['users']),
                        'date': date.strftime('%Y-%m-%d')
                    },
                    time_window='daily'
                )
                self.logs_created['global_system'] += 1

        print(f"  ✅ Created {self.logs_created['global_system']} global system logs")

    def backfill_response_adaptation_logs(self):
        """Create ResponseToAdaptationLog entries for difficulty changes"""
        print("🔄 Backfilling Response to Adaptation Logs...")

        # Find difficulty transitions in attempt sequences
        user_difficulty_sequences = defaultdict(list)

        for attempt in AttemptLog.objects.select_related('user', 'question').order_by('user', 'created_at'):
            user_difficulty_sequences[attempt.user].append({
                'difficulty': attempt.difficulty_attempted,
                'is_correct': attempt.is_correct,
                'time_spent': attempt.time_spent,
                'timestamp': attempt.created_at,
                'id': attempt.id
            })

        for user, attempts in user_difficulty_sequences.items():
            for i in range(1, len(attempts)):
                current = attempts[i]
                previous = attempts[i-1]

                # Check for difficulty adaptation
                if current['difficulty'] != previous['difficulty']:
                    adaptation_type = 'difficulty_transition'

                    ResponseToAdaptationLog.objects.create(
                        user=user,
                        adaptation_type=adaptation_type,
                        old_state={
                            'difficulty': previous['difficulty'],
                            'is_correct': previous['is_correct'],
                            'time_spent': previous['time_spent']
                        },
                        new_state={
                            'difficulty': current['difficulty'],
                            'is_correct': current['is_correct'],
                            'time_spent': current['time_spent']
                        },
                        adaptation_details={
                            'backfilled': True,
                            'reason': 'difficulty_adaptation',
                            'attempt_sequence': f"{previous['id']} → {current['id']}"
                        },
                        first_attempt_after={
                            'is_correct': current['is_correct'],
                            'time_spent': current['time_spent'],
                            'attempt_id': current['id']
                        },
                        hint_usage_change=0,
                        session_duration_change=current['time_spent']
                    )
                    self.logs_created['response_adaptation'] += 1

        print(f"  ✅ Created {self.logs_created['response_adaptation']} response to adaptation logs")

    def print_summary(self):
        """Print backfill summary"""
        print("\n" + "=" * 60)
        print("🎉 BACKFILL COMPLETED SUCCESSFULLY!")
        print("=" * 60)

        print("📊 Logs Created:")
        for log_type, count in self.logs_created.items():
            print(f"  • {log_type.replace('_', ' ').title()}: {count} entries")

        print(f"\n🔢 Total Attempts Processed: {self.total_processed}")
        print(f"📈 Total Log Entries Created: {sum(self.logs_created.values())}")

        print("\n✅ Admin Interface Should Now Show:")
        print("  • User Engagement Logs - Session patterns")
        print("  • Success Rate Logs - Daily accuracy by difficulty")
        print("  • Level Transition Logs - Level up events")
        print("  • Reward & Incentives Logs - XP distribution")
        print("  • Q-Learning Performance Logs - Algorithm metrics")
        print("  • Response to Adaptation Logs - Difficulty changes")
        print("  • Global System Logs - Overall statistics")

        print("\n🚀 Historical data from student3, student5, etc. is now available for analysis!")


def main():
    """Main execution function"""
    print("Q-Learning Log Backfill Script")
    print("This will populate analytics logs from existing AttemptLog data\n")

    # Confirmation prompt
    response = input("⚠️  This will create logs from existing data. Continue? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ Backfill cancelled.")
        return

    # Run backfill
    backfiller = LogBackfiller()
    backfiller.run_backfill()


if __name__ == '__main__':
    main()
