"""
Report generators for Azure Advisor Reports Platform.

This package contains the report generation logic for all report types.
"""

from .base import BaseReportGenerator
from .detailed import DetailedReportGenerator
from .executive import ExecutiveReportGenerator
from .cost import CostOptimizationReportGenerator
from .security import SecurityReportGenerator
from .operations import OperationsReportGenerator


def get_report_generator(report):
    """
    Factory function to get the appropriate report generator for a report type.

    Args:
        report: Report instance with report_type attribute

    Returns:
        Instance of appropriate ReportGenerator subclass

    Raises:
        ValueError: If report_type is not recognized
    """
    generators = {
        'detailed': DetailedReportGenerator,
        'executive': ExecutiveReportGenerator,
        'cost': CostOptimizationReportGenerator,
        'security': SecurityReportGenerator,
        'operations': OperationsReportGenerator,
    }

    generator_class = generators.get(report.report_type)
    if not generator_class:
        raise ValueError(f"Unknown report type: {report.report_type}")

    return generator_class(report)


# Alias for compatibility
get_generator_for_report = get_report_generator


__all__ = [
    'BaseReportGenerator',
    'DetailedReportGenerator',
    'ExecutiveReportGenerator',
    'CostOptimizationReportGenerator',
    'SecurityReportGenerator',
    'OperationsReportGenerator',
    'get_report_generator',
]
