# Manual Recommendations Input - Integration Guide (v1.7.0)

This document explains how to integrate the manual recommendations input feature into your frontend application.

## Overview

The manual recommendations input feature allows users to add custom recommendations that aren't captured by Azure Advisor. This is useful for:
- Adding recommendations from other sources
- Including custom optimization opportunities
- Supplementing Azure Advisor data with manual findings

## Backend Endpoints

### Add Manual Recommendations
```http
POST /api/v1/reports/{report_id}/add-manual-recommendations/
Content-Type: application/json
Authorization: Bearer {token}

{
  "recommendations": [
    {
      "category": "cost",
      "business_impact": "high",
      "recommendation": "Implement auto-shutdown for dev VMs during non-business hours",
      "subscription_id": "sub-123",
      "subscription_name": "Development Subscription",
      "resource_group": "rg-dev-environment",
      "resource_name": "vm-dev-01",
      "resource_type": "Microsoft.Compute/virtualMachines",
      "potential_savings": 1200.00,
      "currency": "USD",
      "potential_benefits": "Reduce monthly costs by shutting down VMs outside of 9-5 business hours",
      "advisor_score_impact": 5.0
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "status": "success",
  "message": "1 manual recommendation(s) added successfully",
  "data": {
    "recommendations_created": 1,
    "total_recommendations": 45,
    "total_potential_savings": 12500.00
  }
}
```

## Frontend Integration

### 1. Create API Service Function

Create or update `frontend/src/services/reportsApi.ts`:

```typescript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

interface ManualRecommendation {
  category: 'cost' | 'security' | 'reliability' | 'operational_excellence' | 'performance';
  business_impact: 'high' | 'medium' | 'low';
  recommendation: string;
  subscription_id?: string;
  subscription_name?: string;
  resource_group?: string;
  resource_name?: string;
  resource_type?: string;
  potential_savings?: number;
  currency?: string;
  potential_benefits?: string;
  retirement_date?: string;
  retiring_feature?: string;
  advisor_score_impact?: number;
}

export const addManualRecommendations = async (
  reportId: string,
  recommendations: ManualRecommendation[]
) => {
  const response = await axios.post(
    `${API_BASE_URL}/reports/${reportId}/add-manual-recommendations/`,
    { recommendations },
    {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      },
    }
  );
  return response.data;
};
```

### 2. Use in Report Details Page

Example usage in a report details component:

```typescript
import React, { useState } from 'react';
import { ManualRecommendationForm } from '../components/reports/ManualRecommendationForm';
import { addManualRecommendations } from '../services/reportsApi';

export const ReportDetailsPage: React.FC<{ reportId: string }> = ({ reportId }) => {
  const [isManualFormOpen, setIsManualFormOpen] = useState(false);

  const handleAddManualRecommendations = async (recommendations: any[]) => {
    try {
      const result = await addManualRecommendations(reportId, recommendations);
      console.log(`Added ${result.data.recommendations_created} recommendations`);

      // Refresh report data
      // await fetchReportDetails(reportId);

      // Show success message
      alert(result.message);
    } catch (error) {
      console.error('Failed to add manual recommendations:', error);
      throw error;
    }
  };

  return (
    <div>
      {/* Report Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Report Details</h1>

        {/* Add Manual Data Button */}
        <button
          onClick={() => setIsManualFormOpen(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
        >
          + Add Manual Data
        </button>
      </div>

      {/* Report Content */}
      <div>
        {/* Your existing report content */}
      </div>

      {/* Manual Recommendation Form Modal */}
      <ManualRecommendationForm
        isOpen={isManualFormOpen}
        onClose={() => setIsManualFormOpen(false)}
        onSubmit={handleAddManualRecommendations}
        reportId={reportId}
      />
    </div>
  );
};
```

### 3. Add to Report Creation Workflow

You can also integrate this into the report creation wizard as an optional step:

```typescript
// In your report creation wizard
const ReportWizard: React.FC = () => {
  const [step, setStep] = useState(1);
  const [reportId, setReportId] = useState<string | null>(null);
  const [isAddingManualData, setIsAddingManualData] = useState(false);

  const steps = [
    { number: 1, name: 'Select Data Source', component: <DataSourceStep /> },
    { number: 2, name: 'Configure Report', component: <ConfigureReportStep /> },
    { number: 3, name: 'Add Manual Data (Optional)', component: <ManualDataStep /> },
    { number: 4, name: 'Generate Report', component: <GenerateReportStep /> },
  ];

  // After report is created (step 2), show option to add manual data
  const handleReportCreated = (newReportId: string) => {
    setReportId(newReportId);
    setStep(3); // Move to manual data step
  };

  const handleSkipManualData = () => {
    setStep(4); // Skip to report generation
  };

  return (
    <div className="wizard-container">
      {/* Wizard steps display */}
      <div className="wizard-steps">
        {steps.map((s) => (
          <div key={s.number} className={step === s.number ? 'active' : ''}>
            {s.name}
          </div>
        ))}
      </div>

      {/* Step 3: Manual Data (Optional) */}
      {step === 3 && reportId && (
        <div>
          <h2>Add Manual Recommendations (Optional)</h2>
          <p className="text-gray-600 mb-4">
            Add any custom recommendations not captured by Azure Advisor
          </p>

          <div className="flex gap-4">
            <button
              onClick={() => setIsAddingManualData(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md"
            >
              Add Manual Data
            </button>
            <button
              onClick={handleSkipManualData}
              className="px-4 py-2 border border-gray-300 rounded-md"
            >
              Skip This Step
            </button>
          </div>

          {isAddingManualData && (
            <ManualRecommendationForm
              isOpen={isAddingManualData}
              onClose={() => setIsAddingManualData(false)}
              onSubmit={async (recommendations) => {
                await addManualRecommendations(reportId, recommendations);
                setIsAddingManualData(false);
                setStep(4); // Move to next step after adding
              }}
              reportId={reportId}
            />
          )}
        </div>
      )}
    </div>
  );
};
```

## Features

### Automatic Reservation Detection
The backend automatically analyzes manual recommendations for Saving Plans and Reserved Instances using the `ReservationAnalyzer` service. This means:
- Keywords like "Reserved Instance", "Savings Plan", "Reserved Capacity" are detected
- Commitment terms (1-year or 3-year) are extracted from the text
- Total commitment savings are automatically calculated
- Recommendations are properly categorized in reports

### Validation
- Category and business_impact are required
- Recommendation text is required (max 5000 characters)
- Potential savings must be non-negative
- Advisor score impact must be between 0-100
- Maximum 100 recommendations can be added at once

### Marking Manual Recommendations
Manual recommendations are marked with `csv_row_number = -1` to distinguish them from CSV-imported or API-fetched data. This allows filtering and identification in the UI if needed.

## UI/UX Recommendations

1. **Placement**: Add the "Add Manual Data" button prominently in:
   - Report details page header
   - Report creation wizard (as optional step)
   - Report edit/update view

2. **Timing**: Best times to offer manual input:
   - After CSV upload completes
   - After Azure API sync completes
   - Before final report generation
   - Any time during report editing

3. **Visual Feedback**:
   - Show count of manual vs. imported recommendations
   - Display badge or indicator on manually-added items
   - Provide confirmation message after successful addition

4. **Workflow Integration**:
   - Make it optional but visible
   - Don't block report generation
   - Allow adding more later
   - Provide ability to edit/delete manual entries (future enhancement)

## Example Use Cases

1. **Custom Cost Optimization**:
   - "Implement tagging policy for cost tracking"
   - "Migrate legacy databases to serverless options"
   - "Consolidate redundant storage accounts"

2. **Security Recommendations**:
   - "Enable Azure AD multi-factor authentication for all users"
   - "Implement network segmentation for production workloads"

3. **Operational Excellence**:
   - "Set up automated backup schedules for critical databases"
   - "Implement infrastructure as code with Terraform"

## Testing

You can test the feature using curl:

```bash
# Add manual recommendations
curl -X POST http://localhost:8000/api/v1/reports/{report-id}/add-manual-recommendations/ \
  -H "Authorization: Bearer {your-token}" \
  -H "Content-Type: application/json" \
  -d '{
    "recommendations": [
      {
        "category": "cost",
        "business_impact": "high",
        "recommendation": "Implement auto-shutdown for dev VMs",
        "potential_savings": 1200.00,
        "currency": "USD"
      }
    ]
  }'
```

## Future Enhancements

Consider adding these features in future versions:
- Bulk import from Excel/CSV template
- Edit existing manual recommendations
- Delete manual recommendations
- Templates for common recommendation types
- AI-assisted recommendation suggestions
- Attach files/screenshots to recommendations
