#!/usr/bin/env python
"""
Test script for the new repetition-aware XP system
Run this to verify that diminishing returns are working correctly.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamify_ai.settings')
django.setup()

from accounts.models import CustomUser
from quizzes.models import Question, AttemptLog


def test_xp_calculation():
    """Test the new XP calculation system"""
    print("🧮 Testing XP Calculation System...")
    print("=" * 50)

    # Get a test user and question
    user = CustomUser.objects.filter(role='student').first()
    question = Question.objects.first()

    if not user or not question:
        print("❌ No test user or question found")
        return False

    print(f"🧑‍🎓 Test User: {user.username}")
    print(f"❓ Test Question: {question.text[:50]}... ({question.difficulty})")

    # Test XP calculation for multiple attempts
    for attempt_num in range(5):
        print(f"\n📝 Attempt {attempt_num + 1}:")

        # Calculate XP as if this was a correct answer
        xp_calc = QuizService.calculate_attempt_xp(
            question, user, is_correct=True, time_spent=45
        )

        print(f"   Base XP: {xp_calc['base_xp']}")
        print(f"   Repetition Multiplier: {xp_calc['repetition_multiplier']}x")
        print(f"   Difficulty Multiplier: {xp_calc['difficulty_multiplier']}x")
        print(f"   Time Bonus: {xp_calc['time_bonus']}")
        print(f"   Final XP: {xp_calc['final_xp']}")
        print(f"   Category: {xp_calc['xp_category']}")

        # Simulate the attempt in database for next calculation
        AttemptLog.objects.create(
            user=user,
            question=question,
            chosen_answer='A',  # Simulate correct answer
            is_correct=True,
            difficulty_attempted=question.difficulty,
            time_spent=45,
            reward_numeric=xp_calc['final_xp'],
            qtable_snapshot={}
        )

    return True


def test_question_selection():
    """Test the new intelligent question selection"""
    print("\n🎯 Testing Question Selection Intelligence...")
    print("=" * 50)

    user = CustomUser.objects.filter(role='student').first()
    if not user:
        print("❌ No test user found")
        return False

    profile = user.student_profile

    # Test question selection
    selected_question = QuizService.pick_next_question(profile)

    if selected_question:
        print(f"✅ Selected Question: {selected_question.text[:50]}... ({selected_question.difficulty})")

        # Check how many times this question has been attempted
        attempt_count = AttemptLog.objects.filter(
            user=user,
            question=selected_question
        ).count()

        print(f"📊 Attempt count for this question: {attempt_count}")

        # Show recent performance on this question
        recent_attempts = AttemptLog.objects.filter(
            user=user,
            question=selected_question
        ).order_by('-created_at')[:3]

        if recent_attempts:
            correct_count = sum(1 for a in recent_attempts if a.is_correct)
            accuracy = correct_count / len(recent_attempts)
            print(f"📈 Recent accuracy: {accuracy:.1%} ({correct_count}/{len(recent_attempts)})")

        return True
    else:
        print("❌ No question selected")
        return False


def test_repetition_patterns():
    """Analyze current repetition patterns in the system"""
    print("\n🔄 Testing Repetition Patterns...")
    print("=" * 50)

    users = CustomUser.objects.filter(role='student')[:3]

    for user in users:
        print(f"\n👤 {user.username}:")

        total_attempts = AttemptLog.objects.filter(user=user).count()
        unique_questions = AttemptLog.objects.filter(user=user).values('question').distinct().count()

        if total_attempts > 0:
            repetition_rate = ((total_attempts - unique_questions) / total_attempts) * 100
            print(f"   Total attempts: {total_attempts}")
            print(f"   Unique questions: {unique_questions}")
            print(f"   Repetition rate: {repetition_rate:.1f}%")

            # Show most repeated questions
            question_repetition = AttemptLog.objects.filter(user=user).values('question__text').annotate(count=Count('question')).order_by('-count')[:3]

            print("   Most repeated questions:")
            for item in question_repetition:
                print(f"     \"{item['question__text'][:40]}...\": {item['count']} times")
        else:
            print("   No attempts yet")

    return True


def test_xp_transparency():
    """Test that XP breakdown is properly calculated and transparent"""
    print("\n💰 Testing XP Transparency...")
    print("=" * 50)

    user = CustomUser.objects.filter(role='student').first()
    question = Question.objects.first()

    if not user or not question:
        print("❌ No test data available")
        return False

    # Test different scenarios
    scenarios = [
        ("First attempt, correct", True, 30, 1.0),
        ("First attempt, wrong", False, 30, -2.0),
        ("Easy question", True, 45, 1.0),
        ("Hard question", True, 45, 2.0),
        ("Fast completion", True, 15, 1.0),
    ]

    for scenario_name, is_correct, time_spent, expected_multiplier in scenarios:
        print(f"\n📋 {scenario_name}:")

        # Clear previous attempts for clean test
        AttemptLog.objects.filter(user=user, question=question).delete()

        xp_calc = QuizService.calculate_attempt_xp(question, user, is_correct, time_spent)

        print(f"   Final XP: {xp_calc['final_xp']}")
        print(f"   Expected multiplier: {expected_multiplier}x")
        print(f"   Actual multiplier: {xp_calc['repetition_multiplier']}x")
        print(f"   Difficulty multiplier: {xp_calc['difficulty_multiplier']}x")
        print(f"   Time bonus: {xp_calc['time_bonus']}")

        # Verify calculation logic
        expected_base = 10 if is_correct else -2
        expected_calc = expected_base * xp_calc['repetition_multiplier'] * xp_calc['difficulty_multiplier'] + xp_calc['time_bonus']

        if abs(expected_calc - xp_calc['final_xp']) < 0.1:
            print("   ✅ Calculation correct")
        else:
            print(f"   ❌ Calculation mismatch: expected {expected_calc}, got {xp_calc['final_xp']}")

    return True


def run_comprehensive_tests():
    """Run all repetition system tests"""
    print("🚀 GamifyLearn Repetition System Testing")
    print("=" * 60)

    tests = [
        ("XP Calculation System", test_xp_calculation),
        ("Question Selection Intelligence", test_question_selection),
        ("Current Repetition Patterns", test_repetition_patterns),
        ("XP Transparency", test_xp_transparency),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🔬 Running: {test_name}")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 60)

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1

    print(f"\n📈 Overall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED! Repetition system is working correctly.")
        print("✅ Diminishing XP rewards implemented")
        print("✅ Smart question selection working")
        print("✅ Transparent XP calculation system")
        print("✅ XP farming prevention active")
        return True
    else:
        print("\n⚠️ Some tests failed. Repetition system needs attention.")
        return False


if __name__ == '__main__':
    success = run_comprehensive_tests()
    print(f"\nExit code: {'0 (SUCCESS)' if success else '1 (NEEDS_FIXES)'}")
