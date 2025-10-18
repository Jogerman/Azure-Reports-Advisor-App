# ============================================
# Script de Verificación de Ambiente Local
# Azure Advisor Reports Platform
# ============================================

Write-Host "`n=== Verificación de Ambiente Local Azure Advisor Reports ===" -ForegroundColor Cyan
Write-Host "Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n" -ForegroundColor Gray

# ============================================
# 1. Software Instalado
# ============================================
Write-Host "1️⃣  Software Instalado:" -ForegroundColor Yellow

# Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   ✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Python NO instalado" -ForegroundColor Red
}

# Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "   ✅ Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Node.js NO instalado" -ForegroundColor Red
}

# Docker
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "   ✅ Docker: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Docker NO instalado" -ForegroundColor Red
}

# ============================================
# 2. Servicios Docker
# ============================================
Write-Host "`n2️⃣  Servicios Docker:" -ForegroundColor Yellow

try {
    $dockerPs = docker-compose ps --format json 2>&1 | ConvertFrom-Json

    # PostgreSQL
    $postgres = $dockerPs | Where-Object { $_.Service -eq "postgres" }
    if ($postgres -and $postgres.State -eq "running") {
        Write-Host "   ✅ PostgreSQL: Running (Port 5432)" -ForegroundColor Green
        Write-Host "      Status: $($postgres.Health)" -ForegroundColor Gray
    } else {
        Write-Host "   ❌ PostgreSQL: NOT Running" -ForegroundColor Red
    }

    # Redis
    $redis = $dockerPs | Where-Object { $_.Service -eq "redis" }
    if ($redis -and $redis.State -eq "running") {
        Write-Host "   ✅ Redis: Running (Port 6379)" -ForegroundColor Green
        Write-Host "      Status: $($redis.Health)" -ForegroundColor Gray
    } else {
        Write-Host "   ❌ Redis: NOT Running" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Error al verificar Docker: $_" -ForegroundColor Red
}

# ============================================
# 3. Archivos de Configuración
# ============================================
Write-Host "`n3️⃣  Archivos de Configuración:" -ForegroundColor Yellow

# Backend .env
if (Test-Path "azure_advisor_reports\.env") {
    Write-Host "   ✅ Backend .env existe" -ForegroundColor Green

    # Verificar variables críticas
    $envContent = Get-Content "azure_advisor_reports\.env" -Raw
    $criticalVars = @("SECRET_KEY", "DATABASE_URL", "REDIS_URL", "DJANGO_SETTINGS_MODULE")

    foreach ($var in $criticalVars) {
        if ($envContent -match $var) {
            Write-Host "      ✓ $var configurado" -ForegroundColor Gray
        } else {
            Write-Host "      ✗ $var FALTA" -ForegroundColor Red
        }
    }
} else {
    Write-Host "   ❌ Backend .env NO existe" -ForegroundColor Red
    Write-Host "      Ejecuta: Copy-Item azure_advisor_reports\.env.example azure_advisor_reports\.env" -ForegroundColor Yellow
}

# Frontend .env.local
if (Test-Path "frontend\.env.local") {
    Write-Host "   ✅ Frontend .env.local existe" -ForegroundColor Green

    # Verificar variables críticas
    $envContent = Get-Content "frontend\.env.local" -Raw
    $criticalVars = @("REACT_APP_API_URL", "REACT_APP_AZURE_CLIENT_ID")

    foreach ($var in $criticalVars) {
        if ($envContent -match $var) {
            Write-Host "      ✓ $var configurado" -ForegroundColor Gray
        } else {
            Write-Host "      ✗ $var FALTA" -ForegroundColor Red
        }
    }
} else {
    Write-Host "   ❌ Frontend .env.local NO existe" -ForegroundColor Red
    Write-Host "      Crea el archivo manualmente según LOCAL_TESTING_GUIDE.md" -ForegroundColor Yellow
}

# ============================================
# 4. Dependencias Backend
# ============================================
Write-Host "`n4️⃣  Dependencias Backend:" -ForegroundColor Yellow

if (Test-Path "azure_advisor_reports\venv") {
    Write-Host "   ✅ Virtual environment existe" -ForegroundColor Green

    # Verificar si está activado
    if ($env:VIRTUAL_ENV) {
        Write-Host "      ✓ Virtual environment ACTIVADO" -ForegroundColor Gray
        Write-Host "      Path: $env:VIRTUAL_ENV" -ForegroundColor Gray
    } else {
        Write-Host "      ⚠️  Virtual environment NO activado" -ForegroundColor Yellow
        Write-Host "      Ejecuta: .\azure_advisor_reports\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ Virtual environment NO existe" -ForegroundColor Red
    Write-Host "      Ejecuta: python -m venv azure_advisor_reports\venv" -ForegroundColor Yellow
}

# ============================================
# 5. Dependencias Frontend
# ============================================
Write-Host "`n5️⃣  Dependencias Frontend:" -ForegroundColor Yellow

if (Test-Path "frontend\node_modules") {
    Write-Host "   ✅ node_modules existe" -ForegroundColor Green

    # Verificar package.json
    if (Test-Path "frontend\package.json") {
        $packageJson = Get-Content "frontend\package.json" -Raw | ConvertFrom-Json
        Write-Host "      ✓ React version: $($packageJson.dependencies.react)" -ForegroundColor Gray
    }
} else {
    Write-Host "   ❌ node_modules NO existe" -ForegroundColor Red
    Write-Host "      Ejecuta: cd frontend && npm install" -ForegroundColor Yellow
}

# ============================================
# 6. Servidores en Ejecución
# ============================================
Write-Host "`n6️⃣  Servidores en Ejecución:" -ForegroundColor Yellow

# Django (Puerto 8000)
$django = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($django) {
    Write-Host "   ✅ Django corriendo en puerto 8000" -ForegroundColor Green
    Write-Host "      URL: http://localhost:8000" -ForegroundColor Gray
} else {
    Write-Host "   ⚠️  Django NO está corriendo" -ForegroundColor Yellow
    Write-Host "      Para iniciar: cd azure_advisor_reports && python manage.py runserver" -ForegroundColor Yellow
}

# React (Puerto 3000)
$react = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($react) {
    Write-Host "   ✅ React corriendo en puerto 3000" -ForegroundColor Green
    Write-Host "      URL: http://localhost:3000" -ForegroundColor Gray
} else {
    Write-Host "   ⚠️  React NO está corriendo" -ForegroundColor Yellow
    Write-Host "      Para iniciar: cd frontend && npm start" -ForegroundColor Yellow
}

# ============================================
# 7. Health Check del Backend
# ============================================
Write-Host "`n7️⃣  Health Check del Backend:" -ForegroundColor Yellow

if ($django) {
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:8000/api/health/" -Method Get -TimeoutSec 5

        if ($health.status -eq "healthy") {
            Write-Host "   ✅ Backend está HEALTHY" -ForegroundColor Green
            Write-Host "      Database: $($health.database)" -ForegroundColor Gray
            Write-Host "      Cache: $($health.cache)" -ForegroundColor Gray
        } else {
            Write-Host "   ⚠️  Backend responde pero status: $($health.status)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ❌ Backend no responde al health check" -ForegroundColor Red
        Write-Host "      Error: $_" -ForegroundColor Red
    }
} else {
    Write-Host "   ⏭️  Saltado (Django no está corriendo)" -ForegroundColor Gray
}

# ============================================
# 8. Database Status
# ============================================
Write-Host "`n8️⃣  Estado de Base de Datos:" -ForegroundColor Yellow

if ($env:VIRTUAL_ENV) {
    try {
        Push-Location "azure_advisor_reports"
        $migrations = python manage.py showmigrations --plan 2>&1

        if ($LASTEXITCODE -eq 0) {
            $pendingCount = ($migrations | Select-String "\[ \]" | Measure-Object).Count
            $appliedCount = ($migrations | Select-String "\[X\]" | Measure-Object).Count

            Write-Host "   ✅ Migraciones aplicadas: $appliedCount" -ForegroundColor Green

            if ($pendingCount -gt 0) {
                Write-Host "   ⚠️  Migraciones pendientes: $pendingCount" -ForegroundColor Yellow
                Write-Host "      Ejecuta: python manage.py migrate" -ForegroundColor Yellow
            } else {
                Write-Host "   ✓ No hay migraciones pendientes" -ForegroundColor Gray
            }
        }
        Pop-Location
    } catch {
        Write-Host "   ❌ Error al verificar migraciones: $_" -ForegroundColor Red
        Pop-Location
    }
} else {
    Write-Host "   ⏭️  Saltado (Virtual environment no activado)" -ForegroundColor Gray
}

# ============================================
# 9. Resumen y Recomendaciones
# ============================================
Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "📊 RESUMEN" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

$issues = @()
$warnings = @()

# Verificar problemas críticos
if (-not (Test-Path "azure_advisor_reports\.env")) { $issues += "Backend .env falta" }
if (-not (Test-Path "frontend\.env.local")) { $issues += "Frontend .env.local falta" }
if (-not $django) { $warnings += "Django no está corriendo" }
if (-not $react) { $warnings += "React no está corriendo" }

$postgresRunning = $dockerPs | Where-Object { $_.Service -eq "postgres" -and $_.State -eq "running" }
$redisRunning = $dockerPs | Where-Object { $_.Service -eq "redis" -and $_.State -eq "running" }

if (-not $postgresRunning) { $issues += "PostgreSQL no está corriendo" }
if (-not $redisRunning) { $issues += "Redis no está corriendo" }

if ($issues.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "`n🎉 ¡TODO ESTÁ CONFIGURADO CORRECTAMENTE!" -ForegroundColor Green
    Write-Host "`nTu ambiente local está listo para desarrollo." -ForegroundColor Green
} else {
    if ($issues.Count -gt 0) {
        Write-Host "`n❌ PROBLEMAS CRÍTICOS:" -ForegroundColor Red
        foreach ($issue in $issues) {
            Write-Host "   • $issue" -ForegroundColor Red
        }
    }

    if ($warnings.Count -gt 0) {
        Write-Host "`n⚠️  ADVERTENCIAS:" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "   • $warning" -ForegroundColor Yellow
        }
    }

    Write-Host "`n📖 Consulta LOCAL_TESTING_GUIDE.md para instrucciones detalladas." -ForegroundColor Cyan
}

# ============================================
# 10. Siguiente Pasos
# ============================================
Write-Host "`n📝 SIGUIENTES PASOS:" -ForegroundColor Cyan

if (-not $django -and -not $react) {
    Write-Host "
Para iniciar el ambiente de desarrollo completo:

1️⃣  Terminal 1 (Backend):
   cd azure_advisor_reports
   .\venv\Scripts\Activate.ps1
   python manage.py runserver

2️⃣  Terminal 2 (Frontend):
   cd frontend
   npm start

3️⃣  Acceder a:
   • Frontend: http://localhost:3000
   • Backend API: http://localhost:8000/api
   • Admin: http://localhost:8000/admin
" -ForegroundColor White
} elseif ($django -and $react) {
    Write-Host "
✅ Ambiente completamente funcional!

URLs disponibles:
   • Frontend: http://localhost:3000
   • Backend API: http://localhost:8000/api
   • Admin Panel: http://localhost:8000/admin
   • Health Check: http://localhost:8000/api/health/
" -ForegroundColor Green
}

Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "Fin del reporte - $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Gray
Write-Host "="*60 + "`n" -ForegroundColor Cyan
