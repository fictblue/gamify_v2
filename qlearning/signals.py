import logging
from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from .models import ResponseToAdaptationLog, QLearningDecisionLog
from quizzes.models import AttemptLog

logger = logging.getLogger(__name__)

# Log when signals are connected
@receiver(post_migrate)
def on_post_migrate(sender, **kwargs):
    logger.info("Q-Learning signals connected")

def log_adaptation(
    user,
    old_difficulty,
    new_difficulty,
    state_hash=None,
    reason=None
):
    """Log an adaptation event when difficulty changes"""
    if old_difficulty != new_difficulty:
        try:
            logger.info(f"Logging adaptation: {old_difficulty} -> {new_difficulty} for user {user.username}")
            adaptation = ResponseToAdaptationLog.objects.create(
                user=user,
                adaptation_type='difficulty_transition',
                old_state={'difficulty': old_difficulty},
                new_state={'difficulty': new_difficulty},
                adaptation_details={
                    'reason': reason or 'Automatic difficulty adjustment',
                    'state_hash': state_hash or ''
                }
            )
            logger.info(f"Adaptation logged with ID {adaptation.id}: {old_difficulty} -> {new_difficulty}")
            print(f"Adaptation logged: {old_difficulty} -> {new_difficulty} (ID: {adaptation.id})")
            return adaptation
        except Exception as e:
            logger.error(f"Error logging adaptation: {e}", exc_info=True)
            print(f"Error logging adaptation: {e}")
    else:
        logger.debug(f"No adaptation needed: {old_difficulty} == {new_difficulty}")
    return None

@receiver(post_save, sender=QLearningDecisionLog)
def on_decision_log_save(sender, instance, created, **kwargs):
    """Log adaptation when a Q-Learning decision is made"""
    if created and instance.decision_type == 'exploitation':
        # Get the previous decision for this user
        prev_decision = QLearningDecisionLog.objects.filter(
            user=instance.user
        ).exclude(pk=instance.pk).order_by('-timestamp').first()
        
        if prev_decision:
            log_adaptation(
                user=instance.user,
                old_difficulty=prev_decision.action_chosen,
                new_difficulty=instance.action_chosen,
                state_hash=instance.state_hash,
                reason=f'Q-Learning decision: {instance.decision_type}'
            )

@receiver(post_save, sender=AttemptLog)
def on_attempt_save(sender, instance, created, **kwargs):
    """Log adaptation when a question is attempted"""
    print(f"\n=== DEBUG: on_attempt_save signal triggered ===")
    print(f"Instance: {instance.id}, Created: {created}, User: {getattr(instance, 'user', None)}")
    
    if not created:
        print("Not a new attempt, skipping...")
        return
        
    if not instance.user or not hasattr(instance, 'question'):
        print("No user or question, skipping...")
        return
        
    try:
        profile = instance.user.student_profile
        print(f"Student profile found: {profile}")
        
        if not hasattr(profile, 'last_difficulty'):
            print("No last_difficulty attribute on profile, skipping...")
            return
            
        current_diff = instance.question.difficulty
        last_diff = profile.last_difficulty
        
        print(f"Current difficulty: {current_diff}, Last difficulty: {last_diff}")
        
        if last_diff and last_diff != current_diff:
            print(f"Difficulty changed: {last_diff} -> {current_diff}, logging adaptation...")
            log_adaptation(
                user=instance.user,
                old_difficulty=last_diff,
                new_difficulty=current_diff,
                reason=f'Question attempted: {instance.is_correct}'
            )
        else:
            print("No difficulty change detected")
        
        # Update last_difficulty
        print(f"Updating last_difficulty from {profile.last_difficulty} to {current_diff}")
        profile.last_difficulty = current_diff
        profile.save(update_fields=['last_difficulty'])
        print(f"Profile saved with new last_difficulty: {profile.last_difficulty}")
        
    except Exception as e:
        print(f"Error in on_attempt_save: {e}")
        import traceback
        traceback.print_exc()
