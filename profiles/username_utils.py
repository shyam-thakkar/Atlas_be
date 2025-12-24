"""
Username validation and management utilities.
Handles username format validation, availability checking, claiming, and changing.
"""
import re
from django.db import transaction
from django.core.exceptions import ValidationError


# Built-in reserved usernames (can't be claimed)
SYSTEM_RESERVED_USERNAMES = {
    'admin', 'administrator', 'api', 'www', 'mail', 'email', 'ftp', 
    'support', 'help', 'info', 'contact', 'blog', 'news', 'app',
    'static', 'assets', 'cdn', 'media', 'images', 'js', 'css',
    'login', 'logout', 'signup', 'signin', 'register', 'auth',
    'dashboard', 'settings', 'profile', 'account', 'user', 'users',
    'portfolio', 'portfolios', 'aifolio', 'atlas', 'test', 'demo',
    'null', 'undefined', 'root', 'system', 'moderator', 'mod',
    'public', 'private', 'internal', 'external', 'home', 'index',
    'about', 'terms', 'privacy', 'legal', 'docs', 'documentation',
}

# Username validation rules
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30
USERNAME_PATTERN = re.compile(r'^[a-z0-9][a-z0-9_-]*[a-z0-9]$|^[a-z0-9]$')


class UsernameError(Exception):
    """Base exception for username operations."""
    pass


class UsernameValidationError(UsernameError):
    """Username format is invalid."""
    pass


class UsernameTakenError(UsernameError):
    """Username is already claimed by another user."""
    pass


class UsernameReservedError(UsernameError):
    """Username is reserved and cannot be claimed."""
    pass


class UsernameChangeLimitError(UsernameError):
    """User has reached their username change limit."""
    pass


def validate_username_format(username: str) -> str:
    """
    Validate username format and return normalized version.
    
    Rules:
    - 3-30 characters
    - Lowercase alphanumeric, hyphens, underscores
    - Must start and end with alphanumeric
    - No consecutive special characters
    
    Raises UsernameValidationError if invalid.
    Returns normalized (lowercase) username.
    """
    if not username:
        raise UsernameValidationError("Username cannot be empty")
    
    # Normalize: lowercase and strip
    normalized = username.lower().strip()
    
    # Length check
    if len(normalized) < USERNAME_MIN_LENGTH:
        raise UsernameValidationError(
            f"Username must be at least {USERNAME_MIN_LENGTH} characters"
        )
    if len(normalized) > USERNAME_MAX_LENGTH:
        raise UsernameValidationError(
            f"Username cannot exceed {USERNAME_MAX_LENGTH} characters"
        )
    
    # Pattern check
    if not USERNAME_PATTERN.match(normalized):
        raise UsernameValidationError(
            "Username must start and end with a letter or number, "
            "and can only contain lowercase letters, numbers, hyphens, and underscores"
        )
    
    # No consecutive special chars
    if '--' in normalized or '__' in normalized or '-_' in normalized or '_-' in normalized:
        raise UsernameValidationError(
            "Username cannot have consecutive special characters"
        )
    
    return normalized


def is_username_reserved(username: str) -> bool:
    """Check if username is reserved (system or database)."""
    from .models import ReservedUsername
    
    normalized = username.lower()
    
    # Check built-in reserved list
    if normalized in SYSTEM_RESERVED_USERNAMES:
        return True
    
    # Check database reserved list
    return ReservedUsername.objects.filter(username=normalized).exists()


def is_username_available(username: str, exclude_user=None) -> bool:
    """
    Check if username is available for claiming.
    
    Args:
        username: The username to check
        exclude_user: User to exclude (for checking own username)
    
    Returns:
        True if available, False otherwise
    """
    from .models import Username
    
    try:
        normalized = validate_username_format(username)
    except UsernameValidationError:
        return False
    
    if is_username_reserved(normalized):
        return False
    
    queryset = Username.objects.filter(username=normalized)
    if exclude_user:
        queryset = queryset.exclude(user=exclude_user)
    
    return not queryset.exists()


def claim_username(user, username: str) -> 'Username':
    """
    Claim a username for a user (first-time claim). Atomic operation.
    
    Raises:
        UsernameValidationError: If format is invalid
        UsernameReservedError: If username is reserved
        UsernameTakenError: If username is already claimed
        UsernameError: If user already has a username
    """
    from .models import Username, Portfolio
    
    # Check if user already has a username
    if hasattr(user, 'portfolio_username') and user.portfolio_username:
        raise UsernameError("User already has a username. Use change_username() to change it.")
    
    # Validate format
    normalized = validate_username_format(username)
    
    # Check reserved
    if is_username_reserved(normalized):
        raise UsernameReservedError(f"Username '{normalized}' is reserved")
    
    # Atomic creation with race condition protection
    with transaction.atomic():
        # Use select_for_update to prevent race conditions
        existing = Username.objects.select_for_update().filter(username=normalized).first()
        if existing:
            raise UsernameTakenError(f"Username '{normalized}' is already taken")
        
        # Create username
        username_obj = Username.objects.create(
            username=normalized,
            user=user
        )
        
        # Link to user's portfolio if exists
        portfolio = Portfolio.objects.filter(user=user).first()
        if portfolio:
            portfolio.username = username_obj
            portfolio.save(update_fields=['username'])
    
    return username_obj


def change_username(user, new_username: str) -> 'Username':
    """
    Change a user's existing username. Atomic operation.
    Counts against user's tier-based change limit.
    
    Raises:
        UsernameError: If user doesn't have a username
        UsernameChangeLimitError: If user has no changes remaining
        UsernameValidationError: If format is invalid
        UsernameReservedError: If username is reserved
        UsernameTakenError: If username is already claimed
    """
    from .models import Username
    
    # Check if user has a username to change
    if not hasattr(user, 'portfolio_username') or not user.portfolio_username:
        raise UsernameError("User doesn't have a username. Use claim_username() first.")
    
    # Check tier limit
    if not user.can_change_username():
        remaining = user.get_remaining_username_changes()
        limit = user.get_username_change_limit()
        raise UsernameChangeLimitError(
            f"You have used all {limit} username changes allowed for your tier. "
            f"Upgrade to get more changes."
        )
    
    # Validate format
    normalized = validate_username_format(new_username)
    
    # Check if same as current
    current_username = user.portfolio_username.username
    if normalized == current_username:
        raise UsernameValidationError("New username is the same as current username")
    
    # Check reserved
    if is_username_reserved(normalized):
        raise UsernameReservedError(f"Username '{normalized}' is reserved")
    
    # Atomic update with race condition protection
    with transaction.atomic():
        # Check availability (excluding current user)
        existing = Username.objects.select_for_update().filter(username=normalized).exclude(user=user).first()
        if existing:
            raise UsernameTakenError(f"Username '{normalized}' is already taken")
        
        # Update the username
        username_obj = user.portfolio_username
        username_obj.username = normalized
        username_obj.save(update_fields=['username', 'updated_at'])
        
        # Increment user's change count
        user.increment_username_change_count()
    
    return username_obj


def get_username_info(user) -> dict:
    """
    Get username and change limit info for a user.
    
    Returns dict with:
    - username: current username or None
    - has_username: bool
    - can_change: bool  
    - changes_used: int
    - changes_remaining: int or -1 for unlimited
    - tier: user's tier
    """
    has_username = hasattr(user, 'portfolio_username') and user.portfolio_username is not None
    
    return {
        'username': user.portfolio_username.username if has_username else None,
        'has_username': has_username,
        'can_change': user.can_change_username() if has_username else True,
        'changes_used': user.username_change_count,
        'changes_remaining': user.get_remaining_username_changes(),
        'tier': user.user_tier,
    }
