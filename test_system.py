#!/usr/bin/env python
"""
Automated Testing Script for GamifyLearn Q-Learning System
Run this script to validate core functionality before expert review.

Usage: python test_system.py
"""

import os
import sys
import django
from datetime import timedelta

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamify_ai.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from accounts.models import StudentProfile
from quizzes.models import Question, AttemptLog
from qlearning.models import QTableEntry, UserEngagementLog
from django.utils import timezone


def test_user_registration():
    """Test user registration and automatic activation"""
    print("🧪 Testing User Registration...")

    client = Client()

    # Test registration
    response = client.post('/accounts/register/', {
        'username': 'testuser_' + str(timezone.now().timestamp()),
        'email': 'test@example.com',
        'password1': 'testpass123',
        'password2': 'testpass123',
        'role': 'student',
        'terms_accepted': True
    })

    if response.status_code in [200, 302]:  # Success or redirect
        print("✅ User registration successful")

        # Check if user was created and is active
        users = User.objects.filter(username__startswith='testuser_')
        if users.exists():
            user = users.first()
            if user.is_active:
                print("✅ User is active immediately")
            else:
                print("❌ User is not active")
                return False

            # Check if profile was created
            if hasattr(user, 'student_profile'):
                print("✅ Student profile created automatically")
                return True
            else:
                print("❌ Student profile not created")
                return False
        else:
            print("❌ User not found in database")
            return False
    else:
        print(f"❌ Registration failed: {response.status_code}")
        return False


def test_qlearning_logs():
    """Test Q-Learning logging functionality"""
    print("🧪 Testing Q-Learning Logs...")

    # Check if backfill data exists
    log_counts = {
        'UserEngagementLog': UserEngagementLog.objects.count(),
        'QTableEntry': QTableEntry.objects.count(),
        'AttemptLog': AttemptLog.objects.count(),
    }

    all_good = True
    for model, count in log_counts.items():
        if count > 0:
            print(f"✅ {model}: {count} entries")
        else:
            print(f"❌ {model}: No entries found")
            all_good = False

    return all_good


def test_level_progression():
    """Test level progression mechanics"""
    print("🧪 Testing Level Progression...")

    # Test XP thresholds
    thresholds = {
        'beginner': 200,
        'intermediate': 500,
        'advanced': 800,
        'expert': 1000
    }

    profile = StudentProfile.objects.filter(level='beginner').first()
    if profile:
        print("✅ Found beginner profile for testing")

        # Test level calculation
        current_xp = profile.xp
        current_level = profile.level

        print(f"✅ Current: Level {current_level}, XP {current_xp}")

        # Test XP for next level
        xp_for_next = profile.get_xp_for_next_level()
        print(f"✅ XP needed for next level: {xp_for_next}")

        return True
    else:
        print("❌ No beginner profile found for testing")
        return False


def test_admin_access():
    """Test admin panel accessibility"""
    print("🧪 Testing Admin Access...")

    # Check if admin user exists
    admin_users = User.objects.filter(role='admin')
    if admin_users.exists():
        print(f"✅ Admin users found: {admin_users.count()}")

        # Test admin dashboard access
        client = Client()
        admin_user = admin_users.first()

        # Login as admin
        client.login(username=admin_user.username, password='admin123')
        response = client.get('/admin/')

        if response.status_code == 200:
            print("✅ Admin dashboard accessible")
            return True
        else:
            print(f"❌ Admin dashboard not accessible: {response.status_code}")
            return False
    else:
        print("❌ No admin users found")
        return False


def test_system_health():
    """Test overall system health"""
    print("🧪 Testing System Health...")

    health_checks = [
        ('Users', User.objects.count()),
        ('Questions', Question.objects.count()),
        ('Student Profiles', StudentProfile.objects.count()),
        ('Q-Table Entries', QTableEntry.objects.count()),
        ('Engagement Logs', UserEngagementLog.objects.count()),
    ]

    all_healthy = True
    for name, count in health_checks:
        if count > 0:
            print(f"✅ {name}: {count}")
        else:
            print(f"⚠️ {name}: {count} (empty)")
            all_healthy = False

    return all_healthy


def run_all_tests():
    """Run all automated tests"""
    print("🚀 GamifyLearn Automated Testing Suite")
    print("=" * 50)

    tests = [
        ("System Health", test_system_health),
        ("User Registration", test_user_registration),
        ("Q-Learning Logs", test_qlearning_logs),
        ("Level Progression", test_level_progression),
        ("Admin Access", test_admin_access),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🔬 Running: {test_name}")
        print("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1

    print(f"\n📈 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! System ready for expert review.")
        return True
    else:
        print("⚠️ Some tests failed. Review issues before proceeding.")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
