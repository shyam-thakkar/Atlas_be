"""
Management command to rebuild RAG documents for all users.
Run this to initialize chatbot for all existing users.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Rebuild RAG documents for all users with portfolios'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Rebuild for specific user ID only',
        )
        parser.add_argument(
            '--async',
            action='store_true',
            dest='run_async',
            help='Run as Celery tasks (async)',
        )
    
    def handle(self, *args, **options):
        from profiles.models import Portfolio
        from chat.services import RAGDocumentGenerator
        from chat.tasks import rebuild_user_rag_documents
        
        user_id = options.get('user_id')
        run_async = options.get('run_async', False)
        
        if user_id:
            # Single user
            users = User.objects.filter(id=user_id)
        else:
            # All users with portfolios
            portfolio_user_ids = Portfolio.objects.values_list('user_id', flat=True).distinct()
            users = User.objects.filter(id__in=portfolio_user_ids)
        
        total = users.count()
        self.stdout.write(f'Found {total} users with portfolios')
        
        success = 0
        failed = 0
        
        for user in users:
            try:
                if run_async:
                    # Queue as Celery task
                    rebuild_user_rag_documents.delay(user.id)
                    self.stdout.write(f'  Queued: {user.email}')
                else:
                    # Run synchronously
                    generator = RAGDocumentGenerator(user.id)
                    count = generator.rebuild()
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ {user.email}: {count} documents')
                    )
                success += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ {user.email}: {e}')
                )
                failed += 1
        
        self.stdout.write('')
        if run_async:
            self.stdout.write(self.style.SUCCESS(f'Queued {success} users for async rebuild'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Success: {success}, Failed: {failed}'))
