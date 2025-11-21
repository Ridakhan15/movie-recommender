from celery import shared_task
from django.core.management import call_command
from .models import ModelUpdateTask, Rating
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def process_model_updates():
    """
    Process pending model update tasks
    Performs incremental updates to recommendation models
    """
    pending_tasks = ModelUpdateTask.objects.filter(status='pending')[:10]
    
    for task in pending_tasks:
        try:
            task.status = 'processing'
            task.started_at = timezone.now()
            task.save()
            
            # Perform incremental model update
            # This is a simplified version - in production, implement actual incremental learning
            logger.info(f"Processing model update task {task.id}")
            
            # Mark as completed
            task.status = 'completed'
            task.completed_at = timezone.now()
            task.save()
            
        except Exception as e:
            task.status = 'failed'
            task.error_message = str(e)
            task.save()
            logger.error(f"Model update task {task.id} failed: {e}")
    
    return f"Processed {len(pending_tasks)} tasks"


@shared_task
def retrain_all_models():
    """
    Full retraining of all recommendation models
    Runs daily via Celery Beat
    """
    try:
        logger.info("Starting full model retraining...")
        
        # Train all models
        call_command('load_data')  # Original collaborative filtering
        call_command('train_svd_model')
        call_command('train_content_model')
        call_command('create_hybrid_config')
        
        # Optional: Train neural model if PyTorch is available
        try:
            call_command('train_neural_model')
        except Exception as e:
            logger.warning(f"Neural model training skipped: {e}")
        
        logger.info("Full model retraining completed successfully")
        return "All models retrained successfully"
        
    except Exception as e:
        logger.error(f"Model retraining failed: {e}")
        return f"Retraining failed: {e}"


@shared_task
def update_user_profiles():
    """
    Update all user profiles with latest statistics
    """
    from .models import UserProfile
    
    profiles = UserProfile.objects.all()
    updated_count = 0
    
    for profile in profiles:
        try:
            profile.update_favorite_genres()
            updated_count += 1
        except Exception as e:
            logger.error(f"Failed to update profile for {profile.user.username}: {e}")
    
    return f"Updated {updated_count} user profiles"