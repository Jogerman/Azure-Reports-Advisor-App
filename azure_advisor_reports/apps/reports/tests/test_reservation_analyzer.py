"""
Tests for ReservationAnalyzer service.

Tests the functionality of detecting and analyzing Saving Plans and
Reserved Instances recommendations from Azure Advisor data.
"""

import unittest
from apps.reports.services.reservation_analyzer import ReservationAnalyzer


class TestReservationDetection(unittest.TestCase):
    """Test reservation recommendation detection."""

    def test_detects_reserved_instance_recommendation(self):
        """Should detect Reserved VM Instance recommendations."""
        text = "Consider using Azure Reserved VM Instances to save money"
        result = ReservationAnalyzer.is_reservation_recommendation(text)
        self.assertTrue(result)

    def test_detects_savings_plan_recommendation(self):
        """Should detect Savings Plan recommendations."""
        text = "Use Azure Savings Plan to reduce costs"
        result = ReservationAnalyzer.is_reservation_recommendation(text)
        self.assertTrue(result)

    def test_detects_reserved_capacity_recommendation(self):
        """Should detect Reserved Capacity recommendations."""
        text = "Purchase reserved capacity for Azure SQL Database"
        result = ReservationAnalyzer.is_reservation_recommendation(text)
        self.assertTrue(result)

    def test_detects_with_commit_keyword(self):
        """Should detect recommendations mentioning commitment."""
        text = "Commit to a one-year term for cost savings"
        result = ReservationAnalyzer.is_reservation_recommendation(text)
        self.assertTrue(result)

    def test_detects_with_reservation_keyword(self):
        """Should detect recommendations mentioning reservation."""
        text = "Purchase reservation for virtual machines"
        result = ReservationAnalyzer.is_reservation_recommendation(text)
        self.assertTrue(result)

    def test_does_not_detect_regular_recommendation(self):
        """Should not detect regular non-reservation recommendations."""
        text = "Right-size your virtual machines to reduce costs"
        result = ReservationAnalyzer.is_reservation_recommendation(text)
        self.assertFalse(result)

    def test_handles_empty_text(self):
        """Should handle empty text gracefully."""
        result = ReservationAnalyzer.is_reservation_recommendation("")
        self.assertFalse(result)

    def test_handles_none_text(self):
        """Should handle None text gracefully."""
        result = ReservationAnalyzer.is_reservation_recommendation(None)
        self.assertFalse(result)

    def test_case_insensitive_detection(self):
        """Should detect reservations regardless of case."""
        text = "CONSIDER USING RESERVED INSTANCES"
        result = ReservationAnalyzer.is_reservation_recommendation(text)
        self.assertTrue(result)

    def test_checks_both_recommendation_and_benefits(self):
        """Should check both recommendation and benefits text."""
        recommendation = "Optimize your virtual machines"
        benefits = "Consider reserved instances for long-term savings"
        result = ReservationAnalyzer.is_reservation_recommendation(
            recommendation, benefits
        )
        self.assertTrue(result)


class TestReservationType(unittest.TestCase):
    """Test reservation type extraction."""

    def test_extracts_reserved_instance_type(self):
        """Should extract 'reserved_instance' type."""
        text = "Use Azure Reserved VM Instances for savings"
        result = ReservationAnalyzer.extract_reservation_type(text)
        self.assertEqual(result, 'reserved_instance')

    def test_extracts_reserved_instance_from_abbreviation(self):
        """Should extract 'reserved_instance' from RI abbreviation."""
        text = "Purchase RI for virtual machines"
        result = ReservationAnalyzer.extract_reservation_type(text)
        self.assertEqual(result, 'reserved_instance')

    def test_extracts_savings_plan_type(self):
        """Should extract 'savings_plan' type."""
        text = "Azure Savings Plan offers flexible commitment"
        result = ReservationAnalyzer.extract_reservation_type(text)
        self.assertEqual(result, 'savings_plan')

    def test_extracts_reserved_capacity_type(self):
        """Should extract 'reserved_capacity' type."""
        text = "Purchase reserved capacity for Azure SQL"
        result = ReservationAnalyzer.extract_reservation_type(text)
        self.assertEqual(result, 'reserved_capacity')

    def test_extracts_database_reservation_as_capacity(self):
        """Should classify database reservations as 'reserved_capacity'."""
        text = "Database reservation for SQL Server"
        result = ReservationAnalyzer.extract_reservation_type(text)
        self.assertEqual(result, 'reserved_capacity')

    def test_returns_other_for_unclassified_reservation(self):
        """Should return 'other' for unclassified reservations."""
        text = "Purchase reservation for special service"
        # First, make it detect as reservation
        is_reservation = ReservationAnalyzer.is_reservation_recommendation(text)
        self.assertTrue(is_reservation)

        result = ReservationAnalyzer.extract_reservation_type(text)
        self.assertEqual(result, 'other')

    def test_returns_none_for_non_reservation(self):
        """Should return None for non-reservation text."""
        text = "Right-size your virtual machines"
        result = ReservationAnalyzer.extract_reservation_type(text)
        self.assertIsNone(result)

    def test_handles_empty_text(self):
        """Should handle empty text gracefully."""
        result = ReservationAnalyzer.extract_reservation_type("")
        self.assertIsNone(result)

    def test_handles_none_text(self):
        """Should handle None text gracefully."""
        result = ReservationAnalyzer.extract_reservation_type(None)
        self.assertIsNone(result)


class TestCommitmentTermExtraction(unittest.TestCase):
    """Test commitment term extraction."""

    def test_extracts_one_year_term(self):
        """Should extract 1-year commitment term."""
        text = "Commit to a one-year term for savings"
        result = ReservationAnalyzer.extract_commitment_term(text)
        self.assertEqual(result, 1)

    def test_extracts_one_year_from_number(self):
        """Should extract 1-year from numeric representation."""
        text = "Purchase a 1 year reservation"
        result = ReservationAnalyzer.extract_commitment_term(text)
        self.assertEqual(result, 1)

    def test_extracts_three_year_term(self):
        """Should extract 3-year commitment term."""
        text = "Commit to a three-year term for maximum savings"
        result = ReservationAnalyzer.extract_commitment_term(text)
        self.assertEqual(result, 3)

    def test_extracts_three_year_from_number(self):
        """Should extract 3-year from numeric representation."""
        text = "3 year commitment available"
        result = ReservationAnalyzer.extract_commitment_term(text)
        self.assertEqual(result, 3)

    def test_extracts_from_12_month_term(self):
        """Should extract 1-year from 12-month representation."""
        text = "12 month commitment"
        result = ReservationAnalyzer.extract_commitment_term(text)
        self.assertEqual(result, 1)

    def test_extracts_from_36_month_term(self):
        """Should extract 3-year from 36-month representation."""
        text = "36 month commitment"
        result = ReservationAnalyzer.extract_commitment_term(text)
        self.assertEqual(result, 3)

    def test_extracts_from_one_or_three_year_pattern(self):
        """Should extract term from 'one or three year' pattern (defaults to 3)."""
        text = "Reduce costs by committing to one or three year terms"
        result = ReservationAnalyzer.extract_commitment_term(text)
        self.assertEqual(result, 3)

    def test_prefers_three_year_when_both_mentioned(self):
        """Should prefer 3-year when both terms are mentioned."""
        text = "Available in 1 year or 3 year options"
        result = ReservationAnalyzer.extract_commitment_term(text)
        self.assertEqual(result, 3)

    def test_handles_hyphenated_terms(self):
        """Should handle hyphenated terms like '3-year'."""
        text = "Purchase a 3-year reservation"
        result = ReservationAnalyzer.extract_commitment_term(text)
        self.assertEqual(result, 3)

    def test_defaults_to_3_for_reservation_without_explicit_term(self):
        """Should default to 3 years for reservations without explicit term."""
        text = "Purchase Azure Reserved VM Instance"
        result = ReservationAnalyzer.extract_commitment_term(text)
        self.assertEqual(result, 3)

    def test_returns_none_for_non_reservation(self):
        """Should return None for non-reservation text."""
        text = "Resize your virtual machines"
        result = ReservationAnalyzer.extract_commitment_term(text)
        self.assertIsNone(result)

    def test_handles_empty_text(self):
        """Should handle empty text gracefully."""
        result = ReservationAnalyzer.extract_commitment_term("")
        self.assertIsNone(result)

    def test_handles_none_text(self):
        """Should handle None text gracefully."""
        result = ReservationAnalyzer.extract_commitment_term(None)
        self.assertIsNone(result)


class TestCompleteAnalysis(unittest.TestCase):
    """Test complete recommendation analysis."""

    def test_analyzes_reserved_instance_recommendation(self):
        """Should correctly analyze a Reserved Instance recommendation."""
        recommendation = "Consider using Azure Reserved VM Instances to save money"
        benefits = "Reduce virtual machine costs by committing to one or three-year terms"

        result = ReservationAnalyzer.analyze_recommendation(recommendation, benefits)

        self.assertTrue(result['is_reservation'])
        self.assertEqual(result['reservation_type'], 'reserved_instance')
        self.assertEqual(result['commitment_term_years'], 3)

    def test_analyzes_savings_plan_recommendation(self):
        """Should correctly analyze a Savings Plan recommendation."""
        recommendation = "Azure Savings Plan provides flexible compute savings"
        benefits = "Commit to 1 year for savings"

        result = ReservationAnalyzer.analyze_recommendation(recommendation, benefits)

        self.assertTrue(result['is_reservation'])
        self.assertEqual(result['reservation_type'], 'savings_plan')
        self.assertEqual(result['commitment_term_years'], 1)

    def test_analyzes_reserved_capacity_recommendation(self):
        """Should correctly analyze a Reserved Capacity recommendation."""
        recommendation = "Purchase reserved capacity for Azure SQL Database"
        benefits = "3-year commitment available"

        result = ReservationAnalyzer.analyze_recommendation(recommendation, benefits)

        self.assertTrue(result['is_reservation'])
        self.assertEqual(result['reservation_type'], 'reserved_capacity')
        self.assertEqual(result['commitment_term_years'], 3)

    def test_analyzes_non_reservation_recommendation(self):
        """Should correctly identify non-reservation recommendations."""
        recommendation = "Right-size your virtual machines"
        benefits = "Reduce costs by selecting appropriate VM sizes"

        result = ReservationAnalyzer.analyze_recommendation(recommendation, benefits)

        self.assertFalse(result['is_reservation'])
        self.assertIsNone(result['reservation_type'])
        self.assertIsNone(result['commitment_term_years'])

    def test_handles_real_world_azure_advisor_text(self):
        """Should handle real Azure Advisor CSV text."""
        recommendation = "Consider using Azure Reserved VM Instances to save money on virtual machines"
        benefits = "Reduce virtual machine costs by committing to one or three-year terms"

        result = ReservationAnalyzer.analyze_recommendation(recommendation, benefits)

        self.assertTrue(result['is_reservation'])
        self.assertEqual(result['reservation_type'], 'reserved_instance')
        self.assertIn(result['commitment_term_years'], [1, 3])


class TestCommitmentSavingsCalculations(unittest.TestCase):
    """Test commitment savings calculations."""

    def test_calculates_one_year_commitment_savings(self):
        """Should calculate total savings for 1-year commitment."""
        annual_savings = 1200.00
        commitment_years = 1

        result = ReservationAnalyzer.calculate_total_commitment_savings(
            annual_savings, commitment_years
        )

        self.assertEqual(result, 1200.00)

    def test_calculates_three_year_commitment_savings(self):
        """Should calculate total savings for 3-year commitment."""
        annual_savings = 2400.50
        commitment_years = 3

        result = ReservationAnalyzer.calculate_total_commitment_savings(
            annual_savings, commitment_years
        )

        self.assertEqual(result, 7201.50)

    def test_returns_annual_savings_when_no_term(self):
        """Should return annual savings when no commitment term."""
        annual_savings = 1500.00
        commitment_years = None

        result = ReservationAnalyzer.calculate_total_commitment_savings(
            annual_savings, commitment_years
        )

        self.assertEqual(result, 1500.00)

    def test_handles_zero_savings(self):
        """Should handle zero savings."""
        result = ReservationAnalyzer.calculate_total_commitment_savings(0, 3)
        self.assertEqual(result, 0)

    def test_handles_none_savings(self):
        """Should handle None savings."""
        result = ReservationAnalyzer.calculate_total_commitment_savings(None, 3)
        self.assertEqual(result, 0)


class TestReservationSummaryFormatting(unittest.TestCase):
    """Test reservation summary formatting."""

    def test_formats_reserved_instance_summary(self):
        """Should format Reserved Instance summary correctly."""
        result = ReservationAnalyzer.format_reservation_summary(
            'reserved_instance', 3, 2400.50, 'USD'
        )

        self.assertIn('Reserved VM Instance', result)
        self.assertIn('3-year', result)
        self.assertIn('2,400.50', result)
        self.assertIn('7,201.50', result)

    def test_formats_savings_plan_summary(self):
        """Should format Savings Plan summary correctly."""
        result = ReservationAnalyzer.format_reservation_summary(
            'savings_plan', 1, 1200.00, 'USD'
        )

        self.assertIn('Savings Plan', result)
        self.assertIn('1-year', result)
        self.assertIn('1,200.00', result)

    def test_formats_reserved_capacity_summary(self):
        """Should format Reserved Capacity summary correctly."""
        result = ReservationAnalyzer.format_reservation_summary(
            'reserved_capacity', 3, 3600.75, 'USD'
        )

        self.assertIn('Reserved Capacity', result)
        self.assertIn('3-year', result)
        self.assertIn('3,600.75', result)

    def test_formats_without_commitment_term(self):
        """Should format summary without commitment term."""
        result = ReservationAnalyzer.format_reservation_summary(
            'reserved_instance', None, 2400.00, 'USD'
        )

        self.assertIn('Reserved VM Instance', result)
        self.assertIn('2,400.00/year', result)
        self.assertNotIn('commitment', result)

    def test_formats_non_reservation_type(self):
        """Should format summary for non-specific reservation."""
        result = ReservationAnalyzer.format_reservation_summary(
            None, None, 1500.00, 'USD'
        )

        self.assertIn('1,500.00', result)
        self.assertIn('Annual savings', result)


if __name__ == '__main__':
    unittest.main()
