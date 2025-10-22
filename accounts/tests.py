from django.test import TestCase
from django.contrib.auth import get_user_model

from accounts.models import CustomUser, StudentProfile


class StudentProfileTests(TestCase):
    """Test cases for StudentProfile model and XP system"""

    def setUp(self):
        """Set up test data"""
        self.user = get_user_model().objects.create_user(
            username='test_student',
            password='testpass123',
            role='student'
        )
        # Create profile only if it doesn't exist
        try:
            self.profile = StudentProfile.objects.get(user=self.user)
        except StudentProfile.DoesNotExist:
            self.profile = StudentProfile.objects.create(user=self.user)

    def test_profile_creation(self):
        """Test that student profile is created correctly"""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.level, 'beginner')
        self.assertEqual(self.profile.xp, 0)
        self.assertEqual(self.profile.total_xp, 0)
        self.assertEqual(self.profile.points, 0)
        self.assertEqual(self.profile.streak_correct, 0)
        self.assertEqual(self.profile.progress, 0)
        self.assertEqual(self.profile.last_difficulty, 'easy')

    def test_xp_for_next_level_calculation(self):
        """Test XP requirements for different levels"""
        # Beginner to intermediate: 100 XP
        self.assertEqual(self.profile.get_xp_for_next_level(), 100)

        # Set to intermediate
        self.profile.level = 'intermediate'
        self.assertEqual(self.profile.get_xp_for_next_level(), 300)

        # Set to advanced
        self.profile.level = 'advanced'
        self.assertEqual(self.profile.get_xp_for_next_level(), 500)

        # Set to expert (max level)
        self.profile.level = 'expert'
        self.assertEqual(self.profile.get_xp_for_next_level(), 1000)

    def test_xp_progress_percentage(self):
        """Test XP progress percentage calculation"""
        # No XP yet
        self.assertEqual(self.profile.get_xp_progress_percentage(), 0)

        # Add some XP
        self.profile.xp = 50
        self.assertEqual(self.profile.get_xp_progress_percentage(), 50.0)  # 50/100 = 50%

        # Add more XP
        self.profile.xp = 75
        self.assertEqual(self.profile.get_xp_progress_percentage(), 75.0)  # 75/100 = 75%

        # Test with different level
        self.profile.level = 'intermediate'
        self.profile.xp = 150
        self.assertEqual(self.profile.get_xp_progress_percentage(), 50.0)  # 150/300 = 50%

        # Test max level
        self.profile.level = 'expert'
        self.profile.xp = 1000
        self.assertEqual(self.profile.get_xp_progress_percentage(), 100.0)  # 1000/1000 = 100%

    def test_can_level_up_logic(self):
        """Test level-up eligibility logic"""
        # Not enough XP
        self.assertFalse(self.profile.can_level_up())

        # Add exactly 100 XP (threshold for beginner to intermediate)
        self.profile.xp = 100
        self.assertTrue(self.profile.can_level_up())

        # Add more XP
        self.profile.xp = 150
        self.assertTrue(self.profile.can_level_up())

        # Test intermediate level
        self.profile.level = 'intermediate'
        self.profile.xp = 299  # Below 300 threshold
        self.assertFalse(self.profile.can_level_up())

        self.profile.xp = 300  # At threshold
        self.assertTrue(self.profile.can_level_up())

        # Test advanced level
        self.profile.level = 'advanced'
        self.profile.xp = 499  # Below 500 threshold
        self.assertFalse(self.profile.can_level_up())

        self.profile.xp = 500  # At threshold
        self.assertTrue(self.profile.can_level_up())

        # Test expert level (cannot level up)
        self.profile.level = 'expert'
        self.profile.xp = 1000
        self.assertFalse(self.profile.can_level_up())

    def test_add_xp_basic_functionality(self):
        """Test basic XP addition without level ups"""
        # Add 25 XP
        leveled_up, new_level = self.profile.add_xp(25)
        self.assertFalse(leveled_up)
        self.assertIsNone(new_level)
        self.assertEqual(self.profile.xp, 25)
        self.assertEqual(self.profile.total_xp, 25)

        # Add another 30 XP
        leveled_up, new_level = self.profile.add_xp(30)
        self.assertFalse(leveled_up)
        self.assertIsNone(new_level)
        self.assertEqual(self.profile.xp, 55)
        self.assertEqual(self.profile.total_xp, 55)

    def test_add_xp_negative_values(self):
        """Test XP addition with negative values"""
        # Add positive XP first
        self.profile.add_xp(50)
        self.assertEqual(self.profile.xp, 50)

        # Add negative XP (should not go below 0)
        leveled_up, new_level = self.profile.add_xp(-30)
        self.assertFalse(leveled_up)
        self.assertIsNone(new_level)
        self.assertEqual(self.profile.xp, 20)  # 50 - 30 = 20
        self.assertEqual(self.profile.total_xp, 20)  # Total XP should reflect the net gain

        # Try to go below 0
        leveled_up, new_level = self.profile.add_xp(-50)
        self.assertFalse(leveled_up)
        self.assertIsNone(new_level)
        self.assertEqual(self.profile.xp, 0)  # Should not go below 0
        self.assertEqual(self.profile.total_xp, 0)  # Should not go below 0

    def test_level_up_from_beginner_to_intermediate(self):
        """Test level up from beginner to intermediate"""
        # Add exactly 100 XP to trigger level up
        leveled_up, new_level = self.profile.add_xp(100)

        self.assertTrue(leveled_up)
        self.assertEqual(new_level, 'intermediate')
        self.assertEqual(self.profile.level, 'intermediate')
        self.assertEqual(self.profile.xp, 0)  # XP resets for new level
        self.assertEqual(self.profile.total_xp, 100)  # Total XP preserved

    def test_level_up_from_intermediate_to_advanced(self):
        """Test level up from intermediate to advanced"""
        # Set to intermediate level
        self.profile.level = 'intermediate'
        self.profile.xp = 0

        # Add exactly 300 XP to trigger level up
        leveled_up, new_level = self.profile.add_xp(300)

        self.assertTrue(leveled_up)
        self.assertEqual(new_level, 'advanced')
        self.assertEqual(self.profile.level, 'advanced')
        self.assertEqual(self.profile.xp, 0)  # XP resets for new level
        self.assertEqual(self.profile.total_xp, 300)  # Total XP preserved

    def test_level_up_from_advanced_to_expert(self):
        """Test level up from advanced to expert"""
        # Set to advanced level
        self.profile.level = 'advanced'
        self.profile.xp = 0

        # Add exactly 500 XP to trigger level up
        leveled_up, new_level = self.profile.add_xp(500)

        self.assertTrue(leveled_up)
        self.assertEqual(new_level, 'expert')
        self.assertEqual(self.profile.level, 'expert')
        self.assertEqual(self.profile.xp, 0)  # XP resets for new level
        self.assertEqual(self.profile.total_xp, 500)  # Total XP preserved

    def test_no_level_up_from_expert(self):
        """Test that expert level cannot level up further"""
        # Set to expert level
        self.profile.level = 'expert'
        self.profile.xp = 0

        # Add 1000 XP (max for expert)
        leveled_up, new_level = self.profile.add_xp(1000)

        self.assertFalse(leveled_up)  # Should not level up
        self.assertIsNone(new_level)
        self.assertEqual(self.profile.level, 'expert')
        self.assertEqual(self.profile.xp, 1000)  # XP doesn't reset
        self.assertEqual(self.profile.total_xp, 1000)

    def test_multiple_level_ups_in_sequence(self):
        """Test multiple XP additions that trigger multiple level ups"""
        # Start from beginner
        self.assertEqual(self.profile.level, 'beginner')
        self.assertEqual(self.profile.xp, 0)

        # Add 350 XP (should go beginner -> intermediate -> advanced)
        leveled_up, new_level = self.profile.add_xp(350)

        self.assertTrue(leveled_up)
        self.assertEqual(new_level, 'advanced')  # Should reach advanced
        self.assertEqual(self.profile.level, 'advanced')
        self.assertEqual(self.profile.xp, 50)  # 350 - 300 = 50 XP remaining
        self.assertEqual(self.profile.total_xp, 350)

    def test_streak_tracking(self):
        """Test streak tracking functionality"""
        # Initial streak should be 0
        self.assertEqual(self.profile.streak_correct, 0)

        # Add XP (this doesn't directly affect streak - streak is managed elsewhere)
        # This test just verifies the field exists and can be modified
        self.profile.streak_correct = 5
        self.profile.save()

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.streak_correct, 5)

    def test_progress_tracking(self):
        """Test progress percentage tracking"""
        # Initial progress should be 0
        self.assertEqual(self.profile.progress, 0)

        # Update progress
        self.profile.progress = 75
        self.profile.save()

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.progress, 75)

    def test_last_difficulty_tracking(self):
        """Test last difficulty tracking"""
        # Initial last difficulty should be 'easy'
        self.assertEqual(self.profile.last_difficulty, 'easy')

        # Update last difficulty
        self.profile.last_difficulty = 'hard'
        self.profile.save()

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.last_difficulty, 'hard')

    def test_profile_string_representation(self):
        """Test string representation of profile"""
        expected_str = f"{self.user.username}'s Profile"
        self.assertEqual(str(self.profile), expected_str)

    def test_user_profile_relationship(self):
        """Test the one-to-one relationship between user and profile"""
        # Profile should be accessible from user
        self.assertEqual(self.user.student_profile, self.profile)

        # User should be accessible from profile
        self.assertEqual(self.profile.user, self.user)

    def test_profile_deletion_cascade(self):
        """Test that deleting user also deletes profile"""
        user_id = self.user.id
        profile_id = self.profile.id

        # Delete user
        self.user.delete()

        # Check that profile is also deleted (cascade delete)
        from django.core.exceptions import ObjectDoesNotExist
        with self.assertRaises(ObjectDoesNotExist):
            StudentProfile.objects.get(id=profile_id)


class CustomUserTests(TestCase):
    """Test cases for CustomUser model"""

    def test_user_creation(self):
        """Test basic user creation"""
        user = get_user_model().objects.create_user(
            username='test_user',
            password='testpass123',
            role='student'
        )

        self.assertEqual(user.username, 'test_user')
        self.assertEqual(user.role, 'student')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_user_role_choices(self):
        """Test role field choices"""
        # Test student role
        student = get_user_model().objects.create_user(
            username='student_user',
            password='testpass123',
            role='student'
        )
        self.assertEqual(student.role, 'student')

        # Test admin role
        admin = get_user_model().objects.create_user(
            username='admin_user',
            password='testpass123',
            role='admin'
        )
        self.assertEqual(admin.role, 'admin')

    def test_user_string_representation(self):
        """Test string representation of user"""
        user = get_user_model().objects.create_user(
            username='test_user',
            password='testpass123',
            role='student'
        )
        expected_str = "test_user (student)"
        self.assertEqual(str(user), expected_str)

    def test_superuser_creation(self):
        """Test superuser creation"""
        superuser = get_user_model().objects.create_superuser(
            username='admin',
            password='adminpass123',
            email='admin@example.com'
        )

        self.assertEqual(superuser.username, 'admin')
        self.assertEqual(superuser.email, 'admin@example.com')
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
