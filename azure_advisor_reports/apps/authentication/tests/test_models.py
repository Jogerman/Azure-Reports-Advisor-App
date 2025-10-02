"""
Test cases for authentication models
Tests User and UserSession models
"""

import pytest
import uuid
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta

from apps.authentication.models import User, UserSession

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test suite for User model"""

    def test_user_creation(self):
        """Test creating a user with all required fields"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )

        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.is_active is True
        assert user.check_password("testpass123")

    def test_user_creation_with_azure_id(self):
        """Test creating a user with Azure AD integration"""
        azure_id = str(uuid.uuid4())
        tenant_id = str(uuid.uuid4())

        user = User.objects.create_user(
            username="azureuser",
            email="azure@example.com",
            password="testpass123",
            azure_object_id=azure_id,
            tenant_id=tenant_id
        )

        assert user.azure_object_id == azure_id
        assert user.tenant_id == tenant_id

    def test_user_with_role(self):
        """Test user creation with specific role"""
        user = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="testpass123",
            role="manager"
        )

        assert user.role == "manager"
        assert user.get_role_display() == "Manager"

    def test_user_default_role(self):
        """Test that default role is 'analyst'"""
        user = User.objects.create_user(
            username="defaultuser",
            email="default@example.com",
            password="testpass123"
        )

        assert user.role == "analyst"

    def test_user_full_name_property(self):
        """Test full_name property"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe"
        )

        assert user.full_name == "John Doe"

    def test_user_full_name_with_empty_names(self):
        """Test full_name property with empty first or last name"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        assert user.full_name == ""

    def test_user_string_representation(self):
        """Test __str__ method"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe"
        )

        assert str(user) == "John Doe (test@example.com)"

    def test_user_timestamps(self):
        """Test that created_at and updated_at are set correctly"""
        before_creation = timezone.now()

        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        after_creation = timezone.now()

        assert before_creation <= user.created_at <= after_creation
        assert before_creation <= user.updated_at <= after_creation

    def test_user_update_timestamp(self):
        """Test that updated_at changes when user is updated"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        original_updated_at = user.updated_at

        # Wait a moment and update
        import time
        time.sleep(0.1)

        user.first_name = "Updated"
        user.save()

        assert user.updated_at > original_updated_at

    def test_unique_email(self):
        """Test that email must be unique"""
        User.objects.create_user(
            username="user1",
            email="unique@example.com",
            password="testpass123"
        )

        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username="user2",
                email="unique@example.com",
                password="testpass123"
            )

    def test_unique_username(self):
        """Test that username must be unique"""
        User.objects.create_user(
            username="uniqueuser",
            email="user1@example.com",
            password="testpass123"
        )

        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username="uniqueuser",
                email="user2@example.com",
                password="testpass123"
            )

    def test_unique_azure_object_id(self):
        """Test that azure_object_id must be unique"""
        azure_id = str(uuid.uuid4())

        User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123",
            azure_object_id=azure_id
        )

        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username="user2",
                email="user2@example.com",
                password="testpass123",
                azure_object_id=azure_id
            )

    def test_user_profile_fields(self):
        """Test user profile fields"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            job_title="Software Engineer",
            department="Engineering",
            phone_number="+1234567890"
        )

        assert user.job_title == "Software Engineer"
        assert user.department == "Engineering"
        assert user.phone_number == "+1234567890"

    def test_user_last_login_ip(self):
        """Test last_login_ip field"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            last_login_ip="192.168.1.1"
        )

        assert user.last_login_ip == "192.168.1.1"

    def test_user_role_choices(self):
        """Test all valid role choices"""
        valid_roles = ["admin", "manager", "analyst", "viewer"]

        for role in valid_roles:
            user = User.objects.create_user(
                username=f"user_{role}",
                email=f"{role}@example.com",
                password="testpass123",
                role=role
            )
            assert user.role == role

    def test_admin_user_creation(self):
        """Test creating an admin user"""
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            role="admin"
        )

        assert admin.is_superuser is True
        assert admin.is_staff is True
        assert admin.role == "admin"


@pytest.mark.django_db
class TestUserSessionModel:
    """Test suite for UserSession model"""

    def test_session_creation(self):
        """Test creating a user session"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        session = UserSession.objects.create(
            user=user,
            session_key="test_session_key",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 Test Browser"
        )

        assert session.id is not None
        assert isinstance(session.id, uuid.UUID)
        assert session.user == user
        assert session.session_key == "test_session_key"
        assert session.ip_address == "192.168.1.1"
        assert session.user_agent == "Mozilla/5.0 Test Browser"
        assert session.is_active is True

    def test_session_string_representation(self):
        """Test __str__ method"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        session = UserSession.objects.create(
            user=user,
            session_key="test_session_key",
            ip_address="192.168.1.1",
            user_agent="Test Browser"
        )

        assert str(session) == "Session for test@example.com from 192.168.1.1"

    def test_session_timestamps(self):
        """Test that created_at and last_activity are set correctly"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        before_creation = timezone.now()

        session = UserSession.objects.create(
            user=user,
            session_key="test_session_key",
            ip_address="192.168.1.1",
            user_agent="Test Browser"
        )

        after_creation = timezone.now()

        assert before_creation <= session.created_at <= after_creation
        assert before_creation <= session.last_activity <= after_creation

    def test_session_last_activity_update(self):
        """Test that last_activity updates when session is modified"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        session = UserSession.objects.create(
            user=user,
            session_key="test_session_key",
            ip_address="192.168.1.1",
            user_agent="Test Browser"
        )

        original_last_activity = session.last_activity

        import time
        time.sleep(0.1)

        session.is_active = False
        session.save()

        assert session.last_activity > original_last_activity

    def test_multiple_sessions_per_user(self):
        """Test that a user can have multiple sessions"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        session1 = UserSession.objects.create(
            user=user,
            session_key="session_key_1",
            ip_address="192.168.1.1",
            user_agent="Browser 1"
        )

        session2 = UserSession.objects.create(
            user=user,
            session_key="session_key_2",
            ip_address="192.168.1.2",
            user_agent="Browser 2"
        )

        assert user.sessions.count() == 2
        assert session1 in user.sessions.all()
        assert session2 in user.sessions.all()

    def test_session_cascade_deletion(self):
        """Test that sessions are deleted when user is deleted"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        UserSession.objects.create(
            user=user,
            session_key="session_key_1",
            ip_address="192.168.1.1",
            user_agent="Browser 1"
        )

        UserSession.objects.create(
            user=user,
            session_key="session_key_2",
            ip_address="192.168.1.2",
            user_agent="Browser 2"
        )

        user_id = user.id
        user.delete()

        assert UserSession.objects.filter(user_id=user_id).count() == 0

    def test_session_deactivation(self):
        """Test deactivating a session"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        session = UserSession.objects.create(
            user=user,
            session_key="test_session_key",
            ip_address="192.168.1.1",
            user_agent="Test Browser"
        )

        session.is_active = False
        session.save()

        assert session.is_active is False

    def test_ipv6_address(self):
        """Test session with IPv6 address"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        session = UserSession.objects.create(
            user=user,
            session_key="test_session_key",
            ip_address="2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            user_agent="Test Browser"
        )

        assert session.ip_address == "2001:0db8:85a3:0000:0000:8a2e:0370:7334"