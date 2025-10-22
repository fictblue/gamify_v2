import hashlib
import json
import random
from typing import Tuple, List, Optional, Dict
from django.db import transaction

from .models import QTableEntry, QLearningLog
from accounts.models import CustomUser
from .policies import LevelTransitionPolicy


class QLearningEngine:
    """
    Enhanced Q-Learning engine for adaptive difficulty selection.

    Features:
    - Epsilon-greedy action selection with user-level constraints
    - Safety checks to prevent frustrating experiences
    - Integration with LevelTransitionPolicy for consecutive tracking
    - Dynamic epsilon based on user performance
    """

    # Default Q-learning parameters
    DEFAULT_ALPHA = 0.1      # Learning rate
    DEFAULT_GAMMA = 0.9      # Discount factor
    DEFAULT_EPSILON = 0.15   # Base exploration rate (increased from 0.1)

    # Dynamic epsilon adjustment
    EPSILON_BY_LEVEL = {
        'beginner': 0.25,      # More exploration for beginners
        'intermediate': 0.15,  # Balanced exploration
        'advanced': 0.10,      # Less exploration, more exploitation
        'expert': 0.05         # Minimal exploration
    }

    # Possible actions (difficulty levels)
    ACTIONS = ['easy', 'medium', 'hard']
    
    # Level-constrained action spaces
    ALLOWED_ACTIONS = {
        'beginner': ['easy', 'medium'],           # No hard for beginners
        'intermediate': ['easy', 'medium', 'hard'], # All difficulties
        'advanced': ['medium', 'hard'],            # No easy for advanced
        'expert': ['hard']                         # Only hard for experts
    }

    @staticmethod
    def hash_state(state_tuple: Tuple) -> str:
        """
        Create a deterministic hash from a state tuple.

        Args:
            state_tuple: Tuple representing the current state

        Returns:
            32-character MD5 hash string
        """
        # Convert tuple to JSON string for consistent hashing
        state_json = json.dumps(state_tuple, sort_keys=True)
        state_bytes = state_json.encode('utf-8')

        # Create MD5 hash
        hash_obj = hashlib.md5(state_bytes)
        return hash_obj.hexdigest()

    @staticmethod
    def get_q(user: CustomUser, state_hash: str, action: str) -> QTableEntry:
        """
        Get Q-value for a specific state-action pair, creating entry if it doesn't exist.

        Args:
            user: User instance
            state_hash: Hash of the current state
            action: Action to get Q-value for

        Returns:
            QTableEntry instance
        """
        return QTableEntry.get_or_create_entry(user, state_hash, action)

    @staticmethod
    def get_dynamic_epsilon(user: CustomUser) -> float:
        """
        NEW: Calculate dynamic epsilon based on user level and recent performance.
        
        Args:
            user: User instance
            
        Returns:
            Adjusted epsilon value
        """
        try:
            profile = user.student_profile
            base_epsilon = QLearningEngine.EPSILON_BY_LEVEL.get(
                profile.level, 
                QLearningEngine.DEFAULT_EPSILON
            )
            
            # Adjust epsilon based on recent performance
            # If user is struggling (high consecutive wrong), reduce exploration
            stats = LevelTransitionPolicy.get_user_statistics(user)
            
            for difficulty, diff_stats in stats.get('difficulty_stats', {}).items():
                consecutive_wrong = diff_stats.get('consecutive_wrong', 0)
                
                # If struggling (3+ consecutive wrong), reduce exploration
                if consecutive_wrong >= 3:
                    return base_epsilon * 0.5  # Cut exploration in half
                # If doing well (5+ consecutive correct), can explore more
                elif diff_stats.get('consecutive_correct', 0) >= 5:
                    return min(base_epsilon * 1.2, 0.3)  # Increase slightly, cap at 30%
            
            return base_epsilon
            
        except:
            return QLearningEngine.DEFAULT_EPSILON

    @staticmethod
    def get_allowed_actions(user: CustomUser, current_difficulty: str = None) -> List[str]:
        """
        NEW: Get allowed actions based on user level and safety checks.
        
        Args:
            user: User instance
            current_difficulty: Current question difficulty (for safety checks)
            
        Returns:
            List of allowed difficulty levels
        """
        try:
            profile = user.student_profile
            level = profile.level
            
            # Get base allowed actions for this level
            allowed = QLearningEngine.ALLOWED_ACTIONS.get(
                level, 
                ['easy', 'medium', 'hard']
            )
            
            # SAFETY CHECK: If user is struggling, restrict to easier difficulties
            if current_difficulty:
                consecutive = LevelTransitionPolicy.get_consecutive_performance(
                    user, current_difficulty, window=5
                )
                
                # If 2+ consecutive wrong, don't allow harder difficulty
                if consecutive['consecutive_wrong'] >= 2:
                    if current_difficulty == 'easy':
                        allowed = ['easy']  # Stay at easy
                    elif current_difficulty == 'medium':
                        allowed = ['easy', 'medium']  # Don't go to hard
                    elif current_difficulty == 'hard':
                        allowed = ['medium', 'hard']  # Don't go to harder
            
            return allowed
            
        except:
            return QLearningEngine.ACTIONS  # Fallback to all actions

    @staticmethod
    def choose_action(
        user: CustomUser, 
        state_tuple: Tuple, 
        epsilon: float = None,
        current_difficulty: str = None
    ) -> str:
        """
        ENHANCED: Choose an action using epsilon-greedy policy with safety checks.

        Args:
            user: User instance
            state_tuple: Current state tuple
            epsilon: Exploration rate (uses dynamic calculation if None)
            current_difficulty: Current question difficulty for safety checks

        Returns:
            Selected action string
        """
        # Use dynamic epsilon if not provided
        if epsilon is None:
            epsilon = QLearningEngine.get_dynamic_epsilon(user)

        # Get allowed actions with safety constraints
        allowed_actions = QLearningEngine.get_allowed_actions(user, current_difficulty)
        
        # If only one action allowed (safety override), return it
        if len(allowed_actions) == 1:
            return allowed_actions[0]

        state_hash = QLearningEngine.hash_state(state_tuple)

        # Epsilon-greedy action selection
        if random.random() < epsilon:
            # ENHANCED EXPLORATION: Choose random from ALLOWED actions only
            return random.choice(allowed_actions)
        else:
            # ENHANCED EXPLOITATION: Choose best action from ALLOWED actions
            q_values = {}

            for action in allowed_actions:
                try:
                    entry = QTableEntry.objects.get(
                        user=user,
                        state_hash=state_hash,
                        action=action
                    )
                    q_values[action] = entry.q_value
                except QTableEntry.DoesNotExist:
                    # If no entry exists, assume Q-value of 0
                    q_values[action] = 0.0

            # Return action with highest Q-value from allowed actions
            if q_values:
                return max(q_values, key=q_values.get)
            else:
                # Fallback to random allowed action
                return random.choice(allowed_actions)

    @staticmethod
    def update_q(
        user: CustomUser,
        state_tuple: Tuple,
        action: str,
        reward: float,
        next_state_tuple: Tuple,
        alpha: float = None,
        gamma: float = None
    ) -> QTableEntry:
        """
        Update Q-value using Q-learning update rule and log the change.

        Args:
            user: User instance
            state_tuple: Current state tuple
            action: Action taken
            reward: Reward received
            next_state_tuple: Next state tuple
            alpha: Learning rate (uses DEFAULT_ALPHA if None)
            gamma: Discount factor (uses DEFAULT_GAMMA if None)

        Returns:
            Updated QTableEntry instance
        """
        if alpha is None:
            alpha = QLearningEngine.DEFAULT_ALPHA
        if gamma is None:
            gamma = QLearningEngine.DEFAULT_GAMMA

        state_hash = QLearningEngine.hash_state(state_tuple)
        next_state_hash = QLearningEngine.hash_state(next_state_tuple) if next_state_tuple else None

        with transaction.atomic():
            # Get current Q-value
            current_entry = QLearningEngine.get_q(user, state_hash, action)
            q_value_before = current_entry.q_value

            # Calculate max Q-value for next state (only from allowed actions)
            max_next_q = 0.0
            if next_state_hash:
                # Get allowed actions for next state
                allowed_next = QLearningEngine.get_allowed_actions(user)
                
                for next_action in allowed_next:
                    try:
                        next_entry = QTableEntry.objects.get(
                            user=user,
                            state_hash=next_state_hash,
                            action=next_action
                        )
                        max_next_q = max(max_next_q, next_entry.q_value)
                    except QTableEntry.DoesNotExist:
                        # Assume 0 for unexplored state-action pairs
                        pass

            # Q-learning update rule
            # Q(s,a) = Q(s,a) + α[r + γ*max(Q(s',a')) - Q(s,a)]
            q_value_after = q_value_before + alpha * (reward + gamma * max_next_q - q_value_before)

            # Update the Q-table entry
            current_entry.q_value = q_value_after
            current_entry.save()

            # Log the Q-learning update
            QLearningLog.objects.create(
                user=user,
                state_hash=state_hash,
                action=action,
                reward=reward,
                q_value_before=q_value_before,
                q_value_after=q_value_after,
                next_state_hash=next_state_hash,
            )

        return current_entry

    @staticmethod
    def get_user_qtable_summary(user: CustomUser) -> dict:
        """
        Get a summary of the user's Q-table for analysis.

        Args:
            user: User instance

        Returns:
            Dictionary with Q-table statistics
        """
        entries = QTableEntry.objects.filter(user=user)

        if not entries:
            return {
                'total_entries': 0,
                'average_q_value': 0.0,
                'max_q_value': 0.0,
                'min_q_value': 0.0,
                'states_explored': 0,
                'actions_taken': {action: 0 for action in QLearningEngine.ACTIONS},
                'current_epsilon': QLearningEngine.get_dynamic_epsilon(user)
            }

        q_values = [entry.q_value for entry in entries]
        states = set(entry.state_hash for entry in entries)

        # Count actions taken
        actions_taken = {action: 0 for action in QLearningEngine.ACTIONS}
        for entry in entries:
            actions_taken[entry.action] += 1

        return {
            'total_entries': len(entries),
            'average_q_value': sum(q_values) / len(q_values),
            'max_q_value': max(q_values),
            'min_q_value': min(q_values),
            'states_explored': len(states),
            'actions_taken': actions_taken,
            'current_epsilon': QLearningEngine.get_dynamic_epsilon(user)
        }

    @staticmethod
    def get_learning_progress(user: CustomUser) -> dict:
        """
        ENHANCED: Get learning progress statistics with safety metrics.

        Args:
            user: User instance

        Returns:
            Dictionary with learning progress data
        """
        logs = QLearningLog.objects.filter(user=user)

        if not logs:
            return {
                'total_updates': 0,
                'average_reward': 0.0,
                'average_q_change': 0.0,
                'current_epsilon': QLearningEngine.get_dynamic_epsilon(user),
                'recent_activity': 0,
                'safety_interventions': 0
            }

        rewards = [log.reward for log in logs]
        q_changes = [abs(log.q_value_after - log.q_value_before) for log in logs]

        # Calculate recent activity (last 24 hours)
        from django.utils import timezone
        from datetime import timedelta
        recent_threshold = timezone.now() - timedelta(hours=24)
        recent_activity = logs.filter(timestamp__gte=recent_threshold).count()
        
        # NEW: Count safety interventions (negative rewards)
        safety_interventions = sum(1 for r in rewards if r < 0)

        return {
            'total_updates': len(logs),
            'average_reward': sum(rewards) / len(rewards) if rewards else 0.0,
            'average_q_change': sum(q_changes) / len(q_changes) if q_changes else 0.0,
            'current_epsilon': QLearningEngine.get_dynamic_epsilon(user),
            'recent_activity': recent_activity,
            'safety_interventions': safety_interventions,
            'positive_rewards': sum(1 for r in rewards if r > 0),
            'negative_rewards': sum(1 for r in rewards if r < 0),
        }

    @staticmethod
    def get_recommended_difficulty(user: CustomUser, state_tuple: Tuple) -> Dict:
        """
        NEW: Get recommended difficulty with confidence score and reasoning.
        
        Args:
            user: User instance
            state_tuple: Current state tuple
            
        Returns:
            Dict with recommendation details
        """
        try:
            profile = user.student_profile
            
            # Get Q-Learning recommendation
            ql_action = QLearningEngine.choose_action(user, state_tuple)
            
            # Get safety constraints
            allowed = QLearningEngine.get_allowed_actions(user)
            
            # Get consecutive performance
            stats = LevelTransitionPolicy.get_user_statistics(user)
            
            # Calculate confidence based on Q-table maturity
            summary = QLearningEngine.get_user_qtable_summary(user)
            confidence = min(summary['total_entries'] / 50.0, 1.0)  # Max at 50 entries
            
            # Determine reasoning
            reasoning = []
            
            if ql_action not in allowed:
                reasoning.append(f"Q-Learning suggested {ql_action}, but safety constraints limit to {allowed}")
                ql_action = random.choice(allowed)  # Fallback to allowed
            
            # Check if user is struggling
            for diff, diff_stats in stats.get('difficulty_stats', {}).items():
                if diff_stats['consecutive_wrong'] >= 2:
                    reasoning.append(f"User struggling with {diff} (consecutive wrong: {diff_stats['consecutive_wrong']})")
            
            # Check if user is excelling
            for diff, diff_stats in stats.get('difficulty_stats', {}).items():
                if diff_stats['consecutive_correct'] >= 5:
                    reasoning.append(f"User excelling at {diff} (consecutive correct: {diff_stats['consecutive_correct']})")
            
            return {
                'recommended_difficulty': ql_action,
                'allowed_difficulties': allowed,
                'confidence': round(confidence, 2),
                'reasoning': reasoning,
                'epsilon': QLearningEngine.get_dynamic_epsilon(user),
                'is_exploring': random.random() < QLearningEngine.get_dynamic_epsilon(user)
            }
            
        except Exception as e:
            # Fallback recommendation
            return {
                'recommended_difficulty': 'easy',
                'allowed_difficulties': ['easy', 'medium', 'hard'],
                'confidence': 0.0,
                'reasoning': [f'Error: {str(e)}'],
                'epsilon': QLearningEngine.DEFAULT_EPSILON,
                'is_exploring': True
            }