# Credentials Management Guide
## Azure Reports Advisor Application

**Version:** 1.0
**Last Updated:** November 5, 2025
**Status:** Security Documentation

---

## Overview

This document provides guidance on secure credential management for the Azure Reports Advisor Application. All credentials, secrets, and sensitive configuration values MUST be managed securely according to these guidelines.

---

## CRITICAL: Never Hardcode Credentials

**DO NOT** hardcode any of the following in source code:
- Azure Tenant IDs
- Azure Client IDs
- Azure Client Secrets
- SECRET_KEY values
- Database passwords
- API keys
- Storage account keys
- Redis passwords
- Any other sensitive configuration

---

## Environment Variables

### Required Environment Variables

All sensitive configuration MUST be provided via environment variables:

| Variable | Description | Example Placeholder |
|----------|-------------|---------------------|
| `AZURE_TENANT_ID` | Azure AD Tenant ID | `00000000-0000-0000-0000-000000000000` |
| `AZURE_CLIENT_ID` | Azure AD Application Client ID | `YOUR_AZURE_CLIENT_ID_HERE` |
| `AZURE_CLIENT_SECRET` | Azure AD Application Client Secret | `YOUR_AZURE_CLIENT_SECRET_HERE` |
| `SECRET_KEY` | Django Secret Key (50+ chars) | Generated with `secrets.token_urlsafe(50)` |
| `DB_PASSWORD` | PostgreSQL Database Password | Strong random password |
| `REDIS_PASSWORD` | Redis Cache Password | Strong random password |
| `AZURE_ACCOUNT_KEY` | Azure Storage Account Key | From Azure Portal |

### Configuration Files

**Production Configuration Files:**
- `/azure_advisor_reports/.env` - NEVER commit to git (in `.gitignore`)
- `/azure_advisor_reports/.env.example` - Template with placeholders only
- `/backend-appsettings.example.json` - Azure Container Apps config template

**Development Configuration:**
- Use `/azure_advisor_reports/.env` for local development
- Copy `.env.example` to `.env` and fill in your values
- NEVER commit your `.env` file

---

## Azure AD Credentials

### Where to Find Azure AD Credentials

1. **Azure Portal** → **Azure Active Directory**
2. Navigate to **App Registrations**
3. Select your application

**Tenant ID:**
- Azure Active Directory → Overview → Tenant ID

**Client ID:**
- App Registrations → [Your App] → Overview → Application (client) ID

**Client Secret:**
- App Registrations → [Your App] → Certificates & secrets
- Create new client secret with appropriate expiration
- **IMPORTANT:** Copy the secret value immediately (shown only once)

### Setting Azure AD Environment Variables

**For Deployment Scripts:**
```bash
# PowerShell
$env:AZURE_TENANT_ID="your-tenant-id"
./deploy-production.ps1 -RegistryName "yourregistry" -ResourceGroup "yourrg"

# Linux/Mac
export AZURE_TENANT_ID="your-tenant-id"
./deploy-production.sh
```

**For Container Apps:**
Use Azure Portal or Azure CLI to set secrets:
```bash
az containerapp secret set \
  --name azure-advisor-backend \
  --resource-group <resource-group> \
  --secrets azure-tenant-id=<your-tenant-id>
```

---

## Secret Rotation Procedures

### Azure AD Client Secret Rotation

**Recommended Frequency:** Every 90 days

**Procedure:**
1. Generate new client secret in Azure Portal
2. Test new secret in staging environment
3. Update production secrets without downtime:
   ```bash
   az containerapp secret set \
     --name azure-advisor-backend \
     --resource-group <resource-group> \
     --secrets azure-client-secret=<new-secret>

   az containerapp revision copy \
     --name azure-advisor-backend \
     --resource-group <resource-group>
   ```
4. Verify application health
5. Wait 24 hours for propagation
6. Delete old secret from Azure AD

### Django SECRET_KEY Rotation

**Recommended Frequency:** Every 180 days or after security incident

**Procedure:**
1. Generate new SECRET_KEY:
   ```bash
   python -c 'import secrets; print(secrets.token_urlsafe(50))'
   ```

2. Add old key to `SECRET_KEY_FALLBACKS` in environment:
   ```
   SECRET_KEY=<new-key>
   SECRET_KEY_FALLBACKS=<old-key>
   ```

3. Deploy with both keys active (zero-downtime)

4. Wait 7 days for all sessions to expire

5. Remove old key from `SECRET_KEY_FALLBACKS`

### Database Password Rotation

**Recommended Frequency:** Every 180 days

**Procedure:**
1. Create new database user with strong password
2. Grant same permissions as current user
3. Update `DATABASE_URL` in container app secrets
4. Test connection in staging
5. Deploy to production
6. Verify application health
7. Wait 24 hours
8. Revoke old user access

---

## Security Best Practices

### 1. Use Azure Key Vault (Production)

For production deployments, integrate with Azure Key Vault:
```python
# settings.py
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

if not DEBUG:
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=VAULT_URL, credential=credential)
    SECRET_KEY = client.get_secret("django-secret-key").value
    AZURE_CLIENT_SECRET = client.get_secret("azure-client-secret").value
```

### 2. Enable Managed Identities

Use Azure Managed Identities instead of client secrets when possible:
- Container Apps can authenticate to Azure services without secrets
- Reduces secret sprawl and rotation burden

### 3. Secret Scanning

Run regular secret scanning on your repository:
```bash
# Install TruffleHog
pip install truffleHog

# Scan repository history
trufflehog --regex --entropy=True file:///.
```

### 4. Audit Credential Access

- Enable Azure AD audit logging
- Monitor access to Key Vault secrets
- Set up alerts for secret access anomalies
- Review logs quarterly

### 5. Secret Expiration

Configure automatic expiration for all secrets:
- Azure AD Client Secrets: 90 days max
- Database passwords: 180 days max
- API keys: 90 days max

Set up alerts 30 days before expiration.

---

## Git History Cleanup

If credentials were accidentally committed to git:

### 1. Immediate Actions
- Rotate compromised credentials immediately
- Revoke exposed secrets in Azure Portal
- Generate new secrets

### 2. Remove from Git History

**Using BFG Repo-Cleaner (Recommended):**
```bash
# Install BFG
brew install bfg  # Mac
# or download from https://rtyley.github.io/bfg-repo-cleaner/

# Remove specific string
bfg --replace-text passwords.txt  # Create file with secrets to remove

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (coordinate with team!)
git push --force
```

**Manual Method:**
```bash
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch <file-with-secret>" \
  --prune-empty --tag-name-filter cat -- --all
```

### 3. Verify Cleanup

```bash
# Search for removed secrets
git log --all --full-history -- '*secret*'
git grep -i "your-secret-pattern"
```

---

## Incident Response

### If Credentials Are Exposed

**IMMEDIATE ACTIONS (within 1 hour):**

1. **Rotate ALL exposed credentials immediately**
   - Azure AD Client Secrets
   - Django SECRET_KEY
   - Database passwords
   - Any other exposed secrets

2. **Revoke access for compromised credentials**
   - Azure Portal → Azure AD → App Registrations → Delete old secrets
   - Database → Revoke user permissions

3. **Review Azure AD Audit Logs**
   - Check for unauthorized access attempts
   - Look for suspicious activity patterns
   - Document timeline of exposure

4. **Assess Impact**
   - What data could be accessed?
   - Were any systems compromised?
   - Do we need to notify users?

5. **Secure the Environment**
   - Remove credentials from git history
   - Update `.gitignore` if needed
   - Run security scan on repository

6. **Monitor for Abuse**
   - Set up enhanced monitoring for 30 days
   - Watch for unusual access patterns
   - Review authentication logs daily

**FOLLOW-UP ACTIONS (within 7 days):**

1. Root cause analysis
2. Update security procedures
3. Team training on credential management
4. Implement additional controls (Azure Key Vault, etc.)
5. Document incident and lessons learned

---

## Compliance Checklist

Before production deployment:

- [ ] All credentials in environment variables (not hardcoded)
- [ ] `.env` file in `.gitignore`
- [ ] No secrets in git history
- [ ] Azure AD secrets rotated within 90 days
- [ ] SECRET_KEY is 50+ characters
- [ ] Database passwords are strong (16+ chars, mixed)
- [ ] Secret rotation procedures documented
- [ ] Incident response plan reviewed
- [ ] Team trained on credential management
- [ ] Azure Key Vault configured (production)
- [ ] Managed Identities enabled where possible
- [ ] Secret scanning configured in CI/CD
- [ ] Monitoring and alerts configured
- [ ] Audit logging enabled
- [ ] Backup credentials stored securely

---

## Tools and Resources

### Secret Management Tools
- **Azure Key Vault** - Secure secret storage for production
- **1Password Teams** - Team password manager
- **HashiCorp Vault** - Alternative secret management

### Security Scanning Tools
- **TruffleHog** - Secret scanning in git history
- **git-secrets** - Prevent secrets from being committed
- **GitGuardian** - Automated secret detection
- **GitHub Secret Scanning** - Built-in for public repos

### Credential Generation
```python
# Generate secure SECRET_KEY
import secrets
print(secrets.token_urlsafe(50))

# Generate strong password
import secrets
import string
alphabet = string.ascii_letters + string.digits + string.punctuation
password = ''.join(secrets.choice(alphabet) for i in range(20))
print(password)
```

---

## Contact and Support

**Security Issues:**
- Report to: security@yourcompany.com
- Azure Support: https://portal.azure.com → Support
- Emergency Hotline: [Your emergency contact]

**Documentation:**
- [Azure AD Best Practices](https://learn.microsoft.com/en-us/azure/active-directory/develop/)
- [Django Security](https://docs.djangoproject.com/en/4.2/topics/security/)
- [OWASP Credential Management](https://cheatsheetseries.owasp.org/cheatsheets/Credential_Storage_Cheat_Sheet.html)

---

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-05 | 1.0 | Initial credential management guide | Security Team |

---

**Next Review:** 2026-02-05
