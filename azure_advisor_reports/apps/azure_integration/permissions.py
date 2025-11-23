"""
Custom permissions for Azure Integration app.

Provides fine-grained access control for Azure subscriptions and related resources.
"""

from rest_framework import permissions


class IsSubscriptionOwner(permissions.BasePermission):
    """
    Permission class to ensure users can only access their own Azure subscriptions.

    This permission checks that the user making the request is the creator
    of the Azure subscription being accessed.

    Usage:
        class AzureSubscriptionViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAuthenticated, IsSubscriptionOwner]
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if user owns the subscription.

        Args:
            request: DRF request object
            view: View being accessed
            obj: AzureSubscription instance

        Returns:
            bool: True if user created the subscription, False otherwise
        """
        # Read permissions are allowed to the owner
        if request.method in permissions.SAFE_METHODS:
            return obj.created_by == request.user

        # Write permissions only for owner
        return obj.created_by == request.user


class CanCreateReport(permissions.BasePermission):
    """
    Permission class to validate report creation requests.

    For Azure API-based reports, verifies that:
    1. The specified Azure subscription exists
    2. The subscription is active
    3. The user owns the subscription

    For CSV-based reports, allows creation without additional checks.

    Usage:
        class ReportViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAuthenticated, CanCreateReport]
    """

    message = 'You do not have permission to create reports with this Azure subscription.'

    def has_permission(self, request, view):
        """
        Check if user can create a report.

        Args:
            request: DRF request object
            view: View being accessed

        Returns:
            bool: True if user can create report, False otherwise
        """
        # Only check for POST (create) requests
        if request.method != 'POST':
            return True

        # Get data source from request
        data_source = request.data.get('data_source', 'csv')

        # CSV reports are always allowed (basic authentication check)
        if data_source == 'csv':
            return True

        # Azure API reports require subscription validation
        if data_source == 'azure_api':
            subscription_id = request.data.get('azure_subscription')

            if not subscription_id:
                # Let serializer validation handle this
                return True

            # Check if subscription exists and user owns it
            from apps.azure_integration.models import AzureSubscription

            try:
                subscription = AzureSubscription.objects.get(id=subscription_id)

                # Check ownership
                if subscription.created_by != request.user:
                    self.message = 'You do not own this Azure subscription.'
                    return False

                # Check if active
                if not subscription.is_active:
                    self.message = 'This Azure subscription is not active.'
                    return False

                return True

            except AzureSubscription.DoesNotExist:
                self.message = 'Azure subscription not found.'
                return False

        # Unknown data source - let serializer validation handle it
        return True


class CanManageAzureSubscription(permissions.BasePermission):
    """
    Permission class for Azure subscription management endpoints.

    Ensures users can only:
    - View their own subscriptions
    - Update/delete their own subscriptions
    - Test connections for their own subscriptions

    Usage:
        @action(detail=True, methods=['post'])
        @permission_classes([IsAuthenticated, CanManageAzureSubscription])
        def test_connection(self, request, pk=None):
            ...
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if user can manage the subscription.

        Args:
            request: DRF request object
            view: View being accessed
            obj: AzureSubscription instance

        Returns:
            bool: True if user owns the subscription, False otherwise
        """
        return obj.created_by == request.user
