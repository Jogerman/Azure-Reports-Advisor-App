"""
Utility functions for audit logging
"""

from typing import Optional, Dict, Any
from django.http import HttpRequest
from django.contrib.auth.models import User


def get_client_ip(request: HttpRequest) -> Optional[str]:
    """
    Extract client IP address from request, handling proxies
    """
    # Check for forwarded IP (when behind a proxy/load balancer)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        ip = x_forwarded_for.split(',')[0].strip()
        return ip

    # Check for real IP header (some proxies use this)
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip:
        return x_real_ip

    # Fall back to REMOTE_ADDR
    return request.META.get('REMOTE_ADDR')


def get_user_context(user: User) -> Dict[str, Any]:
    """
    Extract relevant user context for audit logging
    """
    if not user or not user.is_authenticated:
        return {
            'user_id': None,
            'username': 'Anonymous',
            'email': '',
            'role': 'anonymous',
        }

    return {
        'user_id': str(user.id),
        'username': user.username,
        'email': user.email,
        'role': getattr(user, 'role', ''),
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    }


def calculate_object_changes(old_obj: Any, new_obj: Any, fields: Optional[list] = None) -> Dict[str, Dict[str, Any]]:
    """
    Calculate changes between two object states for audit logging

    Args:
        old_obj: Original object state (can be dict or model instance)
        new_obj: New object state (can be dict or model instance)
        fields: Optional list of fields to track. If None, tracks all fields.

    Returns:
        Dictionary mapping field names to {'old': value, 'new': value}

    Example:
        changes = calculate_object_changes(
            old_report,
            new_report,
            fields=['status', 'title']
        )
        # Returns: {'status': {'old': 'pending', 'new': 'completed'}}
    """
    changes = {}

    # Convert model instances to dictionaries
    if hasattr(old_obj, '__dict__'):
        old_dict = {k: v for k, v in old_obj.__dict__.items() if not k.startswith('_')}
    else:
        old_dict = old_obj

    if hasattr(new_obj, '__dict__'):
        new_dict = {k: v for k, v in new_obj.__dict__.items() if not k.startswith('_')}
    else:
        new_dict = new_obj

    # Determine which fields to check
    fields_to_check = fields if fields else set(old_dict.keys()) | set(new_dict.keys())

    for field in fields_to_check:
        old_value = old_dict.get(field)
        new_value = new_dict.get(field)

        # Only log if values are different
        if old_value != new_value:
            changes[field] = {
                'old': str(old_value) if old_value is not None else None,
                'new': str(new_value) if new_value is not None else None,
            }

    return changes


def format_duration(milliseconds: int) -> str:
    """
    Format duration in milliseconds to human-readable string
    """
    if milliseconds < 1000:
        return f'{milliseconds}ms'
    elif milliseconds < 60000:
        return f'{milliseconds / 1000:.2f}s'
    else:
        minutes = milliseconds // 60000
        seconds = (milliseconds % 60000) / 1000
        return f'{minutes}m {seconds:.2f}s'


def create_audit_context(request: HttpRequest, **kwargs) -> Dict[str, Any]:
    """
    Create a comprehensive audit context from a request

    Args:
        request: Django HttpRequest object
        **kwargs: Additional context to include

    Returns:
        Dictionary with all audit context information
    """
    context = {
        'ip_address': get_client_ip(request),
        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:512],
        'request_path': request.path,
        'request_method': request.method,
        'session_id': request.session.session_key if hasattr(request, 'session') else '',
    }

    # Add user context if authenticated
    if hasattr(request, 'user') and request.user.is_authenticated:
        context.update(get_user_context(request.user))

    # Add any additional context
    context.update(kwargs)

    return context
