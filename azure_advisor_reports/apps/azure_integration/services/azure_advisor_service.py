"""
Azure Advisor API service for fetching recommendations.

This module provides the AzureAdvisorService class that handles:
- Authentication with Azure using Service Principal credentials
- Fetching recommendations from Azure Advisor API
- Data transformation from Azure format to internal format
- Caching for performance optimization
- Retry logic for resilience
- Comprehensive error handling and logging
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

from django.core.cache import cache
from azure.identity import ClientSecretCredential
from azure.mgmt.advisor import AdvisorManagementClient
from azure.core.exceptions import (
    ClientAuthenticationError,
    HttpResponseError,
    ServiceRequestError,
    ResourceNotFoundError,
)
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from apps.azure_integration.models import AzureSubscription
from apps.azure_integration.exceptions import (
    AzureAuthenticationError,
    AzureAPIError,
    AzureConnectionError,
)

logger = logging.getLogger(__name__)


class AzureAdvisorService:
    """
    Service for interacting with Azure Advisor API.

    This service handles authentication, fetching recommendations,
    data transformation, caching, and error handling for Azure Advisor integration.

    Attributes:
        azure_subscription (AzureSubscription): The subscription to use for API calls
        credential (ClientSecretCredential): Azure authentication credential
        client (AdvisorManagementClient): Azure Advisor API client

    Example:
        >>> subscription = AzureSubscription.objects.get(name='Production')
        >>> service = AzureAdvisorService(subscription)
        >>> recommendations = service.fetch_recommendations(filters={'category': 'Cost'})
        >>> stats = service.get_statistics()
    """

    # Cache TTL in seconds (1 hour)
    CACHE_TTL = 3600

    # Valid filter values
    VALID_CATEGORIES = [
        'Cost',
        'HighAvailability',
        'Performance',
        'Security',
        'OperationalExcellence'
    ]

    VALID_IMPACTS = ['High', 'Medium', 'Low']

    def __init__(self, azure_subscription: AzureSubscription):
        """
        Initialize the Azure Advisor service.

        Args:
            azure_subscription (AzureSubscription): The subscription with credentials

        Raises:
            AzureAuthenticationError: If authentication fails
            AzureConnectionError: If cannot connect to Azure
        """
        self.azure_subscription = azure_subscription

        logger.info(
            f"Initializing AzureAdvisorService for subscription: "
            f"{azure_subscription.name} ({azure_subscription.subscription_id})"
        )

        try:
            # Get decrypted credentials
            credentials = azure_subscription.get_credentials()

            # Initialize Azure credential
            self.credential = ClientSecretCredential(
                tenant_id=credentials['tenant_id'],
                client_id=credentials['client_id'],
                client_secret=credentials['client_secret']
            )

            # Initialize Advisor client
            self.client = AdvisorManagementClient(
                credential=self.credential,
                subscription_id=credentials['subscription_id']
            )

            logger.info(
                f"Successfully initialized Azure Advisor client for "
                f"subscription {azure_subscription.subscription_id}"
            )

        except ClientAuthenticationError as e:
            error_msg = f"Authentication failed for subscription {azure_subscription.name}: {str(e)}"
            logger.error(error_msg)
            raise AzureAuthenticationError(error_msg) from e

        except Exception as e:
            error_msg = f"Failed to initialize Azure client: {str(e)}"
            logger.error(error_msg)
            raise AzureConnectionError(error_msg) from e

    def _generate_cache_key(self, filters: Optional[Dict] = None) -> str:
        """
        Generate a cache key based on subscription and filters.

        Args:
            filters (dict, optional): Filter dictionary

        Returns:
            str: Cache key for storing/retrieving cached data
        """
        subscription_id = self.azure_subscription.subscription_id

        # Create a stable hash of filters
        if filters:
            # Sort keys to ensure consistent hashing
            filter_str = json.dumps(filters, sort_keys=True)
            filter_hash = hashlib.md5(filter_str.encode()).hexdigest()
        else:
            filter_hash = 'no_filters'

        return f"azure_advisor:{subscription_id}:recommendations:{filter_hash}"

    def _validate_filters(self, filters: Optional[Dict]) -> None:
        """
        Validate filter parameters.

        Args:
            filters (dict, optional): Filters to validate

        Raises:
            ValueError: If filter values are invalid
        """
        if not filters:
            return

        if 'category' in filters:
            category = filters['category']
            if category not in self.VALID_CATEGORIES:
                raise ValueError(
                    f"Invalid category '{category}'. "
                    f"Must be one of: {', '.join(self.VALID_CATEGORIES)}"
                )

        if 'impact' in filters:
            impact = filters['impact']
            if impact not in self.VALID_IMPACTS:
                raise ValueError(
                    f"Invalid impact '{impact}'. "
                    f"Must be one of: {', '.join(self.VALID_IMPACTS)}"
                )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((HttpResponseError, ServiceRequestError)),
        reraise=True
    )
    def _fetch_recommendations_from_api(self) -> List:
        """
        Fetch recommendations from Azure API with retry logic.

        Returns:
            List: Raw recommendation objects from Azure API

        Raises:
            HttpResponseError: If API returns an error (retriable)
            ServiceRequestError: If network error occurs (retriable)
            ClientAuthenticationError: If authentication fails (not retriable)
            ResourceNotFoundError: If subscription not found (not retriable)
        """
        logger.info(
            f"Fetching recommendations from Azure Advisor API for "
            f"subscription {self.azure_subscription.subscription_id}"
        )

        try:
            recommendations = []

            # Azure SDK returns paged results
            paged_results = self.client.recommendations.list()

            # Iterate through all pages
            for recommendation in paged_results:
                recommendations.append(recommendation)

            logger.info(
                f"Successfully fetched {len(recommendations)} recommendations "
                f"from Azure Advisor API"
            )

            return recommendations

        except ClientAuthenticationError as e:
            # Not retriable - convert immediately
            error_msg = f"Authentication failed: {str(e)}"
            logger.error(error_msg)
            raise AzureAuthenticationError(error_msg) from e

        except ResourceNotFoundError as e:
            # Not retriable - convert immediately
            error_msg = (
                f"Subscription not found: "
                f"{self.azure_subscription.subscription_id}. Error: {str(e)}"
            )
            logger.error(error_msg)
            raise AzureAPIError(error_msg) from e

        # Let HttpResponseError and ServiceRequestError bubble up for retry decorator
        # They will be caught and converted in fetch_recommendations after retries exhausted

    def _transform_recommendation(self, recommendation) -> Dict:
        """
        Transform Azure API recommendation to internal format.

        Args:
            recommendation: Azure recommendation object

        Returns:
            dict: Recommendation in internal format
        """
        # Extract basic properties
        rec_id = recommendation.id or ''
        category = recommendation.category or 'Unknown'
        impact = recommendation.impact or 'Low'

        # Extract resource information
        impacted_field = recommendation.impacted_field or ''
        impacted_value = recommendation.impacted_value or ''

        # Determine risk level based on impact
        risk_mapping = {
            'High': 'Error',
            'Medium': 'Warning',
            'Low': 'None'
        }
        risk = risk_mapping.get(impact, 'None')

        # Extract short description (from short_description if available)
        short_desc = ''
        if hasattr(recommendation, 'short_description') and recommendation.short_description:
            short_desc = recommendation.short_description.get('problem', '')

        # Extract detailed description (from extended_properties if available)
        description = ''
        if hasattr(recommendation, 'extended_properties'):
            extended_props = recommendation.extended_properties or {}
            description = extended_props.get('recommendationText', short_desc)

        if not description:
            description = short_desc

        # Extract resource information
        resource_metadata = recommendation.resource_metadata or {}
        resource_id = resource_metadata.get('resourceId', impacted_value)

        # Parse resource ID to extract resource group and resource name
        resource_group = ''
        resource_name = impacted_value
        resource_type = impacted_field

        if resource_id and '/resourceGroups/' in resource_id:
            parts = resource_id.split('/resourceGroups/')
            if len(parts) > 1:
                rg_parts = parts[1].split('/')
                resource_group = rg_parts[0] if rg_parts else ''
                # Extract resource name (last part of resource ID)
                if len(rg_parts) > 1:
                    resource_name = rg_parts[-1]

        # Extract cost savings information (for Cost category)
        potential_savings = None
        currency = None

        if category == 'Cost':
            extended_props = getattr(recommendation, 'extended_properties', {}) or {}

            # Try different possible field names for savings
            savings_str = (
                extended_props.get('savingsAmount') or
                extended_props.get('annualSavingsAmount') or
                extended_props.get('savings')
            )

            if savings_str:
                try:
                    # Handle both string and numeric formats
                    if isinstance(savings_str, str):
                        # Remove currency symbols and convert to float
                        savings_clean = savings_str.replace('$', '').replace(',', '').strip()
                        potential_savings = float(savings_clean)
                    else:
                        potential_savings = float(savings_str)
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse savings amount: {savings_str}")

            # Extract currency
            currency = extended_props.get('savingsCurrency', 'USD')

        # Extract last updated timestamp
        from django.utils import timezone
        last_updated = timezone.now().isoformat()
        if hasattr(recommendation, 'last_updated') and recommendation.last_updated:
            try:
                last_updated = recommendation.last_updated.isoformat()
            except AttributeError:
                last_updated = str(recommendation.last_updated)

        # Build metadata dictionary
        metadata = {
            'recommendation_type_id': getattr(recommendation, 'recommendation_type_id', None),
            'suppression_ids': getattr(recommendation, 'suppression_ids', []),
            'extended_properties': getattr(recommendation, 'extended_properties', {}),
        }

        return {
            'id': rec_id,
            'category': category,
            'impact': impact,
            'risk': risk,
            'impacted_resource': resource_name,
            'resource_type': resource_type,
            'resource_group': resource_group,
            'recommendation': short_desc,
            'description': description,
            'potential_savings': potential_savings,
            'currency': currency,
            'last_updated': last_updated,
            'metadata': metadata,
        }

    def _apply_filters(
        self,
        recommendations: List[Dict],
        filters: Optional[Dict]
    ) -> List[Dict]:
        """
        Apply filters to recommendations list.

        Args:
            recommendations (list): List of recommendations
            filters (dict, optional): Filters to apply

        Returns:
            list: Filtered recommendations
        """
        if not filters:
            return recommendations

        filtered = recommendations

        # Filter by category
        if 'category' in filters:
            category = filters['category']
            filtered = [r for r in filtered if r['category'] == category]
            logger.debug(f"Filtered by category '{category}': {len(filtered)} results")

        # Filter by impact
        if 'impact' in filters:
            impact = filters['impact']
            filtered = [r for r in filtered if r['impact'] == impact]
            logger.debug(f"Filtered by impact '{impact}': {len(filtered)} results")

        # Filter by resource group
        if 'resource_group' in filters:
            resource_group = filters['resource_group']
            filtered = [
                r for r in filtered
                if r['resource_group'].lower() == resource_group.lower()
            ]
            logger.debug(
                f"Filtered by resource group '{resource_group}': {len(filtered)} results"
            )

        return filtered

    def fetch_recommendations(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Fetch recommendations from Azure Advisor API.

        This method:
        1. Validates filters
        2. Checks cache for existing results
        3. Fetches from API if not cached
        4. Transforms data to internal format
        5. Applies filters
        6. Caches results

        Args:
            filters (dict, optional): Dictionary with filter options:
                - category (str): Filter by category
                - impact (str): Filter by impact level
                - resource_group (str): Filter by resource group name

        Returns:
            list: List of recommendations in internal format

        Raises:
            ValueError: If filter values are invalid
            AzureAuthenticationError: If authentication fails
            AzureAPIError: If API call fails
            AzureConnectionError: If network error occurs

        Example:
            >>> service = AzureAdvisorService(subscription)
            >>> # Fetch all recommendations
            >>> all_recs = service.fetch_recommendations()
            >>> # Fetch only cost recommendations
            >>> cost_recs = service.fetch_recommendations({'category': 'Cost'})
            >>> # Fetch high-impact security recommendations
            >>> security_recs = service.fetch_recommendations({
            ...     'category': 'Security',
            ...     'impact': 'High'
            ... })
        """
        # Validate filters
        self._validate_filters(filters)

        # Generate cache key
        cache_key = self._generate_cache_key(filters)

        # Try to get from cache
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(
                f"Cache hit for key {cache_key}: returning {len(cached_data)} "
                f"cached recommendations"
            )
            return cached_data

        logger.info(f"Cache miss for key {cache_key}: fetching from API")

        # Fetch from API with retry logic
        try:
            raw_recommendations = self._fetch_recommendations_from_api()

            # Transform to internal format
            transformed = [
                self._transform_recommendation(rec)
                for rec in raw_recommendations
            ]

            logger.info(f"Transformed {len(transformed)} recommendations to internal format")

            # Apply filters
            filtered = self._apply_filters(transformed, filters)

            logger.info(
                f"Filtered results: {len(filtered)} recommendations "
                f"(from {len(transformed)} total)"
            )

            # Cache the results
            cache.set(cache_key, filtered, self.CACHE_TTL)
            logger.info(f"Cached {len(filtered)} recommendations with TTL {self.CACHE_TTL}s")

            return filtered

        except (AzureAuthenticationError, AzureAPIError, AzureConnectionError):
            # Re-raise our custom exceptions
            raise

        except HttpResponseError as e:
            # Retries exhausted, convert to our exception
            error_msg = f"Azure API error after retries: {str(e)}"
            logger.error(error_msg)
            raise AzureAPIError(error_msg) from e

        except ServiceRequestError as e:
            # Retries exhausted, convert to our exception
            error_msg = f"Network error after retries: {str(e)}"
            logger.error(error_msg)
            raise AzureConnectionError(error_msg) from e

        except Exception as e:
            error_msg = f"Unexpected error in fetch_recommendations: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise AzureAPIError(error_msg) from e

    def test_connection(self) -> Dict:
        """
        Test Azure connection and credentials.

        This method attempts to authenticate and fetch subscription details
        to verify that the credentials are valid and have proper permissions.

        Returns:
            dict: Connection test results with keys:
                - success (bool): Whether connection succeeded
                - subscription_id (str): The subscription ID
                - subscription_name (str or None): Subscription name if available
                - error_message (str or None): Error details if failed

        Example:
            >>> service = AzureAdvisorService(subscription)
            >>> result = service.test_connection()
            >>> if result['success']:
            ...     print(f"Connected to {result['subscription_name']}")
            ... else:
            ...     print(f"Connection failed: {result['error_message']}")
        """
        logger.info(
            f"Testing connection for subscription "
            f"{self.azure_subscription.subscription_id}"
        )

        try:
            # Try to fetch a single recommendation to test the connection
            # This verifies both authentication and API access
            paged_results = self.client.recommendations.list()

            # Just check if we can iterate (don't need to fetch all)
            try:
                next(iter(paged_results))
            except StopIteration:
                # Empty results are fine - connection works
                pass

            logger.info("Connection test successful")

            return {
                'success': True,
                'subscription_id': self.azure_subscription.subscription_id,
                'subscription_name': self.azure_subscription.name,
                'error_message': None,
            }

        except ClientAuthenticationError as e:
            error_msg = f"Authentication failed: {str(e)}"
            logger.error(f"Connection test failed: {error_msg}")
            return {
                'success': False,
                'subscription_id': self.azure_subscription.subscription_id,
                'subscription_name': None,
                'error_message': error_msg,
            }

        except (HttpResponseError, ResourceNotFoundError) as e:
            error_msg = f"API error: {str(e)}"
            logger.error(f"Connection test failed: {error_msg}")
            return {
                'success': False,
                'subscription_id': self.azure_subscription.subscription_id,
                'subscription_name': None,
                'error_message': error_msg,
            }

        except ServiceRequestError as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(f"Connection test failed: {error_msg}")
            return {
                'success': False,
                'subscription_id': self.azure_subscription.subscription_id,
                'subscription_name': None,
                'error_message': error_msg,
            }

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Connection test failed: {error_msg}", exc_info=True)
            return {
                'success': False,
                'subscription_id': self.azure_subscription.subscription_id,
                'subscription_name': None,
                'error_message': error_msg,
            }

    def get_statistics(self) -> Dict:
        """
        Get summary statistics of recommendations.

        This method fetches all recommendations (using cache if available)
        and calculates statistics by category, impact, and potential savings.

        Returns:
            dict: Statistics dictionary with keys:
                - total_recommendations (int): Total number of recommendations
                - by_category (dict): Count by category
                - by_impact (dict): Count by impact level
                - total_potential_savings (float or None): Sum of cost savings
                - currency (str or None): Currency code

        Example:
            >>> service = AzureAdvisorService(subscription)
            >>> stats = service.get_statistics()
            >>> print(f"Total recommendations: {stats['total_recommendations']}")
            >>> print(f"High impact: {stats['by_impact']['High']}")
            >>> if stats['total_potential_savings']:
            ...     print(f"Potential savings: {stats['total_potential_savings']} "
            ...           f"{stats['currency']}")
        """
        # Generate cache key for statistics
        cache_key = f"azure_advisor:{self.azure_subscription.subscription_id}:statistics"

        # Try to get from cache
        cached_stats = cache.get(cache_key)
        if cached_stats is not None:
            logger.info("Cache hit for statistics")
            return cached_stats

        logger.info("Cache miss for statistics: calculating from recommendations")

        # Fetch all recommendations (this will use recommendation cache if available)
        try:
            recommendations = self.fetch_recommendations()

            # Initialize counters
            by_category = {cat: 0 for cat in self.VALID_CATEGORIES}
            by_impact = {imp: 0 for imp in self.VALID_IMPACTS}
            total_savings = 0.0
            currency = None

            # Calculate statistics
            for rec in recommendations:
                # Count by category
                category = rec.get('category')
                if category in by_category:
                    by_category[category] += 1

                # Count by impact
                impact = rec.get('impact')
                if impact in by_impact:
                    by_impact[impact] += 1

                # Sum potential savings
                savings = rec.get('potential_savings')
                if savings is not None:
                    total_savings += savings
                    if currency is None:
                        currency = rec.get('currency', 'USD')

            # Build statistics dictionary
            stats = {
                'total_recommendations': len(recommendations),
                'by_category': by_category,
                'by_impact': by_impact,
                'total_potential_savings': total_savings if total_savings > 0 else None,
                'currency': currency,
            }

            # Cache the statistics
            cache.set(cache_key, stats, self.CACHE_TTL)
            logger.info(f"Cached statistics with TTL {self.CACHE_TTL}s")

            return stats

        except Exception as e:
            error_msg = f"Error calculating statistics: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise AzureAPIError(error_msg) from e
