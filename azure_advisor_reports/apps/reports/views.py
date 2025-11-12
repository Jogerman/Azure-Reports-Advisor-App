"""
Views for reports app.
"""

import logging
import os
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db import transaction

from .models import Report, Recommendation, ReportTemplate, ReportShare
from .serializers import (
    ReportSerializer,
    ReportListSerializer,
    CSVUploadSerializer,
    RecommendationSerializer,
    RecommendationListSerializer,
    ReportTemplateSerializer,
    ReportShareSerializer,
)
from .services.csv_processor import process_csv_file, CSVProcessingError
from .tasks import process_csv_file as process_csv_task, generate_report as generate_report_task
from .generators import get_generator_for_report
from django.http import FileResponse, HttpResponse
from celery.result import AsyncResult

logger = logging.getLogger(__name__)


class ReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Report CRUD operations and CSV upload.
    """

    queryset = Report.objects.select_related('client', 'created_by').prefetch_related('recommendations')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['client', 'report_type', 'status', 'created_by']
    search_fields = ['title', 'client__company_name']
    ordering_fields = ['created_at', 'updated_at', 'processing_completed_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'list':
            return ReportListSerializer
        elif self.action == 'upload_csv':
            return CSVUploadSerializer
        return ReportSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()

        # Add any role-based filtering here if needed
        # For now, return all reports

        return queryset

    @action(detail=False, methods=['post'], url_path='upload')
    def upload_csv(self, request):
        """
        Upload CSV file and create a report.

        POST /api/v1/reports/upload/

        Request (multipart/form-data):
        {
            "csv_file": <file>,
            "client_id": "uuid",
            "report_type": "detailed",  # optional
            "title": "My Report"  # optional
        }

        Response:
        {
            "status": "success",
            "message": "CSV uploaded successfully",
            "data": {
                "report_id": "uuid",
                "report": { ... }
            }
        }
        """
        serializer = CSVUploadSerializer(data=request.data, context={'request': request})

        if not serializer.is_valid():
            return Response(
                {
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Create the report with uploaded file
            report = serializer.save()

            logger.info(
                f"CSV uploaded successfully - Report ID: {report.id}, "
                f"Client: {report.client.company_name}, "
                f"User: {request.user.email if request.user else 'Anonymous'}"
            )

            # Return the report data
            report_serializer = ReportSerializer(report)

            return Response(
                {
                    'status': 'success',
                    'message': 'CSV uploaded successfully',
                    'data': {
                        'report_id': str(report.id),
                        'report': report_serializer.data
                    }
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Failed to upload CSV: {str(e)}", exc_info=True)
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to upload CSV',
                    'errors': {'detail': str(e)}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='process')
    def process_csv(self, request, pk=None):
        """
        Process the uploaded CSV file and extract recommendations.

        POST /api/v1/reports/{id}/process/

        This endpoint processes the CSV file synchronously for now.
        In production, this will be moved to Celery for async processing.

        Response:
        {
            "status": "success",
            "message": "CSV processed successfully",
            "data": {
                "recommendations_count": 42,
                "statistics": { ... }
            }
        }
        """
        report = self.get_object()

        # Validate report state
        if report.status not in ['uploaded', 'failed']:
            return Response(
                {
                    'status': 'error',
                    'message': f'Report cannot be processed in current status: {report.status}',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not report.csv_file:
            return Response(
                {
                    'status': 'error',
                    'message': 'No CSV file uploaded for this report',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Update status to processing
            report.status = 'processing'
            report.processing_started_at = timezone.now()
            report.save(update_fields=['status', 'processing_started_at'])

            # Get the file path
            csv_file_path = report.csv_file.path

            logger.info(f"Starting CSV processing for report {report.id}")

            # Process the CSV file
            recommendations_data, statistics = process_csv_file(csv_file_path)

            # Save recommendations to database
            with transaction.atomic():
                # Delete existing recommendations if any
                report.recommendations.all().delete()

                # Create new recommendations
                recommendations = [
                    Recommendation(
                        report=report,
                        **rec_data
                    )
                    for rec_data in recommendations_data
                ]

                Recommendation.objects.bulk_create(recommendations, batch_size=500)

                # Update report with statistics
                report.analysis_data = statistics
                report.status = 'completed'
                report.processing_completed_at = timezone.now()
                report.error_message = ''
                report.save(update_fields=[
                    'analysis_data',
                    'status',
                    'processing_completed_at',
                    'error_message'
                ])

            logger.info(
                f"CSV processing completed for report {report.id} - "
                f"{len(recommendations_data)} recommendations created"
            )

            return Response(
                {
                    'status': 'success',
                    'message': 'CSV processed successfully',
                    'data': {
                        'report_id': str(report.id),
                        'recommendations_count': len(recommendations_data),
                        'statistics': statistics,
                    }
                },
                status=status.HTTP_200_OK
            )

        except CSVProcessingError as e:
            logger.error(f"CSV processing error for report {report.id}: {str(e)}")

            report.status = 'failed'
            report.error_message = str(e)
            report.processing_completed_at = timezone.now()
            report.retry_count += 1
            report.save(update_fields=[
                'status',
                'error_message',
                'processing_completed_at',
                'retry_count'
            ])

            return Response(
                {
                    'status': 'error',
                    'message': 'CSV processing failed',
                    'errors': {'detail': str(e)}
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.error(f"Unexpected error processing CSV for report {report.id}: {str(e)}", exc_info=True)

            report.status = 'failed'
            report.error_message = f"Internal error: {str(e)}"
            report.processing_completed_at = timezone.now()
            report.retry_count += 1
            report.save(update_fields=[
                'status',
                'error_message',
                'processing_completed_at',
                'retry_count'
            ])

            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to process CSV',
                    'errors': {'detail': 'An internal error occurred'}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='statistics')
    def statistics(self, request, pk=None):
        """
        Get statistics for a report.

        GET /api/v1/reports/{id}/statistics/

        Response:
        {
            "status": "success",
            "data": { ... }
        }
        """
        report = self.get_object()

        if report.status != 'completed':
            return Response(
                {
                    'status': 'error',
                    'message': 'Report is not completed yet',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get analysis data with defaults for missing fields
        analysis_data = report.analysis_data or {}

        # Define default values for all expected fields
        defaults = {
            'total_recommendations': 0,
            'total_potential_savings': 0,
            'average_potential_savings': 0,
            'estimated_monthly_savings': 0,
            'estimated_working_hours': 0,
            'advisor_score_impact': 0,
            'category_distribution': {},
            'business_impact_distribution': {},
            'top_recommendations': [],
            'processing_errors': 0,
        }

        # Merge defaults with actual data (actual data takes precedence)
        response_data = {**defaults, **analysis_data}

        # Add alias for frontend compatibility
        # Frontend expects 'average_savings_per_recommendation' but backend provides 'average_potential_savings'
        if 'average_potential_savings' in response_data:
            response_data['average_savings_per_recommendation'] = response_data['average_potential_savings']

        logger.debug(
            f"Statistics for report {report.id}: "
            f"total_recommendations={response_data.get('total_recommendations')}, "
            f"total_savings={response_data.get('total_potential_savings')}, "
            f"avg_savings={response_data.get('average_potential_savings')}"
        )

        return Response(
            {
                'status': 'success',
                'data': response_data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'], url_path='recommendations')
    def get_recommendations(self, request, pk=None):
        """
        Get recommendations for a report.

        GET /api/v1/reports/{id}/recommendations/

        Query params:
        - category: Filter by category
        - business_impact: Filter by impact level
        - min_savings: Minimum potential savings

        Response:
        {
            "status": "success",
            "count": 42,
            "data": [ ... ]
        }
        """
        report = self.get_object()

        recommendations = report.recommendations.all()

        # Log the request
        logger.debug(
            f"Recommendations requested for report {report.id}: "
            f"status={report.status}, total_count={recommendations.count()}"
        )

        # Apply filters
        category = request.query_params.get('category')
        if category:
            recommendations = recommendations.filter(category=category)

        impact = request.query_params.get('business_impact')
        if impact:
            recommendations = recommendations.filter(business_impact=impact)

        min_savings = request.query_params.get('min_savings')
        if min_savings:
            try:
                recommendations = recommendations.filter(potential_savings__gte=float(min_savings))
            except ValueError:
                logger.warning(f"Invalid min_savings value: {min_savings}")
                pass

        # Serialize
        serializer = RecommendationListSerializer(recommendations, many=True)

        # Log the response summary
        logger.debug(
            f"Returning {len(serializer.data)} recommendations for report {report.id}"
        )

        return Response(
            {
                'status': 'success',
                'count': recommendations.count(),
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='generate')
    def generate_report(self, request, pk=None):
        """
        Generate HTML and/or PDF report files asynchronously.

        POST /api/v1/reports/{id}/generate/

        Request body:
        {
            "format": "both",  # "html", "pdf", or "both" (default: "both")
            "async": true      # Generate asynchronously (default: true)
        }

        Response (async=true):
        {
            "status": "success",
            "message": "Report generation started",
            "data": {
                "report_id": "uuid",
                "task_id": "celery-task-id",
                "status_url": "/api/v1/reports/{id}/status/"
            }
        }

        Response (async=false):
        {
            "status": "success",
            "message": "HTML, PDF report generated successfully",
            "data": {
                "report_id": "uuid",
                "files_generated": ["HTML", "PDF"],
                "html_url": "...",
                "pdf_url": "..."
            }
        }
        """
        report = self.get_object()

        # Validate report state
        if report.status != 'completed':
            return Response(
                {
                    'status': 'error',
                    'message': f'Report must be completed before generation. Current status: {report.status}',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if report.recommendations.count() == 0:
            return Response(
                {
                    'status': 'error',
                    'message': 'Report has no recommendations to include',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get parameters
        format_type = request.data.get('format', 'both')
        async_mode = request.data.get('async', True)

        if format_type not in ['html', 'pdf', 'both']:
            return Response(
                {
                    'status': 'error',
                    'message': 'Invalid format. Must be "html", "pdf", or "both"',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Async mode (recommended for production)
            if async_mode:
                logger.info(f"Starting async report generation for {report.id} (format: {format_type})")

                # Trigger Celery task
                task = generate_report_task.delay(str(report.id), format_type=format_type)

                return Response(
                    {
                        'status': 'success',
                        'message': 'Report generation started',
                        'data': {
                            'report_id': str(report.id),
                            'task_id': task.id,
                            'status_url': request.build_absolute_uri(
                                f'/api/v1/reports/{report.id}/status/?task_id={task.id}'
                            )
                        }
                    },
                    status=status.HTTP_202_ACCEPTED
                )

            # Synchronous mode (for testing or small reports)
            logger.info(f"Generating {format_type} report synchronously for {report.id}")

            # Get the appropriate generator
            generator = get_generator_for_report(report)

            files_generated = []

            # Generate HTML
            if format_type in ['html', 'both']:
                html_path = generator.generate_html()
                report.html_file = html_path
                files_generated.append('HTML')

            # Generate PDF
            if format_type in ['pdf', 'both']:
                pdf_path = generator.generate_pdf()
                report.pdf_file = pdf_path
                files_generated.append('PDF')

            # Update report
            report.save(update_fields=['html_file', 'pdf_file', 'updated_at'])

            logger.info(f"Report generation completed for {report.id}: {', '.join(files_generated)}")

            return Response(
                {
                    'status': 'success',
                    'message': f'{", ".join(files_generated)} report generated successfully',
                    'data': {
                        'report_id': str(report.id),
                        'files_generated': files_generated,
                        'html_url': request.build_absolute_uri(
                            f'/api/v1/reports/{report.id}/download/html/'
                        ) if report.html_file else None,
                        'pdf_url': request.build_absolute_uri(
                            f'/api/v1/reports/{report.id}/download/pdf/'
                        ) if report.pdf_file else None,
                    }
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Failed to generate report for {report.id}: {str(e)}", exc_info=True)
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to generate report',
                    'errors': {'detail': str(e)}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='status')
    def task_status(self, request, pk=None):
        """
        Get task status for report processing or generation.

        GET /api/v1/reports/{id}/status/?task_id={celery-task-id}

        Response:
        {
            "status": "success",
            "data": {
                "report_id": "uuid",
                "report_status": "completed",
                "task_id": "celery-task-id",
                "task_state": "SUCCESS",
                "task_result": {...}
            }
        }
        """
        report = self.get_object()

        # Get task_id from query params
        task_id = request.query_params.get('task_id')

        response_data = {
            'report_id': str(report.id),
            'report_status': report.status,
            'report_data': {
                'client': report.client.company_name,
                'report_type': report.get_report_type_display(),
                'created_at': report.created_at.isoformat(),
                'updated_at': report.updated_at.isoformat(),
            }
        }

        # If task_id provided, check Celery task status
        if task_id:
            try:
                task_result = AsyncResult(task_id)
                response_data.update({
                    'task_id': task_id,
                    'task_state': task_result.state,
                    'task_info': task_result.info if task_result.info else None,
                })

                # Add task-specific details based on state
                if task_result.state == 'PENDING':
                    response_data['message'] = 'Task is pending or does not exist'
                elif task_result.state == 'STARTED':
                    response_data['message'] = 'Task has started'
                elif task_result.state == 'SUCCESS':
                    response_data['message'] = 'Task completed successfully'
                    response_data['task_result'] = task_result.result
                elif task_result.state == 'FAILURE':
                    response_data['message'] = 'Task failed'
                    response_data['task_error'] = str(task_result.info)
                elif task_result.state == 'RETRY':
                    response_data['message'] = 'Task is retrying'

            except Exception as e:
                logger.error(f"Error getting task status for {task_id}: {str(e)}")
                response_data['task_error'] = f'Could not retrieve task status: {str(e)}'

        # Add download URLs if files are ready
        if report.html_file:
            response_data['html_url'] = request.build_absolute_uri(
                f'/api/v1/reports/{report.id}/download/html/'
            )
        if report.pdf_file:
            response_data['pdf_url'] = request.build_absolute_uri(
                f'/api/v1/reports/{report.id}/download/pdf/'
            )

        # Add processing details
        if report.processing_started_at:
            response_data['processing_started_at'] = report.processing_started_at.isoformat()
        if report.processing_completed_at:
            response_data['processing_completed_at'] = report.processing_completed_at.isoformat()
        if report.processing_duration:
            response_data['processing_duration_seconds'] = report.processing_duration.total_seconds()

        # Add error info if failed
        if report.status == 'failed' and report.error_message:
            response_data['error_message'] = report.error_message
            response_data['retry_count'] = report.retry_count
            response_data['can_retry'] = report.can_retry()

        return Response(
            {
                'status': 'success',
                'data': response_data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'], url_path='download/(?P<file_format>html|pdf)', url_name='download')
    def download_report(self, request, pk=None, file_format=None):
        """
        Download or display generated report file.

        GET /api/v1/reports/{id}/download/html/  - Displays HTML in browser
        GET /api/v1/reports/{id}/download/pdf/   - Downloads PDF file

        Response:
        - HTML: Displayed inline in browser (Content-Disposition: inline)
        - PDF: Downloaded as attachment (Content-Disposition: attachment)
        """
        report = self.get_object()

        # Validate format
        if file_format not in ['html', 'pdf']:
            return Response(
                {
                    'status': 'error',
                    'message': 'Invalid format. Must be "html" or "pdf"',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get file field
        file_field = report.html_file if file_format == 'html' else report.pdf_file

        # Check if file exists
        if not file_field:
            return Response(
                {
                    'status': 'error',
                    'message': f'{file_format.upper()} report has not been generated yet',
                },
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            # Prepare filename
            filename = f"{report.client.company_name.replace(' ', '_')}_" \
                      f"{report.get_report_type_display().replace(' ', '_')}_" \
                      f"{report.created_at.strftime('%Y%m%d')}.{file_format}"

            # Open file from storage (works with both local and cloud storage)
            file_handle = file_field.open('rb')

            # Set content type
            content_type = 'text/html; charset=utf-8' if file_format == 'html' else 'application/pdf'

            # HTML files should be displayed inline, PDF files should be downloaded
            as_attachment = file_format == 'pdf'

            response = FileResponse(
                file_handle,
                content_type=content_type,
                as_attachment=as_attachment,
                filename=filename
            )

            action = 'Downloaded' if as_attachment else 'Displayed'
            logger.info(f"{action} {file_format.upper()} report {report.id} for user {request.user.email}")

            return response

        except Exception as e:
            logger.error(f"Failed to serve {file_format} report {report.id}: {str(e)}", exc_info=True)
            return Response(
                {
                    'status': 'error',
                    'message': f'Failed to serve {file_format.upper()} report',
                    'errors': {'detail': str(e)}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='history/statistics')
    def history_statistics(self, request):
        """
        Get statistics for report history

        GET /api/reports/history/statistics/

        Query params:
        - client: Filter by client ID
        - report_type: Filter by report type
        - status: Filter by status
        - created_by: Filter by user
        - date_from: Start date (YYYY-MM-DD)
        - date_to: End date (YYYY-MM-DD)

        Returns:
        {
            "total_reports": 150,
            "total_reports_change": 12.5,
            "reports_this_month": 25,
            "reports_this_month_change": 8.3,
            "total_size": 1073741824,
            "total_size_formatted": "1.0 GB",
            "total_size_change": 5.2,
            "breakdown": {
                "cost": 45,
                "security": 30,
                "operations": 25,
                "detailed": 35,
                "executive": 15
            }
        }
        """
        from django.db.models import Count, Q, Sum, Avg, FloatField, IntegerField
        from django.db.models.functions import TruncDate, TruncMonth
        from django.db.models.expressions import RawSQL
        from datetime import datetime, timedelta
        from django.utils import timezone

        queryset = self.filter_queryset(self.get_queryset())

        # Get current month start and end
        now = timezone.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            next_month_start = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            next_month_start = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)

        # Get previous month for comparison
        if now.month == 1:
            prev_month_start = now.replace(year=now.year - 1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
            prev_month_end = current_month_start
        else:
            prev_month_start = now.replace(month=now.month - 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            prev_month_end = current_month_start

        # Calculate total reports
        total_reports = queryset.count()

        # Calculate reports this month
        reports_this_month = queryset.filter(
            created_at__gte=current_month_start,
            created_at__lt=next_month_start
        ).count()

        # Calculate reports last month for comparison
        reports_last_month = queryset.filter(
            created_at__gte=prev_month_start,
            created_at__lt=prev_month_end
        ).count()

        # Calculate percentage changes
        total_reports_change = 0.0
        reports_this_month_change = 0.0
        if reports_last_month > 0:
            reports_this_month_change = ((reports_this_month - reports_last_month) / reports_last_month) * 100

        # Calculate total file sizes
        total_csv_size = 0
        total_html_size = 0
        total_pdf_size = 0

        for report in queryset:
            if report.csv_file:
                try:
                    total_csv_size += report.csv_file.size
                except (OSError, ValueError):
                    pass
            if report.html_file:
                try:
                    total_html_size += report.html_file.size
                except (OSError, ValueError):
                    pass
            if report.pdf_file:
                try:
                    total_pdf_size += report.pdf_file.size
                except (OSError, ValueError):
                    pass

        total_size = total_csv_size + total_html_size + total_pdf_size

        # Format total size
        def format_bytes(bytes_size):
            """Convert bytes to human-readable format"""
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_size < 1024.0:
                    return f"{bytes_size:.1f} {unit}"
                bytes_size /= 1024.0
            return f"{bytes_size:.1f} PB"

        total_size_formatted = format_bytes(total_size)

        # Calculate breakdown by report type
        breakdown_data = queryset.values('report_type').annotate(count=Count('id'))
        breakdown = {
            'cost': 0,
            'security': 0,
            'operations': 0,
            'detailed': 0,
            'executive': 0,
        }

        for item in breakdown_data:
            report_type = item['report_type']
            if report_type in breakdown:
                breakdown[report_type] = item['count']

        # Calculate total size change (simplified - using 0 for now as we'd need historical data)
        total_size_change = 0.0

        # Build response matching frontend expectations
        stats = {
            'total_reports': total_reports,
            'total_reports_change': round(total_reports_change, 1),
            'reports_this_month': reports_this_month,
            'reports_this_month_change': round(reports_this_month_change, 1),
            'total_size': total_size,
            'total_size_formatted': total_size_formatted,
            'total_size_change': round(total_size_change, 1),
            'breakdown': breakdown,
        }

        return Response(stats)

    @action(detail=False, methods=['get'], url_path='history/trends')
    def history_trends(self, request):
        """
        Get historical trends data

        GET /api/reports/history/trends/

        Query params:
        - granularity: 'day', 'week', or 'month' (default: 'day')
        - date_from: Start date
        - date_to: End date

        Returns:
        {
            "data": [
                {
                    "date": "2025-11-01",
                    "total": 25,
                    "by_type": {
                        "cost": 10,
                        "security": 5,
                        "operations": 3,
                        "detailed": 5,
                        "executive": 2
                    }
                }
            ]
        }
        """
        from django.db.models import Count, Q
        from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
        from datetime import datetime, timedelta

        queryset = self.filter_queryset(self.get_queryset())
        granularity = request.query_params.get('granularity', 'day')

        # Select truncation function based on granularity
        trunc_func = {
            'day': TruncDate,
            'week': TruncWeek,
            'month': TruncMonth
        }.get(granularity, TruncDate)

        # Group by date and count reports with breakdown by type
        trends = queryset.annotate(
            date=trunc_func('created_at')
        ).values('date').annotate(
            count=Count('id'),
            cost_count=Count('id', filter=Q(report_type='cost')),
            security_count=Count('id', filter=Q(report_type='security')),
            operations_count=Count('id', filter=Q(report_type='operations')),
            detailed_count=Count('id', filter=Q(report_type='detailed')),
            executive_count=Count('id', filter=Q(report_type='executive'))
        ).order_by('date')

        # Format data for frontend with by_type breakdown
        data = [
            {
                'date': item['date'].isoformat() if item['date'] else None,
                'total': item['count'],
                'by_type': {
                    'cost': item['cost_count'],
                    'security': item['security_count'],
                    'operations': item['operations_count'],
                    'detailed': item['detailed_count'],
                    'executive': item['executive_count'],
                }
            }
            for item in trends
        ]

        return Response({'data': data})

    @action(detail=False, methods=['get'], url_path='users')
    def get_users(self, request):
        """
        Get list of users who have created reports

        GET /api/reports/users/

        Returns:
        {
            "users": [
                {
                    "id": "uuid",
                    "username": "jdoe",
                    "full_name": "John Doe",
                    "report_count": 15
                }
            ]
        }
        """
        from django.contrib.auth import get_user_model
        from django.db.models import Count

        User = get_user_model()

        # Get users with report counts
        users_queryset = User.objects.filter(
            created_reports__isnull=False
        ).annotate(
            report_count=Count('created_reports')
        ).distinct()

        # Format users with full_name
        users_list = []
        for user in users_queryset:
            full_name = f"{user.first_name} {user.last_name}".strip()
            if not full_name:
                full_name = user.username

            users_list.append({
                'id': str(user.id),
                'username': user.username,
                'full_name': full_name,
                'report_count': user.report_count
            })

        return Response({'users': users_list})

    @action(detail=False, methods=['post'], url_path='export-csv')
    def export_csv(self, request):
        """
        Export reports to CSV

        POST /api/reports/export-csv/

        Body: same filter params as list endpoint
        """
        import csv
        from io import StringIO

        queryset = self.filter_queryset(self.get_queryset())

        # Create CSV
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'ID', 'Title', 'Client', 'Report Type', 'Status',
            'Created By', 'Created At', 'Completed At',
            'Total Recommendations', 'Potential Savings'
        ])

        # Write data
        for report in queryset:
            writer.writerow([
                str(report.id),
                report.title,
                report.client.company_name,
                report.report_type,
                report.status,
                report.created_by.username if report.created_by else '',
                report.created_at.isoformat(),
                report.processing_completed_at.isoformat() if report.processing_completed_at else '',
                report.analysis_data.get('total_recommendations', 0) if report.analysis_data else 0,
                report.analysis_data.get('total_potential_savings', 0) if report.analysis_data else 0
            ])

        # Create response
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reports_export.csv"'

        return response


class RecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Recommendation read-only operations.
    """

    queryset = Recommendation.objects.select_related('report', 'report__client')
    serializer_class = RecommendationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['report', 'category', 'business_impact']
    search_fields = ['recommendation', 'resource_name', 'resource_type']
    ordering_fields = ['potential_savings', 'advisor_score_impact', 'created_at']
    ordering = ['-potential_savings']

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()

        # Filter by report if specified
        report_id = self.request.query_params.get('report_id')
        if report_id:
            queryset = queryset.filter(report_id=report_id)

        return queryset


class ReportTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ReportTemplate CRUD operations.
    """

    queryset = ReportTemplate.objects.all()
    serializer_class = ReportTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['report_type', 'is_default', 'is_active']
    search_fields = ['name']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        """Set created_by to current user."""
        serializer.save(created_by=self.request.user)


class ReportShareViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ReportShare CRUD operations.
    """

    queryset = ReportShare.objects.select_related('report', 'shared_by')
    serializer_class = ReportShareSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['report', 'is_active', 'permission_level']
    ordering_fields = ['created_at', 'expires_at', 'last_accessed_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        """Set shared_by to current user."""
        serializer.save(shared_by=self.request.user)

    def get_queryset(self):
        """Filter queryset to only show shares created by current user."""
        return super().get_queryset().filter(shared_by=self.request.user)
