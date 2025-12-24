"""
Snapshot service for portfolio publishing.
Handles serialization, atomic publishing, and unpublishing.
"""
from django.db import transaction
from django.conf import settings


def serialize_portfolio_for_snapshot(portfolio) -> dict:
    """
    Serialize entire portfolio state into a JSON-serializable dict.
    This becomes the immutable public snapshot.
    
    Uses the same serializer as the structured data API for consistency.
    """
    from .serializers import PortfolioCompositionSerializer
    
    # Use the same serializer as PortfolioStructuredDataView
    # This ensures identical structure between draft API and public snapshot
    serializer = PortfolioCompositionSerializer(portfolio)
    
    return serializer.data


def publish_portfolio(portfolio) -> 'PublishedSnapshot':
    """
    Create a new published snapshot for the portfolio.
    
    This is an atomic operation:
    - Deactivates any existing active snapshot
    - Creates a new active snapshot
    - Increments version number
    
    Returns the new PublishedSnapshot.
    
    Raises:
        ValueError: If portfolio has no username claimed
    """
    from .models import PublishedSnapshot
    
    if not portfolio.username:
        raise ValueError("Cannot publish portfolio without a username. Claim a username first.")
    
    with transaction.atomic():
        # Get current version
        latest = portfolio.published_snapshots.order_by('-version').first()
        new_version = (latest.version + 1) if latest else 1
        
        # Deactivate current active snapshot (if any)
        portfolio.published_snapshots.filter(is_active=True).update(is_active=False)
        
        # Create new snapshot
        snapshot_data = serialize_portfolio_for_snapshot(portfolio)
        
        new_snapshot = PublishedSnapshot.objects.create(
            portfolio=portfolio,
            version=new_version,
            snapshot_data=snapshot_data,
            is_active=True
        )
    
    return new_snapshot


def unpublish_portfolio(portfolio) -> bool:
    """
    Unpublish a portfolio by deactivating all snapshots.
    The username is retained (cannot be released).
    
    Returns True if was published, False if already unpublished.
    """
    with transaction.atomic():
        updated = portfolio.published_snapshots.filter(is_active=True).update(is_active=False)
    
    return updated > 0


def get_public_snapshot(username: str) -> dict | None:
    """
    Get the active public snapshot for a username.
    
    Returns the snapshot_data dict or None if not found/unpublished.
    """
    from .models import Username
    
    try:
        username_obj = Username.objects.select_related('portfolio').get(
            username=username.lower()
        )
        portfolio = getattr(username_obj, 'portfolio', None)
        
        if portfolio:
            active_snapshot = portfolio.published_snapshots.filter(is_active=True).first()
            if active_snapshot:
                return active_snapshot.snapshot_data
    except Username.DoesNotExist:
        pass
    
    return None


def get_snapshot_history(portfolio, include_data: bool = False) -> list:
    """
    Get version history for a portfolio's snapshots.
    
    Args:
        portfolio: The Portfolio instance
        include_data: Whether to include full snapshot_data (can be large)
    
    Returns list of dicts with version info.
    """
    snapshots = portfolio.published_snapshots.all().order_by('-version')
    
    history = []
    for snapshot in snapshots:
        entry = {
            'version': snapshot.version,
            'is_active': snapshot.is_active,
            'published_at': snapshot.published_at.isoformat(),
        }
        if include_data:
            entry['snapshot_data'] = snapshot.snapshot_data
        history.append(entry)
    
    return history


def rollback_to_version(portfolio, version: int) -> 'PublishedSnapshot':
    """
    Rollback to a specific snapshot version (make it active again).
    
    This doesn't delete newer versions, just changes which one is active.
    
    Returns the reactivated snapshot.
    Raises ValueError if version not found.
    """
    from .models import PublishedSnapshot
    
    with transaction.atomic():
        # Find the target snapshot
        target = portfolio.published_snapshots.filter(version=version).first()
        if not target:
            raise ValueError(f"Version {version} not found for this portfolio")
        
        # Deactivate current active
        portfolio.published_snapshots.filter(is_active=True).update(is_active=False)
        
        # Activate target
        target.is_active = True
        target.save(update_fields=['is_active'])
    
    return target
