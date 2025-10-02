"""
Factory classes for generating test data
Uses factory_boy for creating realistic test objects
"""

import uuid
from decimal import Decimal
from datetime import datetime, timedelta

import factory
from factory import fuzzy
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils import timezone

# Import models
from apps.clients.models import Client, ClientContact, ClientNote
from apps.reports.models import Report, Recommendation, ReportTemplate, ReportShare

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating test users."""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    is_superuser = False

    # Custom fields from User model
    azure_object_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    tenant_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    role = fuzzy.FuzzyChoice(["admin", "manager", "analyst", "viewer"])
    job_title = factory.Faker("job")
    department = factory.Faker("word")
    phone_number = factory.Faker("phone_number")

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """Set password for the user."""
        if not create:
            return

        password = extracted or "testpass123"
        obj.set_password(password)
        obj.save()


class AdminUserFactory(UserFactory):
    """Factory for creating admin users."""

    is_staff = True
    is_superuser = True
    role = "admin"


class ClientFactory(DjangoModelFactory):
    """Factory for creating test clients."""

    class Meta:
        model = Client

    id = factory.LazyFunction(uuid.uuid4)
    company_name = factory.Faker("company")
    industry = fuzzy.FuzzyChoice(["technology", "healthcare", "finance", "manufacturing", "retail", "education", "government", "consulting", "other"])
    contact_email = factory.Faker("company_email")
    contact_phone = factory.Faker("phone_number")
    contact_person = factory.Faker("name")
    status = fuzzy.FuzzyChoice(["active", "inactive", "suspended"])
    notes = factory.Faker("text", max_nb_chars=500)
    billing_contact = factory.Faker("email")
    account_manager = factory.SubFactory(UserFactory)

    # Azure subscription IDs (JSON field)
    azure_subscription_ids = factory.LazyFunction(
        lambda: [str(uuid.uuid4()) for _ in range(factory.random.randint(1, 5))]
    )

    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)


class ReportFactory(DjangoModelFactory):
    """Factory for creating test reports."""

    class Meta:
        model = Report

    id = factory.LazyFunction(uuid.uuid4)
    client = factory.SubFactory(ClientFactory)
    created_by = factory.SubFactory(UserFactory)

    report_type = fuzzy.FuzzyChoice([
        "detailed", "executive", "cost", "security", "operations"
    ])

    status = fuzzy.FuzzyChoice([
        "pending", "processing", "completed", "failed"
    ])

    # File fields (will be populated with dummy files)
    csv_file = factory.LazyAttribute(
        lambda obj: ContentFile(
            "Category,Business Impact,Recommendation\nCost,High,Test recommendation",
            name=f"test_upload_{obj.id}.csv"
        )
    )

    html_file = factory.Maybe(
        "status",
        yes_declaration=factory.LazyAttribute(
            lambda obj: ContentFile(
                "<html><body><h1>Test Report</h1></body></html>",
                name=f"report_{obj.id}.html"
            )
        ),
        no_declaration=None,
        condition="completed"
    )

    pdf_file = factory.Maybe(
        "status",
        yes_declaration=factory.LazyAttribute(
            lambda obj: ContentFile(
                b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF",
                name=f"report_{obj.id}.pdf"
            )
        ),
        no_declaration=None,
        condition="completed"
    )

    # Analysis data (JSON field)
    analysis_data = factory.LazyFunction(
        lambda: {
            "total_recommendations": factory.random.randint(5, 100),
            "category_distribution": {
                "Cost": factory.random.randint(1, 30),
                "Security": factory.random.randint(1, 30),
                "Reliability": factory.random.randint(1, 30),
                "OperationalExcellence": factory.random.randint(1, 30),
            },
            "business_impact_distribution": {
                "High": factory.random.randint(1, 20),
                "Medium": factory.random.randint(1, 30),
                "Low": factory.random.randint(1, 50),
            },
            "estimated_monthly_savings": str(factory.random.uniform(500, 10000)),
            "estimated_working_hours": factory.random.randint(10, 200),
            "advisor_score": factory.random.randint(60, 100),
            "top_recommendations": [
                {
                    "category": "Cost",
                    "recommendation": f"Top recommendation {i}",
                    "potential_savings": str(factory.random.uniform(100, 2000)),
                }
                for i in range(5)
            ]
        }
    )

    error_message = factory.Maybe(
        "status",
        yes_declaration=factory.Faker("text", max_nb_chars=200),
        no_declaration=None,
        condition="failed"
    )

    processing_started_at = factory.Maybe(
        "status",
        yes_declaration=factory.LazyFunction(
            lambda: timezone.now() - timedelta(minutes=factory.random.randint(1, 60))
        ),
        no_declaration=None,
        condition__in=["processing", "completed", "failed"]
    )

    processing_completed_at = factory.Maybe(
        "status",
        yes_declaration=factory.LazyFunction(
            lambda: timezone.now() - timedelta(minutes=factory.random.randint(1, 30))
        ),
        no_declaration=None,
        condition__in=["completed", "failed"]
    )

    created_at = factory.LazyFunction(
        lambda: timezone.now() - timedelta(days=factory.random.randint(0, 30))
    )
    updated_at = factory.LazyFunction(timezone.now)


class RecommendationFactory(DjangoModelFactory):
    """Factory for creating test recommendations."""

    class Meta:
        model = Recommendation

    id = factory.LazyFunction(uuid.uuid4)
    report = factory.SubFactory(ReportFactory)

    category = fuzzy.FuzzyChoice([
        "cost", "security", "reliability", "operational_excellence", "performance"
    ])

    business_impact = fuzzy.FuzzyChoice(["high", "medium", "low"])

    recommendation = factory.Faker("text", max_nb_chars=1000)

    subscription_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    subscription_name = factory.Faker("text", max_nb_chars=100)

    resource_group = factory.LazyAttribute(
        lambda obj: f"rg-{factory.faker.Faker().word()}-{factory.random.randint(1, 999)}"
    )

    resource_name = factory.LazyAttribute(
        lambda obj: f"{factory.faker.Faker().word()}-{factory.random.randint(1, 999)}"
    )

    resource_type = fuzzy.FuzzyChoice([
        "Microsoft.Compute/virtualMachines",
        "Microsoft.Storage/storageAccounts",
        "Microsoft.Sql/servers/databases",
        "Microsoft.Web/sites",
        "Microsoft.Network/loadBalancers",
        "Microsoft.KeyVault/vaults",
        "Microsoft.ContainerService/managedClusters"
    ])

    potential_savings = fuzzy.FuzzyDecimal(10.0, 5000.0, 2)
    currency = "USD"

    potential_benefits = factory.Faker("text", max_nb_chars=500)

    retirement_date = None
    retiring_feature = None
    advisor_score_impact = fuzzy.FuzzyDecimal(0.0, 10.0, 2)
    csv_row_number = factory.Sequence(lambda n: n + 1)

    created_at = factory.LazyFunction(
        lambda: timezone.now() - timedelta(days=factory.random.randint(0, 30))
    )


# Specialized factories for specific test scenarios

class PendingReportFactory(ReportFactory):
    """Factory for creating pending reports."""
    status = "pending"
    html_file = None
    pdf_file = None
    processing_started_at = None
    processing_completed_at = None
    error_message = None


class ProcessingReportFactory(ReportFactory):
    """Factory for creating processing reports."""
    status = "processing"
    html_file = None
    pdf_file = None
    processing_started_at = factory.LazyFunction(
        lambda: timezone.now() - timedelta(minutes=factory.random.randint(1, 30))
    )
    processing_completed_at = None
    error_message = None


class CompletedReportFactory(ReportFactory):
    """Factory for creating completed reports."""
    status = "completed"
    processing_started_at = factory.LazyFunction(
        lambda: timezone.now() - timedelta(minutes=factory.random.randint(5, 60))
    )
    processing_completed_at = factory.LazyFunction(
        lambda: timezone.now() - timedelta(minutes=factory.random.randint(1, 30))
    )
    error_message = None


class FailedReportFactory(ReportFactory):
    """Factory for creating failed reports."""
    status = "failed"
    html_file = None
    pdf_file = None
    processing_started_at = factory.LazyFunction(
        lambda: timezone.now() - timedelta(minutes=factory.random.randint(5, 60))
    )
    processing_completed_at = factory.LazyFunction(
        lambda: timezone.now() - timedelta(minutes=factory.random.randint(1, 30))
    )
    error_message = factory.Faker("text", max_nb_chars=200)


class CostRecommendationFactory(RecommendationFactory):
    """Factory for creating cost-related recommendations."""
    category = "cost"
    potential_savings = fuzzy.FuzzyDecimal(100.0, 10000.0, 2)


class SecurityRecommendationFactory(RecommendationFactory):
    """Factory for creating security-related recommendations."""
    category = "security"
    business_impact = fuzzy.FuzzyChoice(["high", "medium"])  # Security is typically High/Medium
    potential_savings = fuzzy.FuzzyDecimal(0.0, 1000.0, 2)  # Lower direct cost savings


class HighImpactRecommendationFactory(RecommendationFactory):
    """Factory for creating high-impact recommendations."""
    business_impact = "high"
    potential_savings = fuzzy.FuzzyDecimal(1000.0, 10000.0, 2)


class LowImpactRecommendationFactory(RecommendationFactory):
    """Factory for creating low-impact recommendations."""
    business_impact = "low"
    potential_savings = fuzzy.FuzzyDecimal(10.0, 500.0, 2)


# Batch factories for creating multiple related objects

def create_client_with_reports(num_reports=3, **kwargs):
    """Create a client with multiple reports."""
    client = ClientFactory(**kwargs)
    reports = []
    for _ in range(num_reports):
        report = ReportFactory(client=client)
        # Add some recommendations to each report
        RecommendationFactory.create_batch(
            factory.random.randint(5, 25),
            report=report
        )
        reports.append(report)
    return client, reports


def create_user_with_reports(user_role="analyst", num_reports=5, **kwargs):
    """Create a user with multiple reports."""
    user = UserFactory(role=user_role, **kwargs)
    clients = ClientFactory.create_batch(3)
    reports = []
    for _ in range(num_reports):
        client = factory.random.choice(clients)
        report = ReportFactory(client=client, created_by=user)
        RecommendationFactory.create_batch(
            factory.random.randint(5, 20),
            report=report
        )
        reports.append(report)
    return user, reports


def create_comprehensive_test_data():
    """Create a comprehensive set of test data for integration tests."""
    # Create users with different roles
    admin = AdminUserFactory()
    manager = UserFactory(role="manager")
    analyst1 = UserFactory(role="analyst")
    analyst2 = UserFactory(role="analyst")
    viewer = UserFactory(role="viewer")

    # Create clients
    clients = ClientFactory.create_batch(5)

    # Create reports with different statuses
    reports = []

    # Pending reports
    for client in clients[:2]:
        reports.extend(PendingReportFactory.create_batch(
            2, client=client, created_by=analyst1
        ))

    # Processing reports
    for client in clients[1:3]:
        reports.extend(ProcessingReportFactory.create_batch(
            2, client=client, created_by=analyst2
        ))

    # Completed reports with recommendations
    for client in clients[2:]:
        for _ in range(3):
            report = CompletedReportFactory(client=client, created_by=analyst1)
            RecommendationFactory.create_batch(
                factory.random.randint(10, 50),
                report=report
            )
            reports.append(report)

    # Failed reports
    failed_reports = FailedReportFactory.create_batch(
        2, client=clients[0], created_by=analyst2
    )
    reports.extend(failed_reports)

    return {
        "users": {
            "admin": admin,
            "manager": manager,
            "analyst1": analyst1,
            "analyst2": analyst2,
            "viewer": viewer,
        },
        "clients": clients,
        "reports": reports,
    }