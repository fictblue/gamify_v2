#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.insert(0, r'c:\Users\TOUCH U\Videos\gamify_v2')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamify_ai.settings')
django.setup()

from django.db.models import Count
from accounts.models import CustomUser
from quizzes.models import Question, AttemptLog

print('🔍 ANALYZING REPETITION SYSTEM FROM LOGS')
print('=' * 50)

# Get student6 data
try:
    user = CustomUser.objects.get(username='student6')
    print(f'👤 User: {user.username} (Level: {user.student_profile.level})')

    # Analyze beginner attempts
    beginner_attempts = AttemptLog.objects.filter(
        user=user,
        difficulty_attempted='easy'
    ).order_by('created_at')[:15]

    print(f'\n📊 BEGINNER ATTEMPTS (First 15):')
    print('Question | XP | Time | Correct')
    print('-' * 40)

    for attempt in beginner_attempts:
        print(f'{attempt.question.text[:45]}... | {attempt.reward_numeric} | {attempt.time_spent}s | {attempt.is_correct}')

    # Analyze repetition patterns
    print(f'\n🔄 REPETITION ANALYSIS:')
    questions = AttemptLog.objects.filter(user=user).values('question__text').annotate(count=Count('question')).order_by('-count')
    print('Question | Times Seen | Last XP')
    print('-' * 40)

    for q in questions[:10]:
        last_attempt = AttemptLog.objects.filter(user=user, question__text=q['question__text']).order_by('-created_at').first()
        print(f'{q["question__text"][:40]}... | {q["count"]} times | {last_attempt.reward_numeric} XP')

    print(f'\n✅ Total unique questions: {len(questions)}')
    print(f'✅ Total attempts: {AttemptLog.objects.filter(user=user).count()}')

    # Check if XP is varying for same questions
    print(f'\n💰 XP VARIATION ANALYSIS:')
    same_question_attempts = AttemptLog.objects.filter(user=user).values('question__text', 'reward_numeric').order_by('question__text', 'created_at')

    current_question = None
    question_xps = []

    for attempt in same_question_attempts:
        if current_question != attempt['question__text']:
            if question_xps:
                if len(set(question_xps)) > 1:  # Different XP values for same question
                    print(f'✅ {current_question[:40]}... had varying XP: {question_xps}')
                else:
                    print(f'❌ {current_question[:40]}... had constant XP: {question_xps}')
            current_question = attempt['question__text']
            question_xps = [attempt['reward_numeric']]
        else:
            question_xps.append(attempt['reward_numeric'])

    # Final one
    if question_xps and len(set(question_xps)) > 1:
        print(f'✅ {current_question[:40]}... had varying XP: {question_xps}')

except Exception as e:
    print(f'❌ Error: {e}')
    print('Available users:')
    for u in CustomUser.objects.filter(role='student')[:5]:
        print(f'  - {u.username}')
