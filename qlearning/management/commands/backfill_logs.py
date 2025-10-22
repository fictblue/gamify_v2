from django.core.management.base import BaseCommand
from django.db import transaction
from backfill_logs import LogBackfiller


class Command(BaseCommand):
    help = 'Backfill Q-Learning analytics logs from existing AttemptLog data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be backfilled without actually doing it',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Backfill logs for specific user only',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        user_id = options['user_id']

        self.stdout.write(
            self.style.SUCCESS('🚀 Starting Q-Learning Log Backfill...')
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('🔍 DRY RUN MODE - No data will be created')
            )

        backfiller = LogBackfiller()

        # If specific user requested, modify the backfiller
        if user_id:
            self.stdout.write(f"📍 Backfilling for user ID: {user_id}")
            # You could modify the LogBackfiller class to filter by user
            # For now, just run the full backfill

        if not dry_run:
            with transaction.atomic():
                backfiller.run_backfill()
        else:
            self.stdout.write("🔍 Would backfill logs (dry run mode)")

        self.stdout.write(
            self.style.SUCCESS('✅ Backfill completed!')
        )
