# Azure Advisor Reports Platform v2.0 - Implementation Plan

**Document Version:** 1.0
**Created:** November 17, 2025
**Project Orchestrator:** Azure Reports Platform Team
**Current Version:** v1.6.1 (Production)
**Target Version:** v2.0.0

---

## Executive Summary

### Objective
Add direct Azure Advisor API integration to allow users to fetch recommendations automatically by providing only a Subscription ID, while maintaining backward compatibility with the existing CSV upload workflow.

### Current State
- Production version: v1.6.1
- Stack: Django, React, PostgreSQL, Redis, Celery with gevent
- Deployment: Azure Container Apps (3 containers: backend, worker, beat)
- Working CSV-based workflow with 20k row limit
- Existing Azure Cost Management API integration in `apps/cost_monitoring/`

### Success Criteria
- Users can generate reports using only Azure Subscription ID
- CSV upload workflow remains fully functional
- Zero downtime deployment
- No data migration required for existing users
- Same report quality and features as CSV-based reports

---

## Table of Contents

1. [Architecture Analysis](#architecture-analysis)
2. [Implementation Phases](#implementation-phases)
3. [Detailed Task Breakdown](#detailed-task-breakdown)
4. [Dependencies & Integration Points](#dependencies--integration-points)
5. [Testing Strategy](#testing-strategy)
6. [Deployment Strategy](#deployment-strategy)
7. [Risk Management](#risk-management)
8. [Timeline & Resources](#timeline--resources)

---

## Architecture Analysis

### Existing Components Inventory

#### Backend Apps Structure
```
azure_advisor_reports/apps/
├── authentication/      # Azure AD auth (MSAL)
├── clients/            # Client management
├── reports/            # Report generation (CSV-based)
├── analytics/          # Dashboard analytics
├── cost_monitoring/    # Azure Cost Management API integration ✓
│   ├── models.py       # AzureSubscription, CostData
│   ├── services/
│   │   └── azure_cost_service.py  # Azure API pattern to reuse
│   └── encryption.py   # Credential encryption
└── core/              # Shared utilities
```

#### Key Models
**Reports App:**
- `Client` - Client companies
- `Report` - Report instances with CSV workflow
- `Recommendation` - Individual Azure Advisor recommendations
- `ReportTemplate` - HTML/PDF templates
- `ReportShare` - Sharing functionality

**Cost Monitoring App (Reference):**
- `AzureSubscription` - Azure subscription with encrypted credentials
- `CostData` - API-fetched data

#### Current Report Generation Flow
```
User → Upload CSV → Celery Task → Parse CSV → Generate Report → HTML/PDF
```

#### Target v2.0 Flow
```
User → Provide Subscription ID → Celery Task → Azure Advisor API →
Parse API Response → Generate Report → HTML/PDF
```

### Architectural Patterns to Reuse

From `cost_monitoring` app:
1. **Azure Authentication Pattern**
   - Service Principal (Client ID, Secret, Tenant ID)
   - `ClientSecretCredential` from `azure.identity`
   - Encrypted credential storage

2. **Azure API Client Pattern**
   - Service class initialization with subscription
   - Credential decryption on demand
   - Error handling and retry logic
   - Last sync tracking

3. **Data Processing Pattern**
   - Fetch from Azure API
   - Transform to internal format
   - Store in PostgreSQL
   - Update sync status

---

## Implementation Phases

### Phase 0: Preparation & Design (Week 1)
**Duration:** 3-5 days
**Focus:** Architecture finalization, environment setup, documentation

**Deliverables:**
- Detailed API integration design document
- Data model changes specification
- UI/UX mockups for new workflow
- Security review completed
- Development environment with Azure Advisor API access

**Dependencies:**
- Azure subscription with Advisor API permissions
- Service Principal with Reader role on target subscriptions
- Development Azure AD app registration

---

### Phase 1: Backend Foundation (Week 2)
**Duration:** 5-7 days
**Focus:** Core infrastructure without breaking existing functionality

#### 1.1 Data Model Extensions (2 days)

**New Models:**

```python
# apps/reports/models.py

class AzureAdvisorSubscription(models.Model):
    """
    Azure subscription configuration for Advisor API access.
    Similar to cost_monitoring.AzureSubscription but for Advisor.
    """
    id = UUIDField(primary_key=True)
    client = ForeignKey(Client, on_delete=CASCADE)

    # Subscription info
    subscription_id = CharField(max_length=36, unique=True, db_index=True)
    subscription_name = CharField(max_length=255)
    tenant_id = CharField(max_length=36)

    # Encrypted credentials
    client_id_encrypted = BinaryField()
    client_secret_encrypted = BinaryField()

    # Status
    status = CharField(choices=['active', 'inactive', 'error', 'pending'])
    is_active = BooleanField(default=True)
    last_sync_at = DateTimeField(null=True, blank=True)
    last_sync_status = CharField(max_length=255, blank=True)
    last_error = TextField(blank=True)

    # Metadata
    created_by = ForeignKey(User, on_delete=SET_NULL, null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    # Methods (reuse from cost_monitoring)
    def set_client_id(self, client_id: str)
    def get_client_id(self) -> str
    def set_client_secret(self, client_secret: str)
    def get_client_secret(self) -> str
```

**Report Model Changes (Non-breaking):**

```python
# apps/reports/models.py - Add to existing Report model

class Report(models.Model):
    # ... existing fields ...

    # NEW: Source tracking
    data_source = CharField(
        max_length=20,
        choices=[
            ('csv', 'CSV Upload'),
            ('api', 'Azure Advisor API')
        ],
        default='csv',
        help_text="Source of recommendation data"
    )

    # NEW: API-based report link
    azure_subscription = ForeignKey(
        'AzureAdvisorSubscription',
        on_delete=SET_NULL,
        null=True,
        blank=True,
        related_name='reports'
    )

    # NEW: API metadata
    api_sync_metadata = JSONField(
        default=dict,
        blank=True,
        help_text="API response metadata (timestamp, version, etc.)"
    )
```

**Migration Strategy:**
- Additive migrations only (no data loss)
- Default `data_source='csv'` for existing reports
- NULL allowed for `azure_subscription` FK

#### 1.2 Azure Advisor API Service (3 days)

**File:** `apps/reports/services/azure_advisor_service.py`

```python
"""
Azure Advisor API integration service.

Pattern based on apps/cost_monitoring/services/azure_cost_service.py
"""

from azure.identity import ClientSecretCredential
from azure.mgmt.advisor import AdvisorManagementClient
from azure.mgmt.advisor.models import ResourceRecommendationBase

class AzureAdvisorService:
    """
    Service for fetching recommendations from Azure Advisor API.
    """

    def __init__(self, subscription: AzureAdvisorSubscription):
        self.subscription = subscription
        self._client = None

    def _get_client(self) -> AdvisorManagementClient:
        """Get authenticated Azure Advisor client."""
        if self._client is None:
            credential = ClientSecretCredential(
                tenant_id=self.subscription.tenant_id,
                client_id=self.subscription.get_client_id(),
                client_secret=self.subscription.get_client_secret()
            )
            self._client = AdvisorManagementClient(
                credential=credential,
                subscription_id=self.subscription.subscription_id
            )
        return self._client

    def fetch_recommendations(
        self,
        filter_category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch recommendations from Azure Advisor API.

        Returns list of recommendations in internal format.
        """
        # Implementation details
        pass

    def validate_credentials(self) -> bool:
        """Validate Azure credentials."""
        pass

    def sync_recommendations_to_report(
        self,
        report: Report
    ) -> Dict[str, Any]:
        """
        Fetch recommendations and create Recommendation objects.

        Similar to CSV processing but from API.
        """
        pass
```

**Key Responsibilities:**
- Authenticate with Azure Advisor API
- Fetch recommendations for a subscription
- Transform API response to internal `Recommendation` model format
- Handle pagination (Azure API returns max 1000 per page)
- Error handling and retry logic
- Credential validation

#### 1.3 Encryption Module Reuse (1 day)

**Option A: Shared Encryption Module**
```python
# apps/core/encryption.py (new shared module)
# Move from cost_monitoring/encryption.py

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

def encrypt_credential(value: str) -> bytes:
    """Encrypt sensitive credential."""
    pass

def decrypt_credential(encrypted_value: bytes) -> str:
    """Decrypt sensitive credential."""
    pass
```

**Option B: Import from cost_monitoring**
```python
# apps/reports/services/azure_advisor_service.py
from apps.cost_monitoring.encryption import encrypt_credential, decrypt_credential
```

**Decision:** Use Option A (shared module) for better architecture.

#### 1.4 API Serializers & Validators (1 day)

```python
# apps/reports/serializers.py

class AzureAdvisorSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Azure subscription configuration."""

    # Write-only fields for credentials
    client_id = serializers.CharField(write_only=True)
    client_secret = serializers.CharField(write_only=True)

    class Meta:
        model = AzureAdvisorSubscription
        fields = [
            'id', 'subscription_id', 'subscription_name',
            'tenant_id', 'client_id', 'client_secret',
            'status', 'is_active', 'last_sync_at'
        ]
        read_only_fields = ['id', 'status', 'last_sync_at']

    def create(self, validated_data):
        # Extract credentials
        client_id = validated_data.pop('client_id')
        client_secret = validated_data.pop('client_secret')

        # Create instance
        instance = AzureAdvisorSubscription(**validated_data)
        instance.set_client_id(client_id)
        instance.set_client_secret(client_secret)
        instance.save()

        return instance

class ReportCreateAPISerializer(serializers.ModelSerializer):
    """
    Serializer for creating reports via API.
    Supports both CSV upload and Azure Subscription ID.
    """

    # Make CSV optional (was required)
    csv_file = serializers.FileField(required=False, allow_null=True)

    # New field for API-based reports
    azure_subscription_id = serializers.UUIDField(
        required=False,
        allow_null=True
    )

    class Meta:
        model = Report
        fields = [
            'client', 'report_type', 'title',
            'csv_file', 'azure_subscription_id'
        ]

    def validate(self, attrs):
        """Ensure either CSV or Azure Subscription is provided."""
        csv_file = attrs.get('csv_file')
        subscription_id = attrs.get('azure_subscription_id')

        if not csv_file and not subscription_id:
            raise serializers.ValidationError(
                "Either csv_file or azure_subscription_id must be provided"
            )

        if csv_file and subscription_id:
            raise serializers.ValidationError(
                "Provide either csv_file or azure_subscription_id, not both"
            )

        return attrs
```

**Phase 1 Deliverables:**
- [ ] Migration: `0001_add_azure_advisor_subscription.py`
- [ ] Migration: `0002_add_report_api_fields.py`
- [ ] Model: `AzureAdvisorSubscription`
- [ ] Service: `AzureAdvisorService`
- [ ] Shared module: `apps/core/encryption.py`
- [ ] Serializers: API-aware serializers
- [ ] Unit tests: 80%+ coverage for new code
- [ ] API documentation: OpenAPI/Swagger specs

---

### Phase 2: Celery Task Integration (Week 3)
**Duration:** 4-6 days
**Focus:** Async processing for API-based reports

#### 2.1 New Celery Tasks (3 days)

```python
# apps/reports/tasks.py

@shared_task(bind=True, max_retries=3, time_limit=600)
def fetch_and_process_advisor_api(
    self,
    report_id: str,
    subscription_id: str
):
    """
    Fetch recommendations from Azure Advisor API and generate report.

    Similar to process_csv_and_generate_report but for API source.
    """
    try:
        report = Report.objects.get(id=report_id)
        report.start_processing()

        # Get Azure subscription config
        azure_sub = AzureAdvisorSubscription.objects.get(id=subscription_id)

        # Initialize service
        service = AzureAdvisorService(azure_sub)

        # Fetch recommendations
        recommendations = service.fetch_recommendations()

        # Create Recommendation objects
        for rec_data in recommendations:
            Recommendation.objects.create(
                report=report,
                category=rec_data['category'],
                business_impact=rec_data['impact'],
                recommendation=rec_data['recommendation'],
                # ... other fields
            )

        # Generate analysis data (same as CSV flow)
        report.analysis_data = generate_analysis_summary(report)
        report.status = 'generating'
        report.save()

        # Trigger report generation
        generate_report_files.delay(report_id)

    except Exception as exc:
        report.fail_processing(str(exc))
        raise self.retry(exc=exc, countdown=60)

@shared_task(bind=True, max_retries=3)
def validate_azure_credentials(self, subscription_id: str):
    """
    Validate Azure Advisor API credentials.

    Run when user adds new subscription.
    """
    try:
        subscription = AzureAdvisorSubscription.objects.get(id=subscription_id)
        service = AzureAdvisorService(subscription)

        is_valid = service.validate_credentials()

        if is_valid:
            subscription.status = 'active'
            subscription.mark_sync_success()
        else:
            subscription.status = 'error'
            subscription.mark_sync_error("Invalid credentials")

        return is_valid

    except Exception as exc:
        subscription.mark_sync_error(str(exc))
        raise self.retry(exc=exc, countdown=30)
```

#### 2.2 Refactor Existing Tasks (2 days)

**Goal:** Make report generation tasks source-agnostic.

```python
# apps/reports/tasks.py

@shared_task(bind=True, max_retries=3)
def generate_report_files(self, report_id: str):
    """
    Generate HTML and PDF files for a report.

    UPDATED: Works for both CSV and API sources.
    """
    try:
        report = Report.objects.get(id=report_id)

        # Check if recommendations exist (from CSV or API)
        if report.recommendation_count == 0:
            raise ValueError("No recommendations to generate report")

        # Generate HTML (same logic for both sources)
        html_generator = ReportHTMLGenerator(report)
        html_path = html_generator.generate()
        report.html_file = html_path

        # Generate PDF (same logic for both sources)
        pdf_generator = ReportPDFGenerator(report)
        pdf_path = pdf_generator.generate()
        report.pdf_file = pdf_path

        report.complete_processing()

    except Exception as exc:
        report.fail_processing(str(exc))
        raise self.retry(exc=exc, countdown=60)
```

**Phase 2 Deliverables:**
- [ ] Task: `fetch_and_process_advisor_api`
- [ ] Task: `validate_azure_credentials`
- [ ] Refactored: `generate_report_files` (source-agnostic)
- [ ] Task tests: Celery task unit tests
- [ ] Integration test: End-to-end API workflow
- [ ] Monitoring: Task metrics in Application Insights

---

### Phase 3: REST API Endpoints (Week 4)
**Duration:** 4-6 days
**Focus:** Backend API for subscription management and report creation

#### 3.1 Azure Subscription Management Endpoints (2 days)

```python
# apps/reports/views.py

class AzureAdvisorSubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Azure Advisor subscriptions.

    Endpoints:
    - GET /api/azure-subscriptions/  # List subscriptions
    - POST /api/azure-subscriptions/ # Add subscription
    - GET /api/azure-subscriptions/{id}/ # Get details
    - PUT/PATCH /api/azure-subscriptions/{id}/ # Update
    - DELETE /api/azure-subscriptions/{id}/ # Delete
    - POST /api/azure-subscriptions/{id}/validate/ # Validate credentials
    - POST /api/azure-subscriptions/{id}/sync/ # Manual sync
    """

    queryset = AzureAdvisorSubscription.objects.all()
    serializer_class = AzureAdvisorSubscriptionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['client', 'status', 'is_active']

    def get_queryset(self):
        """Filter by user's accessible clients."""
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        return self.queryset.filter(client__in=user.accessible_clients)

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """
        Validate Azure credentials for this subscription.

        POST /api/azure-subscriptions/{id}/validate/
        """
        subscription = self.get_object()

        # Trigger async validation
        task = validate_azure_credentials.delay(str(subscription.id))

        return Response({
            'status': 'validating',
            'task_id': task.id,
            'message': 'Credential validation started'
        })

    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """
        Manually trigger recommendation sync.

        Creates a new report from current recommendations.
        """
        subscription = self.get_object()

        # Create new report
        report = Report.objects.create(
            client=subscription.client,
            report_type=request.data.get('report_type', 'detailed'),
            data_source='api',
            azure_subscription=subscription,
            created_by=request.user,
            status='processing'
        )

        # Trigger API fetch
        fetch_and_process_advisor_api.delay(
            str(report.id),
            str(subscription.id)
        )

        return Response({
            'report_id': report.id,
            'status': 'processing',
            'message': 'Report generation started'
        })
```

#### 3.2 Enhanced Report Creation Endpoint (2 days)

```python
# apps/reports/views.py

class ReportViewSet(viewsets.ModelViewSet):
    """
    UPDATED: Support both CSV and API-based report creation.
    """

    def create(self, request, *args, **kwargs):
        """
        Create a new report.

        POST /api/reports/

        Body (CSV mode):
        {
            "client": "uuid",
            "report_type": "detailed",
            "csv_file": <file>
        }

        Body (API mode):
        {
            "client": "uuid",
            "report_type": "detailed",
            "azure_subscription_id": "uuid"
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Determine data source
        csv_file = serializer.validated_data.get('csv_file')
        azure_sub_id = serializer.validated_data.get('azure_subscription_id')

        # Create report
        report = serializer.save(
            created_by=request.user,
            data_source='csv' if csv_file else 'api'
        )

        # Trigger appropriate processing
        if csv_file:
            # Existing CSV workflow
            process_csv_and_generate_report.delay(
                str(report.id),
                report.report_type
            )
        else:
            # New API workflow
            fetch_and_process_advisor_api.delay(
                str(report.id),
                azure_sub_id
            )

        return Response(
            ReportSerializer(report).data,
            status=status.HTTP_201_CREATED
        )
```

#### 3.3 URL Configuration (1 day)

```python
# apps/reports/urls.py

router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'azure-subscriptions', AzureAdvisorSubscriptionViewSet, basename='azure-subscription')

urlpatterns = [
    path('', include(router.urls)),
]
```

**Phase 3 Deliverables:**
- [ ] ViewSet: `AzureAdvisorSubscriptionViewSet`
- [ ] Enhanced: `ReportViewSet.create()` method
- [ ] URL routing: New endpoints registered
- [ ] API tests: DRF test cases (APITestCase)
- [ ] Postman collection: API documentation
- [ ] OpenAPI schema: Auto-generated with drf-spectacular

---

### Phase 4: Frontend Integration (Week 5-6)
**Duration:** 8-10 days
**Focus:** React UI for Azure subscription management and API-based reports

#### 4.1 New API Service Layer (2 days)

```javascript
// frontend/src/services/azureSubscriptionApi.ts

import apiClient from './apiClient';

export interface AzureSubscription {
  id: string;
  subscription_id: string;
  subscription_name: string;
  tenant_id: string;
  status: 'active' | 'inactive' | 'error' | 'pending';
  is_active: boolean;
  last_sync_at: string | null;
  client: string;
}

export interface CreateSubscriptionRequest {
  subscription_id: string;
  subscription_name: string;
  tenant_id: string;
  client_id: string;
  client_secret: string;
  client: string;
}

class AzureSubscriptionAPI {

  async listSubscriptions(clientId?: string): Promise<AzureSubscription[]> {
    const params = clientId ? { client: clientId } : {};
    const response = await apiClient.get('/azure-subscriptions/', { params });
    return response.data;
  }

  async createSubscription(data: CreateSubscriptionRequest): Promise<AzureSubscription> {
    const response = await apiClient.post('/azure-subscriptions/', data);
    return response.data;
  }

  async validateCredentials(subscriptionId: string): Promise<{ task_id: string }> {
    const response = await apiClient.post(
      `/azure-subscriptions/${subscriptionId}/validate/`
    );
    return response.data;
  }

  async syncRecommendations(
    subscriptionId: string,
    reportType: string
  ): Promise<{ report_id: string }> {
    const response = await apiClient.post(
      `/azure-subscriptions/${subscriptionId}/sync/`,
      { report_type: reportType }
    );
    return response.data;
  }

  async deleteSubscription(subscriptionId: string): Promise<void> {
    await apiClient.delete(`/azure-subscriptions/${subscriptionId}/`);
  }
}

export default new AzureSubscriptionAPI();
```

#### 4.2 Azure Subscription Management Page (3 days)

```tsx
// frontend/src/pages/AzureSubscriptionsPage.tsx

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import azureSubscriptionApi from '../services/azureSubscriptionApi';

const AzureSubscriptionsPage: React.FC = () => {
  const [showAddModal, setShowAddModal] = useState(false);
  const queryClient = useQueryClient();

  // Fetch subscriptions
  const { data: subscriptions, isLoading } = useQuery(
    'azureSubscriptions',
    () => azureSubscriptionApi.listSubscriptions()
  );

  // Delete mutation
  const deleteMutation = useMutation(
    (id: string) => azureSubscriptionApi.deleteSubscription(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('azureSubscriptions');
      }
    }
  );

  // Validate mutation
  const validateMutation = useMutation(
    (id: string) => azureSubscriptionApi.validateCredentials(id),
    {
      onSuccess: () => {
        // Show success notification
        // Refresh data after validation completes
      }
    }
  );

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Azure Subscriptions</h1>
        <button
          onClick={() => setShowAddModal(true)}
          className="btn btn-primary"
        >
          Add Subscription
        </button>
      </div>

      {/* Subscription List */}
      <div className="grid gap-4">
        {subscriptions?.map(sub => (
          <SubscriptionCard
            key={sub.id}
            subscription={sub}
            onValidate={() => validateMutation.mutate(sub.id)}
            onDelete={() => deleteMutation.mutate(sub.id)}
          />
        ))}
      </div>

      {/* Add Subscription Modal */}
      {showAddModal && (
        <AddSubscriptionModal
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            setShowAddModal(false);
            queryClient.invalidateQueries('azureSubscriptions');
          }}
        />
      )}
    </div>
  );
};
```

```tsx
// frontend/src/components/azure/AddSubscriptionModal.tsx

import React, { useState } from 'react';
import { useMutation } from 'react-query';
import azureSubscriptionApi from '../../services/azureSubscriptionApi';

interface AddSubscriptionModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

const AddSubscriptionModal: React.FC<AddSubscriptionModalProps> = ({
  onClose,
  onSuccess
}) => {
  const [formData, setFormData] = useState({
    subscription_id: '',
    subscription_name: '',
    tenant_id: '',
    client_id: '',
    client_secret: '',
    client: ''
  });

  const mutation = useMutation(
    azureSubscriptionApi.createSubscription,
    {
      onSuccess: () => {
        // Show success notification
        onSuccess();
      },
      onError: (error) => {
        // Show error notification
      }
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  return (
    <div className="modal">
      <div className="modal-content">
        <h2 className="text-2xl font-bold mb-4">Add Azure Subscription</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block mb-2">Subscription ID</label>
            <input
              type="text"
              value={formData.subscription_id}
              onChange={e => setFormData({
                ...formData,
                subscription_id: e.target.value
              })}
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              className="input w-full"
              required
            />
            <p className="text-sm text-gray-600 mt-1">
              Found in Azure Portal → Subscriptions
            </p>
          </div>

          <div>
            <label className="block mb-2">Subscription Name</label>
            <input
              type="text"
              value={formData.subscription_name}
              onChange={e => setFormData({
                ...formData,
                subscription_name: e.target.value
              })}
              placeholder="Production Subscription"
              className="input w-full"
              required
            />
          </div>

          <div>
            <label className="block mb-2">Tenant ID</label>
            <input
              type="text"
              value={formData.tenant_id}
              onChange={e => setFormData({
                ...formData,
                tenant_id: e.target.value
              })}
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              className="input w-full"
              required
            />
          </div>

          <div className="border-t pt-4 mt-4">
            <h3 className="font-semibold mb-3">Service Principal Credentials</h3>
            <p className="text-sm text-gray-600 mb-4">
              Create an App Registration in Azure AD with Reader role on the subscription
            </p>

            <div className="mb-4">
              <label className="block mb-2">Client ID (Application ID)</label>
              <input
                type="text"
                value={formData.client_id}
                onChange={e => setFormData({
                  ...formData,
                  client_id: e.target.value
                })}
                placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                className="input w-full"
                required
              />
            </div>

            <div>
              <label className="block mb-2">Client Secret</label>
              <input
                type="password"
                value={formData.client_secret}
                onChange={e => setFormData({
                  ...formData,
                  client_secret: e.target.value
                })}
                placeholder="Enter client secret"
                className="input w-full"
                required
              />
              <p className="text-sm text-gray-600 mt-1">
                Stored encrypted. Never displayed again.
              </p>
            </div>
          </div>

          <div className="flex gap-3 justify-end mt-6">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={mutation.isLoading}
              className="btn btn-primary"
            >
              {mutation.isLoading ? 'Adding...' : 'Add Subscription'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
```

#### 4.3 Enhanced Report Creation Flow (3 days)

```tsx
// frontend/src/components/reports/CreateReportModal.tsx

import React, { useState } from 'react';
import { useQuery } from 'react-query';
import azureSubscriptionApi from '../../services/azureSubscriptionApi';

interface CreateReportModalProps {
  onClose: () => void;
  onSuccess: (reportId: string) => void;
}

const CreateReportModal: React.FC<CreateReportModalProps> = ({
  onClose,
  onSuccess
}) => {
  const [dataSource, setDataSource] = useState<'csv' | 'api'>('csv');
  const [selectedSubscription, setSelectedSubscription] = useState<string>('');
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [reportType, setReportType] = useState<string>('detailed');

  // Fetch Azure subscriptions for dropdown
  const { data: subscriptions } = useQuery(
    'azureSubscriptions',
    azureSubscriptionApi.listSubscriptions,
    { enabled: dataSource === 'api' }
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (dataSource === 'csv') {
      // Existing CSV upload logic
      const formData = new FormData();
      formData.append('csv_file', csvFile!);
      formData.append('report_type', reportType);
      formData.append('client', selectedClient);

      const response = await reportsApi.createReport(formData);
      onSuccess(response.id);

    } else {
      // New API-based logic
      const response = await reportsApi.createReport({
        azure_subscription_id: selectedSubscription,
        report_type: reportType,
        client: selectedClient
      });
      onSuccess(response.id);
    }
  };

  return (
    <div className="modal">
      <div className="modal-content max-w-2xl">
        <h2 className="text-2xl font-bold mb-6">Create New Report</h2>

        {/* Data Source Selection */}
        <div className="mb-6">
          <label className="block mb-3 font-semibold">Data Source</label>
          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => setDataSource('csv')}
              className={`flex-1 p-4 border-2 rounded-lg ${
                dataSource === 'csv'
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300'
              }`}
            >
              <div className="text-lg font-semibold mb-1">CSV Upload</div>
              <div className="text-sm text-gray-600">
                Upload Azure Advisor CSV file
              </div>
            </button>

            <button
              type="button"
              onClick={() => setDataSource('api')}
              className={`flex-1 p-4 border-2 rounded-lg ${
                dataSource === 'api'
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300'
              }`}
            >
              <div className="text-lg font-semibold mb-1">
                Azure Subscription
              </div>
              <div className="text-sm text-gray-600">
                Fetch recommendations automatically
              </div>
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* CSV Upload Section */}
          {dataSource === 'csv' && (
            <div>
              <label className="block mb-2">CSV File</label>
              <input
                type="file"
                accept=".csv"
                onChange={e => setCsvFile(e.target.files?.[0] || null)}
                className="input w-full"
                required
              />
            </div>
          )}

          {/* Azure Subscription Section */}
          {dataSource === 'api' && (
            <div>
              <label className="block mb-2">Azure Subscription</label>
              <select
                value={selectedSubscription}
                onChange={e => setSelectedSubscription(e.target.value)}
                className="input w-full"
                required
              >
                <option value="">Select subscription...</option>
                {subscriptions?.map(sub => (
                  <option key={sub.id} value={sub.id}>
                    {sub.subscription_name} ({sub.subscription_id})
                  </option>
                ))}
              </select>

              {subscriptions?.length === 0 && (
                <p className="text-sm text-orange-600 mt-2">
                  No subscriptions configured. Add one first.
                </p>
              )}
            </div>
          )}

          {/* Report Type */}
          <div>
            <label className="block mb-2">Report Type</label>
            <select
              value={reportType}
              onChange={e => setReportType(e.target.value)}
              className="input w-full"
            >
              <option value="detailed">Detailed Report</option>
              <option value="executive">Executive Summary</option>
              <option value="cost">Cost Optimization</option>
              <option value="security">Security Assessment</option>
              <option value="operations">Operational Excellence</option>
            </select>
          </div>

          {/* Submit Buttons */}
          <div className="flex gap-3 justify-end mt-6">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Create Report
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
```

#### 4.4 Sidebar Navigation Update (1 day)

```tsx
// frontend/src/components/layout/Sidebar.tsx

const Sidebar: React.FC = () => {
  return (
    <aside className="sidebar">
      <nav>
        <NavLink to="/dashboard">Dashboard</NavLink>
        <NavLink to="/clients">Clients</NavLink>
        <NavLink to="/reports">Reports</NavLink>

        {/* NEW */}
        <NavLink to="/azure-subscriptions">
          Azure Subscriptions
        </NavLink>

        <NavLink to="/history">History</NavLink>
        <NavLink to="/analytics">Analytics</NavLink>
      </nav>
    </aside>
  );
};
```

#### 4.5 Report List Enhancements (1 day)

```tsx
// frontend/src/pages/ReportsPage.tsx

const ReportList: React.FC = () => {
  // ... existing code ...

  return (
    <div>
      {/* ... existing code ... */}

      {reports.map(report => (
        <div key={report.id} className="report-card">
          {/* ... existing fields ... */}

          {/* NEW: Show data source badge */}
          <div className="flex items-center gap-2">
            {report.data_source === 'csv' ? (
              <span className="badge badge-blue">CSV Upload</span>
            ) : (
              <span className="badge badge-green">Azure API</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
```

**Phase 4 Deliverables:**
- [ ] Service: `azureSubscriptionApi.ts`
- [ ] Page: `AzureSubscriptionsPage.tsx`
- [ ] Component: `AddSubscriptionModal.tsx`
- [ ] Component: `CreateReportModal.tsx` (enhanced)
- [ ] Component: Report list data source badges
- [ ] Navigation: Sidebar with new link
- [ ] Tests: React Testing Library tests
- [ ] E2E tests: Playwright scenarios

---

### Phase 5: Testing & Quality Assurance (Week 7)
**Duration:** 5-7 days
**Focus:** Comprehensive testing across all layers

#### 5.1 Backend Unit Tests (2 days)

**Test Coverage Goals:**
- Models: 90%+
- Services: 85%+
- Serializers: 85%+
- Views: 80%+
- Tasks: 80%+

```python
# apps/reports/tests/test_azure_advisor_service.py

class AzureAdvisorServiceTestCase(TestCase):

    def setUp(self):
        self.client_obj = Client.objects.create(company_name="Test Client")
        self.subscription = AzureAdvisorSubscription.objects.create(
            client=self.client_obj,
            subscription_id="test-sub-id",
            subscription_name="Test Subscription",
            tenant_id="test-tenant-id"
        )
        self.subscription.set_client_id("test-client-id")
        self.subscription.set_client_secret("test-secret")

    @patch('apps.reports.services.azure_advisor_service.AdvisorManagementClient')
    def test_fetch_recommendations(self, mock_client):
        """Test fetching recommendations from Azure API."""
        # Mock API response
        mock_client.return_value.recommendations.list.return_value = [
            # Mock recommendation objects
        ]

        service = AzureAdvisorService(self.subscription)
        recommendations = service.fetch_recommendations()

        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

    def test_credential_encryption(self):
        """Test credentials are encrypted."""
        subscription = AzureAdvisorSubscription.objects.create(
            client=self.client_obj,
            subscription_id="test-id"
        )
        subscription.set_client_id("my-client-id")
        subscription.save()

        # Reload from DB
        subscription.refresh_from_db()

        # Check encrypted field is binary
        self.assertIsInstance(subscription.client_id_encrypted, bytes)

        # Check decryption works
        self.assertEqual(subscription.get_client_id(), "my-client-id")
```

```python
# apps/reports/tests/test_api_report_creation.py

class APIReportCreationTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass"
        )
        self.client_obj = Client.objects.create(company_name="Test")
        self.subscription = AzureAdvisorSubscription.objects.create(
            client=self.client_obj,
            subscription_id="test-sub"
        )
        self.client.force_authenticate(user=self.user)

    @patch('apps.reports.tasks.fetch_and_process_advisor_api.delay')
    def test_create_report_via_api(self, mock_task):
        """Test creating report with Azure subscription."""
        data = {
            'client': str(self.client_obj.id),
            'report_type': 'detailed',
            'azure_subscription_id': str(self.subscription.id)
        }

        response = self.client.post('/api/reports/', data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data_source'], 'api')

        # Check Celery task was triggered
        mock_task.assert_called_once()

    def test_cannot_provide_both_csv_and_subscription(self):
        """Test validation: cannot provide both sources."""
        # Create test CSV file
        csv_file = SimpleUploadedFile(
            "test.csv",
            b"category,impact\nCost,High",
            content_type="text/csv"
        )

        data = {
            'client': str(self.client_obj.id),
            'report_type': 'detailed',
            'csv_file': csv_file,
            'azure_subscription_id': str(self.subscription.id)
        }

        response = self.client.post('/api/reports/', data)

        self.assertEqual(response.status_code, 400)
        self.assertIn('azure_subscription_id', response.data['errors'])
```

#### 5.2 Frontend Unit Tests (1 day)

```typescript
// frontend/src/pages/__tests__/AzureSubscriptionsPage.test.tsx

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import AzureSubscriptionsPage from '../AzureSubscriptionsPage';
import azureSubscriptionApi from '../../services/azureSubscriptionApi';

jest.mock('../../services/azureSubscriptionApi');

describe('AzureSubscriptionsPage', () => {

  const queryClient = new QueryClient();

  const wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );

  it('renders subscription list', async () => {
    const mockSubscriptions = [
      {
        id: '1',
        subscription_name: 'Test Sub',
        subscription_id: 'abc-123',
        status: 'active'
      }
    ];

    (azureSubscriptionApi.listSubscriptions as jest.Mock)
      .mockResolvedValue(mockSubscriptions);

    render(<AzureSubscriptionsPage />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Test Sub')).toBeInTheDocument();
    });
  });

  it('opens add subscription modal', () => {
    render(<AzureSubscriptionsPage />, { wrapper });

    const addButton = screen.getByText('Add Subscription');
    fireEvent.click(addButton);

    expect(screen.getByText('Add Azure Subscription')).toBeInTheDocument();
  });
});
```

#### 5.3 Integration Tests (2 days)

```python
# apps/reports/tests/test_integration_api_workflow.py

class APIWorkflowIntegrationTestCase(TransactionTestCase):
    """
    Test complete workflow: Add subscription → Create report → Generate files
    """

    def setUp(self):
        # Setup test data
        self.client_obj = Client.objects.create(company_name="Integration Test")
        self.user = User.objects.create_user(email="test@example.com")

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('apps.reports.services.azure_advisor_service.AdvisorManagementClient')
    def test_complete_api_report_workflow(self, mock_azure_client):
        """
        Test full workflow:
        1. Add Azure subscription
        2. Validate credentials
        3. Create report via API
        4. Fetch recommendations
        5. Generate HTML/PDF
        6. Verify report completion
        """

        # Step 1: Create subscription
        subscription = AzureAdvisorSubscription.objects.create(
            client=self.client_obj,
            subscription_id="integration-test-sub",
            subscription_name="Integration Test Subscription",
            tenant_id="test-tenant",
            created_by=self.user
        )
        subscription.set_client_id("test-client-id")
        subscription.set_client_secret("test-secret")
        subscription.save()

        # Step 2: Mock Azure API response
        mock_recommendations = [
            {
                'category': 'Cost',
                'impact': 'High',
                'short_description': {'problem': 'Underutilized VM'},
                'extended_properties': {
                    'savingsAmount': '150.00',
                    'savingsCurrency': 'USD'
                },
                # ... other fields
            },
            # ... more recommendations
        ]

        mock_azure_client.return_value.recommendations.list.return_value = (
            mock_recommendations
        )

        # Step 3: Create report
        report = Report.objects.create(
            client=self.client_obj,
            report_type='detailed',
            data_source='api',
            azure_subscription=subscription,
            created_by=self.user,
            status='processing'
        )

        # Step 4: Trigger processing (runs synchronously in test)
        from apps.reports.tasks import fetch_and_process_advisor_api
        fetch_and_process_advisor_api(str(report.id), str(subscription.id))

        # Step 5: Verify results
        report.refresh_from_db()

        self.assertEqual(report.status, 'completed')
        self.assertGreater(report.recommendation_count, 0)
        self.assertIsNotNone(report.html_file)
        self.assertIsNotNone(report.pdf_file)
        self.assertTrue(report.html_file.storage.exists(report.html_file.name))

        # Step 6: Verify recommendations
        recommendations = report.recommendations.all()
        self.assertGreater(recommendations.count(), 0)

        # Step 7: Verify analysis data
        self.assertIn('total_recommendations', report.analysis_data)
        self.assertIn('total_savings', report.analysis_data)
```

#### 5.4 E2E Tests (Playwright) (1 day)

```typescript
// frontend/e2e/azure-subscription-workflow.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Azure Subscription Workflow', () => {

  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'testpass');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('Complete workflow: Add subscription → Create report', async ({ page }) => {

    // Navigate to Azure Subscriptions page
    await page.goto('/azure-subscriptions');

    // Click "Add Subscription"
    await page.click('text=Add Subscription');

    // Fill form
    await page.fill('[name="subscription_id"]', 'test-sub-id');
    await page.fill('[name="subscription_name"]', 'E2E Test Subscription');
    await page.fill('[name="tenant_id"]', 'test-tenant-id');
    await page.fill('[name="client_id"]', 'test-client-id');
    await page.fill('[name="client_secret"]', 'test-secret');

    // Submit
    await page.click('button[type="submit"]');

    // Verify subscription appears
    await expect(page.locator('text=E2E Test Subscription')).toBeVisible();

    // Navigate to Reports
    await page.goto('/reports');

    // Create new report
    await page.click('text=Create Report');

    // Select API data source
    await page.click('text=Azure Subscription');

    // Select subscription from dropdown
    await page.selectOption('[name="azure_subscription_id"]', 'E2E Test Subscription');

    // Select report type
    await page.selectOption('[name="report_type"]', 'detailed');

    // Submit
    await page.click('button[type="submit"]');

    // Verify report appears in list
    await expect(page.locator('text=Processing')).toBeVisible();

    // Wait for completion (with timeout)
    await page.waitForSelector('text=Completed', { timeout: 60000 });

    // Verify download buttons are visible
    await expect(page.locator('text=Download PDF')).toBeVisible();
    await expect(page.locator('text=Download HTML')).toBeVisible();
  });

  test('Validate credentials flow', async ({ page }) => {
    await page.goto('/azure-subscriptions');

    // Find subscription card
    const subscriptionCard = page.locator('.subscription-card').first();

    // Click validate button
    await subscriptionCard.locator('text=Validate').click();

    // Check for validation status
    await expect(page.locator('text=Validating credentials')).toBeVisible();

    // Wait for result
    await page.waitForSelector('text=Valid', { timeout: 30000 });
  });
});
```

**Phase 5 Deliverables:**
- [ ] Backend unit tests: 85%+ coverage
- [ ] Frontend unit tests: 70%+ coverage
- [ ] Integration tests: Key workflows tested
- [ ] E2E tests: 2-3 critical user journeys
- [ ] Test documentation: How to run tests
- [ ] CI/CD integration: Tests run on PR

---

### Phase 6: Documentation & Training (Week 8)
**Duration:** 3-5 days
**Focus:** User and developer documentation

#### 6.1 User Documentation (2 days)

**File:** `/docs/USER_GUIDE_V2.md`

Content:
1. What's new in v2.0
2. Azure subscription setup guide
3. Service Principal creation guide (with screenshots)
4. How to create API-based reports
5. Comparison: CSV vs API workflow
6. Troubleshooting common issues
7. FAQs

**File:** `/docs/AZURE_SETUP_GUIDE.md`

Step-by-step guide:
1. Create Azure AD App Registration
2. Generate Client Secret
3. Assign Reader role on subscription
4. Copy credentials
5. Add to platform
6. Validate credentials

#### 6.2 Developer Documentation (2 days)

**File:** `/docs/V2_ARCHITECTURE.md`

Content:
- Architecture diagrams
- Data flow diagrams
- API integration patterns
- Error handling strategy
- Security considerations
- Performance optimization

**File:** `/docs/API_REFERENCE_V2.md`

- New endpoints documentation
- Request/response examples
- Authentication requirements
- Rate limiting
- Error codes

#### 6.3 Video Tutorials (Optional, 1 day)

1. "Setting up Azure Integration" (5 min)
2. "Creating your first API-based report" (3 min)
3. "Managing Azure Subscriptions" (4 min)

**Phase 6 Deliverables:**
- [ ] User guide with screenshots
- [ ] Azure setup guide
- [ ] Developer architecture doc
- [ ] API reference
- [ ] Migration guide (CSV → API)
- [ ] Video tutorials (optional)

---

### Phase 7: Deployment Preparation (Week 8-9)
**Duration:** 5-7 days
**Focus:** Production readiness and deployment strategy

#### 7.1 Feature Flag Implementation (2 days)

**Goal:** Allow gradual rollout of v2.0 features.

```python
# apps/core/feature_flags.py

from django.conf import settings
from django.core.cache import cache

class FeatureFlags:
    """
    Feature flag management for gradual rollout.
    """

    AZURE_API_INTEGRATION = 'azure_api_integration'

    @classmethod
    def is_enabled(cls, flag_name: str, user=None) -> bool:
        """
        Check if feature flag is enabled.

        Priority:
        1. Environment variable
        2. Django settings
        3. Database config (cached)
        4. Default: False
        """
        # Check environment
        env_key = f"FEATURE_{flag_name.upper()}"
        if env_key in os.environ:
            return os.environ[env_key].lower() == 'true'

        # Check settings
        if hasattr(settings, 'FEATURE_FLAGS'):
            return settings.FEATURE_FLAGS.get(flag_name, False)

        return False

    @classmethod
    def enable_for_user(cls, flag_name: str, user_id: str):
        """Enable feature for specific user (beta testing)."""
        cache_key = f"feature:{flag_name}:user:{user_id}"
        cache.set(cache_key, True, timeout=86400)  # 24 hours
```

Usage in views:
```python
# apps/reports/views.py

class AzureAdvisorSubscriptionViewSet(viewsets.ModelViewSet):

    def list(self, request, *args, **kwargs):
        # Check feature flag
        if not FeatureFlags.is_enabled(FeatureFlags.AZURE_API_INTEGRATION):
            return Response(
                {'error': 'Feature not available'},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().list(request, *args, **kwargs)
```

Usage in frontend:
```typescript
// frontend/src/config/featureFlags.ts

export const featureFlags = {
  azureApiIntegration: process.env.REACT_APP_FEATURE_AZURE_API === 'true'
};

// frontend/src/components/layout/Sidebar.tsx

{featureFlags.azureApiIntegration && (
  <NavLink to="/azure-subscriptions">Azure Subscriptions</NavLink>
)}
```

#### 7.2 Database Migrations Strategy (1 day)

**Approach:** Blue-Green migrations

1. **Migration 1:** Add new tables (safe)
   ```python
   # 0001_add_azure_advisor_subscription.py
   operations = [
       migrations.CreateModel(
           name='AzureAdvisorSubscription',
           # ... fields
       ),
   ]
   ```

2. **Migration 2:** Add nullable FK to Report (safe)
   ```python
   # 0002_add_report_api_fields.py
   operations = [
       migrations.AddField(
           model_name='report',
           name='azure_subscription',
           field=models.ForeignKey(null=True, blank=True, ...),
       ),
       migrations.AddField(
           model_name='report',
           name='data_source',
           field=models.CharField(default='csv', ...),
       ),
   ]
   ```

3. **Data migration:** Backfill `data_source='csv'` for existing reports
   ```python
   # 0003_backfill_report_data_source.py
   def forwards_func(apps, schema_editor):
       Report = apps.get_model('reports', 'Report')
       Report.objects.filter(data_source__isnull=True).update(data_source='csv')
   ```

#### 7.3 Rollout Strategy (2 days)

**Stage 1: Internal Testing (Week 9 Day 1-2)**
- Deploy to staging environment
- Enable feature flag for internal users only
- Run smoke tests
- Gather feedback

**Stage 2: Beta Users (Week 9 Day 3-4)**
- Enable feature flag for 5-10 selected clients
- Monitor performance metrics
- Collect user feedback
- Fix critical bugs

**Stage 3: Gradual Rollout (Week 9 Day 5-7)**
- Enable for 25% of users
- Monitor for 24 hours
- Enable for 50% of users
- Monitor for 24 hours
- Enable for 100% of users

**Rollback Plan:**
- Disable feature flag immediately
- No data loss (migrations are additive)
- CSV workflow always available as fallback

#### 7.4 Monitoring & Observability (1 day)

**Application Insights Custom Metrics:**

```python
# apps/reports/services/azure_advisor_service.py

from opencensus.ext.azure.log_exporter import AzureLogHandler
import logging

logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(
    connection_string=settings.APPLICATIONINSIGHTS_CONNECTION_STRING
))

class AzureAdvisorService:

    def fetch_recommendations(self):
        start_time = time.time()

        try:
            # Fetch data
            recommendations = self._fetch_from_api()

            # Log success metric
            logger.info('azure_advisor_api_fetch_success', extra={
                'custom_dimensions': {
                    'subscription_id': self.subscription.subscription_id,
                    'recommendation_count': len(recommendations),
                    'duration_seconds': time.time() - start_time
                }
            })

            return recommendations

        except Exception as e:
            # Log error metric
            logger.error('azure_advisor_api_fetch_error', extra={
                'custom_dimensions': {
                    'subscription_id': self.subscription.subscription_id,
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            })
            raise
```

**Dashboard Queries:**

1. API fetch success rate
2. Average API response time
3. Number of API-based reports created
4. Error rate by error type
5. Subscription validation success rate

**Phase 7 Deliverables:**
- [ ] Feature flag system implemented
- [ ] Migrations tested on staging
- [ ] Rollout plan documented
- [ ] Rollback procedures documented
- [ ] Monitoring dashboards created
- [ ] Alert rules configured

---

### Phase 8: Production Deployment (Week 10)
**Duration:** 2-3 days
**Focus:** Zero-downtime production deployment

#### 8.1 Pre-Deployment Checklist

**Code Quality:**
- [ ] All tests passing (backend + frontend)
- [ ] Code review completed
- [ ] Security scan passed
- [ ] Performance testing completed
- [ ] Documentation updated

**Infrastructure:**
- [ ] Staging deployment successful
- [ ] Database backup completed
- [ ] Rollback plan tested
- [ ] Feature flags configured
- [ ] Monitoring dashboards ready

**Communication:**
- [ ] Release notes prepared
- [ ] User notification sent (7 days prior)
- [ ] Support team briefed
- [ ] Escalation contacts identified

#### 8.2 Deployment Steps

**Step 1: Database Migrations (5 min)**
```bash
# Run migrations on production DB
az containerapp exec \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --command "python manage.py migrate --noinput"
```

**Step 2: Deploy Backend (10 min)**
```bash
# Build new backend image
az acr build --registry advisorreportsacr \
  --image advisor-reports-backend:v2.0.0 \
  --image advisor-reports-backend:latest \
  --file azure_advisor_reports/Dockerfile .

# Update container app
az containerapp update \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --image advisorreportsacr.azurecr.io/advisor-reports-backend:v2.0.0
```

**Step 3: Deploy Frontend (10 min)**
```bash
# Build new frontend image
az acr build --registry advisorreportsacr \
  --image advisor-reports-frontend:v2.0.0 \
  --image advisor-reports-frontend:latest \
  --file frontend/Dockerfile .

# Update container app
az containerapp update \
  --name advisor-reports-frontend \
  --resource-group rg-azure-advisor-app \
  --image advisorreportsacr.azurecr.io/advisor-reports-frontend:v2.0.0
```

**Step 4: Update Workers (5 min)**
```bash
# Update worker container
az containerapp update \
  --name advisor-reports-worker \
  --resource-group rg-azure-advisor-app \
  --image advisorreportsacr.azurecr.io/advisor-reports-backend:v2.0.0
```

**Step 5: Enable Feature Flag (Gradual)**
```bash
# Day 1: Internal users only
az containerapp update --name advisor-reports-backend \
  --set-env-vars "FEATURE_AZURE_API_INTEGRATION=internal"

# Day 2: Beta users (25%)
az containerapp update --name advisor-reports-backend \
  --set-env-vars "FEATURE_AZURE_API_INTEGRATION=beta"

# Day 5: All users (100%)
az containerapp update --name advisor-reports-backend \
  --set-env-vars "FEATURE_AZURE_API_INTEGRATION=true"
```

**Step 6: Verification (30 min)**
```bash
# Health check
curl https://advisor-reports-backend.nicefield-788f351e.eastus.azurecontainerapps.io/api/health/

# Test Azure subscriptions endpoint
curl -H "Authorization: Bearer $TOKEN" \
  https://advisor-reports-backend.nicefield-788f351e.eastus.azurecontainerapps.io/api/azure-subscriptions/

# Check logs
az containerapp logs show \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --follow
```

#### 8.3 Post-Deployment Monitoring (24-48 hours)

**Immediate (0-4 hours):**
- Monitor error rates
- Check API response times
- Verify Celery task execution
- Monitor database connections
- Check Redis memory usage

**Short-term (4-24 hours):**
- User adoption metrics
- Feature usage analytics
- Support ticket volume
- Performance trends

**Medium-term (24-48 hours):**
- Azure API quota usage
- Cost impact analysis
- User satisfaction feedback

**Phase 8 Deliverables:**
- [ ] Production deployment completed
- [ ] Zero downtime achieved
- [ ] Feature flag enabled
- [ ] Monitoring active
- [ ] User notification sent
- [ ] Deployment postmortem documented

---

## Dependencies & Integration Points

### Critical Dependencies

**Phase Dependencies:**
```
Phase 0 (Prep) → Phase 1 (Backend)
Phase 1 → Phase 2 (Celery)
Phase 1 → Phase 3 (API)
Phase 3 → Phase 4 (Frontend)
Phase 5 (Testing) depends on: Phase 1, 2, 3, 4
Phase 7 (Deployment Prep) depends on: Phase 5
Phase 8 (Production) depends on: Phase 7
```

**External Dependencies:**

1. **Azure SDK for Python**
   - `azure-identity==1.14.0`
   - `azure-mgmt-advisor==9.0.0`
   - `azure-mgmt-subscription==3.1.1`

2. **Azure Permissions**
   - Service Principal with "Reader" role on subscriptions
   - Azure Advisor API access
   - No additional costs (Advisor API is free)

3. **Environment Variables**
   ```bash
   # New variables for v2.0
   FEATURE_AZURE_API_INTEGRATION=true
   AZURE_ADVISOR_API_TIMEOUT=300  # 5 minutes
   AZURE_ADVISOR_MAX_RETRIES=3
   ```

### Integration Points

**Backend Integration:**
- Reuse encryption module from `cost_monitoring`
- Extend `Report` model (non-breaking)
- Add new Celery tasks
- New API endpoints

**Frontend Integration:**
- New pages/components
- Enhanced report creation flow
- Backward compatible with existing UI
- New API service layer

**Data Integration:**
- No migration of existing data needed
- New tables for Azure subscriptions
- Existing reports unchanged
- API metadata stored in JSONField

---

## Testing Strategy

### Test Pyramid

```
         E2E Tests (5%)
         /         \
    Integration Tests (15%)
    /                     \
Unit Tests (80%)
```

### Coverage Targets

**Backend:**
- Models: 90%+
- Services: 85%+
- Serializers: 85%+
- Views: 80%+
- Tasks: 80%+
- Overall: 85%+

**Frontend:**
- Components: 70%+
- Pages: 65%+
- Services: 80%+
- Utils: 85%+
- Overall: 70%+

### Test Environments

1. **Local Development**
   - Mock Azure API responses
   - SQLite for fast tests
   - Redis not required for unit tests

2. **CI/CD (GitHub Actions)**
   - PostgreSQL service container
   - Redis service container
   - Real Azure API for integration tests (dev subscription)

3. **Staging**
   - Production-like environment
   - Test Azure subscription
   - Full E2E testing

### Test Automation

**Pre-commit Hooks:**
```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest apps/reports/tests -v
        language: system
        pass_filenames: false

      - id: eslint
        name: eslint
        entry: npm run lint
        language: system
        files: \.(ts|tsx|js|jsx)$
```

**GitHub Actions Workflow:**
```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm ci
        working-directory: ./frontend
      - name: Run tests
        run: npm test -- --coverage
        working-directory: ./frontend
```

---

## Deployment Strategy

### Environments

1. **Development**
   - Local Docker Compose
   - Mock Azure APIs
   - Hot reload enabled

2. **Staging**
   - Azure Container Apps (separate environment)
   - Test Azure subscription
   - Production-like configuration

3. **Production**
   - Azure Container Apps (existing)
   - Real client subscriptions
   - High availability configuration

### Deployment Process

**Blue-Green Deployment:**

```
┌─────────────────────────────────────────────────┐
│         Azure Container Apps Environment        │
│                                                  │
│  ┌──────────────┐         ┌──────────────┐     │
│  │   Blue       │         │   Green      │     │
│  │  (v1.6.1)    │◄────────┤   (v2.0.0)   │     │
│  │              │  Switch │              │     │
│  └──────┬───────┘  Traffic└──────┬───────┘     │
│         │                         │             │
│         └────────┬────────────────┘             │
│                  │                              │
│         ┌────────▼────────┐                     │
│         │  Traffic Split  │                     │
│         │   (Gradual)     │                     │
│         └─────────────────┘                     │
└─────────────────────────────────────────────────┘
```

**Traffic Split Strategy:**
- Day 1: 0% (internal testing only)
- Day 2: 10% (early adopters)
- Day 3: 25%
- Day 5: 50%
- Day 7: 100%

### Rollback Procedures

**Scenario 1: Critical Bug Found**
```bash
# Immediate rollback (< 2 minutes)
az containerapp revision activate \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --revision <previous-revision-name>

# Disable feature flag
az containerapp update --name advisor-reports-backend \
  --set-env-vars "FEATURE_AZURE_API_INTEGRATION=false"
```

**Scenario 2: Database Issue**
- Migrations are designed to be non-destructive
- No data loss on rollback
- New tables can remain (empty)
- Previous version ignores new fields

**Scenario 3: Performance Degradation**
- Enable feature flag only for specific users
- Investigate and optimize
- Gradual re-enable

---

## Risk Management

### Risk Assessment Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Azure API quota exceeded | Medium | High | Implement rate limiting, caching |
| Credential security breach | Low | Critical | Encryption at rest, Azure Key Vault |
| API integration breaks existing CSV flow | Low | High | Comprehensive testing, feature flags |
| User confusion (two workflows) | Medium | Medium | Clear UI, documentation, training |
| Azure API changes breaking integration | Low | Medium | Version pinning, monitoring, error handling |
| Performance degradation | Medium | Medium | Load testing, optimization, monitoring |
| Deployment downtime | Low | High | Blue-green deployment, rollback plan |
| Data loss during migration | Very Low | Critical | Additive migrations, backups |

### Mitigation Strategies

**1. Azure API Quota Management**
```python
# apps/reports/services/azure_advisor_service.py

from django.core.cache import cache
from django.utils import timezone

class AzureAdvisorService:

    CACHE_TTL = 3600  # 1 hour

    def fetch_recommendations(self):
        # Check cache first
        cache_key = f"advisor_recommendations:{self.subscription.subscription_id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            logger.info("Using cached recommendations")
            return cached_data

        # Fetch from API
        recommendations = self._fetch_from_api()

        # Cache for 1 hour
        cache.set(cache_key, recommendations, self.CACHE_TTL)

        return recommendations
```

**2. Rate Limiting**
```python
# apps/reports/views.py

from rest_framework.throttling import UserRateThrottle

class AzureAPIRateThrottle(UserRateThrottle):
    rate = '10/hour'  # Max 10 API syncs per hour per user

class AzureAdvisorSubscriptionViewSet(viewsets.ModelViewSet):
    throttle_classes = [AzureAPIRateThrottle]
```

**3. Error Handling & Retry Logic**
```python
# apps/reports/tasks.py

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(AzureAPIError,),
    retry_backoff=True,
    retry_backoff_max=600
)
def fetch_and_process_advisor_api(self, report_id, subscription_id):
    # Task implementation with automatic retry on Azure API errors
    pass
```

**4. Security - Azure Key Vault (Optional Enhancement)**
```python
# apps/core/secrets.py

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class KeyVaultSecretManager:

    def __init__(self):
        credential = DefaultAzureCredential()
        self.client = SecretClient(
            vault_url=settings.AZURE_KEY_VAULT_URL,
            credential=credential
        )

    def get_secret(self, name: str) -> str:
        secret = self.client.get_secret(name)
        return secret.value
```

### Contingency Plans

**Plan A: Feature Flag Disable**
- If critical issues arise
- Disable feature immediately
- Users fall back to CSV workflow
- No data loss

**Plan B: Partial Rollback**
- Keep backend v2.0 (for API endpoints)
- Rollback frontend to v1.6.1
- API features invisible to users
- Allows time to fix frontend issues

**Plan C: Full Rollback**
- Revert all containers to v1.6.1
- Database migrations remain (harmless)
- CSV workflow fully functional
- Schedule v2.0 re-deployment

---

## Timeline & Resources

### Overall Timeline

**Total Duration:** 10 weeks
**Target Release:** Week 10 (Production deployment)

```
Week 1:  Phase 0 - Preparation
Week 2:  Phase 1 - Backend Foundation
Week 3:  Phase 2 - Celery Tasks
Week 4:  Phase 3 - REST API
Week 5-6: Phase 4 - Frontend
Week 7:  Phase 5 - Testing
Week 8:  Phase 6 - Documentation
Week 8-9: Phase 7 - Deployment Prep
Week 10: Phase 8 - Production Deployment
```

### Detailed Schedule

**Week 1: Preparation**
- Day 1-2: Architecture design finalization
- Day 3: Azure environment setup
- Day 4-5: Development environment setup, kickoff

**Week 2: Backend Foundation**
- Day 1-2: Data models and migrations
- Day 3-5: Azure Advisor service implementation
- Day 6-7: Encryption module, serializers, unit tests

**Week 3: Celery Integration**
- Day 1-3: New Celery tasks
- Day 4-5: Refactor existing tasks
- Day 6-7: Task testing and optimization

**Week 4: REST API**
- Day 1-2: Subscription management endpoints
- Day 3-4: Enhanced report creation
- Day 5-7: API testing and documentation

**Week 5-6: Frontend**
- Week 5 Day 1-2: API service layer
- Week 5 Day 3-5: Azure Subscriptions page
- Week 5 Day 6-7: Report creation enhancements
- Week 6 Day 1-3: UI polish and testing
- Week 6 Day 4-5: Frontend integration testing

**Week 7: Testing**
- Day 1-2: Backend unit tests
- Day 3: Frontend unit tests
- Day 4-5: Integration tests
- Day 6-7: E2E tests and bug fixes

**Week 8: Documentation**
- Day 1-2: User documentation
- Day 3-4: Developer documentation
- Day 5: Video tutorials (optional)

**Week 9: Deployment Prep**
- Day 1-2: Feature flags and staging deployment
- Day 3-4: Beta testing
- Day 5-7: Monitoring setup and final validation

**Week 10: Production**
- Day 1: Database migrations
- Day 2: Backend/frontend deployment
- Day 3-7: Gradual rollout and monitoring

### Resource Requirements

**Team Composition:**

1. **Backend Developer** (1 person, full-time)
   - Phases 1, 2, 3, 5
   - Skills: Django, Azure SDK, Celery

2. **Frontend Developer** (1 person, full-time)
   - Phases 4, 5
   - Skills: React, TypeScript, TailwindCSS

3. **DevOps Engineer** (0.5 person, part-time)
   - Phases 7, 8
   - Skills: Azure Container Apps, CI/CD, monitoring

4. **QA Engineer** (0.5 person, part-time)
   - Phase 5
   - Skills: Testing, Playwright, pytest

5. **Technical Writer** (0.25 person, part-time)
   - Phase 6
   - Skills: Documentation, video creation

6. **Project Manager** (0.25 person, part-time)
   - All phases
   - Skills: Coordination, stakeholder management

**Total Effort Estimation:**
- Backend: 40 days (8 weeks)
- Frontend: 30 days (6 weeks)
- DevOps: 15 days (3 weeks)
- QA: 10 days (2 weeks)
- Documentation: 5 days (1 week)
- PM: 10 days (2 weeks)
- **Total:** 110 person-days (~5.5 person-months)

### Budget Considerations

**Development Costs:**
- Personnel: ~5.5 person-months
- Azure development subscription: $200/month × 3 months = $600
- Third-party tools (if needed): $500

**Infrastructure Costs (Incremental):**
- No additional container apps needed
- Minimal increase in:
  - Database storage: +5GB (~$1/month)
  - Redis memory: No change (existing cache used)
  - Outbound bandwidth: +10GB (~$1/month)
- **Total incremental:** ~$2-5/month

**Total Project Budget (Estimated):**
- Development: Personnel costs (varies by region)
- Infrastructure: $600 (one-time) + $5/month (ongoing)
- Contingency: 20% buffer

---

## Success Metrics

### Key Performance Indicators (KPIs)

**Adoption Metrics:**
- % of users who add Azure subscriptions: Target 40% in 3 months
- % of reports created via API vs CSV: Target 30% API by 6 months
- Average time to first API-based report: Target < 10 minutes

**Technical Metrics:**
- Azure API success rate: Target 99%+
- API response time (p95): Target < 5 seconds
- Report generation time (API vs CSV): Target similar or better
- System uptime: Target 99.9%

**User Satisfaction:**
- User feedback score: Target 4.5/5
- Support ticket volume: Target no increase
- Feature usage rate: Target 50%+ of active users try API feature

**Business Metrics:**
- Time saved per report: Target 60% reduction (from CSV download time)
- User retention: Target no decrease
- New user activation: Target 20% increase

### Monitoring Dashboard

**Real-time Metrics:**
1. Azure API calls (count, success rate, response time)
2. API-based report creation (count, status distribution)
3. Credential validation success rate
4. Celery task queue depth and processing time
5. Error rates by endpoint

**Weekly Reports:**
1. Adoption trend (users, subscriptions, reports)
2. Performance comparison (API vs CSV)
3. Error analysis and top issues
4. User feedback summary

**Monthly Business Review:**
1. ROI analysis
2. User satisfaction score
3. Feature roadmap priorities
4. Infrastructure cost analysis

---

## Acceptance Criteria

### Phase Acceptance Criteria

**Phase 1: Backend Foundation**
- [ ] All migrations apply successfully
- [ ] `AzureAdvisorSubscription` model CRUD operations work
- [ ] Credentials encrypt/decrypt correctly
- [ ] `AzureAdvisorService` can authenticate with Azure
- [ ] Unit test coverage ≥ 85%
- [ ] No breaking changes to existing models

**Phase 2: Celery Integration**
- [ ] `fetch_and_process_advisor_api` task works end-to-end
- [ ] Task retries on failure (max 3 times)
- [ ] Task timeout prevents indefinite hangs (5 min limit)
- [ ] Existing CSV tasks remain functional
- [ ] Task monitoring in Application Insights

**Phase 3: REST API**
- [ ] All CRUD endpoints for subscriptions work
- [ ] Credential validation endpoint functional
- [ ] Report creation accepts `azure_subscription_id`
- [ ] OpenAPI documentation auto-generated
- [ ] API tests pass with ≥ 80% coverage

**Phase 4: Frontend**
- [ ] Azure Subscriptions page renders correctly
- [ ] Add subscription flow completes successfully
- [ ] Report creation modal supports both CSV and API
- [ ] UI clearly indicates data source (CSV vs API badge)
- [ ] Responsive design on mobile/tablet
- [ ] Accessibility (WCAG 2.1 AA compliance)

**Phase 5: Testing**
- [ ] All unit tests pass
- [ ] Integration tests cover key workflows
- [ ] E2E tests pass in CI/CD
- [ ] Load testing shows acceptable performance
- [ ] Security scan passes (no critical/high vulnerabilities)

**Phase 6: Documentation**
- [ ] User guide published and reviewed
- [ ] Azure setup guide with screenshots
- [ ] API reference complete
- [ ] Developer architecture documented
- [ ] Video tutorials created (optional)

**Phase 7: Deployment Prep**
- [ ] Feature flags working correctly
- [ ] Staging deployment successful
- [ ] Rollback tested and documented
- [ ] Monitoring dashboards created
- [ ] Alert rules configured

**Phase 8: Production Deployment**
- [ ] Zero downtime achieved
- [ ] All health checks passing
- [ ] Feature flag enabled successfully
- [ ] User notification sent
- [ ] No P1/P2 bugs in first 48 hours

### Overall v2.0 Acceptance Criteria

**Functional:**
- [ ] Users can add Azure subscriptions with Service Principal credentials
- [ ] Users can create reports using Subscription ID (no CSV upload)
- [ ] API-fetched recommendations generate same quality reports as CSV
- [ ] CSV upload workflow remains fully functional
- [ ] Report history shows data source correctly
- [ ] Users can switch between CSV and API workflows seamlessly

**Non-Functional:**
- [ ] API-based report generation completes within 2 minutes (p95)
- [ ] System handles ≥ 100 concurrent API requests
- [ ] Credentials encrypted at rest and in transit
- [ ] No data loss during migration
- [ ] Backward compatibility maintained
- [ ] Documentation complete and accessible

**Business:**
- [ ] At least 20% of beta users adopt API workflow
- [ ] User satisfaction score ≥ 4/5
- [ ] No increase in support tickets
- [ ] Feature can be monetized (if desired)

---

## Appendices

### Appendix A: Azure Advisor API Overview

**API Capabilities:**
- List recommendations for a subscription
- Filter by category (Cost, Security, Performance, etc.)
- Get recommendation details
- Suppress recommendations
- Get Advisor score

**API Limits:**
- No explicit rate limits documented
- Recommendation data updated daily
- Max 1000 recommendations per response (pagination required)

**Authentication:**
- Azure AD Service Principal
- Requires "Reader" role on subscription
- Same pattern as Cost Management API

### Appendix B: Data Mapping

**Azure Advisor API → Internal Model:**

| Azure API Field | Internal Field | Notes |
|----------------|----------------|-------|
| `category` | `category` | Direct mapping |
| `impact` | `business_impact` | Values: High, Medium, Low |
| `shortDescription.problem` | `recommendation` | Main text |
| `extendedProperties.savingsAmount` | `potential_savings` | Numeric value |
| `extendedProperties.savingsCurrency` | `currency` | Default USD |
| `resourceMetadata.resourceId` | `resource_name` | Parsed from ID |
| `resourceMetadata.resourceGroup` | `resource_group` | Direct |
| `suppressionIds` | (not stored) | Future enhancement |

### Appendix C: Security Checklist

**Data Security:**
- [x] Credentials encrypted at rest (Fernet encryption)
- [x] Credentials encrypted in transit (HTTPS/TLS)
- [ ] Optional: Azure Key Vault integration
- [x] Client secrets never logged
- [x] Client secrets never returned in API responses

**Access Control:**
- [x] Authentication required for all endpoints
- [x] User can only access their organization's subscriptions
- [x] Role-based permissions (future: RBAC)
- [x] Audit logging for sensitive operations

**Azure Security:**
- [x] Service Principal with least privilege (Reader role)
- [x] Tenant isolation (one Service Principal per tenant)
- [x] Credential rotation reminder (90 days)
- [ ] Future: Managed Identity support

### Appendix D: Troubleshooting Guide

**Common Issues:**

1. **"Invalid credentials" error**
   - Check Service Principal exists in Azure AD
   - Verify Client ID and Secret are correct
   - Ensure Service Principal has Reader role on subscription
   - Check tenant ID matches Azure AD tenant

2. **"No recommendations found"**
   - Azure Advisor may have no recommendations (legitimate)
   - Check subscription has resources deployed
   - Verify Service Principal has Reader access
   - Azure Advisor data updates once per day

3. **"API timeout"**
   - Check Azure service health
   - Verify network connectivity
   - Check Celery worker is running
   - Review task timeout settings (default 5 min)

4. **"Report stuck in processing"**
   - Check Celery worker logs
   - Verify Redis connection
   - Run `python manage.py fix_stuck_reports`
   - Check Application Insights for errors

### Appendix E: Cost Analysis

**Azure Costs (per 1000 API calls):**
- Azure Advisor API: Free (no charges)
- Azure authentication calls: Free (no charges)
- Data transfer: ~$0.01 (outbound data)
- **Total:** Negligible

**Platform Costs:**
- Additional database storage: ~$1/month per 10GB
- Additional Celery worker time: Minimal (existing workers)
- Redis memory: No change (using existing cache)
- **Total incremental:** < $5/month for typical usage

**ROI Calculation:**
- Time saved per report: ~15 minutes (no CSV download/upload)
- Reports per month: ~100 (example)
- Time saved: 25 hours/month
- Value at $50/hour: $1,250/month
- **ROI:** Very high (minimal cost, significant time savings)

---

## Conclusion

This implementation plan provides a comprehensive roadmap for adding Azure Advisor API integration to the Azure Advisor Reports Platform v2.0. The plan prioritizes:

1. **Backward Compatibility:** Existing CSV workflow remains fully functional
2. **Zero Downtime:** Blue-green deployment with feature flags
3. **Security:** Encrypted credentials, role-based access
4. **Quality:** Comprehensive testing at all levels
5. **User Experience:** Clear UI, excellent documentation

**Key Success Factors:**
- Reuse proven patterns from `cost_monitoring` app
- Incremental rollout with feature flags
- Thorough testing before production
- Clear documentation and training
- Monitoring and observability from day one

**Next Steps:**
1. Review and approve this plan
2. Allocate resources (team members)
3. Set up Azure development subscription
4. Begin Phase 0 (Preparation)
5. Weekly progress reviews

**Questions for Stakeholders:**
1. Approval to proceed with 10-week timeline?
2. Team member assignments confirmed?
3. Azure subscription for development ready?
4. Budget approved?
5. Target release date confirmed?

---

**Document Control:**
- Version: 1.0
- Created: November 17, 2025
- Author: Project Orchestrator
- Next Review: At end of Phase 0
- Approval Status: Pending

---

**End of Implementation Plan**
