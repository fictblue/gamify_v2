import json
import pandas as pd
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Avg, F, Q, Min, Max
from django.utils import timezone
from datetime import datetime, timedelta
from accounts.models import CustomUser, StudentProfile
from quizzes.models import AttemptLog, Question
from qlearning.models import QLearningLog, QTableEntry, LoginActivityLog, UserEngagementLog

def export_research_data(format='excel'):
    """
    Export research data in Excel or JSON format based on the research requirements.
    
    Args:
        format (str): 'excel' or 'json' or 'csv'
    
    Returns:
        HttpResponse: File response with the exported data
    """
    # Get data for all metrics from research narrative
    print("\n=== DEBUG: Getting user engagement metrics ===")
    user_engagement = get_user_engagement_metrics()
    print(f"User Engagement data: {user_engagement}")
    
    print("\n=== DEBUG: Getting success rate metrics ===")
    success_rates = get_success_rate_metrics()
    print(f"Success Rates data: {success_rates}")
    
    print("\n=== DEBUG: Getting Q-Learning performance metrics ===")
    qlearning_performance = get_qlearning_performance_metrics()
    print(f"Q-Learning Performance data: {qlearning_performance}")
    
    print("\n=== DEBUG: Getting adaptation effectiveness metrics ===")
    adaptation_effectiveness = get_adaptation_effectiveness_metrics()
    print(f"Adaptation Effectiveness data: {adaptation_effectiveness}")
    
    if format.lower() == 'json':
        # Combine all data into a single dictionary
        export_data = {
            'user_engagement': user_engagement['data'],
            'success_rates': success_rates['data'],
            'qlearning_performance': qlearning_performance['data'],
            'adaptation_effectiveness': adaptation_effectiveness['data'],
            'metadata': {
                'exported_at': timezone.now().isoformat(),
                'time_range': {
                    'start': (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    'end': timezone.now().strftime('%Y-%m-%d')
                },
                'data_sources': [
                    'user_engagement',
                    'success_rates',
                    'qlearning_performance',
                    'adaptation_effectiveness'
                ]
            }
        }
        
        # Create JSON response
        response = JsonResponse(export_data, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = f'attachment; filename="research_data_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
        return response
    
    elif format.lower() == 'excel':  # Excel format
        try:
            # Create a Pandas Excel writer using XlsxWriter as the engine
            from io import BytesIO
            import io
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # User Engagement
                if 'user_engagement' in user_engagement.get('data', {}):
                    engagement_data = user_engagement['data']['user_engagement']
                    if isinstance(engagement_data, list) and len(engagement_data) > 0:
                        pd.json_normalize(engagement_data).to_excel(
                            writer, sheet_name='User Engagement', index=False
                        )
                
                # Success Rates
                if 'by_difficulty' in success_rates.get('data', {}):
                    try:
                        success_rates_data = success_rates['data']['by_difficulty']
                        if isinstance(success_rates_data, dict):
                            success_rates_df = pd.DataFrame([
                                {
                                    'Difficulty': k,
                                    'Total Attempts': v.get('total_attempts', 0),
                                    'Correct Attempts': v.get('correct_attempts', 0),
                                    'Success Rate': v.get('success_rate', 0)
                                }
                                for k, v in success_rates_data.items()
                            ])
                            if not success_rates_df.empty:
                                success_rates_df.to_excel(writer, sheet_name='Success Rates', index=False)
                    except Exception as e:
                        print(f"Error processing success rates: {e}")
                
                # Q-Learning Performance
                if 'action_distribution' in qlearning_performance.get('data', {}):
                    try:
                        qlearning_data = qlearning_performance['data']['action_distribution']
                        if isinstance(qlearning_data, list) and len(qlearning_data) > 0:
                            qlearning_df = pd.DataFrame(qlearning_data)
                            if not qlearning_df.empty:
                                qlearning_df.to_excel(writer, sheet_name='Q-Learning Actions', index=False)
                    except Exception as e:
                        print(f"Error processing Q-Learning data: {e}")
                
                # Adaptation Effectiveness
                if 'adaptations' in adaptation_effectiveness.get('data', {}):
                    try:
                        adaptation_data = adaptation_effectiveness['data']['adaptations']
                        if isinstance(adaptation_data, list) and len(adaptation_data) > 0:
                            adaptation_df = pd.DataFrame(adaptation_data)
                            if not adaptation_df.empty:
                                adaptation_df.to_excel(writer, sheet_name='Adaptations', index=False)
                    except Exception as e:
                        print(f"Error processing adaptation data: {e}")
                
                # Add metadata sheet
                metadata_data = {
                    'Export Date': [timezone.now().strftime('%Y-%m-%d %H:%M:%S')],
                    'Data Range': [
                        f"{(timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')} "
                        f"to {timezone.now().strftime('%Y-%m-%d')}"
                    ]
                }
                
                # Add summary metrics if available
                if 'summary' in user_engagement.get('data', {}):
                    metadata_data['Total Active Users'] = [user_engagement['data']['summary'].get('total_active_users', 0)]
                    metadata_data['Average Logins'] = [user_engagement['data']['summary'].get('avg_logins_per_user', 0)]
                
                if 'overall' in success_rates.get('data', {}):
                    metadata_data['Average Success Rate'] = [success_rates['data']['overall'].get('success_rate', 0)]
                
                pd.DataFrame(metadata_data).to_excel(writer, sheet_name='Metadata', index=False)
            
            # Prepare the Excel response
            output.seek(0)
            response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="research_data_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
            return response
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'error': 'Failed to generate Excel export',
                'details': str(e)
            }, status=500)
        
        # Prepare the Excel response
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="research_data_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        return response
    
    else:  # CSV format
        import csv
        from django.http import HttpResponse
        
        # Create a CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="research_data_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Write User Engagement data
        writer.writerow(['=== User Engagement ==='])
        if user_engagement['data'].get('user_engagement'):
            writer.writerow(user_engagement['data']['user_engagement'][0].keys())  # Header
            for item in user_engagement['data']['user_engagement']:
                writer.writerow(item.values())
        
        # Write Success Rates
        writer.writerow(['\n=== Success Rates ==='])
        writer.writerow(['Difficulty', 'Total Attempts', 'Correct Attempts', 'Success Rate'])
        for difficulty, data in success_rates['data'].get('by_difficulty', {}).items():
            writer.writerow([
                difficulty,
                data.get('total_attempts', 0),
                data.get('correct_attempts', 0),
                data.get('success_rate', 0)
            ])
        
        # Write Q-Learning Performance
        writer.writerow(['\n=== Q-Learning Performance ==='])
        if qlearning_performance['data'].get('action_distribution'):
            writer.writerow(qlearning_performance['data']['action_distribution'][0].keys())  # Header
            for item in qlearning_performance['data']['action_distribution']:
                writer.writerow(item.values())
        
        # Write Adaptation Effectiveness
        writer.writerow(['\n=== Adaptation Effectiveness ==='])
        if adaptation_effectiveness['data'].get('adaptations'):
            writer.writerow(adaptation_effectiveness['data']['adaptations'][0].keys())  # Header
            for item in adaptation_effectiveness['data']['adaptations']:
                writer.writerow(item.values())
        
        return response

def get_user_engagement_metrics():
    """Get user engagement metrics based on research requirements"""
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Get active users with their activities
    active_users = CustomUser.objects.filter(
        last_login__gte=thirty_days_ago,
        is_active=True
    )
    
    engagement_data = []
    for user in active_users:
        # Get user's attempts and login activity using the correct field names
        attempts = AttemptLog.objects.filter(user=user, created_at__gte=thirty_days_ago)
        logins = LoginActivityLog.objects.filter(user=user, login_timestamp__gte=thirty_days_ago)
        
        # Skip users with no activity
        if not (attempts.exists() or logins.exists()):
            continue
            
        # Get first and last activity timestamps
        first_activity = timezone.now()
        last_activity = timezone.make_aware(datetime.min)
        
        if attempts.exists():
            first_attempt = attempts.order_by('created_at').first()
            last_attempt = attempts.order_by('-created_at').first()
            first_activity = min(first_activity, first_attempt.created_at)
            last_activity = max(last_activity, last_attempt.created_at)
            
        if logins.exists():
            first_login = logins.order_by('login_timestamp').first()
            last_login = logins.order_by('-login_timestamp').first()
            first_activity = min(first_activity, first_login.login_timestamp)
            last_activity = max(last_activity, last_login.login_timestamp)
        
        # Calculate session duration (simplified as time between first and last activity)
        session_duration = (last_activity - first_activity).total_seconds() / 3600  # in hours
        
        engagement_data.append({
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'login_count': logins.count(),
            'attempt_count': attempts.count(),
            'first_activity': first_activity.isoformat(),
            'last_activity': last_activity.isoformat(),
            'session_duration_hours': round(session_duration, 2),
            'avg_attempts_per_session': round(attempts.count() / max(1, logins.count()), 2) if logins.exists() else 0,
            'active_days': (timezone.now().date() - first_activity.date()).days + 1
        })
    
    # Calculate summary statistics
    total_users = len(engagement_data)
    if total_users > 0:
        summary = {
            'total_active_users': total_users,
            'avg_logins_per_user': round(sum(u['login_count'] for u in engagement_data) / total_users, 2),
            'avg_attempts_per_user': round(sum(u['attempt_count'] for u in engagement_data) / total_users, 2),
            'avg_session_duration': round(sum(u['session_duration_hours'] for u in engagement_data) / total_users, 2)
        }
    else:
        summary = {
            'total_active_users': 0,
            'avg_logins_per_user': 0,
            'avg_attempts_per_user': 0,
            'avg_session_duration': 0
        }
    
    return {
        'data': {
            'user_engagement': engagement_data,
            'summary': summary
        },
        'metadata': {
            'time_range': {
                'start': thirty_days_ago.date().isoformat(),
                'end': timezone.now().date().isoformat()
            },
            'exported_at': timezone.now().isoformat(),
            'total_records': total_users
        }
    }

def get_success_rate_metrics():
    """Get success rate metrics by difficulty level"""
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Get all attempts in the last 30 days with question difficulty
    attempts = AttemptLog.objects.filter(
        created_at__gte=thirty_days_ago,
        question__difficulty__isnull=False
    ).values('question__difficulty', 'is_correct')
    
    # Calculate success rates by difficulty
    difficulty_stats = {}
    for difficulty in ['easy', 'medium', 'hard']:
        difficulty_attempts = attempts.filter(question__difficulty=difficulty)
        total = difficulty_attempts.count()
        correct = difficulty_attempts.filter(is_correct=True).count()
        
        difficulty_stats[difficulty] = {
            'total_attempts': total,
            'correct_attempts': correct,
            'success_rate': round(correct / total * 100, 2) if total > 0 else 0
        }
    
    return {
        'data': {
            'by_difficulty': difficulty_stats,
            'overall': {
                'total_attempts': sum(s['total_attempts'] for s in difficulty_stats.values()),
                'success_rate': round(sum(s['correct_attempts'] for s in difficulty_stats.values()) / 
                                    max(1, sum(s['total_attempts'] for s in difficulty_stats.values())) * 100, 2)
            }
        },
        'metadata': {
            'time_range': {
                'start': thirty_days_ago.date().isoformat(),
                'end': timezone.now().date().isoformat()
            },
            'exported_at': timezone.now().isoformat()
        }
    }

def get_qlearning_performance_metrics():
    """Get Q-Learning performance metrics"""
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Get Q-Learning logs
    qlogs = QLearningLog.objects.filter(
        timestamp__gte=thirty_days_ago
    )
    
    # Calculate action distribution
    action_distribution = []
    if qlogs.exists():
        action_distribution = list(qlogs.values('action').annotate(
            count=Count('id'),
            avg_reward=Avg('reward')
        ).order_by('-count'))
    
    # Calculate state-action values over time
    state_action_values = {}
    for log in qlogs:
        key = f"{log.state_hash if hasattr(log, 'state_hash') else 'unknown'}_{log.action if hasattr(log, 'action') else 'unknown'}"
        if key not in state_action_values:
            state_action_values[key] = []
        state_action_values[key].append({
            'timestamp': log.timestamp.isoformat() if hasattr(log, 'timestamp') else timezone.now().isoformat(),
            'q_value': log.q_value if hasattr(log, 'q_value') else 0,
            'reward': log.reward if hasattr(log, 'reward') else 0
        })
    
    # Calculate summary statistics
    total_updates = qlogs.count()
    avg_reward = qlogs.aggregate(avg=Avg('reward'))['avg'] or 0 if qlogs.exists() else 0
    
    return {
        'data': {
            'action_distribution': action_distribution,
            'state_action_values': state_action_values,
            'summary': {
                'total_learning_updates': total_updates,
                'avg_reward': round(float(avg_reward), 4),
                'unique_actions': len(action_distribution)
            }
        },
        'metadata': {
            'time_range': {
                'start': thirty_days_ago.date().isoformat(),
                'end': timezone.now().date().isoformat()
            },
            'exported_at': timezone.now().isoformat(),
            'total_records': qlogs.count()
        }
    }

def get_adaptation_effectiveness_metrics():
    """Get metrics on how well the system adapts to users"""
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Get user adaptation data from ResponseToAdaptationLog
    from qlearning.models import ResponseToAdaptationLog
    
    adaptations = ResponseToAdaptationLog.objects.filter(
        timestamp__gte=thirty_days_ago,
        adaptation_type='difficulty_transition'
    ).select_related('user')
    
    print(f"Found {adaptations.count()} adaptation events in the last 30 days")
    
    adaptation_data = []
    for adapt in adaptations:
        if not hasattr(adapt, 'timestamp') or not hasattr(adapt, 'user'):
            continue
            
        try:
            # Get old and new difficulty from the adaptation log
            old_difficulty = adapt.old_state.get('difficulty', 'unknown')
            new_difficulty = adapt.new_state.get('difficulty', 'unknown')
            
            # Skip if we don't have valid difficulties
            if old_difficulty == 'unknown' or new_difficulty == 'unknown':
                continue
                
            # Get user's performance before and after adaptation
            before_window = adapt.timestamp - timedelta(hours=1)
            after_window = adapt.timestamp + timedelta(hours=1)
            
            before_attempts = AttemptLog.objects.filter(
                user=adapt.user,
                created_at__gte=before_window,
                created_at__lt=adapt.timestamp
            )
            
            after_attempts = AttemptLog.objects.filter(
                user=adapt.user,
                created_at__gt=adapt.timestamp,
                created_at__lte=after_window
            )
            
            before_success = before_attempts.filter(is_correct=True).count()
            after_success = after_attempts.filter(is_correct=True).count()
            
            before_total = before_attempts.count()
            after_total = after_attempts.count()
            
            before_rate = round(before_success / max(1, before_total) * 100, 2) if before_total > 0 else 0
            after_rate = round(after_success / max(1, after_total) * 100, 2) if after_total > 0 else 0
            
            # Determine adaptation type based on difficulty change
            if old_difficulty == new_difficulty:
                adaptation_type = 'maintain_difficulty'
            elif (
                (old_difficulty == 'easy' and new_difficulty == 'medium') or
                (old_difficulty == 'medium' and new_difficulty == 'hard')
            ):
                adaptation_type = 'increase_difficulty'
            else:
                adaptation_type = 'decrease_difficulty'
            
            adaptation_data.append({
                'user_id': adapt.user.id,
                'username': adapt.user.username,
                'adaptation_type': adaptation_type,
                'timestamp': adapt.timestamp.isoformat(),
                'old_difficulty': old_difficulty,
                'new_difficulty': new_difficulty,
                'before_attempts': before_total,
                'before_success_rate': before_rate,
                'after_attempts': after_total,
                'after_success_rate': after_rate,
                'improvement': round(after_rate - before_rate, 2)
            })
            
            print(f"Processed adaptation: {old_difficulty} -> {new_difficulty} for user {adapt.user.username}")
            
        except Exception as e:
            print(f"Error processing adaptation {adapt.id}: {e}")
    
    # Calculate summary statistics
    total_adaptations = len(adaptation_data)
    print(f"Total valid adaptations processed: {total_adaptations}")
    
    avg_improvement = round(sum(a['improvement'] for a in adaptation_data) / max(1, total_adaptations), 2) if adaptation_data else 0
    
    adaptation_types = {}
    if adaptation_data:
        adaptation_types = {
            'increase_difficulty': len([a for a in adaptation_data if a['adaptation_type'] == 'increase_difficulty']),
            'decrease_difficulty': len([a for a in adaptation_data if a['adaptation_type'] == 'decrease_difficulty']),
            'maintain_difficulty': len([a for a in adaptation_data if a['adaptation_type'] == 'maintain_difficulty'])
        }
    
    return {
        'data': {
            'adaptations': adaptation_data,
            'summary': {
                'total_adaptations': total_adaptations,
                'avg_improvement': avg_improvement,
                'adaptation_types': adaptation_types
            }
        },
        'metadata': {
            'time_range': {
                'start': thirty_days_ago.date().isoformat(),
                'end': timezone.now().date().isoformat()
            },
            'exported_at': timezone.now().isoformat(),
            'total_records': total_adaptations
        }
    }

def get_user_engagement_data():
    """Get user engagement data for export"""
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Get active users (logged in last 30 days)
    active_users = CustomUser.objects.filter(
        last_login__gte=thirty_days_ago,
        role='student'
    ).values('id', 'username', 'email', 'last_login', 'date_joined')
    
    # Get user activity metrics
    user_activity = []
    for user in active_users:
        attempts = AttemptLog.objects.filter(user_id=user['id'])
        total_attempts = attempts.count()
        correct_attempts = attempts.filter(is_correct=True).count()
        
        user_activity.append({
            'user_id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'date_joined': user['date_joined'],
            'last_login': user['last_login'],
            'total_attempts': total_attempts,
            'correct_attempts': correct_attempts,
            'success_rate': (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0,
            'days_since_active': (timezone.now() - user['last_login']).days if user['last_login'] else None,
            'account_age_days': (timezone.now() - user['date_joined']).days
        })
    
    return {
        'data': user_activity,
        'metadata': {
            'total_students': len(user_activity),
            'time_range': f"{thirty_days_ago.date()} to {timezone.now().date()}",
            'exported_at': timezone.now().isoformat()
        }
    }

def get_quiz_performance_data():
    """Get quiz performance data for export"""
    # Get all attempts with related data
    attempts = AttemptLog.objects.select_related('user', 'question').all()
    
    # Prepare attempt data
    attempt_data = [{
        'attempt_id': attempt.id,
        'user_id': attempt.user_id,
        'username': attempt.user.username,
        'question_id': attempt.question_id,
        'question_text': attempt.question.text[:100] + '...' if attempt.question.text else '',
        'difficulty': attempt.question.difficulty if attempt.question else None,
        'is_correct': attempt.is_correct,
        'selected_option': attempt.selected_option,
        'time_spent': attempt.time_spent,
        'timestamp': attempt.created_at,
        'xp_earned': attempt.xp_earned,
        'points_earned': attempt.points_earned
    } for attempt in attempts]
    
    # Calculate question statistics
    questions = Question.objects.annotate(
        total_attempts=Count('attemptlog'),
        correct_attempts=Count('attemptlog', filter=Q(attemptlog__is_correct=True))
    )
    
    question_stats = [{
        'question_id': q.id,
        'question_text': q.text[:100] + '...' if q.text else '',
        'difficulty': q.difficulty,
        'topic': q.topic,
        'total_attempts': q.total_attempts,
        'correct_attempts': q.correct_attempts,
        'success_rate': (q.correct_attempts / q.total_attempts * 100) if q.total_attempts > 0 else 0,
        'created_at': q.created_at,
        'updated_at': q.updated_at
    } for q in questions]
    
    return {
        'data': {
            'attempts': attempt_data,
            'question_stats': question_stats
        },
        'metadata': {
            'total_attempts': len(attempt_data),
            'total_questions': len(question_stats),
            'exported_at': timezone.now().isoformat()
        }
    }

def get_qlearning_data():
    """Get Q-Learning related data for export"""
    # Get Q-Learning logs
    qlogs = QLearningLog.objects.select_related('user', 'state', 'action', 'next_state').all()
    
    log_data = [{
        'log_id': log.id,
        'user_id': log.user_id,
        'username': log.user.username if log.user else None,
        'timestamp': log.timestamp,
        'state_id': log.state_id,
        'state_name': log.state.name if log.state else None,
        'action_id': log.action_id,
        'action_name': log.action.name if log.action else None,
        'reward_id': log.reward_id,
        'reward_value': log.reward.value if log.reward else None,
        'next_state_id': log.next_state_id,
        'next_state_name': log.next_state.name if log.next_state else None,
        'q_value': log.q_value,
        'learning_rate': log.learning_rate,
        'discount_factor': log.discount_factor,
        'exploration_rate': log.exploration_rate
    } for log in qlogs]
    
    # Get Q-Table data
    qtable_data = []
    try:
        qtable_entries = QTable.objects.select_related('state', 'action').all()
        qtable_data = [{
            'state_id': entry.state_id,
            'state_name': entry.state.name if entry.state else None,
            'action_id': entry.action_id,
            'action_name': entry.action.name if entry.action else None,
            'q_value': entry.q_value,
            'update_count': entry.update_count,
            'last_updated': entry.updated_at
        } for entry in qtable_entries]
    except Exception as e:
        print(f"Error getting Q-Table data: {e}")
    
    return {
        'data': {
            'qlearning_logs': log_data,
            'qtable': qtable_data
        },
        'metadata': {
            'total_logs': len(log_data),
            'total_qtable_entries': len(qtable_data),
            'exported_at': timezone.now().isoformat(),
            'total_q_updates': sum(entry['update_count'] for entry in qtable_data) if qtable_data else 0
        }
    }

def get_system_metrics():
    """Get system performance metrics for export"""
    # This would typically come from system monitoring
    # For now, we'll return some basic metrics
    return {
        'data': [{
            'metric': 'active_users',
            'value': CustomUser.objects.filter(is_active=True).count(),
            'timestamp': timezone.now()
        }, {
            'metric': 'total_questions',
            'value': Question.objects.count(),
            'timestamp': timezone.now()
        }, {
            'metric': 'total_attempts',
            'value': AttemptLog.objects.count(),
            'timestamp': timezone.now()
        }],
        'metadata': {
            'exported_at': timezone.now().isoformat(),
            'server_time': timezone.now().isoformat()
        }
    }
