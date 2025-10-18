# Security Checklist - Azure Advisor Reports Platform

**Document Version:** 1.0
**Last Updated:** October 4, 2025
**Status:** Production Security Hardening Guide

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Deployment Security](#pre-deployment-security)
3. [Django Application Security](#django-application-security)
4. [Infrastructure Security](#infrastructure-security)
5. [Azure Services Security](#azure-services-security)
6. [Network Security](#network-security)
7. [Authentication & Authorization](#authentication--authorization)
8. [Data Protection](#data-protection)
9. [Monitoring & Logging](#monitoring--logging)
10. [Incident Response](#incident-response)
11. [Compliance & Auditing](#compliance--auditing)

---

## Overview

This security checklist ensures the Azure Advisor Reports Platform meets enterprise-grade security standards. All items must be reviewed and implemented before production deployment.

**Security Severity Levels:**
- 🔴 **CRITICAL** - Must be addressed immediately, deployment blocker
- 🟠 **HIGH** - Should be addressed before deployment
- 🟡 **MEDIUM** - Should be addressed soon after deployment
- 🟢 **LOW** - Nice to have, can be addressed in future iterations

---

## Pre-Deployment Security

### Secret Management 🔴 CRITICAL

- [ ] **Generate Strong SECRET_KEY**
  ```powershell
  # Generate using Django
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
  - Minimum 50 characters
  - Contains uppercase, lowercase, numbers, special characters
  - Never commit to Git
  - Store in Azure Key Vault (recommended) or environment variables

- [ ] **Review All Environment Variables**
  - No hardcoded credentials in code
  - All sensitive values in `.env.production`
  - `.env.production` in `.gitignore`
  - Environment variables set in Azure App Service Configuration

- [ ] **Verify .gitignore**
  - `.env` and `.env.production` excluded
  - `*.pem`, `*.key` excluded
  - Database dumps excluded
  - Compiled Python files excluded

### Configuration Review 🔴 CRITICAL

- [ ] **Django Settings Verification**
  ```powershell
  # Run Django's production deployment check
  python manage.py check --deploy --settings=azure_advisor_reports.settings.production
  ```
  - Fix all warnings and errors
  - Review output carefully

- [ ] **DEBUG Mode**
  - `DEBUG = False` in production.py ✅
  - Verified in Azure App Service settings
  - No debug output in production logs

- [ ] **ALLOWED_HOSTS Configuration**
  - Production domain(s) listed
  - No wildcard (`*`) in production
  - Example: `['your-app.azurewebsites.net', 'www.yourdomain.com']`

---

## Django Application Security

### HTTP Security Headers 🔴 CRITICAL

- [ ] **HTTPS Enforcement**
  ```python
  SECURE_SSL_REDIRECT = True  # ✅ Already configured in production.py
  SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
  ```

- [ ] **HSTS (HTTP Strict Transport Security)**
  ```python
  SECURE_HSTS_SECONDS = 31536000  # 1 year ✅
  SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # ✅
  SECURE_HSTS_PRELOAD = True  # ✅
  ```
  - Submit domain to HSTS preload list: https://hstspreload.org/

- [ ] **XSS Protection**
  ```python
  SECURE_BROWSER_XSS_FILTER = True  # ✅
  ```

- [ ] **Content Type Sniffing**
  ```python
  SECURE_CONTENT_TYPE_NOSNIFF = True  # ✅
  ```

- [ ] **Clickjacking Protection**
  ```python
  X_FRAME_OPTIONS = 'DENY'  # ✅
  ```

### Cookie Security 🔴 CRITICAL

- [ ] **Session Cookie Security**
  ```python
  SESSION_COOKIE_SECURE = True  # ✅ HTTPS only
  SESSION_COOKIE_HTTPONLY = True  # ✅ No JavaScript access
  SESSION_COOKIE_SAMESITE = 'Lax'  # ✅ CSRF protection
  SESSION_COOKIE_AGE = 86400  # 24 hours
  ```

- [ ] **CSRF Cookie Security**
  ```python
  CSRF_COOKIE_SECURE = True  # ✅ HTTPS only
  CSRF_COOKIE_HTTPONLY = True  # ✅
  CSRF_COOKIE_SAMESITE = 'Lax'  # ✅
  ```

- [ ] **CSRF Trusted Origins**
  - All frontend domains listed in `CSRF_TRUSTED_ORIGINS`
  - Example: `['https://your-frontend.azurewebsites.net']`

### CORS Configuration 🟠 HIGH

- [ ] **CORS Allowed Origins**
  - Only specific frontend domains allowed
  - NO wildcard (`*`) in production
  - Example: `['https://your-frontend.azurewebsites.net']`

- [ ] **CORS Credentials**
  ```python
  CORS_ALLOW_CREDENTIALS = True  # Required for auth cookies
  ```

- [ ] **CORS Methods**
  - Only necessary HTTP methods allowed
  - DELETE, GET, OPTIONS, PATCH, POST, PUT

### SQL Injection Protection 🟢 LOW

- [ ] **ORM Usage Verification**
  - All database queries use Django ORM ✅
  - No raw SQL queries without parameterization
  - Review all `.raw()` and `.execute()` calls

- [ ] **Parameterized Queries**
  - If raw SQL is necessary, use parameterized queries
  ```python
  # Good
  cursor.execute("SELECT * FROM table WHERE id = %s", [user_id])

  # Bad - SQL Injection vulnerability
  cursor.execute(f"SELECT * FROM table WHERE id = {user_id}")
  ```

### Input Validation 🟠 HIGH

- [ ] **File Upload Validation**
  - File size limits enforced (50MB max for CSV) ✅
  - File type validation (only CSV allowed) ✅
  - File content scanning (implement virus scanning)
  - Filename sanitization ✅

- [ ] **Serializer Validation**
  - All DRF serializers have proper validation
  - Required fields enforced
  - Field-level validation for email, phone, URLs
  - Custom validators for business logic

- [ ] **User Input Sanitization**
  - No user input directly rendered in templates
  - Django template auto-escaping enabled ✅
  - `mark_safe()` used sparingly and carefully

### Password Security 🔴 CRITICAL

- [ ] **Password Hashing**
  - Strong password hashers configured (Argon2 recommended)
  ```python
  PASSWORD_HASHERS = [
      'django.contrib.auth.hashers.Argon2PasswordHasher',
      'django.contrib.auth.hashers.PBKDF2PasswordHasher',
  ]
  ```

- [ ] **Password Validation**
  - All validators enabled ✅
  - Minimum length enforced (8+ characters)
  - Common passwords blocked
  - User attribute similarity checked

### Rate Limiting 🟠 HIGH

- [ ] **API Rate Limiting**
  ```python
  'anon': '100/hour',  # ✅ Configured
  'user': '1000/hour',  # ✅
  'report_generation': '10/hour',  # ✅ Prevents abuse
  'csv_upload': '20/hour',  # ✅
  ```

- [ ] **Login Rate Limiting**
  - Implement rate limiting on login endpoint
  - Block after 5 failed attempts
  - Use django-ratelimit or DRF throttling

---

## Infrastructure Security

### Docker Security 🟠 HIGH

- [ ] **Non-Root User**
  - Container runs as non-root user ✅ (appuser, UID 1000)
  - Verified in Dockerfile.prod

- [ ] **Minimal Base Image**
  - Using python:3.11-slim ✅
  - No unnecessary packages installed

- [ ] **Multi-Stage Build**
  - Build dependencies separated from runtime ✅
  - Smaller attack surface

- [ ] **Vulnerability Scanning**
  - Scan Docker images with Trivy or Aqua Security
  ```powershell
  docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image azure-advisor-backend:prod
  ```

- [ ] **Container Hardening**
  - Read-only root filesystem (if possible)
  - Drop unnecessary capabilities
  - Resource limits set (CPU, memory)

### Environment Variables 🔴 CRITICAL

- [ ] **Azure App Service Configuration**
  - All secrets in App Service → Configuration → Application settings
  - NOT in source code or Docker image
  - Connection strings marked as "Connection strings" (not App settings)

- [ ] **Azure Key Vault Integration (Optional but Recommended)**
  - Store secrets in Key Vault
  - Grant App Service managed identity access
  - Reference secrets with @Microsoft.KeyVault(SecretUri=...)

---

## Azure Services Security

### Azure PostgreSQL 🔴 CRITICAL

- [ ] **SSL/TLS Enforcement**
  - SSL mode set to `require` ✅ (configured in production.py)
  - Minimum TLS version: 1.2

- [ ] **Firewall Rules**
  - Only allow Azure services (if backend in Azure)
  - Or whitelist specific IPs (App Service outbound IPs)
  - No `0.0.0.0/0` rule (allow all)

- [ ] **Authentication**
  - Strong password for database user (20+ characters)
  - Consider Azure AD authentication (more secure)
  - Rotate password regularly (every 90 days)

- [ ] **Network Security**
  - Private endpoint (if using VNet)
  - Or service endpoint for better security

- [ ] **Backup & Retention**
  - Automated backups enabled
  - 14-day retention minimum
  - Geo-redundant backups (for disaster recovery)

### Azure Cache for Redis 🔴 CRITICAL

- [ ] **SSL/TLS Only**
  - Non-SSL port disabled
  - SSL port 6380 used ✅ (rediss:// in configuration)

- [ ] **Authentication**
  - Access keys rotated regularly
  - Consider regenerating keys every 90 days

- [ ] **Firewall Rules**
  - Only allow Azure services or specific IPs
  - No public access if not needed

- [ ] **Data Persistence**
  - RDB persistence enabled (for cache recovery)
  - AOF persistence optional (higher durability)

### Azure Blob Storage 🟠 HIGH

- [ ] **Access Control**
  - Private containers for sensitive data (CSV uploads, reports)
  - Public container only for static files (if needed)
  - SAS tokens with expiration for temporary access

- [ ] **Encryption**
  - Encryption at rest enabled (default in Azure) ✅
  - HTTPS required for transfers ✅ (`AZURE_SSL = True`)

- [ ] **Network Security**
  - Firewall rules or service endpoints
  - Disable public blob access if not needed

- [ ] **Versioning & Soft Delete**
  - Blob versioning enabled (recover from accidental deletion)
  - Soft delete enabled (7-30 days retention)

### Azure Active Directory 🔴 CRITICAL

- [ ] **App Registration Security**
  - Client secret stored securely (Key Vault or App Service settings)
  - Client secret expiration set (24 months maximum)
  - Set reminder to rotate before expiration

- [ ] **API Permissions**
  - Only necessary permissions granted (User.Read)
  - Admin consent granted if required

- [ ] **Redirect URIs**
  - Only production domains listed
  - No localhost or development URIs

- [ ] **Token Configuration**
  - Token lifetime appropriate (default: 1 hour)
  - Refresh tokens used for extended sessions

### Application Insights 🟡 MEDIUM

- [ ] **Data Collection**
  - Personally Identifiable Information (PII) not logged
  - Sensitive data masked in logs
  - Review telemetry data for compliance

- [ ] **Access Control**
  - Role-based access to Application Insights
  - Only authorized personnel can view logs

- [ ] **Data Retention**
  - Configure appropriate retention (90 days default)
  - Archive older data if needed for compliance

---

## Network Security

### Azure Front Door / CDN 🟠 HIGH

- [ ] **WAF (Web Application Firewall)**
  - WAF enabled on Front Door
  - OWASP Core Rule Set 3.2 configured ✅ (in networking.bicep)
  - Custom rules for specific threats

- [ ] **Rate Limiting**
  - Rate limit rules configured
  - DDoS protection enabled (L7)

- [ ] **SSL/TLS**
  - TLS 1.2 minimum
  - Strong cipher suites only
  - HSTS header configured

- [ ] **Custom Domains**
  - Valid SSL certificate (Let's Encrypt or purchased)
  - Certificate auto-renewal configured

### Network Isolation 🟡 MEDIUM

- [ ] **Virtual Network (Optional)**
  - Deploy App Service in VNet for isolation
  - Use private endpoints for Azure services

- [ ] **Network Security Groups**
  - Restrict inbound/outbound traffic
  - Only necessary ports open

- [ ] **Service Endpoints**
  - Enable for PostgreSQL, Redis, Storage
  - Restrict access to Azure services only

---

## Authentication & Authorization

### Azure AD Integration 🔴 CRITICAL

- [ ] **Token Validation**
  - JWT tokens validated on every request ✅
  - Token signature verified against Azure AD
  - Token expiration checked

- [ ] **User Authentication**
  - Only authenticated users can access API ✅
  - Public endpoints explicitly marked (e.g., /health/)

- [ ] **MFA (Multi-Factor Authentication)**
  - Enforce MFA in Azure AD for all users
  - Conditional access policies configured

### Role-Based Access Control (RBAC) 🟠 HIGH

- [ ] **Role Implementation**
  - User roles implemented (Admin, Manager, Analyst, Viewer) ✅
  - Permissions enforced at API level ✅

- [ ] **Permission Checks**
  - Every sensitive action checks permissions
  - Delete operations restricted to Admin
  - Report generation restricted to Analyst+ roles

- [ ] **Audit Logging**
  - Log all authentication attempts
  - Log authorization failures
  - Log role changes

---

## Data Protection

### Data Encryption 🔴 CRITICAL

- [ ] **Encryption at Rest**
  - Database encryption enabled (Azure PostgreSQL default)
  - Blob storage encryption enabled (Azure default)
  - Redis encryption enabled

- [ ] **Encryption in Transit**
  - HTTPS enforced everywhere ✅
  - TLS 1.2 minimum
  - Database connections use SSL ✅
  - Redis connections use SSL ✅

- [ ] **Sensitive Data Handling**
  - No sensitive data in logs
  - No sensitive data in error messages
  - Client data isolated per tenant (if multi-tenant)

### Data Backup 🔴 CRITICAL

- [ ] **Database Backups**
  - Automated daily backups enabled
  - 14-day retention minimum
  - Test restore procedure quarterly

- [ ] **Blob Storage Backups**
  - Versioning enabled
  - Soft delete enabled (7+ days)
  - Critical data replicated to geo-redundant storage

- [ ] **Backup Security**
  - Backups encrypted
  - Access to backups restricted
  - Backup integrity verified regularly

### Data Retention & Deletion 🟡 MEDIUM

- [ ] **Retention Policies**
  - Define retention period for reports (e.g., 90 days)
  - Define retention for logs (e.g., 30 days)
  - Comply with GDPR/data protection laws

- [ ] **Secure Deletion**
  - Soft delete implemented for critical data
  - Hard delete with confirmation for permanent removal
  - Cascade deletes configured properly

---

## Monitoring & Logging

### Application Logging 🟠 HIGH

- [ ] **Logging Configuration**
  - All errors logged to Application Insights ✅
  - Warning-level events logged
  - Audit events logged (login, logout, sensitive operations)

- [ ] **Log Levels**
  - Production: INFO or WARNING minimum
  - No DEBUG logs in production
  - Sensitive data not logged (passwords, tokens, PII)

- [ ] **Structured Logging**
  - JSON formatted logs for better querying
  - Include request IDs for tracing
  - Include user IDs for auditing

### Security Monitoring 🟠 HIGH

- [ ] **Failed Login Attempts**
  - Monitor and alert on > 5 failed attempts from same IP
  - Block IPs after 10 failed attempts (1 hour)

- [ ] **Unusual Activity**
  - Monitor for unusual API call patterns
  - Alert on bulk data downloads
  - Alert on permission escalation attempts

- [ ] **Error Monitoring**
  - Alert on 5xx errors > 5% of requests
  - Alert on 4xx errors > 20% of requests
  - Alert on database connection failures

### Alerting 🟠 HIGH

- [ ] **Critical Alerts**
  - Database down → Page on-call team
  - Redis down → Page on-call team
  - Authentication service down → Page immediately

- [ ] **Warning Alerts**
  - CPU > 80% for 10 minutes → Email team
  - Memory > 80% for 10 minutes → Email team
  - Disk space < 20% → Email team

- [ ] **Notification Channels**
  - Email configured for alerts
  - SMS/Phone for critical alerts (optional)
  - Slack/Teams integration (optional)

---

## Incident Response

### Incident Response Plan 🟠 HIGH

- [ ] **Security Incident Procedures**
  - Document steps for handling security incidents
  - Define escalation paths
  - Contact information for security team

- [ ] **Breach Notification**
  - Procedures for notifying affected users
  - Compliance with GDPR (72-hour notification)
  - Communication templates prepared

- [ ] **Rollback Procedures**
  - Documented rollback steps
  - Tested rollback in staging
  - Rollback can be executed in < 10 minutes

### Emergency Contacts 🔴 CRITICAL

- [ ] **On-Call Rotation**
  - 24/7 on-call engineer assigned
  - Backup on-call engineer assigned
  - Contact information up-to-date

- [ ] **Escalation Paths**
  - Level 1: On-call engineer
  - Level 2: Senior engineer/Tech lead
  - Level 3: CTO/VP Engineering

---

## Compliance & Auditing

### GDPR Compliance (if applicable) 🟡 MEDIUM

- [ ] **User Data Rights**
  - Right to access (API endpoint for user data export)
  - Right to deletion (hard delete user data)
  - Right to portability (export in JSON format)

- [ ] **Privacy Policy**
  - Privacy policy published and accessible
  - Users consent to data collection
  - Cookie consent implemented

- [ ] **Data Processing Agreement**
  - DPA with Azure (automatically covered)
  - DPA with third-party services (if any)

### Security Audits 🟡 MEDIUM

- [ ] **Penetration Testing**
  - Schedule annual penetration test
  - Fix high/critical findings before deployment
  - Retest after fixes

- [ ] **Vulnerability Scanning**
  - Run OWASP ZAP or similar scanner
  - Scan dependencies for vulnerabilities
  ```powershell
  # Python dependencies
  safety check

  # Node.js dependencies
  npm audit
  ```

- [ ] **Code Security Review**
  - Security review of authentication code
  - Security review of file upload code
  - Security review of database queries

### Compliance Certifications (if needed) 🟢 LOW

- [ ] **SOC 2 Type II**
  - Audit controls if required by customers
  - Azure SOC 2 compliance inherited

- [ ] **ISO 27001**
  - Information security management system
  - Azure ISO 27001 compliance inherited

- [ ] **HIPAA (if handling healthcare data)**
  - Sign Azure BAA (Business Associate Agreement)
  - Implement additional controls

---

## Production Readiness Checklist

### Final Pre-Deployment Checks 🔴 CRITICAL

- [ ] **Run Django deployment check**
  ```powershell
  python manage.py check --deploy --settings=azure_advisor_reports.settings.production
  ```
  - All warnings resolved
  - All errors fixed

- [ ] **Dependency Security Scan**
  ```powershell
  safety check --full-report
  npm audit
  ```
  - No critical vulnerabilities
  - High vulnerabilities addressed

- [ ] **Container Security Scan**
  ```powershell
  trivy image azure-advisor-backend:prod
  ```
  - No critical vulnerabilities in base image

- [ ] **SSL Certificate Validation**
  - Certificate installed and valid
  - Certificate expiration > 30 days
  - Auto-renewal configured

- [ ] **Security Testing**
  - OWASP ZAP scan completed
  - SQL injection tests passed
  - XSS tests passed
  - CSRF tests passed

- [ ] **Access Control Verification**
  - Test unauthenticated access blocked
  - Test role-based permissions working
  - Test admin-only endpoints restricted

---

## Security Maintenance

### Regular Security Tasks

**Weekly:**
- [ ] Review Application Insights for anomalies
- [ ] Check for failed login attempts
- [ ] Review error logs

**Monthly:**
- [ ] Update dependencies (security patches)
- [ ] Review access logs
- [ ] Verify backup integrity

**Quarterly:**
- [ ] Rotate database passwords
- [ ] Rotate Azure AD client secrets
- [ ] Rotate Redis access keys
- [ ] Review and update firewall rules
- [ ] Test disaster recovery procedures

**Annually:**
- [ ] Penetration testing
- [ ] Security audit
- [ ] GDPR compliance review
- [ ] Update privacy policy

---

## References

- **Django Security Docs:** https://docs.djangoproject.com/en/4.2/topics/security/
- **OWASP Top 10:** https://owasp.org/www-project-top-ten/
- **Azure Security Best Practices:** https://docs.microsoft.com/azure/security/
- **NIST Cybersecurity Framework:** https://www.nist.gov/cyberframework

---

## Sign-Off

Before deploying to production, this checklist must be reviewed and signed off by:

- [ ] **Backend Developer:** _______________ Date: ___________
- [ ] **Security Engineer:** _______________ Date: ___________
- [ ] **DevOps Engineer:** _______________ Date: ___________
- [ ] **Technical Lead:** _______________ Date: ___________
- [ ] **CTO/VP Engineering:** _______________ Date: ___________

---

**End of Security Checklist**

*Keep this document updated as new security measures are implemented or threats are identified.*
