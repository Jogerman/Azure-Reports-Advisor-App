# Script para reconstruir y reiniciar los contenedores Docker
# Azure Advisor Reports Platform

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Azure Advisor Reports - Docker Rebuild" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que Docker está corriendo
Write-Host "1. Verificando Docker Desktop..." -ForegroundColor Yellow
docker info > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker Desktop no está corriendo." -ForegroundColor Red
    Write-Host "Por favor inicia Docker Desktop y ejecuta este script nuevamente." -ForegroundColor Yellow
    exit 1
}
Write-Host "   ✓ Docker Desktop está corriendo" -ForegroundColor Green
Write-Host ""

# Detener contenedores existentes
Write-Host "2. Deteniendo contenedores existentes..." -ForegroundColor Yellow
docker-compose down
Write-Host "   ✓ Contenedores detenidos" -ForegroundColor Green
Write-Host ""

# Limpiar imágenes antiguas (opcional)
Write-Host "3. ¿Deseas limpiar imágenes antiguas no utilizadas? (s/n): " -ForegroundColor Yellow -NoNewline
$clean = Read-Host
if ($clean -eq "s" -or $clean -eq "S") {
    Write-Host "   Limpiando imágenes antiguas..." -ForegroundColor Yellow
    docker image prune -f
    Write-Host "   ✓ Imágenes limpiadas" -ForegroundColor Green
}
Write-Host ""

# Reconstruir imágenes
Write-Host "4. Reconstruyendo imágenes (esto puede tomar varios minutos)..." -ForegroundColor Yellow
docker-compose build --no-cache
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Falló la construcción de las imágenes." -ForegroundColor Red
    exit 1
}
Write-Host "   ✓ Imágenes reconstruidas exitosamente" -ForegroundColor Green
Write-Host ""

# Iniciar contenedores
Write-Host "5. Iniciando contenedores..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Falló el inicio de los contenedores." -ForegroundColor Red
    exit 1
}
Write-Host "   ✓ Contenedores iniciados" -ForegroundColor Green
Write-Host ""

# Esperar a que los servicios estén listos
Write-Host "6. Esperando a que los servicios estén listos (30 segundos)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30
Write-Host "   ✓ Servicios iniciados" -ForegroundColor Green
Write-Host ""

# Aplicar migraciones
Write-Host "7. Aplicando migraciones de base de datos..." -ForegroundColor Yellow
docker-compose exec -T backend python manage.py migrate
Write-Host "   ✓ Migraciones aplicadas" -ForegroundColor Green
Write-Host ""

# Inicializar analytics
Write-Host "8. Inicializando módulo Analytics..." -ForegroundColor Yellow
docker-compose exec -T backend python manage.py initialize_analytics
Write-Host "   ✓ Analytics inicializado" -ForegroundColor Green
Write-Host ""

# Mostrar estado de los contenedores
Write-Host "9. Estado de los contenedores:" -ForegroundColor Yellow
docker-compose ps
Write-Host ""

# Información de acceso
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "¡Deployment completado exitosamente!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Servicios disponibles:" -ForegroundColor Yellow
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "  Admin:     http://localhost:8000/admin" -ForegroundColor White
Write-Host ""
Write-Host "Nuevas páginas:" -ForegroundColor Yellow
Write-Host "  History:   http://localhost:3000/history" -ForegroundColor Cyan
Write-Host "  Analytics: http://localhost:3000/analytics" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para ver los logs en tiempo real:" -ForegroundColor Yellow
Write-Host "  docker-compose logs -f" -ForegroundColor White
Write-Host ""
Write-Host "Para detener los servicios:" -ForegroundColor Yellow
Write-Host "  docker-compose down" -ForegroundColor White
Write-Host ""
