#!/bin/bash
# Safe cleanup script for production readiness
echo "=== Limpieza Segura para Producción ==="
echo ""

# Create backup directory
BACKUP_DIR="cleanup_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "✓ Directorio de respaldo creado: $BACKUP_DIR"

# Move test files to backup
echo ""
echo "Moviendo archivos de prueba al respaldo..."
mv test_*.py "$BACKUP_DIR/" 2>/dev/null && echo "  ✓ Archivos test_*.py movidos"
mv test-*.js test_*.js "$BACKUP_DIR/" 2>/dev/null && echo "  ✓ Archivos test-*.js movidos"
mv debug-*.js "$BACKUP_DIR/" 2>/dev/null && echo "  ✓ Archivos debug-*.js movidos"

# Move utility scripts that shouldn't be in root
echo ""
echo "Moviendo scripts de utilidad..."
mv diagnose_stuck_reports.py fix_stuck_reports.py "$BACKUP_DIR/" 2>/dev/null && echo "  ✓ Scripts de diagnóstico movidos"
mv generate_*.py "$BACKUP_DIR/" 2>/dev/null && echo "  ✓ Scripts de generación movidos"
mv generate_*.js "$BACKUP_DIR/" 2>/dev/null && echo "  ✓ Scripts JS de generación movidos"

# Move CSV processor (already integrated in apps)
mv csv_processor.py "$BACKUP_DIR/" 2>/dev/null && echo "  ✓ csv_processor.py movido"

# Move verification scripts
mv verify_*.py "$BACKUP_DIR/" 2>/dev/null && echo "  ✓ Scripts de verificación movidos"

# Move create_groups (dev utility)
mv create_groups.py "$BACKUP_DIR/" 2>/dev/null && echo "  ✓ create_groups.py movido"

echo ""
echo "=== Resumen ==="
echo "✓ Archivos movidos a: $BACKUP_DIR"
echo "✓ Si algo falla, puedes restaurar desde ese directorio"
echo ""
echo "Para eliminar permanentemente el backup después de verificar:"
echo "  rm -rf $BACKUP_DIR"
