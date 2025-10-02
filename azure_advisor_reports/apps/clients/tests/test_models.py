"""
Test cases for clients app models
Tests Client, ClientContact, and ClientNote models
"""

import pytest
import uuid
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone
from datetime import date, timedelta

from apps.clients.models import Client, ClientContact, ClientNote

User = get_user_model()


@pytest.mark.django_db
class TestClientModel:
    """Test suite for Client model"""

    def test_client_creation(self):
        """Test creating a client with required fields"""
        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@testcompany.com"
        )

        assert client.id is not None
        assert isinstance(client.id, uuid.UUID)
        assert client.company_name == "Test Company"
        assert client.contact_email == "contact@testcompany.com"
        assert client.status == "active"  # Default status
        assert client.industry == "other"  # Default industry

    def test_client_with_all_fields(self):
        """Test creating a client with all fields"""
        user = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Acme Corporation",
            industry="technology",
            contact_email="contact@acme.com",
            contact_phone="+1-555-0123",
            contact_person="John Doe",
            status="active",
            notes="Important client",
            contract_start_date=date.today(),
            contract_end_date=date.today() + timedelta(days=365),
            billing_contact="billing@acme.com",
            account_manager=user,
            created_by=user
        )

        assert client.company_name == "Acme Corporation"
        assert client.industry == "technology"
        assert client.contact_phone == "+1-555-0123"
        assert client.contact_person == "John Doe"
        assert client.notes == "Important client"
        assert client.account_manager == user
        assert client.created_by == user

    def test_client_string_representation(self):
        """Test __str__ method"""
        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com",
            status="active"
        )

        assert str(client) == "Test Company (Active)"

    def test_client_default_status(self):
        """Test that default status is 'active'"""
        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com"
        )

        assert client.status == "active"

    def test_client_status_choices(self):
        """Test all valid status choices"""
        statuses = ["active", "inactive", "suspended"]

        for status in statuses:
            client = Client.objects.create(
                company_name=f"Company {status}",
                contact_email=f"{status}@test.com",
                status=status
            )
            assert client.status == status

    def test_client_industry_choices(self):
        """Test valid industry choices"""
        industries = ["technology", "healthcare", "finance", "education",
                     "manufacturing", "retail", "government", "consulting", "other"]

        for industry in industries:
            client = Client.objects.create(
                company_name=f"Company {industry}",
                contact_email=f"{industry}@test.com",
                industry=industry
            )
            assert client.industry == industry

    def test_client_azure_subscription_ids(self):
        """Test azure_subscription_ids JSONField"""
        subscription_ids = [str(uuid.uuid4()), str(uuid.uuid4())]

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com",
            azure_subscription_ids=subscription_ids
        )

        assert client.azure_subscription_ids == subscription_ids
        assert len(client.azure_subscription_ids) == 2

    def test_client_azure_subscription_ids_default(self):
        """Test azure_subscription_ids defaults to empty list"""
        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com"
        )

        assert client.azure_subscription_ids == []

    def test_client_add_subscription(self):
        """Test add_subscription method"""
        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com"
        )

        sub_id = str(uuid.uuid4())
        client.add_subscription(sub_id)

        assert sub_id in client.azure_subscription_ids
        assert len(client.azure_subscription_ids) == 1

    def test_client_add_duplicate_subscription(self):
        """Test that duplicate subscription IDs are not added"""
        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com"
        )

        sub_id = str(uuid.uuid4())
        client.add_subscription(sub_id)
        client.add_subscription(sub_id)  # Try to add again

        assert client.azure_subscription_ids.count(sub_id) == 1

    def test_client_remove_subscription(self):
        """Test remove_subscription method"""
        sub_id = str(uuid.uuid4())
        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com",
            azure_subscription_ids=[sub_id]
        )

        client.remove_subscription(sub_id)

        assert sub_id not in client.azure_subscription_ids

    def test_client_subscription_count_property(self):
        """Test subscription_count property"""
        subscription_ids = [str(uuid.uuid4()) for _ in range(3)]

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com",
            azure_subscription_ids=subscription_ids
        )

        assert client.subscription_count == 3

    def test_client_timestamps(self):
        """Test that created_at and updated_at are set correctly"""
        before_creation = timezone.now()

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com"
        )

        after_creation = timezone.now()

        assert before_creation <= client.created_at <= after_creation
        assert before_creation <= client.updated_at <= after_creation

    def test_client_update_timestamp(self):
        """Test that updated_at changes when client is updated"""
        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com"
        )

        original_updated_at = client.updated_at

        import time
        time.sleep(0.1)

        client.company_name = "Updated Company"
        client.save()

        assert client.updated_at > original_updated_at

    def test_client_ordering(self):
        """Test that clients are ordered by company_name"""
        Client.objects.create(company_name="Zebra", contact_email="z@test.com")
        Client.objects.create(company_name="Alpha", contact_email="a@test.com")
        Client.objects.create(company_name="Beta", contact_email="b@test.com")

        clients = list(Client.objects.all())
        assert clients[0].company_name == "Alpha"
        assert clients[1].company_name == "Beta"
        assert clients[2].company_name == "Zebra"

    def test_client_account_manager_relationship(self):
        """Test account_manager foreign key relationship"""
        manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com",
            account_manager=manager
        )

        assert client.account_manager == manager
        assert client in manager.managed_clients.all()

    def test_client_created_by_relationship(self):
        """Test created_by foreign key relationship"""
        user = User.objects.create_user(
            username="creator",
            email="creator@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com",
            created_by=user
        )

        assert client.created_by == user
        assert client in user.created_clients.all()


@pytest.mark.django_db
class TestClientContactModel:
    """Test suite for ClientContact model"""

    def test_contact_creation(self):
        """Test creating a client contact"""
        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com"
        )

        contact = ClientContact.objects.create(
            client=client,
            name="John Doe",
            email="john@test.com",
            phone="+1-555-0123",
            role="primary",
            title="CEO"
        )

        assert contact.id is not None
        assert isinstance(contact.id, uuid.UUID)
        assert contact.client == client
        assert contact.name == "John Doe"
        assert contact.email == "john@test.com"
        assert contact.phone == "+1-555-0123"
        assert contact.role == "primary"
        assert contact.title == "CEO"

    def test_contact_string_representation(self):
        """Test __str__ method"""
        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com"
        )

        contact = ClientContact.objects.create(
            client=client,
            name="John Doe",
            email="john@test.com"
        )

        assert str(contact) == "John Doe (Test Company)"

    def test_contact_role_choices(self):
        """Test all valid role choices"""
        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com"
        )

        roles = ["primary", "technical", "billing", "executive", "other"]

        for role in roles:
            contact = ClientContact.objects.create(
                client=client,
                name=f"Contact {role}",
                email=f"{role}@test.com",
                role=role
            )
            assert contact.role == role

    def test_contact_unique_email_per_client(self):
        """Test that email must be unique per client"""
        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com"
        )

        ClientContact.objects.create(
            client=client,
            name="Contact 1",
            email="duplicate@test.com"
        )

        with pytest.raises(IntegrityError):
            ClientContact.objects.create(
                client=client,
                name="Contact 2",
                email="duplicate@test.com"
            )

    def test_contact_same_email_different_clients(self):
        """Test that same email can be used for different clients"""
        client1 = Client.objects.create(
            company_name="Company 1",
            contact_email="contact1@test.com"
        )

        client2 = Client.objects.create(
            company_name="Company 2",
            contact_email="contact2@test.com"
        )

        contact1 = ClientContact.objects.create(
            client=client1,
            name="Contact 1",
            email="same@test.com"
        )

        contact2 = ClientContact.objects.create(
            client=client2,
            name="Contact 2",
            email="same@test.com"
        )

        assert contact1.email == contact2.email
        assert contact1.client != contact2.client

    def test_contact_primary_flag(self):
        """Test is_primary flag"""
        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com"
        )

        contact = ClientContact.objects.create(
            client=client,
            name="Primary Contact",
            email="primary@test.com",
            is_primary=True
        )

        assert contact.is_primary is True

    def test_contact_only_one_primary_per_client(self):
        """Test that only one contact can be primary per client"""
        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com"
        )

        contact1 = ClientContact.objects.create(
            client=client,
            name="Contact 1",
            email="contact1@test.com",
            is_primary=True
        )

        assert contact1.is_primary is True

        # Create second primary contact - should unset first one
        contact2 = ClientContact.objects.create(
            client=client,
            name="Contact 2",
            email="contact2@test.com",
            is_primary=True
        )

        # Refresh contact1 from database
        contact1.refresh_from_db()

        assert contact2.is_primary is True
        assert contact1.is_primary is False

    def test_contact_cascade_deletion(self):
        """Test that contacts are deleted when client is deleted"""
        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com"
        )

        ClientContact.objects.create(
            client=client,
            name="Contact 1",
            email="contact1@test.com"
        )

        ClientContact.objects.create(
            client=client,
            name="Contact 2",
            email="contact2@test.com"
        )

        client_id = client.id
        client.delete()

        assert ClientContact.objects.filter(client_id=client_id).count() == 0


@pytest.mark.django_db
class TestClientNoteModel:
    """Test suite for ClientNote model"""

    def test_note_creation(self):
        """Test creating a client note"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com"
        )

        note = ClientNote.objects.create(
            client=client,
            author=user,
            note_type="meeting",
            subject="Initial Meeting",
            content="Discussed project requirements and timeline."
        )

        assert note.id is not None
        assert isinstance(note.id, uuid.UUID)
        assert note.client == client
        assert note.author == user
        assert note.note_type == "meeting"
        assert note.subject == "Initial Meeting"
        assert note.content == "Discussed project requirements and timeline."

    def test_note_string_representation(self):
        """Test __str__ method"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com"
        )

        note = ClientNote.objects.create(
            client=client,
            author=user,
            note_type="meeting",
            subject="Test Subject",
            content="Test content"
        )

        assert str(note) == "Meeting: Test Subject (Test Company)"

    def test_note_type_choices(self):
        """Test all valid note_type choices"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com"
        )

        note_types = ["meeting", "call", "email", "issue", "opportunity", "general"]

        for note_type in note_types:
            note = ClientNote.objects.create(
                client=client,
                author=user,
                note_type=note_type,
                subject=f"Subject {note_type}",
                content="Test content"
            )
            assert note.note_type == note_type

    def test_note_ordering(self):
        """Test that notes are ordered by created_at descending"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com"
        )

        import time

        note1 = ClientNote.objects.create(
            client=client,
            author=user,
            subject="First Note",
            content="Content 1"
        )

        time.sleep(0.1)

        note2 = ClientNote.objects.create(
            client=client,
            author=user,
            subject="Second Note",
            content="Content 2"
        )

        time.sleep(0.1)

        note3 = ClientNote.objects.create(
            client=client,
            author=user,
            subject="Third Note",
            content="Content 3"
        )

        notes = list(ClientNote.objects.all())
        assert notes[0] == note3  # Most recent first
        assert notes[1] == note2
        assert notes[2] == note1

    def test_note_cascade_deletion_client(self):
        """Test that notes are deleted when client is deleted"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com"
        )

        ClientNote.objects.create(
            client=client,
            author=user,
            subject="Note 1",
            content="Content 1"
        )

        ClientNote.objects.create(
            client=client,
            author=user,
            subject="Note 2",
            content="Content 2"
        )

        client_id = client.id
        client.delete()

        assert ClientNote.objects.filter(client_id=client_id).count() == 0

    def test_note_timestamps(self):
        """Test that created_at and updated_at are set correctly"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="contact@test.com"
        )

        before_creation = timezone.now()

        note = ClientNote.objects.create(
            client=client,
            author=user,
            subject="Test Note",
            content="Test content"
        )

        after_creation = timezone.now()

        assert before_creation <= note.created_at <= after_creation
        assert before_creation <= note.updated_at <= after_creation