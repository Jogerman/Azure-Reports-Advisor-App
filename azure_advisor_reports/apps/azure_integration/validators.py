"""
Custom validators for Azure Integration app.

This module provides validation functions for Azure credentials and identifiers.
All validators follow DRF ValidationError pattern for consistent error handling.
"""

import re
from rest_framework import serializers


def validate_uuid_format(value):
    """
    Validate UUID format (with or without hyphens).

    Accepts UUIDs in standard format (with hyphens) or without hyphens.
    Returns lowercase normalized UUID string.

    Args:
        value (str): UUID string to validate

    Returns:
        str: Lowercase normalized UUID

    Raises:
        serializers.ValidationError: If UUID format is invalid

    Examples:
        >>> validate_uuid_format("550e8400-e29b-41d4-a716-446655440000")
        '550e8400-e29b-41d4-a716-446655440000'
        >>> validate_uuid_format("550e8400e29b41d4a716446655440000")
        '550e8400e29b41d4a716446655440000'
    """
    uuid_pattern = r'^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$'

    if not value:
        raise serializers.ValidationError('UUID cannot be empty.')

    if not isinstance(value, str):
        raise serializers.ValidationError('UUID must be a string.')

    if not re.match(uuid_pattern, value.lower()):
        raise serializers.ValidationError(
            'Invalid UUID format. Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
        )

    return value.lower()


def validate_subscription_id(value):
    """
    Validate Azure subscription ID and check uniqueness.

    Validates UUID format and ensures no duplicate subscription IDs exist.
    Check is case-insensitive to prevent similar IDs.

    Args:
        value (str): Azure subscription ID to validate

    Returns:
        str: Validated and normalized subscription ID

    Raises:
        serializers.ValidationError: If UUID format invalid or duplicate exists

    Note:
        This validator should only be used during creation. Update operations
        should skip uniqueness check for the current instance.
    """
    # First validate UUID format
    validated = validate_uuid_format(value)

    # Check uniqueness (case-insensitive)
    from apps.azure_integration.models import AzureSubscription

    if AzureSubscription.objects.filter(
        subscription_id__iexact=validated
    ).exists():
        raise serializers.ValidationError(
            'An Azure subscription with this ID already exists.'
        )

    return validated


def validate_client_secret(value):
    """
    Validate Azure client secret format and security requirements.

    Enforces security best practices for Azure Service Principal secrets:
    - Minimum length of 20 characters
    - Maximum length of 200 characters
    - No spaces allowed (prevents copy-paste errors)

    Args:
        value (str): Client secret to validate

    Returns:
        str: Validated client secret

    Raises:
        serializers.ValidationError: If secret doesn't meet requirements

    Security Notes:
        - Azure-generated secrets are typically 40+ characters
        - Minimum of 20 chars ensures reasonable entropy
        - Space check prevents common copy-paste issues
    """
    if not value:
        raise serializers.ValidationError('Client secret cannot be empty.')

    if not isinstance(value, str):
        raise serializers.ValidationError('Client secret must be a string.')

    if len(value) < 20:
        raise serializers.ValidationError(
            'Client secret must be at least 20 characters long.'
        )

    if len(value) > 200:
        raise serializers.ValidationError(
            'Client secret cannot exceed 200 characters.'
        )

    if ' ' in value:
        raise serializers.ValidationError(
            'Client secret cannot contain spaces.'
        )

    return value


def validate_azure_filter_keys(filters):
    """
    Validate Azure API filter keys.

    Ensures only allowed filter keys are used for Azure Advisor API queries.

    Args:
        filters (dict): Filter dictionary to validate

    Returns:
        dict: Validated filters

    Raises:
        serializers.ValidationError: If invalid keys are present
    """
    if not filters:
        return filters

    if not isinstance(filters, dict):
        raise serializers.ValidationError('Filters must be a dictionary.')

    allowed_keys = {'category', 'impact', 'resource_group'}
    invalid_keys = set(filters.keys()) - allowed_keys

    if invalid_keys:
        raise serializers.ValidationError(
            f"Invalid filter keys: {', '.join(invalid_keys)}. "
            f"Allowed: {', '.join(allowed_keys)}"
        )

    return filters


def validate_azure_category(value):
    """
    Validate Azure Advisor recommendation category.

    Args:
        value (str): Category value to validate

    Returns:
        str: Validated category

    Raises:
        serializers.ValidationError: If category is invalid
    """
    valid_categories = [
        'Cost',
        'HighAvailability',
        'Performance',
        'Security',
        'OperationalExcellence'
    ]

    if value not in valid_categories:
        raise serializers.ValidationError(
            f'Invalid category. Must be one of: {", ".join(valid_categories)}'
        )

    return value


def validate_azure_impact(value):
    """
    Validate Azure Advisor recommendation impact level.

    Args:
        value (str): Impact level to validate

    Returns:
        str: Validated impact level

    Raises:
        serializers.ValidationError: If impact level is invalid
    """
    valid_impacts = ['High', 'Medium', 'Low']

    if value not in valid_impacts:
        raise serializers.ValidationError(
            f'Invalid impact. Must be one of: {", ".join(valid_impacts)}'
        )

    return value
