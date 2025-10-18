# ============================================
# Script de Verificación Rápida - Ambiente Local
# Azure Advisor Reports Platform
# ============================================

Write-Host "`n=== Verificación de Ambiente Local ===" -ForegroundColor Cyan

# 1. Docker Services
Write-Host "`n🐳 Docker Services:" -ForegroundColor Yellow
docker-compose ps

# 2. Archivos de Configuración
Write-Host "`n📄 Archivos de Configuración:" -ForegroundColor Yellow

if (Test-Path "azure_advisor_reports\.env") {
    Write-Host "   ✅ Backend .env existe" -ForegroundColor Green
} else {
    Write-Host "   ❌ Backend .env NO existe" -ForegroundColor Red
}

if (Test-Path "frontend\.env.local") {
    Write-Host "   ✅ Frontend .env.local existe" -ForegroundColor Green
} else {
    Write-Host "   ❌ Frontend .env.local NO existe" -ForegroundColor Red
}

# 3. Servidores
Write-Host "`n🖥️  Servidores:" -ForegroundColor Yellow

$django = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($django) {
    Write-Host "   ✅ Django corriendo en puerto 8000" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Django NO está corriendo" -ForegroundColor Yellow
}

$react = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($react) {
    Write-Host "   ✅ React corriendo en puerto 3000" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  React NO está corriendo" -ForegroundColor Yellow
}

# 4. Health Check
if ($django) {
    Write-Host "`n🏥 Health Check:" -ForegroundColor Yellow
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:8000/api/health/" -Method Get -TimeoutSec 5
        Write-Host "   ✅ Backend: $($health.status)" -ForegroundColor Green
        Write-Host "      Database: $($health.database)" -ForegroundColor Gray
        Write-Host "      Cache: $($health.cache)" -ForegroundColor Gray
    } catch {
        Write-Host "   ❌ Backend no responde" -ForegroundColor Red
    }
}

# 5. URLs
Write-Host "`n🌐 URLs Importantes:" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "   Backend API: http://localhost:8000/api" -ForegroundColor White
Write-Host "   Admin Panel: http://localhost:8000/admin" -ForegroundColor White
Write-Host "   Health Check: http://localhost:8000/api/health/" -ForegroundColor White

Write-Host "`n=============================================`n" -ForegroundColor Cyan
