# Plan de Implementación de Seguridad
## Azure Reports Advisor Application

**Fecha de Creación:** 5 de Noviembre, 2025
**Versión:** 1.0
**Estado:** Pendiente de Implementación
**Prioridad:** CRÍTICA

---

## Resumen Ejecutivo

Este documento contiene el plan detallado de implementación para remediar las **16 vulnerabilidades** identificadas en la auditoría de seguridad del proyecto Azure Reports Advisor App.

**Distribución de Vulnerabilidades:**
- 🔴 **2 CRÍTICAS** - Requieren acción inmediata (Semana 1)
- 🟠 **5 ALTAS** - Corto plazo (Semanas 2-3)
- 🟡 **6 MEDIAS** - Mediano plazo (Mes 2)
- 🟢 **3 BAJAS** - Largo plazo (Mes 3+)

**Esfuerzo Total Estimado:** ~300 horas

---

## FASE 1: VULNERABILIDADES CRÍTICAS (Semana 1) ⏰ URGENTE

### ✅ TAREA 1.1: Fix SECRET_KEY Débil y Predecible
**Prioridad:** 🔴 CRÍTICA
**Severidad:** CVSS 9.1
**Esfuerzo:** 8 horas
**Archivos Afectados:**
- `azure_advisor_reports/azure_advisor_reports/settings.py`
- `.env.example`
- Documentación de deployment

**Problema:**
El SECRET_KEY tiene un valor default débil que podría usarse en producción si la variable de entorno no está configurada. Esta clave se usa para:
- Firma de tokens JWT (HS256)
- Seguridad de sesiones Django
- Generación de tokens CSRF
- Firma criptográfica

**Riesgo:** Bypass completo de autenticación, escalación de privilegios, brecha de datos

**Subtareas:**
- [ ] Eliminar el valor default del SECRET_KEY en settings.py
- [ ] Implementar validación de longitud mínima (50 caracteres)
- [ ] Agregar verificación al inicio de la aplicación
- [ ] Implementar soporte para SECRET_KEY_FALLBACKS (rotación)
- [ ] Generar nuevo SECRET_KEY fuerte para producción
- [ ] Actualizar .env.example con instrucciones
- [ ] Documentar procedimiento de rotación de SECRET_KEY
- [ ] Configurar monitoreo/alertas para cambios de SECRET_KEY
- [ ] Integrar con Azure Key Vault (producción)

**Código a Implementar:**
```python
# settings.py
import secrets
import sys

# Remove default - force SECRET_KEY to be set
try:
    SECRET_KEY = config('SECRET_KEY')
except Exception:
    raise ValueError(
        "SECRET_KEY must be set in environment variables. "
        "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(50))'"
    )

# Validate SECRET_KEY strength
if SECRET_KEY == 'django-insecure-change-this-in-production' or len(SECRET_KEY) < 50:
    if 'migrate' not in sys.argv and 'collectstatic' not in sys.argv:
        raise ValueError(
            "SECRET_KEY must be at least 50 characters long and cryptographically secure."
        )

# Add secret rotation support
SECRET_KEY_FALLBACKS = config(
    'SECRET_KEY_FALLBACKS',
    default='',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]
)
```

**Comando para generar SECRET_KEY seguro:**
```bash
python -c 'import secrets; print(secrets.token_urlsafe(50))'
```

**Testing:**
- [ ] Verificar que la app NO arranca sin SECRET_KEY
- [ ] Verificar que rechaza SECRET_KEY débiles
- [ ] Probar rotación de claves con fallbacks
- [ ] Verificar generación y validación de JWT tokens

---

### ✅ TAREA 1.2: Implementar Rate Limiting en Autenticación
**Prioridad:** 🔴 CRÍTICA
**Severidad:** CVSS 8.6
**Esfuerzo:** 12 horas
**Archivos Afectados:**
- `azure_advisor_reports/apps/authentication/views.py`
- `azure_advisor_reports/requirements.txt`
- `azure_advisor_reports/azure_advisor_reports/settings.py`

**Problema:**
Los endpoints de autenticación no tienen rate limiting, exponiéndolos a:
- Ataques de fuerza bruta
- Credential stuffing
- Denegación de servicio (DoS)
- Agotamiento de recursos

**Subtareas:**
- [ ] Instalar django-ratelimit
- [ ] Configurar rate limiting para endpoint /api/v1/auth/login/
- [ ] Configurar rate limiting para endpoint /api/v1/auth/refresh/
- [ ] Implementar rate limiting por IP
- [ ] Implementar rate limiting por User-Agent
- [ ] Agregar logging de intentos bloqueados
- [ ] Implementar lockout progresivo (exponential backoff)
- [ ] Configurar respuestas HTTP 429 personalizadas
- [ ] Agregar rate limiting al endpoint de upload CSV
- [ ] Documentar límites de rate en API docs

**Dependencia a Instalar:**
```bash
pip install django-ratelimit==4.1.0
```

**Código a Implementar:**
```python
# views.py
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.core.cache import cache
import logging

security_logger = logging.getLogger('security')

def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class AzureADLoginView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = AzureADLoginSerializer

    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True))
    @method_decorator(ratelimit(key='header:user-agent', rate='10/m', method='POST', block=True))
    def post(self, request):
        """Authenticate user with Azure AD access token - rate limited."""

        # Check if IP is in lockout
        ip = get_client_ip(request)
        lockout_key = f'auth_lockout:{ip}'
        if cache.get(lockout_key):
            security_logger.warning(f'Authentication attempt from locked out IP: {ip}')
            return Response(
                {'error': 'Too many failed attempts. Please try again later.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        serializer = AzureADLoginSerializer(data=request.data)

        if not serializer.is_valid():
            # Track failed attempts
            self._track_failed_attempt(ip)
            security_logger.warning(
                f'Authentication failed from IP {ip}: Invalid request'
            )
            return Response(
                {'error': 'Invalid request data'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ... rest of authentication logic ...

    def _track_failed_attempt(self, ip):
        """Track failed authentication attempts and implement progressive lockout."""
        key = f'auth_failures:{ip}'
        failures = cache.get(key, 0) + 1
        cache.set(key, failures, 3600)  # Track for 1 hour

        # Progressive lockout: 5 failures = 15 min lockout, 10 = 1 hour, 15 = 24 hours
        if failures >= 15:
            cache.set(f'auth_lockout:{ip}', True, 86400)  # 24 hours
            security_logger.error(f'IP {ip} locked out for 24 hours after {failures} failures')
        elif failures >= 10:
            cache.set(f'auth_lockout:{ip}', True, 3600)  # 1 hour
            security_logger.warning(f'IP {ip} locked out for 1 hour after {failures} failures')
        elif failures >= 5:
            cache.set(f'auth_lockout:{ip}', True, 900)  # 15 minutes
            security_logger.warning(f'IP {ip} locked out for 15 minutes after {failures} failures')

class TokenRefreshView(views.APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='30/h', method='POST', block=True))
    def post(self, request):
        """Generate new access token using refresh token - rate limited."""
        # ... implementation ...
```

**Settings Configuration:**
```python
# settings.py
RATELIMIT_ENABLE = config('RATELIMIT_ENABLE', default=True, cast=bool)
RATELIMIT_USE_CACHE = 'default'

# Logging for security events
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'security': {
            'format': '{levelname} {asctime} user={user} ip={ip} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'security.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'security',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['security_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

**Testing:**
- [ ] Probar límite de 5 requests/min por IP
- [ ] Verificar lockout progresivo (5, 10, 15 intentos)
- [ ] Probar rate limiting con múltiples IPs
- [ ] Verificar respuestas HTTP 429
- [ ] Confirmar logging de eventos de seguridad
- [ ] Probar rate limiting en token refresh

---

## FASE 2: VULNERABILIDADES ALTAS (Semanas 2-3)

### ✅ TAREA 2.1: Remover Azure Tenant ID Hardcodeado
**Prioridad:** 🟠 ALTA
**Severidad:** CVSS 7.5
**Esfuerzo:** 2 horas
**Archivo:** `backend-appsettings.example.json`

**Problema:** El Tenant ID real está hardcodeado en el archivo de ejemplo

**Cambio:**
```json
{
  "name": "AZURE_TENANT_ID",
  "value": "00000000-0000-0000-0000-000000000000",
  "description": "⚠️ REEMPLAZAR con tu Azure AD Tenant ID"
}
```

---

### ✅ TAREA 2.2: Validación Comprehensiva de Archivos CSV
**Prioridad:** 🟠 ALTA
**Severidad:** CVSS 7.3
**Esfuerzo:** 16 horas

**Instalar:**
```bash
pip install python-magic==0.4.27
```

**Validaciones a Implementar:**
1. Validación de extensión de archivo
2. Validación de tamaño de archivo
3. Validación de MIME type usando magic numbers
4. Validación de estructura CSV (parsing)
5. Verificación de columnas requeridas
6. Validación de encoding
7. Sanitización de nombres de archivo

---

### ✅ TAREA 2.3: Prevenir CSV Injection
**Prioridad:** 🟠 ALTA
**Severidad:** CVSS 7.1
**Esfuerzo:** 8 horas

**Implementar:**
```python
FORMULA_PREFIXES = ('=', '+', '-', '@', '|', '\t', '\r')

def sanitize_cell_value(self, value: str) -> str:
    """Prevenir ejecución de fórmulas en CSV."""
    if value and value[0] in self.FORMULA_PREFIXES:
        return "'" + value
    return value
```

---

### ✅ TAREA 2.4: JWT Token Blacklisting
**Prioridad:** 🟠 ALTA
**Severidad:** CVSS 7.0
**Esfuerzo:** 20 horas

**Implementar:**
- Modelo TokenBlacklist
- Reducir expiración de tokens (access: 15min, refresh: 1 día)
- Agregar JTI a tokens
- Endpoint de logout que revoque tokens
- Limpieza automática de tokens expirados

---

### ✅ TAREA 2.5: Fix Azure AD Audience Validation
**Prioridad:** 🟠 ALTA
**Severidad:** CVSS 6.8
**Esfuerzo:** 6 horas

**Problema:** La validación de audiencia está deshabilitada

**Fix:** Habilitar `verify_aud=True` y validar que solo se acepten ID tokens

---

## FASE 3: VULNERABILIDADES MEDIAS (Mes 2)

### ✅ TAREA 3.1: Content Security Policy Headers
**Prioridad:** 🟡 MEDIA
**Esfuerzo:** 12 horas

```bash
pip install django-csp==3.8
```

### ✅ TAREA 3.2: Security Event Logging
**Prioridad:** 🟡 MEDIA
**Esfuerzo:** 10 horas

Loggear todos los eventos de seguridad críticos

### ✅ TAREA 3.3: Fix CORS Configuration
**Prioridad:** 🟡 MEDIA
**Esfuerzo:** 4 horas

Eliminar `CORS_ALLOW_ALL_ORIGINS=True`

### ✅ TAREA 3.4: Secure Playwright
**Prioridad:** 🟡 MEDIA
**Esfuerzo:** 8 horas

Remover `--disable-web-security` en producción

### ✅ TAREA 3.5: Fix Database Credentials
**Prioridad:** 🟡 MEDIA
**Esfuerzo:** 2 horas

Cambiar contraseñas por defecto

### ✅ TAREA 3.6: Path Traversal Protection
**Prioridad:** 🟡 MEDIA
**Esfuerzo:** 4 horas

Validar rutas de archivos

---

## FASE 4: VULNERABILIDADES BAJAS (Mes 3+)

### ✅ TAREA 4.1: Mejorar Error Handling
**Prioridad:** 🟢 BAJA
**Esfuerzo:** 6 horas

### ✅ TAREA 4.2: Crear security.txt
**Prioridad:** 🟢 BAJA
**Esfuerzo:** 2 horas

### ✅ TAREA 4.3: Mejorar Token Storage Frontend
**Prioridad:** 🟢 BAJA
**Esfuerzo:** 8 horas

### ✅ TAREA 4.4: Actualizar Dependencias
**Prioridad:** 🟠 ALTA
**Esfuerzo:** 4 horas

```bash
pip install --upgrade Pillow>=10.3.0 cryptography>=42.0.0 Django>=4.2.11
```

---

## TESTING Y QA

### Security Test Suite
**Esfuerzo:** 30 horas

```python
# tests/security/test_authentication_security.py
# tests/security/test_file_upload_security.py
# tests/security/test_csv_injection.py
# tests/security/test_rate_limiting.py
```

### Penetration Testing
**Esfuerzo:** 40 horas

Herramientas:
- OWASP ZAP
- Burp Suite
- SQLMap

---

## MONITOREO Y ALERTAS

**Alertas a Configurar:**
- Múltiples intentos fallidos de login
- Tokens revocados accediendo al sistema
- Cambios en SECRET_KEY
- Uploads sospechosos
- Patrones de SQL injection

Herramientas:
- Azure Application Insights
- Sentry
- Custom logging

---

## CI/CD SECURITY

```yaml
# .github/workflows/security-scan.yml
name: Security Scan
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - name: Run Bandit
        run: bandit -r azure_advisor_reports/
      - name: Run Safety
        run: safety check
```

---

## CHECKLIST MAESTRO

### Fase 1 - Crítico (Semana 1) ⏰
- [ ] 1.1 Fix SECRET_KEY
- [ ] 1.2 Rate limiting
- [ ] 1.3 Rotar credenciales Azure
- [ ] 1.4 Testing crítico

### Fase 2 - Alto (Semanas 2-3)
- [ ] 2.1 Remover Tenant ID
- [ ] 2.2 Validación CSV
- [ ] 2.3 CSV injection
- [ ] 2.4 Token blacklisting
- [ ] 2.5 Azure AD validation

### Fase 3 - Medio (Mes 2)
- [ ] 3.1 CSP headers
- [ ] 3.2 Security logging
- [ ] 3.3 CORS fix
- [ ] 3.4 Secure Playwright
- [ ] 3.5 DB credentials
- [ ] 3.6 Path traversal

### Fase 4 - Bajo (Mes 3+)
- [ ] 4.1 Error handling
- [ ] 4.2 security.txt
- [ ] 4.3 Token storage
- [ ] 4.4 Actualizar deps

### Testing
- [ ] Test suite completo
- [ ] Penetration testing
- [ ] Security audit externo

### Operaciones
- [ ] Security monitoring
- [ ] Alertas configuradas
- [ ] CI/CD scanning
- [ ] Documentación actualizada

---

## MÉTRICAS DE ÉXITO

**Objetivos:**
- ✅ 0 vulnerabilidades CRÍTICAS
- ✅ 0 vulnerabilidades ALTAS
- ✅ <5 vulnerabilidades MEDIAS
- ✅ Tiempo de respuesta a incidentes: <1 hora
- ✅ 100% del equipo con training
- ✅ Security scans automáticos
- ✅ Auditoría externa aprobada

---

## RECURSOS

**Documentación:**
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security](https://docs.djangoproject.com/en/4.2/topics/security/)
- [Azure AD Best Practices](https://learn.microsoft.com/en-us/azure/active-directory/develop/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

**Herramientas:**
- Bandit (Python security linter)
- Safety (dependency scanner)
- OWASP ZAP (penetration testing)

---

## HISTORIAL DE CAMBIOS

| Fecha | Versión | Cambios | Autor |
|-------|---------|---------|-------|
| 2025-11-05 | 1.0 | Plan inicial | Claude Security Specialist |

---

**Próxima Revisión:** 2025-12-05
**Estado:** 🟡 EN PROGRESO
**Progreso:** 0% (0/50 tareas completadas)
