from django.core.management.base import BaseCommand
from qlearning.adaptation_analyzer import run_adaptation_analysis
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Analyze adaptation effectiveness and generate AdaptationEffectivenessLog entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-back',
            type=int,
            default=30,
            help='Number of days to look back for unanalyzed adaptations (default: 30)'
        )

    def handle(self, *args, **options):
        days_back = options['days_back']
        self.stdout.write(self.style.SUCCESS(f'Starting adaptation analysis for the last {days_back} days...'))
        
        from qlearning.adaptation_analyzer import analyze_adaptation_effectiveness
        
        try:
            count = analyze_adaptation_effectiveness(days_back=days_back)
            if count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully analyzed {count} adaptations.')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('No unanalyzed adaptations found in the specified time period.')
                )
        except Exception as e:
            logger.error(f"Error running adaptation analysis: {e}", exc_info=True)
            self.stderr.write(
                self.style.ERROR(f'Error running adaptation analysis: {e}')
            )
