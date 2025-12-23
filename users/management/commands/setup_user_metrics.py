from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from profiles.models import Portfolio, PortfolioAISnapshot
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Initializes user tiers, auth methods, and backfills resume process counts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without applying them',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        users = User.objects.all()
        
        self.stdout.write(self.style.SUCCESS(f"Processing {users.count()} users..."))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be saved"))

        with transaction.atomic():
            for user in users:
                self.stdout.write(f"\nUser: {user.email}")
                
                # 1. Update Tier to beta if not already set (or just force-set for initialization)
                old_tier = user.user_tier
                user.user_tier = 'beta'
                self.stdout.write(f"  Tier: {old_tier} -> beta")

                # 2. Set Authentication Method based on google_id or usable password
                old_auth = user.authentication_method
                if user.google_id or not user.has_usable_password():
                    user.authentication_method = 'google'
                else:
                    user.authentication_method = 'email'
                self.stdout.write(f"  Auth Method: {old_auth} -> {user.authentication_method}")

                # 3. Backfill Resume Process Count
                portfolios = Portfolio.objects.filter(user=user)
                snapshot_count = PortfolioAISnapshot.objects.filter(portfolio__in=portfolios).count()
                old_count = user.resume_process_count
                user.resume_process_count = snapshot_count
                self.stdout.write(f"  Process Count: {old_count} -> {snapshot_count}")

                if not dry_run:
                    user.save()
                    self.stdout.write(self.style.SUCCESS("  Saved."))
                else:
                    self.stdout.write(self.style.WARNING("  (Dry run - not saved)"))

        self.stdout.write(self.style.SUCCESS("\nDone!"))
