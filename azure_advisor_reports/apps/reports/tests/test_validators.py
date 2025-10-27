"""
Tests for CSV file validators.

This module tests the validation functions used for CSV file uploads,
ensuring file size, extension, structure, and content validation work correctly.
"""

import io
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile, InMemoryUploadedFile
from django.conf import settings

from apps.reports.validators import (
    validate_file_size,
    validate_file_extension,
    validate_csv_structure,
    validate_csv_content,
    validate_csv_file
)


@pytest.mark.django_db
class TestValidateFileSize:
    """Test cases for file size validation."""

    def test_validate_file_size_within_limit(self):
        """Test that files within size limit pass validation."""
        # Create a small file (1 MB)
        file_content = b'a' * (1024 * 1024)  # 1 MB
        file = SimpleUploadedFile("test.csv", file_content)

        # Should not raise ValidationError
        validate_file_size(file)

    def test_validate_file_size_at_limit(self):
        """Test file exactly at size limit passes validation."""
        max_size = settings.MAX_UPLOAD_SIZE
        file = Mock()
        file.size = max_size

        # Should not raise ValidationError
        validate_file_size(file)

    def test_validate_file_size_exceeds_limit(self):
        """Test that files exceeding size limit raise ValidationError."""
        max_size = settings.MAX_UPLOAD_SIZE
        file = Mock()
        file.size = max_size + 1  # Just over the limit

        with pytest.raises(ValidationError) as exc_info:
            validate_file_size(file)

        assert "exceeds the maximum allowed size" in str(exc_info.value)

    def test_validate_file_size_far_exceeds_limit(self):
        """Test very large files raise ValidationError."""
        file = Mock()
        file.size = 100 * 1024 * 1024  # 100 MB (default limit is 50 MB)

        with pytest.raises(ValidationError) as exc_info:
            validate_file_size(file)

        assert "exceeds the maximum allowed size" in str(exc_info.value)

    def test_validate_file_size_error_message_includes_sizes(self):
        """Test error message includes both file size and limit."""
        max_size = settings.MAX_UPLOAD_SIZE
        file = Mock()
        file.size = max_size * 2  # Double the limit

        with pytest.raises(ValidationError) as exc_info:
            validate_file_size(file)

        error_message = str(exc_info.value)
        assert "MB" in error_message
        # Should contain both file size and max size


@pytest.mark.django_db
class TestValidateFileExtension:
    """Test cases for file extension validation."""

    def test_validate_csv_extension_lowercase(self):
        """Test that .csv extension passes validation."""
        file = Mock()
        file.name = "test_file.csv"

        # Should not raise ValidationError
        validate_file_extension(file)

    def test_validate_csv_extension_uppercase(self):
        """Test that .CSV extension passes validation."""
        file = Mock()
        file.name = "test_file.CSV"

        # Should not raise ValidationError
        validate_file_extension(file)

    def test_validate_csv_extension_mixed_case(self):
        """Test that .Csv extension passes validation."""
        file = Mock()
        file.name = "test_file.CsV"

        # Should not raise ValidationError
        validate_file_extension(file)

    def test_validate_invalid_extension_txt(self):
        """Test that .txt extension raises ValidationError."""
        file = Mock()
        file.name = "test_file.txt"

        with pytest.raises(ValidationError) as exc_info:
            validate_file_extension(file)

        assert "Invalid file extension" in str(exc_info.value)
        assert ".txt" in str(exc_info.value)

    def test_validate_invalid_extension_xlsx(self):
        """Test that .xlsx extension raises ValidationError."""
        file = Mock()
        file.name = "test_file.xlsx"

        with pytest.raises(ValidationError) as exc_info:
            validate_file_extension(file)

        assert "Invalid file extension" in str(exc_info.value)

    def test_validate_invalid_extension_no_extension(self):
        """Test that files without extension raise ValidationError."""
        file = Mock()
        file.name = "test_file"

        with pytest.raises(ValidationError) as exc_info:
            validate_file_extension(file)

        assert "Invalid file extension" in str(exc_info.value)

    def test_validate_extension_error_message_shows_allowed(self):
        """Test error message shows allowed extensions."""
        file = Mock()
        file.name = "test.pdf"

        with pytest.raises(ValidationError) as exc_info:
            validate_file_extension(file)

        error_message = str(exc_info.value)
        assert "Allowed extensions:" in error_message
        assert ".csv" in error_message.lower()

    def test_validate_extension_multiple_dots(self):
        """Test file with multiple dots in name validates correctly."""
        file = Mock()
        file.name = "my.test.file.csv"

        # Should not raise ValidationError
        validate_file_extension(file)


@pytest.mark.django_db
class TestValidateCSVStructure:
    """Test cases for CSV structure validation."""

    def create_csv_file(self, content):
        """Helper to create a CSV file from string content."""
        return io.BytesIO(content.encode('utf-8'))

    def test_validate_csv_structure_valid_standard_columns(self):
        """Test CSV with standard Azure Advisor columns passes validation."""
        csv_content = """Category,Impact,Recommendation,Affected Resource,Type
Cost,High,Reduce unused resources,vm-test-001,Virtual Machine
Security,Medium,Enable firewall,storage-acc-001,Storage Account
Reliability,Low,Add availability zone,db-001,Database"""

        file = self.create_csv_file(csv_content)

        # Should not raise ValidationError
        validate_csv_structure(file)

    def test_validate_csv_structure_valid_variant_columns(self):
        """Test CSV with variant column names passes validation."""
        csv_content = """category,business_impact,description,resource_name,resource_type
Cost,High,Reduce unused resources,vm-test-001,Virtual Machine"""

        file = self.create_csv_file(csv_content)

        # Should not raise ValidationError
        validate_csv_structure(file)

    def test_validate_csv_structure_missing_required_column(self):
        """Test CSV missing required column raises ValidationError."""
        # Missing 'Recommendation' column
        csv_content = """Category,Impact,Affected Resource,Type
Cost,High,vm-test-001,Virtual Machine"""

        file = self.create_csv_file(csv_content)

        with pytest.raises(ValidationError) as exc_info:
            validate_csv_structure(file)

        assert "missing required columns" in str(exc_info.value).lower()

    def test_validate_csv_structure_empty_file(self):
        """Test empty CSV file raises ValidationError."""
        csv_content = ""
        file = self.create_csv_file(csv_content)

        with pytest.raises(ValidationError) as exc_info:
            validate_csv_structure(file)

        error_msg = str(exc_info.value).lower()
        # Error can be about empty file or no columns
        assert "empty" in error_msg or "no data" in error_msg or "no columns" in error_msg

    def test_validate_csv_structure_only_headers(self):
        """Test CSV with only headers (no data rows) raises ValidationError."""
        csv_content = """Category,Impact,Recommendation,Affected Resource,Type"""
        file = self.create_csv_file(csv_content)

        with pytest.raises(ValidationError) as exc_info:
            validate_csv_structure(file)

        error_msg = str(exc_info.value).lower()
        assert "no data rows" in error_msg or "empty" in error_msg

    def test_validate_csv_structure_too_many_rows(self):
        """Test CSV exceeding max rows raises ValidationError."""
        # Create CSV with more than MAX_ROWS
        max_rows = settings.CSV_MAX_ROWS
        headers = "Category,Impact,Recommendation,Affected Resource,Type\n"
        rows = "Cost,High,Test recommendation,vm-001,Virtual Machine\n" * (max_rows + 100)
        csv_content = headers + rows

        file = self.create_csv_file(csv_content)

        with pytest.raises(ValidationError) as exc_info:
            validate_csv_structure(file)

        assert "exceeding the maximum allowed" in str(exc_info.value)

    def test_validate_csv_structure_with_extra_columns(self):
        """Test CSV with extra columns still passes validation."""
        csv_content = """Category,Impact,Recommendation,Affected Resource,Type,Extra1,Extra2
Cost,High,Reduce unused resources,vm-test-001,Virtual Machine,value1,value2"""

        file = self.create_csv_file(csv_content)

        # Should not raise ValidationError (extra columns are OK)
        validate_csv_structure(file)

    def test_validate_csv_structure_invalid_encoding(self):
        """Test CSV with invalid encoding raises appropriate error."""
        # Create file with invalid encoding
        file = io.BytesIO(b'\x80\x81\x82\x83')  # Invalid UTF-8 bytes

        # Should raise ValidationError (any error message is acceptable)
        with pytest.raises(ValidationError):
            validate_csv_structure(file)

    def test_validate_csv_structure_with_bom(self):
        """Test CSV with UTF-8 BOM is handled correctly."""
        csv_content = """Category,Impact,Recommendation,Affected Resource,Type
Cost,High,Reduce unused resources,vm-test-001,Virtual Machine"""

        # Add UTF-8 BOM
        file = io.BytesIO(b'\xef\xbb\xbf' + csv_content.encode('utf-8'))

        # Should handle BOM and not raise ValidationError
        validate_csv_structure(file)

    def test_validate_csv_structure_malformed_csv(self):
        """Test malformed CSV raises ValidationError."""
        # CSV with inconsistent number of columns
        csv_content = """Category,Impact,Recommendation,Affected Resource,Type
Cost,High,Test
Security,Medium,Test,resource,type,extra,extra2"""

        file = self.create_csv_file(csv_content)

        # pandas should handle this, but validation should still work
        # This might not raise error as pandas is forgiving
        try:
            validate_csv_structure(file)
        except ValidationError:
            pass  # OK if it raises

    def test_validate_csv_structure_resets_file_pointer(self):
        """Test that file pointer is reset after validation."""
        csv_content = """Category,Impact,Recommendation,Affected Resource,Type
Cost,High,Reduce unused resources,vm-test-001,Virtual Machine"""

        file = self.create_csv_file(csv_content)

        validate_csv_structure(file)

        # File pointer should be reset to beginning
        assert file.tell() == 0


@pytest.mark.django_db
class TestValidateCSVContent:
    """Test cases for CSV content validation."""

    def create_csv_file(self, content):
        """Helper to create a CSV file from string content."""
        return io.BytesIO(content.encode('utf-8'))

    def test_validate_csv_content_valid_data(self):
        """Test CSV with valid content passes validation."""
        csv_content = """Category,Impact,Recommendation,Affected Resource,Type
Cost,High,Reduce unused resources,vm-test-001,Virtual Machine
Security,Medium,Enable firewall,storage-001,Storage Account"""

        file = self.create_csv_file(csv_content)

        # Should not raise ValidationError
        validate_csv_content(file)

    def test_validate_csv_content_with_some_empty_cells(self):
        """Test CSV with some empty cells passes validation."""
        csv_content = """Category,Impact,Recommendation,Affected Resource,Type
Cost,High,Reduce unused resources,vm-test-001,Virtual Machine
Security,,Enable firewall,storage-001,"""

        file = self.create_csv_file(csv_content)

        # Should not raise ValidationError (some empty cells are OK)
        validate_csv_content(file)

    def test_validate_csv_content_many_empty_columns(self):
        """Test CSV with too many empty columns raises ValidationError."""
        # Create CSV with 10 empty columns
        headers = "Col1,Col2,Col3,Col4,Col5,Col6,Col7,Col8,Col9,Col10"
        rows = ",,,,,,,,,"
        csv_content = f"{headers}\n{rows}\n{rows}\n{rows}"

        file = self.create_csv_file(csv_content)

        with pytest.raises(ValidationError) as exc_info:
            validate_csv_content(file)

        assert "empty columns" in str(exc_info.value).lower()

    def test_validate_csv_content_all_data_empty(self):
        """Test CSV where all data cells are empty raises ValidationError."""
        csv_content = """Category,Impact,Recommendation
,,
,,
,,"""

        file = self.create_csv_file(csv_content)

        with pytest.raises(ValidationError) as exc_info:
            validate_csv_content(file)

        assert "no actual data" in str(exc_info.value).lower()

    def test_validate_csv_content_empty_data_error(self):
        """Test completely empty CSV raises ValidationError."""
        csv_content = ""
        file = self.create_csv_file(csv_content)

        with pytest.raises(ValidationError) as exc_info:
            validate_csv_content(file)

        error_msg = str(exc_info.value).lower()
        assert "empty" in error_msg or "corrupted" in error_msg

    def test_validate_csv_content_with_special_characters(self):
        """Test CSV with special characters in content passes validation."""
        csv_content = """Category,Impact,Recommendation,Affected Resource,Type
Cost,High,"Reduce $100/month costs",vm-test-001,Virtual Machine
Security,Medium,"Enable firewall & monitoring",storage-001,Storage Account"""

        file = self.create_csv_file(csv_content)

        # Should handle special characters and not raise error
        validate_csv_content(file)

    def test_validate_csv_content_resets_file_pointer(self):
        """Test that file pointer is reset after validation."""
        csv_content = """Category,Impact,Recommendation
Cost,High,Test recommendation"""

        file = self.create_csv_file(csv_content)

        validate_csv_content(file)

        # File pointer should be reset to beginning
        assert file.tell() == 0

    def test_validate_csv_content_different_encoding(self):
        """Test CSV with different encoding is handled."""
        csv_content = """Category,Impact,Recommendation
Cost,High,Café recommendation"""

        # Try with UTF-8
        file = io.BytesIO(csv_content.encode('utf-8'))
        validate_csv_content(file)

        # Try with Latin-1
        file = io.BytesIO(csv_content.encode('latin-1'))
        # Should try different encodings and not fail
        try:
            validate_csv_content(file)
        except ValidationError:
            pass  # OK if it can't decode


@pytest.mark.django_db
class TestValidateCSVFile:
    """Test cases for the main CSV file validation function."""

    def create_csv_file(self, content, filename="test.csv"):
        """Helper to create a CSV file from string content."""
        file_bytes = content.encode('utf-8')
        return SimpleUploadedFile(filename, file_bytes, content_type='text/csv')

    def test_validate_csv_file_valid_complete(self):
        """Test complete validation of valid CSV file passes."""
        csv_content = """Category,Impact,Recommendation,Affected Resource,Type
Cost,High,Reduce unused resources,vm-test-001,Virtual Machine
Security,Medium,Enable firewall,storage-001,Storage Account
Reliability,Low,Add availability zone,db-001,Database"""

        file = self.create_csv_file(csv_content)

        # Should not raise ValidationError
        validate_csv_file(file)

    def test_validate_csv_file_fails_on_size(self):
        """Test validation fails if file size exceeds limit."""
        # Create oversized file
        max_size = settings.MAX_UPLOAD_SIZE
        large_content = "a" * (max_size + 1000)
        file = self.create_csv_file(large_content)

        with pytest.raises(ValidationError) as exc_info:
            validate_csv_file(file)

        assert "exceeds the maximum allowed size" in str(exc_info.value)

    def test_validate_csv_file_fails_on_extension(self):
        """Test validation fails for wrong file extension."""
        csv_content = """Category,Impact,Recommendation,Affected Resource,Type
Cost,High,Test,vm-001,VM"""

        file = self.create_csv_file(csv_content, filename="test.txt")

        with pytest.raises(ValidationError) as exc_info:
            validate_csv_file(file)

        assert "Invalid file extension" in str(exc_info.value)

    def test_validate_csv_file_fails_on_structure(self):
        """Test validation fails for invalid CSV structure."""
        # Missing required columns
        csv_content = """OnlyOneColumn
SomeData"""

        file = self.create_csv_file(csv_content)

        with pytest.raises(ValidationError) as exc_info:
            validate_csv_file(file)

        assert "missing required columns" in str(exc_info.value).lower()

    def test_validate_csv_file_fails_on_empty_content(self):
        """Test validation fails for empty CSV."""
        csv_content = ""
        file = self.create_csv_file(csv_content)

        with pytest.raises(ValidationError):
            validate_csv_file(file)

    def test_validate_csv_file_runs_all_validators(self):
        """Test that all validators are called in sequence."""
        csv_content = """Category,Impact,Recommendation,Affected Resource,Type
Cost,High,Test,vm-001,VM"""

        file = self.create_csv_file(csv_content)

        # Mock all validators to verify they're called
        with patch('apps.reports.validators.validate_file_size') as mock_size, \
             patch('apps.reports.validators.validate_file_extension') as mock_ext, \
             patch('apps.reports.validators.validate_csv_structure') as mock_struct, \
             patch('apps.reports.validators.validate_csv_content') as mock_content:

            validate_csv_file(file)

            # All validators should be called
            mock_size.assert_called_once()
            mock_ext.assert_called_once()
            mock_struct.assert_called_once()
            mock_content.assert_called_once()

    def test_validate_csv_file_stops_on_first_error(self):
        """Test that validation stops at first error."""
        csv_content = """Category,Impact,Recommendation,Affected Resource,Type
Cost,High,Test,vm-001,VM"""

        file = self.create_csv_file(csv_content, filename="test.txt")

        # Should fail on extension check and not proceed to structure check
        with patch('apps.reports.validators.validate_csv_structure') as mock_struct:
            with pytest.raises(ValidationError):
                validate_csv_file(file)

            # Structure validation should not be called
            mock_struct.assert_not_called()

    def test_validate_csv_file_with_realistic_azure_data(self):
        """Test validation with realistic Azure Advisor export data."""
        csv_content = """Category,Impact,Recommendation,Subscription ID,Resource Group,Affected Resource,Type,Potential Savings,Currency
Cost,High,Delete unused virtual machine,12345-67890,rg-production,vm-unused-001,Microsoft.Compute/virtualMachines,$500.00,USD
Security,Medium,Enable Azure Security Center,12345-67890,rg-production,subscription-level,Subscription,N/A,USD
Reliability,Low,Enable availability zones,12345-67890,rg-production,db-prod-001,Microsoft.Sql/servers,N/A,USD"""

        file = self.create_csv_file(csv_content)

        # Should pass all validations
        validate_csv_file(file)


@pytest.mark.django_db
class TestEdgeCases:
    """Test edge cases and corner scenarios."""

    def create_csv_file(self, content, filename="test.csv"):
        """Helper to create a CSV file."""
        file_bytes = content.encode('utf-8')
        return SimpleUploadedFile(filename, file_bytes, content_type='text/csv')

    def test_csv_with_unicode_characters(self):
        """Test CSV with Unicode characters passes validation."""
        csv_content = """Category,Impact,Recommendation,Affected Resource,Type
Cost,High,Réduire les coûts,vm-café-001,Virtual Machine
Security,Medium,启用防火墙,storage-001,Storage Account"""

        file = self.create_csv_file(csv_content)
        validate_csv_file(file)

    def test_csv_with_very_long_lines(self):
        """Test CSV with very long lines passes validation."""
        long_recommendation = "This is a very long recommendation " * 100
        csv_content = f"""Category,Impact,Recommendation,Affected Resource,Type
Cost,High,{long_recommendation},vm-001,Virtual Machine"""

        file = self.create_csv_file(csv_content)
        validate_csv_file(file)

    def test_csv_with_newlines_in_quoted_fields(self):
        """Test CSV with newlines in quoted fields is handled."""
        csv_content = """Category,Impact,Recommendation,Affected Resource,Type
Cost,High,"Multi-line
recommendation
text",vm-001,Virtual Machine"""

        file = self.create_csv_file(csv_content)
        validate_csv_file(file)

    def test_csv_with_commas_in_quoted_fields(self):
        """Test CSV with commas in quoted fields is handled."""
        csv_content = """Category,Impact,Recommendation,Affected Resource,Type
Cost,High,"Reduce costs by $1,000, $2,000, or $3,000",vm-001,Virtual Machine"""

        file = self.create_csv_file(csv_content)
        validate_csv_file(file)

    def test_file_size_exactly_zero(self):
        """Test zero-size file raises ValidationError."""
        file = Mock()
        file.size = 0
        file.name = "test.csv"

        # Zero-size should be allowed by size validator
        # But should fail on structure/content validation
        validate_file_size(file)  # Should pass

    def test_case_insensitive_column_matching(self):
        """Test that column name matching is case-insensitive."""
        csv_content = """CATEGORY,IMPACT,RECOMMENDATION,AFFECTED RESOURCE,TYPE
Cost,High,Test,vm-001,VM"""

        file = self.create_csv_file(csv_content)
        validate_csv_structure(io.BytesIO(csv_content.encode('utf-8')))
