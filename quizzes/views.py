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

        context = {
            'is_edit': False,
            'DIFFICULTY_CHOICES': Question.DIFFICULTY_CHOICES,
            'FORMAT_CHOICES': Question.FORMAT_CHOICES
        }
        return render(request, 'quizzes/admin/quiz_form.html', context)

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
            'DIFFICULTY_CHOICES': Question.DIFFICULTY_CHOICES,
            'FORMAT_CHOICES': Question.FORMAT_CHOICES
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


@csrf_exempt
@login_required
def get_next_question(request):
    """Get the next question using Q-Learning with anti-repetition and difficulty constraints"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    if request.user.role != 'student':
        return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)

    try:
        profile = request.user.student_profile

        # ============================================
        # FIX 1: Use engine.ALLOWED_ACTIONS for difficulty constraints
        # ============================================
        from qlearning.engine import QLearningEngine
        
        # Get allowed difficulties from engine (respects beginner/advanced constraints)
        allowed_difficulties = QLearningEngine.ALLOWED_ACTIONS.get(
            profile.level, 
            ['easy', 'medium', 'hard']
        )

        # SAFE FALLBACK: If level not in ALLOWED_ACTIONS, default based on level
        if allowed_difficulties is None:
            if profile.level == 'beginner':
                allowed_difficulties = ['easy', 'medium']
            elif profile.level == 'intermediate':
                allowed_difficulties = ['easy', 'medium', 'hard']
            elif profile.level == 'advanced':
                allowed_difficulties = ['medium', 'hard']
            elif profile.level == 'expert':
                allowed_difficulties = ['hard']
            else:
                # Unknown level - start with easy only for safety
                allowed_difficulties = ['easy']
                print(f"WARNING: Unknown user level '{profile.level}', defaulting to easy only")
        
        print(f"User level: {profile.level}, Allowed difficulties: {allowed_difficulties}")

        # ============================================
        # FIX 2: Get UNATTEMPTED questions filtered by allowed difficulties
        # ============================================
        
        # Get IDs of questions user has already attempted
        attempted_question_ids = set(
            AttemptLog.objects
            .filter(user=request.user)
            .values_list('question_id', flat=True)
        )
        
        print(f"User has attempted {len(attempted_question_ids)} questions")

        # Get unattempted questions within allowed difficulties
        unattempted_questions = Question.objects.filter(
            difficulty__in=allowed_difficulties
        ).exclude(id__in=attempted_question_ids)
        
        print(f"Found {unattempted_questions.count()} unattempted questions in allowed difficulties")

        # If no unattempted questions, user has completed all available questions
        if not unattempted_questions.exists():
            return JsonResponse({
                'success': False,
                'error': 'no_more_questions',
                'message': f'Congratulations! You have attempted all available questions for level {profile.level}.',
                'completed': True,
                'allowed_difficulties': allowed_difficulties,
                'total_attempted': len(attempted_question_ids)
            }, status=200)

        # ============================================
        # FIX 3: Use Q-Learning to select difficulty, then pick question from that difficulty
        # ============================================
        
        # Get current state for Q-Learning
        current_state = get_user_state(profile)
        
        # Use Q-Learning engine to choose difficulty (with safety constraints)
        from quizzes.services import QuizService
        state_tuple = QuizService.state_tuple(profile)
        
        selected_difficulty = QLearningEngine.choose_action(
            user=request.user,
            state_tuple=state_tuple,
            epsilon=None,  # Use dynamic epsilon
            current_difficulty=profile.last_difficulty
        )
        
        print(f"Q-Learning selected difficulty: {selected_difficulty}")

        # Get unattempted questions in selected difficulty
        candidate_questions = unattempted_questions.filter(difficulty=selected_difficulty)
        
        # If no questions in selected difficulty, try other allowed difficulties
        if not candidate_questions.exists():
            print(f"No questions in {selected_difficulty}, trying other difficulties")
            for difficulty in allowed_difficulties:
                if difficulty != selected_difficulty:
                    candidate_questions = unattempted_questions.filter(difficulty=difficulty)
                    if candidate_questions.exists():
                        selected_difficulty = difficulty
                        print(f"Found questions in {difficulty}")
                        break
        
        # Final check: if still no questions (shouldn't happen, but safety)
        if not candidate_questions.exists():
            return JsonResponse({
                'success': False,
                'error': 'no_suitable_questions',
                'message': 'No suitable questions found. Please contact administrator.',
            }, status=404)

        # Select random question from candidates
        selected_question = random.choice(candidate_questions)
        
        print(f"Selected question: ID={selected_question.id}, Difficulty={selected_question.difficulty}")

        # Get level transition info
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
            'allowed_difficulties': allowed_difficulties,
            'can_level_up': can_level_up,
            'target_level': target_level,
            'level_progress': level_progress,
            'user_stats': user_stats,
            'is_first_attempt': True,
        }

        return JsonResponse(response_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
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
        next_state_hash=next_state,
        metadata={}  # Add empty metadata
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

    def validate_answer(question, chosen_answer):
        """
        FIX 4: Fixed validation for mcq_complex with proper type handling
        """
        try:
            # Handle None case
            if chosen_answer is None:
                return False
            
            # Ensure chosen_answer is a string
            chosen_answer = str(chosen_answer)
        
            if question.format == 'mcq_simple':
                # Simple MCQ: direct comparison
                if chosen_answer.strip():
                    return bool(chosen_answer.strip() == question.answer_key.strip())
                return False
            
            elif question.format == 'mcq_complex':
                # Complex MCQ with multiple correct answers
                try:
                    # Check if answer is empty
                    if not chosen_answer or not chosen_answer.strip():
                        return False
                
                    print(f"\n=== VALIDATING MCQ COMPLEX ===")
                    print(f"Question ID: {question.id}")
                    print(f"Chosen answer (raw): {chosen_answer} (type: {type(chosen_answer).__name__})")
                    print(f"Answer key (raw): {question.answer_key} (type: {type(question.answer_key).__name__})")
                
                # Parse chosen answer (should be JSON string from frontend)
                    try:
                        chosen_answers = json.loads(chosen_answer)
                    except json.JSONDecodeError as e:
                        print(f"ERROR: Failed to parse chosen_answer: {e}")
                        return False
                
                    # ============================================
                    # FIX: Handle answer_key being either Python list or JSON string
                    # ============================================
                    answer_key = question.answer_key
                
                    # Case 1: answer_key is already a Python list (from database JSONField)
                    if isinstance(answer_key, list):
                        correct_answers = answer_key
                        print(f"Answer key is Python list: {correct_answers}")
                
                    # Case 2: answer_key is a string
                    elif isinstance(answer_key, str):
                        answer_key_str = answer_key.strip()
                        
                        # Case 2a: JSON array string like '["A", "B"]'
                        if answer_key_str.startswith('[') and answer_key_str.endswith(']'):
                            try:
                                correct_answers = json.loads(answer_key_str)
                                print(f"Parsed JSON array: {correct_answers}")
                            except json.JSONDecodeError:
                                # Fallback: manual parsing
                                correct_answers = [ans.strip().strip('"\'') for ans in answer_key_str[1:-1].split(',')]
                                print(f"Manual parse: {correct_answers}")
                    
                    # Case 2b: Comma-separated like 'A,B' or 'A, B'
                        elif ',' in answer_key_str:
                            correct_answers = [ans.strip() for ans in answer_key_str.split(',')]
                            print(f"Comma-separated: {correct_answers}")
                    
                    # Case 2c: Single value
                        else:
                            correct_answers = [answer_key_str]
                            print(f"Single value: {correct_answers}")
                    else:
                        print(f"ERROR: Unexpected answer_key type: {type(answer_key)}")
                        return False
                
                    # Ensure both are lists
                    if not isinstance(chosen_answers, list) or not isinstance(correct_answers, list):
                        print(f"ERROR: Expected lists, got {type(chosen_answers)} and {type(correct_answers)}")
                        return False
                
                    # Compare sets (order doesn't matter)
                    result = set(chosen_answers) == set(correct_answers)
                    print(f"Comparison: {set(chosen_answers)} == {set(correct_answers)} → {result}")
                
                    return result
                
                except Exception as e:
                    print(f"ERROR in validate_answer (mcq_complex): {e}")
                    import traceback
                    traceback.print_exc()
                    return False
            
            elif question.format == 'short_answer':
                # Short answer: case-insensitive comparison
                if chosen_answer.strip() and question.answer_key.strip():
                    return bool(chosen_answer.strip().lower() == question.answer_key.strip().lower())
                return False
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"ERROR in validate_answer: {e}")
            return False
        
        # Default: incorrect
        return False


# Replace submit_answer() function in views.py

@csrf_exempt
@login_required
def submit_answer(request):
    """Enhanced quiz submission with Adaptive Retry System"""
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

        # Get wrong attempts count (0-based from frontend, so attempt 1 = 0 wrong attempts initially)
        wrong_attempts = int(request.POST.get('wrong_attempts', 0))
        current_attempt_number = wrong_attempts + 1  # 1-based attempt number

        # Get time spent
        time_spent = float(request.POST.get('time_spent', 0))

        # ============================================
        # ADAPTIVE RETRY SYSTEM
        # ============================================
        from qlearning.policies import RetryPolicy
        
        # Get max retries for this question
        max_retries = RetryPolicy.get_max_retries(question, request.user)
        
        print(f"\n=== ADAPTIVE RETRY SYSTEM ===")
        print(f"Question: {question.id} ({question.difficulty})")
        print(f"Current attempt: {current_attempt_number}/{max_retries + 1}")
        print(f"Wrong attempts so far: {wrong_attempts}")

        # Validate answer
        print(f"\n=== VALIDATING ANSWER ===")
        print(f"Chosen answer: {chosen_answer}")
        print(f"Answer key: {question.answer_key}")
        
        try:
            is_correct = validate_answer(question, chosen_answer)
            print(f"Validation result: {is_correct}")
        except Exception as e:
            print(f"Error in validate_answer: {str(e)}")
            is_correct = False

        # Get user profile
        profile = request.user.student_profile

        # ============================================
        # XP CALCULATION with Retry Penalty
        # ============================================
        
        # Get base XP from QuizService (considers repetition)
        xp_calculation = QuizService.calculate_attempt_xp(
            question, request.user, is_correct, time_spent
        )
        base_xp = xp_calculation['final_xp']
        
        # Apply retry penalty if wrong
        if not is_correct:
            # Apply attempt-based penalty
            adaptive_reward = RetryPolicy.calculate_attempt_xp(
                base_xp=abs(base_xp),  # Use absolute value for penalty calculation
                attempt_number=current_attempt_number,
                is_correct=False
            )
        else:
            # Apply attempt-based multiplier for correct answers
            adaptive_reward = RetryPolicy.calculate_attempt_xp(
                base_xp=base_xp,
                attempt_number=current_attempt_number,
                is_correct=True
            )
            
            # Update XP calculation for frontend display
            xp_calculation['attempt_penalty'] = 1.0 - RetryPolicy.get_xp_multiplier(current_attempt_number)
            xp_calculation['final_xp'] = adaptive_reward

        print(f"Base XP: {base_xp}, Adaptive XP: {adaptive_reward}, Attempt: {current_attempt_number}")

        # Q-Learning state update
        current_state = get_user_state(profile)

        # Update profile XP
        profile.xp += adaptive_reward
        profile.total_xp += max(0, adaptive_reward)  # Only positive XP for total
        
        if profile.xp < 0:
            profile.xp = 0

        # Check for level up
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
            profile.xp = 0

        # Update streak
        if is_correct:
            profile.streak_correct += 1
        else:
            profile.streak_correct = 0
            wrong_attempts += 1

        profile.last_difficulty = question.difficulty
        profile.save()

        # Update Q-table
        next_state = get_user_state(profile)
        update_q_table(
            user=request.user,
            current_state=current_state,
            action=question.difficulty,
            reward=adaptive_reward,
            next_state=next_state
        )

        # Create attempt log
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

        # ============================================
        # PROGRESSIVE HINT SYSTEM
        # ============================================
        
        hint_data = None
        show_hint = False
        should_advance = False
        
        if not is_correct:
            # Get progressive hint
            hint_data = RetryPolicy.get_progressive_hint(
                question, 
                current_attempt_number,
                max_retries
            )
            show_hint = True
            
            # Check if should auto-advance
            should_advance = RetryPolicy.should_auto_advance(
                wrong_attempts, 
                max_retries
            )
            
            print(f"Hint level: {hint_data['level']}, Should advance: {should_advance}")

        # ============================================
        # RESPONSE DATA
        # ============================================
        
        # Get correct answer for display
        correct_answer = None
        correct_answers = None
        
        if question.format == 'mcq_simple':
            correct_answer = question.answer_key
        elif question.format == 'mcq_complex':
            answer_key = question.answer_key
            if isinstance(answer_key, list):
                correct_answers = answer_key
            elif isinstance(answer_key, str):
                answer_key_str = answer_key.strip()
                if answer_key_str.startswith('['):
                    try:
                        correct_answers = json.loads(answer_key_str)
                    except:
                        correct_answers = [ans.strip() for ans in answer_key_str[1:-1].split(',')]
                else:
                    correct_answers = [ans.strip() for ans in answer_key_str.split(',')]
        else:
            correct_answer = question.answer_key

        # Build response
        response_data = {
            'success': True,
            'is_correct': is_correct,
            'xp_change': adaptive_reward,
            'xp_calculation': xp_calculation,
            'new_xp': profile.xp,
            'new_total_xp': profile.total_xp,
            'leveled_up': leveled_up,
            'new_level': new_level,
            
            # Retry system data
            'wrong_attempts': wrong_attempts,
            'current_attempt': current_attempt_number,
            'max_attempts': max_retries + 1,
            'should_advance': should_advance,
            
            # Hint system data
            'show_hint': show_hint,
            'hint_data': hint_data,
            
            # Answer data
            'correct_answer': correct_answer,
            'correct_answers': correct_answers,
            'explanation': question.explanation,
            
            # Messages
            'message': get_feedback_message(is_correct, adaptive_reward, leveled_up, new_level),
            'retry_message': RetryPolicy.get_retry_message(current_attempt_number, max_retries) if not is_correct else None,
            
            'next_url': reverse('quizzes:student_quiz_list')
        }

        return JsonResponse(response_data)

    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Error in submit_answer: {str(e)}", exc_info=True)
        traceback.print_exc()
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
            # Process answer_key for complex MCQ
            answer_key = question.answer_key.strip() if question.answer_key else ''
            if answer_key.startswith('[') and answer_key.endswith(']'):
                try:
                    correct_answers = json.loads(answer_key)
                except json.JSONDecodeError:
                    correct_answers = [ans.strip() for ans in answer_key[1:-1].split(',')]
            else:
                correct_answers = [ans.strip() for ans in answer_key.split(',')] if answer_key else []
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
        # Handle case where chosen_answer is None
        if chosen_answer is None:
            return False
            
        # Ensure chosen_answer is a string
        chosen_answer = str(chosen_answer)
        
        if question.format == 'mcq_simple':
            # For MCQ, expect JSON like "A" or "B"
            if chosen_answer.strip():
                return bool(chosen_answer.strip() == question.answer_key.strip())
            return False
            
        elif question.format == 'mcq_complex':
            # For complex MCQ, expect JSON array like ["A", "B"]
            try:
                # Check if answer is empty or just whitespace
                if not chosen_answer or not chosen_answer.strip():
                    return False
                
                # Debug log
                print(f"Validating complex MCQ answer. Chosen: '{chosen_answer}', Type: {type(chosen_answer)}")
                
                # Parse the JSON answer with better error handling
                try:
                    chosen_answers = json.loads(chosen_answer)
                except json.JSONDecodeError:
                    print(f"Failed to parse chosen_answer as JSON: {chosen_answer}")
                    return False
                
                # Handle different answer_key formats
                answer_key = question.answer_key.strip()
                
                # Case 1: Already a JSON array string like '["A", "B"]'
                if answer_key.startswith('[') and answer_key.endswith(']'):
                    try:
                        correct_answers = json.loads(answer_key)
                    except json.JSONDecodeError:
                        print(f"Invalid JSON array in answer_key for question {question.id}")
                        return False
                # Case 2: Comma-separated values like 'A,B' or 'B,C'
                elif ',' in answer_key:
                    correct_answers = [ans.strip() for ans in answer_key.split(',')]
                # Case 3: Single value
                else:
                    correct_answers = [answer_key.strip()]
                    
                print(f"Processed correct_answers: {correct_answers}")
                
                # Ensure both are lists
                if not isinstance(chosen_answers, list) or not isinstance(correct_answers, list):
                    print(f"Invalid answer format. Expected lists, got {type(chosen_answers)} and {type(correct_answers)}")
                    return False
                
                # Debug log
                print(f"Comparing answers - Chosen: {chosen_answers}, Correct: {correct_answers}")
                
                # Compare the sets of answers
                return set(chosen_answers) == set(correct_answers)
                
            except Exception as e:
                print(f"Unexpected error in validate_answer (mcq_complex): {str(e)}")
                return False
            
        elif question.format == 'short_answer':
            # For short answer, do case-insensitive comparison
            if chosen_answer.strip() and question.answer_key.strip():
                return bool(chosen_answer.strip().lower() == question.answer_key.strip().lower())
            return False
            
    except (json.JSONDecodeError, ValueError):
        pass
        
    # Default return False for any unhandled case
    return False
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

@login_required
def debug_user_constraints(request):
    """Debug endpoint to check user's difficulty constraints"""
    if request.user.role != 'student':
        return JsonResponse({'error': 'Students only'}, status=403)
    
    from qlearning.engine import QLearningEngine
    profile = request.user.student_profile
    
    allowed = QLearningEngine.ALLOWED_ACTIONS.get(profile.level, ['unknown'])
    
    # Get attempted questions by difficulty
    attempts_by_diff = {}
    for diff in ['easy', 'medium', 'hard']:
        count = AttemptLog.objects.filter(
            user=request.user,
            question__difficulty=diff
        ).count()
        attempts_by_diff[diff] = count
    
    return JsonResponse({
        'user': request.user.username,
        'level': profile.level,
        'allowed_difficulties': allowed,
        'attempts_by_difficulty': attempts_by_diff,
        'total_attempts': sum(attempts_by_diff.values()),
        'xp': profile.xp,
        'total_xp': profile.total_xp,
    })

def get_available_difficulties(user_level, user, is_initial_session=False):
    """
    SIMPLIFIED: Get available difficulties based ONLY on QLearningEngine.ALLOWED_ACTIONS.
    
    This function is now just a wrapper around QLearningEngine.ALLOWED_ACTIONS
    to maintain compatibility with StudentQuizListView.
    
    Args:
        user_level: Current user level (beginner/intermediate/advanced/expert)
        user: User instance (not used anymore, kept for compatibility)
        is_initial_session: Not used anymore, kept for compatibility
    
    Returns:
        List of allowed difficulty strings
    """
    from qlearning.engine import QLearningEngine
    
    # Simply return ALLOWED_ACTIONS from engine
    allowed = QLearningEngine.ALLOWED_ACTIONS.get(user_level)
    
    # Safe fallback
    if allowed is None:
        print(f"WARNING: Unknown user level '{user_level}', defaulting based on level name")
        if user_level == 'beginner':
            allowed = ['easy', 'medium']
        elif user_level == 'intermediate':
            allowed = ['easy', 'medium', 'hard']
        elif user_level == 'advanced':
            allowed = ['medium', 'hard']
        elif user_level == 'expert':
            allowed = ['hard']
        else:
            # Unknown level - default to easy only for safety
            allowed = ['easy']
            print(f"ERROR: Completely unknown level '{user_level}', forcing easy only")
    
    return allowed