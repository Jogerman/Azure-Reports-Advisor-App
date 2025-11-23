"""
Tests for manual recommendations input feature (v1.7.0).

Tests the functionality of manually adding recommendations to reports,
including validation, serialization, and API endpoints.
"""

import json
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.clients.models import Client
from apps.reports.models import Report, Recommendation
from apps.reports.serializers import (
    ManualRecommendationInputSerializer,
    BulkManualRecommendationSerializer,
)

User = get_user_model()


class TestManualRecommendationInputSerializer(TestCase):
    """Test manual recommendation input serializer."""

    def test_valid_minimal_recommendation(self):
        """Should accept recommendation with only required fields."""
        data = {
            'category': 'cost',
            'business_impact': 'high',
            'recommendation': 'Implement auto-shutdown for dev VMs',
        }

        serializer = ManualRecommendationInputSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_valid_complete_recommendation(self):
        """Should accept recommendation with all fields."""
        data = {
            'category': 'cost',
            'business_impact': 'high',
            'recommendation': 'Implement auto-shutdown for dev VMs',
            'subscription_id': 'sub-123',
            'subscription_name': 'Dev Subscription',
            'resource_group': 'rg-dev',
            'resource_name': 'vm-dev-01',
            'resource_type': 'Microsoft.Compute/virtualMachines',
            'potential_savings': 1200.00,
            'currency': 'USD',
            'potential_benefits': 'Reduce costs by shutting down VMs',
            'advisor_score_impact': 5.0,
        }

        serializer = ManualRecommendationInputSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['potential_savings'], Decimal('1200.00'))

    def test_missing_required_fields(self):
        """Should reject recommendation missing required fields."""
        data = {
            'category': 'cost',
            # Missing business_impact and recommendation
        }

        serializer = ManualRecommendationInputSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('business_impact', serializer.errors)
        self.assertIn('recommendation', serializer.errors)

    def test_invalid_category(self):
        """Should reject invalid category."""
        data = {
            'category': 'invalid_category',
            'business_impact': 'high',
            'recommendation': 'Test',
        }

        serializer = ManualRecommendationInputSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('category', serializer.errors)

    def test_negative_potential_savings(self):
        """Should reject negative potential savings."""
        data = {
            'category': 'cost',
            'business_impact': 'high',
            'recommendation': 'Test',
            'potential_savings': -100.00,
        }

        serializer = ManualRecommendationInputSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('potential_savings', serializer.errors)

    def test_invalid_advisor_score_impact(self):
        """Should reject advisor score impact outside 0-100 range."""
        data = {
            'category': 'cost',
            'business_impact': 'high',
            'recommendation': 'Test',
            'advisor_score_impact': 150.0,
        }

        serializer = ManualRecommendationInputSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('advisor_score_impact', serializer.errors)


class TestBulkManualRecommendationSerializer(TestCase):
    """Test bulk manual recommendation serializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client_obj = Client.objects.create(
            company_name='Test Company',
            contact_email='client@test.com',
            created_by=self.user
        )
        self.report = Report.objects.create(
            client=self.client_obj,
            created_by=self.user,
            report_type='detailed',
            title='Test Report',
            status='completed'
        )

    def test_create_single_manual_recommendation(self):
        """Should create single manual recommendation."""
        data = {
            'recommendations': [
                {
                    'category': 'cost',
                    'business_impact': 'high',
                    'recommendation': 'Implement auto-shutdown for dev VMs',
                    'potential_savings': 1200.00,
                }
            ]
        }

        serializer = BulkManualRecommendationSerializer(
            data=data,
            context={'report': self.report}
        )

        self.assertTrue(serializer.is_valid())
        recommendations = serializer.save()

        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0].report, self.report)
        self.assertEqual(recommendations[0].category, 'cost')
        self.assertEqual(recommendations[0].csv_row_number, -1)  # Marked as manual

    def test_create_multiple_manual_recommendations(self):
        """Should create multiple manual recommendations."""
        data = {
            'recommendations': [
                {
                    'category': 'cost',
                    'business_impact': 'high',
                    'recommendation': 'Shutdown dev VMs',
                    'potential_savings': 1200.00,
                },
                {
                    'category': 'security',
                    'business_impact': 'high',
                    'recommendation': 'Enable MFA',
                    'potential_savings': 0,
                },
                {
                    'category': 'performance',
                    'business_impact': 'medium',
                    'recommendation': 'Upgrade database tier',
                    'potential_savings': 500.00,
                },
            ]
        }

        serializer = BulkManualRecommendationSerializer(
            data=data,
            context={'report': self.report}
        )

        self.assertTrue(serializer.is_valid())
        recommendations = serializer.save()

        self.assertEqual(len(recommendations), 3)
        self.assertEqual(Recommendation.objects.filter(report=self.report).count(), 3)

    def test_reservation_analysis_integration(self):
        """Should analyze recommendations for reservations."""
        data = {
            'recommendations': [
                {
                    'category': 'cost',
                    'business_impact': 'high',
                    'recommendation': 'Use Azure Reserved VM Instances for production workloads',
                    'potential_benefits': 'Save up to 72% with 3-year commitment',
                    'potential_savings': 5000.00,
                }
            ]
        }

        serializer = BulkManualRecommendationSerializer(
            data=data,
            context={'report': self.report}
        )

        self.assertTrue(serializer.is_valid())
        recommendations = serializer.save()

        # Should be detected as reservation
        self.assertTrue(recommendations[0].is_reservation_recommendation)
        self.assertEqual(recommendations[0].reservation_type, 'reserved_instance')
        self.assertEqual(recommendations[0].commitment_term_years, 3)

    def test_empty_recommendations_list(self):
        """Should reject empty recommendations list."""
        data = {'recommendations': []}

        serializer = BulkManualRecommendationSerializer(
            data=data,
            context={'report': self.report}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('recommendations', serializer.errors)

    def test_too_many_recommendations(self):
        """Should reject more than 100 recommendations."""
        data = {
            'recommendations': [
                {
                    'category': 'cost',
                    'business_impact': 'low',
                    'recommendation': f'Recommendation {i}',
                }
                for i in range(101)
            ]
        }

        serializer = BulkManualRecommendationSerializer(
            data=data,
            context={'report': self.report}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('recommendations', serializer.errors)


class TestManualRecommendationsAPI(TestCase):
    """Test manual recommendations API endpoint."""

    def setUp(self):
        """Set up test fixtures."""
        self.client_api = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client_obj = Client.objects.create(
            company_name='Test Company',
            contact_email='client@test.com',
            created_by=self.user
        )
        self.report = Report.objects.create(
            client=self.client_obj,
            created_by=self.user,
            report_type='detailed',
            title='Test Report',
            status='completed'
        )

        # Authenticate
        self.client_api.force_authenticate(user=self.user)

    def test_add_manual_recommendations_success(self):
        """Should successfully add manual recommendations via API."""
        url = f'/api/v1/reports/{self.report.id}/add-manual-recommendations/'
        data = {
            'recommendations': [
                {
                    'category': 'cost',
                    'business_impact': 'high',
                    'recommendation': 'Implement auto-shutdown for dev VMs',
                    'potential_savings': 1200.00,
                    'currency': 'USD',
                }
            ]
        }

        response = self.client_api.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['recommendations_created'], 1)
        self.assertEqual(response.data['data']['total_recommendations'], 1)

        # Verify in database
        self.assertEqual(Recommendation.objects.filter(report=self.report).count(), 1)

    def test_add_manual_recommendations_to_invalid_status_report(self):
        """Should reject adding to failed report."""
        self.report.status = 'failed'
        self.report.save()

        url = f'/api/v1/reports/{self.report.id}/add-manual-recommendations/'
        data = {
            'recommendations': [
                {
                    'category': 'cost',
                    'business_impact': 'high',
                    'recommendation': 'Test',
                }
            ]
        }

        response = self.client_api.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot add manual recommendations', response.data['message'])

    def test_add_manual_recommendations_unauthenticated(self):
        """Should reject unauthenticated requests."""
        self.client_api.force_authenticate(user=None)

        url = f'/api/v1/reports/{self.report.id}/add-manual-recommendations/'
        data = {
            'recommendations': [
                {
                    'category': 'cost',
                    'business_impact': 'high',
                    'recommendation': 'Test',
                }
            ]
        }

        response = self.client_api.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_manual_recommendations_validation_error(self):
        """Should return validation errors for invalid data."""
        url = f'/api/v1/reports/{self.report.id}/add-manual-recommendations/'
        data = {
            'recommendations': [
                {
                    'category': 'invalid_category',
                    'business_impact': 'high',
                    # Missing recommendation
                }
            ]
        }

        response = self.client_api.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        self.assertIn('errors', response.data)

    def test_add_multiple_manual_recommendations(self):
        """Should add multiple recommendations and update totals."""
        url = f'/api/v1/reports/{self.report.id}/add-manual-recommendations/'
        data = {
            'recommendations': [
                {
                    'category': 'cost',
                    'business_impact': 'high',
                    'recommendation': 'Shutdown dev VMs',
                    'potential_savings': 1200.00,
                },
                {
                    'category': 'security',
                    'business_impact': 'high',
                    'recommendation': 'Enable MFA',
                },
                {
                    'category': 'performance',
                    'business_impact': 'medium',
                    'recommendation': 'Upgrade database',
                    'potential_savings': 500.00,
                },
            ]
        }

        response = self.client_api.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['recommendations_created'], 3)
        self.assertEqual(response.data['data']['total_recommendations'], 3)
        self.assertEqual(response.data['data']['total_potential_savings'], 1700.00)


if __name__ == '__main__':
    import unittest
    unittest.main()
