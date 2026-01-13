from django.core.management.base import BaseCommand, CommandParser
from users.models import User


class Command(BaseCommand):
    help = 'Reset all users to free plan or reset a specific user'

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Reset ALL users to free plan',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Reset a specific user by email',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if options['email']:
            # Reset specific user
            try:
                user = User.objects.get(email=options['email'])
                if dry_run:
                    self.stdout.write(f"[DRY RUN] Would reset user: {user.email} (current tier: {user.user_tier}, plan: {user.plan_type})")
                else:
                    old_tier = user.user_tier
                    old_plan = user.plan_type
                    user.user_tier = 'free'
                    user.plan_type = 'free'
                    user.subscription_expiry = None
                    user.save(update_fields=['user_tier', 'plan_type', 'subscription_expiry'])
                    self.stdout.write(self.style.SUCCESS(
                        f"Reset user {user.email}: {old_tier}/{old_plan} -> free/free"
                    ))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User with email '{options['email']}' not found."))
        
        elif options['all']:
            # Reset all users
            users = User.objects.exclude(user_tier='free')
            count = users.count()
            
            if dry_run:
                self.stdout.write(f"[DRY RUN] Would reset {count} users to free plan:")
                for user in users[:10]:  # Show first 10
                    self.stdout.write(f"  - {user.email} ({user.user_tier}/{user.plan_type})")
                if count > 10:
                    self.stdout.write(f"  ... and {count - 10} more")
            else:
                updated = users.update(
                    user_tier='free',
                    plan_type='free',
                    subscription_expiry=None
                )
                self.stdout.write(self.style.SUCCESS(f"Reset {updated} users to free plan."))
        
        else:
            self.stdout.write(self.style.WARNING(
                "Please specify --all to reset all users or --email <email> to reset a specific user.\n"
                "Use --dry-run to preview changes."
            ))
            self.stdout.write("\nExamples:")
            self.stdout.write("  python manage.py reset_to_free --all")
            self.stdout.write("  python manage.py reset_to_free --email user@example.com")
            self.stdout.write("  python manage.py reset_to_free --all --dry-run")
