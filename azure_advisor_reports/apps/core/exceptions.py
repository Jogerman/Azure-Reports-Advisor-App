"""
Custom exception handlers for the API.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent error format.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        custom_response_data = {
            'status': 'error',
            'message': 'An error occurred',
            'errors': {}
        }

        # Handle validation errors
        if hasattr(response.data, 'items'):
            custom_response_data['errors'] = response.data
            if 'non_field_errors' in response.data:
                custom_response_data['message'] = response.data['non_field_errors'][0]
            else:
                # Get first error message
                for field, errors in response.data.items():
                    if isinstance(errors, list) and errors:
                        custom_response_data['message'] = f"{field}: {errors[0]}"
                        break
        elif hasattr(response.data, 'get'):
            if 'detail' in response.data:
                custom_response_data['message'] = response.data['detail']
            else:
                custom_response_data['errors'] = response.data

        # Log the error
        logger.error(f"API Error: {response.status_code} - {custom_response_data['message']}")

        response.data = custom_response_data

    return response


class BusinessLogicError(Exception):
    """Custom exception for business logic errors."""

    def __init__(self, message, code=None):
        self.message = message
        self.code = code or 'business_logic_error'
        super().__init__(self.message)


class FileProcessingError(Exception):
    """Custom exception for file processing errors."""

    def __init__(self, message, code=None):
        self.message = message
        self.code = code or 'file_processing_error'
        super().__init__(self.message)


class ReportGenerationError(Exception):
    """Custom exception for report generation errors."""

    def __init__(self, message, code=None):
        self.message = message
        self.code = code or 'report_generation_error'
        super().__init__(self.message)