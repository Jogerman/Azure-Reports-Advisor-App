"""
Client models for managing customer information and Azure subscriptions.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Client(models.Model):
    """
    Client represents a customer/organization that uses Azure Advisor reports.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]

    INDUSTRY_CHOICES = [
        ('technology', 'Technology'),
        ('healthcare', 'Healthcare'),
        ('finance', 'Finance'),
        ('education', 'Education'),
        ('manufacturing', 'Manufacturing'),
        ('retail', 'Retail'),
        ('government', 'Government'),
        ('consulting', 'Consulting'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=255, help_text="Client company name")
    industry = models.CharField(
        max_length=50,
        choices=INDUSTRY_CHOICES,
        default='other',
        help_text="Client industry sector"
    )
    contact_email = models.EmailField(help_text="Primary contact email")
    contact_phone = models.CharField(max_length=20, blank=True, help_text="Primary contact phone")
    contact_person = models.CharField(max_length=255, blank=True, help_text="Primary contact person name")

    # Azure subscription management
    azure_subscription_ids = models.JSONField(
        default=list,
        blank=True,
        help_text="List of Azure subscription IDs"
    )

    # Client status and metadata
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Client account status"
    )
    notes = models.TextField(blank=True, help_text="Internal notes about the client")

    # Billing and contract information
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    billing_contact = models.EmailField(blank=True, help_text="Billing contact email")

    # Relationship management
    account_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_clients',
        help_text="Assigned account manager"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_clients'
    )

    class Meta:
        db_table = 'clients'
        ordering = ['company_name']
        indexes = [
            models.Index(fields=['company_name']),
            models.Index(fields=['status']),
            models.Index(fields=['industry']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.company_name} ({self.get_status_display()})"

    @property
    def subscription_count(self):
        """Return the number of Azure subscriptions for this client."""
        return len(self.azure_subscription_ids) if self.azure_subscription_ids else 0

    @property
    def total_reports(self):
        """Return the total number of reports generated for this client."""
        return self.reports.count()

    @property
    def latest_report_date(self):
        """Return the date of the most recent report."""
        latest_report = self.reports.order_by('-created_at').first()
        return latest_report.created_at if latest_report else None

    def add_subscription(self, subscription_id):
        """Add an Azure subscription ID to the client."""
        if not self.azure_subscription_ids:
            self.azure_subscription_ids = []

        if subscription_id not in self.azure_subscription_ids:
            self.azure_subscription_ids.append(subscription_id)
            self.save()

    def remove_subscription(self, subscription_id):
        """Remove an Azure subscription ID from the client."""
        if self.azure_subscription_ids and subscription_id in self.azure_subscription_ids:
            self.azure_subscription_ids.remove(subscription_id)
            self.save()


class ClientContact(models.Model):
    """
    Additional contact persons for a client.
    """
    ROLE_CHOICES = [
        ('primary', 'Primary Contact'),
        ('technical', 'Technical Contact'),
        ('billing', 'Billing Contact'),
        ('executive', 'Executive Contact'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='other')
    title = models.CharField(max_length=100, blank=True, help_text="Job title")
    is_primary = models.BooleanField(default=False, help_text="Is this the primary contact?")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_contacts'
        unique_together = ['client', 'email']

    def __str__(self):
        return f"{self.name} ({self.client.company_name})"

    def save(self, *args, **kwargs):
        # Ensure only one primary contact per client
        if self.is_primary:
            ClientContact.objects.filter(client=self.client, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class ClientNote(models.Model):
    """
    Notes and comments about clients for tracking interactions and history.
    """
    NOTE_TYPES = [
        ('meeting', 'Meeting'),
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('issue', 'Issue'),
        ('opportunity', 'Opportunity'),
        ('general', 'General'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='client_notes')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default='general')
    subject = models.CharField(max_length=255, help_text="Brief subject line")
    content = models.TextField(help_text="Detailed note content")

    # Optional reference to a specific report
    related_report = models.ForeignKey(
        'reports.Report',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Related report (if applicable)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_notes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_note_type_display()}: {self.subject} ({self.client.company_name})"