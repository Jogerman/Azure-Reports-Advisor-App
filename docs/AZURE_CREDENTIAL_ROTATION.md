# Azure AD Credential Rotation Guide

**Audience:** DevOps Engineers, System Administrators
**Priority:** CRITICAL SECURITY
**Last Updated:** November 5, 2025

---

## Overview

This document provides step-by-step procedures for rotating Azure AD credentials (Client Secrets) for the Azure Reports Advisor application. Regular credential rotation is a critical security practice that limits the exposure window if credentials are compromised.

**Rotation Schedule:**
- **Regular Rotation:** Every 90 days (recommended)
- **Emergency Rotation:** Immediately if compromise is suspected
- **Expiration Alert:** Set alerts 30-60 days before expiration

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Before You Start](#before-you-start)
3. [Rotation Procedure](#rotation-procedure)
4. [Verification Steps](#verification-steps)
5. [Rollback Procedure](#rollback-procedure)
6. [Emergency Rotation](#emergency-rotation)
7. [Automation](#automation)
8. [Audit and Compliance](#audit-and-compliance)

---

## Prerequisites

### Required Access
- Azure Portal access with permissions to manage App Registrations
- Azure Container Apps access (for production deployments)
- Access to environment variable management (Azure Portal, Key Vault)

### Tools Required
- Azure CLI (`az`) installed and authenticated
- Access to Azure Portal (https://portal.azure.com)
- Access to production logs and monitoring

### Before Rotation
- Verify current credentials are working
- Schedule maintenance window (if zero-downtime is not required)
- Notify team members
- Backup current configuration

---

## Before You Start

### 1. Review Current Configuration

Check the current Azure AD configuration in your environment:

```bash
# Check Azure Container Apps secrets (don't display values)
az containerapp secret list \
  --name azure-advisor-backend \
  --resource-group <your-resource-group> \
  --query "[?name=='azure-client-secret'].name"
```

### 2. Check Secret Expiration

In Azure Portal:
1. Navigate to: **Azure Active Directory** > **App Registrations**
2. Select your application: `Azure Reports Advisor`
3. Go to: **Certificates & secrets**
4. Check expiration date of current client secret

**IMPORTANT:** If secret is expiring in less than 7 days, this is URGENT.

### 3. Review Audit Logs

Check for any suspicious activity before rotation:

```bash
# Check Azure AD sign-in logs
az ad signed-in-user list-owned-objects
```

In Azure Portal:
- **Azure Active Directory** > **Monitoring** > **Sign-in logs**
- **Azure Active Directory** > **Monitoring** > **Audit logs**

Look for:
- Unusual login locations
- Failed authentication attempts
- Unexpected application access

---

## Rotation Procedure

### Option A: Zero-Downtime Rotation (Recommended)

This approach uses dual secrets to ensure no downtime during rotation.

#### Step 1: Generate New Secret in Azure AD

1. Navigate to **Azure Portal** > **Azure Active Directory** > **App Registrations**
2. Select your application: `Azure Reports Advisor`
3. Go to **Certificates & secrets**
4. Click **New client secret**
5. Configure:
   - **Description:** `Backend API - Generated <DATE>`
   - **Expires:** `In 3 months` (recommended) or `Custom` (90 days)
6. Click **Add**
7. **CRITICAL:** Copy the secret value immediately (it only shows once)
   - Save to secure location (password manager, Azure Key Vault)

```bash
# Example secret format (yours will be different):
# Secret ID: abc123def-456-789-ghi-012345678901
# Secret Value: XyZ~AbC123.dEf456_GhI789~JkL012
```

#### Step 2: Add New Secret to Production (Without Removing Old One)

**Using Azure CLI:**

```bash
# Add the new secret as a secondary secret
az containerapp secret set \
  --name azure-advisor-backend \
  --resource-group <your-resource-group> \
  --secrets azure-client-secret-new="<NEW_SECRET_VALUE>"

# Update environment variable to use new secret
az containerapp update \
  --name azure-advisor-backend \
  --resource-group <your-resource-group> \
  --set-env-vars AZURE_CLIENT_SECRET=secretref:azure-client-secret-new
```

**Using Azure Portal:**

1. Navigate to your **Container App**: `azure-advisor-backend`
2. Go to **Settings** > **Secrets**
3. Click **Add** to add new secret:
   - **Key:** `azure-client-secret-new`
   - **Value:** `<paste new secret>`
4. Go to **Settings** > **Environment variables**
5. Update `AZURE_CLIENT_SECRET` to reference: `azure-client-secret-new`
6. Click **Save** (this will restart the container)

#### Step 3: Create New Revision and Monitor

```bash
# Create new revision with new secret
az containerapp revision copy \
  --name azure-advisor-backend \
  --resource-group <your-resource-group>

# Monitor the new revision
az containerapp revision show \
  --name azure-advisor-backend \
  --resource-group <your-resource-group> \
  --query "properties.provisioningState"
```

#### Step 4: Verify New Secret Works

**Test authentication:**

```bash
# Test login endpoint
curl -X POST https://<your-backend-url>/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"access_token": "<valid_azure_ad_token>"}'

# Check application logs
az containerapp logs show \
  --name azure-advisor-backend \
  --resource-group <your-resource-group> \
  --tail 50
```

**Check for errors:**
- No authentication failures in logs
- Users can log in successfully
- No Azure AD token validation errors

#### Step 5: Remove Old Secret (After 24-48 Hours)

Wait 24-48 hours to ensure new secret is stable, then:

**In Azure AD:**
1. Navigate to **App Registrations** > Your App > **Certificates & secrets**
2. Find the old secret (check by description and expiration date)
3. Click **Delete**
4. Confirm deletion

**In Azure Container Apps:**

```bash
# Remove old secret from Container Apps
az containerapp secret remove \
  --name azure-advisor-backend \
  --resource-group <your-resource-group> \
  --secret-names azure-client-secret
```

### Option B: Simple Rotation (With Brief Downtime)

Use this approach if zero-downtime is not critical.

#### Step 1: Generate New Secret (Same as Option A, Step 1)

#### Step 2: Update Secret Directly

```bash
# Update the existing secret
az containerapp secret set \
  --name azure-advisor-backend \
  --resource-group <your-resource-group> \
  --secrets azure-client-secret="<NEW_SECRET_VALUE>"

# Trigger revision restart
az containerapp revision restart \
  --name azure-advisor-backend \
  --resource-group <your-resource-group>
```

Expected downtime: 30-60 seconds during restart

#### Step 3: Verify (Same as Option A, Step 4)

#### Step 4: Delete Old Secret in Azure AD (Same as Option A, Step 5)

---

## Verification Steps

### 1. Health Check

```bash
# Check application health endpoint
curl https://<your-backend-url>/health/

# Expected response:
# {"status": "healthy", "timestamp": "2025-11-05T..."}
```

### 2. Authentication Test

Test login with a valid Azure AD account:

```bash
# From frontend, attempt login
# OR use Postman/curl with valid Azure AD token
```

### 3. Monitor Logs

```bash
# Check for authentication errors
az containerapp logs show \
  --name azure-advisor-backend \
  --resource-group <your-resource-group> \
  --tail 100 | grep -i "auth\|error\|azure"
```

### 4. Application Insights

In Azure Portal:
1. Go to **Application Insights** for your app
2. Check **Failures** dashboard
3. Look for spike in errors after rotation
4. Check **Live Metrics** for real-time status

---

## Rollback Procedure

If issues are detected after rotation:

### Quick Rollback (Within 24-48 hours)

If old secret is still active:

```bash
# Revert to old secret
az containerapp secret set \
  --name azure-advisor-backend \
  --resource-group <your-resource-group> \
  --secrets azure-client-secret="<OLD_SECRET_VALUE>"

# Restart to apply
az containerapp revision restart \
  --name azure-advisor-backend \
  --resource-group <your-resource-group>
```

### Emergency Rollback (If old secret deleted)

1. Generate a new secret in Azure AD (as emergency secret)
2. Update Container Apps with emergency secret
3. Investigate root cause
4. Plan re-rotation after fixing issues

---

## Emergency Rotation

**When to perform emergency rotation:**
- Suspected credential compromise
- Secret accidentally exposed (logs, code repository, screenshots)
- Security incident
- Employee termination (if they had access)

**Emergency procedure:**

1. **Immediate:** Generate new secret in Azure AD
2. **Immediate:** Update production with new secret
3. **Immediate:** Revoke old secret in Azure AD
4. **Within 1 hour:** Review audit logs for unauthorized access
5. **Within 24 hours:** Complete security incident report
6. **Within 48 hours:** Review and update access controls

```bash
# Emergency rotation script
#!/bin/bash

# 1. Generate and set new secret (manual step in portal)
NEW_SECRET="<paste_new_secret_here>"

# 2. Update production immediately
az containerapp secret set \
  --name azure-advisor-backend \
  --resource-group <your-resource-group> \
  --secrets azure-client-secret="$NEW_SECRET"

# 3. Force restart
az containerapp revision restart \
  --name azure-advisor-backend \
  --resource-group <your-resource-group>

# 4. Verify
echo "Waiting 30 seconds for restart..."
sleep 30
az containerapp logs show \
  --name azure-advisor-backend \
  --resource-group <your-resource-group> \
  --tail 20
```

---

## Automation

### Set Up Expiration Alerts

**Using Azure Monitor:**

```bash
# Create alert rule for secret expiration
az monitor metrics alert create \
  --name "Azure-AD-Secret-Expiring" \
  --resource-group <your-resource-group> \
  --scopes /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.AAD/secrets \
  --condition "TimeToExpiration < 30 days" \
  --description "Azure AD client secret expiring in 30 days" \
  --evaluation-frequency 1d \
  --window-size 1d \
  --action <action-group-id>
```

### Automated Rotation Script (Future Enhancement)

```python
# rotation_script.py - Example automation
# This would be run as scheduled Azure Function or GitHub Action

import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.containerapp import ContainerAppsAPIClient
from msgraph.core import GraphClient

def rotate_secret():
    # 1. Generate new secret via Microsoft Graph API
    # 2. Update Azure Container Apps secret
    # 3. Verify new secret works
    # 4. Delete old secret
    # 5. Send notification
    pass
```

---

## Audit and Compliance

### Document Rotation

After each rotation, update rotation log:

| Date | Old Secret ID | New Secret ID | Rotated By | Reason | Status |
|------|---------------|---------------|------------|--------|--------|
| 2025-11-05 | abc-123 | def-456 | admin@company.com | Scheduled | Success |

### Compliance Checks

- [ ] Secret rotated within 90 days
- [ ] Old secret deleted after verification
- [ ] Rotation documented in change log
- [ ] No security incidents during rotation
- [ ] Team notified of rotation
- [ ] Monitoring confirmed normal operations

### Security Best Practices

1. **Never commit secrets to code repositories**
2. **Use Azure Key Vault for production secrets** (recommended upgrade)
3. **Implement secret scanning in CI/CD**
4. **Limit access to production secrets** (RBAC)
5. **Enable audit logging** for secret access
6. **Use managed identities** where possible (future enhancement)

---

## Troubleshooting

### Issue: "Invalid client secret" error after rotation

**Symptoms:**
- Users cannot log in
- Logs show: `Invalid Azure AD token`
- Application Insights shows authentication failures

**Resolution:**
1. Verify new secret was correctly copied (no extra spaces)
2. Check secret is not expired in Azure AD
3. Confirm Container Apps environment variable is updated
4. Restart container app
5. If issue persists, rollback to old secret (if still active)

### Issue: "Secret not found" error

**Symptoms:**
- Container app fails to start
- Logs show: `AZURE_CLIENT_SECRET not set`

**Resolution:**
1. Check secret exists in Container Apps: `az containerapp secret list`
2. Verify environment variable references correct secret name
3. Ensure secret name matches reference (case-sensitive)

### Issue: Intermittent authentication failures

**Symptoms:**
- Some users can log in, others cannot
- Failures occur randomly

**Possible causes:**
- Multiple container instances with mixed configurations
- DNS/load balancer caching old configuration
- Some instances didn't restart properly

**Resolution:**
1. Force restart all instances
2. Wait 2-3 minutes for propagation
3. Clear Azure AD token cache on client-side

---

## Contact Information

**For issues during rotation:**
- **Primary Contact:** DevOps Team - devops@company.com
- **Secondary Contact:** Security Team - security@company.com
- **Emergency:** On-call engineer - +1-XXX-XXX-XXXX

**Escalation Path:**
1. DevOps Engineer (0-15 minutes)
2. DevOps Lead (15-30 minutes)
3. CTO (30+ minutes)

---

## Appendix: Secret Management Best Practices

### Use Azure Key Vault (Recommended)

Instead of Container Apps secrets, use Azure Key Vault for enhanced security:

```bash
# Store secret in Key Vault
az keyvault secret set \
  --vault-name <your-keyvault> \
  --name azure-client-secret \
  --value "<secret>"

# Grant Container App access to Key Vault
az containerapp identity assign \
  --name azure-advisor-backend \
  --resource-group <your-resource-group> \
  --system-assigned

# Reference Key Vault secret in Container App
az containerapp update \
  --name azure-advisor-backend \
  --resource-group <your-resource-group> \
  --set-env-vars \
    AZURE_CLIENT_SECRET=@Microsoft.KeyVault(SecretUri=https://<vault>.vault.azure.net/secrets/azure-client-secret)
```

**Benefits:**
- Centralized secret management
- Automatic secret rotation capabilities
- Enhanced audit logging
- Fine-grained access control
- Compliance with security standards

---

## Change History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-11-05 | Initial documentation | Claude Security Specialist |

---

**Next Review Date:** December 5, 2025
