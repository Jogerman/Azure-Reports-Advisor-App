# ============================================
# Script de Inicio Rápido - Desarrollo Local
# Azure Advisor Reports Platform
# ============================================

Write-Host "`n=== Iniciando Ambiente de Desarrollo ===" -ForegroundColor Cyan
Write-Host "Presiona Ctrl+C en cualquier momento para detener`n" -ForegroundColor Gray

# Verificar Docker está corriendo
Write-Host "1️⃣  Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerRunning = docker ps 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   ❌ Docker no está corriendo" -ForegroundColor Red
        Write-Host "   Por favor, inicia Docker Desktop primero" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "   ✅ Docker está corriendo" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Error al verificar Docker: $_" -ForegroundColor Red
    exit 1
}

# Iniciar servicios Docker
Write-Host "`n2️⃣  Iniciando PostgreSQL y Redis..." -ForegroundColor Yellow
docker-compose up -d postgres redis

Start-Sleep -Seconds 3

# Verificar servicios Docker
$postgres = docker-compose ps postgres --format json 2>&1 | ConvertFrom-Json
$redis = docker-compose ps redis --format json 2>&1 | ConvertFrom-Json

if ($postgres.State -eq "running") {
    Write-Host "   ✅ PostgreSQL: Running" -ForegroundColor Green
} else {
    Write-Host "   ❌ PostgreSQL: Failed to start" -ForegroundColor Red
    exit 1
}

if ($redis.State -eq "running") {
    Write-Host "   ✅ Redis: Running" -ForegroundColor Green
} else {
    Write-Host "   ❌ Redis: Failed to start" -ForegroundColor Red
    exit 1
}

# Iniciar Backend (Django) en nueva ventana
Write-Host "`n3️⃣  Iniciando Backend (Django)..." -ForegroundColor Yellow

$backendScript = @'
Write-Host "=== Backend (Django) ===" -ForegroundColor Cyan
cd azure_advisor_reports
.\venv\Scripts\Activate.ps1
Write-Host "Activating virtual environment..." -ForegroundColor Gray
Write-Host "Starting Django development server..." -ForegroundColor Gray
python manage.py runserver
'@

$backendScript | Out-File -FilePath "start-backend.ps1" -Encoding utf8
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "start-backend.ps1"

Write-Host "   ✅ Backend iniciando en nueva terminal (puerto 8000)" -ForegroundColor Green

# Esperar a que Django esté listo
Write-Host "   ⏳ Esperando a que Django esté listo..." -ForegroundColor Gray
Start-Sleep -Seconds 5

$retries = 0
$maxRetries = 10
$djangoReady = $false

while ($retries -lt $maxRetries -and -not $djangoReady) {
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:8000/api/health/" -Method Get -TimeoutSec 2 -ErrorAction Stop
        if ($health.status -eq "healthy") {
            $djangoReady = $true
            Write-Host "   ✅ Backend está listo y funcionando" -ForegroundColor Green
        }
    } catch {
        $retries++
        Start-Sleep -Seconds 2
    }
}

if (-not $djangoReady) {
    Write-Host "   ⚠️  Backend tardó en iniciarse (esto es normal la primera vez)" -ForegroundColor Yellow
}

# Iniciar Frontend (React) en nueva ventana
Write-Host "`n4️⃣  Iniciando Frontend (React)..." -ForegroundColor Yellow

$frontendScript = @'
Write-Host "=== Frontend (React) ===" -ForegroundColor Cyan
cd frontend
Write-Host "Starting React development server..." -ForegroundColor Gray
npm start
'@

$frontendScript | Out-File -FilePath "start-frontend.ps1" -Encoding utf8
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "start-frontend.ps1"

Write-Host "   ✅ Frontend iniciando en nueva terminal (puerto 3000)" -ForegroundColor Green

# Resumen
Write-Host "`n" + "="*50 -ForegroundColor Cyan
Write-Host "✅ AMBIENTE DE DESARROLLO INICIADO" -ForegroundColor Green
Write-Host "="*50 -ForegroundColor Cyan

Write-Host "`n🌐 URLs Disponibles:" -ForegroundColor Yellow
Write-Host "   Frontend:    http://localhost:3000" -ForegroundColor White
Write-Host "   Backend API: http://localhost:8000/api" -ForegroundColor White
Write-Host "   Admin Panel: http://localhost:8000/admin" -ForegroundColor White
Write-Host "   Health Check: http://localhost:8000/api/health/" -ForegroundColor White

Write-Host "`n📝 Notas:" -ForegroundColor Yellow
Write-Host "   • El navegador abrirá automáticamente en unos segundos" -ForegroundColor Gray
Write-Host "   • Backend y Frontend están en terminales separadas" -ForegroundColor Gray
Write-Host "   • Para detener: Cierra las terminales o presiona Ctrl+C" -ForegroundColor Gray
Write-Host "   • Para ver logs: Revisa las terminales de Backend y Frontend" -ForegroundColor Gray

Write-Host "`n⏳ Esperando 10 segundos para que React compile..." -ForegroundColor Gray
Start-Sleep -Seconds 10

# Abrir navegador
Write-Host "`n🌍 Abriendo navegador..." -ForegroundColor Yellow
Start-Process "http://localhost:3000"

Write-Host "`n✅ Todo listo! Presiona Enter para cerrar esta ventana..." -ForegroundColor Green
Write-Host "(Las otras terminales seguirán funcionando)`n" -ForegroundColor Gray

Read-Host
