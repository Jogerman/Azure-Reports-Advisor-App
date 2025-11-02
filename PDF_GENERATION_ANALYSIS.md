# PDF Generation System Analysis - Azure Advisor Reports Platform

## Executive Summary

The Azure Advisor Reports Platform implements a dual PDF generation system with Playwright as the current active method and WeasyPrint as a fallback. The system is fully configurable and supports seamless switching between engines.

---

## 1. Current Active PDF Generation Method

### Active Engine: Playwright
- Status: Primary/Default
- Configuration: PDF_ENGINE = 'playwright' (in settings.py, line 359)
- Method: Headless browser-based PDF generation using Playwright/Chromium
- Advantages:
  - Full Chart.js support with real rendering
  - Modern CSS3 support
  - Dynamic content rendering
  - Professional typography
  - Page headers/footers with page numbers

### Configuration Location
File: azure_advisor_reports/settings.py

PDF_ENGINE = config('PDF_ENGINE', default='playwright').lower()

PLAYWRIGHT_PDF_OPTIONS = {
    'format': 'A4',
    'print_background': True,
    'display_header_footer': True,
    'margin': {
        'top': '25mm',
        'right': '15mm',
        'bottom': '25mm',
        'left': '15mm',
    },
    'prefer_css_page_size': False,
    'timeout': 30000,
}

PDF_WAIT_FOR_CHARTS = config('PDF_WAIT_FOR_CHARTS', default=True, cast=bool)
PDF_WAIT_FOR_FONTS = config('PDF_WAIT_FOR_FONTS', default=True, cast=bool)
PDF_HEADLESS_BROWSER = config('PDF_HEADLESS_BROWSER', default=True, cast=bool)

---

## 2. Playwright Implementation

### Core Service Implementation
File: apps/reports/services/pdf_service.py

Key Classes:
1. PlaywrightPDFGenerator (Async)
2. SyncPlaywrightPDFGenerator (Sync Wrapper)
3. generate_pdf() (Convenience function)

Features:
- Async context manager for browser lifecycle
- Chart.js detection and waiting
- Font loading detection
- Print CSS optimization
- Viewport optimization: 1100x1400px
- Scale factor: 0.95

Browser Arguments:
- --disable-web-security (Allow CORS)
- --no-sandbox (Docker requirement)
- --disable-dev-shm-usage (Resource optimization)

---

## 3. Report Types and Generators

All report types use PDF_ENGINE setting:

1. DetailedReportGenerator
   - Template: reports/detailed.html
   - Audience: Technical teams

2. ExecutiveReportGenerator
   - Template: reports/executive_enhanced.html
   - Audience: Executives

3. CostOptimizationReportGenerator
   - Template: reports/cost_enhanced.html
   - Audience: Finance teams

4. SecurityReportGenerator
   - Template: reports/security_enhanced.html
   - Audience: Security teams

5. OperationsReportGenerator
   - Template: reports/operations.html
   - Audience: Operations teams

---

## 4. API Integration

### Report Generation Endpoint
POST /api/v1/reports/{id}/generate/

Request:
{
    "format": "both",      // html, pdf, or both
    "async": true          // true for async
}

### Async Flow (Recommended)
1. API receives request
2. Triggers Celery task: generate_report.delay()
3. Returns task_id for polling
4. Client polls: GET /api/v1/reports/{id}/status/?task_id={task_id}
5. Task updates report with file paths
6. Client downloads via: GET /api/v1/reports/{id}/download/pdf/

### Celery Task
File: apps/reports/tasks.py
- Task: generate_report()
- Max retries: 3
- Retry delay: 60 seconds (exponential backoff)

---

## 5. How to Switch PDF Generators

### Method 1: Environment Variable (Recommended)
PDF_ENGINE=playwright    # Use Playwright
PDF_ENGINE=weasyprint    # Use WeasyPrint

### Method 2: Settings File
File: settings.py (line 359)
PDF_ENGINE = config('PDF_ENGINE', default='playwright').lower()

### Decision Logic
Location: BaseReportGenerator.generate_pdf() (base.py, line 288)

if pdf_engine == 'playwright':
    return self.generate_pdf_with_playwright()
else:
    return self.generate_pdf_with_weasyprint()

---

## 6. WeasyPrint Implementation (Fallback)

Method: generate_pdf_with_weasyprint()
File: apps/reports/generators/base.py (lines 400-485)

Differences:
- Uses WeasyPrint library (not headless browser)
- No Chart.js support
- Faster for simple reports
- Lower memory footprint
- Uses PDF-specific templates

---

## 7. File Storage

Storage Backend: Azure Blob Storage (via Django default_storage)

File Organization:
reports/
├── html/{report_id}_{report_type}.html
└── pdf/{report_id}_{report_type}.pdf

Flow:
1. Generate PDF to temporary file
2. Read temporary file to bytes
3. Upload to Azure Blob Storage
4. Clean up temporary file
5. Return relative path for Django FileField

---

## 8. Docker Configuration

Installation:
File: Dockerfile (lines 77-79)
RUN python -m playwright install chromium

System Dependencies (Playwright):
- libnss3, libnspr4, libatk1.0-0
- libatk-bridge2.0-0, libcups2, libdrm2
- libdbus-1-3, libxkbcommon0, libxcomposite1
- libxdamage1, libxfixes3, libxrandr2
- libgbm1, libasound2, libatspi2.0-0

Memory Requirements:
- Minimum: 2GB RAM
- Recommended: 4GB RAM

---

## 9. Performance

Generation Times:
- Executive Report (5 charts): ~3.5 seconds
- Cost Report (8 charts): ~4.2 seconds
- Security Report (3 charts): ~2.8 seconds
- Detailed Report: ~1.5-2.5 seconds

Resource Usage:
- Docker Image: ~680MB
- Memory per PDF: ~300-500MB
- CPU: 2-3 cores recommended

---

## 10. Key Files

Core Service:
- pdf_service.py - Playwright PDF generator
- base.py - BaseReportGenerator (PDF methods)
- detailed.py - Detailed report
- executive.py - Executive report
- cost.py - Cost report
- security.py - Security report
- operations.py - Operations report
- views.py - API endpoints
- tasks.py - Celery tasks

Configuration:
- settings.py - PDF_ENGINE and options
- Dockerfile - Chromium installation
- requirements.txt - playwright==1.40.0

Documentation:
- PLAYWRIGHT_PDF_GUIDE.md - User guide

---

## 11. Error Handling

Common Issues:

1. Playwright Not Installed
   Solution: pip install playwright && playwright install chromium

2. Charts Not Rendering
   Solution: Ensure PDF_WAIT_FOR_CHARTS=True

3. Timeout Errors
   Solution: Increase timeout to 60000ms

4. Memory Errors
   Solution: Increase Docker memory to 2GB+

5. Chromium Not Found
   Solution: playwright install chromium --with-deps

Logging:
- File: logs/django.log
- Logger: apps.reports.services.pdf_service

---

## 12. Migration Guide

From WeasyPrint to Playwright:

Step 1: Update Environment
PDF_ENGINE=playwright

Step 2: Rebuild Docker
docker-compose build backend
docker-compose up -d

Step 3: Test Generation
POST /api/v1/reports/{id}/generate/

Step 4: Monitor Logs
docker logs backend | grep playwright

Step 5: Rollback if Needed
PDF_ENGINE=weasyprint

---

## 13. Summary

Current Active Method: Playwright with Chart.js support
Location: apps/reports/services/pdf_service.py
Configuration: PDF_ENGINE = 'playwright' in settings.py
Report Types: 5 types (Detailed, Executive, Cost, Security, Operations)
API Endpoint: POST /api/v1/reports/{id}/generate/
Async Processing: Celery with retry logic
Storage: Azure Blob Storage
Performance: 2-4 seconds per report
Fallback: WeasyPrint available via engine switch

