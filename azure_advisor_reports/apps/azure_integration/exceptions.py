"""
Custom exceptions for Azure Integration.

This module defines specific exception types for Azure API integration errors,
allowing for granular error handling and better error messages.
"""


class AzureIntegrationError(Exception):
    """
    Base exception for Azure integration errors.

    All Azure integration-specific exceptions inherit from this class,
    making it easy to catch all Azure-related errors with a single except block.
    """
    pass


class AzureAuthenticationError(AzureIntegrationError):
    """
    Authentication failed with Azure.

    Raised when:
    - Invalid credentials (client_id, client_secret, tenant_id)
    - Expired credentials
    - Insufficient permissions
    - Service Principal not found

    Examples:
        >>> raise AzureAuthenticationError("Invalid client secret")
        >>> raise AzureAuthenticationError("Service Principal lacks Reader role")
    """
    pass


class AzureAPIError(AzureIntegrationError):
    """
    Azure API returned an error.

    Raised when:
    - API returns 4xx or 5xx status codes
    - Subscription not found
    - Resource not found
    - Rate limiting
    - API quota exceeded

    Examples:
        >>> raise AzureAPIError("Subscription not found: abc-123")
        >>> raise AzureAPIError("Rate limit exceeded, retry after 60s")
    """
    pass


class AzureConnectionError(AzureIntegrationError):
    """
    Cannot connect to Azure.

    Raised when:
    - Network connectivity issues
    - Timeout errors
    - DNS resolution failures
    - Service unavailable

    Examples:
        >>> raise AzureConnectionError("Connection timeout after 30s")
        >>> raise AzureConnectionError("Cannot resolve management.azure.com")
    """
    pass
