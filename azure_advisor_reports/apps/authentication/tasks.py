"""
Celery tasks for authentication maintenance and security operations.

This module contains periodic tasks for:
- Cleaning up expired JWT tokens from blacklist
- Token statistics and monitoring
- Security audit logging
"""

import logging
from celery import shared_task
from django.utils import timezone
from apps.authentication.models import TokenBlacklist

logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security')


@shared_task(bind=True, name='authentication.cleanup_expired_tokens')
def cleanup_expired_tokens(self):
    """
    Periodic task to remove expired JWT tokens from the blacklist database.

    This task should be scheduled to run regularly (recommended: every 6-12 hours)
    to prevent the blacklist table from growing indefinitely and maintain
    optimal database performance.

    Returns:
        dict: Cleanup statistics including count of deleted tokens

    Celery Beat Schedule Example:
        CELERY_BEAT_SCHEDULE = {
            'cleanup-expired-tokens': {
                'task': 'authentication.cleanup_expired_tokens',
                'schedule': crontab(hour='*/6'),  # Every 6 hours
            },
        }
    """
    try:
        logger.info("Starting periodic cleanup of expired JWT tokens")

        # Get statistics before cleanup
        now = timezone.now()
        total_before = TokenBlacklist.objects.count()
        expired_count = TokenBlacklist.objects.filter(expires_at__lt=now).count()

        # Perform cleanup
        deleted_count = TokenBlacklist.cleanup_expired()

        # Get statistics after cleanup
        total_after = TokenBlacklist.objects.count()
        active_count = TokenBlacklist.objects.filter(
            is_revoked=False,
            expires_at__gte=now
        ).count()
        revoked_count = TokenBlacklist.objects.filter(is_revoked=True).count()

        # Log results
        logger.info(
            f"Cleaned up {deleted_count} expired tokens. "
            f"Before: {total_before}, After: {total_after}, "
            f"Active: {active_count}, Revoked: {revoked_count}"
        )

        # Log to security logger if significant cleanup occurred
        if deleted_count > 100:
            security_logger.info(
                f"Large token cleanup: {deleted_count} expired tokens removed from blacklist"
            )

        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'total_before': total_before,
            'total_after': total_after,
            'active_tokens': active_count,
            'revoked_tokens': revoked_count,
            'timestamp': now.isoformat(),
        }

    except Exception as e:
        logger.error(f"Error during token cleanup: {str(e)}")
        security_logger.error(f"Token cleanup task failed: {str(e)}")

        # Retry the task if it fails
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes


@shared_task(name='authentication.generate_token_statistics')
def generate_token_statistics():
    """
    Generate statistics about JWT tokens in the blacklist.

    This task can be used for monitoring and alerting on token usage patterns.
    Schedule this to run daily for monitoring purposes.

    Returns:
        dict: Token statistics including counts, ages, and trends

    Celery Beat Schedule Example:
        CELERY_BEAT_SCHEDULE = {
            'token-statistics': {
                'task': 'authentication.generate_token_statistics',
                'schedule': crontab(hour=0, minute=0),  # Daily at midnight
            },
        }
    """
    try:
        logger.info("Generating JWT token statistics")

        now = timezone.now()

        # Basic counts
        total_tokens = TokenBlacklist.objects.count()
        active_tokens = TokenBlacklist.objects.filter(
            is_revoked=False,
            expires_at__gte=now
        ).count()
        revoked_tokens = TokenBlacklist.objects.filter(is_revoked=True).count()
        expired_tokens = TokenBlacklist.objects.filter(
            is_revoked=False,
            expires_at__lt=now
        ).count()

        # Token type breakdown
        access_tokens = TokenBlacklist.objects.filter(token_type='access').count()
        refresh_tokens = TokenBlacklist.objects.filter(token_type='refresh').count()

        # Age analysis
        oldest_token = TokenBlacklist.objects.order_by('created_at').first()
        oldest_age_days = None
        if oldest_token:
            oldest_age_days = (now - oldest_token.created_at).days

        # Revocation reasons
        from django.db.models import Count
        revocation_stats = TokenBlacklist.objects.filter(
            is_revoked=True
        ).values('revoked_reason').annotate(
            count=Count('id')
        ).order_by('-count')

        stats = {
            'timestamp': now.isoformat(),
            'total_tokens': total_tokens,
            'active_tokens': active_tokens,
            'revoked_tokens': revoked_tokens,
            'expired_tokens': expired_tokens,
            'access_tokens': access_tokens,
            'refresh_tokens': refresh_tokens,
            'oldest_token_age_days': oldest_age_days,
            'revocation_reasons': list(revocation_stats),
        }

        logger.info(
            f"Token statistics: {total_tokens} total, "
            f"{active_tokens} active, {revoked_tokens} revoked, "
            f"{expired_tokens} expired"
        )

        # Alert if expired tokens are accumulating
        if expired_tokens > 1000:
            security_logger.warning(
                f"High number of expired tokens ({expired_tokens}) in blacklist. "
                f"Consider running cleanup_expired_tokens task."
            )

        return stats

    except Exception as e:
        logger.error(f"Error generating token statistics: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }


@shared_task(name='authentication.revoke_old_tokens_for_inactive_users')
def revoke_old_tokens_for_inactive_users():
    """
    Revoke all tokens for users who have been inactive for a long period.

    This is an additional security measure to automatically revoke tokens
    for inactive accounts. Schedule this to run weekly.

    Returns:
        dict: Statistics about revoked tokens

    Celery Beat Schedule Example:
        CELERY_BEAT_SCHEDULE = {
            'revoke-inactive-user-tokens': {
                'task': 'authentication.revoke_old_tokens_for_inactive_users',
                'schedule': crontab(day_of_week=0, hour=2),  # Weekly on Sunday at 2 AM
            },
        }
    """
    try:
        from django.contrib.auth import get_user_model
        from datetime import timedelta

        User = get_user_model()
        logger.info("Checking for inactive users with active tokens")

        # Find users inactive for more than 90 days
        inactive_threshold = timezone.now() - timedelta(days=90)
        inactive_users = User.objects.filter(
            last_login__lt=inactive_threshold,
            is_active=True
        )

        total_revoked = 0
        users_affected = 0

        for user in inactive_users:
            # Check if user has any active tokens
            active_token_count = TokenBlacklist.objects.filter(
                user=user,
                is_revoked=False,
                expires_at__gte=timezone.now()
            ).count()

            if active_token_count > 0:
                # Revoke all tokens for this user
                revoked_count = TokenBlacklist.revoke_user_tokens(
                    user,
                    reason='inactive_user_cleanup'
                )
                total_revoked += revoked_count
                users_affected += 1

                logger.info(
                    f"Revoked {revoked_count} tokens for inactive user {user.email} "
                    f"(last login: {user.last_login})"
                )

        if users_affected > 0:
            security_logger.warning(
                f"Revoked {total_revoked} tokens for {users_affected} inactive users "
                f"(inactive > 90 days)"
            )

        return {
            'status': 'success',
            'users_affected': users_affected,
            'tokens_revoked': total_revoked,
            'timestamp': timezone.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error revoking tokens for inactive users: {str(e)}")
        security_logger.error(f"Inactive user token revocation failed: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }
