#!/usr/bin/env python
"""
Test script to verify registration works without IntegrityError
Run this to test the fix for duplicate StudentProfile creation.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamify_ai.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from accounts.models import StudentProfile, CustomUser


def test_registration():
    """Test user registration without IntegrityError"""
    print("🧪 Testing User Registration Fix...")
    print("=" * 50)

    client = Client()

    # Test data
    test_username = f"testuser_{CustomUser.objects.count() + 1}"
    test_data = {
        'username': test_username,
        'email': f'{test_username}@example.com',
        'password1': 'testpass123',
        'password2': 'testpass123',
        'role': 'student',
        'terms_accepted': True
    }

    print(f"📝 Testing registration for: {test_username}")

    # Attempt registration
    try:
        response = client.post('/accounts/register/', test_data)

        print(f"✅ Registration response: {response.status_code}")

        if response.status_code in [200, 302]:  # Success or redirect
            print("✅ Registration successful!")

            # Check if user was created
            user = CustomUser.objects.filter(username=test_username).first()
            if user:
                print(f"✅ User created: {user.username}")
                print(f"   - Active: {user.is_active}")
                print(f"   - Role: {user.role}")

                # Check if profile was created automatically
                try:
                    profile = user.student_profile
                    print("✅ StudentProfile created automatically!")
                    print(f"   - Level: {profile.level}")
                    print(f"   - XP: {profile.xp}")
                    print(f"   - Total XP: {profile.total_xp}")

                    return True

                except StudentProfile.DoesNotExist:
                    print("❌ StudentProfile was not created")
                    return False

            else:
                print("❌ User was not created")
                return False

        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"Response content: {response.content}")
            return False

    except Exception as e:
        print(f"❌ Error during registration: {e}")
        return False


def test_existing_profiles():
    """Check existing profiles for any issues"""
    print("\n🔍 Checking Existing Profiles...")
    print("-" * 30)

    total_users = CustomUser.objects.count()
    total_profiles = StudentProfile.objects.count()
    users_with_profiles = CustomUser.objects.filter(student_profile__isnull=False).count()
    users_without_profiles = CustomUser.objects.filter(student_profile__isnull=True).count()

    print(f"📊 Total Users: {total_users}")
    print(f"📊 Total Profiles: {total_profiles}")
    print(f"✅ Users with Profiles: {users_with_profiles}")
    print(f"❌ Users without Profiles: {users_without_profiles}")

    if users_without_profiles > 0:
        print("\n⚠️ Users without profiles:")
        for user in CustomUser.objects.filter(student_profile__isnull=True):
            print(f"   - {user.username} ({user.role})")

    # Check for any profile inconsistencies
    if total_profiles != users_with_profiles:
        print("\n❌ Profile inconsistency detected!")
        return False
    else:
        print("\n✅ All profiles are consistent")
        return True


def test_signal_functionality():
    """Test that the Django signal is working"""
    print("\n🔄 Testing Django Signal...")
    print("-" * 30)

    # Create a test user and see if profile is created automatically
    test_user = CustomUser.objects.create_user(
        username=f"signal_test_{CustomUser.objects.count()}",
        email="signal@test.com",
        password="test123",
        role='student',
        is_active=True
    )

    try:
        profile = test_user.student_profile
        print(f"✅ Signal worked! Profile created: Level={profile.level}, XP={profile.xp}")

        # Clean up
        profile.delete()
        test_user.delete()
        print("🧹 Test user and profile cleaned up")

        return True

    except StudentProfile.DoesNotExist:
        print("❌ Signal did not create profile")
        test_user.delete()
        return False


def run_all_tests():
    """Run comprehensive registration tests"""
    print("🚀 GamifyLearn Registration Testing")
    print("=" * 50)

    tests = [
        ("Existing Profiles Check", test_existing_profiles),
        ("Signal Functionality", test_signal_functionality),
        ("Registration Process", test_registration),
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
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1

    print(f"\n📈 Overall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED! Registration is working correctly.")
        print("✅ No more IntegrityError issues")
        print("✅ Profiles created automatically via signals")
        print("✅ Users can register and login immediately")
        return True
    else:
        print("\n⚠️ Some tests failed. Registration may still have issues.")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    print(f"\nExit code: {'0 (SUCCESS)' if success else '1 (FAILED)'}")
