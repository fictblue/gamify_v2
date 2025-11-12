from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg, Count, Q
from qlearning.models import ResponseToAdaptationLog, AdaptationEffectivenessLog
from quizzes.models import AttemptLog
import logging

logger = logging.getLogger(__name__)

def calculate_attempt_metrics(attempts):
    """Calculate metrics from a queryset of attempts"""
    if not attempts.exists():
        return {
            'count': 0,
            'success_rate': 0,
            'avg_time': 0,
            'correct_attempts': 0
        }
    
    correct_attempts = attempts.filter(is_correct=True)
    success_rate = (correct_attempts.count() / attempts.count()) * 100
    avg_time = attempts.aggregate(avg_time=Avg('time_spent'))['avg_time'] or 0
    
    return {
        'count': attempts.count(),
        'success_rate': round(success_rate, 2),
        'avg_time': round(avg_time, 2) if avg_time else 0,
        'correct_attempts': correct_attempts.count()
    }

def analyze_adaptation_effectiveness(days_back=7):
    """
    Analyze adaptation effectiveness and create AdaptationEffectivenessLog entries.
    
    Args:
        days_back: Number of days to look back for unanalyzed adaptations
    """
    cutoff_date = timezone.now() - timedelta(days=days_back)
    
    # Get unanalyzed adaptations
    adaptations = ResponseToAdaptationLog.objects.filter(
        timestamp__gte=cutoff_date
    ).exclude(
        effectiveness_logs__isnull=False
    ).order_by('timestamp')
    
    if not adaptations.exists():
        logger.info("No unanalyzed adaptations found in the last %d days", days_back)
        return 0
    
    logger.info("Analyzing %d adaptations...", adaptations.count())
    analyzed_count = 0
    
    for adaptation in adaptations:
        try:
            # Define time windows (7 days before and after adaptation)
            time_window = timedelta(days=7)
            before_end = adaptation.timestamp
            before_start = before_end - time_window
            after_start = before_end
            after_end = after_start + time_window
            
            # Get attempts in the time windows
            user_filter = Q(user=adaptation.user)
            before_filter = user_filter & Q(created_at__gte=before_start, created_at__lt=before_end)
            after_filter = user_filter & Q(created_at__gte=after_start, created_at__lt=after_end)
            
            before_attempts = AttemptLog.objects.filter(before_filter)
            after_attempts = AttemptLog.objects.filter(after_filter)
            
            # Calculate metrics
            before_metrics = calculate_attempt_metrics(before_attempts)
            after_metrics = calculate_attempt_metrics(after_attempts)
            
            # Calculate changes
            success_rate_change = round(after_metrics['success_rate'] - before_metrics['success_rate'], 2)
            time_efficiency_change = 0
            
            if before_metrics['avg_time'] > 0:
                time_efficiency_change = round(
                    ((before_metrics['avg_time'] - after_metrics['avg_time']) / before_metrics['avg_time']) * 100, 2
                )
            
            # Check if user continued the session
            continued_session = after_attempts.exists()
            
            # Create effectiveness log
            AdaptationEffectivenessLog.objects.create(
                user=adaptation.user,
                adaptation_event=adaptation,
                success_rate_before=before_metrics['success_rate'],
                avg_time_before=before_metrics['avg_time'],
                attempts_before=before_metrics['count'],
                success_rate_after=after_metrics['success_rate'],
                avg_time_after=after_metrics['avg_time'],
                attempts_after=after_metrics['count'],
                success_rate_change=success_rate_change,
                time_efficiency_change=time_efficiency_change,
                continued_session=continued_session,
                attempts_until_quit=0,  # This would require additional tracking
                measurement_window_days=7
            )
            
            analyzed_count += 1
            logger.debug("Analyzed adaptation %d: %s -> %s (change: %.2f%%)",
                       adaptation.id,
                       adaptation.old_state.get('difficulty', 'unknown'),
                       adaptation.new_state.get('difficulty', 'unknown'),
                       success_rate_change)
                       
        except Exception as e:
            logger.error("Error analyzing adaptation %d: %s", adaptation.id, str(e), exc_info=True)
    
    logger.info("Successfully analyzed %d/%d adaptations", analyzed_count, adaptations.count())
    return analyzed_count

def run_adaptation_analysis():
    """Run the adaptation analysis and return results"""
    try:
        logger.info("Starting adaptation effectiveness analysis...")
        count = analyze_adaptation_effectiveness(days_back=30)  # Look back 30 days
        logger.info("Adaptation analysis completed. Analyzed %d adaptations.", count)
        return {"status": "success", "adaptations_analyzed": count}
    except Exception as e:
        logger.error("Error in adaptation analysis: %s", str(e), exc_info=True)
        return {"status": "error", "message": str(e)}
