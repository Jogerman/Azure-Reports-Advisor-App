"""
Business logic services for client management.
"""

import logging
from typing import Optional, Dict, List
from django.db.models import Count, Q, Sum
from django.contrib.auth import get_user_model
from .models import Client, ClientContact, ClientNote

User = get_user_model()
logger = logging.getLogger(__name__)


class ClientService:
    """
    Service class for client-related business logic.
    """

    @staticmethod
    def create_client(data: Dict, created_by: User) -> Optional[Client]:
        """
        Create a new client with validation.

        Args:
            data: Dictionary containing client data
            created_by: User creating the client

        Returns:
            Created Client instance or None
        """
        try:
            client = Client.objects.create(
                **data,
                created_by=created_by
            )

            logger.info(
                f"Client '{client.company_name}' created by {created_by.email}"
            )

            return client

        except Exception as e:
            logger.error(f"Error creating client: {str(e)}")
            return None

    @staticmethod
    def update_client(
        client: Client,
        data: Dict,
        updated_by: User
    ) -> Optional[Client]:
        """
        Update existing client.

        Args:
            client: Client instance to update
            data: Dictionary containing updated data
            updated_by: User performing the update

        Returns:
            Updated Client instance or None
        """
        try:
            for field, value in data.items():
                if hasattr(client, field):
                    setattr(client, field, value)

            client.save()

            logger.info(
                f"Client '{client.company_name}' updated by {updated_by.email}"
            )

            return client

        except Exception as e:
            logger.error(f"Error updating client: {str(e)}")
            return None

    @staticmethod
    def deactivate_client(client: Client, deactivated_by: User) -> bool:
        """
        Deactivate a client (soft delete).

        Args:
            client: Client instance to deactivate
            deactivated_by: User performing the deactivation

        Returns:
            Boolean indicating success
        """
        try:
            client.status = 'inactive'
            client.save(update_fields=['status'])

            logger.info(
                f"Client '{client.company_name}' deactivated by {deactivated_by.email}"
            )

            return True

        except Exception as e:
            logger.error(f"Error deactivating client: {str(e)}")
            return False

    @staticmethod
    def activate_client(client: Client, activated_by: User) -> bool:
        """
        Activate a client.

        Args:
            client: Client instance to activate
            activated_by: User performing the activation

        Returns:
            Boolean indicating success
        """
        try:
            client.status = 'active'
            client.save(update_fields=['status'])

            logger.info(
                f"Client '{client.company_name}' activated by {activated_by.email}"
            )

            return True

        except Exception as e:
            logger.error(f"Error activating client: {str(e)}")
            return False

    @staticmethod
    def add_subscription(
        client: Client,
        subscription_id: str,
        added_by: User
    ) -> bool:
        """
        Add Azure subscription to client.

        Args:
            client: Client instance
            subscription_id: Azure subscription ID
            added_by: User adding the subscription

        Returns:
            Boolean indicating success
        """
        try:
            client.add_subscription(subscription_id)

            logger.info(
                f"Subscription {subscription_id} added to client "
                f"'{client.company_name}' by {added_by.email}"
            )

            return True

        except Exception as e:
            logger.error(f"Error adding subscription: {str(e)}")
            return False

    @staticmethod
    def remove_subscription(
        client: Client,
        subscription_id: str,
        removed_by: User
    ) -> bool:
        """
        Remove Azure subscription from client.

        Args:
            client: Client instance
            subscription_id: Azure subscription ID
            removed_by: User removing the subscription

        Returns:
            Boolean indicating success
        """
        try:
            client.remove_subscription(subscription_id)

            logger.info(
                f"Subscription {subscription_id} removed from client "
                f"'{client.company_name}' by {removed_by.email}"
            )

            return True

        except Exception as e:
            logger.error(f"Error removing subscription: {str(e)}")
            return False

    @staticmethod
    def get_client_statistics() -> Dict:
        """
        Get statistics about clients.

        Returns:
            Dictionary containing client statistics
        """
        try:
            from apps.reports.models import Report

            total_clients = Client.objects.count()
            active_clients = Client.objects.filter(status='active').count()
            inactive_clients = Client.objects.filter(status='inactive').count()
            suspended_clients = Client.objects.filter(status='suspended').count()

            # Clients by industry
            clients_by_industry = dict(
                Client.objects.values_list('industry')
                .annotate(count=Count('id'))
            )

            # Subscription statistics
            total_subscriptions = sum(
                client.subscription_count
                for client in Client.objects.all()
            )

            # Report statistics
            total_reports = Report.objects.count()
            clients_with_reports = Client.objects.filter(
                reports__isnull=False
            ).distinct().count()
            clients_without_reports = total_clients - clients_with_reports

            stats = {
                'total_clients': total_clients,
                'active_clients': active_clients,
                'inactive_clients': inactive_clients,
                'suspended_clients': suspended_clients,
                'clients_by_industry': clients_by_industry,
                'total_subscriptions': total_subscriptions,
                'total_reports': total_reports,
                'clients_with_reports': clients_with_reports,
                'clients_without_reports': clients_without_reports,
            }

            logger.info("Client statistics generated successfully")

            return stats

        except Exception as e:
            logger.error(f"Error generating client statistics: {str(e)}")
            return {}

    @staticmethod
    def search_clients(query: str, filters: Optional[Dict] = None) -> List[Client]:
        """
        Search clients by query and filters.

        Args:
            query: Search query string
            filters: Optional dictionary of filters

        Returns:
            List of matching Client instances
        """
        try:
            queryset = Client.objects.all()

            # Apply search query
            if query:
                queryset = queryset.filter(
                    Q(company_name__icontains=query) |
                    Q(contact_email__icontains=query) |
                    Q(contact_person__icontains=query) |
                    Q(notes__icontains=query)
                )

            # Apply filters
            if filters:
                if 'status' in filters:
                    queryset = queryset.filter(status=filters['status'])

                if 'industry' in filters:
                    queryset = queryset.filter(industry=filters['industry'])

                if 'account_manager' in filters:
                    queryset = queryset.filter(
                        account_manager_id=filters['account_manager']
                    )

            return list(queryset.order_by('company_name'))

        except Exception as e:
            logger.error(f"Error searching clients: {str(e)}")
            return []


class ClientContactService:
    """
    Service class for client contact management.
    """

    @staticmethod
    def create_contact(client: Client, data: Dict, created_by: User) -> Optional[ClientContact]:
        """
        Create a new client contact.

        Args:
            client: Client instance
            data: Contact data dictionary
            created_by: User creating the contact

        Returns:
            Created ClientContact instance or None
        """
        try:
            contact = ClientContact.objects.create(
                client=client,
                **data
            )

            logger.info(
                f"Contact '{contact.name}' created for client "
                f"'{client.company_name}' by {created_by.email}"
            )

            return contact

        except Exception as e:
            logger.error(f"Error creating client contact: {str(e)}")
            return None


class ClientNoteService:
    """
    Service class for client note management.
    """

    @staticmethod
    def create_note(
        client: Client,
        author: User,
        note_type: str,
        subject: str,
        content: str,
        related_report=None
    ) -> Optional[ClientNote]:
        """
        Create a new client note.

        Args:
            client: Client instance
            author: User creating the note
            note_type: Type of note
            subject: Note subject
            content: Note content
            related_report: Optional related report

        Returns:
            Created ClientNote instance or None
        """
        try:
            note = ClientNote.objects.create(
                client=client,
                author=author,
                note_type=note_type,
                subject=subject,
                content=content,
                related_report=related_report
            )

            logger.info(
                f"Note '{note.subject}' created for client "
                f"'{client.company_name}' by {author.email}"
            )

            return note

        except Exception as e:
            logger.error(f"Error creating client note: {str(e)}")
            return None