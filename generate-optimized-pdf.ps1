# PowerShell Script to Generate Optimized PDF
# Azure Advisor Reports - PDF Optimization

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "Azure Advisor Reports - PDF Optimization Generator" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Change to the Django project directory
$projectDir = Join-Path $PSScriptRoot "azure_advisor_reports"
Set-Location $projectDir

Write-Host "Project directory: $projectDir" -ForegroundColor Yellow
Write-Host ""

# Check if virtual environment exists
$venvPath = Join-Path $projectDir "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "ERROR: Virtual environment not found at $venvPath" -ForegroundColor Red
    Write-Host "Please create a virtual environment first:" -ForegroundColor Yellow
    Write-Host "  python -m venv venv" -ForegroundColor White
    exit 1
}

# Activate virtual environment
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
Write-Host "Activating virtual environment..." -ForegroundColor Green
& $activateScript

# Verify Django is available
Write-Host "Checking Django installation..." -ForegroundColor Green
$djangoVersion = python -c "import django; print(django.get_version())" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Django is not installed in the virtual environment" -ForegroundColor Red
    Write-Host "Please install requirements:" -ForegroundColor Yellow
    Write-Host "  pip install -r requirements.txt" -ForegroundColor White
    exit 1
}
Write-Host "Django version: $djangoVersion" -ForegroundColor White
Write-Host ""

# Create temporary Python script
$tempScript = @"
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings')
django.setup()

from apps.reports.models import Client
from apps.reports.services.report_generator import ReportGenerator

def main():
    print("\n" + "=" * 80)
    print("Generating Optimized PDF")
    print("=" * 80 + "\n")

    # Get client
    try:
        client = Client.objects.get(company_name='Autozama')
        print(f"Client found: {client.company_name}")
    except Client.DoesNotExist:
        print("ERROR: Autozama client not found in database!")
        print("\nAvailable clients:")
        for c in Client.objects.all():
            print(f"  - {c.company_name}")
        return 1

    # Generate PDF
    print("\nGenerating PDF with optimizations...")
    print("  - Reduced margins (12mm/10mm)")
    print("  - Compact spacing (50% reduction)")
    print("  - Optimized charts (200px height)")
    print("  - Compressed tables")
    print("")

    generator = ReportGenerator()

    try:
        output_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_file = 'playwright_optimized.pdf'

        pdf_path = generator.generate_executive_report(
            client=client,
            output_filename=output_file
        )

        print("\n" + "=" * 80)
        print("SUCCESS: PDF Generated!")
        print("=" * 80)
        print(f"\nLocation: {pdf_path}")

        # Get file size
        size_bytes = os.path.getsize(pdf_path)
        size_mb = size_bytes / (1024 * 1024)
        size_kb = size_bytes / 1024

        print(f"Size: {size_mb:.2f} MB ({size_kb:.0f} KB)")

        # Compare with original
        original_path = os.path.join(output_dir, 'playwright_current.pdf')
        if os.path.exists(original_path):
            original_size_mb = os.path.getsize(original_path) / (1024 * 1024)
            reduction = ((original_size_mb - size_mb) / original_size_mb) * 100

            print(f"\nComparison:")
            print(f"  Original:  {original_size_mb:.2f} MB")
            print(f"  Optimized: {size_mb:.2f} MB")
            print(f"  Reduction: {reduction:.1f}%")

            if size_mb <= 0.7:
                print(f"\n✅ SUCCESS: Target file size achieved (≤700 KB)!")
            elif reduction >= 30:
                print(f"\n✅ GOOD: File size reduced by >30%")
            else:
                print(f"\n⚠️  NOTE: Further optimization may be needed")
        else:
            print(f"\nNOTE: Original PDF not found for comparison")
            print(f"  Expected at: {original_path}")

        print("\n" + "=" * 80)
        print("Next steps:")
        print("  1. Open the PDF and verify quality")
        print("  2. Compare with playwright_current.pdf")
        print("  3. Check that all charts render correctly")
        print("=" * 80 + "\n")

        return 0

    except Exception as e:
        print(f"\nERROR: Failed to generate PDF")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
"@

# Write temporary script
$tempScriptPath = Join-Path $PSScriptRoot "temp_generate_pdf.py"
$tempScript | Out-File -FilePath $tempScriptPath -Encoding UTF8

# Run the script
Write-Host "Executing PDF generation..." -ForegroundColor Green
Write-Host ""
python $tempScriptPath

# Store exit code
$exitCode = $LASTEXITCODE

# Cleanup temporary script
Remove-Item $tempScriptPath -ErrorAction SilentlyContinue

# Return to original directory
Set-Location $PSScriptRoot

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "PDF generation completed successfully!" -ForegroundColor Green
    Write-Host "Check the file: playwright_optimized.pdf" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "PDF generation failed. Please check the error messages above." -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

exit $exitCode
