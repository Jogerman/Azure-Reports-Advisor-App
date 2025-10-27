"""
Unit tests for Reports API views.

Tests all endpoints in ReportViewSet including:
- CSV upload
- CSV processing
- Report generation
- File downloads
- Statistics and recommendations retrieval
"""

import pytest
import io
import os
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestReportViewSetUpload:
    """Test CSV upload endpoint POST /api/v1/reports/upload/"""

    def test_upload_csv_success(self, authenticated_api_client, test_client, sample_csv_valid):
        """Test successful CSV upload creates a report."""
        # Import inside the test to avoid Django setup issues
        from apps.reports.models import Report

        csv_content = sample_csv_valid.encode('utf-8')
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

        data = {
            'csv_file': csv_file,
            'client_id': str(test_client.id),
            'report_type': 'detailed',
            'title': 'Test Upload Report'
        }

        response = authenticated_api_client.post('/api/v1/reports/upload/', data, format='multipart')

        assert response.status_code == 201
        assert response.data['status'] == 'success'
        assert 'report_id' in response.data['data']
        assert response.data['data']['report']['title'] == 'Test Upload Report'

        # Verify report was created
        report = Report.objects.get(id=response.data['data']['report_id'])
        assert report.client == test_client
        assert report.report_type == 'detailed'
        assert report.status == 'uploaded'
        assert report.csv_file is not None

    def test_upload_csv_without_authentication(self, api_client, test_client, sample_csv_valid):
        """Test upload fails without authentication."""
        csv_content = sample_csv_valid.encode('utf-8')
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

        data = {
            'csv_file': csv_file,
            'client_id': str(test_client.id),
            'report_type': 'detailed'
        }

        response = api_client.post('/api/v1/reports/upload/', data, format='multipart')
        assert response.status_code == 401

    def test_upload_csv_missing_file(self, authenticated_api_client, test_client):
        """Test upload fails when CSV file is missing."""
        data = {
            'client_id': str(test_client.id),
            'report_type': 'detailed'
        }

        response = authenticated_api_client.post('/api/v1/reports/upload/', data)
        assert response.status_code == 400
        assert response.data['status'] == 'error'

    def test_upload_csv_missing_client_id(self, authenticated_api_client, sample_csv_valid):
        """Test upload fails when client_id is missing."""
        csv_content = sample_csv_valid.encode('utf-8')
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

        data = {
            'csv_file': csv_file,
            'report_type': 'detailed'
        }

        response = authenticated_api_client.post('/api/v1/reports/upload/', data, format='multipart')
        assert response.status_code == 400

    def test_upload_csv_invalid_client_id(self, authenticated_api_client, sample_csv_valid):
        """Test upload fails with invalid client ID."""
        csv_content = sample_csv_valid.encode('utf-8')
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

        data = {
            'csv_file': csv_file,
            'client_id': '00000000-0000-0000-0000-000000000000',
            'report_type': 'detailed'
        }

        response = authenticated_api_client.post('/api/v1/reports/upload/', data, format='multipart')
        assert response.status_code == 400

    def test_upload_csv_invalid_report_type(self, authenticated_api_client, test_client, sample_csv_valid):
        """Test upload fails with invalid report type."""
        csv_content = sample_csv_valid.encode('utf-8')
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

        data = {
            'csv_file': csv_file,
            'client_id': str(test_client.id),
            'report_type': 'invalid_type'
        }

        response = authenticated_api_client.post('/api/v1/reports/upload/', data, format='multipart')
        assert response.status_code == 400

    def test_upload_csv_non_csv_file(self, authenticated_api_client, test_client):
        """Test upload fails with non-CSV file."""
        txt_file = SimpleUploadedFile("test.txt", b"Not a CSV file", content_type="text/plain")

        data = {
            'csv_file': txt_file,
            'client_id': str(test_client.id),
            'report_type': 'detailed'
        }

        response = authenticated_api_client.post('/api/v1/reports/upload/', data, format='multipart')
        assert response.status_code == 400


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestReportViewSetProcessCSV:
    """Test CSV processing endpoint POST /api/v1/reports/{id}/process/"""

    def test_process_csv_success(self, authenticated_api_client, test_report_with_csv, sample_csv_file_valid):
        """Test successful CSV processing."""
        from apps.reports.models import Recommendation

        # Update the report's CSV file to point to actual valid file
        test_report_with_csv.csv_file.name = sample_csv_file_valid
        test_report_with_csv.status = 'uploaded'
        test_report_with_csv.save()

        response = authenticated_api_client.post(
            f'/api/v1/reports/{test_report_with_csv.id}/process/'
        )

        assert response.status_code == 200
        assert response.data['status'] == 'success'
        assert response.data['data']['recommendations_count'] > 0

        # Verify report status was updated
        test_report_with_csv.refresh_from_db()
        assert test_report_with_csv.status == 'completed'
        assert test_report_with_csv.analysis_data is not None

        # Verify recommendations were created
        assert Recommendation.objects.filter(report=test_report_with_csv).count() > 0

    def test_process_csv_already_processing(self, authenticated_api_client, test_report_processing):
        """Test processing fails if report is already processing."""
        response = authenticated_api_client.post(
            f'/api/v1/reports/{test_report_processing.id}/process/'
        )

        assert response.status_code == 400
        assert 'cannot be processed' in response.data['message']

    def test_process_csv_already_completed(self, authenticated_api_client, test_report_completed):
        """Test processing fails if report is already completed."""
        response = authenticated_api_client.post(
            f'/api/v1/reports/{test_report_completed.id}/process/'
        )

        assert response.status_code == 400

    def test_process_csv_no_file_uploaded(self, authenticated_api_client, test_report):
        """Test processing fails when no CSV file is uploaded."""
        test_report.status = 'uploaded'
        test_report.csv_file = None
        test_report.save()

        response = authenticated_api_client.post(
            f'/api/v1/reports/{test_report.id}/process/'
        )

        assert response.status_code == 400
        assert 'No CSV file' in response.data['message']

    def test_process_csv_invalid_report_id(self, authenticated_api_client):
        """Test processing fails with invalid report ID."""
        response = authenticated_api_client.post(
            '/api/v1/reports/00000000-0000-0000-0000-000000000000/process/'
        )

        assert response.status_code == 404


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestReportViewSetGenerate:
    """Test report generation endpoint POST /api/v1/reports/{id}/generate/"""

    def test_generate_report_both_formats(self, authenticated_api_client, test_report_completed, test_recommendations):
        """Test generating both HTML and PDF report formats."""
        response = authenticated_api_client.post(
            f'/api/v1/reports/{test_report_completed.id}/generate/',
            {'format': 'both'}
        )

        assert response.status_code == 200
        assert response.data['status'] == 'success'
        assert 'HTML' in response.data['data']['files_generated']
        assert 'PDF' in response.data['data']['files_generated']
        assert response.data['data']['html_url'] is not None
        assert response.data['data']['pdf_url'] is not None

        # Verify files were created
        test_report_completed.refresh_from_db()
        assert test_report_completed.html_file is not None
        assert test_report_completed.pdf_file is not None

    def test_generate_report_html_only(self, authenticated_api_client, test_report_completed, test_recommendations):
        """Test generating HTML report only."""
        response = authenticated_api_client.post(
            f'/api/v1/reports/{test_report_completed.id}/generate/',
            {'format': 'html'}
        )

        assert response.status_code == 200
        assert 'HTML' in response.data['data']['files_generated']
        assert 'PDF' not in response.data['data']['files_generated']

    def test_generate_report_pdf_only(self, authenticated_api_client, test_report_completed, test_recommendations):
        """Test generating PDF report only."""
        response = authenticated_api_client.post(
            f'/api/v1/reports/{test_report_completed.id}/generate/',
            {'format': 'pdf'}
        )

        assert response.status_code == 200
        assert 'PDF' in response.data['data']['files_generated']
        assert 'HTML' not in response.data['data']['files_generated']

    def test_generate_report_invalid_format(self, authenticated_api_client, test_report_completed, test_recommendations):
        """Test generation fails with invalid format."""
        response = authenticated_api_client.post(
            f'/api/v1/reports/{test_report_completed.id}/generate/',
            {'format': 'invalid'}
        )

        assert response.status_code == 400
        assert 'Invalid format' in response.data['message']

    def test_generate_report_not_completed(self, authenticated_api_client, test_report):
        """Test generation fails if report is not completed."""
        response = authenticated_api_client.post(
            f'/api/v1/reports/{test_report.id}/generate/',
            {'format': 'both'}
        )

        assert response.status_code == 400
        assert 'must be completed' in response.data['message']

    def test_generate_report_no_recommendations(self, authenticated_api_client, test_report_completed):
        """Test generation fails if report has no recommendations."""
        # Delete all recommendations
        from apps.reports.models import Recommendation
        Recommendation.objects.filter(report=test_report_completed).delete()

        response = authenticated_api_client.post(
            f'/api/v1/reports/{test_report_completed.id}/generate/',
            {'format': 'both'}
        )

        assert response.status_code == 400
        assert 'no recommendations' in response.data['message']


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestReportViewSetDownload:
    """Test report download endpoints GET /api/v1/reports/{id}/download/{format}/"""

    def test_download_html_report(self, authenticated_api_client, test_report_completed, tmp_path):
        """Test downloading HTML report file."""
        # Create a mock HTML file
        html_content = "<html><body><h1>Test Report</h1></body></html>"
        html_file_path = tmp_path / "report.html"
        html_file_path.write_text(html_content)

        test_report_completed.html_file = str(html_file_path)
        test_report_completed.save()

        response = authenticated_api_client.get(
            f'/api/v1/reports/{test_report_completed.id}/download/html/'
        )

        assert response.status_code == 200
        assert response['Content-Type'] == 'text/html; charset=utf-8'
        assert 'attachment' in response['Content-Disposition']

    def test_download_pdf_report(self, authenticated_api_client, test_report_completed, tmp_path):
        """Test downloading PDF report file."""
        # Create a mock PDF file
        pdf_content = b"%PDF-1.4 mock content"
        pdf_file_path = tmp_path / "report.pdf"
        pdf_file_path.write_bytes(pdf_content)

        test_report_completed.pdf_file = str(pdf_file_path)
        test_report_completed.save()

        response = authenticated_api_client.get(
            f'/api/v1/reports/{test_report_completed.id}/download/pdf/'
        )

        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'
        assert 'attachment' in response['Content-Disposition']

    def test_download_file_not_generated(self, authenticated_api_client, test_report_completed):
        """Test download fails when file hasn't been generated."""
        test_report_completed.html_file = None
        test_report_completed.save()

        response = authenticated_api_client.get(
            f'/api/v1/reports/{test_report_completed.id}/download/html/'
        )

        assert response.status_code == 404
        assert 'not been generated' in response.data['message']

    def test_download_file_missing_on_disk(self, authenticated_api_client, test_report_completed):
        """Test download fails when file exists in DB but not on disk."""
        test_report_completed.html_file = '/nonexistent/path/report.html'
        test_report_completed.save()

        response = authenticated_api_client.get(
            f'/api/v1/reports/{test_report_completed.id}/download/html/'
        )

        assert response.status_code == 404
        assert 'not found on server' in response.data['message']


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestReportViewSetStatistics:
    """Test statistics endpoint GET /api/v1/reports/{id}/statistics/"""

    def test_get_statistics_success(self, authenticated_api_client, test_report_completed):
        """Test retrieving statistics for completed report."""
        response = authenticated_api_client.get(
            f'/api/v1/reports/{test_report_completed.id}/statistics/'
        )

        assert response.status_code == 200
        assert response.data['status'] == 'success'
        assert 'total_recommendations' in response.data['data']
        assert 'category_distribution' in response.data['data']
        assert 'business_impact_distribution' in response.data['data']

    def test_get_statistics_not_completed(self, authenticated_api_client, test_report):
        """Test statistics fails for non-completed report."""
        response = authenticated_api_client.get(
            f'/api/v1/reports/{test_report.id}/statistics/'
        )

        assert response.status_code == 400
        assert 'not completed' in response.data['message']


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestReportViewSetRecommendations:
    """Test recommendations endpoint GET /api/v1/reports/{id}/recommendations/"""

    def test_get_recommendations_success(self, authenticated_api_client, test_report, test_recommendations):
        """Test retrieving all recommendations for a report."""
        response = authenticated_api_client.get(
            f'/api/v1/reports/{test_report.id}/recommendations/'
        )

        assert response.status_code == 200
        assert response.data['status'] == 'success'
        assert response.data['count'] == 20
        assert len(response.data['data']) == 20

    def test_get_recommendations_filter_by_category(self, authenticated_api_client, test_report, test_recommendations):
        """Test filtering recommendations by category."""
        response = authenticated_api_client.get(
            f'/api/v1/reports/{test_report.id}/recommendations/?category=cost'
        )

        assert response.status_code == 200
        assert response.data['count'] == 4  # 20 recommendations, 5 categories = 4 per category
        for rec in response.data['data']:
            assert rec['category'] == 'cost'

    def test_get_recommendations_filter_by_impact(self, authenticated_api_client, test_report, test_recommendations):
        """Test filtering recommendations by business impact."""
        response = authenticated_api_client.get(
            f'/api/v1/reports/{test_report.id}/recommendations/?business_impact=high'
        )

        assert response.status_code == 200
        for rec in response.data['data']:
            assert rec['business_impact'] == 'high'

    def test_get_recommendations_filter_by_min_savings(self, authenticated_api_client, test_report, test_recommendations):
        """Test filtering recommendations by minimum savings."""
        response = authenticated_api_client.get(
            f'/api/v1/reports/{test_report.id}/recommendations/?min_savings=1000'
        )

        assert response.status_code == 200
        for rec in response.data['data']:
            # Check that potential_savings >= 1000
            assert float(rec['potential_savings']) >= 1000.0

    def test_get_recommendations_empty_result(self, authenticated_api_client, test_report):
        """Test recommendations endpoint with no recommendations."""
        response = authenticated_api_client.get(
            f'/api/v1/reports/{test_report.id}/recommendations/'
        )

        assert response.status_code == 200
        assert response.data['count'] == 0
        assert len(response.data['data']) == 0


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestReportViewSetCRUD:
    """Test standard CRUD operations for Report ViewSet"""

    def test_list_reports(self, authenticated_api_client, test_report, test_report_completed):
        """Test listing all reports."""
        response = authenticated_api_client.get('/api/v1/reports/')

        assert response.status_code == 200
        assert len(response.data['results']) >= 2

    def test_retrieve_report(self, authenticated_api_client, test_report):
        """Test retrieving a single report."""
        response = authenticated_api_client.get(f'/api/v1/reports/{test_report.id}/')

        assert response.status_code == 200
        assert response.data['id'] == str(test_report.id)
        assert response.data['title'] == test_report.title

    def test_filter_reports_by_client(self, authenticated_api_client, test_report, test_client):
        """Test filtering reports by client."""
        response = authenticated_api_client.get(
            f'/api/v1/reports/?client={test_client.id}'
        )

        assert response.status_code == 200
        for report in response.data['results']:
            assert report['client']['id'] == str(test_client.id)

    def test_filter_reports_by_type(self, authenticated_api_client, test_report_cost):
        """Test filtering reports by type."""
        response = authenticated_api_client.get('/api/v1/reports/?report_type=cost')

        assert response.status_code == 200
        for report in response.data['results']:
            assert report['report_type'] == 'cost'

    def test_filter_reports_by_status(self, authenticated_api_client, test_report_completed):
        """Test filtering reports by status."""
        response = authenticated_api_client.get('/api/v1/reports/?status=completed')

        assert response.status_code == 200
        for report in response.data['results']:
            assert report['status'] == 'completed'

    def test_search_reports(self, authenticated_api_client, test_report):
        """Test searching reports by title."""
        response = authenticated_api_client.get('/api/v1/reports/?search=Test')

        assert response.status_code == 200
        assert len(response.data['results']) > 0

    def test_delete_report(self, authenticated_api_client, test_report):
        """Test deleting a report."""
        from apps.reports.models import Report

        report_id = test_report.id

        response = authenticated_api_client.delete(f'/api/v1/reports/{report_id}/')

        assert response.status_code == 204
        assert not Report.objects.filter(id=report_id).exists()


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestReportViewSetPermissions:
    """Test permission requirements for Report ViewSet"""

    def test_unauthenticated_access_denied(self, api_client):
        """Test that unauthenticated users cannot access reports."""
        response = api_client.get('/api/v1/reports/')
        assert response.status_code == 401

    def test_authenticated_access_granted(self, authenticated_api_client):
        """Test that authenticated users can access reports."""
        response = authenticated_api_client.get('/api/v1/reports/')
        assert response.status_code == 200


# ============================================================================
# Tests for RecommendationViewSet
# ============================================================================

@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestRecommendationViewSet:
    """Test RecommendationViewSet read-only operations"""

    def test_list_recommendations(self, authenticated_api_client, test_report, test_recommendations):
        """Test listing all recommendations."""
        response = authenticated_api_client.get('/api/v1/recommendations/')

        assert response.status_code == 200
        assert len(response.data['results']) >= 20

    def test_retrieve_recommendation(self, authenticated_api_client, test_recommendation):
        """Test retrieving a single recommendation."""
        response = authenticated_api_client.get(f'/api/v1/recommendations/{test_recommendation.id}/')

        assert response.status_code == 200
        assert response.data['id'] == str(test_recommendation.id)
        assert response.data['category'] == test_recommendation.category

    def test_filter_by_report(self, authenticated_api_client, test_report, test_recommendations):
        """Test filtering recommendations by report."""
        response = authenticated_api_client.get(
            f'/api/v1/recommendations/?report={test_report.id}'
        )

        assert response.status_code == 200
        for rec in response.data['results']:
            assert rec['report'] == str(test_report.id)

    def test_filter_by_category(self, authenticated_api_client, test_report, test_recommendations):
        """Test filtering recommendations by category."""
        response = authenticated_api_client.get('/api/v1/recommendations/?category=cost')

        assert response.status_code == 200
        for rec in response.data['results']:
            assert rec['category'] == 'cost'

    def test_filter_by_business_impact(self, authenticated_api_client, test_report, test_recommendations):
        """Test filtering recommendations by business impact."""
        response = authenticated_api_client.get('/api/v1/recommendations/?business_impact=high')

        assert response.status_code == 200
        for rec in response.data['results']:
            assert rec['business_impact'] == 'high'

    def test_search_recommendations(self, authenticated_api_client, test_report, test_recommendations):
        """Test searching recommendations by text."""
        response = authenticated_api_client.get('/api/v1/recommendations/?search=Optimize')

        assert response.status_code == 200
        assert len(response.data['results']) > 0

    def test_order_by_savings(self, authenticated_api_client, test_report, test_recommendations):
        """Test ordering recommendations by potential savings."""
        response = authenticated_api_client.get('/api/v1/recommendations/?ordering=-potential_savings')

        assert response.status_code == 200
        assert len(response.data['results']) > 0

        # Verify descending order
        results = response.data['results']
        for i in range(len(results) - 1):
            assert float(results[i]['potential_savings']) >= float(results[i + 1]['potential_savings'])

    def test_unauthenticated_access_denied(self, api_client):
        """Test that unauthenticated users cannot access recommendations."""
        response = api_client.get('/api/v1/recommendations/')
        assert response.status_code == 401


# ============================================================================
# Tests for ReportTemplateViewSet
# ============================================================================

@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestReportTemplateViewSet:
    """Test ReportTemplateViewSet CRUD operations"""

    def test_list_templates(self, authenticated_api_client):
        """Test listing all report templates."""
        response = authenticated_api_client.get('/api/v1/report-templates/')

        assert response.status_code == 200

    def test_create_template(self, authenticated_api_client):
        """Test creating a new report template."""
        data = {
            'name': 'Custom Detailed Report',
            'report_type': 'detailed',
            'html_template': '<html><body>{{ content }}</body></html>',
            'is_default': False,
            'is_active': True
        }

        response = authenticated_api_client.post('/api/v1/report-templates/', data)

        assert response.status_code == 201
        assert response.data['name'] == 'Custom Detailed Report'
        assert response.data['report_type'] == 'detailed'

    def test_retrieve_template(self, authenticated_api_client, test_report_template):
        """Test retrieving a single report template."""
        response = authenticated_api_client.get(f'/api/v1/report-templates/{test_report_template.id}/')

        assert response.status_code == 200
        assert response.data['id'] == str(test_report_template.id)

    def test_update_template(self, authenticated_api_client, test_report_template):
        """Test updating a report template."""
        data = {
            'name': 'Updated Template Name',
            'is_active': False
        }

        response = authenticated_api_client.patch(
            f'/api/v1/report-templates/{test_report_template.id}/',
            data
        )

        assert response.status_code == 200
        assert response.data['name'] == 'Updated Template Name'
        assert response.data['is_active'] is False

    def test_delete_template(self, authenticated_api_client, test_report_template):
        """Test deleting a report template."""
        from apps.reports.models import ReportTemplate

        template_id = test_report_template.id

        response = authenticated_api_client.delete(
            f'/api/v1/report-templates/{template_id}/'
        )

        assert response.status_code == 204
        assert not ReportTemplate.objects.filter(id=template_id).exists()

    def test_filter_by_report_type(self, authenticated_api_client, test_report_template):
        """Test filtering templates by report type."""
        response = authenticated_api_client.get(
            f'/api/v1/report-templates/?report_type={test_report_template.report_type}'
        )

        assert response.status_code == 200
        for template in response.data['results']:
            assert template['report_type'] == test_report_template.report_type

    def test_filter_by_is_default(self, authenticated_api_client):
        """Test filtering templates by is_default flag."""
        response = authenticated_api_client.get('/api/v1/report-templates/?is_default=true')

        assert response.status_code == 200
        for template in response.data['results']:
            assert template['is_default'] is True

    def test_unauthenticated_access_denied(self, api_client):
        """Test that unauthenticated users cannot access templates."""
        response = api_client.get('/api/v1/report-templates/')
        assert response.status_code == 401


# ============================================================================
# Tests for ReportShareViewSet
# ============================================================================

@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestReportShareViewSet:
    """Test ReportShareViewSet CRUD operations"""

    def test_create_share(self, authenticated_api_client, test_report_completed, test_user):
        """Test creating a new report share."""
        from datetime import datetime, timedelta

        expires_at = (datetime.now() + timedelta(days=7)).isoformat()

        data = {
            'report': str(test_report_completed.id),
            'shared_with_email': 'recipient@example.com',
            'permission_level': 'view',
            'expires_at': expires_at,
            'is_active': True
        }

        response = authenticated_api_client.post('/api/v1/report-shares/', data)

        assert response.status_code == 201
        assert response.data['shared_with_email'] == 'recipient@example.com'
        assert response.data['permission_level'] == 'view'
        assert response.data['is_active'] is True

    def test_list_shares(self, authenticated_api_client, test_report_share):
        """Test listing all report shares (user only sees their own)."""
        response = authenticated_api_client.get('/api/v1/report-shares/')

        assert response.status_code == 200
        # All shares should be created by the authenticated user
        for share in response.data['results']:
            assert share['shared_by'] == str(test_report_share.shared_by.id)

    def test_retrieve_share(self, authenticated_api_client, test_report_share):
        """Test retrieving a single report share."""
        response = authenticated_api_client.get(f'/api/v1/report-shares/{test_report_share.id}/')

        assert response.status_code == 200
        assert response.data['id'] == str(test_report_share.id)

    def test_update_share(self, authenticated_api_client, test_report_share):
        """Test updating a report share."""
        data = {
            'permission_level': 'download',
            'is_active': False
        }

        response = authenticated_api_client.patch(
            f'/api/v1/report-shares/{test_report_share.id}/',
            data
        )

        assert response.status_code == 200
        assert response.data['permission_level'] == 'download'
        assert response.data['is_active'] is False

    def test_delete_share(self, authenticated_api_client, test_report_share):
        """Test deleting a report share."""
        from apps.reports.models import ReportShare

        share_id = test_report_share.id

        response = authenticated_api_client.delete(f'/api/v1/report-shares/{share_id}/')

        assert response.status_code == 204
        assert not ReportShare.objects.filter(id=share_id).exists()

    def test_filter_by_report(self, authenticated_api_client, test_report_share):
        """Test filtering shares by report."""
        response = authenticated_api_client.get(
            f'/api/v1/report-shares/?report={test_report_share.report.id}'
        )

        assert response.status_code == 200
        for share in response.data['results']:
            assert share['report'] == str(test_report_share.report.id)

    def test_filter_by_permission_level(self, authenticated_api_client, test_report_share):
        """Test filtering shares by permission level."""
        response = authenticated_api_client.get(
            f'/api/v1/report-shares/?permission_level={test_report_share.permission_level}'
        )

        assert response.status_code == 200
        for share in response.data['results']:
            assert share['permission_level'] == test_report_share.permission_level

    def test_unauthenticated_access_denied(self, api_client):
        """Test that unauthenticated users cannot access shares."""
        response = api_client.get('/api/v1/report-shares/')
        assert response.status_code == 401
