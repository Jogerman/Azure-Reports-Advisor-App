# ============================================
# Script para Detener Ambiente de Desarrollo
# Azure Advisor Reports Platform
# ============================================

Write-Host "`n=== Deteniendo Ambiente de Desarrollo ===" -ForegroundColor Cyan

# Detener procesos en puertos 8000 y 3000
Write-Host "`n1️⃣  Deteniendo servidores..." -ForegroundColor Yellow

# Detener Django (puerto 8000)
$django = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($django) {
    $processId = $django.OwningProcess
    Write-Host "   🔴 Deteniendo Django (PID: $processId)..." -ForegroundColor Gray
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    Write-Host "   ✅ Django detenido" -ForegroundColor Green
} else {
    Write-Host "   ⏭️  Django no estaba corriendo" -ForegroundColor Gray
}

# Detener React (puerto 3000)
$react = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($react) {
    $processId = $react.OwningProcess
    Write-Host "   🔴 Deteniendo React (PID: $processId)..." -ForegroundColor Gray
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    Write-Host "   ✅ React detenido" -ForegroundColor Green
} else {
    Write-Host "   ⏭️  React no estaba corriendo" -ForegroundColor Gray
}

# Detener contenedores Docker
Write-Host "`n2️⃣  Deteniendo Docker containers..." -ForegroundColor Yellow
docker-compose stop

Write-Host "`n" + "="*50 -ForegroundColor Cyan
Write-Host "✅ AMBIENTE DETENIDO" -ForegroundColor Green
Write-Host "="*50 -ForegroundColor Cyan

Write-Host "`n📝 Opciones:" -ForegroundColor Yellow
Write-Host "   Para iniciar de nuevo: .\start-dev.ps1" -ForegroundColor White
Write-Host "   Para limpiar todo: docker-compose down -v" -ForegroundColor White

Write-Host "`n"

# Limpiar scripts temporales
Remove-Item -Path "start-backend.ps1" -ErrorAction SilentlyContinue
Remove-Item -Path "start-frontend.ps1" -ErrorAction SilentlyContinue
