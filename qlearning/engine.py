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

    @classmethod
    def log_decision(
        cls,
        user: CustomUser,
        state_hash: str,
        decision_type: str,
        epsilon_value: float,
        action_chosen: str,
        q_value_chosen: float,
        best_q_value: float,
        all_q_values: dict,
        is_optimal: bool
    ) -> None:
        """
        Log Q-Learning decision making process
        """
        from .models import QLearningDecisionLog
        try:
            QLearningDecisionLog.objects.create(
                user=user,
                state_hash=state_hash,
                decision_type=decision_type,
                epsilon_value=epsilon_value,
                action_chosen=action_chosen,
                q_value_chosen=q_value_chosen,
                best_q_value=best_q_value,
                all_q_values=all_q_values,
                is_optimal=is_optimal
            )
            print(f"Decision logged: {decision_type} - {action_chosen} (Optimal: {is_optimal})")
        except Exception as e:
            print(f"Error logging decision: {e}")

    @classmethod
    def log_adaptation(
        cls,
        user: CustomUser,
        old_difficulty: str,
        new_difficulty: str,
        state_hash: str,
        reason: str = None
    ) -> None:
        """
        Log an adaptation event when difficulty changes
        """
        from .models import ResponseToAdaptationLog
        if old_difficulty != new_difficulty:
            try:
                ResponseToAdaptationLog.objects.create(
                    user=user,
                    adaptation_type='difficulty_transition',
                    old_state={'difficulty': old_difficulty},
                    new_state={'difficulty': new_difficulty},
                    adaptation_details={
                        'reason': reason or 'Automatic difficulty adjustment',
                        'state_hash': state_hash
                    }
                )
                print(f"Adaptation logged: {old_difficulty} -> {new_difficulty}")
            except Exception as e:
                print(f"Error logging adaptation: {e}")

    @classmethod
    def choose_action(
        cls,
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
        print(f"\n=== DEBUG: QLearningEngine.choose_action called ===")
        print(f"User: {user}, Current difficulty: {current_difficulty}, State tuple: {state_tuple}")
        
        # Use dynamic epsilon if not provided
        if epsilon is None:
            epsilon = QLearningEngine.get_dynamic_epsilon(user)
            print(f"Using dynamic epsilon: {epsilon}")

        # Get allowed actions with safety constraints
        allowed_actions = QLearningEngine.get_allowed_actions(user, current_difficulty)
        print(f"Allowed actions: {allowed_actions}")
        
        # If only one action allowed (safety override), return it
        if len(allowed_actions) == 1:
            print(f"Only one action allowed: {allowed_actions[0]}")
            return allowed_actions[0]

        state_hash = QLearningEngine.hash_state(state_tuple)
        print(f"State hash: {state_hash}")

        # Epsilon-greedy action selection
        rand_val = random.random()
        print(f"Random value: {rand_val}, Epsilon: {epsilon}")
        
        if rand_val < epsilon:
            # EXPLORATION: Choose random from ALLOWED actions
            chosen_action = random.choice(allowed_actions)
            decision_type = 'exploration'
            print(f"EXPLORATION: Chose {chosen_action} randomly from {allowed_actions}")
            
            # Get Q-values for logging
            q_values = {}
            print("Fetching Q-values for actions:")
            for action in allowed_actions:
                try:
                    entry = QTableEntry.objects.get(
                        user=user,
                        state_hash=state_hash,
                        action=action
                    )
                    q_values[action] = entry.q_value
                    print(f"  - {action}: {entry.q_value} (from DB)")
                except QTableEntry.DoesNotExist:
                    q_values[action] = 0.0
                    print(f"  - {action}: 0.0 (default)")
            
            # Find best action and its Q-value
            best_action = max(q_values, key=q_values.get)
            best_q_value = q_values[best_action]
            print(f"Best action: {best_action} (Q-value: {best_q_value})")
            
            # Log the exploration decision
            print("Logging exploration decision...")
            try:
                from .models import QLearningDecisionLog
                print(f"QLearningDecisionLog model: {QLearningDecisionLog}")
                
                cls.log_decision(
                    user=user,
                    state_hash=state_hash,
                    decision_type='exploration',
                    epsilon_value=epsilon,
                    action_chosen=chosen_action,
                    q_value_chosen=q_values.get(chosen_action, 0.0),
                    best_q_value=best_q_value,
                    all_q_values=q_values,
                    is_optimal=(chosen_action == best_action)
                )
                print("Successfully logged exploration decision")
            except Exception as e:
                print(f"ERROR in log_decision: {e}")
                import traceback
                traceback.print_exc()
            
            # Log adaptation if difficulty changes
            if current_difficulty and chosen_action != current_difficulty:
                cls.log_adaptation(
                    user, 
                    current_difficulty or 'none', 
                    chosen_action,
                    state_hash,
                    'Exploration (epsilon-greedy)'
                )
                
            return chosen_action
        else:
            # EXPLOITATION: Choose best action from ALLOWED actions
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
                    q_values[action] = 0.0

            # Get action with highest Q-value
            best_action = max(q_values, key=q_values.get)
            best_q_value = q_values[best_action]
            
            # Log the exploitation decision
            cls.log_decision(
                user=user,
                state_hash=state_hash,
                decision_type='exploitation',
                epsilon_value=epsilon,
                action_chosen=best_action,
                q_value_chosen=best_q_value,
                best_q_value=best_q_value,
                all_q_values=q_values,
                is_optimal=True  # Always optimal in exploitation
            )
            
            # Log adaptation if difficulty changes
            if current_difficulty and best_action != current_difficulty:
                cls.log_adaptation(
                    user,
                    current_difficulty,
                    best_action,
                    state_hash,
                    'Exploitation (best Q-value)'
                )
                
            return best_action

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