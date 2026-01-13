from celery import shared_task
from django.utils import timezone
from .models import User

@shared_task
def check_expired_subscriptions():
    """
    Check for users with expired subscriptions and revert them to beta tier.
    """
    now = timezone.now()
    expired_users = User.objects.filter(
        subscription_expiry__lt=now
    ).exclude(
        user_tier='free'
    )
    
    count = expired_users.update(
        user_tier='free',
        plan_type='free',
        subscription_expiry=None
    )
    
    if count > 0:
        print(f"Downgraded {count} expired subscriptions to beta/free tier.")
    
    return count
