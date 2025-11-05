# Playwright PDF Generation System - Complete Guide

## Overview

The Azure Advisor Reports Platform now includes a professional PDF generation system powered by Playwright.

### Key Features

- Full Chart.js Support
- Modern CSS3 Complete Support  
- Professional Headers/Footers with Page Numbers
- Automatic Print Optimization
- Both Async and Sync APIs
- Fully Docker Compatible

## Installation

### 1. Install Dependencies

Dependencies are in requirements.txt:
- playwright==1.40.0
- greenlet==3.0.1

Install:
```bash
pip install -r requirements.txt
playwright install chromium --with-deps
```

### 2. Verify

```bash
python -c "from playwright.sync_api import sync_playwright; print(OK)"
```

## Configuration

### Environment Variables

```bash
PDF_ENGINE=playwright
PDF_WAIT_FOR_CHARTS=True
PDF_WAIT_FOR_FONTS=True
```

## Usage

### Automatic

```python
from apps.reports.generators.executive import ExecutiveReportGenerator

generator = ExecutiveReportGenerator(report)
pdf_path = generator.generate_pdf()
```

### Direct API

```python
from apps.reports.services.pdf_service import SyncPlaywrightPDFGenerator

generator = SyncPlaywrightPDFGenerator()
pdf_path = generator.generate_pdf_from_html(
    html_content=html,
    output_path=path,
)
```

## Docker

```bash
docker-compose build backend
docker-compose up -d
```

Requires 2GB RAM minimum.

## Troubleshooting

### Playwright not installed
```bash
playwright install chromium --with-deps
```

### Charts not rendering
Ensure wait_for_charts=True

### Timeout errors
Increase timeout to 60000ms

### Memory errors  
Increase Docker memory to 2GB

## Migration from WeasyPrint

1. Set PDF_ENGINE=playwright in .env
2. Rebuild Docker: docker-compose build backend
3. Test report generation
4. Rollback if needed: PDF_ENGINE=weasyprint

Both engines supported simultaneously.

## Performance

- Executive Report: ~3.5s (5 charts)
- Cost Report: ~4.2s (8 charts)
- Security Report: ~2.8s (3 charts)

Docker image: ~680MB (vs 520MB with WeasyPrint)

## Best Practices

1. Use headless mode in production
2. Set appropriate timeouts
3. Monitor memory (2GB min)
4. Cache generated PDFs
5. Use background tasks for large reports

## Architecture

Files Updated:
- requirements.txt (Playwright deps)
- apps/reports/services/pdf_service.py (new)
- apps/reports/generators/base.py (updated)
- settings.py (PDF_ENGINE config)
- Dockerfile (Chromium install)
- Dockerfile.prod (Chromium install)

Version: 1.0.0
Last Updated: 2025-10-25
