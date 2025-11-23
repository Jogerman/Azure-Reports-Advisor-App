#!/bin/bash
# Azure Advisor Reports Platform - Production Cleanup Script
# This script implements the cleanup recommendations from PRODUCTION_CLEANUP_REPORT.md
#
# IMPORTANT: Review PRODUCTION_CLEANUP_REPORT.md before running this script
# Run with: bash cleanup-production.sh --phase <1|2|3>

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to prompt for confirmation
confirm() {
    read -p "$1 [y/N]: " response
    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Phase 1: Critical cleanup (must be done before production)
phase1_critical() {
    print_info "=== PHASE 1: CRITICAL CLEANUP ==="
    print_warning "This phase addresses critical issues that must be fixed before production"
    echo ""

    if ! confirm "Start Phase 1 cleanup?"; then
        print_info "Phase 1 cancelled"
        return
    fi

    print_info "1. Checking for cost_monitoring references..."
    if grep -r "cost_monitoring.encryption" azure_advisor_reports/ 2>/dev/null; then
        print_warning "Found cost_monitoring.encryption references - MANUAL REVIEW REQUIRED"
    else
        print_info "No cost_monitoring.encryption references found"
    fi

    if grep -r "from apps.cost_monitoring" azure_advisor_reports/ 2>/dev/null; then
        print_warning "Found 'from apps.cost_monitoring' imports - MANUAL REVIEW REQUIRED"
    else
        print_info "No cost_monitoring imports found"
    fi

    print_info "2. Removing backup files (.bak)..."
    find . -name "*.bak" -type f -print
    if confirm "Remove these .bak files?"; then
        find . -name "*.bak" -type f -delete
        print_info "Backup files removed"
    fi

    print_warning "3. Manual action required: Fix TODO in frontend/src/pages/SettingsPage.tsx"
    print_warning "   Line 15: Implement proper admin role checking"

    print_info "Phase 1 critical checks complete"
    echo ""
}

# Phase 2: High priority cleanup
phase2_high_priority() {
    print_info "=== PHASE 2: HIGH PRIORITY CLEANUP ==="
    print_warning "This phase removes test files and development artifacts"
    echo ""

    if ! confirm "Start Phase 2 cleanup?"; then
        print_info "Phase 2 cancelled"
        return
    fi

    print_info "Creating backup before cleanup..."
    BACKUP_DIR="cleanup_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    # Remove root test Python files
    print_info "1. Removing root test Python files..."
    TEST_PY_FILES=(
        "csv_processor.py"
        "test_chart_pdf.py"
        "test_optimized_pdf.py"
        "test_pdf_fallback.py"
        "test_pdf_generation.py"
        "test_pdf_render_timing.py"
    )

    for file in "${TEST_PY_FILES[@]}"; do
        if [ -f "$file" ]; then
            print_info "  Moving $file to backup..."
            mv "$file" "$BACKUP_DIR/" 2>/dev/null || print_warning "  Could not move $file"
        fi
    done

    # Remove root test JavaScript files
    print_info "2. Removing root test/debug JavaScript files..."
    TEST_JS_FILES=(
        "debug-app.js"
        "debug-live-app.js"
        "debug-reports-functionality.js"
        "debug-with-existing-chrome.js"
        "test-cost-report.js"
        "test-redesigned-templates.js"
        "test-reports-functionality.js"
        "test_final_optimization.js"
        "generate_final_pdf.js"
    )

    for file in "${TEST_JS_FILES[@]}"; do
        if [ -f "$file" ]; then
            print_info "  Moving $file to backup..."
            mv "$file" "$BACKUP_DIR/" 2>/dev/null || print_warning "  Could not move $file"
        fi
    done

    # Remove test PDF files
    print_info "3. Removing test PDF files..."
    TEST_PDF_FILES=(
        "pdf_test_latest.pdf"
        "playwright_current.pdf"
        "playwright_centered_charts.pdf"
        "playwright_final_optimized.pdf"
        "optimization_verification.pdf"
        "redesigned_report.pdf"
        "test_playwright_charts_fixed.pdf"
    )

    for file in "${TEST_PDF_FILES[@]}"; do
        if [ -f "$file" ]; then
            print_info "  Moving $file to backup..."
            mv "$file" "$BACKUP_DIR/" 2>/dev/null || print_warning "  Could not move $file"
        fi
    done

    # Remove debug/log files
    print_info "4. Removing debug and log files..."
    DEBUG_FILES=(
        "DEBUG_REPORT.json"
        "full_logs.txt"
        "temp_logs.txt"
        "backend_logs.txt"
        "_nul"
    )

    for file in "${DEBUG_FILES[@]}"; do
        if [ -f "$file" ]; then
            print_info "  Moving $file to backup..."
            mv "$file" "$BACKUP_DIR/" 2>/dev/null || print_warning "  Could not move $file"
        fi
    done

    # Remove test HTML files
    print_info "5. Removing test HTML files..."
    if [ -f "redesigned_report.html" ]; then
        mv "redesigned_report.html" "$BACKUP_DIR/" 2>/dev/null
    fi
    if [ -f "test-report.html" ]; then
        mv "test-report.html" "$BACKUP_DIR/" 2>/dev/null
    fi

    # Check for skipped test files
    print_info "6. Checking for skipped test files..."
    if [ -f "frontend/src/components/reports/ReportList.test.tsx.skip" ]; then
        print_warning "  Found: frontend/src/components/reports/ReportList.test.tsx.skip"
        print_warning "  Action required: Fix or remove this test"
    fi
    if [ -f "frontend/src/pages/ReportsPage.test.tsx.skip" ]; then
        print_warning "  Found: frontend/src/pages/ReportsPage.test.tsx.skip"
        print_warning "  Action required: Fix or remove this test"
    fi

    print_info "Phase 2 cleanup complete"
    print_info "Backup created at: $BACKUP_DIR"
    echo ""
}

# Phase 3: Medium priority cleanup (organizational)
phase3_organize() {
    print_info "=== PHASE 3: ORGANIZATIONAL CLEANUP ==="
    print_warning "This phase organizes documentation and scripts"
    echo ""

    if ! confirm "Start Phase 3 cleanup?"; then
        print_info "Phase 3 cancelled"
        return
    fi

    # Create directory structure
    print_info "1. Creating organized directory structure..."
    mkdir -p docs/archive/phase_reports
    mkdir -p docs/architecture
    mkdir -p docs/deployment
    mkdir -p docs/api
    mkdir -p scripts/archive
    mkdir -p scripts/utilities

    # Move phase reports
    print_info "2. Moving phase/agent reports to archive..."
    PHASE_REPORTS=(
        "AGENT_3_IMPLEMENTATION_REPORT.md"
        "PHASE_1_AGENT_4_COMPLETION_REPORT.md"
        "PHASE_1_COMPLETION_SUMMARY.md"
        "PHASE_2_COMPLETION_SUMMARY.md"
        "PHASE_3_COMPLETION_SUMMARY.md"
        "PHASE_4_IMPLEMENTATION_COMPLETE.md"
    )

    for report in "${PHASE_REPORTS[@]}"; do
        if [ -f "$report" ]; then
            print_info "  Moving $report..."
            mv "$report" docs/archive/phase_reports/ 2>/dev/null || print_warning "  Could not move $report"
        fi
    done

    # Move architecture docs
    print_info "3. Organizing architecture documentation..."
    ARCH_DOCS=(
        "AZURE_ADVISOR_V2_ARCHITECTURE.md"
        "AZURE_ADVISOR_V2_SEQUENCE_DIAGRAMS.md"
        "V2_IMPLEMENTATION_PLAN.md"
        "V2_TASK_BREAKDOWN.md"
    )

    for doc in "${ARCH_DOCS[@]}"; do
        if [ -f "$doc" ]; then
            mv "$doc" docs/architecture/ 2>/dev/null || print_warning "  Could not move $doc"
        fi
    done

    # Move old deployment scripts
    print_info "4. Archiving old deployment scripts..."
    OLD_DEPLOY_SCRIPTS=(
        "deploy_v1.3.15.sh"
        "deploy_v1.3.16.sh"
        "deploy_v1.3.17.sh"
        "deploy_celery_fix.sh"
        "deploy_csv_fix_v1.3.20.sh"
    )

    for script in "${OLD_DEPLOY_SCRIPTS[@]}"; do
        if [ -f "$script" ]; then
            mv "$script" scripts/archive/ 2>/dev/null || print_warning "  Could not move $script"
        fi
    done

    # Move utility scripts
    print_info "5. Organizing utility scripts..."
    UTILITY_SCRIPTS=(
        "create_groups.py"
        "diagnose_stuck_reports.py"
        "fix_stuck_reports.py"
        "generate_reports_shell.py"
        "generate_sample_data.py"
        "generate_sample_reports.py"
        "verify_analytics_setup.py"
    )

    for script in "${UTILITY_SCRIPTS[@]}"; do
        if [ -f "$script" ]; then
            mv "$script" scripts/utilities/ 2>/dev/null || print_warning "  Could not move $script"
        fi
    done

    print_info "Phase 3 organization complete"
    echo ""
}

# Show statistics
show_stats() {
    print_info "=== CLEANUP STATISTICS ==="

    print_info "Root Python files: $(find . -maxdepth 1 -name "*.py" -type f | wc -l | tr -d ' ')"
    print_info "Root JavaScript files: $(find . -maxdepth 1 -name "*.js" -type f | wc -l | tr -d ' ')"
    print_info "Root PDF files: $(find . -maxdepth 1 -name "*.pdf" -type f | wc -l | tr -d ' ')"
    print_info "Backup files (.bak): $(find . -name "*.bak" -type f | wc -l | tr -d ' ')"

    if [ -d "docs/archive" ]; then
        print_info "Archived documents: $(find docs/archive -type f | wc -l | tr -d ' ')"
    fi

    if [ -d "scripts/archive" ]; then
        print_info "Archived scripts: $(find scripts/archive -type f | wc -l | tr -d ' ')"
    fi

    echo ""
}

# Main script
main() {
    echo ""
    print_info "Azure Advisor Reports Platform - Production Cleanup Script"
    print_info "========================================================="
    echo ""

    if [ "$1" == "" ]; then
        print_warning "Usage: bash cleanup-production.sh --phase <1|2|3|all|stats>"
        echo ""
        echo "Phases:"
        echo "  1    - Critical cleanup (must be done before production)"
        echo "  2    - High priority cleanup (remove test files)"
        echo "  3    - Medium priority cleanup (organize documentation)"
        echo "  all  - Run all phases"
        echo "  stats - Show current statistics"
        echo ""
        exit 1
    fi

    case "$2" in
        1)
            phase1_critical
            ;;
        2)
            phase2_high_priority
            ;;
        3)
            phase3_organize
            ;;
        all)
            phase1_critical
            phase2_high_priority
            phase3_organize
            show_stats
            ;;
        stats)
            show_stats
            ;;
        *)
            print_error "Invalid phase: $2"
            print_info "Use --phase <1|2|3|all|stats>"
            exit 1
            ;;
    esac

    print_info "Cleanup operations complete!"
    print_warning "Remember to:"
    print_warning "  1. Review PRODUCTION_CLEANUP_REPORT.md for details"
    print_warning "  2. Test thoroughly after cleanup"
    print_warning "  3. Update .dockerignore as recommended"
    print_warning "  4. Commit changes and create PR"
    echo ""
}

main "$@"
