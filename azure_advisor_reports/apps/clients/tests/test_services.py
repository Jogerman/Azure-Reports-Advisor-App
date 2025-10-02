"""
Tests for client services (business logic).
"""

import pytest
from django.contrib.auth import get_user_model
from apps.clients.models import Client, ClientContact, ClientNote
from apps.clients.services import ClientService, ClientContactService, ClientNoteService

User = get_user_model()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def test_client(db, test_user):
    """Create a test client."""
    return Client.objects.create(
        company_name="Test Company",
        industry="technology",
        contact_email="contact@testcompany.com",
        status="active",
        created_by=test_user
    )


@pytest.mark.django_db
class TestClientService:
    """Tests for ClientService."""

    def test_create_client_success(self, test_user):
        """Test successful client creation."""
        data = {
            'company_name': 'New Corp',
            'industry': 'technology',
            'contact_email': 'contact@newcorp.com',
            'status': 'active'
        }

        client = ClientService.create_client(data, test_user)

        assert client is not None
        assert client.company_name == 'New Corp'
        assert client.created_by == test_user
        assert Client.objects.filter(company_name='New Corp').exists()

    def test_create_client_with_subscriptions(self, test_user):
        """Test creating client with Azure subscription IDs."""
        data = {
            'company_name': 'New Corp',
            'industry': 'technology',
            'contact_email': 'contact@newcorp.com',
            'azure_subscription_ids': [
                '12345678-1234-1234-1234-123456789012',
                '87654321-4321-4321-4321-210987654321'
            ]
        }

        client = ClientService.create_client(data, test_user)

        assert client is not None
        assert len(client.azure_subscription_ids) == 2

    def test_update_client_success(self, test_client, test_user):
        """Test successful client update."""
        data = {
            'company_name': 'Updated Company',
            'industry': 'finance'
        }

        updated_client = ClientService.update_client(test_client, data, test_user)

        assert updated_client is not None
        assert updated_client.company_name == 'Updated Company'
        assert updated_client.industry == 'finance'

    def test_update_client_partial(self, test_client, test_user):
        """Test partial client update."""
        original_industry = test_client.industry
        data = {
            'company_name': 'Partially Updated'
        }

        updated_client = ClientService.update_client(test_client, data, test_user)

        assert updated_client is not None
        assert updated_client.company_name == 'Partially Updated'
        assert updated_client.industry == original_industry

    def test_deactivate_client_success(self, test_client, test_user):
        """Test successful client deactivation."""
        assert test_client.status == 'active'

        success = ClientService.deactivate_client(test_client, test_user)

        assert success is True
        test_client.refresh_from_db()
        assert test_client.status == 'inactive'

    def test_activate_client_success(self, test_client, test_user):
        """Test successful client activation."""
        test_client.status = 'inactive'
        test_client.save()

        success = ClientService.activate_client(test_client, test_user)

        assert success is True
        test_client.refresh_from_db()
        assert test_client.status == 'active'

    def test_add_subscription_success(self, test_client, test_user):
        """Test adding Azure subscription to client."""
        subscription_id = '12345678-1234-1234-1234-123456789012'
        initial_count = len(test_client.azure_subscription_ids or [])

        success = ClientService.add_subscription(test_client, subscription_id, test_user)

        assert success is True
        test_client.refresh_from_db()
        assert len(test_client.azure_subscription_ids) == initial_count + 1
        assert subscription_id in test_client.azure_subscription_ids

    def test_add_duplicate_subscription(self, test_client, test_user):
        """Test that duplicate subscriptions are not added."""
        subscription_id = '12345678-1234-1234-1234-123456789012'

        # Add subscription first time
        ClientService.add_subscription(test_client, subscription_id, test_user)
        test_client.refresh_from_db()
        count_after_first = len(test_client.azure_subscription_ids)

        # Try to add same subscription again
        ClientService.add_subscription(test_client, subscription_id, test_user)
        test_client.refresh_from_db()
        count_after_second = len(test_client.azure_subscription_ids)

        assert count_after_first == count_after_second

    def test_remove_subscription_success(self, test_client, test_user):
        """Test removing Azure subscription from client."""
        subscription_id = '12345678-1234-1234-1234-123456789012'

        # Add subscription first
        test_client.add_subscription(subscription_id)
        test_client.refresh_from_db()
        assert subscription_id in test_client.azure_subscription_ids

        # Remove subscription
        success = ClientService.remove_subscription(test_client, subscription_id, test_user)

        assert success is True
        test_client.refresh_from_db()
        assert subscription_id not in test_client.azure_subscription_ids

    def test_remove_nonexistent_subscription(self, test_client, test_user):
        """Test removing subscription that doesn't exist."""
        subscription_id = 'nonexistent-id'

        success = ClientService.remove_subscription(test_client, subscription_id, test_user)

        # Should still return success even if subscription doesn't exist
        assert success is True

    def test_get_client_statistics(self, test_client):
        """Test getting client statistics."""
        # Create additional clients
        Client.objects.create(
            company_name="Client 2",
            industry="healthcare",
            contact_email="client2@example.com",
            status="active"
        )
        Client.objects.create(
            company_name="Client 3",
            industry="technology",
            contact_email="client3@example.com",
            status="inactive"
        )

        stats = ClientService.get_client_statistics()

        assert stats is not None
        assert 'total_clients' in stats
        assert 'active_clients' in stats
        assert 'inactive_clients' in stats
        assert 'suspended_clients' in stats
        assert 'clients_by_industry' in stats
        assert stats['total_clients'] >= 3

    def test_search_clients_by_name(self, test_client):
        """Test searching clients by company name."""
        # Create additional clients
        Client.objects.create(
            company_name="Another Company",
            contact_email="another@example.com"
        )
        Client.objects.create(
            company_name="Different Corp",
            contact_email="different@example.com"
        )

        results = ClientService.search_clients("Test")

        assert len(results) >= 1
        assert any(client.company_name == "Test Company" for client in results)

    def test_search_clients_with_filters(self, test_client):
        """Test searching clients with filters."""
        # Create clients with different statuses
        Client.objects.create(
            company_name="Active Corp",
            industry="technology",
            contact_email="active@example.com",
            status="active"
        )
        Client.objects.create(
            company_name="Inactive Corp",
            industry="finance",
            contact_email="inactive@example.com",
            status="inactive"
        )

        # Filter by status
        results = ClientService.search_clients("", filters={'status': 'active'})

        assert len(results) >= 2
        assert all(client.status == 'active' for client in results)

    def test_search_clients_by_email(self, test_client):
        """Test searching clients by email."""
        results = ClientService.search_clients("testcompany.com")

        assert len(results) >= 1
        assert any("testcompany.com" in client.contact_email for client in results)


@pytest.mark.django_db
class TestClientContactService:
    """Tests for ClientContactService."""

    def test_create_contact_success(self, test_client, test_user):
        """Test successful contact creation."""
        data = {
            'name': 'John Doe',
            'email': 'john@testcompany.com',
            'phone': '+1-555-0123',
            'role': 'primary',
            'title': 'CEO'
        }

        contact = ClientContactService.create_contact(test_client, data, test_user)

        assert contact is not None
        assert contact.name == 'John Doe'
        assert contact.email == 'john@testcompany.com'
        assert contact.client == test_client
        assert ClientContact.objects.filter(client=test_client).count() == 1

    def test_create_contact_minimal_data(self, test_client, test_user):
        """Test creating contact with minimal required data."""
        data = {
            'name': 'Jane Doe',
            'email': 'jane@testcompany.com'
        }

        contact = ClientContactService.create_contact(test_client, data, test_user)

        assert contact is not None
        assert contact.name == 'Jane Doe'
        assert contact.role == 'other'  # Default role

    def test_create_primary_contact(self, test_client, test_user):
        """Test creating a primary contact."""
        data = {
            'name': 'Primary Contact',
            'email': 'primary@testcompany.com',
            'is_primary': True
        }

        contact = ClientContactService.create_contact(test_client, data, test_user)

        assert contact is not None
        assert contact.is_primary is True


@pytest.mark.django_db
class TestClientNoteService:
    """Tests for ClientNoteService."""

    def test_create_note_success(self, test_client, test_user):
        """Test successful note creation."""
        note = ClientNoteService.create_note(
            client=test_client,
            author=test_user,
            note_type='meeting',
            subject='Initial Meeting',
            content='Discussed project requirements and timeline.'
        )

        assert note is not None
        assert note.subject == 'Initial Meeting'
        assert note.content == 'Discussed project requirements and timeline.'
        assert note.client == test_client
        assert note.author == test_user
        assert note.note_type == 'meeting'
        assert ClientNote.objects.filter(client=test_client).count() == 1

    def test_create_note_default_type(self, test_client, test_user):
        """Test creating note with default type."""
        note = ClientNoteService.create_note(
            client=test_client,
            author=test_user,
            note_type='general',
            subject='General Note',
            content='Some general information'
        )

        assert note is not None
        assert note.note_type == 'general'

    def test_create_note_with_related_report(self, test_client, test_user):
        """Test creating note with related report reference."""
        # Note: This test assumes Report model exists
        # If Report model is not yet implemented, this test will be skipped
        try:
            from apps.reports.models import Report

            report = Report.objects.create(
                client=test_client,
                created_by=test_user,
                report_type='detailed',
                status='pending'
            )

            note = ClientNoteService.create_note(
                client=test_client,
                author=test_user,
                note_type='general',
                subject='Report Note',
                content='Note related to specific report',
                related_report=report
            )

            assert note is not None
            assert note.related_report == report
        except ImportError:
            pytest.skip("Report model not yet implemented")

    def test_create_multiple_notes(self, test_client, test_user):
        """Test creating multiple notes for a client."""
        for i in range(3):
            ClientNoteService.create_note(
                client=test_client,
                author=test_user,
                note_type='general',
                subject=f'Note {i+1}',
                content=f'Content for note {i+1}'
            )

        assert ClientNote.objects.filter(client=test_client).count() == 3

    def test_note_ordering(self, test_client, test_user):
        """Test that notes are ordered by created_at descending."""
        import time

        note1 = ClientNoteService.create_note(
            client=test_client,
            author=test_user,
            note_type='general',
            subject='First Note',
            content='First'
        )

        time.sleep(0.1)

        note2 = ClientNoteService.create_note(
            client=test_client,
            author=test_user,
            note_type='general',
            subject='Second Note',
            content='Second'
        )

        notes = list(ClientNote.objects.filter(client=test_client))
        assert notes[0] == note2  # Most recent first
        assert notes[1] == note1
