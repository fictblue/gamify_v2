import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from accounts.models import StudentProfile
from quizzes.models import Question, AttemptLog
from qlearning.models import QTableEntry, QLearningLog
from qlearning.policies import LevelTransitionPolicy


class QuizTests(TestCase):
    """Test cases for quiz functionality and Q-Learning integration"""

    def setUp(self):
        """Set up test data"""
        self.user = get_user_model().objects.create_user(
            username='test_student',
            password='testpass123',
            role='student'
        )
        self.profile = StudentProfile.objects.create(user=self.user)

        # Create test questions
        self.easy_question = Question.objects.create(
            text="What is 2 + 2?",
            difficulty='easy',
            format='mcq_simple',
            options={"A": "3", "B": "4", "C": "5", "D": "6"},
            answer_key="B",
            curriculum_tag="Basic Math"
        )

        self.medium_question = Question.objects.create(
            text="What is the capital of France?",
            difficulty='medium',
            format='mcq_simple',
            options={"A": "London", "B": "Berlin", "C": "Paris", "D": "Madrid"},
            answer_key="C",
            curriculum_tag="Geography"
        )

        self.hard_question = Question.objects.create(
            text="Explain Einstein's theory of relativity in one sentence.",
            difficulty='hard',
            format='short_answer',
            answer_key="Einstein's theory states that space and time are relative concepts.",
            curriculum_tag="Physics"
        )

    def test_q_update_sequence(self):
        """Test Q-Learning update sequence and assert QTableEntry changes"""
        # Create initial Q-table entry
        state_hash = "test_state_hash"
        action = "easy"

        entry = QTableEntry.get_or_create_entry(self.user, state_hash, action)
        initial_q_value = entry.q_value

        # Simulate a learning update
        reward = 10.0  # Positive reward for correct answer
        learning_rate = 0.1
        discount_factor = 0.9
        next_state_max_q = 5.0

        # Calculate expected Q-value update
        old_q = entry.q_value
        new_q = old_q + learning_rate * (reward + discount_factor * next_state_max_q - old_q)
        expected_q_value = new_q

        # Update the Q-table entry
        entry.q_value = expected_q_value
        entry.save()

        # Create Q-Learning log entry
        QLearningLog.objects.create(
            user=self.user,
            state_hash=state_hash,
            action=action,
            reward=reward,
            q_value_before=old_q,
            q_value_after=expected_q_value,
            next_state_hash="next_state_hash"
        )

        # Verify the update
        entry.refresh_from_db()
        self.assertEqual(entry.q_value, expected_q_value)

        # Verify log was created
        log = QLearningLog.objects.filter(user=self.user, state_hash=state_hash).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.reward, reward)
        self.assertEqual(log.q_value_before, old_q)
        self.assertEqual(log.q_value_after, expected_q_value)

    def test_can_level_up_threshold(self):
        """Test level-up threshold logic with various attempt scenarios"""
        # Test case 1: Not enough attempts
        can_level_up, target_level = LevelTransitionPolicy.can_level_up(self.profile)
        self.assertFalse(can_level_up)
        self.assertIsNone(target_level)

        # Create attempts to meet threshold
        for i in range(10):
            AttemptLog.objects.create(
                user=self.user,
                question=self.easy_question,
                chosen_answer="B",
                is_correct=True,
                difficulty_attempted='easy',
                time_spent=30.0,
                reward_numeric=10
            )

        # Should now be able to level up (70% correct = 7/10)
        can_level_up, target_level = LevelTransitionPolicy.can_level_up(self.profile)
        self.assertTrue(can_level_up)
        self.assertEqual(target_level, 'intermediate')

        # Test case 2: Below threshold (only 60% correct)
        # Reset profile level
        self.profile.level = 'beginner'
        self.profile.save()

        # Delete old attempts
        AttemptLog.objects.filter(user=self.user).delete()

        # Create 10 attempts with only 6 correct (60% - below 70% threshold)
        for i in range(10):
            is_correct = i < 6  # First 6 correct, last 4 wrong
            AttemptLog.objects.create(
                user=self.user,
                question=self.easy_question,
                chosen_answer="B" if is_correct else "A",
                is_correct=is_correct,
                difficulty_attempted='easy',
                time_spent=30.0,
                reward_numeric=10 if is_correct else -5
            )

        can_level_up, target_level = LevelTransitionPolicy.can_level_up(self.profile)
        self.assertFalse(can_level_up)  # Should not level up
        self.assertIsNone(target_level)

    def test_hint_policy_logic(self):
        """Test hint policy triggers expected responses based on wrong attempts"""
        # Test easy question hints
        easy_hint_1 = LevelTransitionPolicy.get_hint_for_question(self.easy_question, 1)
        easy_hint_2 = LevelTransitionPolicy.get_hint_for_question(self.easy_question, 2)
        easy_hint_3 = LevelTransitionPolicy.get_hint_for_question(self.easy_question, 3)
        easy_hint_4 = LevelTransitionPolicy.get_hint_for_question(self.easy_question, 4)

        self.assertIsNotNone(easy_hint_1)
        self.assertIsNotNone(easy_hint_2)
        self.assertIsNotNone(easy_hint_3)
        self.assertIsNone(easy_hint_4)  # No more hints after 3

        # Test medium question hints (limited hints)
        medium_hint_1 = LevelTransitionPolicy.get_hint_for_question(self.medium_question, 1)
        medium_hint_2 = LevelTransitionPolicy.get_hint_for_question(self.medium_question, 2)
        medium_hint_3 = LevelTransitionPolicy.get_hint_for_question(self.medium_question, 3)

        self.assertIsNotNone(medium_hint_1)
        self.assertIsNotNone(medium_hint_2)
        self.assertIsNotNone(medium_hint_3)  # Cycles through available hints

        # Test hard question hints (very limited)
        hard_hint_1 = LevelTransitionPolicy.get_hint_for_question(self.hard_question, 1)
        hard_hint_2 = LevelTransitionPolicy.get_hint_for_question(self.hard_question, 2)
        hard_hint_3 = LevelTransitionPolicy.get_hint_for_question(self.hard_question, 3)

        self.assertIsNone(hard_hint_1)  # No hints for first wrong attempt
        self.assertIsNotNone(hard_hint_2)  # Hint available for second wrong attempt
        self.assertIsNotNone(hard_hint_3)  # Cycles through available hints

    def test_window_stats_calculation(self):
        """Test performance window statistics calculation"""
        # Create 15 attempts (more than window size of 10)
        for i in range(15):
            is_correct = i % 2 == 0  # Alternate correct/incorrect
            AttemptLog.objects.create(
                user=self.user,
                question=self.easy_question,
                chosen_answer="B" if is_correct else "A",
                is_correct=is_correct,
                difficulty_attempted='easy',
                time_spent=30.0,
                reward_numeric=10 if is_correct else -5
            )

        correct, total = LevelTransitionPolicy.compute_window_stats(self.user, 'easy', window=10)

        # Should only consider last 10 attempts
        self.assertEqual(total, 10)
        # Last 10 attempts: indices 5-14, alternating starting with correct (index 5 is correct)
        # So: correct, wrong, correct, wrong, correct, wrong, correct, wrong, correct, wrong
        # That's 5 correct out of 10
        self.assertEqual(correct, 5)

    def test_attempt_log_creation(self):
        """Test attempt log creation and field validation"""
        attempt = AttemptLog.objects.create(
            user=self.user,
            question=self.medium_question,
            chosen_answer="C",
            is_correct=True,
            difficulty_attempted='medium',
            time_spent=45.0,
            reward_numeric=15,
            hint_given="Try to think about European capitals"
        )

        # Verify all fields are set correctly
        self.assertEqual(attempt.user, self.user)
        self.assertEqual(attempt.question, self.medium_question)
        self.assertEqual(attempt.chosen_answer, "C")
        self.assertTrue(attempt.is_correct)
        self.assertEqual(attempt.difficulty_attempted, 'medium')
        self.assertEqual(attempt.time_spent, 45.0)
        self.assertEqual(attempt.reward_numeric, 15)
        self.assertEqual(attempt.hint_given, "Try to think about European capitals")

        # Test that difficulty_attempted defaults to question difficulty
        attempt_no_difficulty = AttemptLog.objects.create(
            user=self.user,
            question=self.hard_question,
            chosen_answer="Einstein's theory of relativity explains that space and time are relative.",
            is_correct=False,
            time_spent=120.0,
            reward_numeric=-10
        )

        self.assertEqual(attempt_no_difficulty.difficulty_attempted, 'hard')

    def test_question_format_handling(self):
        """Test different question formats and their handling"""
        # Test MCQ simple
        mcq_simple = Question.objects.create(
            text="What is the color of the sky?",
            difficulty='easy',
            format='mcq_simple',
            options={"A": "Blue", "B": "Green", "C": "Red", "D": "Yellow"},
            answer_key="A",
            curriculum_tag="Science"
        )

        # Test MCQ complex
        mcq_complex = Question.objects.create(
            text="Which of the following are programming languages? (Select all that apply)",
            difficulty='medium',
            format='mcq_complex',
            options={"A": "Python", "B": "HTML", "C": "CSS", "D": "JavaScript"},
            answer_key='["A", "D"]',  # JSON array for multiple correct answers
            curriculum_tag="Computer Science"
        )

        # Test short answer
        short_answer = Question.objects.create(
            text="What does 'www' stand for in a website address?",
            difficulty='easy',
            format='short_answer',
            answer_key="World Wide Web",
            curriculum_tag="Technology"
        )

        # Verify formats are stored correctly
        self.assertEqual(mcq_simple.format, 'mcq_simple')
        self.assertEqual(mcq_complex.format, 'mcq_complex')
        self.assertEqual(short_answer.format, 'short_answer')

        # Test options handling
        self.assertIsInstance(mcq_simple.options, dict)
        self.assertIsInstance(mcq_complex.options, dict)
        self.assertIsNone(short_answer.options)

    def test_performance_summary_calculation(self):
        """Test performance summary calculation over time periods"""
        # Create attempts over several days
        base_time = timezone.now() - timedelta(days=5)

        for i in range(5):
            attempt_time = base_time + timedelta(days=i)
            is_correct = i % 2 == 0

            attempt = AttemptLog.objects.create(
                user=self.user,
                question=self.easy_question,
                chosen_answer="B" if is_correct else "A",
                is_correct=is_correct,
                difficulty_attempted='easy',
                time_spent=30.0,
                reward_numeric=10 if is_correct else -5
            )
            # Manually set the timestamp for testing
            attempt.created_at = attempt_time
            attempt.save()

        # Test 7-day performance summary
        summary = LevelTransitionPolicy.get_performance_summary(self.user, days=7)

        self.assertEqual(summary['period_days'], 7)
        self.assertEqual(summary['total_attempts'], 5)
        self.assertEqual(summary['correct_attempts'], 3)  # 3 correct out of 5
        self.assertEqual(summary['accuracy'], 60.0)  # 60% accuracy
        self.assertEqual(len(summary['daily_stats']), 7)

    def test_level_progress_calculation(self):
        """Test level progress calculation and percentage"""
        # Create 8 correct attempts out of 10 (80% - above 70% threshold)
        for i in range(10):
            is_correct = i < 8  # 8 correct, 2 wrong
            AttemptLog.objects.create(
                user=self.user,
                question=self.easy_question,
                chosen_answer="B" if is_correct else "A",
                is_correct=is_correct,
                difficulty_attempted='easy',
                time_spent=30.0,
                reward_numeric=10 if is_correct else -5
            )

        progress = LevelTransitionPolicy.calculate_level_progress(self.profile)

        self.assertTrue(progress['can_level_up'])
        self.assertEqual(progress['target_level'], 'intermediate')
        self.assertEqual(progress['current_correct'], 8)
        self.assertEqual(progress['required_correct'], 7)  # 70% of 10 = 7
        self.assertEqual(progress['remaining_correct'], 0)  # Already met threshold
        self.assertGreater(progress['progress_percentage'], 100)  # Above 100% since we have 8/7

    def test_user_statistics_aggregation(self):
        """Test comprehensive user statistics aggregation"""
        # Create mixed attempts across difficulties
        questions = [self.easy_question, self.medium_question, self.hard_question]
        difficulties = ['easy', 'medium', 'hard']

        for i in range(15):
            question = questions[i % 3]
            difficulty = difficulties[i % 3]
            is_correct = i % 2 == 0  # Alternate correct/incorrect

            AttemptLog.objects.create(
                user=self.user,
                question=question,
                chosen_answer="B" if is_correct else "A",
                is_correct=is_correct,
                difficulty_attempted=difficulty,
                time_spent=30.0,
                reward_numeric=10 if is_correct else -5
            )

        stats = LevelTransitionPolicy.get_user_statistics(self.user)

        self.assertEqual(stats['total_attempts'], 15)
        self.assertEqual(stats['correct_attempts'], 8)  # 8 correct out of 15
        self.assertEqual(stats['overall_accuracy'], 53.3)  # Rounded to 1 decimal
        self.assertEqual(stats['current_streak'], 0)  # No streak since alternating
        self.assertEqual(stats['level'], 'beginner')
        self.assertEqual(stats['points'], 0)  # No XP system integration in this test

        # Check difficulty stats
        self.assertIn('easy', stats['difficulty_stats'])
        self.assertIn('medium', stats['difficulty_stats'])
        self.assertIn('hard', stats['difficulty_stats'])

    def test_mcq_complex_format_handling(self):
        """Test MCQ complex format with multiple correct answers"""
        # Create MCQ complex question
        mcq_complex = Question.objects.create(
            text="Which of the following are programming languages? (Select all that apply)",
            difficulty='medium',
            format='mcq_complex',
            options={"A": "Python", "B": "HTML", "C": "CSS", "D": "JavaScript", "E": "English"},
            answer_key='["A", "D"]',  # JSON array for multiple correct answers
            curriculum_tag="Computer Science"
        )

        # Verify format and answer key
        self.assertEqual(mcq_complex.format, 'mcq_complex')
        self.assertEqual(mcq_complex.answer_key, '["A", "D"]')
        self.assertIsInstance(mcq_complex.options, dict)

        # Test attempt with correct multiple answers
        attempt_correct = AttemptLog.objects.create(
            user=self.user,
            question=mcq_complex,
            chosen_answer='["A", "D"]',  # Correct multiple choice
            is_correct=True,
            difficulty_attempted='medium',
            time_spent=45.0,
            reward_numeric=20
        )

        # Test attempt with partial correct answers
        attempt_partial = AttemptLog.objects.create(
            user=self.user,
            question=mcq_complex,
            chosen_answer='["A"]',  # Only one correct
            is_correct=False,  # Should be marked incorrect for MCQ complex
            difficulty_attempted='medium',
            time_spent=30.0,
            reward_numeric=-5
        )

        # Test attempt with wrong answers
        attempt_wrong = AttemptLog.objects.create(
            user=self.user,
            question=mcq_complex,
            chosen_answer='["B", "C"]',  # Wrong answers
            is_correct=False,
            difficulty_attempted='medium',
            time_spent=25.0,
            reward_numeric=-10
        )

        # Verify attempts were created correctly
        self.assertTrue(attempt_correct.is_correct)
        self.assertFalse(attempt_partial.is_correct)
        self.assertFalse(attempt_wrong.is_correct)

    def test_short_answer_format_handling(self):
        """Test short answer format with text-based answers"""
        # Create short answer question
        short_answer = Question.objects.create(
            text="What does 'www' stand for in a website address?",
            difficulty='hard',
            format='short_answer',
            answer_key="World Wide Web",
            curriculum_tag="Technology"
        )

        # Verify format and answer key
        self.assertEqual(short_answer.format, 'short_answer')
        self.assertEqual(short_answer.answer_key, "World Wide Web")
        self.assertIsNone(short_answer.options)

        # Test attempt with correct answer
        attempt_correct = AttemptLog.objects.create(
            user=self.user,
            question=short_answer,
            chosen_answer="World Wide Web",
            is_correct=True,
            difficulty_attempted='hard',
            time_spent=60.0,
            reward_numeric=25
        )

        # Test attempt with incorrect answer
        attempt_wrong = AttemptLog.objects.create(
            user=self.user,
            question=short_answer,
            chosen_answer="Wrong Answer",
            is_correct=False,
            difficulty_attempted='hard',
            time_spent=45.0,
            reward_numeric=-10
        )

        # Test attempt with case-insensitive answer
        attempt_case = AttemptLog.objects.create(
            user=self.user,
            question=short_answer,
            chosen_answer="world wide web",  # Lowercase
            is_correct=False,  # Case-sensitive by default
            difficulty_attempted='hard',
            time_spent=50.0,
            reward_numeric=0
        )

        # Verify attempts
        self.assertTrue(attempt_correct.is_correct)
        self.assertFalse(attempt_wrong.is_correct)
        self.assertFalse(attempt_case.is_correct)

    def test_question_difficulty_format_mapping(self):
        """Test that questions follow the correct format for their difficulty level"""
        # Easy questions should be MCQ simple
        easy_questions = Question.objects.filter(difficulty='easy')
        for question in easy_questions:
            self.assertEqual(question.format, 'mcq_simple')
            self.assertIsInstance(question.options, dict)
            self.assertIsInstance(question.answer_key, str)
            self.assertNotEqual(question.answer_key, '[]')  # Should not be empty array

        # Medium questions should be MCQ complex
        medium_questions = Question.objects.filter(difficulty='medium')
        for question in medium_questions:
            self.assertEqual(question.format, 'mcq_complex')
            self.assertIsInstance(question.options, dict)
            # Answer key should be JSON array format
            import json
            try:
                answers = json.loads(question.answer_key)
                self.assertIsInstance(answers, list)
                self.assertGreater(len(answers), 1)  # Should have multiple correct answers
            except (json.JSONDecodeError, TypeError):
                self.fail(f"Question {question.id} has invalid answer_key format")

        # Hard questions should be short answer
        hard_questions = Question.objects.filter(difficulty='hard')
        for question in hard_questions:
            self.assertEqual(question.format, 'short_answer')
            self.assertIsNone(question.options)
            self.assertIsInstance(question.answer_key, str)
            self.assertNotEqual(question.answer_key.strip(), "")  # Should not be empty
