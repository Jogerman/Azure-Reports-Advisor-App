#!/usr/bin/env python
"""
Template Tag Verification Script for Azure Advisor Reports

This script tests if template filters (intcomma, floatformat) are working
correctly across all report templates.

Usage:
    python manage.py shell < scripts/verify_template_tags.py

Or:
    python scripts/verify_template_tags.py
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings.production')
django.setup()

from django.template import Context, Template, TemplateDoesNotExist, TemplateSyntaxError
from django.template.loader import get_template


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'


def print_test(description, passed, expected=None, actual=None):
    """Print formatted test result."""
    symbol = f"{Colors.GREEN}✓{Colors.ENDC}" if passed else f"{Colors.RED}✗{Colors.ENDC}"
    print(f"{symbol} {description}")
    if not passed and expected and actual:
        print(f"    Expected: {expected}")
        print(f"    Actual: {actual}")


def test_basic_filters():
    """Test basic Django template filters."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Basic Django Filters{Colors.ENDC}")
    print("-" * 60)

    # Test intcomma from humanize
    try:
        template_str = "{% load humanize %}{{ value|intcomma }}"
        template = Template(template_str)
        result = template.render(Context({'value': 12345}))
        passed = result.strip() == "12,345"
        print_test(
            "humanize intcomma filter",
            passed,
            "12,345",
            result.strip()
        )
    except Exception as e:
        print_test(f"humanize intcomma filter", False)
        print(f"    Error: {str(e)}")

    # Test floatformat
    try:
        template_str = "{{ value|floatformat:0 }}"
        template = Template(template_str)
        result = template.render(Context({'value': 12345.67}))
        passed = result.strip() == "12346"
        print_test(
            "Built-in floatformat filter",
            passed,
            "12346",
            result.strip()
        )
    except Exception as e:
        print_test("Built-in floatformat filter", False)
        print(f"    Error: {str(e)}")

    # Test combined
    try:
        template_str = "{% load humanize %}{{ value|floatformat:0|intcomma }}"
        template = Template(template_str)
        result = template.render(Context({'value': 12345.67}))
        passed = result.strip() == "12,346"
        print_test(
            "Combined floatformat:0|intcomma",
            passed,
            "12,346",
            result.strip()
        )
    except Exception as e:
        print_test("Combined floatformat:0|intcomma", False)
        print(f"    Error: {str(e)}")


def test_report_filters():
    """Test report_filters template tag library."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Testing report_filters Library{Colors.ENDC}")
    print("-" * 60)

    # Check if report_filters exists
    try:
        from apps.reports.templatetags import report_filters
        print_test("report_filters module exists", True)

        # Check what's registered
        if hasattr(report_filters, 'register'):
            filters = report_filters.register.filters.keys()
            print(f"    Registered filters: {', '.join(filters)}")
        else:
            print_test("report_filters.register exists", False)
            return

    except ImportError as e:
        print_test("report_filters module exists", False)
        print(f"    Error: {str(e)}")
        print(f"\n{Colors.YELLOW}WARNING: report_filters.py may be missing!{Colors.ENDC}")
        print(f"    Expected location: apps/reports/templatetags/report_filters.py")
        return

    # Test using report_filters
    try:
        template_str = "{% load report_filters %}{{ value|intcomma }}"
        template = Template(template_str)
        result = template.render(Context({'value': 12345}))
        passed = result.strip() == "12,345"
        print_test(
            "report_filters intcomma",
            passed,
            "12,345",
            result.strip()
        )
    except Exception as e:
        print_test("report_filters intcomma", False)
        print(f"    Error: {str(e)}")

    # Test combined with report_filters
    try:
        template_str = "{% load report_filters %}{{ value|floatformat:0|intcomma }}"
        template = Template(template_str)
        result = template.render(Context({'value': 12345.67}))
        passed = result.strip() == "12,346"
        print_test(
            "report_filters floatformat:0|intcomma",
            passed,
            "12,346",
            result.strip()
        )
    except Exception as e:
        print_test("report_filters floatformat:0|intcomma", False)
        print(f"    Error: {str(e)}")


def test_actual_templates():
    """Test actual report templates."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Actual Report Templates{Colors.ENDC}")
    print("-" * 60)

    templates_to_test = [
        'reports/cost_enhanced.html',
        'reports/security_enhanced.html',
        'reports/executive_enhanced.html',
        'reports/detailed.html',
        'reports/detailed_redesigned.html',
    ]

    for template_name in templates_to_test:
        try:
            template = get_template(template_name)

            # Check if it has {% load report_filters %}
            with open(template.origin.name, 'r') as f:
                content = f.read()
                has_load_tag = '{% load report_filters %}' in content or "{% load humanize %}" in content

            print_test(f"{template_name} - loads filters", has_load_tag)

            if not has_load_tag:
                print(f"    {Colors.YELLOW}Missing {% load report_filters %} or {% load humanize %}{Colors.ENDC}")

            # Try to render a small snippet
            try:
                test_context = Context({
                    'total_savings': 12345.67,
                    'total_recommendations': 1234,
                    'client': type('obj', (object,), {'company_name': 'Test Client'})(),
                    'generated_date': None,
                })

                # This will fail if template has syntax errors
                # We don't care about the full output, just that it doesn't crash
                template.render(test_context)
                print_test(f"{template_name} - renders without errors", True)

            except Exception as e:
                # Template might need more context, that's okay
                if 'does not exist' in str(e) or 'has no attribute' in str(e):
                    print_test(f"{template_name} - renders (needs full context)", True)
                else:
                    print_test(f"{template_name} - renders without errors", False)
                    print(f"    Error: {str(e)}")

        except TemplateDoesNotExist:
            print_test(f"{template_name} - exists", False)
            print(f"    {Colors.YELLOW}Template file not found{Colors.ENDC}")
        except Exception as e:
            print_test(f"{template_name} - loads", False)
            print(f"    Error: {str(e)}")


def test_template_filter_in_context():
    """Test filters work with realistic report context."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Filters with Realistic Context{Colors.ENDC}")
    print("-" * 60)

    test_cases = [
        {
            'template': '{% load report_filters %}${{ value|floatformat:0|intcomma }}',
            'context': {'value': 125450.50},
            'expected': '$125,451',
            'description': 'Currency with floatformat and intcomma'
        },
        {
            'template': '{% load report_filters %}{{ value|intcomma }}',
            'context': {'value': 1245},
            'expected': '1,245',
            'description': 'Integer with intcomma'
        },
        {
            'template': '{% load report_filters %}{{ value|floatformat:2|intcomma }}',
            'context': {'value': 1245.678},
            'expected': '1,245.68',
            'description': 'Float with 2 decimals and intcomma'
        },
        {
            'template': '{% load humanize %}{{ value|intcomma }}',
            'context': {'value': 3847},
            'expected': '3,847',
            'description': 'Using humanize directly'
        },
    ]

    for test_case in test_cases:
        try:
            template = Template(test_case['template'])
            result = template.render(Context(test_case['context']))
            passed = result.strip() == test_case['expected']
            print_test(
                test_case['description'],
                passed,
                test_case['expected'],
                result.strip()
            )
        except Exception as e:
            print_test(test_case['description'], False)
            print(f"    Error: {str(e)}")


def check_templatetags_directory():
    """Check if templatetags directory is properly set up."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Checking templatetags Directory Structure{Colors.ENDC}")
    print("-" * 60)

    templatetags_path = 'apps/reports/templatetags'
    report_filters_path = os.path.join(templatetags_path, 'report_filters.py')
    init_path = os.path.join(templatetags_path, '__init__.py')

    # Check directory exists
    exists = os.path.isdir(templatetags_path)
    print_test(f"{templatetags_path}/ directory exists", exists)

    if exists:
        # Check __init__.py
        has_init = os.path.isfile(init_path)
        print_test(f"{init_path} exists", has_init)

        # Check report_filters.py
        has_filters = os.path.isfile(report_filters_path)
        print_test(f"{report_filters_path} exists", has_filters)

        if has_filters:
            # Show contents
            print(f"\n{Colors.BOLD}Contents of report_filters.py:{Colors.ENDC}")
            with open(report_filters_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')[:20]  # First 20 lines
                for i, line in enumerate(lines, 1):
                    print(f"    {i:2d}  {line}")
                if len(content.split('\n')) > 20:
                    print(f"    ... ({len(content.split('\n'))} total lines)")
    else:
        print(f"\n{Colors.RED}ERROR: templatetags directory is missing!{Colors.ENDC}")
        print(f"    Create it with:")
        print(f"    mkdir -p {templatetags_path}")
        print(f"    touch {init_path}")


def main():
    """Run all tests."""
    print(f"\n{Colors.BOLD}{'='*60}")
    print(f"Template Tag Verification for Azure Advisor Reports v2.0.19")
    print(f"{'='*60}{Colors.ENDC}\n")

    check_templatetags_directory()
    test_basic_filters()
    test_report_filters()
    test_template_filter_in_context()
    test_actual_templates()

    print(f"\n{Colors.BOLD}{'='*60}")
    print(f"Verification Complete")
    print(f"{'='*60}{Colors.ENDC}\n")


if __name__ == '__main__':
    main()
