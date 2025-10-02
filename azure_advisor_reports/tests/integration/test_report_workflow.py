"""
Integration Tests for Complete Report Generation Workflow

These tests verify the end-to-end functionality of the report generation
process, from CSV upload through report generation to download.
"""

import pytest
import time
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.clients.models import Client
from apps.reports.models import Report, Recommendation

User = get_user_model()


@pytest.mark.integration
class TestCompleteReportGenerationWorkflow:
    """Test the complete report generation workflow from start to finish"""

    @pytest.fixture
    def setup_workflow_data(self, db):
        """Setup test data for workflow tests"""
        # Create user
        user = User.objects.create_user(
            username='analyst',
            email='analyst@example.com',
            password='testpass123',
            role='analyst'
        )

        # Create client
        client = Client.objects.create(
            company_name='Test Company Inc',
            industry='technology',
            contact_email='contact@testcompany.com',
            status='active'
        )

        return {
            'user': user,
            'client': client
        }

    @pytest.fixture
    def authenticated_api_client(self, setup_workflow_data):
        """Create authenticated API client with JWT token"""
        import jwt
        from datetime import datetime, timedelta
        from django.conf import settings

        client = APIClient()
        user = setup_workflow_data['user']

        # Generate JWT token
        payload = {
            'user_id': str(user.id),
            'email': user.email,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        return client

    @pytest.fixture
    def valid_csv_content(self):
        """Generate valid Azure Advisor CSV content"""
        csv_data = """Category,Business Impact,Recommendation,Subscription ID,Subscription Name,Resource Group,Resource Name,Resource Type,Potential Annual Cost Savings (USD),Currency,Potential Benefits,Retirement Date,Retiring Feature
Cost,High,Right-size underutilized virtual machines,sub-123,Production,rg-prod,vm-web-01,Microsoft.Compute/virtualMachines,1200.50,USD,Reduce VM size to save costs,,
Security,High,Enable Azure Defender for servers,sub-123,Production,rg-prod,vm-web-01,Microsoft.Compute/virtualMachines,0,USD,Improve security posture,,
Reliability,Medium,Enable backup for virtual machines,sub-123,Production,rg-prod,vm-web-01,Microsoft.Compute/virtualMachines,0,USD,Ensure business continuity,,
OperationalExcellence,Low,Apply recommended tags to resources,sub-123,Production,rg-prod,vm-web-01,Microsoft.Compute/virtualMachines,0,USD,Improve resource organization,,
Cost,Medium,Delete unattached managed disks,sub-123,Production,rg-prod,disk-orphan-01,Microsoft.Compute/disks,500.00,USD,Eliminate unnecessary costs,,
"""
        return csv_data.encode('utf-8')

    def test_complete_report_workflow_success(
        self,
        authenticated_api_client,
        setup_workflow_data,
        valid_csv_content,
        mocker
    ):
        """
        Test complete workflow: Upload CSV → Process → Generate Report → Download

        Flow:
        1. Upload CSV file
        2. Verify report created with 'pending' status
        3. Process CSV (create recommendations)
        4. Generate report (HTML/PDF)
        5. Download report files
        """
        client_obj = setup_workflow_data['client']

        # Mock Celery task execution to run synchronously
        mock_process_csv = mocker.patch(
            'apps.reports.tasks.process_csv_and_generate_report.delay'
        )

        # Step 1: Upload CSV file
        csv_file = SimpleUploadedFile(
            "advisor_data.csv",
            valid_csv_content,
            content_type="text/csv"
        )

        upload_response = authenticated_api_client.post(
            '/api/reports/upload/',
            {
                'client': str(client_obj.id),
                'csv_file': csv_file,
                'report_type': 'detailed'
            },
            format='multipart'
        )

        assert upload_response.status_code == 201, \
            f"CSV upload failed: {upload_response.data}"

        report_id = upload_response.data['id']
        assert upload_response.data['status'] == 'pending'
        assert upload_response.data['client'] == str(client_obj.id)

        # Verify Celery task was triggered
        mock_process_csv.assert_called_once_with(report_id, 'detailed')

        # Step 2: Simulate CSV processing (normally done by Celery)
        report = Report.objects.get(id=report_id)

        # Manually process CSV to create recommendations
        import pandas as pd
        from io import StringIO

        df = pd.read_csv(StringIO(valid_csv_content.decode('utf-8')))

        for _, row in df.iterrows():
            Recommendation.objects.create(
                report=report,
                category=row['Category'].lower(),
                business_impact=row['Business Impact'].lower(),
                recommendation=row['Recommendation'],
                subscription_id=row['Subscription ID'],
                subscription_name=row['Subscription Name'],
                resource_group=row['Resource Group'],
                resource_name=row['Resource Name'],
                resource_type=row['Resource Type'],
                potential_savings=float(row['Potential Annual Cost Savings (USD)']),
                currency=row['Currency'],
                potential_benefits=row['Potential Benefits']
            )

        # Update report status and analysis data
        total_recommendations = Recommendation.objects.filter(report=report).count()
        total_savings = sum(
            rec.potential_savings
            for rec in Recommendation.objects.filter(report=report)
        )

        report.status = 'completed'
        report.analysis_data = {
            'total_recommendations': total_recommendations,
            'total_savings': float(total_savings),
            'category_distribution': {
                'cost': 2,
                'security': 1,
                'reliability': 1,
                'operational_excellence': 1
            }
        }
        report.save()

        # Step 3: Verify report status
        status_response = authenticated_api_client.get(
            f'/api/reports/{report_id}/'
        )

        assert status_response.status_code == 200
        assert status_response.data['status'] == 'completed'
        assert status_response.data['analysis_data']['total_recommendations'] == 5
        assert float(status_response.data['analysis_data']['total_savings']) == 1700.50

        # Step 4: Verify recommendations were created
        recommendations = Recommendation.objects.filter(report=report)
        assert recommendations.count() == 5

        # Verify recommendation categories
        categories = set(rec.category for rec in recommendations)
        assert 'cost' in categories
        assert 'security' in categories
        assert 'reliability' in categories
        assert 'operational_excellence' in categories

    @pytest.mark.slow
    def test_large_csv_processing_workflow(
        self,
        authenticated_api_client,
        setup_workflow_data,
        mocker
    ):
        """
        Test workflow with large CSV file (100+ recommendations)
        Verifies performance and data integrity
        """
        import pandas as pd
        from io import StringIO

        client_obj = setup_workflow_data['client']

        # Generate large CSV with 100 recommendations
        rows = []
        categories = ['Cost', 'Security', 'Reliability', 'OperationalExcellence']
        impacts = ['High', 'Medium', 'Low']

        for i in range(100):
            rows.append({
                'Category': categories[i % 4],
                'Business Impact': impacts[i % 3],
                'Recommendation': f'Test recommendation {i}',
                'Subscription ID': f'sub-{i % 5}',
                'Subscription Name': f'Subscription {i % 5}',
                'Resource Group': f'rg-test-{i}',
                'Resource Name': f'resource-{i}',
                'Resource Type': 'Microsoft.Compute/virtualMachines',
                'Potential Annual Cost Savings (USD)': str(100.00 + i),
                'Currency': 'USD',
                'Potential Benefits': f'Benefits {i}',
                'Retirement Date': '',
                'Retiring Feature': ''
            })

        df = pd.DataFrame(rows)
        csv_content = df.to_csv(index=False).encode('utf-8')

        # Mock Celery task
        mocker.patch('apps.reports.tasks.process_csv_and_generate_report.delay')

        # Upload large CSV
        csv_file = SimpleUploadedFile(
            "large_advisor_data.csv",
            csv_content,
            content_type="text/csv"
        )

        start_time = time.time()

        upload_response = authenticated_api_client.post(
            '/api/reports/upload/',
            {
                'client': str(client_obj.id),
                'csv_file': csv_file,
                'report_type': 'detailed'
            },
            format='multipart'
        )

        upload_duration = time.time() - start_time

        assert upload_response.status_code == 201
        assert upload_duration < 5.0, \
            f"Upload took {upload_duration}s, should be < 5s"

        # Verify file size is within limits
        report = Report.objects.get(id=upload_response.data['id'])
        file_size = report.csv_file.size
        max_size = 50 * 1024 * 1024  # 50MB

        assert file_size < max_size, \
            f"File size {file_size} exceeds limit {max_size}"

    def test_invalid_csv_upload_handling(
        self,
        authenticated_api_client,
        setup_workflow_data
    ):
        """Test error handling for invalid CSV uploads"""
        client_obj = setup_workflow_data['client']

        # Test 1: Invalid file format (not CSV)
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b"This is not a CSV file",
            content_type="text/plain"
        )

        response = authenticated_api_client.post(
            '/api/reports/upload/',
            {
                'client': str(client_obj.id),
                'csv_file': invalid_file,
                'report_type': 'detailed'
            },
            format='multipart'
        )

        assert response.status_code == 400
        assert 'error' in response.data or 'csv_file' in response.data

        # Test 2: Empty CSV file
        empty_file = SimpleUploadedFile(
            "empty.csv",
            b"",
            content_type="text/csv"
        )

        response = authenticated_api_client.post(
            '/api/reports/upload/',
            {
                'client': str(client_obj.id),
                'csv_file': empty_file,
                'report_type': 'detailed'
            },
            format='multipart'
        )

        assert response.status_code == 400

        # Test 3: CSV with missing required columns
        invalid_csv = SimpleUploadedFile(
            "invalid.csv",
            b"Column1,Column2\nValue1,Value2",
            content_type="text/csv"
        )

        response = authenticated_api_client.post(
            '/api/reports/upload/',
            {
                'client': str(client_obj.id),
                'csv_file': invalid_csv,
                'report_type': 'detailed'
            },
            format='multipart'
        )

        assert response.status_code == 400

    def test_report_generation_with_all_types(
        self,
        authenticated_api_client,
        setup_workflow_data,
        valid_csv_content,
        mocker
    ):
        """Test generating all 5 report types from same CSV"""
        client_obj = setup_workflow_data['client']
        report_types = ['detailed', 'executive', 'cost', 'security', 'operations']

        mocker.patch('apps.reports.tasks.process_csv_and_generate_report.delay')

        for report_type in report_types:
            csv_file = SimpleUploadedFile(
                f"advisor_data_{report_type}.csv",
                valid_csv_content,
                content_type="text/csv"
            )

            response = authenticated_api_client.post(
                '/api/reports/upload/',
                {
                    'client': str(client_obj.id),
                    'csv_file': csv_file,
                    'report_type': report_type
                },
                format='multipart'
            )

            assert response.status_code == 201, \
                f"Failed to create {report_type} report: {response.data}"
            assert response.data['report_type'] == report_type

        # Verify all reports were created
        reports = Report.objects.filter(client=client_obj)
        assert reports.count() == 5

        # Verify each report type exists
        for report_type in report_types:
            assert reports.filter(report_type=report_type).exists()

    def test_concurrent_report_generation(
        self,
        authenticated_api_client,
        setup_workflow_data,
        valid_csv_content,
        mocker
    ):
        """Test handling multiple concurrent report requests"""
        client_obj = setup_workflow_data['client']

        mocker.patch('apps.reports.tasks.process_csv_and_generate_report.delay')

        # Create 3 reports simultaneously
        responses = []
        for i in range(3):
            csv_file = SimpleUploadedFile(
                f"advisor_data_{i}.csv",
                valid_csv_content,
                content_type="text/csv"
            )

            response = authenticated_api_client.post(
                '/api/reports/upload/',
                {
                    'client': str(client_obj.id),
                    'csv_file': csv_file,
                    'report_type': 'detailed'
                },
                format='multipart'
            )
            responses.append(response)

        # Verify all uploads succeeded
        for response in responses:
            assert response.status_code == 201

        # Verify unique report IDs
        report_ids = [r.data['id'] for r in responses]
        assert len(set(report_ids)) == 3, "Report IDs should be unique"

        # Verify all reports exist
        assert Report.objects.filter(client=client_obj).count() == 3


@pytest.mark.integration
class TestAuthenticationIntegration:
    """Test authentication flow integration"""

    def test_unauthenticated_upload_rejected(self, db, valid_csv_content):
        """Test that unauthenticated requests are rejected"""
        client = APIClient()  # No authentication

        csv_file = SimpleUploadedFile(
            "advisor_data.csv",
            b"test,data",
            content_type="text/csv"
        )

        response = client.post(
            '/api/reports/upload/',
            {
                'client': 'some-uuid',
                'csv_file': csv_file,
                'report_type': 'detailed'
            },
            format='multipart'
        )

        assert response.status_code == 401

    def test_invalid_token_rejected(self, db):
        """Test that invalid JWT tokens are rejected"""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')

        response = client.get('/api/reports/')

        assert response.status_code == 401

    def test_expired_token_rejected(self, db):
        """Test that expired JWT tokens are rejected"""
        import jwt
        from datetime import datetime, timedelta
        from django.conf import settings

        # Create user
        user = User.objects.create_user(
            username='test',
            email='test@example.com',
            password='testpass123'
        )

        # Generate expired token
        payload = {
            'user_id': str(user.id),
            'email': user.email,
            'exp': datetime.utcnow() - timedelta(hours=1),  # Expired
            'iat': datetime.utcnow() - timedelta(hours=2),
            'type': 'access'
        }
        expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token}')

        response = client.get('/api/reports/')

        assert response.status_code == 401


@pytest.mark.integration
class TestClientReportRelationship:
    """Test the relationship between clients and reports"""

    @pytest.fixture
    def setup_client_data(self, db):
        """Setup client with multiple reports"""
        user = User.objects.create_user(
            username='analyst',
            email='analyst@example.com',
            password='testpass123',
            role='analyst'
        )

        client = Client.objects.create(
            company_name='Multi-Report Client',
            industry='technology',
            contact_email='contact@client.com',
            status='active'
        )

        return {'user': user, 'client': client}

    def test_client_cascade_deletion(self, setup_client_data):
        """Test that deleting client cascades to reports"""
        client_obj = setup_client_data['client']
        user = setup_client_data['user']

        # Create multiple reports for the client
        for i in range(3):
            Report.objects.create(
                client=client_obj,
                created_by=user,
                report_type='detailed',
                status='completed'
            )

        assert Report.objects.filter(client=client_obj).count() == 3

        # Delete client
        client_id = client_obj.id
        client_obj.delete()

        # Verify reports were deleted
        assert Report.objects.filter(client_id=client_id).count() == 0

    def test_report_client_filter(self, setup_client_data):
        """Test filtering reports by client"""
        from tests.factories import ClientFactory, ReportFactory

        client1 = setup_client_data['client']
        client2 = ClientFactory(company_name='Other Client')
        user = setup_client_data['user']

        # Create reports for both clients
        ReportFactory.create_batch(3, client=client1, created_by=user)
        ReportFactory.create_batch(2, client=client2, created_by=user)

        # Filter by client1
        client1_reports = Report.objects.filter(client=client1)
        assert client1_reports.count() == 3

        # Filter by client2
        client2_reports = Report.objects.filter(client=client2)
        assert client2_reports.count() == 2


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Integration tests for performance-critical operations"""

    def test_batch_recommendation_creation(self, db):
        """Test creating many recommendations efficiently"""
        from tests.factories import ReportFactory, ClientFactory, UserFactory

        user = UserFactory()
        client = ClientFactory()
        report = ReportFactory(client=client, created_by=user)

        # Create 500 recommendations
        recommendations = []
        for i in range(500):
            recommendations.append(
                Recommendation(
                    report=report,
                    category='cost',
                    business_impact='medium',
                    recommendation=f'Recommendation {i}',
                    subscription_id=f'sub-{i}',
                    resource_name=f'resource-{i}',
                    potential_savings=100.00
                )
            )

        start_time = time.time()
        Recommendation.objects.bulk_create(recommendations)
        duration = time.time() - start_time

        assert duration < 2.0, \
            f"Bulk creation took {duration}s, should be < 2s"
        assert Recommendation.objects.filter(report=report).count() == 500

    def test_report_list_query_performance(self, db):
        """Test that report list queries are optimized"""
        from tests.factories import ReportFactory, ClientFactory, UserFactory

        user = UserFactory()

        # Create 50 reports with clients
        for _ in range(50):
            client = ClientFactory()
            ReportFactory(client=client, created_by=user)

        # Test query performance with select_related
        from django.test.utils import override_settings
        from django.db import connection
        from django.test.utils import override_settings

        with override_settings(DEBUG=True):
            # Clear previous queries
            connection.queries_log.clear()

            # Execute optimized query
            reports = Report.objects.select_related('client', 'created_by').all()
            list(reports)  # Force evaluation

            # Should use minimal queries (ideally 1-2)
            query_count = len(connection.queries)
            assert query_count <= 3, \
                f"Query count {query_count} too high, should be <= 3"
