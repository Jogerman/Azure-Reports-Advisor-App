"""
Report models for Azure Advisor report generation and management.
"""

import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from apps.clients.models import Client


class Report(models.Model):
    """
    Report represents an Azure Advisor report generated for a client.
    """
    REPORT_TYPES = [
        ('detailed', 'Detailed Report'),
        ('executive', 'Executive Summary'),
        ('cost', 'Cost Optimization'),
        ('security', 'Security Assessment'),
        ('operations', 'Operational Excellence'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Upload'),
        ('uploaded', 'CSV Uploaded'),
        ('processing', 'Processing CSV'),
        ('generating', 'Generating Report'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='reports')
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_reports'
    )

    # Report configuration
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES,
        help_text="Type of report to generate"
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Custom report title (optional)"
    )

    # File management
    csv_file = models.FileField(
        upload_to='csv_uploads/%Y/%m/',
        null=True,
        blank=True,
        help_text="Uploaded Azure Advisor CSV file"
    )
    html_file = models.FileField(
        upload_to='reports/html/%Y/%m/',
        null=True,
        blank=True,
        help_text="Generated HTML report file"
    )
    pdf_file = models.FileField(
        upload_to='reports/pdf/%Y/%m/',
        null=True,
        blank=True,
        help_text="Generated PDF report file"
    )

    # Processing status and metadata
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current processing status"
    )

    # Analysis data stored as JSON
    analysis_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Processed analytics and metrics from CSV"
    )

    # Error handling
    error_message = models.TextField(
        blank=True,
        help_text="Error details if processing failed"
    )
    retry_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="Number of processing retry attempts"
    )

    # Processing timestamps
    csv_uploaded_at = models.DateTimeField(null=True, blank=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)

    # General timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['report_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        title = self.title or f"{self.get_report_type_display()} Report"
        return f"{title} - {self.client.company_name} ({self.get_status_display()})"

    @property
    def processing_duration(self):
        """Calculate total processing time if completed."""
        if self.processing_started_at and self.processing_completed_at:
            return self.processing_completed_at - self.processing_started_at
        return None

    @property
    def recommendation_count(self):
        """Get total number of recommendations for this report."""
        return self.recommendations.count()

    @property
    def total_potential_savings(self):
        """Calculate total potential savings from all recommendations."""
        return self.recommendations.aggregate(
            total=models.Sum('potential_savings')
        )['total'] or 0

    def start_processing(self):
        """Mark report as started processing."""
        self.status = 'processing'
        self.processing_started_at = timezone.now()
        self.save(update_fields=['status', 'processing_started_at'])

    def complete_processing(self):
        """Mark report as completed."""
        self.status = 'completed'
        self.processing_completed_at = timezone.now()
        self.save(update_fields=['status', 'processing_completed_at'])

    def fail_processing(self, error_message):
        """Mark report as failed with error message."""
        self.status = 'failed'
        self.error_message = error_message
        self.processing_completed_at = timezone.now()
        self.retry_count += 1
        self.save(update_fields=['status', 'error_message', 'processing_completed_at', 'retry_count'])

    def can_retry(self):
        """Check if report can be retried (max 5 attempts)."""
        return self.status == 'failed' and self.retry_count < 5


class Recommendation(models.Model):
    """
    Individual Azure Advisor recommendation from CSV data.
    """
    CATEGORY_CHOICES = [
        ('cost', 'Cost'),
        ('security', 'Security'),
        ('reliability', 'Reliability'),
        ('operational_excellence', 'Operational Excellence'),
        ('performance', 'Performance'),
    ]

    IMPACT_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationship to report
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='recommendations')

    # Azure Advisor CSV fields
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        help_text="Recommendation category"
    )
    business_impact = models.CharField(
        max_length=10,
        choices=IMPACT_CHOICES,
        help_text="Business impact level"
    )
    recommendation = models.TextField(help_text="Recommendation description")

    # Azure resource information
    subscription_id = models.CharField(max_length=255, blank=True)
    subscription_name = models.CharField(max_length=255, blank=True)
    resource_group = models.CharField(max_length=255, blank=True)
    resource_name = models.CharField(max_length=255, blank=True)
    resource_type = models.CharField(max_length=255, blank=True)

    # Financial impact
    potential_savings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Potential annual cost savings"
    )
    currency = models.CharField(max_length=3, default='USD')

    # Additional details
    potential_benefits = models.TextField(blank=True)
    retirement_date = models.DateField(null=True, blank=True)
    retiring_feature = models.CharField(max_length=255, blank=True)

    # Metadata from CSV
    advisor_score_impact = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Impact on Azure Advisor Score"
    )

    # Processing metadata
    csv_row_number = models.IntegerField(
        null=True,
        blank=True,
        help_text="Original row number in CSV file"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recommendations'
        ordering = ['-potential_savings', '-advisor_score_impact']
        indexes = [
            models.Index(fields=['report', 'category']),
            models.Index(fields=['business_impact']),
            models.Index(fields=['potential_savings']),
            models.Index(fields=['subscription_id']),
        ]

    def __str__(self):
        return f"{self.get_category_display()} - {self.resource_name or 'General'} (${self.potential_savings})"

    @property
    def monthly_savings(self):
        """Calculate monthly potential savings."""
        return self.potential_savings / 12 if self.potential_savings else 0


class ReportTemplate(models.Model):
    """
    Customizable report templates for different report types.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    report_type = models.CharField(max_length=20, choices=Report.REPORT_TYPES)

    # Template content
    html_template = models.TextField(help_text="HTML template content")
    css_styles = models.TextField(blank=True, help_text="Custom CSS styles")

    # Configuration
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # Metadata
    created_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'report_templates'
        unique_together = ['report_type', 'is_default']

    def __str__(self):
        default_marker = " (Default)" if self.is_default else ""
        return f"{self.name} - {self.get_report_type_display()}{default_marker}"

    def save(self, *args, **kwargs):
        # Ensure only one default template per report type
        if self.is_default:
            ReportTemplate.objects.filter(
                report_type=self.report_type,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class ReportShare(models.Model):
    """
    Track report sharing and access permissions.
    """
    PERMISSION_CHOICES = [
        ('view', 'View Only'),
        ('download', 'View & Download'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='shares')
    shared_by = models.ForeignKey('authentication.User', on_delete=models.CASCADE, related_name='shared_reports')
    shared_with_email = models.EmailField()
    permission_level = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='view')

    # Access control
    access_token = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    # Usage tracking
    access_count = models.IntegerField(default=0)
    last_accessed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'report_shares'
        unique_together = ['report', 'shared_with_email']

    def __str__(self):
        return f"Shared {self.report} with {self.shared_with_email}"

    @property
    def is_expired(self):
        """Check if the share link has expired."""
        return timezone.now() > self.expires_at

    def record_access(self):
        """Record an access to this shared report."""
        self.access_count += 1
        self.last_accessed_at = timezone.now()
        self.save(update_fields=['access_count', 'last_accessed_at'])