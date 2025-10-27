"""
Reports models for storing generated reports and recommendations.
"""

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Report(models.Model):
    """
    Model to store generated reports.
    """
    REPORT_TYPE_CHOICES = [
        ('cost', 'Cost Optimization'),
        ('security', 'Security'),
        ('performance', 'Performance'),
        ('operational', 'Operational Excellence'),
        ('reliability', 'Reliability'),
        ('detailed', 'Detailed Report'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, related_name='reports')
    title = models.CharField(max_length=255, blank=True, null=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, default='detailed')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # File information
    csv_file = models.FileField(upload_to='reports/csv/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='reports/pdf/', blank=True, null=True)
    file_url = models.URLField(max_length=500, blank=True, null=True)
    file_path = models.CharField(max_length=500, blank=True, null=True)
    file_size = models.BigIntegerField(default=0, help_text="File size in bytes")

    # User tracking
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_reports')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)

    # Error tracking
    error_message = models.TextField(blank=True, null=True)
    celery_task_id = models.CharField(max_length=255, blank=True, null=True)

    # Report metadata
    subscription_ids = models.JSONField(default=list, blank=True)
    date_range_start = models.DateField(null=True, blank=True)
    date_range_end = models.DateField(null=True, blank=True)
    parameters = models.JSONField(default=dict, blank=True)

    # Statistics
    total_recommendations = models.IntegerField(default=0)
    high_impact_count = models.IntegerField(default=0)
    medium_impact_count = models.IntegerField(default=0)
    low_impact_count = models.IntegerField(default=0)
    estimated_savings = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['report_type']),
            models.Index(fields=['client']),
        ]

    def __str__(self):
        type_display = self.get_report_type_display() if self.report_type else "Report"
        client_name = self.client.company_name if self.client else "Unknown"
        return f"{type_display} - {client_name} - {self.created_at}"

    def mark_as_completed(self, file_url=None, file_path=None):
        """Mark report as completed."""
        self.status = 'completed'
        self.processing_completed_at = timezone.now()
        if file_url:
            self.file_url = file_url
        if file_path:
            self.file_path = file_path
        self.save()

    def mark_as_failed(self, error_message):
        """Mark report as failed."""
        self.status = 'failed'
        self.error_message = error_message
        self.processing_completed_at = timezone.now()
        self.save()


class Recommendation(models.Model):
    """
    Model to store individual recommendations from Azure Advisor.
    """
    IMPACT_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]

    CATEGORY_CHOICES = [
        ('Cost', 'Cost'),
        ('Security', 'Security'),
        ('Performance', 'Performance'),
        ('Operational Excellence', 'Operational Excellence'),
        ('Reliability', 'Reliability'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='recommendations')

    # Recommendation details
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    impact = models.CharField(max_length=20, choices=IMPACT_CHOICES)
    title = models.CharField(max_length=500)
    description = models.TextField()
    recommendation = models.TextField()

    # Resource information
    resource_name = models.CharField(max_length=500, blank=True, null=True)
    resource_type = models.CharField(max_length=200, blank=True, null=True)
    resource_group = models.CharField(max_length=200, blank=True, null=True)
    subscription_id = models.CharField(max_length=200, blank=True, null=True)

    # Financial impact
    potential_savings = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')

    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recommendations'
        ordering = ['category', '-impact']
        indexes = [
            models.Index(fields=['report', 'category']),
            models.Index(fields=['impact']),
        ]

    def __str__(self):
        return f"{self.category} - {self.impact} - {self.title[:50]}"


class ReportTemplate(models.Model):
    """
    Model to store report templates for customization.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    template_type = models.CharField(max_length=50)

    # Template configuration
    configuration = models.JSONField(default=dict)

    # Ownership
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='report_templates')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'report_templates'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.template_type})"


class ReportShare(models.Model):
    """
    Model to manage report sharing between users.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='shares')
    shared_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_shared')
    shared_with = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_received')

    # Permissions
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    shared_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # Access tracking
    accessed_at = models.DateTimeField(null=True, blank=True)
    access_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'report_shares'
        ordering = ['-shared_at']
        unique_together = ['report', 'shared_with']

    def __str__(self):
        return f"{self.report} shared with {self.shared_with.email}"

    def is_expired(self):
        """Check if share has expired."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
