"""
Tests for client serializers.
"""

import pytest
from django.contrib.auth import get_user_model
from apps.clients.models import Client, ClientContact
from apps.clients.serializers import (
    ClientListSerializer,
    ClientDetailSerializer,
    ClientCreateUpdateSerializer,
    ClientContactSerializer,
)

User = get_user_model()


@pytest.mark.django_db
class TestClientListSerializer:
    """Tests for ClientListSerializer."""

    def test_serializer_fields(self):
        """Test that serializer has expected fields."""
        serializer = ClientListSerializer()
        expected_fields = {
            'id', 'company_name', 'industry', 'status', 'contact_email',
            'subscription_count', 'total_reports', 'account_manager_name',
            'created_at', 'updated_at', 'status_display', 'industry_display'
        }
        assert set(serializer.fields.keys()) == expected_fields

    def test_serialize_client(self):
        """Test serializing a client instance."""
        client = Client.objects.create(
            company_name="Test Corp",
            industry="technology",
            contact_email="contact@testcorp.com",
            status="active"
        )

        serializer = ClientListSerializer(client)
        data = serializer.data

        assert data['company_name'] == "Test Corp"
        assert data['industry'] == "technology"
        assert data['status'] == "active"
        assert data['contact_email'] == "contact@testcorp.com"
        assert 'id' in data
        assert 'created_at' in data


@pytest.mark.django_db
class TestClientDetailSerializer:
    """Tests for ClientDetailSerializer."""

    def test_serializer_includes_related_data(self):
        """Test that detail serializer includes contacts and notes."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )

        client = Client.objects.create(
            company_name="Test Corp",
            industry="technology",
            contact_email="contact@testcorp.com",
            created_by=user
        )

        # Add a contact
        ClientContact.objects.create(
            client=client,
            name="John Doe",
            email="john@testcorp.com",
            role="primary"
        )

        serializer = ClientDetailSerializer(client)
        data = serializer.data

        assert 'contacts' in data
        assert 'client_notes' in data
        assert len(data['contacts']) == 1
        assert data['contacts'][0]['name'] == "John Doe"


@pytest.mark.django_db
class TestClientCreateUpdateSerializer:
    """Tests for ClientCreateUpdateSerializer."""

    def test_validate_company_name_required(self):
        """Test that company name is required."""
        data = {
            'industry': 'technology',
            'contact_email': 'test@example.com'
        }
        serializer = ClientCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'company_name' in serializer.errors

    def test_validate_company_name_unique(self):
        """Test that company name must be unique."""
        Client.objects.create(
            company_name="Existing Corp",
            contact_email="existing@corp.com"
        )

        data = {
            'company_name': 'Existing Corp',
            'industry': 'technology',
            'contact_email': 'new@corp.com'
        }
        serializer = ClientCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'company_name' in serializer.errors

    def test_validate_contract_dates(self):
        """Test that contract end date must be after start date."""
        data = {
            'company_name': 'Test Corp',
            'industry': 'technology',
            'contact_email': 'test@corp.com',
            'contract_start_date': '2025-12-31',
            'contract_end_date': '2025-01-01'
        }
        serializer = ClientCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'contract_end_date' in serializer.errors

    def test_create_client_valid_data(self):
        """Test creating a client with valid data."""
        data = {
            'company_name': 'New Corp',
            'industry': 'technology',
            'contact_email': 'contact@newcorp.com',
            'azure_subscription_ids': [
                '12345678-1234-1234-1234-123456789012'
            ]
        }
        serializer = ClientCreateUpdateSerializer(data=data)
        assert serializer.is_valid()
        client = serializer.save()
        assert client.company_name == 'New Corp'
        assert len(client.azure_subscription_ids) == 1


@pytest.mark.django_db
class TestClientContactSerializer:
    """Tests for ClientContactSerializer."""

    def test_validate_email_unique_per_client(self):
        """Test that email must be unique per client."""
        client = Client.objects.create(
            company_name="Test Corp",
            contact_email="contact@testcorp.com"
        )

        # Create first contact
        ClientContact.objects.create(
            client=client,
            name="John Doe",
            email="john@testcorp.com",
            role="primary"
        )

        # Try to create second contact with same email
        data = {
            'client': client.id,
            'name': 'Jane Doe',
            'email': 'john@testcorp.com',
            'role': 'technical'
        }
        serializer = ClientContactSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_create_contact_valid_data(self):
        """Test creating a contact with valid data."""
        client = Client.objects.create(
            company_name="Test Corp",
            contact_email="contact@testcorp.com"
        )

        data = {
            'client': client.id,
            'name': 'John Doe',
            'email': 'john@testcorp.com',
            'phone': '+1234567890',
            'role': 'primary',
            'title': 'CTO',
            'is_primary': True
        }
        serializer = ClientContactSerializer(data=data)
        assert serializer.is_valid()
        contact = serializer.save()
        assert contact.name == 'John Doe'
        assert contact.is_primary is True
