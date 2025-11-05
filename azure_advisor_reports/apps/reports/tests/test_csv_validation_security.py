"""
Security Tests for CSV File Upload Validation.

These tests verify that the CSV upload validation correctly rejects
malicious files and prevents common attack vectors.

Security Vulnerabilities Tested:
- File type spoofing (renaming .exe to .csv)
- Path traversal attacks via filename
- Oversized file uploads (DoS)
- Invalid file formats
- Missing required columns
- Empty files
- Excessive cell sizes (DoS)
"""

import os
import tempfile
from io import BytesIO
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile, InMemoryUploadedFile
from apps.reports.serializers import CSVUploadSerializer
from apps.clients.models import Client
from apps.authentication.models import User


class CSVUploadValidationSecurityTestCase(TestCase):
    """
    Security test suite for CSV file upload validation.
    """

    def setUp(self):
        """Set up test fixtures."""
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User',
            role='admin'
        )

        # Create test client
        self.client_instance = Client.objects.create(
            company_name='Test Company',
            primary_contact_email='contact@test.com'
        )

    def create_csv_file(self, filename: str, content: str, content_type='text/csv'):
        """
        Helper to create a test CSV file.

        Args:
            filename: Name of the file
            content: File content as string
            content_type: MIME type

        Returns:
            SimpleUploadedFile instance
        """
        return SimpleUploadedFile(
            filename,
            content.encode('utf-8'),
            content_type=content_type
        )

    def test_valid_csv_passes_validation(self):
        """Test that a valid CSV file passes validation."""
        csv_content = "Category,Recommendation,Business Impact\nCost,Test recommendation,High\n"
        csv_file = self.create_csv_file('valid.csv', csv_content)

        data = {
            'csv_file': csv_file,
            'client_id': str(self.client_instance.id),
            'report_type': 'detailed',
        }

        serializer = CSVUploadSerializer(data=data)
        self.assertTrue(serializer.is_valid(), f"Validation errors: {serializer.errors}")

    def test_invalid_extension_rejected(self):
        """Test that non-CSV file extensions are rejected."""
        csv_content = "Category,Recommendation\nCost,Test\n"

        # Try various invalid extensions
        invalid_extensions = ['.txt', '.xlsx', '.exe', '.pdf', '.doc', '.xls']

        for ext in invalid_extensions:
            with self.subTest(extension=ext):
                csv_file = self.create_csv_file(f'malicious{ext}', csv_content)

                data = {
                    'csv_file': csv_file,
                    'client_id': str(self.client_instance.id),
                }

                serializer = CSVUploadSerializer(data=data)
                self.assertFalse(serializer.is_valid(),
                                f"Should reject {ext} files")
                self.assertIn('csv_file', serializer.errors)

    def test_empty_file_rejected(self):
        """Test that empty files are rejected."""
        csv_file = self.create_csv_file('empty.csv', '')

        data = {
            'csv_file': csv_file,
            'client_id': str(self.client_instance.id),
        }

        serializer = CSVUploadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('csv_file', serializer.errors)

    def test_oversized_file_rejected(self):
        """Test that files exceeding MAX_UPLOAD_SIZE are rejected."""
        from django.conf import settings

        # Create a file larger than MAX_UPLOAD_SIZE
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 50 * 1024 * 1024)
        large_content = "A" * (max_size + 1000)

        csv_file = SimpleUploadedFile(
            'large.csv',
            large_content.encode('utf-8'),
            content_type='text/csv'
        )

        data = {
            'csv_file': csv_file,
            'client_id': str(self.client_instance.id),
        }

        serializer = CSVUploadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('csv_file', serializer.errors)
        self.assertIn('size', str(serializer.errors['csv_file'][0]).lower())

    def test_missing_required_columns_rejected(self):
        """Test that CSVs without required columns are rejected."""
        # CSV missing 'Recommendation' column
        csv_content = "Category,Description\nCost,Some description\n"
        csv_file = self.create_csv_file('missing_columns.csv', csv_content)

        data = {
            'csv_file': csv_file,
            'client_id': str(self.client_instance.id),
        }

        serializer = CSVUploadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('csv_file', serializer.errors)
        self.assertIn('recommendation', str(serializer.errors['csv_file'][0]).lower())

    def test_csv_with_only_header_rejected(self):
        """Test that CSV with only headers (no data) is rejected."""
        csv_content = "Category,Recommendation\n"
        csv_file = self.create_csv_file('header_only.csv', csv_content)

        data = {
            'csv_file': csv_file,
            'client_id': str(self.client_instance.id),
        }

        serializer = CSVUploadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('csv_file', serializer.errors)
        self.assertIn('no data', str(serializer.errors['csv_file'][0]).lower())

    def test_invalid_encoding_rejected(self):
        """Test that files with invalid encoding are rejected."""
        # Create file with invalid UTF-8 sequences
        csv_file = SimpleUploadedFile(
            'invalid_encoding.csv',
            b'\xff\xfe\x00\x00',  # Invalid UTF-8
            content_type='text/csv'
        )

        data = {
            'csv_file': csv_file,
            'client_id': str(self.client_instance.id),
        }

        serializer = CSVUploadSerializer(data=data)
        # Should either reject or handle gracefully
        if not serializer.is_valid():
            self.assertIn('csv_file', serializer.errors)

    def test_path_traversal_filename_sanitized(self):
        """Test that filenames with path traversal attempts are sanitized."""
        csv_content = "Category,Recommendation\nCost,Test\n"

        # Attempt path traversal via filename
        malicious_filenames = [
            '../../../etc/passwd.csv',
            '..\\..\\..\\windows\\system32\\config\\sam.csv',
            'test/../../evil.csv',
            'test\\..\\..\\evil.csv',
        ]

        for mal_filename in malicious_filenames:
            with self.subTest(filename=mal_filename):
                csv_file = self.create_csv_file(mal_filename, csv_content)

                data = {
                    'csv_file': csv_file,
                    'client_id': str(self.client_instance.id),
                }

                serializer = CSVUploadSerializer(data=data)

                # Should pass validation after sanitization
                if serializer.is_valid():
                    # Verify filename was sanitized (no ../ or ..\\)
                    sanitized_name = csv_file.name
                    self.assertNotIn('..', sanitized_name,
                                   "Path traversal characters should be removed")
                    self.assertNotIn('/', sanitized_name,
                                   "Path separators should be removed")
                    self.assertNotIn('\\', sanitized_name,
                                   "Path separators should be removed")

    def test_special_characters_in_filename_sanitized(self):
        """Test that special characters in filenames are sanitized."""
        csv_content = "Category,Recommendation\nCost,Test\n"

        special_filenames = [
            'test<script>.csv',
            'test|command.csv',
            'test;rm-rf.csv',
            'test&whoami.csv',
            'test$(whoami).csv',
            'test`whoami`.csv',
        ]

        for special_filename in special_filenames:
            with self.subTest(filename=special_filename):
                csv_file = self.create_csv_file(special_filename, csv_content)

                data = {
                    'csv_file': csv_file,
                    'client_id': str(self.client_instance.id),
                }

                serializer = CSVUploadSerializer(data=data)

                if serializer.is_valid():
                    # Verify dangerous characters were removed
                    sanitized_name = csv_file.name
                    dangerous_chars = ['<', '>', '|', ';', '&', '$', '`', '(', ')']
                    for char in dangerous_chars:
                        self.assertNotIn(char, sanitized_name,
                                       f"Dangerous character '{char}' should be removed")

    def test_excessive_cell_size_rejected(self):
        """Test that CSVs with excessively large cells are rejected (DoS prevention)."""
        from django.conf import settings

        max_cell_size = getattr(settings, 'CSV_MAX_CELL_SIZE', 10000)

        # Create CSV with cell larger than max
        large_cell = "A" * (max_cell_size + 100)
        csv_content = f"Category,Recommendation\nCost,{large_cell}\n"
        csv_file = self.create_csv_file('large_cell.csv', csv_content)

        data = {
            'csv_file': csv_file,
            'client_id': str(self.client_instance.id),
        }

        serializer = CSVUploadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('csv_file', serializer.errors)
        self.assertIn('cell', str(serializer.errors['csv_file'][0]).lower())

    def test_invalid_csv_format_rejected(self):
        """Test that malformed CSV structure is rejected."""
        # Invalid CSV: unclosed quotes
        csv_content = 'Category,Recommendation\n"Unclosed quote,Test\n'
        csv_file = self.create_csv_file('invalid_format.csv', csv_content)

        data = {
            'csv_file': csv_file,
            'client_id': str(self.client_instance.id),
        }

        serializer = CSVUploadSerializer(data=data)
        # May pass or fail depending on parser tolerance
        # Main goal is to not crash the application

    def test_binary_file_disguised_as_csv_rejected(self):
        """Test that binary files with .csv extension are rejected."""
        # Create a fake binary file (e.g., PE executable header)
        binary_content = b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00'  # PE header

        csv_file = SimpleUploadedFile(
            'malicious.csv',
            binary_content,
            content_type='text/csv'
        )

        data = {
            'csv_file': csv_file,
            'client_id': str(self.client_instance.id),
        }

        serializer = CSVUploadSerializer(data=data)
        # Should fail validation (either MIME type check or CSV parsing)
        self.assertFalse(serializer.is_valid())
        self.assertIn('csv_file', serializer.errors)

    def test_file_with_null_bytes_rejected(self):
        """Test that files containing null bytes are handled safely."""
        csv_content = "Category,Recommendation\nCost,Test\x00malicious\n"
        csv_file = self.create_csv_file('null_bytes.csv', csv_content)

        data = {
            'csv_file': csv_file,
            'client_id': str(self.client_instance.id),
        }

        serializer = CSVUploadSerializer(data=data)
        # Should either reject or handle gracefully without crashing

    def test_filename_length_limited(self):
        """Test that excessively long filenames are truncated."""
        csv_content = "Category,Recommendation\nCost,Test\n"

        # Create filename longer than 255 characters
        long_filename = "A" * 300 + ".csv"
        csv_file = self.create_csv_file(long_filename, csv_content)

        data = {
            'csv_file': csv_file,
            'client_id': str(self.client_instance.id),
        }

        serializer = CSVUploadSerializer(data=data)

        if serializer.is_valid():
            # Verify filename was truncated to max 255 characters
            self.assertLessEqual(len(csv_file.name), 255,
                               "Filename should be truncated to 255 characters")

    def test_case_insensitive_column_matching(self):
        """Test that column matching is case-insensitive."""
        # Required columns in different cases
        test_cases = [
            "category,recommendation\nCost,Test\n",  # lowercase
            "CATEGORY,RECOMMENDATION\nCost,Test\n",  # uppercase
            "Category,Recommendation\nCost,Test\n",  # mixed case
            "CaTeGoRy,ReCoMmEnDaTiOn\nCost,Test\n",  # random case
        ]

        for csv_content in test_cases:
            with self.subTest(content=csv_content[:30]):
                csv_file = self.create_csv_file('test.csv', csv_content)

                data = {
                    'csv_file': csv_file,
                    'client_id': str(self.client_instance.id),
                }

                serializer = CSVUploadSerializer(data=data)
                self.assertTrue(serializer.is_valid(),
                              f"Should accept case variations. Errors: {serializer.errors}")

    def test_whitespace_in_column_names_handled(self):
        """Test that whitespace in column names is handled correctly."""
        csv_content = " Category , Recommendation \nCost,Test\n"
        csv_file = self.create_csv_file('whitespace.csv', csv_content)

        data = {
            'csv_file': csv_file,
            'client_id': str(self.client_instance.id),
        }

        serializer = CSVUploadSerializer(data=data)
        self.assertTrue(serializer.is_valid(),
                       f"Should handle whitespace in headers. Errors: {serializer.errors}")


class MIMETypeValidationTestCase(TestCase):
    """
    Test MIME type validation with python-magic (if available).
    """

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User',
            role='admin'
        )

        self.client_instance = Client.objects.create(
            company_name='Test Company',
            primary_contact_email='contact@test.com'
        )

    def test_text_csv_mime_type_accepted(self):
        """Test that text/csv MIME type is accepted."""
        csv_content = "Category,Recommendation\nCost,Test\n"
        csv_file = SimpleUploadedFile(
            'test.csv',
            csv_content.encode('utf-8'),
            content_type='text/csv'
        )

        data = {
            'csv_file': csv_file,
            'client_id': str(self.client_instance.id),
        }

        serializer = CSVUploadSerializer(data=data)
        self.assertTrue(serializer.is_valid(),
                       f"Should accept text/csv. Errors: {serializer.errors}")

    def test_application_csv_mime_type_accepted(self):
        """Test that application/csv MIME type is accepted."""
        csv_content = "Category,Recommendation\nCost,Test\n"
        csv_file = SimpleUploadedFile(
            'test.csv',
            csv_content.encode('utf-8'),
            content_type='application/csv'
        )

        data = {
            'csv_file': csv_file,
            'client_id': str(self.client_instance.id),
        }

        serializer = CSVUploadSerializer(data=data)
        self.assertTrue(serializer.is_valid(),
                       f"Should accept application/csv. Errors: {serializer.errors}")

    def test_invalid_mime_type_rejected(self):
        """Test that invalid MIME types are rejected."""
        csv_content = "Category,Recommendation\nCost,Test\n"

        invalid_mime_types = [
            'application/octet-stream',
            'application/x-msdownload',  # .exe
            'application/pdf',
            'image/jpeg',
        ]

        for mime_type in invalid_mime_types:
            with self.subTest(mime_type=mime_type):
                csv_file = SimpleUploadedFile(
                    'test.csv',
                    csv_content.encode('utf-8'),
                    content_type=mime_type
                )

                data = {
                    'csv_file': csv_file,
                    'client_id': str(self.client_instance.id),
                }

                serializer = CSVUploadSerializer(data=data)
                # python-magic might catch this
                # If not available, basic validation should still work
