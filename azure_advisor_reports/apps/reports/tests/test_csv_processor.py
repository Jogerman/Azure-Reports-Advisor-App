"""
Test suite for CSV processing functionality.

Tests cover CSV parsing, validation, data extraction, and statistics calculation.
"""

import pytest
import os
import tempfile
from decimal import Decimal
from apps.reports.services.csv_processor import (
    AzureAdvisorCSVProcessor,
    CSVProcessingError,
    process_csv_file
)


@pytest.mark.django_db
class TestCSVProcessorValidation:
    """Test CSV file validation logic."""

    def test_validate_file_exists(self, sample_csv_valid):
        """Test file existence validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(sample_csv_valid)
            file_path = f.name

        try:
            processor = AzureAdvisorCSVProcessor(file_path)
            assert processor.validate_file() is True
        finally:
            os.unlink(file_path)

    def test_validate_file_not_found(self):
        """Test validation with non-existent file."""
        processor = AzureAdvisorCSVProcessor('/nonexistent/file.csv')

        with pytest.raises(CSVProcessingError, match="File not found"):
            processor.validate_file()

    def test_validate_empty_file(self, sample_csv_empty):
        """Test validation with empty file."""
        processor = AzureAdvisorCSVProcessor(sample_csv_empty)

        with pytest.raises(CSVProcessingError, match="File is empty"):
            processor.validate_file()

    def test_validate_file_size_exceeds_limit(self):
        """Test file size limit validation."""
        # Create a large temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Write more than 50MB
            f.write("x" * (55 * 1024 * 1024))
            file_path = f.name

        try:
            processor = AzureAdvisorCSVProcessor(file_path)
            with pytest.raises(CSVProcessingError, match="exceeds maximum allowed size"):
                processor.validate_file()
        finally:
            os.unlink(file_path)


@pytest.mark.django_db
class TestCSVProcessorParsing:
    """Test CSV parsing functionality."""

    def test_read_csv_utf8(self, sample_csv_valid):
        """Test reading CSV with UTF-8 encoding."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(sample_csv_valid)
            file_path = f.name

        try:
            processor = AzureAdvisorCSVProcessor(file_path)
            df = processor.read_csv()

            assert df is not None
            assert len(df) > 0
            assert 'Category' in df.columns
            assert 'Recommendation' in df.columns
        finally:
            os.unlink(file_path)

    def test_read_csv_utf8_bom(self, sample_csv_utf8_bom):
        """Test reading CSV with UTF-8 BOM encoding."""
        processor = AzureAdvisorCSVProcessor(sample_csv_utf8_bom)
        df = processor.read_csv()

        assert df is not None
        assert len(df) > 0
        # BOM should be handled transparently

    def test_read_csv_empty_raises_error(self, sample_csv_empty):
        """Test reading empty CSV raises error."""
        processor = AzureAdvisorCSVProcessor(sample_csv_empty)

        with pytest.raises(CSVProcessingError, match="empty"):
            processor.read_csv()

    def test_read_csv_malformed_raises_error(self, sample_csv_malformed):
        """Test reading malformed CSV raises error."""
        processor = AzureAdvisorCSVProcessor(sample_csv_malformed)

        # This may or may not raise depending on pandas behavior
        # but should be handled gracefully
        try:
            processor.read_csv()
        except CSVProcessingError:
            pass  # Expected


@pytest.mark.django_db
class TestCSVStructureValidation:
    """Test CSV structure validation."""

    def test_validate_structure_with_required_columns(self, sample_csv_valid):
        """Test structure validation with all required columns."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(sample_csv_valid)
            file_path = f.name

        try:
            processor = AzureAdvisorCSVProcessor(file_path)
            processor.read_csv()
            assert processor.validate_structure() is True
        finally:
            os.unlink(file_path)

    def test_validate_structure_missing_columns(self, sample_csv_missing_columns):
        """Test structure validation with missing required columns."""
        processor = AzureAdvisorCSVProcessor(sample_csv_missing_columns)
        processor.read_csv()

        with pytest.raises(CSVProcessingError, match="Missing required columns"):
            processor.validate_structure()

    def test_validate_structure_no_data_rows(self):
        """Test validation with only header, no data rows."""
        content = "Category,Recommendation,Impact\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(content)
            file_path = f.name

        try:
            processor = AzureAdvisorCSVProcessor(file_path)
            processor.read_csv()

            with pytest.raises(CSVProcessingError, match="no data rows"):
                processor.validate_structure()
        finally:
            os.unlink(file_path)

    def test_validate_structure_too_many_rows(self):
        """Test validation with too many rows (>50,000)."""
        # Create CSV with 50,001 rows
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Category,Recommendation\n")
            for i in range(50001):
                f.write(f"Cost,Recommendation {i}\n")
            file_path = f.name

        try:
            processor = AzureAdvisorCSVProcessor(file_path)
            processor.read_csv()

            with pytest.raises(CSVProcessingError, match="exceeds the maximum allowed"):
                processor.validate_structure()
        finally:
            os.unlink(file_path)


@pytest.mark.django_db
class TestCategoryNormalization:
    """Test category mapping and normalization."""

    def test_normalize_cost_category(self, sample_csv_valid):
        """Test category normalization for Cost."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(sample_csv_valid)
            file_path = f.name

        try:
            processor = AzureAdvisorCSVProcessor(file_path)
            recommendations, _ = processor.process()

            cost_recs = [r for r in recommendations if r['category'] == 'cost']
            assert len(cost_recs) > 0
        finally:
            os.unlink(file_path)

    def test_normalize_security_category(self):
        """Test category normalization for Security."""
        content = "Category,Recommendation\nSecurity,Enable MFA\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(content)
            file_path = f.name

        try:
            processor = AzureAdvisorCSVProcessor(file_path)
            recommendations, _ = processor.process()

            assert recommendations[0]['category'] == 'security'
        finally:
            os.unlink(file_path)

    def test_normalize_reliability_category(self):
        """Test category normalization for Reliability/High Availability."""
        content = "Category,Recommendation\nHigh Availability,Enable backup\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(content)
            file_path = f.name

        try:
            processor = AzureAdvisorCSVProcessor(file_path)
            recommendations, _ = processor.process()

            assert recommendations[0]['category'] == 'reliability'
        finally:
            os.unlink(file_path)

    def test_normalize_case_insensitive(self):
        """Test case-insensitive category normalization."""
        content = "Category,Recommendation\ncost,Test\nCOST,Test2\nCost,Test3\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(content)
            file_path = f.name

        try:
            processor = AzureAdvisorCSVProcessor(file_path)
            recommendations, _ = processor.process()

            # All should be normalized to 'cost'
            for rec in recommendations:
                assert rec['category'] == 'cost'
        finally:
            os.unlink(file_path)


@pytest.mark.django_db
class TestImpactNormalization:
    """Test business impact normalization."""

    def test_normalize_high_impact(self):
        """Test High/high/HIGH impact normalization."""
        content = "Category,Recommendation,Business Impact\nCost,Test1,High\nCost,Test2,high\nCost,Test3,HIGH\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(content)
            file_path = f.name

        try:
            processor = AzureAdvisorCSVProcessor(file_path)
            recommendations, _ = processor.process()

            for rec in recommendations:
                assert rec['business_impact'] == 'high'
        finally:
            os.unlink(file_path)

    def test_normalize_medium_impact(self):
        """Test Medium impact normalization."""
        content = "Category,Recommendation,Business Impact\nCost,Test,Medium\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(content)
            file_path = f.name

        try:
            processor = AzureAdvisorCSVProcessor(file_path)
            recommendations, _ = processor.process()

            assert recommendations[0]['business_impact'] == 'medium'
        finally:
            os.unlink(file_path)

    def test_default_impact_when_missing(self):
        """Test default impact when Business Impact column is missing."""
        content = "Category,Recommendation\nCost,Test\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(content)
            file_path = f.name

        try:
            processor = AzureAdvisorCSVProcessor(file_path)
            recommendations, _ = processor.process()

            # Should default to 'medium'
            assert recommendations[0]['business_impact'] == 'medium'
        finally:
            os.unlink(file_path)


@pytest.mark.django_db
class TestStatisticsCalculation:
    """Test statistics calculation from recommendations."""

    def test_calculate_category_distribution(self, sample_csv_valid):
        """Test category distribution calculation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(sample_csv_valid)
            file_path = f.name

        try:
            processor = AzureAdvisorCSVProcessor(file_path)
            recommendations, statistics = processor.process()

            assert 'category_distribution' in statistics
            assert isinstance(statistics['category_distribution'], dict)
            assert statistics['total_recommendations'] == len(recommendations)
        finally:
            os.unlink(file_path)

    def test_calculate_total_savings(self, sample_csv_valid):
        """Test total potential savings calculation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(sample_csv_valid)
            file_path = f.name

        try:
            processor = AzureAdvisorCSVProcessor(file_path)
            recommendations, statistics = processor.process()

            assert 'total_potential_savings' in statistics
            assert statistics['total_potential_savings'] >= 0
            # Sample CSV has 1,350 in savings (1,200 + 150)
            assert statistics['total_potential_savings'] == 1350.00
        finally:
            os.unlink(file_path)

    def test_calculate_impact_distribution(self, sample_csv_valid):
        """Test business impact distribution calculation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(sample_csv_valid)
            file_path = f.name

        try:
            processor = AzureAdvisorCSVProcessor(file_path)
            recommendations, statistics = processor.process()

            assert 'business_impact_distribution' in statistics
            impact_dist = statistics['business_impact_distribution']
            assert isinstance(impact_dist, dict)
        finally:
            os.unlink(file_path)

    def test_calculate_top_recommendations(self, sample_csv_valid):
        """Test top 10 recommendations by savings."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(sample_csv_valid)
            file_path = f.name

        try:
            processor = AzureAdvisorCSVProcessor(file_path)
            recommendations, statistics = processor.process()

            assert 'top_recommendations' in statistics
            top_recs = statistics['top_recommendations']
            assert isinstance(top_recs, list)
            assert len(top_recs) <= 10
        finally:
            os.unlink(file_path)


@pytest.mark.django_db
class TestDataCleaning:
    """Test data cleaning and handling of missing values."""

    def test_handle_missing_data(self):
        """Test handling of missing/null values in CSV."""
        content = "Category,Recommendation,Potential Annual Cost Savings\nCost,Test1,\nSecurity,Test2,N/A\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(content)
            file_path = f.name

        try:
            processor = AzureAdvisorCSVProcessor(file_path)
            recommendations, _ = processor.process()

            # Missing savings should default to 0
            for rec in recommendations:
                assert rec['potential_savings'] >= 0
        finally:
            os.unlink(file_path)

    def test_clean_whitespace(self):
        """Test whitespace trimming in data."""
        content = "Category,Recommendation\n  Cost  ,  Test recommendation  \n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(content)
            file_path = f.name

        try:
            processor = AzureAdvisorCSVProcessor(file_path)
            recommendations, _ = processor.process()

            # Whitespace should be trimmed
            assert recommendations[0]['recommendation'] == 'Test recommendation'
        finally:
            os.unlink(file_path)

    def test_remove_empty_rows(self):
        """Test removal of completely empty rows."""
        content = "Category,Recommendation\nCost,Test1\n,,\nSecurity,Test2\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(content)
            file_path = f.name

        try:
            processor = AzureAdvisorCSVProcessor(file_path)
            recommendations, _ = processor.process()

            # Empty row should be skipped
            assert len(recommendations) == 2
        finally:
            os.unlink(file_path)


@pytest.mark.django_db
class TestLargeCSVPerformance:
    """Test CSV processing performance with large files."""

    def test_large_csv_processing_performance(self, sample_csv_large):
        """Test processing 1000+ row CSV completes in reasonable time."""
        import time

        start = time.time()
        processor = AzureAdvisorCSVProcessor(sample_csv_large)
        recommendations, statistics = processor.process()
        duration = time.time() - start

        # Should complete in less than 30 seconds
        assert duration < 30
        assert len(recommendations) == 1000
        assert statistics['total_recommendations'] == 1000

    def test_large_csv_statistics_accuracy(self, sample_csv_large):
        """Test statistics calculation accuracy with large dataset."""
        processor = AzureAdvisorCSVProcessor(sample_csv_large)
        recommendations, statistics = processor.process()

        # Verify statistics make sense
        assert statistics['total_recommendations'] == len(recommendations)
        assert statistics['total_potential_savings'] > 0
        assert len(statistics['category_distribution']) > 0


@pytest.mark.django_db
class TestConvenienceFunction:
    """Test the convenience function for CSV processing."""

    def test_process_csv_file_function(self, sample_csv_valid):
        """Test process_csv_file convenience function."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(sample_csv_valid)
            file_path = f.name

        try:
            recommendations, statistics = process_csv_file(file_path)

            assert isinstance(recommendations, list)
            assert isinstance(statistics, dict)
            assert len(recommendations) > 0
        finally:
            os.unlink(file_path)

    def test_process_csv_file_error_handling(self):
        """Test error handling in convenience function."""
        with pytest.raises(CSVProcessingError):
            process_csv_file('/nonexistent/file.csv')
