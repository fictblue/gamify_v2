import os
import django
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from quizzes.models import Question, AttemptLog
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamify.settings')
django.setup()

class TestQuestionRepetition(TestCase):
    def setUp(self):
        # Create test user
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Create 50 easy, 50 medium, and 50 hard questions
        self.questions = []
        for i in range(150):
            difficulty = 'easy' if i < 50 else 'medium' if i < 100 else 'hard'
            question = Question.objects.create(
                text=f'Test Question {i+1}',
                difficulty=difficulty,
                answer_key='A' if i % 2 == 0 else 'B',
                format='mcq_simple',
                created_at=timezone.now()
            )
            self.questions.append(question)
        
        # Create initial attempt log to simulate a session
        self.initial_attempt = AttemptLog.objects.create(
            user=self.user,
            question=self.questions[0],
            is_correct=True,
            difficulty_attempted='easy',
            time_spent=10.5,
            reward_numeric=10
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_question_repetition(self):
        """Test that questions don't repeat in a session"""
        seen_questions = set()
        total_questions = 20  # Test with 20 questions
        
        for i in range(total_questions):
            try:
                # Get next question (using the first available question not yet attempted)
                attempted_ids = AttemptLog.objects.filter(
                    user=self.user
                ).values_list('question_id', flat=True)
                
                # Get a question not yet attempted
                question = Question.objects.exclude(id__in=attempted_ids).first()
                
                # If all questions have been attempted, reset by removing the oldest attempt
                if not question:
                    # Remove the oldest attempt
                    AttemptLog.objects.filter(
                        user=self.user
                    ).order_by('created_at').first().delete()
                    question = Question.objects.exclude(id__in=attempted_ids).first()
                
                self.assertIsNotNone(question, "Should always have a question to return")
                question_id = question.id
                
                # Check for repetition
                self.assertNotIn(question_id, seen_questions, 
                               f"Question ID {question_id} was repeated in the same session!")
                
                seen_questions.add(question_id)
                
                print(f"Processing question {i+1}/{total_questions}: ID {question_id}")
                
                # Create a new attempt log
                AttemptLog.objects.create(
                    user=self.user,
                    question=question,
                    is_correct=True,
                    difficulty_attempted=question.difficulty,
                    time_spent=10.5,
                    reward_numeric=10,
                    created_at=timezone.now()
                )
                
            except Exception as e:
                self.fail(f"Unexpected error on iteration {i+1}: {str(e)}")
        
        print(f"\nTest completed. Processed {len(seen_questions)} unique questions without repetition.")
        print(f"Questions processed: {sorted(seen_questions)}")
        
        # Verify all questions were unique
        self.assertEqual(len(seen_questions), total_questions, 
                        f"Expected {total_questions} unique questions, got {len(seen_questions)}")
        
        print("\nTest completed successfully with no question repetitions.")
