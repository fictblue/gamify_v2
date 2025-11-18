import json
import random
from typing import Dict, Tuple, Optional
from django.db import transaction
from django.utils import timezone

from accounts.models import StudentProfile
from quizzes.models import Question, AttemptLog
from qlearning.engine import QLearningEngine
from qlearning.models import QTableEntry
from qlearning.policies import LevelTransitionPolicy


class QuizService:
    """
    Service class for quiz-related operations with Q-Learning integration.

    This service handles:
    - ENHANCED state representation with performance metrics
    - Adaptive question selection using Q-Learning
    - Attempt recording with reward calculation
    - Hidden reward system for streaks
    - Hint policy for easy questions
    """

    # Reward constants
    BASE_CORRECT_REWARD = 10
    BASE_INCORRECT_PENALTY = -2
    STREAK_REWARD_THRESHOLD = 3
    HIDDEN_STREAK_REWARD = 10

    # Difficulty mapping for Q-Learning
    DIFFICULTY_ACTIONS = ['easy', 'medium', 'hard']

    @staticmethod
    def state_tuple(profile: StudentProfile) -> Tuple:
        """
        FIXED: Create an ENHANCED state tuple that captures user performance.
        
        Now includes:
        - User level
        - Overall accuracy (discretized)
        - Per-difficulty accuracy (discretized)
        - Experience per difficulty (discretized)
        - Current streak
        - Consecutive performance metrics
        
        This allows Q-Learning to properly distinguish between:
        - High performers (should get harder questions)
        - Struggling users (should get easier questions)

        Args:
            profile: StudentProfile instance

        Returns:
            Tuple representing the current state with performance metrics
        """
        try:
            # Get comprehensive user statistics
            stats = LevelTransitionPolicy.get_user_statistics(profile.user)
            
            # Extract overall accuracy
            overall_acc = stats.get('overall_accuracy', 0) / 100.0
            
            # Extract per-difficulty stats
            easy_stats = stats.get('difficulty_stats', {}).get('easy', {})
            medium_stats = stats.get('difficulty_stats', {}).get('medium', {})
            hard_stats = stats.get('difficulty_stats', {}).get('hard', {})
            
            # Calculate accuracies
            easy_acc = easy_stats.get('accuracy', 0) / 100.0
            medium_acc = medium_stats.get('accuracy', 0) / 100.0
            hard_acc = hard_stats.get('accuracy', 0) / 100.0
            
            # Get attempt counts (experience)
            easy_count = easy_stats.get('total', 0)
            medium_count = medium_stats.get('total', 0)
            hard_count = hard_stats.get('total', 0)
            
            # Get consecutive performance
            easy_consec_correct = easy_stats.get('consecutive_correct', 0)
            easy_consec_wrong = easy_stats.get('consecutive_wrong', 0)
            
            # Discretize accuracy to reduce state space
            # 0 = very low (<50%), 1 = low (50-69%), 2 = medium (70-89%), 3 = high (90%+)
            def discretize_accuracy(acc):
                if acc >= 0.90:
                    return 3  # High
                elif acc >= 0.70:
                    return 2  # Medium
                elif acc >= 0.50:
                    return 1  # Low
                else:
                    return 0  # Very low
            
            # Discretize experience (attempt counts)
            # 0 = none (0), 1 = beginner (1-4), 2 = intermediate (5-9), 3 = experienced (10+)
            def discretize_experience(count):
                if count == 0:
                    return 0
                elif count <= 4:
                    return 1
                elif count <= 9:
                    return 2
                else:
                    return 3
            
            # Discretize consecutive performance
            # 0 = none/mixed, 1 = some (2-3), 2 = strong (4-5), 3 = excellent (6+)
            def discretize_consecutive(count):
                if count >= 6:
                    return 3
                elif count >= 4:
                    return 2
                elif count >= 2:
                    return 1
                else:
                    return 0
            
            # Cap streak to prevent state explosion
            capped_streak = min(profile.streak_correct, 5)
            
            # Build comprehensive state tuple
            state = (
                profile.level,                              # String: beginner/intermediate/advanced/expert
                discretize_accuracy(overall_acc),           # 0-3: Overall performance
                discretize_accuracy(easy_acc),              # 0-3: Easy performance
                discretize_accuracy(medium_acc),            # 0-3: Medium performance
                discretize_accuracy(hard_acc),              # 0-3: Hard performance (for advanced tracking)
                discretize_experience(easy_count),          # 0-3: Easy experience
                discretize_experience(medium_count),        # 0-3: Medium experience
                discretize_experience(hard_count),          # 0-3: Hard experience
                capped_streak,                              # 0-5: Current streak
                discretize_consecutive(easy_consec_correct),# 0-3: Easy consecutive correct
                discretize_consecutive(easy_consec_wrong),  # 0-3: Easy consecutive wrong
            )
            
            return state
            
        except Exception as e:
            # Fallback to minimal state if error occurs
            print(f"Error creating state tuple: {e}")
            return (
                profile.level,
                1,  # Medium overall accuracy
                1,  # Medium easy accuracy
                0,  # No medium accuracy
                0,  # No hard accuracy
                1,  # Some easy experience
                0,  # No medium experience
                0,  # No hard experience
                min(profile.streak_correct, 5),
                0,  # No consecutive correct
                0   # No consecutive wrong
            )

    @staticmethod
    def pick_next_question(profile: StudentProfile, epsilon: float = None) -> Optional[Dict]:
        """
        FIXED: Pick next question respecting difficulty constraints AND anti-repetition.
        
        Now integrated with QLearningEngine.ALLOWED_ACTIONS to respect level constraints.

        Args:
            profile: StudentProfile instance
            epsilon: Not used, kept for backward compatibility

        Returns:
            Dict with question and metadata or None if no questions available
        """
        from qlearning.engine import QLearningEngine
    
        # ============================================
        # FIX: Get allowed difficulties from engine
        # ============================================
        allowed_difficulties = QLearningEngine.ALLOWED_ACTIONS.get(
            profile.level,
            ['easy', 'medium', 'hard']  # Fallback
        )
    
        print(f"\n=== QuizService.pick_next_question ===")
        print(f"User: {profile.user}, Level: {profile.level}")
        print(f"Allowed difficulties: {allowed_difficulties}")

        # Get IDs of all questions the user has attempted
        attempted_question_ids = set(AttemptLog.objects
                                   .filter(user=profile.user)
                                   .values_list('question_id', flat=True))
    
        print(f"Attempted questions: {len(attempted_question_ids)}")

        # ============================================
        # FIX: Only get questions in allowed difficulties
        # ============================================
        all_allowed_questions = list(
            Question.objects.filter(difficulty__in=allowed_difficulties)
        )
    
        if not all_allowed_questions:
            print("ERROR: No questions available in allowed difficulties!")
            return {
                'question': None,
                'is_first_attempt': False,
                'message': f'No questions available for level {profile.level}. Please contact administrator.'
            }
    
        print(f"Total questions in allowed difficulties: {len(all_allowed_questions)}")

        # Find un-attempted questions within allowed difficulties
        new_questions = [q for q in all_allowed_questions if q.id not in attempted_question_ids]
    
        print(f"Unattempted questions: {len(new_questions)}")

        if new_questions:
            # Use Q-Learning to select difficulty, then pick from that difficulty
            state_tuple = QuizService.state_tuple(profile)
        
            selected_difficulty = QLearningEngine.choose_action(
                user=profile.user,
                state_tuple=state_tuple,
                epsilon=epsilon,
                current_difficulty=profile.last_difficulty
            )
        
            print(f"Q-Learning selected difficulty: {selected_difficulty}")
        
            # Get unattempted questions in selected difficulty
            candidate_questions = [q for q in new_questions if q.difficulty == selected_difficulty]
        
            # Fallback: if no questions in selected difficulty, try other allowed difficulties
            if not candidate_questions:
                print(f"No questions in {selected_difficulty}, trying others")
            for difficulty in allowed_difficulties:
                if difficulty != selected_difficulty:
                    candidate_questions = [q for q in new_questions if q.difficulty == difficulty]
                    if candidate_questions:
                        print(f"Found {len(candidate_questions)} in {difficulty}")
                        break
        
            # Final fallback: any unattempted question
            if not candidate_questions:
                candidate_questions = new_questions
                print(f"Using any unattempted: {len(candidate_questions)}")
        
            # Select random from candidates
            question = random.choice(candidate_questions)
        
            print(f"Selected: ID={question.id}, Difficulty={question.difficulty}")
        
            return {
                'question': question,
                'is_first_attempt': True,
                'message': 'Try this new question!',
                'selected_difficulty': question.difficulty,
                'allowed_difficulties': allowed_difficulties
            }
        else:
            # All questions in allowed difficulties have been attempted
            print("All questions completed!")
            return {
                'question': None,
                'is_first_attempt': False,
                'message': f'Congratulations! You have attempted all {len(all_allowed_questions)} questions available for level {profile.level}.',
                'total_attempted': len(attempted_question_ids),
                'allowed_difficulties': allowed_difficulties
            }

    @staticmethod
    def calculate_attempt_xp(question: Question, user, is_correct: bool, time_spent: float) -> Dict:
        """
        Calculate XP reward considering question repetition and other factors.
        
        Args:
            question: Question instance
            user: User instance
            is_correct: Whether the answer was correct
            time_spent: Time spent in seconds

        Returns:
            Dict with XP breakdown and metadata
        """
        # Count previous attempts for this question by this user
        previous_attempts = AttemptLog.objects.filter(
            user=user,
            question=question
        ).count()

        # Base XP calculation
        if is_correct:
            base_reward = QuizService.BASE_CORRECT_REWARD
        else:
            base_reward = QuizService.BASE_INCORRECT_PENALTY

        # Apply repetition penalty (diminishing returns)
        if previous_attempts == 0:
            # First attempt - full XP
            repetition_multiplier = 1.0
            xp_category = "first_attempt"
        elif previous_attempts == 1:
            # Second attempt - 70% XP
            repetition_multiplier = 0.7
            xp_category = "second_attempt"
        elif previous_attempts == 2:
            # Third attempt - 50% XP
            repetition_multiplier = 0.5
            xp_category = "third_attempt"
        else:
            # Fourth+ attempts - 30% XP
            repetition_multiplier = 0.3
            xp_category = "repeated_attempt"

        # Apply difficulty multiplier
        difficulty_multiplier = {
            'easy': 1.0,
            'medium': 1.5,
            'hard': 2.0
        }.get(question.difficulty, 1.0)

        # Apply time bonus (only for first attempts)
        time_bonus = 0
        if previous_attempts == 0 and time_spent <= 60:
            time_bonus = 2.0 - (time_spent / 60.0)

        # Calculate final XP
        adjusted_base = base_reward * repetition_multiplier * difficulty_multiplier
        total_xp = adjusted_base + time_bonus

        return {
            'base_xp': base_reward,
            'repetition_multiplier': repetition_multiplier,
            'difficulty_multiplier': difficulty_multiplier,
            'time_bonus': time_bonus,
            'final_xp': round(total_xp),
            'attempt_count': previous_attempts + 1,
            'xp_category': xp_category,
            'is_first_attempt': previous_attempts == 0
        }

    @staticmethod
    def record_attempt(
        profile: StudentProfile,
        question: Question,
        chosen_answer: str,
        time_spent: float
    ) -> Dict:
        """
        Record attempt with anti-farming protection.
        Only first attempts are awarded XP and count towards progress.

        Args:
            profile: StudentProfile instance
            question: Question instance
            chosen_answer: Student's answer
            time_spent: Time spent in seconds

        Returns:
            Dict with attempt results and metadata
        """
        with transaction.atomic():
            # Determine if answer is correct
            is_correct = QuizService._validate_answer(question, chosen_answer)
            
            # Check if this is the first attempt
            previous_attempts = AttemptLog.objects.filter(
                user=profile.user,
                question=question
            )
            is_first_attempt = not previous_attempts.exists()
            
            # Calculate XP (0 for repeat attempts)
            if is_first_attempt:
                xp_info = QuizService.calculate_attempt_xp(
                    question=question,
                    user=profile.user,
                    is_correct=is_correct,
                    time_spent=time_spent
                )
                xp_earned = xp_info['final_xp']
            else:
                xp_info = {
                    'base_xp': 0,
                    'final_xp': 0,
                    'is_first_attempt': False,
                    'xp_category': 'repeat_attempt',
                    'attempt_count': previous_attempts.count() + 1,
                    'difficulty_multiplier': 1.0,
                    'time_bonus': 0,
                    'streak_bonus': 0
                }
                xp_earned = 0

            # Apply hint policy if answer was wrong
            hint = None
            if not is_correct:
                # Count previous wrong attempts for this question
                previous_wrong = previous_attempts.filter(is_correct=False).count()
                hint = QuizService._apply_hint_policy(question, is_correct, previous_wrong)

            # Create attempt log
            attempt = AttemptLog.objects.create(
                user=profile.user,
                question=question,
                chosen_answer=chosen_answer,
                is_correct=is_correct,
                difficulty_attempted=question.difficulty,
                time_spent=time_spent,
                reward_numeric=xp_earned,
                is_first_attempt=is_first_attempt,
                hint_given=hint
            )

            # Only update XP and streak for first attempts
            if is_first_attempt and xp_earned > 0:
                # Update XP
                profile.xp += xp_earned
                
                # Update streak
                if is_correct:
                    profile.streak_count += 1
                    # Apply streak bonus if threshold reached
                    if profile.streak_count % QuizService.STREAK_REWARD_THRESHOLD == 0:
                        streak_bonus = QuizService.HIDDEN_STREAK_REWARD
                        xp_info['streak_bonus'] = streak_bonus
                        profile.xp += streak_bonus
                else:
                    profile.streak_count = 0
                
                profile.save()

            # Check for level up (only for first attempts with XP earned)
            level_up = False
            new_level = profile.level
            if is_first_attempt and xp_earned > 0 and QuizService._check_level_up(profile):
                level_up = True
                new_level = profile.level

        return {
            'is_correct': is_correct,
            'xp_earned': xp_earned,
            'total_xp': profile.xp,
            'streak': profile.streak_count,
            'is_first_attempt': is_first_attempt,
            'explanation': question.explanation,
            'correct_answer': question.answer_key,
            'attempt_count': xp_info['attempt_count'],
            'level_up': level_up,
            'new_level': new_level,
            'hint': hint,
            'xp_breakdown': {
                'base_xp': xp_info.get('base_xp', 0),
                'difficulty_multiplier': xp_info.get('difficulty_multiplier', 1.0),
                'time_bonus': xp_info.get('time_bonus', 0),
                'streak_bonus': xp_info.get('streak_bonus', 0),
                'final_xp': xp_earned,
                'is_repeat': not is_first_attempt
            }
        }

    @staticmethod
    def _validate_answer(question: Question, chosen_answer: str) -> bool:
        """
        FIXED: Validate answer with proper type handling for mcq_complex.
        """
        try:
            if question.format == 'mcq_simple':
                # Simple MCQ
                if chosen_answer.strip():
                    return chosen_answer.strip() == question.answer_key.strip()
                
            elif question.format == 'mcq_complex':
                # Complex MCQ with multiple answers
                if not chosen_answer or not chosen_answer.strip():
                    return False
            
                # Parse chosen answer (JSON from frontend)
                chosen_answers = json.loads(chosen_answer)
            
                # ============================================
                # FIX: Handle answer_key type properly
                # ============================================
                answer_key = question.answer_key
            
                # Case 1: Python list (from JSONField)
                if isinstance(answer_key, list):
                    correct_answers = answer_key
                
                # Case 2: String (needs parsing)
                elif isinstance(answer_key, str):
                    answer_key_str = answer_key.strip()
                
                    if answer_key_str.startswith('[') and answer_key_str.endswith(']'):
                        # JSON array string
                        try:
                            correct_answers = json.loads(answer_key_str)
                        except json.JSONDecodeError:
                            # Manual parse
                            correct_answers = [ans.strip().strip('"\'') for ans in answer_key_str[1:-1].split(',')]
                    elif ',' in answer_key_str:
                        # Comma-separated
                        correct_answers = [ans.strip() for ans in answer_key_str.split(',')]
                    else:
                        # Single value
                        correct_answers = [answer_key_str]
                else:
                    return False
            
                # Compare sets
                return set(chosen_answers) == set(correct_answers)
            
            elif question.format == 'short_answer':
                # Short answer (case-insensitive)
                if chosen_answer.strip() and question.answer_key.strip():
                    return chosen_answer.strip().lower() == question.answer_key.strip().lower()
                
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Validation error: {e}")
            return False
    
        return False

    @staticmethod
    def _calculate_q_reward(
        is_correct: bool,
        difficulty: str,
        streak: int,
        time_spent: float
    ) -> float:
        """
        ENHANCED: Calculate Q-Learning reward with better differentiation.

        Reward structure:
        - Correct answers: Base + difficulty multiplier + streak bonus + time bonus
        - Wrong answers: Penalty (more severe for easier questions)

        Args:
            is_correct: Whether the answer was correct
            difficulty: Question difficulty
            streak: Current streak count
            time_spent: Time spent on question

        Returns:
            Calculated reward value
        """
        if is_correct:
            # Base reward
            base_reward = QuizService.BASE_CORRECT_REWARD
            
            # Difficulty multiplier (reward harder questions more)
            difficulty_multiplier = {
                'easy': 1.0,
                'medium': 1.5,    # 50% bonus for medium
                'hard': 2.0       # 100% bonus for hard
            }.get(difficulty, 1.0)
            
            # Streak bonus (diminishing returns)
            streak_bonus = min(streak * 0.5, 5.0)  # Max 5 points bonus
            
            # Time bonus (faster completion = better)
            # Reward if completed in under 60 seconds
            if time_spent <= 60:
                time_bonus = 2.0 - (time_spent / 60.0)
            else:
                time_bonus = 0
            
            return (base_reward * difficulty_multiplier) + streak_bonus + time_bonus
        else:
            # Penalty for wrong answers
            base_penalty = QuizService.BASE_INCORRECT_PENALTY
            
            # Easier questions penalized more (should have gotten it right!)
            difficulty_penalty_multiplier = {
                'easy': 1.5,      # Worse penalty for getting easy wrong
                'medium': 1.0,    # Normal penalty
                'hard': 0.7       # Lighter penalty for hard questions
            }.get(difficulty, 1.0)
            
            return base_penalty * difficulty_penalty_multiplier

    @staticmethod
    def _create_qtable_snapshot(user, state: Tuple) -> Dict:
        """
        Create a snapshot of the Q-Table for the given state.

        Args:
            user: User instance
            state: State tuple

        Returns:
            Dictionary representing Q-Table snapshot
        """
        state_hash = QLearningEngine.hash_state(state)

        # Get Q-Table entries for this state
        entries = QTableEntry.objects.filter(
            user=user,
            state_hash=state_hash
        )

        snapshot = {
            'state_hash': state_hash,
            'state': str(state),
            'timestamp': timezone.now().isoformat(),
            'q_values': {}
        }

        for entry in entries:
            snapshot['q_values'][entry.action] = {
                'q_value': entry.q_value,
                'updated_at': entry.updated_at.isoformat()
            }

        return snapshot

    @staticmethod
    def _apply_hint_policy(question: Question, is_correct: bool, streak: int) -> Optional[str]:
        """
        Apply hint policy based on question difficulty and performance.

        Args:
            question: Question instance
            is_correct: Whether the answer was correct
            streak: Current correct streak

        Returns:
            Hint text or None
        """
        # Only provide hints for wrong answers
        if is_correct:
            return None
            
        # Use the policies system for hint generation
        return LevelTransitionPolicy.get_hint_for_question(question, 0)

    @staticmethod
    def _check_level_up(profile: StudentProfile) -> bool:
        """
        Check if the user can level up based on their XP.

        Args:
            profile: StudentProfile instance

        Returns:
            Boolean indicating if level up is possible
        """
        can_level_up, target_level = LevelTransitionPolicy.can_level_up(profile)
        return can_level_up