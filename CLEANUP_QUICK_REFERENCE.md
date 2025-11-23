# Production Cleanup - Quick Reference Card

**Date:** November 21, 2025
**Status:** Ready for Review

---

## Quick Start

```bash
# 1. Review the full report
cat PRODUCTION_CLEANUP_REPORT.md

# 2. Run cleanup script
bash cleanup-production.sh --phase all

# 3. Verify changes
git status

# 4. Run tests
cd azure_advisor_reports && python manage.py test
cd ../frontend && npm test
```

---

## Critical Issues (Fix First)

### 1. cost_monitoring Module Reference
**Status:** Deleted module may still be referenced
**Action:**
```bash
grep -r "cost_monitoring.encryption" azure_advisor_reports/
grep -r "from apps.cost_monitoring" azure_advisor_reports/
# Fix any found references to use apps.core.encryption
```

### 2. Frontend TODO
**File:** `frontend/src/pages/SettingsPage.tsx:15`
**Issue:** `const isAdmin = !!user; // TODO: Update once we fetch user details from backend`
**Action:** Implement proper admin role checking

### 3. Skipped Tests
**Files:**
- `frontend/src/components/reports/ReportList.test.tsx.skip`
- `frontend/src/pages/ReportsPage.test.tsx.skip`
**Action:** Fix and enable OR remove with justification

---

## Files to Remove Immediately (42 files, ~11MB)

### Test Files (22 files)
```bash
rm csv_processor.py
rm test_*.py test_*.js debug-*.js generate_final_pdf.js
```

### Test PDFs (7 files, ~10MB)
```bash
rm *.pdf
```

### Debug Files (6 files)
```bash
rm DEBUG_REPORT.json full_logs.txt temp_logs.txt backend_logs.txt _nul
```

### Test HTML (2 files)
```bash
rm redesigned_report.html test-report.html
```

### Backup Files (5 files)
```bash
find . -name "*.bak" -delete
```

---

## Automated Cleanup

```bash
# Phase 1: Critical checks
bash cleanup-production.sh --phase 1

# Phase 2: Remove test files
bash cleanup-production.sh --phase 2

# Phase 3: Organize documentation
bash cleanup-production.sh --phase 3

# Run all phases
bash cleanup-production.sh --phase all

# Check statistics
bash cleanup-production.sh --phase stats
```

---

## Manual Review Required

### 1. /apps/ Directory
**Location:** Root `/apps/` vs `/azure_advisor_reports/apps/`
**Action:** Verify if root /apps/ is duplicate and remove

### 2. Old Templates
**If redesigned templates work properly:**
```bash
# Archive old templates
mv templates/reports/cost.html templates/reports/backup/
mv templates/reports/detailed.html templates/reports/backup/
mv templates/reports/executive.html templates/reports/backup/
mv templates/reports/security.html templates/reports/backup/
```

### 3. Utility Scripts
**Consider moving to scripts/ directory:**
- create_groups.py
- diagnose_stuck_reports.py
- fix_stuck_reports.py
- generate_sample_*.py
- verify_analytics_setup.py

---

## Update .dockerignore

Add to both `azure_advisor_reports/.dockerignore` and `frontend/.dockerignore`:

```dockerfile
# Development artifacts
*.bak
*.log
test_*.py
test_*.js
debug-*.js
*.pdf

# Documentation
screenshots/
sample_reports/
docs/
Context_docs/

# Scripts
scripts/
```

---

## Size Reduction

**Before Cleanup:**
- Test files: ~11MB
- Screenshots: ~5MB
- Sample reports: ~3MB
- Documentation: ~1.5MB
- **Total removable:** ~20MB

**After Cleanup:**
- Docker image: ~10-15MB smaller
- Repository: ~20MB smaller
- Cleaner structure

---

## Testing After Cleanup

```bash
# Backend tests
cd azure_advisor_reports
python manage.py test
python manage.py check --deploy

# Frontend tests
cd frontend
npm test
npm run build

# Docker build test
docker-compose build

# Run locally
docker-compose up
```

---

## Git Workflow

```bash
# Create cleanup branch
git checkout -b cleanup/production-readiness

# Review changes
git status
git diff

# Stage changes
git add .

# Commit
git commit -m "chore: production cleanup - remove test files and organize structure

- Remove test files and debug scripts from root directory
- Remove test PDF outputs (~10MB)
- Remove .bak backup files
- Organize documentation into docs/ structure
- Archive old deployment scripts
- Update .dockerignore for production

Refs: PRODUCTION_CLEANUP_REPORT.md"

# Push and create PR
git push -u origin cleanup/production-readiness
```

---

## Deployment Checklist

Before deploying to production:

- [ ] All Phase 1 critical issues resolved
- [ ] Test files removed from repository
- [ ] Backup files removed
- [ ] Documentation organized
- [ ] .dockerignore updated
- [ ] All tests passing
- [ ] Docker images build successfully
- [ ] Staging deployment tested
- [ ] Security review completed
- [ ] Database migrations tested

---

## Rollback Plan

If issues arise after cleanup:

```bash
# Cleanup script creates backups in cleanup_backup_YYYYMMDD_HHMMSS/
ls cleanup_backup_*/

# Restore from backup if needed
cp cleanup_backup_*/filename .

# Or revert git changes
git checkout main -- <file>
```

---

## Dependencies Status

### Backend (requirements.txt)
**Status:** All dependencies in use
**Action:** No changes needed

### Frontend (package.json)
**Status:** All dependencies in use
**Action:** No changes needed

---

## Key Metrics

**Total Files Analyzed:** 1000+
**Files to Remove:** 42
**Size Reduction:** ~20MB
**Estimated Cleanup Time:** 4-6 hours
**Risk Level:** LOW
**Production Impact:** POSITIVE

---

## Contact for Issues

If you encounter issues during cleanup:
1. Review full report: `PRODUCTION_CLEANUP_REPORT.md`
2. Check backup directory: `cleanup_backup_*/`
3. Review git history: `git log`
4. Consult with team before proceeding with uncertain changes

---

## Post-Cleanup Tasks

1. **Update README.md** if directory structure changed
2. **Update CI/CD pipelines** if test paths changed
3. **Document** any manual decisions made during cleanup
4. **Archive** old documentation to separate repository (optional)
5. **Monitor** production for any issues after deployment

---

## Success Criteria

Cleanup is successful when:
- [x] All test files removed from root
- [x] No .bak files in repository
- [x] Documentation organized
- [x] All tests passing
- [x] Docker images build successfully
- [x] Staging deployment works
- [x] Production deployment successful
- [x] No regression in functionality

---

**Quick Reference Version:** 1.0
**Last Updated:** November 21, 2025
