#!/usr/bin/env python
"""
Quick verification script for Analytics module setup.

Run this script to verify that all Analytics components are properly configured.

Usage:
    python verify_analytics_setup.py
"""

import os
import sys
from pathlib import Path

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_check(name, passed, details=None):
    symbol = f"{Colors.GREEN}✓" if passed else f"{Colors.RED}✗"
    status = f"{Colors.GREEN}PASS" if passed else f"{Colors.RED}FAIL"
    print(f"{symbol} {name:.<50} {status}{Colors.RESET}")
    if details and not passed:
        print(f"  {Colors.YELLOW}→ {details}{Colors.RESET}")

def check_file_exists(filepath):
    """Check if a file exists."""
    return Path(filepath).exists()

def main():
    print_header("Analytics Module Verification")

    base_path = Path("azure_advisor_reports/apps/analytics")
    checks = []

    # 1. Core Files
    print(f"{Colors.BOLD}1. Core Files{Colors.RESET}")
    files = {
        "models.py": base_path / "models.py",
        "services.py": base_path / "services.py",
        "views.py": base_path / "views.py",
        "urls.py": base_path / "urls.py",
        "serializers.py": base_path / "serializers.py",
    }

    for name, path in files.items():
        exists = check_file_exists(path)
        print_check(f"Core file: {name}", exists, f"Missing: {path}")
        checks.append(exists)

    # 2. New Implementation Files
    print(f"\n{Colors.BOLD}2. New Implementation Files{Colors.RESET}")
    new_files = {
        "middleware.py": base_path / "middleware.py",
        "tasks.py": base_path / "tasks.py",
        "celery_config.py": base_path / "celery_config.py",
    }

    for name, path in new_files.items():
        exists = check_file_exists(path)
        print_check(f"New file: {name}", exists, f"Missing: {path}")
        checks.append(exists)

    # 3. Test Files
    print(f"\n{Colors.BOLD}3. Test Files{Colors.RESET}")
    test_files = {
        "test_new_endpoints.py": base_path / "tests/test_new_endpoints.py",
        "test_middleware.py": base_path / "tests/test_middleware.py",
        "test_tasks.py": base_path / "tests/test_tasks.py",
    }

    for name, path in test_files.items():
        exists = check_file_exists(path)
        print_check(f"Test file: {name}", exists, f"Missing: {path}")
        checks.append(exists)

    # 4. Documentation Files
    print(f"\n{Colors.BOLD}4. Documentation Files{Colors.RESET}")
    doc_files = {
        "README.md": base_path / "README.md",
        "ANALYTICS_API_DOCUMENTATION.md": base_path / "ANALYTICS_API_DOCUMENTATION.md",
        "Completion Report": Path("ANALYTICS_MODULE_COMPLETION_REPORT.md"),
    }

    for name, path in doc_files.items():
        exists = check_file_exists(path)
        print_check(f"Documentation: {name}", exists, f"Missing: {path}")
        checks.append(exists)

    # 5. Management Commands
    print(f"\n{Colors.BOLD}5. Management Commands{Colors.RESET}")
    cmd_file = base_path / "management/commands/initialize_analytics.py"
    exists = check_file_exists(cmd_file)
    print_check("initialize_analytics command", exists, f"Missing: {cmd_file}")
    checks.append(exists)

    # 6. File Content Verification
    print(f"\n{Colors.BOLD}6. Implementation Verification{Colors.RESET}")

    # Check services.py for new methods
    services_path = base_path / "services.py"
    if check_file_exists(services_path):
        content = services_path.read_text()
        has_user_activity = "get_user_activity_detailed" in content
        has_activity_summary = "get_activity_summary_aggregated" in content
        has_system_health = "get_system_health" in content

        print_check("Service: get_user_activity_detailed()", has_user_activity)
        print_check("Service: get_activity_summary_aggregated()", has_activity_summary)
        print_check("Service: get_system_health()", has_system_health)
        checks.extend([has_user_activity, has_activity_summary, has_system_health])
    else:
        print_check("Service methods", False, "services.py not found")
        checks.extend([False, False, False])

    # Check views.py for new views
    views_path = base_path / "views.py"
    if check_file_exists(views_path):
        content = views_path.read_text()
        has_user_activity = "UserActivityView" in content
        has_activity_summary = "ActivitySummaryView" in content
        has_system_health = "SystemHealthView" in content

        print_check("View: UserActivityView", has_user_activity)
        print_check("View: ActivitySummaryView", has_activity_summary)
        print_check("View: SystemHealthView", has_system_health)
        checks.extend([has_user_activity, has_activity_summary, has_system_health])
    else:
        print_check("View classes", False, "views.py not found")
        checks.extend([False, False, False])

    # Check urls.py for new routes
    urls_path = base_path / "urls.py"
    if check_file_exists(urls_path):
        content = urls_path.read_text()
        has_user_activity = "user-activity/" in content
        has_activity_summary = "activity-summary/" in content
        has_system_health = "system-health/" in content

        print_check("Route: user-activity/", has_user_activity)
        print_check("Route: activity-summary/", has_activity_summary)
        print_check("Route: system-health/", has_system_health)
        checks.extend([has_user_activity, has_activity_summary, has_system_health])
    else:
        print_check("URL routes", False, "urls.py not found")
        checks.extend([False, False, False])

    # Summary
    print_header("Verification Summary")

    total = len(checks)
    passed = sum(checks)
    failed = total - passed
    percentage = (passed / total * 100) if total > 0 else 0

    print(f"Total Checks: {total}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
    print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
    print(f"Success Rate: {percentage:.1f}%\n")

    if percentage == 100:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All checks passed! Analytics module is ready.{Colors.RESET}")
        print(f"\n{Colors.BLUE}Next steps:{Colors.RESET}")
        print("1. Add middleware to settings.py")
        print("2. Configure Celery Beat schedule")
        print("3. Run: python manage.py initialize_analytics")
        print("4. Start Celery workers")
        return 0
    elif percentage >= 80:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠ Most checks passed, but review failures above.{Colors.RESET}")
        return 1
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Multiple checks failed. Review implementation.{Colors.RESET}")
        return 2

if __name__ == "__main__":
    sys.exit(main())
