from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class QlearningConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'qlearning'

    def ready(self):
        # Import signal handlers
        try:
            import qlearning.signals  # noqa
            logger.info("Q-Learning signals imported successfully")
        except Exception as e:
            logger.error(f"Error importing signals: {e}", exc_info=True)
