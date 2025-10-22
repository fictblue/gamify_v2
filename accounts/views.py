from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserChangeForm
from django import forms
from .models import CustomUser
from .forms import RegisterForm, LoginForm

class RegisterView(View):
    """Handle user registration"""

    def get(self, request):
        form = RegisterForm()
        return render(request, 'accounts/register.html', {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True  # User is active immediately - no email verification needed
            user.save()

            # StudentProfile is created automatically by Django signal
            # No need to create it manually here

            messages.success(
                request,
                f'Registration successful! Welcome to GamifyLearn, {user.username}! You can now log in.'
            )
            return redirect('accounts:login')
        else:
            messages.error(request, 'Please correct the errors below.')
            return render(request, 'accounts/register.html', {'form': form})


class LoginView(View):
    """Handle user login"""

    def get(self, request):
        form = LoginForm()
        return render(request, 'accounts/login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Try to authenticate with username or email
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.username}!')

                    # Redirect based on role
                    if user.role == 'admin':
                        return redirect('dashboards:admin_dashboard')
                    else:
                        return redirect('dashboards:student_dashboard')
                else:
                    messages.error(request, 'Your account has been deactivated. Please contact an administrator.')
            else:
                messages.error(request, 'Invalid username/email or password.')
                return render(request, 'accounts/login.html', {'form': form})

        return render(request, 'accounts/login.html', {'form': form})


@login_required
def profile_view(request):
    """Handle user profile view and editing"""
    user_form = UserChangeForm(instance=request.user)

    context = {
        'user_form': user_form,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile_view(request):
    """Handle user profile editing with avatar upload support"""

    class ProfileEditForm(forms.ModelForm):
        """Custom form for profile editing with avatar support"""

        class Meta:
            model = CustomUser
            fields = ['username', 'email', 'avatar']
            widgets = {
                'username': forms.TextInput(attrs={'class': 'form-control'}),
                'email': forms.EmailInput(attrs={'class': 'form-control'}),
                'avatar': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            }

    if request.method == 'POST':
        # Handle avatar upload
        if 'avatar' in request.FILES:
            avatar_file = request.FILES['avatar']

            # Validate file size (5MB max)
            if avatar_file.size > 5 * 1024 * 1024:
                messages.error(request, 'Avatar file size must be less than 5MB')
                return redirect('accounts:edit_profile')

            # Validate file type
            if not avatar_file.content_type.startswith('image/'):
                messages.error(request, 'Please upload a valid image file')
                return redirect('accounts:edit_profile')

            # Save avatar to user model
            request.user.avatar = avatar_file
            request.user.save()
            messages.success(request, 'Avatar updated successfully!')

        # Handle regular form fields
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileEditForm(instance=request.user)

    context = {
        'user_form': form,
    }
    return render(request, 'accounts/edit_profile.html', context)


def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')
