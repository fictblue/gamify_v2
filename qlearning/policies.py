from typing import Dict, Tuple, Optional
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from accounts.models import StudentProfile
from quizzes.models import AttemptLog
from qlearning.models import QLearningLog


class LevelTransitionPolicy:
    """
    Policies for level transitions and progression in the gamification system.

    Handles:
    - Level up/down logic based on performance windows
    - Progressive hint system
    - Dual progress tracking (user + global)
    - Consecutive performance tracking for adaptive difficulty
    """

    # Level progression thresholds (KEPT ORIGINAL)
    LEVEL_UP_THRESHOLDS = {
        'easy_to_medium': 0.7,    # 70% correct in last 10 questions
        'medium_to_hard': 0.6,    # 60% correct in last 10 questions
    }

    # Level degradation thresholds (KEPT ORIGINAL)
    LEVEL_DOWN_THRESHOLDS = {
        'medium_to_easy': 0.3,    # ≤30% correct (≤3/10) triggers level down
        'hard_to_medium': 0.5,    # ≤50% correct (≤5/10) triggers level down
    }

    # Window size for performance calculation
    PERFORMANCE_WINDOW = 10
    
    # NEW: Quick response window for immediate level down
    QUICK_CHECK_WINDOW = 5  # Check last 5 for fast intervention
    
    # NEW: Consecutive wrong threshold for emergency level down
    MAX_CONSECUTIVE_WRONG = 3  # Drop down after 3 consecutive wrong

    # Hint progression for easy questions
    EASY_HINTS = {
        1: "Try reading the question more carefully and look at all options.",
        2: "Consider the basic principles and most straightforward answer.",
        3: "The answer is related to fundamental concepts. Let me show you..."
    }

    # Limited hints for medium/hard questions
    MEDIUM_HINTS = [
        "Think about the key concepts involved.",
        "Consider the most likely correct approach."
    ]

    HARD_HINTS = [
        "This requires careful analysis.",
        "Consider all possibilities systematically."
    ]

    @staticmethod
    def compute_window_stats(user, difficulty: str, window: int = None) -> Tuple[int, int]:
        """
        Compute statistics for the last N questions of a specific difficulty.

        Args:
            user: User instance
            difficulty: Question difficulty ('easy', 'medium', 'hard')
            window: Number of recent questions to consider (default: PERFORMANCE_WINDOW)

        Returns:
            Tuple of (correct_count, total_count) for the window
        """
        if window is None:
            window = LevelTransitionPolicy.PERFORMANCE_WINDOW

        # Get recent attempts for this difficulty
        all_attempts = AttemptLog.objects.filter(
            user=user,
            question__difficulty=difficulty
        ).order_by('-created_at')

        # Get the first 'window' attempts
        recent_attempts = list(all_attempts[:window])

        total_count = len(recent_attempts)
        correct_count = sum(1 for attempt in recent_attempts if attempt.is_correct)

        return correct_count, total_count

    @staticmethod
    def get_consecutive_performance(user, difficulty: str, window: int = 5) -> Dict:
        """
        NEW METHOD: Track consecutive correct/wrong answers for adaptive response.
        
        Args:
            user: User instance
            difficulty: Question difficulty
            window: Number of recent questions to check
            
        Returns:
            Dict with consecutive performance metrics
        """
        recent_attempts = AttemptLog.objects.filter(
            user=user,
            question__difficulty=difficulty
        ).order_by('-created_at')[:window]
        
        attempts_list = list(recent_attempts)
        
        if not attempts_list:
            return {
                'consecutive_correct': 0,
                'consecutive_wrong': 0,
                'total_checked': 0,
                'last_result': None
            }
        
        # Count consecutive from most recent
        consecutive_correct = 0
        consecutive_wrong = 0
        
        for attempt in attempts_list:
            if attempt.is_correct:
                if consecutive_wrong == 0:  # Still counting correct streak
                    consecutive_correct += 1
                else:
                    break  # Hit a wrong answer, stop counting
            else:
                if consecutive_correct == 0:  # Still counting wrong streak
                    consecutive_wrong += 1
                else:
                    break  # Hit a correct answer, stop counting
        
        return {
            'consecutive_correct': consecutive_correct,
            'consecutive_wrong': consecutive_wrong,
            'total_checked': len(attempts_list),
            'last_result': attempts_list[0].is_correct if attempts_list else None
        }

    @staticmethod
    def can_level_up(profile: StudentProfile) -> Tuple[bool, Optional[str]]:
        """
        Check if user can level up based on XP thresholds (consistent with StudentProfile).

        Args:
            profile: StudentProfile instance

        Returns:
            Tuple of (can_level_up, target_level)
        """
        current_level = profile.level
        current_xp = profile.xp

        # XP thresholds (consistent with StudentProfile and views)
        xp_thresholds = {
            'beginner': 200,     # Updated from 100 to 200
            'intermediate': 500, # Updated from 300 to 500
            'advanced': 800,    # Updated from 500 to 800
            'expert': 1000,     # Set to 1000 for achievement goal
        }

        if current_level == 'beginner' and current_xp >= xp_thresholds['beginner']:
            return True, 'intermediate'
        elif current_level == 'intermediate' and current_xp >= xp_thresholds['intermediate']:
            return True, 'advanced'
        elif current_level == 'advanced' and current_xp >= xp_thresholds['advanced']:
            return True, 'expert'
        elif current_level == 'expert':
            # Already at max level
            return False, None

        return False, None

    @staticmethod
    def should_level_down(profile: StudentProfile) -> Tuple[bool, Optional[str]]:
        """
        ENHANCED: Check if user should level down based on poor performance.
        Now includes quick response for consecutive wrong answers.

        Args:
            profile: StudentProfile instance

        Returns:
            Tuple of (should_level_down, target_level)
        """
        current_level = profile.level

        if current_level == 'beginner':
            # Beginner cannot level down
            return False, None

        elif current_level == 'intermediate':
            # Check medium difficulty performance
            difficulty = 'medium'
            
            # QUICK CHECK: Emergency level down for consecutive wrong
            consecutive = LevelTransitionPolicy.get_consecutive_performance(
                profile.user, difficulty, window=LevelTransitionPolicy.QUICK_CHECK_WINDOW
            )
            
            if consecutive['consecutive_wrong'] >= LevelTransitionPolicy.MAX_CONSECUTIVE_WRONG:
                # Emergency level down!
                return True, 'beginner'
            
            # REGULAR CHECK: Window-based accuracy
            correct, total = LevelTransitionPolicy.compute_window_stats(
                profile.user, difficulty
            )

            if total >= LevelTransitionPolicy.PERFORMANCE_WINDOW:
                accuracy = correct / total
                if accuracy <= LevelTransitionPolicy.LEVEL_DOWN_THRESHOLDS['medium_to_easy']:
                    return True, 'beginner'

        elif current_level == 'advanced':
            # Check hard difficulty performance
            difficulty = 'hard'
            
            # QUICK CHECK: Emergency level down for consecutive wrong
            consecutive = LevelTransitionPolicy.get_consecutive_performance(
                profile.user, difficulty, window=LevelTransitionPolicy.QUICK_CHECK_WINDOW
            )
            
            if consecutive['consecutive_wrong'] >= LevelTransitionPolicy.MAX_CONSECUTIVE_WRONG:
                # Emergency level down!
                return True, 'intermediate'
            
            # REGULAR CHECK: Window-based accuracy
            correct, total = LevelTransitionPolicy.compute_window_stats(
                profile.user, difficulty
            )

            if total >= LevelTransitionPolicy.PERFORMANCE_WINDOW:
                accuracy = correct / total
                if accuracy <= LevelTransitionPolicy.LEVEL_DOWN_THRESHOLDS['hard_to_medium']:
                    return True, 'intermediate'

        return False, None

    @staticmethod
    def get_hint_for_question(question, wrong_count: int) -> Optional[str]:
        """
        Get appropriate hint based on question difficulty and wrong attempts.

        Args:
            question: Question instance
            wrong_count: Number of times user got this question wrong

        Returns:
            Hint text or None
        """
        difficulty = question.difficulty

        if difficulty == 'easy':
            # Progressive hints for easy questions
            if wrong_count >= 3:
                return LevelTransitionPolicy.EASY_HINTS[3]
            elif wrong_count >= 2:
                return LevelTransitionPolicy.EASY_HINTS[2]
            elif wrong_count >= 1:
                return LevelTransitionPolicy.EASY_HINTS[1]

        elif difficulty == 'medium':
            # Limited hints for medium questions
            if wrong_count >= 1:
                return LevelTransitionPolicy.MEDIUM_HINTS[wrong_count % len(LevelTransitionPolicy.MEDIUM_HINTS)]

        elif difficulty == 'hard':
            # Very limited hints for hard questions
            if wrong_count >= 2:
                return LevelTransitionPolicy.HARD_HINTS[wrong_count % len(LevelTransitionPolicy.HARD_HINTS)]

        return None

    @staticmethod
    def calculate_level_progress(profile: StudentProfile) -> Dict:
        """
        FIXED: Calculate progress towards level up (XP-based, consistent with StudentProfile).

        Args:
            profile: StudentProfile instance

        Returns:
            Dict with progress information
        """
        current_level = profile.level
        current_xp = profile.xp

        # XP thresholds for NEXT level
        level_requirements = {
            'beginner': {'next': 'intermediate', 'xp_required': 200},    # Updated from 100 to 200
            'intermediate': {'next': 'advanced', 'xp_required': 500},   # Updated from 300 to 500
            'advanced': {'next': 'expert', 'xp_required': 800},        # Updated from 500 to 800
            'expert': {'next': None, 'xp_required': 1000}              # Set to 1000 for achievement goal
        }

        # Expert level (max)
        if current_level == 'expert':
            return {
                'can_level_up': False,
                'target_level': None,
                'progress_percentage': 100,
                'current_xp': current_xp,
                'required_xp': level_requirements['expert']['xp_required'],
                'remaining_xp': 0
            }

        # Get current level requirements
        level_info = level_requirements.get(current_level)
        if not level_info:
            # Fallback for unknown level
            return {
                'can_level_up': False,
                'target_level': None,
                'progress_percentage': 0,
                'current_xp': current_xp,
                'required_xp': 0,
                'remaining_xp': 0
            }

        required_xp = level_info['xp_required']
        target_level = level_info['next']
        
        # Calculate progress
        can_level_up = current_xp >= required_xp
        progress_percentage = min(100, (current_xp / required_xp * 100)) if required_xp > 0 else 0
        remaining_xp = max(0, required_xp - current_xp)

        return {
            'can_level_up': can_level_up,
            'target_level': target_level,
            'progress_percentage': round(progress_percentage, 1),
            'current_xp': current_xp,
            'required_xp': required_xp,
            'remaining_xp': remaining_xp
        }

    @staticmethod
    def get_user_statistics(user) -> Dict:
        """
        Get comprehensive user statistics for dashboard display.

        Args:
            user: User instance

        Returns:
            Dict with user statistics
        """
        try:
            profile = user.student_profile
        except:
            return {'error': 'No profile found'}

        # Get attempt statistics
        all_attempts = AttemptLog.objects.filter(user=user)
        total_attempts = all_attempts.count()
        correct_attempts = all_attempts.filter(is_correct=True).count()
        accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0

        # Get difficulty breakdown
        difficulty_stats = {}
        for difficulty in ['easy', 'medium', 'hard']:
            correct, total = LevelTransitionPolicy.compute_window_stats(user, difficulty)
            
            # NEW: Add consecutive tracking
            consecutive = LevelTransitionPolicy.get_consecutive_performance(user, difficulty)
            
            difficulty_stats[difficulty] = {
                'correct': correct,
                'total': total,
                'accuracy': (correct / total * 100) if total > 0 else 0,
                'consecutive_correct': consecutive['consecutive_correct'],
                'consecutive_wrong': consecutive['consecutive_wrong']
            }

        # Get streak information
        current_streak = profile.streak_correct

        # Get level progress
        level_progress = LevelTransitionPolicy.calculate_level_progress(profile)

        return {
            'total_attempts': total_attempts,
            'correct_attempts': correct_attempts,
            'overall_accuracy': round(accuracy, 1),
            'current_streak': current_streak,
            'level': profile.level,
            'points': profile.points,
            'progress': profile.progress,
            'difficulty_stats': difficulty_stats,
            'level_progress': level_progress
        }

    @staticmethod
    def update_global_statistics(attempt_log: AttemptLog):
        """
        Update global system statistics when an attempt is recorded.

        Args:
            attempt_log: AttemptLog instance
        """
        # This could update global counters, achievements, etc.
        # For now, we'll just ensure the attempt is properly logged
        pass

    @staticmethod
    def get_performance_summary(user, days: int = 30) -> Dict:
        """
        Get performance summary for the last N days.

        Args:
            user: User instance
            days: Number of days to look back

        Returns:
            Dict with performance summary
        """
        cutoff_date = timezone.now() - timedelta(days=days)

        recent_attempts = AttemptLog.objects.filter(
            user=user,
            created_at__gte=cutoff_date
        )

        total = recent_attempts.count()
        correct = recent_attempts.filter(is_correct=True).count()

        # Daily breakdown
        daily_stats = []
        for i in range(days):
            day = cutoff_date + timedelta(days=i)
            next_day = day + timedelta(days=1)

            day_attempts = recent_attempts.filter(
                created_at__gte=day,
                created_at__lt=next_day
            )

            daily_stats.append({
                'date': day.date(),
                'total': day_attempts.count(),
                'correct': day_attempts.filter(is_correct=True).count()
            })

        return {
            'period_days': days,
            'total_attempts': total,
            'correct_attempts': correct,
            'accuracy': (correct / total * 100) if total > 0 else 0,
            'daily_stats': daily_stats
        }