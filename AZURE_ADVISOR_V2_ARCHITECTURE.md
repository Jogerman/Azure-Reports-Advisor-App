# Azure Advisor Reports v2.0 - Arquitectura de Integración Directa con Azure API

**Versión:** 2.0.0
**Fecha:** 2025-11-17
**Estado:** Propuesta de Diseño
**Autor:** Software Architecture Team

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura de Alto Nivel](#arquitectura-de-alto-nivel)
3. [Componentes Nuevos](#componentes-nuevos)
4. [Integración con Azure Advisor API](#integración-con-azure-advisor-api)
5. [Modelo de Datos](#modelo-de-datos)
6. [Flujo de Datos](#flujo-de-datos)
7. [Seguridad y Credenciales](#seguridad-y-credenciales)
8. [Coexistencia de Flujos (CSV vs API)](#coexistencia-de-flujos-csv-vs-api)
9. [Tareas Asíncronas (Celery)](#tareas-asíncronas-celery)
10. [API REST Endpoints](#api-rest-endpoints)
11. [Frontend (React)](#frontend-react)
12. [Manejo de Rate Limits](#manejo-de-rate-limits)
13. [Escalabilidad y Performance](#escalabilidad-y-performance)
14. [Plan de Implementación](#plan-de-implementación)
15. [Decisiones Arquitectónicas (ADRs)](#decisiones-arquitectónicas-adrs)

---

## 1. Resumen Ejecutivo

### 1.1 Objetivo

Evolucionar Azure Advisor Reports de v1.6.1 a v2.0 agregando **integración directa con Azure Advisor API**, permitiendo a los usuarios obtener recomendaciones automáticamente mediante Azure Service Principal, mientras se mantiene la funcionalidad existente de carga manual de CSV.

### 1.2 Beneficios Clave

- **Automatización**: Eliminación del proceso manual de descarga/carga de CSV
- **Tiempo Real**: Acceso a recomendaciones actualizadas directamente desde Azure
- **Multi-Suscripción**: Soporte nativo para clientes con múltiples suscripciones
- **Trazabilidad**: Historial completo de recomendaciones a lo largo del tiempo
- **Flexibilidad**: Los usuarios eligen entre API o CSV según sus necesidades

### 1.3 Stack Tecnológico

**Backend:**
- Django 5.1 + Django REST Framework
- Azure SDK: `azure-identity`, `azure-mgmt-advisor`, `azure-mgmt-resourcegraph`
- Celery 5+ con Redis broker (worker pool: gevent)
- PostgreSQL 15+

**Frontend:**
- React 18 + TypeScript
- Componentes nuevos para gestión de suscripciones Azure

**Infraestructura:**
- Azure Container Apps (existente)
- Azure Blob Storage (para archivos)
- Redis (cache y Celery broker)

---

## 2. Arquitectura de Alto Nivel

### 2.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │  CSV Upload UI   │  │ Azure API Config │  │  Reports Dashboard│ │
│  │  (Existing)      │  │  (NEW)           │  │  (Enhanced)       │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘ │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ HTTPS/REST API
┌─────────────────────────┴───────────────────────────────────────────┐
│                      DJANGO BACKEND                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    API Layer (DRF)                            │  │
│  │  ┌─────────────┐  ┌──────────────────┐  ┌─────────────────┐ │  │
│  │  │ Reports API │  │ Subscriptions API│  │  Clients API    │ │  │
│  │  │ (Enhanced)  │  │     (NEW)        │  │  (Enhanced)     │ │  │
│  │  └─────────────┘  └──────────────────┘  └─────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   Service Layer                               │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐ │  │
│  │  │ CSV Processor    │  │ Azure Advisor    │  │  Report    │ │  │
│  │  │ Service          │  │ Service (NEW)    │  │  Generator │ │  │
│  │  │ (Existing)       │  │                  │  │  Service   │ │  │
│  │  └──────────────────┘  └──────────────────┘  └────────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                      Data Models                              │  │
│  │  ┌─────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────┐ │  │
│  │  │ Report  │ │ Subscription │ │Recommendation│ │  Client  │ │  │
│  │  │(Enhanced)│ │    (NEW)     │ │  (Enhanced)  │ │(Enhanced)│ │  │
│  │  └─────────┘ └──────────────┘ └──────────────┘ └──────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
└──────────────────────┬───────────────────────────────────────────────┘
                       │
┌──────────────────────┴────────────────────────────────────────────┐
│                   CELERY WORKERS (Gevent Pool)                    │
│  ┌──────────────────┐  ┌─────────────────────┐  ┌─────────────┐ │
│  │ process_csv_file │  │ fetch_azure_advisor │  │ generate    │ │
│  │    (Existing)    │  │  _recommendations   │  │  _report    │ │
│  │                  │  │       (NEW)         │  │ (Existing)  │ │
│  └──────────────────┘  └─────────────────────┘  └─────────────┘ │
└───────────────────────────────────────────────────────────────────┘
                       │
┌──────────────────────┴────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐│
│  │ PostgreSQL   │  │    Redis     │  │   Azure Services         ││
│  │              │  │  (Cache +    │  │  ┌────────────────────┐  ││
│  │   Database   │  │   Broker)    │  │  │ Azure Advisor API  │  ││
│  │              │  │              │  │  ├────────────────────┤  ││
│  │              │  │              │  │  │ Azure Resource     │  ││
│  │              │  │              │  │  │ Graph API          │  ││
│  │              │  │              │  │  ├────────────────────┤  ││
│  │              │  │              │  │  │ Azure Identity     │  ││
│  │              │  │              │  │  │ (Service Principal)│  ││
│  └──────────────┘  └──────────────┘  │  └────────────────────┘  ││
└───────────────────────────────────────┴──────────────────────────┘
```

### 2.2 Flujo Dual: CSV vs Azure API

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INITIATES REPORT                        │
└────────────┬───────────────────────────┬────────────────────────┘
             │                           │
    ┌────────▼────────┐         ┌────────▼─────────┐
    │  Upload CSV     │         │ Fetch from Azure │
    │  (Legacy Path)  │         │  (New API Path)  │
    └────────┬────────┘         └────────┬─────────┘
             │                           │
    ┌────────▼──────────────┐   ┌────────▼────────────────────┐
    │ Report.source='csv'   │   │ Report.source='azure_api'   │
    │ csv_file field set    │   │ subscription_id field set   │
    └────────┬──────────────┘   └────────┬────────────────────┘
             │                           │
    ┌────────▼──────────────┐   ┌────────▼────────────────────┐
    │ Celery Task:          │   │ Celery Task:                │
    │ process_csv_file()    │   │ fetch_azure_advisor_data()  │
    └────────┬──────────────┘   └────────┬────────────────────┘
             │                           │
             │                   ┌───────▼───────────┐
             │                   │ Azure Advisor API │
             │                   │ Authentication    │
             │                   │ + API Calls       │
             │                   └───────┬───────────┘
             │                           │
    ┌────────▼──────────────────────────▼────────────────────┐
    │         Create Recommendation Records                  │
    │         (Common data model)                            │
    └────────┬───────────────────────────────────────────────┘
             │
    ┌────────▼──────────────┐
    │ Celery Task:          │
    │ generate_report()     │
    │ (HTML/PDF)            │
    └───────────────────────┘
```

---

## 3. Componentes Nuevos

### 3.1 Azure Subscription Manager

**Nueva App Django:** `apps/azure_integration/`

**Propósito:** Gestionar credenciales de Azure, subscripciones, y configuración de Service Principals.

**Estructura:**
```
apps/azure_integration/
├── __init__.py
├── apps.py
├── models.py                    # AzureSubscription, ServicePrincipal
├── services/
│   ├── __init__.py
│   ├── azure_advisor_client.py  # Cliente para Azure Advisor API
│   ├── credential_manager.py    # Gestión segura de credenciales
│   └── subscription_validator.py # Validación de conexión Azure
├── serializers.py
├── views.py
├── urls.py
├── tasks.py                     # Celery tasks para Azure
├── admin.py
├── tests/
│   ├── test_models.py
│   ├── test_services.py
│   └── test_tasks.py
└── migrations/
```

### 3.2 Azure Advisor Service Client

**Archivo:** `apps/azure_integration/services/azure_advisor_client.py`

**Responsabilidades:**
1. Autenticación con Azure usando Service Principal
2. Llamadas a Azure Advisor API
3. Transformación de datos de Azure a formato interno
4. Manejo de paginación de resultados
5. Rate limiting y retry logic
6. Caching de resultados

### 3.3 Credential Manager

**Archivo:** `apps/azure_integration/services/credential_manager.py`

**Responsabilidades:**
1. Encriptación/desencriptación de Client Secret
2. Almacenamiento seguro en base de datos
3. Rotación de credenciales
4. Validación de permisos Azure

---

## 4. Integración con Azure Advisor API

### 4.1 Azure APIs Utilizadas

#### Azure Advisor API
- **Endpoint:** `https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.Advisor/recommendations`
- **Versión API:** `2020-01-01`
- **Propósito:** Obtener recomendaciones de Azure Advisor

#### Azure Resource Graph API (Opcional - para queries avanzadas)
- **Endpoint:** `https://management.azure.com/providers/Microsoft.ResourceGraph/resources`
- **Versión API:** `2021-03-01`
- **Propósito:** Queries complejas sobre recursos Azure

### 4.2 Autenticación con Service Principal

#### Permisos Requeridos en Azure

El Service Principal necesita los siguientes roles en las suscripciones objetivo:

1. **Reader** (Lector): Acceso de solo lectura a recursos
   - Permite listar recursos y obtener recomendaciones
   - Rol mínimo necesario

2. **Advisor Reader** (Recomendado): Acceso específico a Azure Advisor
   - Rol específico para leer recomendaciones
   - Más restrictivo y seguro que Reader general

#### Configuración del Service Principal

```bash
# 1. Crear App Registration en Azure AD
az ad app create --display-name "Azure-Advisor-Reports-App"

# 2. Crear Service Principal
az ad sp create --id <application-id>

# 3. Crear Client Secret
az ad app credential reset --id <application-id> --append

# 4. Asignar rol en la suscripción
az role assignment create \
  --assignee <service-principal-id> \
  --role "Advisor Reader" \
  --scope "/subscriptions/{subscription-id}"
```

#### Credenciales Necesarias

Los usuarios deberán proporcionar:
- **Tenant ID**: ID del directorio Azure AD
- **Client ID** (Application ID): ID de la aplicación registrada
- **Client Secret**: Secret generado para la aplicación
- **Subscription ID**: ID de la suscripción a monitorear

### 4.3 SDK y Librerías

**Dependencias nuevas en `requirements.txt`:**

```txt
# Azure SDK Core
azure-identity==1.15.0
azure-mgmt-core==1.4.0

# Azure Advisor API
azure-mgmt-advisor==9.0.0

# Azure Resource Graph (opcional, para queries avanzadas)
azure-mgmt-resourcegraph==8.0.0

# Utilities
azure-common==1.1.28
msrestazure==0.6.4
```

### 4.4 Ejemplo de Código: Azure Advisor Client

```python
"""
Azure Advisor API Client
apps/azure_integration/services/azure_advisor_client.py
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from azure.identity import ClientSecretCredential
from azure.mgmt.advisor import AdvisorManagementClient
from azure.core.exceptions import AzureError, HttpResponseError
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class AzureAdvisorClient:
    """
    Client for interacting with Azure Advisor API.

    Handles authentication, API calls, pagination, rate limiting,
    and data transformation.
    """

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        subscription_id: str
    ):
        """
        Initialize Azure Advisor client.

        Args:
            tenant_id: Azure AD Tenant ID
            client_id: Service Principal Client ID
            client_secret: Service Principal Secret
            subscription_id: Azure Subscription ID
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.subscription_id = subscription_id
        self._client = None

    def _get_client(self) -> AdvisorManagementClient:
        """
        Get authenticated Azure Advisor client (lazy initialization).

        Returns:
            AdvisorManagementClient instance
        """
        if self._client is None:
            try:
                # Create credential
                credential = ClientSecretCredential(
                    tenant_id=self.tenant_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )

                # Create client
                self._client = AdvisorManagementClient(
                    credential=credential,
                    subscription_id=self.subscription_id
                )

                logger.info(
                    f"Azure Advisor client initialized for subscription: "
                    f"{self.subscription_id[:8]}..."
                )

            except Exception as e:
                logger.error(
                    f"Failed to initialize Azure Advisor client: {str(e)}",
                    exc_info=True
                )
                raise

        return self._client

    def validate_credentials(self) -> tuple[bool, str]:
        """
        Validate Azure credentials by making a test API call.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            client = self._get_client()

            # Try to list recommendations (limited to 1)
            list(client.recommendations.list(top=1))

            logger.info(
                f"Credentials validated successfully for subscription: "
                f"{self.subscription_id[:8]}..."
            )
            return True, "Credentials validated successfully"

        except HttpResponseError as e:
            if e.status_code == 401:
                msg = "Invalid credentials or insufficient permissions"
            elif e.status_code == 403:
                msg = "Forbidden: Service Principal lacks required permissions"
            else:
                msg = f"Azure API error: {e.message}"
            logger.error(f"Credential validation failed: {msg}")
            return False, msg

        except AzureError as e:
            msg = f"Azure SDK error: {str(e)}"
            logger.error(f"Credential validation failed: {msg}")
            return False, msg

        except Exception as e:
            msg = f"Unexpected error: {str(e)}"
            logger.error(f"Credential validation failed: {msg}", exc_info=True)
            return False, msg

    def fetch_recommendations(
        self,
        category_filter: Optional[str] = None,
        impact_filter: Optional[str] = None,
        use_cache: bool = True,
        cache_ttl: int = 3600
    ) -> List[Dict[str, Any]]:
        """
        Fetch recommendations from Azure Advisor API.

        Args:
            category_filter: Filter by category (Cost, Security, etc.)
            impact_filter: Filter by impact (High, Medium, Low)
            use_cache: Whether to use cached results
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)

        Returns:
            List of recommendation dictionaries

        Example:
            >>> client = AzureAdvisorClient(...)
            >>> recs = client.fetch_recommendations(category_filter='Cost')
            >>> print(len(recs))
            42
        """
        # Generate cache key
        cache_key = None
        if use_cache:
            cache_key = (
                f"azure_advisor_recs_{self.subscription_id}_"
                f"{category_filter}_{impact_filter}"
            )
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(
                    f"Returning cached recommendations for {self.subscription_id[:8]}..."
                )
                return cached_data

        try:
            client = self._get_client()

            logger.info(
                f"Fetching recommendations from Azure Advisor for "
                f"subscription {self.subscription_id[:8]}... "
                f"(category={category_filter}, impact={impact_filter})"
            )

            # Build filter
            filter_parts = []
            if category_filter:
                filter_parts.append(f"Category eq '{category_filter}'")
            if impact_filter:
                filter_parts.append(f"Impact eq '{impact_filter}'")

            filter_str = " and ".join(filter_parts) if filter_parts else None

            # Fetch recommendations with pagination
            recommendations = []

            # List recommendations (handles pagination automatically)
            recommendation_list = client.recommendations.list(
                filter=filter_str
            )

            for rec in recommendation_list:
                # Transform Azure recommendation to internal format
                transformed = self._transform_recommendation(rec)
                recommendations.append(transformed)

            logger.info(
                f"Fetched {len(recommendations)} recommendations from "
                f"Azure Advisor for {self.subscription_id[:8]}..."
            )

            # Cache results
            if use_cache and cache_key:
                cache.set(cache_key, recommendations, cache_ttl)

            return recommendations

        except HttpResponseError as e:
            logger.error(
                f"Azure API HTTP error while fetching recommendations: "
                f"{e.status_code} - {e.message}",
                exc_info=True
            )
            raise

        except AzureError as e:
            logger.error(
                f"Azure SDK error while fetching recommendations: {str(e)}",
                exc_info=True
            )
            raise

        except Exception as e:
            logger.error(
                f"Unexpected error while fetching recommendations: {str(e)}",
                exc_info=True
            )
            raise

    def _transform_recommendation(self, azure_rec) -> Dict[str, Any]:
        """
        Transform Azure Advisor recommendation to internal format.

        Args:
            azure_rec: Azure Recommendation object

        Returns:
            Dictionary with standardized recommendation data
        """
        # Extract properties
        props = azure_rec.properties or {}
        extended_props = props.get('extendedProperties', {})
        resource_metadata = props.get('resourceMetadata', {})
        short_desc = props.get('shortDescription', {})

        # Map category
        category_mapping = {
            'Cost': 'cost',
            'Security': 'security',
            'Reliability': 'reliability',
            'OperationalExcellence': 'operational_excellence',
            'Performance': 'performance',
        }
        category = category_mapping.get(
            props.get('category'),
            'operational_excellence'
        )

        # Map impact
        impact_mapping = {
            'High': 'high',
            'Medium': 'medium',
            'Low': 'low',
        }
        impact = impact_mapping.get(props.get('impact'), 'medium')

        # Extract savings (if cost recommendation)
        potential_savings = 0.0
        currency = 'USD'
        if category == 'cost':
            # Azure provides annual savings in extendedProperties
            savings_str = extended_props.get('annualSavingsAmount', '0')
            try:
                potential_savings = float(savings_str)
            except (ValueError, TypeError):
                potential_savings = 0.0

            currency = extended_props.get('savingsCurrency', 'USD')

        # Parse resource ID
        resource_id = resource_metadata.get('resourceId', '')
        resource_parts = self._parse_resource_id(resource_id)

        # Build transformed recommendation
        transformed = {
            # Azure metadata
            'azure_recommendation_id': azure_rec.id,
            'azure_recommendation_name': azure_rec.name,

            # Category and impact
            'category': category,
            'business_impact': impact,

            # Recommendation details
            'recommendation': short_desc.get('problem', ''),
            'potential_benefits': short_desc.get('solution', ''),

            # Resource information
            'subscription_id': resource_parts.get('subscription_id', ''),
            'subscription_name': extended_props.get('subscriptionName', ''),
            'resource_group': resource_parts.get('resource_group', ''),
            'resource_name': resource_parts.get('resource_name', ''),
            'resource_type': resource_metadata.get('resourceType', ''),

            # Cost information
            'potential_savings': potential_savings,
            'currency': currency,

            # Additional metadata
            'advisor_score_impact': extended_props.get('score', 0),
            'last_updated': props.get('lastUpdated'),
            'suppression_ids': props.get('suppressionIds', []),

            # Raw data for debugging
            'raw_extended_properties': extended_props,
        }

        return transformed

    def _parse_resource_id(self, resource_id: str) -> Dict[str, str]:
        """
        Parse Azure Resource ID into components.

        Azure Resource ID format:
        /subscriptions/{subscriptionId}/resourceGroups/{resourceGroup}/
        providers/{provider}/{resourceType}/{resourceName}

        Args:
            resource_id: Full Azure Resource ID

        Returns:
            Dictionary with parsed components
        """
        parts = {}

        if not resource_id:
            return parts

        segments = resource_id.split('/')

        try:
            # Find indices
            if 'subscriptions' in segments:
                idx = segments.index('subscriptions')
                parts['subscription_id'] = segments[idx + 1]

            if 'resourceGroups' in segments:
                idx = segments.index('resourceGroups')
                parts['resource_group'] = segments[idx + 1]

            if 'providers' in segments:
                idx = segments.index('providers')
                # Resource name is typically the last segment
                parts['resource_name'] = segments[-1]

        except (IndexError, ValueError):
            logger.warning(f"Failed to parse resource ID: {resource_id}")

        return parts

    def get_subscription_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the Azure subscription.

        Returns:
            Dictionary with subscription information
        """
        try:
            # This would use Azure Resource Manager API to get subscription details
            # For now, returning minimal data
            return {
                'subscription_id': self.subscription_id,
                'tenant_id': self.tenant_id,
            }
        except Exception as e:
            logger.error(
                f"Failed to get subscription metadata: {str(e)}",
                exc_info=True
            )
            return {}
```

---

## 5. Modelo de Datos

### 5.1 Nuevos Modelos

#### AzureSubscription (apps/azure_integration/models.py)

```python
"""
Azure Integration models
"""

import uuid
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from apps.clients.models import Client
from apps.authentication.models import User
from .encryption import encrypt_credential, decrypt_credential


class AzureSubscription(models.Model):
    """
    Azure Subscription configuration with Service Principal credentials.

    Stores encrypted credentials for accessing Azure Advisor API.
    Each client can have multiple Azure subscriptions.
    """

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error - Credentials Invalid'),
        ('pending', 'Pending Validation'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationship with Client
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='azure_advisor_subscriptions',
        help_text="Client that owns this Azure subscription"
    )

    # Azure Subscription Information
    subscription_id = models.CharField(
        max_length=36,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
                message='Invalid Azure Subscription ID format (must be GUID)',
                code='invalid_subscription_id'
            )
        ],
        help_text="Azure Subscription ID (GUID format)"
    )
    subscription_name = models.CharField(
        max_length=255,
        help_text="Friendly name for this subscription"
    )

    # Azure AD / Service Principal Configuration
    tenant_id = models.CharField(
        max_length=36,
        validators=[
            RegexValidator(
                regex=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
                message='Invalid Azure Tenant ID format (must be GUID)'
            )
        ],
        help_text="Azure AD Tenant ID"
    )

    # Encrypted Credentials (Service Principal)
    client_id_encrypted = models.BinaryField(
        help_text="Encrypted Azure AD Application (Client) ID"
    )
    client_secret_encrypted = models.BinaryField(
        help_text="Encrypted Azure AD Application Client Secret"
    )

    # Status and Health Monitoring
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Enable/disable automatic recommendation fetching"
    )

    # Last Sync Information
    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful recommendation fetch"
    )
    last_sync_status = models.CharField(
        max_length=50,
        blank=True,
        help_text="Status of last sync attempt"
    )
    last_error_message = models.TextField(
        blank=True,
        help_text="Last error message if sync failed"
    )
    consecutive_failures = models.IntegerField(
        default=0,
        help_text="Number of consecutive sync failures"
    )

    # Configuration
    auto_fetch_enabled = models.BooleanField(
        default=True,
        help_text="Automatically fetch recommendations on schedule"
    )
    fetch_frequency_hours = models.IntegerField(
        default=24,
        help_text="How often to fetch recommendations (hours)"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_azure_subscriptions'
    )
    validated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When credentials were last validated"
    )

    class Meta:
        db_table = 'azure_advisor_subscriptions'
        unique_together = [['client', 'subscription_id']]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', 'is_active']),
            models.Index(fields=['subscription_id']),
            models.Index(fields=['status']),
            models.Index(fields=['last_sync_at']),
        ]
        verbose_name = 'Azure Subscription'
        verbose_name_plural = 'Azure Subscriptions'

    def __str__(self):
        return f"{self.subscription_name} ({self.subscription_id[:8]}...)"

    # Credential Management Methods

    def set_client_id(self, client_id: str):
        """Encrypt and store Client ID."""
        self.client_id_encrypted = encrypt_credential(client_id)

    def get_client_id(self) -> str:
        """Decrypt and return Client ID."""
        if not self.client_id_encrypted:
            return ''
        return decrypt_credential(self.client_id_encrypted)

    def set_client_secret(self, client_secret: str):
        """Encrypt and store Client Secret."""
        self.client_secret_encrypted = encrypt_credential(client_secret)

    def get_client_secret(self) -> str:
        """Decrypt and return Client Secret."""
        if not self.client_secret_encrypted:
            return ''
        return decrypt_credential(self.client_secret_encrypted)

    # Status Management Methods

    def mark_sync_success(self):
        """Mark last sync as successful."""
        self.last_sync_at = timezone.now()
        self.last_sync_status = 'success'
        self.last_error_message = ''
        self.consecutive_failures = 0
        self.status = 'active'
        self.save(update_fields=[
            'last_sync_at', 'last_sync_status', 'last_error_message',
            'consecutive_failures', 'status', 'updated_at'
        ])

    def mark_sync_failure(self, error_message: str):
        """Mark last sync as failed."""
        self.last_sync_at = timezone.now()
        self.last_sync_status = 'failed'
        self.last_error_message = error_message
        self.consecutive_failures += 1

        # Disable after 5 consecutive failures
        if self.consecutive_failures >= 5:
            self.status = 'error'
            self.is_active = False

        self.save(update_fields=[
            'last_sync_at', 'last_sync_status', 'last_error_message',
            'consecutive_failures', 'status', 'is_active', 'updated_at'
        ])

    def mark_validated(self):
        """Mark credentials as validated."""
        self.validated_at = timezone.now()
        self.status = 'active'
        self.save(update_fields=['validated_at', 'status', 'updated_at'])

    @property
    def needs_fetch(self) -> bool:
        """Check if subscription needs recommendation fetch."""
        if not self.is_active or not self.auto_fetch_enabled:
            return False

        if not self.last_sync_at:
            return True

        # Calculate next fetch time
        next_fetch = self.last_sync_at + timezone.timedelta(
            hours=self.fetch_frequency_hours
        )

        return timezone.now() >= next_fetch

    @property
    def health_status(self) -> str:
        """Get health status indicator."""
        if self.status == 'error':
            return 'unhealthy'
        elif self.consecutive_failures >= 3:
            return 'degraded'
        elif self.status == 'active':
            return 'healthy'
        else:
            return 'unknown'
```

### 5.2 Cambios en Modelos Existentes

#### Report Model (apps/reports/models.py)

**Cambios necesarios:**

```python
class Report(models.Model):
    # ... campos existentes ...

    # NEW: Source type field
    SOURCE_CHOICES = [
        ('csv', 'CSV Upload'),
        ('azure_api', 'Azure API'),
    ]

    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='csv',
        help_text="Source of recommendations data"
    )

    # NEW: Link to Azure Subscription (for API-sourced reports)
    azure_subscription = models.ForeignKey(
        'azure_integration.AzureSubscription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        help_text="Azure subscription (if source is azure_api)"
    )

    # MODIFIED: csv_file is now optional
    csv_file = models.FileField(
        upload_to='csv_uploads/%Y/%m/',
        null=True,
        blank=True,
        help_text="Uploaded Azure Advisor CSV file (for CSV source)"
    )

    # NEW: Fetch metadata (for API-sourced reports)
    fetch_started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When Azure API fetch started"
    )
    fetch_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When Azure API fetch completed"
    )

    # ... resto de campos existentes ...

    class Meta:
        # ... existing meta ...
        indexes = [
            # ... existing indexes ...
            models.Index(fields=['source', 'status']),
            models.Index(fields=['azure_subscription', 'created_at']),
        ]
```

#### Recommendation Model (apps/reports/models.py)

**Cambios necesarios:**

```python
class Recommendation(models.Model):
    # ... campos existentes ...

    # NEW: Azure-specific fields
    azure_recommendation_id = models.CharField(
        max_length=500,
        blank=True,
        db_index=True,
        help_text="Azure Advisor recommendation ID"
    )
    azure_recommendation_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Azure Advisor recommendation name"
    )
    last_updated_by_azure = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last update timestamp from Azure"
    )
    suppression_ids = models.JSONField(
        default=list,
        blank=True,
        help_text="Azure suppression IDs if recommendation is suppressed"
    )

    # ... resto de campos existentes ...

    class Meta:
        # ... existing meta ...
        indexes = [
            # ... existing indexes ...
            models.Index(fields=['azure_recommendation_id']),
        ]
```

#### Client Model (apps/clients/models.py)

**Cambios sugeridos:**

```python
class Client(models.Model):
    # ... campos existentes ...

    # ENHANCED: More detailed Azure configuration
    has_azure_integration = models.BooleanField(
        default=False,
        help_text="Client has Azure API integration configured"
    )

    # ... resto de campos existentes ...

    @property
    def active_azure_subscriptions_count(self):
        """Count active Azure subscriptions with API integration."""
        return self.azure_advisor_subscriptions.filter(
            is_active=True,
            status='active'
        ).count()
```

---

## 6. Flujo de Datos

### 6.1 Flujo Completo: Azure API to Report

```
┌────────────────────────────────────────────────────────────────┐
│ STEP 1: User Initiates Report Generation (Azure API Source)   │
└────────────────────┬───────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Frontend: POST /api/reports/                                    │
│ {                                                               │
│   "client_id": "uuid",                                          │
│   "source": "azure_api",                                        │
│   "azure_subscription_id": "uuid",                              │
│   "report_type": "detailed"                                     │
│ }                                                               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Backend Creates Report Record                          │
│ - Validate client and subscription                             │
│ - Create Report instance (status='pending')                    │
│ - Set source='azure_api'                                       │
│ - Link to AzureSubscription                                    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Dispatch Celery Task                                   │
│ fetch_azure_advisor_recommendations.delay(report_id)            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Celery Worker Executes Task                            │
│ - Update report status to 'processing'                         │
│ - Get AzureSubscription credentials                            │
│ - Initialize AzureAdvisorClient                                │
│ - Validate credentials (if not recently validated)             │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Fetch from Azure Advisor API                           │
│ - Call Azure Advisor API                                       │
│ - Handle pagination (if many recommendations)                  │
│ - Transform Azure format to internal format                    │
│ - Apply filters (if specified)                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Store Recommendations                                  │
│ - Create Recommendation instances in database                  │
│ - Link to Report                                               │
│ - Bulk create (batch_size=1000)                                │
│ - Calculate statistics                                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: Update Report Status                                   │
│ - Set status='completed'                                       │
│ - Set processing_completed_at timestamp                        │
│ - Save analysis_data with statistics                           │
│ - Mark subscription sync as successful                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: Auto-trigger Report Generation                         │
│ generate_report.delay(report_id, format_type='both')            │
│ - Generate HTML report                                         │
│ - Generate PDF report                                          │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Flujo de Validación de Credenciales

```
┌──────────────────────────────────────────────────────────────┐
│ User Adds Azure Subscription via Frontend                   │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────┐
│ POST /api/azure-subscriptions/                               │
│ {                                                            │
│   "subscription_id": "...",                                  │
│   "subscription_name": "Production",                         │
│   "tenant_id": "...",                                        │
│   "client_id": "...",                                        │
│   "client_secret": "..."                                     │
│ }                                                            │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────┐
│ Backend Validates and Encrypts                               │
│ - Validate GUID formats                                      │
│ - Encrypt client_id and client_secret                        │
│ - Create AzureSubscription instance (status='pending')       │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────┐
│ Dispatch Validation Task                                     │
│ validate_azure_subscription.delay(subscription_id)           │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────┐
│ Celery Worker: Validation                                    │
│ - Initialize AzureAdvisorClient                              │
│ - Call validate_credentials()                                │
│ - Test API call (list recommendations, limit 1)              │
└────────────────┬─────────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌─────────────┐   ┌─────────────────┐
│  SUCCESS    │   │    FAILURE      │
└──────┬──────┘   └────────┬────────┘
       │                   │
       ▼                   ▼
┌─────────────┐   ┌─────────────────┐
│ Set status  │   │ Set status to   │
│ to 'active' │   │ 'error'         │
│             │   │ Save error msg  │
└─────────────┘   └─────────────────┘
```

---

## 7. Seguridad y Credenciales

### 7.1 Encriptación de Credenciales

**Archivo:** `apps/azure_integration/encryption.py`

```python
"""
Credential encryption utilities for Azure credentials.

Uses Fernet symmetric encryption with key derived from Django SECRET_KEY.
"""

from cryptography.fernet import Fernet
from django.conf import settings
import base64
import hashlib


def _get_fernet_key() -> bytes:
    """
    Derive Fernet key from Django SECRET_KEY.

    Returns:
        32-byte URL-safe base64-encoded key
    """
    # Use SHA-256 to derive a consistent 32-byte key
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(key)


def encrypt_credential(plaintext: str) -> bytes:
    """
    Encrypt a credential string.

    Args:
        plaintext: Credential to encrypt (Client ID or Secret)

    Returns:
        Encrypted bytes suitable for BinaryField storage
    """
    if not plaintext:
        return b''

    fernet = Fernet(_get_fernet_key())
    encrypted = fernet.encrypt(plaintext.encode('utf-8'))
    return encrypted


def decrypt_credential(encrypted_bytes: bytes) -> str:
    """
    Decrypt a credential.

    Args:
        encrypted_bytes: Encrypted credential from database

    Returns:
        Decrypted plaintext string
    """
    if not encrypted_bytes:
        return ''

    fernet = Fernet(_get_fernet_key())
    decrypted = fernet.decrypt(encrypted_bytes)
    return decrypted.decode('utf-8')
```

**Requisitos de Seguridad:**

1. **SECRET_KEY robusto**: El `SECRET_KEY` de Django debe ser fuerte y único por entorno
2. **Rotación de credenciales**: Implementar flujo para actualizar Client Secrets sin downtime
3. **Auditoría**: Log de acceso a credenciales (quién, cuándo)
4. **Permisos**: Solo usuarios con permisos de admin pueden gestionar Azure Subscriptions

### 7.2 Variables de Entorno

```bash
# .env (producción)

# Django
SECRET_KEY=<strong-secret-key-min-50-chars>
DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings.production

# Azure (opcional - para autenticación de la app misma)
AZURE_CLIENT_ID=<app-client-id>
AZURE_CLIENT_SECRET=<app-client-secret>
AZURE_TENANT_ID=<tenant-id>

# Encryption
# (Opcional) Separate encryption key for credentials
CREDENTIALS_ENCRYPTION_KEY=<base64-encoded-key>
```

### 7.3 Permisos Azure Requeridos

**Service Principal debe tener:**

1. **Advisor Reader** (preferido):
   ```bash
   az role assignment create \
     --assignee <service-principal-id> \
     --role "Advisor Reader" \
     --scope "/subscriptions/{subscription-id}"
   ```

2. **O Reader** (más amplio):
   ```bash
   az role assignment create \
     --assignee <service-principal-id> \
     --role "Reader" \
     --scope "/subscriptions/{subscription-id}"
   ```

**Verificación de permisos:**
```bash
# Listar role assignments
az role assignment list \
  --assignee <service-principal-id> \
  --subscription <subscription-id>
```

---

## 8. Coexistencia de Flujos (CSV vs API)

### 8.1 Estrategia de Coexistencia

**Principio:** Ambos flujos usan el mismo modelo de datos (`Recommendation`) pero con diferentes fuentes.

**Diferencias clave:**

| Aspecto | CSV Upload | Azure API |
|---------|-----------|-----------|
| Campo `Report.source` | `'csv'` | `'azure_api'` |
| Campo `Report.csv_file` | Requerido | NULL |
| Campo `Report.azure_subscription` | NULL | Requerido |
| Celery Task | `process_csv_file` | `fetch_azure_advisor_recommendations` |
| Datos únicos | `csv_row_number` | `azure_recommendation_id`, `last_updated_by_azure` |

### 8.2 UI/UX: Selección de Fuente

**Frontend: Componente de Creación de Reporte**

```typescript
// frontend/src/components/reports/CreateReportModal.tsx

interface CreateReportFormData {
  client_id: string;
  report_type: string;
  title?: string;

  // Source selection
  source: 'csv' | 'azure_api';

  // CSV-specific
  csv_file?: File;

  // Azure API-specific
  azure_subscription_id?: string;
}

const CreateReportModal: React.FC = () => {
  const [source, setSource] = useState<'csv' | 'azure_api'>('csv');

  return (
    <Modal>
      {/* Client selection */}
      <ClientSelector />

      {/* Source Type Toggle */}
      <SourceTypeToggle
        value={source}
        onChange={setSource}
        options={[
          { value: 'csv', label: 'Upload CSV File', icon: <UploadIcon /> },
          { value: 'azure_api', label: 'Fetch from Azure', icon: <CloudIcon /> }
        ]}
      />

      {/* Conditional rendering based on source */}
      {source === 'csv' && (
        <CSVFileUploader
          onFileSelect={(file) => { /* ... */ }}
        />
      )}

      {source === 'azure_api' && (
        <AzureSubscriptionSelector
          clientId={formData.client_id}
          onSelect={(subscriptionId) => { /* ... */ }}
        />
      )}

      {/* Report type and other options */}
      <ReportTypeSelector />

      <Button onClick={handleSubmit}>
        {source === 'csv' ? 'Upload & Process' : 'Fetch Recommendations'}
      </Button>
    </Modal>
  );
};
```

### 8.3 Backend: Routing basado en Source

```python
# apps/reports/views.py

class ReportViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Reports with dual source support.
    """

    def create(self, request, *args, **kwargs):
        """
        Create a new report from either CSV or Azure API.
        """
        source = request.data.get('source', 'csv')

        # Validate source
        if source not in ['csv', 'azure_api']:
            return Response(
                {'error': 'Invalid source. Must be "csv" or "azure_api".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Source-specific validation
        if source == 'csv':
            if 'csv_file' not in request.FILES:
                return Response(
                    {'error': 'CSV file is required for CSV source.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        elif source == 'azure_api':
            if 'azure_subscription_id' not in request.data:
                return Response(
                    {'error': 'Azure subscription ID is required for API source.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate subscription exists and is active
            try:
                subscription = AzureSubscription.objects.get(
                    id=request.data['azure_subscription_id'],
                    client_id=request.data['client'],
                    is_active=True
                )
            except AzureSubscription.DoesNotExist:
                return Response(
                    {'error': 'Invalid or inactive Azure subscription.'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Use serializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = serializer.save()

        # Dispatch appropriate Celery task based on source
        if source == 'csv':
            from apps.reports.tasks import process_csv_file
            process_csv_file.delay(str(report.id))

        elif source == 'azure_api':
            from apps.azure_integration.tasks import fetch_azure_advisor_recommendations
            fetch_azure_advisor_recommendations.delay(str(report.id))

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
```

---

## 9. Tareas Asíncronas (Celery)

### 9.1 Nueva Tarea: fetch_azure_advisor_recommendations

**Archivo:** `apps/azure_integration/tasks.py`

```python
"""
Celery tasks for Azure Advisor integration.
"""

import logging
from celery import shared_task
from celery.exceptions import Ignore, SoftTimeLimitExceeded
from django.utils import timezone
from django.db import transaction

from apps.reports.models import Report, Recommendation
from apps.azure_integration.models import AzureSubscription
from apps.azure_integration.services.azure_advisor_client import AzureAdvisorClient

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=120,  # 2 minutes
    soft_time_limit=900,      # 15 minutes
    time_limit=960            # 16 minutes
)
def fetch_azure_advisor_recommendations(self, report_id: str):
    """
    Fetch recommendations from Azure Advisor API and populate Report.

    Args:
        report_id: UUID of the Report instance

    Returns:
        dict: Task result with status and details
    """
    logger.info(f"Starting Azure Advisor fetch task for report {report_id}")

    try:
        # Get report instance
        report = Report.objects.select_related(
            'azure_subscription', 'client'
        ).get(id=report_id)

        # Validate source
        if report.source != 'azure_api':
            raise ValueError(
                f"Report source is '{report.source}', expected 'azure_api'"
            )

        # Validate Azure subscription
        if not report.azure_subscription:
            raise ValueError("Report has no Azure subscription linked")

        subscription = report.azure_subscription

        # Update status
        report.status = 'processing'
        report.fetch_started_at = timezone.now()
        report.save(update_fields=['status', 'fetch_started_at'])

        logger.info(
            f"Fetching recommendations from Azure for subscription: "
            f"{subscription.subscription_name}"
        )

        # Initialize Azure client
        client = AzureAdvisorClient(
            tenant_id=subscription.tenant_id,
            client_id=subscription.get_client_id(),
            client_secret=subscription.get_client_secret(),
            subscription_id=subscription.subscription_id
        )

        # Validate credentials (if not recently validated)
        if not subscription.validated_at or (
            timezone.now() - subscription.validated_at
        ).days > 7:
            logger.info("Validating Azure credentials...")
            is_valid, message = client.validate_credentials()

            if not is_valid:
                raise Exception(f"Credential validation failed: {message}")

            subscription.mark_validated()

        # Fetch recommendations from Azure
        azure_recommendations = client.fetch_recommendations(
            use_cache=False  # Don't use cache for explicit report generation
        )

        logger.info(
            f"Fetched {len(azure_recommendations)} recommendations from Azure"
        )

        # Transform and save recommendations
        with transaction.atomic():
            recommendation_instances = []

            for azure_rec in azure_recommendations:
                recommendation = Recommendation(
                    report=report,

                    # Standard fields
                    category=azure_rec['category'],
                    business_impact=azure_rec['business_impact'],
                    recommendation=azure_rec['recommendation'][:5000],
                    potential_benefits=azure_rec.get('potential_benefits', '')[:5000],

                    # Resource information
                    subscription_id=azure_rec.get('subscription_id', '')[:255],
                    subscription_name=azure_rec.get('subscription_name', '')[:255],
                    resource_group=azure_rec.get('resource_group', '')[:255],
                    resource_name=azure_rec.get('resource_name', '')[:255],
                    resource_type=azure_rec.get('resource_type', '')[:255],

                    # Financial impact
                    potential_savings=azure_rec.get('potential_savings', 0),
                    currency=azure_rec.get('currency', 'USD')[:3],

                    # Azure-specific fields
                    azure_recommendation_id=azure_rec.get('azure_recommendation_id', '')[:500],
                    azure_recommendation_name=azure_rec.get('azure_recommendation_name', '')[:255],
                    advisor_score_impact=azure_rec.get('advisor_score_impact', 0),
                    last_updated_by_azure=azure_rec.get('last_updated'),
                    suppression_ids=azure_rec.get('suppression_ids', []),
                )
                recommendation_instances.append(recommendation)

            # Bulk create recommendations
            if recommendation_instances:
                Recommendation.objects.bulk_create(
                    recommendation_instances,
                    batch_size=1000
                )
                logger.info(
                    f"Created {len(recommendation_instances)} recommendations "
                    f"for report {report_id}"
                )

            # Calculate statistics
            from django.db.models import Sum, Count

            stats = Recommendation.objects.filter(report=report).aggregate(
                total_recommendations=Count('id'),
                total_savings=Sum('potential_savings'),
                cost_recommendations=Count('id', filter=models.Q(category='cost')),
                security_recommendations=Count('id', filter=models.Q(category='security')),
                reliability_recommendations=Count('id', filter=models.Q(category='reliability')),
                performance_recommendations=Count('id', filter=models.Q(category='performance')),
                operational_recommendations=Count('id', filter=models.Q(category='operational_excellence')),
            )

            # Update report
            report.analysis_data = {
                'total_recommendations': stats['total_recommendations'],
                'total_potential_savings': float(stats['total_savings'] or 0),
                'by_category': {
                    'cost': stats['cost_recommendations'],
                    'security': stats['security_recommendations'],
                    'reliability': stats['reliability_recommendations'],
                    'performance': stats['performance_recommendations'],
                    'operational_excellence': stats['operational_recommendations'],
                },
                'fetch_source': 'azure_api',
                'subscription_id': subscription.subscription_id,
                'subscription_name': subscription.subscription_name,
            }
            report.status = 'completed'
            report.fetch_completed_at = timezone.now()
            report.processing_completed_at = timezone.now()
            report.error_message = ''
            report.save(update_fields=[
                'analysis_data', 'status', 'fetch_completed_at',
                'processing_completed_at', 'error_message'
            ])

        # Mark subscription sync as successful
        subscription.mark_sync_success()

        logger.info(
            f"Azure Advisor fetch completed successfully for report {report_id}"
        )

        # Auto-trigger report generation
        try:
            from apps.reports.tasks import generate_report
            generate_report.delay(str(report_id), format_type='both')
            logger.info(f"Report generation task dispatched for {report_id}")
        except Exception as e:
            logger.error(
                f"Failed to trigger report generation for {report_id}: {str(e)}",
                exc_info=True
            )

        return {
            'status': 'success',
            'report_id': str(report_id),
            'recommendations_count': len(recommendation_instances),
            'statistics': report.analysis_data,
        }

    except Report.DoesNotExist:
        error_msg = f"Report with ID {report_id} not found"
        logger.error(error_msg)
        raise Ignore()

    except SoftTimeLimitExceeded:
        error_msg = "Azure API fetch timed out after 15 minutes"
        logger.error(f"Task timed out for report {report_id}")

        try:
            report = Report.objects.get(id=report_id)
            report.fail_processing(error_msg)
        except:
            pass

        return {'status': 'error', 'error': error_msg}

    except Exception as e:
        error_msg = f"Azure API fetch error: {str(e)}"
        logger.error(
            f"Failed to fetch Azure recommendations for report {report_id}: {error_msg}",
            exc_info=True
        )

        try:
            report = Report.objects.get(id=report_id)
            report.fail_processing(error_msg)

            # Mark subscription sync as failed
            if report.azure_subscription:
                report.azure_subscription.mark_sync_failure(error_msg)
        except:
            pass

        # Retry with exponential backoff
        if self.request.retries < 3:
            raise self.retry(exc=e, countdown=120 * (self.request.retries + 1))

        return {'status': 'error', 'error': error_msg}


@shared_task(bind=True)
def validate_azure_subscription(self, subscription_id: str):
    """
    Validate Azure subscription credentials.

    Args:
        subscription_id: UUID of AzureSubscription instance

    Returns:
        dict: Validation result
    """
    logger.info(f"Validating Azure subscription {subscription_id}")

    try:
        subscription = AzureSubscription.objects.get(id=subscription_id)

        # Initialize client
        client = AzureAdvisorClient(
            tenant_id=subscription.tenant_id,
            client_id=subscription.get_client_id(),
            client_secret=subscription.get_client_secret(),
            subscription_id=subscription.subscription_id
        )

        # Validate
        is_valid, message = client.validate_credentials()

        if is_valid:
            subscription.mark_validated()
            logger.info(
                f"Subscription {subscription.subscription_name} validated successfully"
            )
            return {'status': 'success', 'message': message}
        else:
            subscription.mark_sync_failure(message)
            logger.error(
                f"Subscription {subscription.subscription_name} validation failed: {message}"
            )
            return {'status': 'error', 'message': message}

    except AzureSubscription.DoesNotExist:
        logger.error(f"Azure subscription {subscription_id} not found")
        return {'status': 'error', 'message': 'Subscription not found'}

    except Exception as e:
        error_msg = str(e)
        logger.error(
            f"Subscription validation failed: {error_msg}",
            exc_info=True
        )

        try:
            subscription = AzureSubscription.objects.get(id=subscription_id)
            subscription.mark_sync_failure(error_msg)
        except:
            pass

        return {'status': 'error', 'message': error_msg}


@shared_task
def scheduled_fetch_azure_recommendations():
    """
    Scheduled task to auto-fetch recommendations for all active subscriptions.

    This task should be configured in Celery Beat to run periodically
    (e.g., daily or every 12 hours).
    """
    logger.info("Starting scheduled Azure recommendations fetch")

    # Get all subscriptions that need fetching
    subscriptions = AzureSubscription.objects.filter(
        is_active=True,
        status='active',
        auto_fetch_enabled=True
    )

    fetched_count = 0

    for subscription in subscriptions:
        if subscription.needs_fetch:
            logger.info(
                f"Auto-fetching recommendations for: {subscription.subscription_name}"
            )

            # Create a background report for this subscription
            from apps.reports.models import Report

            report = Report.objects.create(
                client=subscription.client,
                source='azure_api',
                azure_subscription=subscription,
                report_type='detailed',
                title=f"Auto-generated Report - {subscription.subscription_name}",
                status='pending'
            )

            # Dispatch fetch task
            fetch_azure_advisor_recommendations.delay(str(report.id))
            fetched_count += 1

    logger.info(
        f"Scheduled fetch completed. Dispatched {fetched_count} fetch tasks."
    )

    return {
        'status': 'success',
        'subscriptions_processed': fetched_count
    }
```

### 9.2 Configuración Celery Beat

**Archivo:** `azure_advisor_reports/celery.py`

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    # ... existing tasks ...

    # NEW: Auto-fetch Azure Advisor recommendations daily at 2 AM
    'scheduled-fetch-azure-recommendations': {
        'task': 'apps.azure_integration.tasks.scheduled_fetch_azure_recommendations',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2:00 AM
    },
}
```

---

## 10. API REST Endpoints

### 10.1 Nuevos Endpoints: Azure Subscriptions

```python
# apps/azure_integration/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AzureSubscriptionViewSet

router = DefaultRouter()
router.register(r'azure-subscriptions', AzureSubscriptionViewSet, basename='azure-subscription')

urlpatterns = [
    path('', include(router.urls)),
]
```

```python
# apps/azure_integration/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import AzureSubscription
from .serializers import AzureSubscriptionSerializer, AzureSubscriptionCreateSerializer
from .tasks import validate_azure_subscription


class AzureSubscriptionViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing Azure Subscriptions.

    Endpoints:
    - GET /api/azure-subscriptions/ - List all subscriptions
    - POST /api/azure-subscriptions/ - Create new subscription
    - GET /api/azure-subscriptions/{id}/ - Get subscription details
    - PUT/PATCH /api/azure-subscriptions/{id}/ - Update subscription
    - DELETE /api/azure-subscriptions/{id}/ - Delete subscription
    - POST /api/azure-subscriptions/{id}/validate/ - Validate credentials
    - POST /api/azure-subscriptions/{id}/test-connection/ - Test Azure connection
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['client', 'status', 'is_active']

    def get_queryset(self):
        """Filter subscriptions based on user permissions."""
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return AzureSubscription.objects.all()

        # Regular users see only their clients' subscriptions
        return AzureSubscription.objects.filter(
            client__in=user.accessible_clients.all()
        )

    def get_serializer_class(self):
        """Use different serializer for create action."""
        if self.action == 'create':
            return AzureSubscriptionCreateSerializer
        return AzureSubscriptionSerializer

    def perform_create(self, serializer):
        """
        Create subscription and trigger validation.
        """
        subscription = serializer.save(created_by=self.request.user)

        # Trigger async validation
        validate_azure_subscription.delay(str(subscription.id))

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """
        Manually trigger credential validation.

        POST /api/azure-subscriptions/{id}/validate/
        """
        subscription = self.get_object()

        # Dispatch validation task
        task = validate_azure_subscription.delay(str(subscription.id))

        return Response({
            'message': 'Validation task dispatched',
            'task_id': task.id,
            'subscription_id': str(subscription.id)
        })

    @action(detail=True, methods=['get'])
    def health(self, request, pk=None):
        """
        Get health status of subscription.

        GET /api/azure-subscriptions/{id}/health/
        """
        subscription = self.get_object()

        return Response({
            'subscription_id': str(subscription.id),
            'subscription_name': subscription.subscription_name,
            'health_status': subscription.health_status,
            'status': subscription.status,
            'is_active': subscription.is_active,
            'last_sync_at': subscription.last_sync_at,
            'last_sync_status': subscription.last_sync_status,
            'consecutive_failures': subscription.consecutive_failures,
            'needs_fetch': subscription.needs_fetch,
        })
```

### 10.2 Serializers

```python
# apps/azure_integration/serializers.py

from rest_framework import serializers
from .models import AzureSubscription


class AzureSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for AzureSubscription (read operations).

    Excludes encrypted credential fields for security.
    """

    health_status = serializers.ReadOnlyField()
    needs_fetch = serializers.ReadOnlyField()
    client_name = serializers.CharField(source='client.company_name', read_only=True)

    class Meta:
        model = AzureSubscription
        fields = [
            'id', 'client', 'client_name', 'subscription_id', 'subscription_name',
            'tenant_id', 'status', 'is_active', 'health_status', 'needs_fetch',
            'last_sync_at', 'last_sync_status', 'last_error_message',
            'consecutive_failures', 'auto_fetch_enabled', 'fetch_frequency_hours',
            'created_at', 'updated_at', 'validated_at'
        ]
        read_only_fields = [
            'id', 'status', 'last_sync_at', 'last_sync_status',
            'last_error_message', 'consecutive_failures', 'validated_at',
            'created_at', 'updated_at'
        ]


class AzureSubscriptionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating AzureSubscription.

    Accepts plaintext credentials and encrypts them.
    """

    client_id = serializers.CharField(
        write_only=True,
        help_text="Azure AD Application (Client) ID"
    )
    client_secret = serializers.CharField(
        write_only=True,
        help_text="Azure AD Application Client Secret"
    )

    class Meta:
        model = AzureSubscription
        fields = [
            'id', 'client', 'subscription_id', 'subscription_name',
            'tenant_id', 'client_id', 'client_secret', 'is_active',
            'auto_fetch_enabled', 'fetch_frequency_hours'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        """
        Create subscription with encrypted credentials.
        """
        # Extract credentials
        client_id = validated_data.pop('client_id')
        client_secret = validated_data.pop('client_secret')

        # Create instance
        subscription = AzureSubscription(**validated_data)

        # Encrypt and set credentials
        subscription.set_client_id(client_id)
        subscription.set_client_secret(client_secret)

        subscription.save()

        return subscription
```

### 10.3 Endpoints Modificados: Reports

```python
# apps/reports/serializers.py

class ReportSerializer(serializers.ModelSerializer):
    # ... existing fields ...

    # NEW: Support for Azure API source
    azure_subscription = serializers.PrimaryKeyRelatedField(
        queryset=AzureSubscription.objects.all(),
        required=False,
        allow_null=True
    )
    azure_subscription_name = serializers.CharField(
        source='azure_subscription.subscription_name',
        read_only=True
    )

    class Meta:
        model = Report
        fields = [
            # ... existing fields ...
            'source',  # NEW
            'azure_subscription',  # NEW
            'azure_subscription_name',  # NEW
            'fetch_started_at',  # NEW
            'fetch_completed_at',  # NEW
            # ... rest of fields ...
        ]

    def validate(self, data):
        """
        Validate source-specific requirements.
        """
        source = data.get('source', 'csv')

        if source == 'csv':
            # CSV file required
            if not data.get('csv_file') and not self.instance:
                raise serializers.ValidationError({
                    'csv_file': 'CSV file is required when source is "csv"'
                })

        elif source == 'azure_api':
            # Azure subscription required
            if not data.get('azure_subscription'):
                raise serializers.ValidationError({
                    'azure_subscription': 'Azure subscription is required when source is "azure_api"'
                })

            # Validate subscription is active
            subscription = data.get('azure_subscription')
            if not subscription.is_active or subscription.status != 'active':
                raise serializers.ValidationError({
                    'azure_subscription': 'Selected Azure subscription is not active'
                })

        return data
```

---

## 11. Frontend (React)

### 11.1 Nuevos Componentes

#### AzureSubscriptionManager

```typescript
// frontend/src/components/azure/AzureSubscriptionManager.tsx

import React, { useState, useEffect } from 'react';
import {
  Table, Button, Modal, Form, Input, Select, Tag, Space,
  message, Popconfirm, Tooltip
} from 'antd';
import {
  PlusOutlined, CloudOutlined, CheckCircleOutlined,
  WarningOutlined, CloseCircleOutlined, SyncOutlined
} from '@ant-design/icons';
import { azureSubscriptionApi } from '../../services/api';
import type { AzureSubscription } from '../../types';

export const AzureSubscriptionManager: React.FC<{ clientId: string }> = ({
  clientId
}) => {
  const [subscriptions, setSubscriptions] = useState<AzureSubscription[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadSubscriptions();
  }, [clientId]);

  const loadSubscriptions = async () => {
    setLoading(true);
    try {
      const data = await azureSubscriptionApi.list({ client: clientId });
      setSubscriptions(data);
    } catch (error) {
      message.error('Failed to load Azure subscriptions');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (values: any) => {
    try {
      await azureSubscriptionApi.create({
        ...values,
        client: clientId,
      });
      message.success('Azure subscription added successfully. Validating credentials...');
      setModalVisible(false);
      form.resetFields();
      loadSubscriptions();
    } catch (error) {
      message.error('Failed to add Azure subscription');
    }
  };

  const handleValidate = async (subscriptionId: string) => {
    try {
      await azureSubscriptionApi.validate(subscriptionId);
      message.info('Validation task dispatched. This may take a few moments.');
      setTimeout(loadSubscriptions, 3000);
    } catch (error) {
      message.error('Failed to trigger validation');
    }
  };

  const getStatusTag = (subscription: AzureSubscription) => {
    const statusConfig = {
      active: { color: 'success', icon: <CheckCircleOutlined />, text: 'Active' },
      error: { color: 'error', icon: <CloseCircleOutlined />, text: 'Error' },
      pending: { color: 'processing', icon: <SyncOutlined spin />, text: 'Validating' },
      inactive: { color: 'default', icon: null, text: 'Inactive' },
    };

    const config = statusConfig[subscription.status] || statusConfig.inactive;

    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    );
  };

  const columns = [
    {
      title: 'Subscription Name',
      dataIndex: 'subscription_name',
      key: 'subscription_name',
    },
    {
      title: 'Subscription ID',
      dataIndex: 'subscription_id',
      key: 'subscription_id',
      render: (id: string) => (
        <code style={{ fontSize: '0.85em' }}>{id}</code>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (_: any, record: AzureSubscription) => getStatusTag(record),
    },
    {
      title: 'Health',
      dataIndex: 'health_status',
      key: 'health_status',
      render: (health: string) => {
        const healthConfig = {
          healthy: { color: 'success', text: 'Healthy' },
          degraded: { color: 'warning', text: 'Degraded' },
          unhealthy: { color: 'error', text: 'Unhealthy' },
          unknown: { color: 'default', text: 'Unknown' },
        };
        const config = healthConfig[health] || healthConfig.unknown;
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: 'Last Sync',
      dataIndex: 'last_sync_at',
      key: 'last_sync_at',
      render: (date: string | null) =>
        date ? new Date(date).toLocaleString() : 'Never',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: AzureSubscription) => (
        <Space>
          <Tooltip title="Validate Credentials">
            <Button
              size="small"
              icon={<SyncOutlined />}
              onClick={() => handleValidate(record.id)}
            />
          </Tooltip>
          <Button size="small">Edit</Button>
          <Popconfirm
            title="Are you sure you want to delete this subscription?"
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button size="small" danger>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setModalVisible(true)}
        >
          Add Azure Subscription
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={subscriptions}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title="Add Azure Subscription"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreate}
        >
          <Form.Item
            label="Subscription Name"
            name="subscription_name"
            rules={[{ required: true, message: 'Please enter subscription name' }]}
          >
            <Input placeholder="Production Subscription" />
          </Form.Item>

          <Form.Item
            label="Azure Subscription ID"
            name="subscription_id"
            rules={[
              { required: true, message: 'Please enter subscription ID' },
              {
                pattern: /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
                message: 'Invalid GUID format'
              }
            ]}
          >
            <Input placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
          </Form.Item>

          <Form.Item
            label="Tenant ID"
            name="tenant_id"
            rules={[
              { required: true, message: 'Please enter tenant ID' },
              {
                pattern: /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
                message: 'Invalid GUID format'
              }
            ]}
          >
            <Input placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
          </Form.Item>

          <Form.Item
            label="Client ID (Application ID)"
            name="client_id"
            rules={[{ required: true, message: 'Please enter client ID' }]}
          >
            <Input placeholder="Application (Client) ID" />
          </Form.Item>

          <Form.Item
            label="Client Secret"
            name="client_secret"
            rules={[{ required: true, message: 'Please enter client secret' }]}
          >
            <Input.Password placeholder="Client Secret Value" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                Add Subscription
              </Button>
              <Button onClick={() => setModalVisible(false)}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
```

#### SourceSelector (CSV vs Azure API)

```typescript
// frontend/src/components/reports/SourceSelector.tsx

import React from 'react';
import { Radio, Space } from 'antd';
import { UploadOutlined, CloudOutlined } from '@ant-design/icons';

interface SourceSelectorProps {
  value: 'csv' | 'azure_api';
  onChange: (value: 'csv' | 'azure_api') => void;
}

export const SourceSelector: React.FC<SourceSelectorProps> = ({
  value,
  onChange
}) => {
  return (
    <Radio.Group value={value} onChange={(e) => onChange(e.target.value)}>
      <Space direction="vertical" size="middle">
        <Radio.Button value="csv" style={{ width: '100%', height: 'auto', padding: '16px' }}>
          <Space direction="vertical">
            <Space>
              <UploadOutlined style={{ fontSize: '24px' }} />
              <strong>Upload CSV File</strong>
            </Space>
            <span style={{ fontSize: '12px', color: '#666' }}>
              Manually upload Azure Advisor recommendations CSV
            </span>
          </Space>
        </Radio.Button>

        <Radio.Button value="azure_api" style={{ width: '100%', height: 'auto', padding: '16px' }}>
          <Space direction="vertical">
            <Space>
              <CloudOutlined style={{ fontSize: '24px' }} />
              <strong>Fetch from Azure</strong>
            </Space>
            <span style={{ fontSize: '12px', color: '#666' }}>
              Automatically fetch recommendations from Azure Advisor API
            </span>
          </Space>
        </Radio.Button>
      </Space>
    </Radio.Group>
  );
};
```

---

## 12. Manejo de Rate Limits

### 12.1 Azure Advisor API Rate Limits

Azure impone rate limits en sus APIs. Para Azure Advisor:

- **Límite por suscripción:** ~12,000 requests/hour
- **Límite por tenant:** Variable según tier

### 12.2 Estrategia de Mitigación

```python
# apps/azure_integration/services/rate_limiter.py

"""
Rate limiting for Azure API calls.
"""

import time
from functools import wraps
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class AzureRateLimiter:
    """
    Rate limiter for Azure API calls using token bucket algorithm.
    """

    def __init__(
        self,
        subscription_id: str,
        max_calls: int = 100,
        time_window: int = 3600  # 1 hour
    ):
        self.subscription_id = subscription_id
        self.max_calls = max_calls
        self.time_window = time_window
        self.cache_key = f"azure_rate_limit_{subscription_id}"

    def can_proceed(self) -> bool:
        """
        Check if we can proceed with an API call.

        Returns:
            bool: True if within rate limit, False otherwise
        """
        current_count = cache.get(self.cache_key, 0)

        if current_count >= self.max_calls:
            logger.warning(
                f"Rate limit reached for subscription {self.subscription_id[:8]}... "
                f"({current_count}/{self.max_calls} calls)"
            )
            return False

        return True

    def increment(self):
        """Increment API call counter."""
        current_count = cache.get(self.cache_key, 0)
        cache.set(
            self.cache_key,
            current_count + 1,
            timeout=self.time_window
        )

    def wait_if_needed(self):
        """Wait if rate limit is reached."""
        if not self.can_proceed():
            wait_time = self.get_wait_time()
            logger.info(
                f"Rate limit reached. Waiting {wait_time} seconds before retry."
            )
            time.sleep(wait_time)

    def get_wait_time(self) -> int:
        """
        Calculate wait time until rate limit resets.

        Returns:
            int: Wait time in seconds
        """
        ttl = cache.ttl(self.cache_key)
        return ttl if ttl > 0 else 0


def rate_limit(max_calls: int = 100, time_window: int = 3600):
    """
    Decorator for rate limiting Azure API methods.

    Args:
        max_calls: Maximum calls allowed in time window
        time_window: Time window in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            limiter = AzureRateLimiter(
                subscription_id=self.subscription_id,
                max_calls=max_calls,
                time_window=time_window
            )

            limiter.wait_if_needed()
            limiter.increment()

            return func(self, *args, **kwargs)

        return wrapper
    return decorator
```

**Uso en AzureAdvisorClient:**

```python
class AzureAdvisorClient:
    # ...

    @rate_limit(max_calls=100, time_window=3600)  # 100 calls/hour
    def fetch_recommendations(self, ...):
        # ... implementation ...
        pass
```

---

## 13. Escalabilidad y Performance

### 13.1 Caching Strategy

```python
# apps/azure_integration/services/cache_manager.py

"""
Caching strategy for Azure API responses.
"""

from django.core.cache import cache
from typing import Optional, Any
import hashlib
import json

class AzureCacheManager:
    """Manage caching for Azure API responses."""

    DEFAULT_TTL = 3600  # 1 hour

    @staticmethod
    def get_cache_key(
        subscription_id: str,
        operation: str,
        **params
    ) -> str:
        """
        Generate cache key for Azure API operation.

        Args:
            subscription_id: Azure subscription ID
            operation: Operation name (e.g., 'fetch_recommendations')
            **params: Additional parameters to include in key

        Returns:
            str: Cache key
        """
        # Create stable key from params
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()

        return f"azure_{operation}_{subscription_id}_{params_hash}"

    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get value from cache."""
        return cache.get(key)

    @staticmethod
    def set(key: str, value: Any, ttl: int = DEFAULT_TTL):
        """Set value in cache with TTL."""
        cache.set(key, value, timeout=ttl)

    @staticmethod
    def delete(key: str):
        """Delete key from cache."""
        cache.delete(key)

    @staticmethod
    def clear_subscription(subscription_id: str):
        """Clear all cache entries for a subscription."""
        pattern = f"azure_*_{subscription_id}_*"
        # Note: This requires Redis backend with pattern support
        cache.delete_pattern(pattern)
```

### 13.2 Database Optimization

**Índices recomendados:**

```sql
-- AzureSubscription indexes
CREATE INDEX idx_azure_sub_client_active ON azure_advisor_subscriptions(client_id, is_active);
CREATE INDEX idx_azure_sub_status ON azure_advisor_subscriptions(status);
CREATE INDEX idx_azure_sub_last_sync ON azure_advisor_subscriptions(last_sync_at);

-- Report indexes (modified)
CREATE INDEX idx_report_source_status ON reports(source, status);
CREATE INDEX idx_report_azure_sub ON reports(azure_subscription_id, created_at);

-- Recommendation indexes (modified)
CREATE INDEX idx_recommendation_azure_id ON recommendations(azure_recommendation_id);
CREATE INDEX idx_recommendation_report_category ON recommendations(report_id, category);
```

### 13.3 Query Optimization

```python
# Eager loading for performance

# Good: Select related to avoid N+1 queries
reports = Report.objects.select_related(
    'client',
    'azure_subscription',
    'created_by'
).prefetch_related(
    'recommendations'
).filter(source='azure_api')

# Good: Use values() for aggregations
stats = Recommendation.objects.filter(
    report__azure_subscription=subscription
).values('category').annotate(
    count=Count('id'),
    total_savings=Sum('potential_savings')
)
```

### 13.4 Celery Concurrency

```python
# celeryconfig.py

# Use gevent for I/O-bound tasks (Azure API calls)
CELERY_WORKER_POOL = 'gevent'
CELERY_WORKER_CONCURRENCY = 20  # Adjust based on server capacity

# Task routing
CELERY_TASK_ROUTES = {
    'apps.azure_integration.tasks.fetch_azure_advisor_recommendations': {
        'queue': 'azure_api',
        'routing_key': 'azure.fetch',
    },
    'apps.azure_integration.tasks.validate_azure_subscription': {
        'queue': 'azure_api',
        'routing_key': 'azure.validate',
    },
    'apps.reports.tasks.process_csv_file': {
        'queue': 'csv_processing',
        'routing_key': 'reports.csv',
    },
}
```

---

## 14. Plan de Implementación

### Fase 1: Infraestructura Base (1-2 semanas)

**Tareas:**
1. Crear app `azure_integration`
2. Implementar modelo `AzureSubscription`
3. Implementar sistema de encriptación de credenciales
4. Crear migraciones
5. Configurar Azure SDK dependencies

**Entregables:**
- Modelos de datos funcionando
- Sistema de encriptación probado
- Migraciones aplicadas

### Fase 2: Azure API Client (1-2 semanas)

**Tareas:**
1. Implementar `AzureAdvisorClient`
2. Implementar autenticación con Service Principal
3. Implementar fetching de recomendaciones
4. Implementar transformación de datos
5. Implementar manejo de errores y retry logic
6. Implementar rate limiting
7. Tests unitarios

**Entregables:**
- Cliente Azure completamente funcional
- Tests con >80% coverage
- Documentación de uso

### Fase 3: Backend Integration (2 semanas)

**Tareas:**
1. Modificar modelo `Report` para soporte dual
2. Modificar modelo `Recommendation` para campos Azure
3. Crear API endpoints para `AzureSubscription`
4. Implementar serializers
5. Crear Celery task `fetch_azure_advisor_recommendations`
6. Crear Celery task `validate_azure_subscription`
7. Modificar `ReportViewSet` para routing dual
8. Tests de integración

**Entregables:**
- API REST completa para Azure Subscriptions
- Celery tasks funcionando
- Report creation dual-source
- Tests de integración

### Fase 4: Frontend (2 semanas)

**Tareas:**
1. Crear `AzureSubscriptionManager` component
2. Crear `SourceSelector` component
3. Modificar `CreateReportModal` para soporte dual
4. Modificar `ReportList` para mostrar source
5. Crear página de gestión Azure Subscriptions
6. Implementar validación de formularios
7. Tests E2E (Playwright)

**Entregables:**
- UI completa para gestión de Azure Subscriptions
- Flujo completo de creación de reportes dual-source
- Tests E2E

### Fase 5: Testing y Documentation (1 semana)

**Tareas:**
1. Testing integral end-to-end
2. Performance testing
3. Security audit
4. Documentación de usuario
5. Documentación técnica
6. Video tutorials

**Entregables:**
- Suite de tests completa
- Documentación de usuario
- Documentación técnica
- Guías de setup

### Fase 6: Deployment y Monitoring (1 semana)

**Tareas:**
1. Setup Celery Beat para scheduled fetches
2. Configurar monitoring (Azure Monitor, Prometheus)
3. Configurar alertas
4. Deployment a staging
5. User acceptance testing
6. Deployment a producción
7. Post-deployment monitoring

**Entregables:**
- Sistema en producción
- Monitoring activo
- Runbooks de operación

**Timeline total:** 8-10 semanas

---

## 15. Decisiones Arquitectónicas (ADRs)

### ADR-001: Uso de Service Principal en lugar de Managed Identity

**Estado:** Aceptado

**Contexto:**
Azure ofrece dos métodos principales de autenticación para aplicaciones: Service Principal (con Client ID/Secret) y Managed Identity.

**Decisión:**
Usar Service Principal con Client Secret como método principal de autenticación.

**Razones:**
1. **Flexibilidad multi-tenant:** Los clientes pueden usar sus propios Service Principals en sus propios tenants
2. **Control granular:** Cada cliente controla sus propios permisos y puede rotarlos independientemente
3. **Portabilidad:** No depende de infraestructura Azure específica
4. **Simplicidad de setup:** Los clientes pueden crear Service Principals fácilmente

**Consecuencias:**
- Necesidad de almacenar credenciales encriptadas
- Responsabilidad de rotación de secrets
- Gestión de permisos por parte del cliente

---

### ADR-002: Coexistencia de CSV y API en lugar de migración completa

**Estado:** Aceptado

**Contexto:**
Podríamos eliminar el soporte de CSV y migrar completamente a API, o mantener ambos.

**Decisión:**
Mantener ambos métodos (CSV y Azure API) de forma permanente.

**Razones:**
1. **Casos de uso diferentes:** CSV es útil para datos históricos o clientes sin acceso API
2. **Menor fricción:** No forzar migración a clientes existentes
3. **Flexibilidad:** Algunos clientes pueden preferir CSV por razones de seguridad
4. **Redundancia:** Si Azure API falla, CSV sigue funcionando

**Consecuencias:**
- Mayor complejidad en código
- Necesidad de mantener dos flujos
- Testing más extensivo

---

### ADR-003: Encriptación de credenciales en base de datos

**Estado:** Aceptado

**Contexto:**
Las credenciales (Client Secret) son sensibles y deben protegerse.

**Decisión:**
Encriptar Client ID y Client Secret usando Fernet (symmetric encryption) antes de almacenarlos en PostgreSQL.

**Razones:**
1. **Seguridad:** Protección en caso de breach de base de datos
2. **Compliance:** Cumplimiento de estándares de seguridad
3. **Simplicidad:** Fernet es estándar en Python (cryptography library)
4. **Performance:** Symmetric encryption es rápida

**Consecuencias:**
- Dependencia del SECRET_KEY de Django (debe ser fuerte y estable)
- Necesidad de key management en producción
- Overhead mínimo de performance

---

### ADR-004: Uso de Celery para llamadas Azure API

**Estado:** Aceptado

**Contexto:**
Las llamadas a Azure API pueden ser lentas y no deben bloquear requests HTTP.

**Decisión:**
Usar Celery tasks asíncronas para todas las operaciones con Azure API.

**Razones:**
1. **Performance:** No bloquear requests HTTP del usuario
2. **Resiliencia:** Retry automático en caso de fallos
3. **Escalabilidad:** Procesamiento paralelo de múltiples suscripciones
4. **Monitoring:** Visibilidad de tareas en progreso

**Consecuencias:**
- Complejidad adicional de infraestructura (workers, Redis)
- Necesidad de comunicar estado asíncrono al frontend
- Debugging más complejo

---

### ADR-005: Caching de resultados Azure API

**Estado:** Aceptado

**Contexto:**
Las recomendaciones de Azure no cambian frecuentemente (actualizaciones cada 24-48 horas).

**Decisión:**
Cachear resultados de Azure Advisor API con TTL de 1 hora por defecto.

**Razones:**
1. **Performance:** Reducir latencia en requests repetidos
2. **Rate limiting:** Reducir consumo de cuota Azure API
3. **Costo:** Menos llamadas = menos costo
4. **UX:** Respuestas más rápidas

**Consecuencias:**
- Datos pueden estar ligeramente desactualizados
- Necesidad de invalidación manual de cache
- Uso de memoria en Redis

---

## Conclusión

Esta arquitectura proporciona una base sólida para la versión 2.0 de Azure Advisor Reports, con integración directa a Azure Advisor API mientras se mantiene compatibilidad con el flujo existente de CSV. El diseño prioriza seguridad, escalabilidad, y experiencia de usuario.

**Próximos pasos:**
1. Revisión y aprobación de arquitectura
2. Planning detallado de sprints
3. Setup de entorno de desarrollo
4. Inicio de Fase 1

---

**Documento preparado por:** Software Architecture Team
**Fecha de última actualización:** 2025-11-17
**Versión:** 2.0.0-draft
