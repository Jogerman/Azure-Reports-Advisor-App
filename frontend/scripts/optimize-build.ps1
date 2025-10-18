# Optimize Build Script for Windows
# Azure Advisor Reports Platform - Frontend Production Build

Write-Host "🚀 Starting production build optimization..." -ForegroundColor Cyan
Write-Host ""

# Set error action preference
$ErrorActionPreference = "Stop"

# Navigate to frontend directory
$frontendPath = Split-Path -Parent $PSScriptRoot
Set-Location $frontendPath

# Clean previous builds
Write-Host "🧹 Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item -Path "build" -Recurse -Force
    Write-Host "   ✓ Removed build directory" -ForegroundColor Green
}

# Install dependencies
Write-Host ""
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
npm ci --only=production
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Dependency installation failed!" -ForegroundColor Red
    exit 1
}
Write-Host "   ✓ Dependencies installed" -ForegroundColor Green

# Run production build
Write-Host ""
Write-Host "🔨 Building production bundle..." -ForegroundColor Yellow
$env:GENERATE_SOURCEMAP = "false"
$env:BUILD_DATE = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "   ✓ Build successful" -ForegroundColor Green

# Analyze bundle size
Write-Host ""
Write-Host "📊 Analyzing bundle size..." -ForegroundColor Yellow

if (Test-Path "build/static/js") {
    $jsFiles = Get-ChildItem -Path "build/static/js" -Filter "*.js"
    $totalSize = 0
    
    foreach ($file in $jsFiles) {
        $sizeKB = [math]::Round($file.Length / 1KB, 2)
        $totalSize += $file.Length
        Write-Host "   $($file.Name): $sizeKB KB" -ForegroundColor Cyan
    }
    
    $totalSizeMB = [math]::Round($totalSize / 1MB, 2)
    Write-Host "   Total JS size: $totalSizeMB MB" -ForegroundColor Cyan
}

# Verify build
Write-Host ""
Write-Host "✅ Verifying build..." -ForegroundColor Yellow
if (Test-Path "build/index.html") {
    Write-Host "   ✓ index.html found" -ForegroundColor Green
    
    $buildSize = (Get-ChildItem -Path "build" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "   ✓ Total build size: $([math]::Round($buildSize, 2)) MB" -ForegroundColor Green
    
    # Check for critical files
    $criticalFiles = @("index.html", "static/js", "static/css", "manifest.json")
    foreach ($file in $criticalFiles) {
        if (Test-Path "build/$file") {
            Write-Host "   ✓ $file present" -ForegroundColor Green
        } else {
            Write-Host "   ⚠ $file missing" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "   ❌ Build failed - index.html not found!" -ForegroundColor Red
    exit 1
}

# Performance recommendations
Write-Host ""
Write-Host "💡 Performance Recommendations:" -ForegroundColor Magenta
if ($buildSize -gt 1) {
    Write-Host "   ⚠ Build size is larger than 1MB. Consider:" -ForegroundColor Yellow
    Write-Host "     - Code splitting" -ForegroundColor Gray
    Write-Host "     - Lazy loading components" -ForegroundColor Gray
    Write-Host "     - Tree shaking unused dependencies" -ForegroundColor Gray
} else {
    Write-Host "   ✓ Build size is optimized (<1MB)" -ForegroundColor Green
}

# Optional: Run bundle analyzer (if installed)
if (Get-Command source-map-explorer -ErrorAction SilentlyContinue) {
    Write-Host ""
    $response = Read-Host "Would you like to analyze the bundle? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "📈 Running bundle analyzer..." -ForegroundColor Cyan
        npm run analyze
    }
}

# Summary
Write-Host ""
Write-Host "🎉 Build optimization complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Test build locally: npm run serve:prod" -ForegroundColor Gray
Write-Host "  2. Run Lighthouse audit: npm run lighthouse" -ForegroundColor Gray
Write-Host "  3. Deploy to Azure: docker build -f Dockerfile.prod ." -ForegroundColor Gray
Write-Host ""
