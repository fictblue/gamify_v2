from django.views.decorators.csrf import csrf_exempt
from qlearning.models import QTableEntry, QLearningLog
import hashlib
import json
import random
from qlearning.policies import LevelTransitionPolicy
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .services import QuizService
from .models import Question, AttemptLog
from django.views.generic import View
import time
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

# Q-Learning Parameters
LEARNING_RATE = 0.1
DISCOUNT_FACTOR = 0.9
EPSILON = 0.1  # Exploration rate
MAX_Q_VALUE = 10.0  # Prevent extreme Q-values
MIN_Q_VALUE = -5.0  # Prevent extreme negative Q-values

@method_decorator(login_required, name='dispatch')
class AdminQuizListView(View):
    """Admin view for listing and managing all questions"""

    def get(self, request):
        if request.user.role != 'admin':
            messages.error(request, 'Access denied. Quiz management is for administrators only.')
            return redirect('accounts:login')

        # Filter questions based on search parameters
        questions = Question.objects.all()

        # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            questions = questions.filter(
                Q(text__icontains=search_query) |
                Q(curriculum_tag__icontains=search_query)
            )

        # Filter by difficulty
        difficulty_filter = request.GET.get('difficulty', '')
        if difficulty_filter:
            questions = questions.filter(difficulty=difficulty_filter)

        # Filter by format
        format_filter = request.GET.get('format', '')
        if format_filter:
            questions = questions.filter(format=format_filter)

        context = {
            'questions': questions,
            'search_query': search_query,
            'difficulty_filter': difficulty_filter,
            'format_filter': format_filter,
            'difficulty_choices': Question.DIFFICULTY_CHOICES,
            'format_choices': Question.FORMAT_CHOICES,
        }

        return render(request, 'quizzes/admin/quiz_list.html', context)


@method_decorator(login_required, name='dispatch')
class AdminQuizCreateView(View):
    """Admin view for creating new questions"""

    def get(self, request):
        if request.user.role != 'admin':
            messages.error(request, 'Access denied. Quiz creation is for administrators only.')
            return redirect('accounts:login')

        return render(request, 'quizzes/admin/quiz_form.html', {'is_edit': False})

    def post(self, request):
        if request.user.role != 'admin':
            messages.error(request, 'Access denied. Quiz creation is for administrators only.')
            return redirect('accounts:login')

        try:
            # Handle JSON options
            options_data = request.POST.get('options', '{}')
            if options_data:
                options_json = json.loads(options_data)
            else:
                options_json = None

            # Create question
            question = Question.objects.create(
                text=request.POST.get('text', ''),
                difficulty=request.POST.get('difficulty', 'easy'),
                format=request.POST.get('format', 'mcq_simple'),
                options=options_json,
                answer_key=request.POST.get('answer_key', ''),
                curriculum_tag=request.POST.get('curriculum_tag', ''),
                explanation=request.POST.get('explanation', ''),
            )

            messages.success(request, f'Question "{question.text[:50]}..." created successfully!')
            return redirect('quizzes:admin_quiz_list')

        except json.JSONDecodeError:
            messages.error(request, 'Invalid JSON format in options field.')
            return render(request, 'quizzes/admin/quiz_form.html', {
                'is_edit': False,
                'form_data': request.POST
            })
        except Exception as e:
            messages.error(request, f'Error creating question: {str(e)}')
            return render(request, 'quizzes/admin/quiz_form.html', {
                'is_edit': False,
                'form_data': request.POST
            })


@method_decorator(login_required, name='dispatch')
class AdminQuizEditView(View):
    """Admin view for editing existing questions"""

    def get(self, request, question_id):
        if request.user.role != 'admin':
            messages.error(request, 'Access denied. Quiz editing is for administrators only.')
            return redirect('accounts:login')

        question = get_object_or_404(Question, id=question_id)

        # Convert options JSON to string for form
        options_str = ''
        if question.options:
            options_str = json.dumps(question.options, indent=2)

        context = {
            'is_edit': True,
            'question': question,
            'options_str': options_str,
        }

        return render(request, 'quizzes/admin/quiz_form.html', context)

    def post(self, request, question_id):
        if request.user.role != 'admin':
            messages.error(request, 'Access denied. Quiz editing is for administrators only.')
            return redirect('accounts:login')

        question = get_object_or_404(Question, id=question_id)

        try:
            # Handle JSON options
            options_data = request.POST.get('options', '{}')
            if options_data:
                options_json = json.loads(options_data)
            else:
                options_json = None

            # Update question
            question.text = request.POST.get('text', question.text)
            question.difficulty = request.POST.get('difficulty', question.difficulty)
            question.format = request.POST.get('format', question.format)
            question.options = options_json
            question.answer_key = request.POST.get('answer_key', question.answer_key)
            question.curriculum_tag = request.POST.get('curriculum_tag', question.curriculum_tag)
            question.explanation = request.POST.get('explanation', question.explanation)
            question.save()

            messages.success(request, f'Question "{question.text[:50]}..." updated successfully!')
            return redirect('quizzes:admin_quiz_list')

        except json.JSONDecodeError:
            messages.error(request, 'Invalid JSON format in options field.')
            return render(request, 'quizzes/admin/quiz_form.html', {
                'is_edit': True,
                'question': question,
                'form_data': request.POST
            })
        except Exception as e:
            messages.error(request, f'Error updating question: {str(e)}')
            return render(request, 'quizzes/admin/quiz_form.html', {
                'is_edit': True,
                'question': question,
                'form_data': request.POST
            })


@method_decorator(login_required, name='dispatch')
class AdminQuizDeleteView(View):
    """Admin view for deleting questions"""

    def post(self, request, question_id):
        if request.user.role != 'admin':
            messages.error(request, 'Access denied. Quiz deletion is for administrators only.')
            return redirect('accounts:login')

        question = get_object_or_404(Question, id=question_id)

        try:
            question_text = question.text[:50]
            question.delete()
            messages.success(request, f'Question "{question_text}..." deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting question: {str(e)}')

        return redirect('quizzes:admin_quiz_list')


@method_decorator(login_required, name='dispatch')
class StudentQuizListView(View):
    """Student view for available quizzes based on their current level"""

    def get(self, request):
        if request.user.role != 'student':
            messages.error(request, 'Access denied. Quiz taking is for students only.')
            return redirect('accounts:login')

        try:
            profile = request.user.student_profile
        except:
            messages.error(request, 'Student profile not found.')
            return redirect('accounts:login')

        # Get appropriate questions based on user level and adaptive performance
        available_difficulties = get_available_difficulties(profile.level, request.user, is_initial_session=False)
        questions = Question.objects.filter(difficulty__in=available_difficulties)

        # Get level transition information
        can_level_up, target_level = LevelTransitionPolicy.can_level_up(profile)
        should_level_down, target_down = LevelTransitionPolicy.should_level_down(profile)
        level_progress = LevelTransitionPolicy.calculate_level_progress(profile)

        # Get recent performance stats
        user_stats = LevelTransitionPolicy.get_user_statistics(request.user)

        # Format difficulty stats for easier template access
        difficulty_counts = {}
        for difficulty in available_difficulties:
            # Get actual count from database instead of cached stats
            count = Question.objects.filter(difficulty=difficulty).count()
            difficulty_counts[difficulty] = count

        # Create a list of difficulty info for template
        difficulty_info_list = []
        for difficulty in available_difficulties:
            difficulty_info_list.append({
                'name': difficulty,
                'count': difficulty_counts.get(difficulty, 0),
                'title': difficulty.title()
            })

        context = {
            'questions': questions,
            'available_difficulties': available_difficulties,
            'current_level': profile.level,
            'can_level_up': can_level_up,
            'target_level': target_level,
            'should_level_down': should_level_down,
            'target_down': target_down,
            'level_progress': level_progress,
            'user_stats': user_stats,
            'difficulty_counts': difficulty_counts,
            'difficulty_info_list': difficulty_info_list,
        }

        return render(request, 'quizzes/student/quiz_list.html', context)


def get_available_difficulties(user_level, user, is_initial_session=False):
    """
    Get available question difficulties based on refined adaptive logic.

    Args:
        user_level: Current user level
        user: User instance for performance analysis
        is_initial_session: If True, use primary difficulty selection for new sessions
    """
    if is_initial_session:
        # PRIMARY DIFFICULTY SELECTION for new quiz sessions
        primary_difficulties = {
            'beginner': ['easy'],  # New users and beginners start with easy
            'intermediate': ['medium'],  # Intermediate start with medium
            'advanced': ['hard'],  # Advanced start with hard
            'expert': ['hard']  # Expert only hard
        }
        return primary_difficulties.get(user_level, ['easy'])

    # ADAPTIVE DIFFICULTY SELECTION for ongoing sessions
    base_difficulties = {
        'beginner': ['easy', 'medium'],      # Easy dominated, but can explore medium
        'intermediate': ['easy', 'medium', 'hard'],  # Fully adaptive
        'advanced': ['medium', 'hard'],     # Hard dominated, fallback to medium
        'expert': ['hard']                  # Only hard
    }

    # Get user's performance metrics
    recent_attempts = AttemptLog.objects.filter(user=user).order_by('-created_at')[:20]

    if not recent_attempts.exists():
        # New user - use base difficulties for their level
        return base_difficulties.get(user_level, ['easy'])

    # Calculate performance by difficulty
    easy_attempts = [a for a in recent_attempts if a.question.difficulty == 'easy']
    medium_attempts = [a for a in recent_attempts if a.question.difficulty == 'medium']
    hard_attempts = [a for a in recent_attempts if a.question.difficulty == 'hard']

    easy_accuracy = 0
    medium_accuracy = 0
    hard_accuracy = 0

    if easy_attempts:
        easy_accuracy = sum(1 for a in easy_attempts if a.is_correct) / len(easy_attempts)
    if medium_attempts:
        medium_accuracy = sum(1 for a in medium_attempts if a.is_correct) / len(medium_attempts)
    if hard_attempts:
        hard_accuracy = sum(1 for a in hard_attempts if a.is_correct) / len(hard_attempts)

    # Adaptive difficulty selection based on performance thresholds
    available_difficulties = list(base_difficulties.get(user_level, ['easy']))

    # Enhanced fallback logic for struggling users at higher levels
    if user_level == 'beginner':
        # Beginner: Start with EASY ONLY, then gradually introduce medium
        if len(recent_attempts) < 3:
            # First 3 questions: ONLY easy for confidence building
            available_difficulties = ['easy']
        elif len(recent_attempts) < 8:
            # Next 5 questions: Easy dominated, but can explore medium if performing well
            if easy_accuracy >= 0.8 and len(easy_attempts) >= 3:
                # Performing very well on easy - allow medium exploration
                available_difficulties = ['easy', 'medium']
            else:
                # Still building confidence - stick to easy
                available_difficulties = ['easy']
        else:
            # After 8+ questions: Normal beginner exploration
            # If performing well on easy (70%+ accuracy), increase medium exploration
            if easy_accuracy >= 0.7 and len(easy_attempts) >= 5:
                # Keep both easy and medium, but Q-learning will handle the balance
                pass  # Already included in base_difficulties
            else:
                # Not performing well enough yet - stick to easy
                available_difficulties = ['easy']

    elif user_level == 'intermediate':
        # Intermediate: Fully adaptive - all difficulties available
        # Performance-based adjustments handled by Q-learning
        pass  # Already includes all difficulties

    elif user_level == 'advanced':
        # Advanced: Hard dominated, but fallback to medium if struggling
        if hard_accuracy < 0.5 and len(hard_attempts) >= 3:
            # Struggling on hard - ensure medium is available for fallback
            if 'medium' not in available_difficulties:
                available_difficulties.append('medium')

        # Additional fallback: if struggling badly, also allow easy
        if hard_accuracy < 0.3 and len(hard_attempts) >= 5:
            if 'easy' not in available_difficulties:
                available_difficulties.append('easy')

    elif user_level == 'expert':
        # Expert: Hard dominated, but fallback to medium if struggling badly
        if hard_accuracy < 0.4 and len(hard_attempts) >= 5:
            # Really struggling on hard - allow medium for fallback
            if 'medium' not in available_difficulties:
                available_difficulties.append('medium')

        # Extreme fallback: if still struggling, allow easy
        if hard_accuracy < 0.2 and len(hard_attempts) >= 8:
            if 'easy' not in available_difficulties:
                available_difficulties.append('easy')

    # Remove duplicates and sort
    available_difficulties = list(set(available_difficulties))
    available_difficulties.sort()

    return available_difficulties


@csrf_exempt
@login_required
def get_next_question(request):
    """Get the next question using Q-Learning algorithm"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    if request.user.role != 'student':
        return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)

    try:
        # Get user profile
        profile = request.user.student_profile

        # Get current state for Q-Learning
        current_state = get_user_state(profile)

        # Check if this is the first question in a new session
        # If user has no recent attempts (last 5 minutes), treat as initial session
        recent_attempts = AttemptLog.objects.filter(
            user=request.user,
            created_at__gte=timezone.now() - timedelta(minutes=5)
        )

        is_initial_session = not recent_attempts.exists()

        # Get available difficulties based on session type
        available_difficulties = get_available_difficulties(profile.level, request.user, is_initial_session)

        if not available_difficulties:
            # Fallback if no difficulties available
            available_difficulties = ['easy']

        # Select action (question difficulty) using epsilon-greedy, but only from available difficulties
        selected_difficulty = select_action_epsilon_greedy_adaptive(
            profile.user, current_state, available_difficulties, is_initial_session
        )

        # Get questions for selected difficulty
        questions = Question.objects.filter(difficulty=selected_difficulty)

        if not questions.exists():
            # Fallback to easy if no questions available
            questions = Question.objects.filter(difficulty='easy')
            if not questions.exists():
                return JsonResponse({
                    'success': False,
                    'error': 'No questions available'
                }, status=404)

        # Select random question from chosen difficulty
        selected_question = random.choice(questions)

        # Get level transition info (for UI display)
        can_level_up, target_level = LevelTransitionPolicy.can_level_up(profile)
        level_progress = LevelTransitionPolicy.calculate_level_progress(profile)
        user_stats = LevelTransitionPolicy.get_user_statistics(request.user)

        response_data = {
            'success': True,
            'question': {
                'id': selected_question.id,
                'text': selected_question.text,
                'difficulty': selected_question.difficulty,
                'format': selected_question.format,
                'options': selected_question.options,
                'curriculum_tag': selected_question.curriculum_tag,
            },
            'user_level': profile.level,
            'selected_difficulty': selected_difficulty,
            'can_level_up': can_level_up,
            'target_level': target_level,
            'level_progress': level_progress,
            'user_stats': user_stats,
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def get_user_state(profile):
    """Create highly sensitive state representation for Q-Learning"""
    # Get recent performance (last 30 attempts for better trend analysis)
    recent_attempts = AttemptLog.objects.filter(user=profile.user).order_by('-created_at')[:30]

    # Calculate comprehensive performance metrics
    if recent_attempts.exists():
        total_count = len(recent_attempts)
        correct_count = sum(1 for attempt in recent_attempts if attempt.is_correct)
        recent_accuracy = correct_count / total_count

        # Difficulty-specific performance (more granular)
        easy_attempts = [a for a in recent_attempts if a.question.difficulty == 'easy']
        medium_attempts = [a for a in recent_attempts if a.question.difficulty == 'medium']
        hard_attempts = [a for a in recent_attempts if a.question.difficulty == 'hard']

        easy_accuracy = 0
        if easy_attempts:
            easy_correct = sum(1 for a in easy_attempts if a.is_correct)
            easy_accuracy = easy_correct / len(easy_attempts)

        medium_accuracy = 0
        if medium_attempts:
            medium_correct = sum(1 for a in medium_attempts if a.is_correct)
            medium_accuracy = medium_correct / len(medium_attempts)

        hard_accuracy = 0
        if hard_attempts:
            hard_correct = sum(1 for a in hard_attempts if a.is_correct)
            hard_accuracy = hard_correct / len(hard_attempts)

        # Calculate average time spent (more accurate)
        times_with_values = [a.time_spent for a in recent_attempts if a.time_spent > 0]
        avg_time = sum(times_with_values) / len(times_with_values) if times_with_values else 30

        # Get hints used
        hints_used = sum(1 for attempt in recent_attempts if attempt.chosen_answer == 'hint_used')

        # Calculate performance trend (comparing first half vs second half)
        mid_point = total_count // 2
        first_half = recent_attempts[mid_point:]
        second_half = recent_attempts[:mid_point]

        first_half_accuracy = sum(1 for a in first_half if a.is_correct) / len(first_half) if first_half else 0.5
        second_half_accuracy = sum(1 for a in second_half if a.is_correct) / len(second_half) if second_half else 0.5
        performance_trend = second_half_accuracy - first_half_accuracy  # Positive = improving

        # Enhanced performance indicators for struggling users
        struggling_streak = 0
        for attempt in reversed(recent_attempts[:10]):  # Check last 10 attempts
            if not attempt.is_correct:
                struggling_streak += 1
            else:
                break

        # Calculate difficulty-specific trends
        easy_trend = 0
        if len(easy_attempts) >= 4:
            recent_easy = easy_attempts[:2]  # Last 2 easy attempts
            older_easy = easy_attempts[2:4] if len(easy_attempts) >= 4 else recent_easy
            recent_easy_acc = sum(1 for a in recent_easy if a.is_correct) / len(recent_easy)
            older_easy_acc = sum(1 for a in older_easy if a.is_correct) / len(older_easy)
            easy_trend = recent_easy_acc - older_easy_acc

        medium_trend = 0
        if len(medium_attempts) >= 4:
            recent_medium = medium_attempts[:2]
            older_medium = medium_attempts[2:4] if len(medium_attempts) >= 4 else recent_medium
            recent_medium_acc = sum(1 for a in recent_medium if a.is_correct) / len(recent_medium)
            older_medium_acc = sum(1 for a in older_medium if a.is_correct) / len(older_medium)
            medium_trend = recent_medium_acc - older_medium_acc

        hard_trend = 0
        if len(hard_attempts) >= 4:
            recent_hard = hard_attempts[:2]
            older_hard = hard_attempts[2:4] if len(hard_attempts) >= 4 else recent_hard
            recent_hard_acc = sum(1 for a in recent_hard if a.is_correct) / len(recent_hard)
            older_hard_acc = sum(1 for a in older_hard if a.is_correct) / len(older_hard)
            hard_trend = recent_hard_acc - older_hard_acc

        # Streak analysis
        current_streak = 0
        for attempt in recent_attempts:
            if attempt.is_correct:
                current_streak += 1
            else:
                break

    else:
        # No attempts yet - use neutral values
        recent_accuracy = 0.5
        easy_accuracy = 0.5
        medium_accuracy = 0.5
        hard_accuracy = 0.5
        avg_time = 30
        hints_used = 0
        performance_trend = 0
        struggling_streak = 0
        easy_trend = 0
        medium_trend = 0
        hard_trend = 0
        current_streak = 0
        total_count = 0  # Initialize total_count for no attempts case

    # Create highly granular state tuple with enhanced performance tracking
    state = (
        profile.level,                    # User level (beginner/intermediate/advanced)
        round(recent_accuracy, 3),        # Overall recent performance (0.000-1.000)
        round(easy_accuracy, 3),          # Easy-specific accuracy
        round(medium_accuracy, 3),        # Medium-specific accuracy
        round(hard_accuracy, 3),          # Hard-specific accuracy
        round(avg_time, 1),               # Average time in seconds
        min(hints_used, 20),             # Hints used (capped at 20)
        current_streak,                   # Current streak
        round(performance_trend, 3),      # Performance trend (-1.0 to 1.0)
        struggling_streak,                # How many wrong answers in a row
        round(easy_trend, 3),             # Easy difficulty trend
        round(medium_trend, 3),           # Medium difficulty trend
        round(hard_trend, 3),             # Hard difficulty trend
        total_count,                      # Total attempts (experience indicator)
    )

    # Create hash for efficient lookup
    state_hash = hashlib.md5(str(state).encode()).hexdigest()
    return state_hash


def get_intelligent_q_value(user, action):
    """Get intelligent initial Q-value based on user profile and action"""
    profile = user.student_profile
    total_attempts = AttemptLog.objects.filter(user=user).count()

    # Base Q-value - start more neutral to encourage exploration
    base_q = 0.0

    # Difficulty mapping
    difficulty_map = {'easy': 1, 'medium': 2, 'hard': 3}
    action_difficulty = difficulty_map.get(action, 1)

    # User level mapping
    level_map = {'beginner': 1, 'intermediate': 2, 'advanced': 3}
    user_level = level_map.get(profile.level, 1)

    # Calculate expected difficulty match - reduce bias
    difficulty_match = abs(action_difficulty - user_level)

    # Initialize Q-value based on expected performance - much more neutral
    if difficulty_match == 0:
        # Perfect match - start with small positive but not extreme
        base_q = 0.3
    elif difficulty_match == 1:
        # One level off - start neutral
        base_q = 0.0
    else:
        # Two levels off - start slightly negative but not extreme
        base_q = -0.2

    # Adjust based on user experience - encourage exploration for new users
    if total_attempts < 5:
        # Very new user - start very neutral to encourage exploration
        base_q = base_q * 0.8  # Reduce bias even more
    elif total_attempts < 10:
        # New user - be less conservative
        base_q *= 0.9
    elif total_attempts > 50:
        # Experienced user - be more decisive
        base_q *= 1.2

    # Adjust based on recent performance - smaller adjustments
    recent_attempts = AttemptLog.objects.filter(user=user).order_by('-created_at')[:10]
    if recent_attempts.exists():
        recent_accuracy = sum(1 for a in recent_attempts if a.is_correct) / len(recent_attempts)
        if recent_accuracy > 0.8:
            # High performer - slightly increase Q-values
            base_q *= 1.1
        elif recent_accuracy < 0.5:
            # Struggling user - slightly decrease Q-values
            base_q *= 0.9

    return base_q


def select_action_epsilon_greedy_adaptive(user, state_hash, available_difficulties, is_initial_session=False):
    """
    Select action using performance-adaptive epsilon-greedy policy,
    but constrained to only available difficulties based on user performance.
    For initial sessions, strongly bias toward primary difficulty.
    """
    # Get Q-values for all available actions
    q_values = {}
    for action in available_difficulties:
        entry, created = QTableEntry.objects.get_or_create(
            user=user,
            state_hash=state_hash,
            action=action,
            defaults={'q_value': get_intelligent_q_value(user, action)}
        )

        # If newly created, update with intelligent Q-value
        if created:
            entry.q_value = get_intelligent_q_value(user, action)
            entry.save()

        q_values[action] = entry.q_value

    # Get user profile for adaptive strategy
    profile = user.student_profile
    total_attempts = AttemptLog.objects.filter(user=user).count()

    # Calculate user performance metrics
    recent_attempts = AttemptLog.objects.filter(user=user).order_by('-created_at')[:20]
    if recent_attempts.exists():
        recent_accuracy = sum(1 for a in recent_attempts if a.is_correct) / len(recent_attempts)
        avg_time = sum(a.time_spent for a in recent_attempts if a.time_spent > 0) / len([a for a in recent_attempts if a.time_spent > 0]) if any(a.time_spent > 0 for a in recent_attempts) else 30
    else:
        recent_accuracy = 0.5
        avg_time = 30

    # Adaptive epsilon based on multiple factors
    base_epsilon = 0.1

    # Performance factor: struggling users need MORE exploration to find better difficulties
    if recent_accuracy > 0.9:
        performance_factor = 2.0  # Double exploration for excellent users
    elif recent_accuracy > 0.8:
        performance_factor = 1.5  # 50% more exploration for good users
    elif recent_accuracy > 0.6:
        performance_factor = 1.0  # Normal exploration
    else:
        # STRUGGLING users need MORE exploration to find easier difficulties that work
        performance_factor = 2.5  # 2.5x exploration for struggling users (was 0.5)

    # Experience factor: NEW USERS NEED CONFIDENCE BUILDING FIRST
    if total_attempts < 3:
        experience_factor = 1.2  # Minimal exploration for first 3 questions (was 3.0)
    elif total_attempts < 5:
        experience_factor = 1.5  # Conservative exploration for first 5 questions (was 3.0)
    elif total_attempts < 10:
        experience_factor = 2.0  # Moderate exploration for new users (was 2.0)
    elif total_attempts > 100:
        experience_factor = 1.8  # Very experienced
    elif total_attempts > 50:
        experience_factor = 1.4  # Moderately experienced
    elif total_attempts > 20:
        experience_factor = 1.1  # Some experience
    else:
        experience_factor = 0.8  # New user

    # Speed factor: fast users = more exploration (confident)
    if avg_time < 15:
        speed_factor = 1.3  # Fast and confident
    elif avg_time < 30:
        speed_factor = 1.0  # Normal speed
    else:
        speed_factor = 0.7  # Slow, maybe needs easier questions

    # Calculate adaptive epsilon
    adaptive_epsilon = base_epsilon * performance_factor * experience_factor * speed_factor
    adaptive_epsilon = min(0.8, adaptive_epsilon)  # Cap at 80% for more exploration

    # For initial sessions, use LOWER epsilon for confidence building
    if is_initial_session:
        # More conservative exploration for very new users
        if total_attempts < 3:
            adaptive_epsilon = 0.1  # Only 10% exploration for first 3 questions
        elif total_attempts < 8:
            adaptive_epsilon = 0.2  # 20% exploration for first 8 questions
        else:
            adaptive_epsilon = max(0.15, adaptive_epsilon)  # At least 15% for established users

    # Epsilon-greedy: random exploration vs greedy exploitation
    if random.random() < adaptive_epsilon:
        # Explore: weighted selection favoring primary difficulty for initial sessions
        if is_initial_session:
            # Initial session: strongly favor primary difficulty
            primary_difficulties = {
                'beginner': 'easy',
                'intermediate': 'medium',
                'advanced': 'hard',
                'expert': 'hard'
            }
            primary_diff = primary_difficulties.get(profile.level, 'easy')

            if primary_diff in available_difficulties:
                # More conservative exploration weights for confidence building
                if total_attempts < 3:
                    # First 3 questions: heavily favor primary (90% vs 10%)
                    weights = {}
                    for action in available_difficulties:
                        if action == primary_diff:
                            weights[action] = 0.9  # 90% chance for primary difficulty
                        else:
                            weights[action] = 0.1 / (len(available_difficulties) - 1)  # Split remaining 10%
                elif total_attempts < 8:
                    # Next 5 questions: moderately favor primary (70% vs 30%)
                    weights = {}
                    for action in available_difficulties:
                        if action == primary_diff:
                            weights[action] = 0.7  # 70% chance for primary difficulty
                        else:
                            weights[action] = 0.3 / (len(available_difficulties) - 1)  # Split remaining 30%
                else:
                    # Established users: balanced exploration (40% vs 60%)
                    weights = {}
                    for action in available_difficulties:
                        if action == primary_diff:
                            weights[action] = 0.4  # 40% chance for primary difficulty
                        else:
                            weights[action] = 0.6 / (len(available_difficulties) - 1)  # Split remaining 60%
            else:
                # Fallback to equal weights
                weights = {action: 1.0 / len(available_difficulties) for action in available_difficulties}
        else:
            # Ongoing session: use adaptive weights based on performance
            if recent_accuracy > 0.8 and total_attempts > 20:
                # High-performing experienced user: slight bias toward harder questions
                weights = {}
                for action in available_difficulties:
                    if action == 'easy':
                        weights[action] = 0.2
                    elif action == 'medium':
                        weights[action] = 0.35
                    else:  # hard
                        weights[action] = 0.45
            elif recent_accuracy < 0.6:
                # STRUGGLING user: bias toward easier questions to help them improve
                weights = {}
                for action in available_difficulties:
                    if action == 'easy':
                        weights[action] = 0.5  # Favor easy heavily for struggling users
                    elif action == 'medium':
                        weights[action] = 0.3  # Moderate weight for medium
                    else:  # hard
                        weights[action] = 0.2  # Low weight for hard when struggling
            else:
                # Normal user: balanced exploration of available difficulties
                current_level_map = {'beginner': 'easy', 'intermediate': 'medium', 'advanced': 'hard'}
                current_diff = current_level_map.get(profile.level, 'easy')

                weights = {}
                for action in available_difficulties:
                    if action == current_diff:
                        weights[action] = 0.35  # Slight favor for current level
                    elif abs(available_difficulties.index(action) - available_difficulties.index(current_diff)) == 1:
                        weights[action] = 0.35  # Equal weight for adjacent
                    else:
                        weights[action] = 0.3  # More balanced for other difficulties

        selected_action = random.choices(available_difficulties, weights=[weights[action] for action in available_difficulties])[0]
    else:
        # Exploit: choose action with highest Q-value from available difficulties
        if q_values:
            selected_action = max(q_values, key=q_values.get)
        else:
            # Fallback to first available difficulty
            selected_action = available_difficulties[0]

    return selected_action


def update_q_table(user, current_state, action, reward, next_state, learning_rate=LEARNING_RATE, discount_factor=DISCOUNT_FACTOR):
    """Update Q-table using Q-Learning formula with normalization"""
    # Get current Q-value
    current_entry, created = QTableEntry.objects.get_or_create(
        user=user,
        state_hash=current_state,
        action=action,
        defaults={'q_value': 0.0}
    )

    # Get max Q-value for next state
    max_next_q = 0
    if next_state:
        next_entries = QTableEntry.objects.filter(
            user=user,
            state_hash=next_state
        )
        if next_entries.exists():
            max_next_q = max(entry.q_value for entry in next_entries)

    # Q-Learning update formula: Q(s,a) = Q(s,a) + α[r + γ max Q(s',a') - Q(s,a)]
    old_q = current_entry.q_value
    new_q = old_q + learning_rate * (reward + discount_factor * max_next_q - old_q)

    # Normalize Q-value to prevent extreme values
    new_q = max(MIN_Q_VALUE, min(MAX_Q_VALUE, new_q))

    # Update Q-value
    current_entry.q_value = new_q
    current_entry.save()

    # Log the update
    QLearningLog.objects.create(
        user=user,
        state_hash=current_state,
        action=action,
        reward=reward,
        q_value_before=old_q,
        q_value_after=new_q,
        next_state_hash=next_state
    )

    return new_q


@method_decorator(login_required, name='dispatch')
class StudentQuizTakeView(View):
    """Student view for taking a quiz"""

    def get(self, request, question_id):
        if request.user.role != 'student':
            messages.error(request, 'Access denied. Quiz taking is for students only.')
            return redirect('accounts:login')

        question = get_object_or_404(Question, id=question_id)

        context = {
            'question': question,
            'start_time': time.time(),
        }

        return render(request, 'quizzes/student/quiz_take.html', context)

    def post(self, request, question_id):
        if request.user.role != 'student':
            messages.error(request, 'Access denied. Quiz taking is for students only.')
            return redirect('accounts:login')

        question = get_object_or_404(Question, id=question_id)
        start_time = float(request.POST.get('start_time', time.time()))
        time_spent = time.time() - start_time

        # Get student's answer
        chosen_answer = request.POST.get('answer', '')

        # Validate answer based on question format
        is_correct = self.validate_answer(question, chosen_answer)

        # Calculate reward using new repetition-aware system
        xp_calculation = QuizService.calculate_attempt_xp(
            question, request.user, is_correct, time_spent
        )
        reward_numeric = xp_calculation['final_xp']

        # Create attempt log
        attempt_log = AttemptLog.objects.create(
            user=request.user,
            question=question,
            chosen_answer=chosen_answer,
            is_correct=is_correct,
            difficulty_attempted=question.difficulty,
            time_spent=round(time_spent, 2),
            reward_numeric=reward_numeric,
            qtable_snapshot=None,  # Will be populated by Q-learning system
        )

        # Update user profile
        profile = request.user.student_profile
        profile.points += max(0, reward_numeric)

        # Check for level up BEFORE updating other stats
        old_level = profile.level
        leveled_up, new_level = profile.add_xp(reward_numeric)

        if is_correct:
            profile.streak_correct += 1
        else:
            profile.streak_correct = 0
        profile.last_difficulty = question.difficulty
        profile.save()

        context = {
            'question': question,
            'attempt_log': attempt_log,
            'is_correct': is_correct,
            'time_spent': round(time_spent, 2),
            'reward_earned': reward_numeric,
            'xp_calculation': xp_calculation,
        }

        return render(request, 'quizzes/student/quiz_result.html', context)

    def validate_answer(self, question, chosen_answer):
        """Validate student answer based on question format"""
        try:
            if question.format == 'mcq_simple':
                # For MCQ, expect JSON like "A" or "B"
                if chosen_answer.strip():
                    return chosen_answer.strip() == question.answer_key.strip()
            elif question.format == 'mcq_complex':
                # For complex MCQ, expect JSON array like ["A", "B"]
                if chosen_answer.strip():
                    chosen_answers = json.loads(chosen_answer)
                    correct_answers = json.loads(question.answer_key)
                    return set(chosen_answers) == set(correct_answers)
            elif question.format == 'short_answer':
                # For short answer, do case-insensitive comparison
                if chosen_answer.strip() and question.answer_key.strip():
                    return chosen_answer.strip().lower() == question.answer_key.strip().lower()
        except (json.JSONDecodeError, ValueError):
            pass


@csrf_exempt
@login_required
def submit_answer(request):
    """Enhanced quiz submission with improved Q-Learning and time tracking"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    if request.user.role != 'student':
        return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)

    try:
        # Get question
        question_id = request.POST.get('question_id')
        if not question_id:
            return JsonResponse({'success': False, 'error': 'Question ID required'})

        question = get_object_or_404(Question, id=question_id)

        # Get student's answer
        chosen_answer = request.POST.get('answer', '')

        # Get wrong attempts count
        wrong_attempts = int(request.POST.get('wrong_attempts', 0))

        # Get time spent from client-side calculation
        time_spent = float(request.POST.get('time_spent', 0))

        # Validate answer based on question format
        is_correct = validate_answer(question, chosen_answer)

        # Get user profile for Q-Learning
        profile = request.user.student_profile

        # Calculate XP using new repetition-aware system
        xp_calculation = QuizService.calculate_attempt_xp(
            question, request.user, is_correct, time_spent
        )
        adaptive_reward = xp_calculation['final_xp']

        # Q-Learning: Get current state and next state
        current_state = get_user_state(profile)

        # FIXED: Update XP directly without calling non-existent add_xp()
        profile.xp += adaptive_reward
        profile.total_xp += adaptive_reward
        
        # Ensure XP doesn't go negative
        if profile.xp < 0:
            profile.xp = 0

        # Check for automatic level up based on XP thresholds (INCREASED for more learning time)
        leveled_up = False
        new_level = None
        old_level = profile.level
        
        if profile.level == 'beginner' and profile.xp >= 200:  
            new_level = 'intermediate'
            leveled_up = True
        elif profile.level == 'intermediate' and profile.xp >= 500:  
            new_level = 'advanced'
            leveled_up = True
        elif profile.level == 'advanced' and profile.xp >= 800:  
            new_level = 'expert'
            leveled_up = True
        
        if leveled_up:
            profile.level = new_level
            profile.xp = 0  # Reset XP for new level
            
            # Log level transition for analytics
            from qlearning.models import LevelTransitionLog
            try:
                LevelTransitionLog.objects.create(
                    user=request.user,
                    transition_type='level_up_auto',
                    old_level=old_level,
                    new_level=new_level,
                    transition_condition={
                        'xp_threshold': profile.get_xp_for_next_level(),
                        'xp_earned': adaptive_reward,
                        'total_xp': profile.total_xp
                    },
                    performance_metrics={
                        'current_streak': profile.streak_correct,
                        'total_attempts': 0,
                        'questions_attempted': 0
                    }
                )
            except Exception as e:
                # Silently fail if level transition logging fails
                pass

        # Log reward for analytics
        from qlearning.models import RewardIncentivesLog
        try:
            # Determine reward type
            reward_type = 'points'
            if leveled_up:
                reward_type = 'level_up_bonus'

            RewardIncentivesLog.objects.create(
                user=request.user,
                reward_type=reward_type,
                reward_value=adaptive_reward,
                trigger_condition={
                    'question_difficulty': question.difficulty,
                    'is_correct': is_correct,
                    'time_spent': time_spent,
                    'leveled_up': leveled_up,
                    'new_level': new_level if leveled_up else None
                },
                user_reaction={
                    'will_continue_session': True,  # Assume they continue unless logout
                    'engagement_score': 1.0 if adaptive_reward > 0 else 0.5
                },
                session_continuation=True  # Will be updated by session tracking
            )
        except Exception as e:
            # Silently fail if reward logging fails
            pass

        # Update other profile stats
        if is_correct:
            profile.streak_correct += 1
        else:
            profile.streak_correct = 0
            wrong_attempts += 1

        profile.last_difficulty = question.difficulty
        profile.save()

        # Get next state after profile update
        next_state = get_user_state(profile)

        # Update Q-table with the reward
        update_q_table(
            user=request.user,
            current_state=current_state,
            action=question.difficulty,
            reward=adaptive_reward,
            next_state=next_state
        )

        # Log Q-Learning performance periodically (every 10 attempts)
        from qlearning.models import QLearningPerformanceLog
        try:
            user_q_entries = QTableEntry.objects.filter(user=request.user)
            total_entries = user_q_entries.count()

            if total_entries > 0 and total_entries % 10 == 0:  # Every 10 Q-table entries
                # Calculate performance metrics
                avg_q_value = sum(entry.q_value for entry in user_q_entries) / total_entries

                # Simple action distribution (count by difficulty)
                action_counts = {'easy': 0, 'medium': 0, 'hard': 0}
                for entry in user_q_entries:
                    if entry.action in action_counts:
                        action_counts[entry.action] += 1

                total_actions = sum(action_counts.values())
                action_distribution = {
                    action: count / total_actions if total_actions > 0 else 0
                    for action, count in action_counts.items()
                }

                # Estimate optimal action frequency (simplified)
                optimal_frequency = max(action_distribution.values()) if action_distribution else 0

                QLearningPerformanceLog.objects.create(
                    user=request.user,
                    state_hash=current_state,
                    action_distribution=action_distribution,
                    optimal_action_frequency=optimal_frequency,
                    average_q_value=avg_q_value,
                    q_table_size=total_entries,
                    learning_progress=min(1.0, total_entries / 100),  # Progress towards maturity
                    snapshot_interval=10,
                    metadata={
                        'total_attempts': total_entries,
                        'user_level': profile.level,
                        'recent_accuracy': recent_accuracy if 'recent_accuracy' in locals() else 0.5
                    }
                )
        except Exception as e:
            # Silently fail if Q-Learning performance logging fails
            pass

        # Log success rate for analytics (daily aggregation)
        from qlearning.models import SuccessRateLog
        try:
            # Check if we need to create/update daily success rate log
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)

            # Get or create today's success rate log for this user and difficulty
            success_log, created = SuccessRateLog.objects.get_or_create(
                user=request.user,
                difficulty=question.difficulty,
                time_window_start=today_start,
                time_window_end=today_end,
                defaults={
                    'total_attempts': 0,
                    'correct_attempts': 0,
                    'average_time_spent': 0.0,
                    'accuracy_percentage': 0.0
                }
            )

            # Update the log with this attempt
            success_log.total_attempts += 1
            if is_correct:
                success_log.correct_attempts += 1

            # Update average time (simple moving average)
            if success_log.average_time_spent == 0:
                success_log.average_time_spent = time_spent
            else:
                success_log.average_time_spent = (
                    (success_log.average_time_spent * (success_log.total_attempts - 1)) + time_spent
                ) / success_log.total_attempts

            # Recalculate accuracy
            success_log.accuracy_percentage = (
                success_log.correct_attempts / success_log.total_attempts * 100
            )

            success_log.save()

        except Exception as e:
            # Silently fail if success rate logging fails
            pass

        # Log global system statistics periodically (daily)
        from qlearning.models import GlobalSystemLog
        try:
            # Check if we need to update daily global stats
            today = timezone.now().date()
            today_start = timezone.datetime.combine(today, timezone.datetime.min.time())
            today_end = today_start + timedelta(days=1)

            # Check if today's global log exists
            global_log_exists = GlobalSystemLog.objects.filter(
                metric_type='engagement_daily',
                time_window='daily',
                timestamp__gte=today_start,
                timestamp__lt=today_end
            ).exists()

            if not global_log_exists:
                # Calculate global statistics for today
                total_users = CustomUser.objects.filter(role='student').count()
                today_attempts = AttemptLog.objects.filter(created_at__gte=today_start).count()

                if today_attempts > 0:
                    correct_attempts = AttemptLog.objects.filter(
                        created_at__gte=today_start,
                        is_correct=True
                    ).count()
                    global_accuracy = correct_attempts / today_attempts * 100

                    GlobalSystemLog.objects.create(
                        metric_type='engagement_daily',
                        metric_data={
                            'total_users': total_users,
                            'total_attempts': today_attempts,
                            'correct_attempts': correct_attempts,
                            'global_accuracy': round(global_accuracy, 2),
                            'active_users': CustomUser.objects.filter(
                                student_profile__updated_at__gte=today_start
                            ).count()
                        },
                        time_window='daily'
                    )
        except Exception as e:
            # Silently fail if global logging fails
            pass

        # Create attempt log with proper time tracking
        attempt_log = AttemptLog.objects.create(
            user=request.user,
            question=question,
            chosen_answer=chosen_answer,
            is_correct=is_correct,
            difficulty_attempted=question.difficulty,
            time_spent=round(time_spent, 2),
            reward_numeric=adaptive_reward,
            qtable_snapshot=current_state,
        )

        # Log response to adaptation (difficulty changes, hints, etc.)
        from qlearning.models import ResponseToAdaptationLog
        try:
            # Check if this was an adaptation response
            adaptation_type = None
            adaptation_details = {}

            # Check for difficulty adaptation
            if question.difficulty != profile.last_difficulty:
                adaptation_type = 'difficulty_transition'
                adaptation_details = {
                    'old_difficulty': profile.last_difficulty,
                    'new_difficulty': question.difficulty,
                    'reason': 'Q-Learning adaptation based on performance'
                }

            # Check for hint adaptation
            if show_hint and wrong_attempts > 0:
                adaptation_type = 'hint_adaptation'
                adaptation_details = {
                    'hint_level': wrong_attempts,
                    'question_difficulty': question.difficulty,
                    'hint_shown': show_hint
                }

            if adaptation_type:
                ResponseToAdaptationLog.objects.create(
                    user=request.user,
                    adaptation_type=adaptation_type,
                    old_state={
                        'level': old_level if 'old_level' in locals() else profile.level,
                        'last_difficulty': profile.last_difficulty,
                        'streak': profile.streak_correct
                    },
                    new_state={
                        'level': profile.level,
                        'current_difficulty': question.difficulty,
                        'streak': profile.streak_correct,
                        'xp': profile.xp
                    },
                    adaptation_details=adaptation_details,
                    first_attempt_after={
                        'is_correct': is_correct,
                        'time_spent': time_spent,
                        'xp_earned': adaptive_reward
                    },
                    hint_usage_change=1 if show_hint else 0,
                    session_duration_change=time_spent if is_correct else 0
                )
        except Exception as e:
            # Silently fail if adaptation logging fails
            pass

        # Determine if hint should be shown (after 1st, 2nd, or 3rd wrong attempt)
        show_hint = False
        if not is_correct and wrong_attempts >= 1:
            show_hint = True

        # Get correct answer for UI feedback
        correct_answer = None
        correct_answers = None
        if question.format == 'mcq_simple':
            correct_answer = question.answer_key
        elif question.format == 'mcq_complex':
            correct_answers = json.loads(question.answer_key) if question.answer_key else []

        response_data = {
            'success': True,
            'is_correct': is_correct,
            'xp_change': adaptive_reward,
            'xp_calculation': xp_calculation,
            'new_xp': profile.xp,
            'new_total_xp': profile.total_xp,
            'leveled_up': leveled_up,
            'new_level': new_level,
            'show_hint': show_hint,
            'wrong_attempts': wrong_attempts,
            'correct_answer': correct_answer,
            'correct_answers': correct_answers,
            'message': get_feedback_message(is_correct, adaptive_reward, leveled_up, new_level),
            'next_url': reverse('quizzes:student_quiz_list')
        }

        return JsonResponse(response_data)

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in submit_answer: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def get_contextual_hint(question, hint_attempts: int, profile) -> dict:
    """Get contextual hint based on question, attempts, and user profile"""
    from qlearning.policies import LevelTransitionPolicy

    # Use the existing hint system from policies.py
    base_hint = LevelTransitionPolicy.get_hint_for_question(question, hint_attempts)

    if not base_hint:
        return {
            'text': 'No hint available for this question.',
            'level': 0,
            'show_answer': False
        }

    # Enhance hint with question-specific context
    enhanced_hint = enhance_hint_with_context(base_hint, question, hint_attempts)

    # Determine if we should show the answer
    show_answer = (hint_attempts >= 3 and question.difficulty == 'easy')

    return {
        'text': enhanced_hint,
        'level': hint_attempts,
        'show_answer': show_answer
    }


def enhance_hint_with_context(base_hint: str, question, attempts: int) -> str:
    """Enhance hint with question-specific context"""
    # Add curriculum context
    if attempts == 1:
        return f"💡 This relates to {question.curriculum_tag}. {base_hint}"
    elif attempts == 2:
        return f"🔍 Focus on the key concept: {base_hint}"
    elif attempts >= 3:
        # For level 3, include the answer
        answer_text = ""
        if question.format == 'mcq_simple':
            answer_text = f"The correct answer is {question.answer_key}."
        elif question.format == 'mcq_complex':
            correct_answers = json.loads(question.answer_key) if question.answer_key else []
            answer_text = f"The correct answers are: {', '.join(correct_answers)}."
        else:  # short_answer
            answer_text = f"The correct answer is: {question.answer_key}"

        return f"🎯 {base_hint} {answer_text}"
    else:
        return base_hint


def track_hint_usage(user, question, hint_attempts: int):
    """Track hint usage for research and analytics"""
    try:
        # This could be expanded to create HintUsageLog model
        # For now, we'll just ensure the data is available for analysis
        pass
    except Exception:
        # Silently fail if tracking fails
        pass


def validate_answer(question, chosen_answer):
    """Validate student answer based on question format"""
    try:
        if question.format == 'mcq_simple':
            # For MCQ, expect JSON like "A" or "B"
            if chosen_answer.strip():
                return chosen_answer.strip() == question.answer_key.strip()
        elif question.format == 'mcq_complex':
            # For complex MCQ, expect JSON array like ["A", "B"]
            if chosen_answer.strip():
                chosen_answers = json.loads(chosen_answer)
                correct_answers = json.loads(question.answer_key)
                return set(chosen_answers) == set(correct_answers)
        elif question.format == 'short_answer':
            # For short answer, do case-insensitive comparison
            if chosen_answer.strip() and question.answer_key.strip():
                return chosen_answer.strip().lower() == question.answer_key.strip().lower()
    except (json.JSONDecodeError, ValueError):
        pass
def get_feedback_message(is_correct, xp_change, leveled_up, new_level):
    """Generate appropriate feedback message"""
    if is_correct:
        if leveled_up:
            return f"Excellent! You leveled up to {new_level}! 🎉"
        else:
            return f"Correct! You earned {xp_change} XP! 🎉"
    else:
        return f"Keep trying! You earned {xp_change} XP."


@login_required
def get_question_hint(request, question_id):
    """Get contextual hint for a specific question"""
    if request.user.role != 'student':
        return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)

    try:
        question = get_object_or_404(Question, id=question_id)

        # Get hint attempts from request
        hint_attempts = int(request.GET.get('attempts', 1))

        # Get user profile for context
        profile = request.user.student_profile

        # Get contextual hint based on question and attempts
        hint_data = get_contextual_hint(question, hint_attempts, profile)

        # Track hint usage for research
        track_hint_usage(request.user, question, hint_attempts)

        return JsonResponse({
            'success': True,
            'hint': hint_data['text'],
            'level': hint_data['level'],
            'show_answer': hint_data['show_answer'],
            'attempts': hint_attempts
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def take_quiz(request, question_id):
    """Enhanced quiz view with proper context"""
    if request.user.role != 'student':
        return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)
    
    try:
        question = get_object_or_404(Question, id=question_id)
        profile = request.user.student_profile
        
        # Check if user can level up
        can_level_up, target_level = LevelTransitionPolicy.can_level_up(profile)
        
        # Get level progress
        level_progress = LevelTransitionPolicy.calculate_level_progress(profile)
        
        context = {
            'question': question,
            'profile': profile,  # Pass full profile object
            'user_level': profile.level,  # User's current level
            'can_level_up': can_level_up,
            'target_level': target_level,
            'level_progress': level_progress,
            'start_time': timezone.now().timestamp(),
        }
        
        return render(request, 'quizzes/take_quiz.html', context)
        
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Student profile not found')
        return redirect('quizzes:student_quiz_list')
    except Exception as e:
        messages.error(request, f'Error loading quiz: {str(e)}')
        return redirect('quizzes:student_quiz_list')