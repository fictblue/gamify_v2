from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authentication backend that allows users to log in with either username or email
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()

        # Try to find user by username or email
        try:
            user = UserModel.objects.get(
                Q(username=username) | Q(email=username)
            )
        except UserModel.DoesNotExist:
            return None

        # Check if password is correct
        if user.check_password(password):
            return user

        return None

    def get_user(self, user_id):
        """Get user by ID"""
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
