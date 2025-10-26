"""
Views for reports app.
"""

import logging
import os
import csv
from datetime import datetime, timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Sum, Q
from django.conf import settings
from django.core.cache import cache

from .models import Report, Recommendation, ReportTemplate, ReportShare
from .serializers import (
    ReportSerializer,
    ReportListSerializer,
    CSVUploadSerializer,
    RecommendationSerializer,
    RecommendationListSerializer,
    ReportTemplateSerializer,
    ReportShareSerializer,
    HistoryStatisticsSerializer,
    TrendsResponseSerializer,
    UsersListResponseSerializer,
    CSVExportRequestSerializer,
)
from .filters import ReportFilter
from .utils import (
    calculate_period_comparison,
    calculate_percentage_change,
    format_file_size,
    get_report_type_breakdown,
    get_trends_data,
    apply_filters_from_params,
    get_file_size_from_report,
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
    Includes history endpoints for statistics, trends, and analytics.
    """

    queryset = Report.objects.select_related('client', 'created_by').prefetch_related('recommendations')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ReportFilter
    search_fields = ['title', 'client__company_name']
    ordering_fields = ['created_at', 'updated_at', 'processing_completed_at', 'client__company_name', 'report_type', 'status']
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

        # Get file path - handle both relative and absolute paths
        file_path_str = file_field.name if hasattr(file_field, 'name') else str(file_field)

        # Remove any leading /app/media/ or /media/ prefixes
        file_path_str = file_path_str.replace('/app/media/', '').replace('/media/', '')

        # Construct full path
        full_path = os.path.join(settings.MEDIA_ROOT, file_path_str)

        # Check if file exists on disk
        if not os.path.exists(full_path):
            logger.error(f"File not found on disk: {full_path}")
            return Response(
                {
                    'status': 'error',
                    'message': f'{file_format.upper()} file not found on server',
                    'debug_info': {
                        'file_field': str(file_field),
                        'expected_path': full_path,
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            # Prepare filename
            filename = f"{report.client.company_name.replace(' ', '_')}_" \
                      f"{report.get_report_type_display().replace(' ', '_')}_" \
                      f"{report.created_at.strftime('%Y%m%d')}.{file_format}"

            # Open file and return as response
            file_handle = open(full_path, 'rb')

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
        Get aggregated statistics for reports based on filters.

        GET /api/v1/reports/history/statistics/

        Query parameters:
        - date_from: ISO date (YYYY-MM-DD)
        - date_to: ISO date (YYYY-MM-DD)
        - report_type: Comma-separated list of report types
        - status: Comma-separated list of statuses
        - created_by: Comma-separated list of user IDs or usernames
        - client_id: Client UUID

        Response:
        {
            "total_reports": 1247,
            "total_reports_change": 12.5,
            "reports_this_month": 87,
            "reports_this_month_change": 5.2,
            "total_size": 2516582400,
            "total_size_formatted": "2.4 GB",
            "total_size_change": 8.1,
            "breakdown": {
                "cost": 45,
                "security": 32,
                ...
            }
        }
        """
        # Create cache key based on query params
        cache_params = dict(request.query_params)
        cache_key = f"history_stats_{hash(str(sorted(cache_params.items())))}"

        # Try to get from cache (2 minutes cache)
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Returning cached statistics for key: {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        try:
            # Parse date range parameters
            date_from_str = request.query_params.get('date_from')
            date_to_str = request.query_params.get('date_to')

            date_from = None
            date_to = None

            if date_from_str:
                try:
                    date_from = datetime.fromisoformat(date_from_str)
                    if timezone.is_naive(date_from):
                        date_from = timezone.make_aware(date_from)
                except (ValueError, TypeError):
                    return Response(
                        {
                            'status': 'error',
                            'message': f'Invalid date_from format. Use YYYY-MM-DD',
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

            if date_to_str:
                try:
                    date_to = datetime.fromisoformat(date_to_str)
                    if timezone.is_naive(date_to):
                        date_to = timezone.make_aware(date_to)
                    # Set to end of day
                    date_to = date_to.replace(hour=23, minute=59, second=59)
                except (ValueError, TypeError):
                    return Response(
                        {
                            'status': 'error',
                            'message': f'Invalid date_to format. Use YYYY-MM-DD',
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Validate date range
            if date_from and date_to and date_from > date_to:
                return Response(
                    {
                        'status': 'error',
                        'message': 'date_from must be less than or equal to date_to',
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get base queryset and apply filters
            queryset = self.get_queryset()
            queryset = apply_filters_from_params(queryset, request.query_params)

            # Calculate statistics for current period
            current_queryset, previous_queryset, days = calculate_period_comparison(
                queryset, date_from, date_to
            )

            # Total reports
            total_reports = current_queryset.count() if date_from and date_to else queryset.count()
            previous_total = previous_queryset.count()
            total_reports_change = calculate_percentage_change(total_reports, previous_total)

            # Reports this month
            now = timezone.now()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = now

            # Calculate previous month dates
            if month_start.month == 1:
                prev_month_start = month_start.replace(year=month_start.year - 1, month=12)
            else:
                prev_month_start = month_start.replace(month=month_start.month - 1)

            prev_month_end = month_start - timedelta(seconds=1)

            reports_this_month = queryset.filter(
                created_at__gte=month_start,
                created_at__lte=month_end
            ).count()

            reports_prev_month = queryset.filter(
                created_at__gte=prev_month_start,
                created_at__lte=prev_month_end
            ).count()

            reports_this_month_change = calculate_percentage_change(
                reports_this_month, reports_prev_month
            )

            # Total file size
            target_queryset = current_queryset if date_from and date_to else queryset

            # Calculate total size from files
            total_size = 0
            for report in target_queryset:
                total_size += get_file_size_from_report(report)

            # Calculate previous period size for comparison
            previous_size = 0
            if previous_queryset.exists():
                for report in previous_queryset:
                    previous_size += get_file_size_from_report(report)

            total_size_change = calculate_percentage_change(total_size, previous_size)
            total_size_formatted = format_file_size(total_size)

            # Breakdown by report type
            breakdown = get_report_type_breakdown(target_queryset)

            # Build response
            response_data = {
                'total_reports': total_reports,
                'total_reports_change': total_reports_change,
                'reports_this_month': reports_this_month,
                'reports_this_month_change': reports_this_month_change,
                'total_size': total_size,
                'total_size_formatted': total_size_formatted,
                'total_size_change': total_size_change,
                'breakdown': breakdown,
            }

            # Cache for 2 minutes (120 seconds)
            cache.set(cache_key, response_data, 120)

            logger.info(
                f"History statistics calculated: total={total_reports}, "
                f"this_month={reports_this_month}, size={total_size_formatted}"
            )

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error calculating history statistics: {str(e)}", exc_info=True)
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to calculate statistics',
                    'errors': {'detail': str(e)}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='history/trends')
    def history_trends(self, request):
        """
        Get trend data for reports over a date range.

        GET /api/v1/reports/history/trends/

        Query parameters (required):
        - date_from: ISO date (YYYY-MM-DD)
        - date_to: ISO date (YYYY-MM-DD)

        Query parameters (optional):
        - granularity: "day" | "week" | "month" (default: "day")
        - report_type: Comma-separated list of report types
        - status: Comma-separated list of statuses
        - created_by: Comma-separated list of user IDs or usernames
        - client_id: Client UUID

        Response:
        {
            "data": [
                {
                    "date": "2025-01-01",
                    "total": 15,
                    "by_type": {
                        "cost": 5,
                        "security": 4,
                        ...
                    }
                },
                ...
            ]
        }
        """
        try:
            # Validate required parameters
            date_from_str = request.query_params.get('date_from')
            date_to_str = request.query_params.get('date_to')

            if not date_from_str or not date_to_str:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Both date_from and date_to are required',
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Parse dates
            try:
                date_from = datetime.fromisoformat(date_from_str)
                if timezone.is_naive(date_from):
                    date_from = timezone.make_aware(date_from)
            except (ValueError, TypeError):
                return Response(
                    {
                        'status': 'error',
                        'message': 'Invalid date_from format. Use YYYY-MM-DD',
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                date_to = datetime.fromisoformat(date_to_str)
                if timezone.is_naive(date_to):
                    date_to = timezone.make_aware(date_to)
                # Set to end of day
                date_to = date_to.replace(hour=23, minute=59, second=59)
            except (ValueError, TypeError):
                return Response(
                    {
                        'status': 'error',
                        'message': 'Invalid date_to format. Use YYYY-MM-DD',
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate date range
            if date_from > date_to:
                return Response(
                    {
                        'status': 'error',
                        'message': 'date_from must be less than or equal to date_to',
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get granularity
            granularity = request.query_params.get('granularity', 'day')
            valid_granularities = ['day', 'week', 'month']

            if granularity not in valid_granularities:
                return Response(
                    {
                        'status': 'error',
                        'message': f'Invalid granularity. Must be one of: {", ".join(valid_granularities)}',
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get base queryset and apply filters
            queryset = self.get_queryset()
            queryset = apply_filters_from_params(queryset, request.query_params)

            # Generate trend data
            trends_data = get_trends_data(queryset, date_from, date_to, granularity)

            logger.info(
                f"Trends data generated: {len(trends_data)} data points "
                f"from {date_from_str} to {date_to_str} with {granularity} granularity"
            )

            return Response(
                {'data': trends_data},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error generating trends data: {str(e)}", exc_info=True)
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to generate trends data',
                    'errors': {'detail': str(e)}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='users')
    def users_list(self, request):
        """
        Get list of users who have created reports for filter dropdowns.

        GET /api/v1/reports/users/

        Response:
        {
            "users": [
                {
                    "id": "uuid",
                    "username": "john.doe@company.com",
                    "full_name": "John Doe",
                    "report_count": 42
                },
                ...
            ]
        }
        """
        try:
            from apps.authentication.models import User

            # Get users who have created at least one report
            users = User.objects.annotate(
                report_count=Count('created_reports')
            ).filter(
                report_count__gt=0
            ).order_by('-report_count')

            # Build response data
            users_data = [
                {
                    'id': str(user.id),
                    'username': user.username,
                    'full_name': user.full_name or f"{user.first_name} {user.last_name}".strip() or user.username,
                    'report_count': user.report_count,
                }
                for user in users
            ]

            logger.info(f"Users list retrieved: {len(users_data)} users with reports")

            return Response(
                {'users': users_data},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error retrieving users list: {str(e)}", exc_info=True)
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to retrieve users list',
                    'errors': {'detail': str(e)}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='export-csv')
    def export_csv(self, request):
        """
        Export filtered reports to CSV file.

        POST /api/v1/reports/export-csv/

        Request body:
        {
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "report_type": ["cost", "security"],
            "status": ["completed"],
            "created_by": ["uuid1", "uuid2"],
            "client_id": "client-uuid",
            "search": "azure"
        }

        Response:
        - CSV file download
        - Content-Type: text/csv
        - Content-Disposition: attachment; filename="reports_export_YYYY-MM-DD.csv"
        """
        try:
            # Validate request data
            serializer = CSVExportRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {
                        'status': 'error',
                        'message': 'Invalid request data',
                        'errors': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            validated_data = serializer.validated_data

            # Get base queryset
            queryset = self.get_queryset()

            # Apply filters from validated data
            # Convert validated data to query params format for apply_filters_from_params
            filter_params = {}

            if validated_data.get('date_from'):
                filter_params['date_from'] = validated_data['date_from'].isoformat()

            if validated_data.get('date_to'):
                filter_params['date_to'] = validated_data['date_to'].isoformat()

            if validated_data.get('report_type'):
                filter_params['report_type'] = validated_data['report_type']

            if validated_data.get('status'):
                filter_params['status'] = validated_data['status']

            if validated_data.get('created_by'):
                filter_params['created_by'] = validated_data['created_by']

            if validated_data.get('client_id'):
                filter_params['client_id'] = str(validated_data['client_id'])

            if validated_data.get('search'):
                filter_params['search'] = validated_data['search']

            # Apply filters
            queryset = apply_filters_from_params(queryset, filter_params)

            # Limit to 10,000 records to prevent timeout
            MAX_EXPORT_RECORDS = 10000
            total_count = queryset.count()

            if total_count > MAX_EXPORT_RECORDS:
                return Response(
                    {
                        'status': 'error',
                        'message': f'Too many records to export. Maximum is {MAX_EXPORT_RECORDS}, found {total_count}. Please add more filters.',
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Order by created_at descending
            queryset = queryset.order_by('-created_at')

            # Create CSV response
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            filename = f"reports_export_{timezone.now().strftime('%Y-%m-%d')}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            # Write CSV
            writer = csv.writer(response)

            # Write header
            writer.writerow([
                'ID',
                'Title',
                'Report Type',
                'Client',
                'Created By',
                'Created Date',
                'Status',
                'File Size',
                'Recommendations',
                'Potential Savings',
            ])

            # Write data rows
            for report in queryset:
                # Calculate file size
                file_size = get_file_size_from_report(report)
                file_size_formatted = format_file_size(file_size)

                # Get user name
                user_name = 'N/A'
                if report.created_by:
                    user_name = report.created_by.full_name or report.created_by.username

                # Get title
                title = report.title or f"{report.get_report_type_display()} Report"

                writer.writerow([
                    str(report.id),
                    title,
                    report.get_report_type_display(),
                    report.client.company_name,
                    user_name,
                    report.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    report.get_status_display(),
                    file_size_formatted,
                    report.recommendation_count,
                    f"${report.total_potential_savings:.2f}" if report.total_potential_savings else '$0.00',
                ])

            logger.info(
                f"CSV export generated: {total_count} reports exported by user {request.user.username}"
            )

            return response

        except Exception as e:
            logger.error(f"Error exporting reports to CSV: {str(e)}", exc_info=True)
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to export reports to CSV',
                    'errors': {'detail': str(e)}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
