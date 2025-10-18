# Azure Advisor Reports Platform - Frequently Asked Questions (FAQ)

**Version:** 1.0
**Last Updated:** October 4, 2025
**Audience:** All Users

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Account and Authentication](#account-and-authentication)
3. [CSV Upload and Processing](#csv-upload-and-processing)
4. [Report Generation](#report-generation)
5. [Technical Issues](#technical-issues)
6. [Features and Functionality](#features-and-functionality)
7. [Billing and Pricing](#billing-and-pricing)
8. [Security and Privacy](#security-and-privacy)

---

## Getting Started

### Q1: What is the Azure Advisor Reports Platform?

**A:** The Azure Advisor Reports Platform is a professional tool that automates the generation of Azure Advisor reports. It transforms raw CSV exports from Azure Advisor into polished, professional reports in minutes, saving you up to 90% of the time compared to manual report creation.

**Key features:**
- Upload Azure Advisor CSV files
- Generate 5 specialized report types (Detailed, Executive, Cost, Security, Operations)
- Download reports as HTML or PDF
- Track analytics and trends across clients
- Professional formatting with consistent branding

---

### Q2: Who should use this platform?

**A:** The platform is designed for:

- **Cloud Engineers** - Generate technical reports for infrastructure reviews
- **IT Consultants** - Create professional client deliverables
- **Service Delivery Managers** - Track optimization progress across multiple clients
- **MSPs (Managed Service Providers)** - Automate monthly reporting for clients
- **Cloud Analysts** - Analyze trends and patterns in Azure recommendations
- **DevOps Teams** - Document operational improvements and best practices

If you regularly work with Azure Advisor recommendations and need to present them professionally, this platform is for you.

---

### Q3: What browsers are supported?

**A:** Supported browsers:
- ✅ Google Chrome 90+ (recommended)
- ✅ Microsoft Edge 90+
- ✅ Mozilla Firefox 88+
- ✅ Safari 14+

**Not supported:**
- ❌ Internet Explorer (any version)
- ❌ Browsers with JavaScript disabled
- ❌ Very old browser versions (5+ years)

**Recommendation:** Use the latest version of Chrome or Edge for the best experience.

---

### Q4: Do I need an Azure subscription to use this platform?

**A:** **Yes**, but only for authentication. Here's what you need:

**Required:**
- Azure Active Directory (Azure AD) account (work or school account)
- Access to Azure Advisor in your organization's Azure subscription

**Not required:**
- You don't need admin access to Azure
- You don't need to create Azure resources yourself
- You don't need a separate platform subscription (check with your admin)

The platform uses Azure AD for secure authentication, ensuring only authorized users from your organization can access it.

---

### Q5: How long does it take to generate a report?

**A:** Report generation time depends on file size and report type:

| File Size | Recommendations | Typical Time |
|-----------|----------------|--------------|
| Small (< 1 MB) | < 100 | 45-90 seconds |
| Medium (1-5 MB) | 100-500 | 2-3 minutes |
| Large (5-20 MB) | 500-2000 | 3-5 minutes |
| Very Large (20-50 MB) | 2000+ | 5-10 minutes |

**Processing stages:**
1. CSV upload (10-30 seconds)
2. Data processing (15-60 seconds)
3. Report generation (30-120 seconds)
4. PDF creation (30-90 seconds)

**Tip:** You can close the browser tab during generation. You'll receive a notification when the report is ready.

---

## Account and Authentication

### Q6: How do I get access to the platform?

**A:** Access is granted by your organization's system administrator. Here's the process:

1. **Request Access:**
   - Contact your IT department or system administrator
   - Request access to the Azure Advisor Reports Platform
   - Provide your work email address

2. **Wait for Account Creation:**
   - Admin will create your user account
   - You'll receive an email with login instructions

3. **First Login:**
   - Navigate to the platform URL (provided by admin)
   - Click "Sign in with Microsoft"
   - Use your Azure AD credentials (work/school account)
   - Approve permission request (first login only)

4. **Start Using:**
   - You'll be redirected to the dashboard
   - Begin uploading CSVs and generating reports

**Note:** You must have an Azure Active Directory account in your organization. Personal Microsoft accounts (outlook.com, hotmail.com) are not supported.

---

### Q7: I get "Permission denied" when logging in. What should I do?

**A:** This error means your account exists but doesn't have proper permissions. Here's how to resolve it:

**Common Causes:**
1. **Account not activated**: Contact your admin to activate your account
2. **Wrong user role**: Your role may not have sufficient permissions
3. **Account deactivated**: Previous access may have been revoked

**Solutions:**
- Contact your system administrator
- Verify your email address is correct
- Check if you're using the right Azure AD tenant (work account)
- Ask admin to verify your role assignment (should be at least "Viewer")

**Expected Roles:**
- **Viewer**: Read-only access
- **Analyst**: Can create reports
- **Manager**: Can manage users and delete reports
- **Admin**: Full system access

---

### Q8: How often do I need to log in? Does my session expire?

**A:** The platform uses Azure AD authentication with session management:

**Session Duration:**
- **Active usage**: Stays logged in indefinitely
- **Inactivity**: Auto-logout after 1 hour of no activity
- **Browser close**: Session persists (stored in sessionStorage)
- **Azure AD token**: Refreshes automatically every hour

**Best Practices:**
- Always log out when leaving your workstation (security)
- Don't stay logged in on shared computers
- Close browser tabs when finished
- Use "Remember Me" only on personal devices

**Troubleshooting:**
- If logged out unexpectedly, simply sign in again
- Clear browser cache if experiencing login loops
- Check Azure AD status if authentication fails

---

### Q9: Can I use a personal Microsoft account to log in?

**A:** **No**, personal Microsoft accounts are not supported. Here's why:

**What won't work:**
- ❌ Personal accounts (outlook.com, hotmail.com, live.com)
- ❌ Xbox accounts
- ❌ Microsoft 365 Personal subscriptions
- ❌ Consumer Microsoft accounts

**What will work:**
- ✅ Azure AD organizational accounts (work/school)
- ✅ Microsoft 365 business accounts
- ✅ Domain-joined accounts (yourname@yourcompany.com)

**Why this restriction?**
The platform is designed for enterprise use and requires Azure Active Directory for:
- Centralized user management
- Role-based access control
- Audit logging and compliance
- Single sign-on (SSO) integration
- Multi-factor authentication (MFA)

**Solution:**
Contact your IT department to get a work/school account with Azure AD access.

---

### Q10: What permissions does the platform request from Azure AD?

**A:** During first login, you'll see a permission consent screen requesting:

**Permissions Requested:**
1. **User.Read** - Read your basic profile
   - Purpose: Display your name and email in the UI
   - Scope: Only your own profile information

2. **openid** - Sign you in
   - Purpose: Enable authentication
   - Scope: Identity verification

3. **profile** - Access your basic profile
   - Purpose: Display your name in the header
   - Scope: First name, last name, username

4. **email** - Read your email address
   - Purpose: Contact information and notifications
   - Scope: Your work email address

**What the platform CANNOT do:**
- ❌ Read your emails
- ❌ Access other users' data
- ❌ Modify your Azure resources
- ❌ Access your OneDrive or SharePoint
- ❌ Send emails on your behalf

**Why these permissions?**
These are Microsoft Graph API permissions required for user authentication and profile display. They're standard for enterprise applications.

**Concerned about privacy?**
All permissions are read-only and limited to your basic profile. The platform does not access any Azure resources or corporate data beyond what's necessary for authentication.

---

## CSV Upload and Processing

### Q11: What Azure Advisor CSV columns are required?

**A:** The platform supports the standard Azure Advisor CSV export format. Required columns include:

**Essential Columns:**
- `Category` - Cost, Security, Reliability, Operational Excellence, Performance
- `Impact` (or `Business Impact`) - High, Medium, Low
- `Impacted Resource` (or `Resource Name`) - Name of affected resource
- `Recommendation` - The specific recommendation text
- `Description` - Detailed explanation
- `Subscription ID` - Azure subscription identifier
- `Subscription Name` - Friendly subscription name
- `Resource Type` - Type of Azure service

**Optional Columns (enhance report quality):**
- `Potential Benefits` - Expected improvements
- `Potential Annual Cost Savings` - Estimated savings (for cost reports)
- `Retirement Date` - For deprecation notifications
- `Region` - Azure region/location

**How to get the correct CSV:**
1. Azure Portal → Azure Advisor
2. Click "Recommendations"
3. Click "Download as CSV" (top toolbar)
4. Use the downloaded file as-is (don't modify in Excel)

**Note:** Azure occasionally updates the CSV format. The platform automatically adapts to these changes.

---

### Q12: My CSV file is 80 MB. Can I upload it?

**A:** **No**, the maximum file size is 50 MB. Here's how to handle large files:

**Size Limits:**
- Maximum: 50 MB per file
- Recommended: Under 20 MB for best performance
- Optimal: 5-10 MB (processes fastest)

**Solutions for Large Files:**

**Option 1: Split by Subscription**
1. In Azure Portal, filter recommendations by subscription
2. Export each subscription separately
3. Upload multiple CSV files (one per subscription)
4. Generate separate reports per subscription

**Option 2: Split by Category**
1. Filter Azure Advisor by category (Cost, Security, etc.)
2. Export each category separately
3. Upload and generate specialized reports

**Option 3: Filter by Date Range**
1. Use Azure Advisor filters to limit date range
2. Export smaller time periods
3. Generate monthly or quarterly reports

**Option 4: Remove Resolved Recommendations**
1. In Azure Advisor, filter to "Active" recommendations only
2. Exclude "Resolved" or "Dismissed" items
3. Export reduced dataset

**Why the 50 MB limit?**
- Processing time increases exponentially with size
- Server resource constraints
- Better user experience with faster processing
- Most organizations have < 2000 recommendations (well under 50 MB)

**Average File Sizes:**
- 100 recommendations ≈ 0.5 MB
- 500 recommendations ≈ 2 MB
- 1000 recommendations ≈ 5 MB
- 5000 recommendations ≈ 25 MB

---

### Q13: I modified the CSV in Excel and now uploads fail. What went wrong?

**A:** Excel often corrupts CSV files when saving. Common issues:

**Problems Caused by Excel:**
1. **Encoding changes**: Excel may save as ANSI instead of UTF-8
2. **Quote characters**: Excel adds unnecessary quotes around fields
3. **Date formatting**: Excel converts text to date format
4. **Comma separators**: Excel might use semicolons in some locales
5. **Line endings**: Windows vs. Unix line endings
6. **BOM (Byte Order Mark)**: Excel adds BOM characters

**Symptoms:**
- "Invalid CSV format" error
- "CSV validation failed"
- Missing columns
- Corrupted data

**Solutions:**

**Best Practice: Don't modify the CSV**
- Upload the original file from Azure Advisor without opening it

**If you must edit:**
1. **Save as UTF-8 CSV:**
   - Excel: File → Save As → CSV UTF-8 (Comma delimited)
   - Not "CSV (Comma delimited)" - that's ANSI!

2. **Use a text editor instead:**
   - Notepad++, VS Code, or Sublime Text
   - Make minimal changes
   - Save with UTF-8 encoding

3. **Re-export from Azure:**
   - If file is corrupted, go back to Azure Portal
   - Export fresh CSV
   - Start over without Excel

**Validation Before Upload:**
1. Open file in Notepad
2. Check first line has column headers
3. Verify commas separate fields
4. Look for strange characters (â€", �, etc.)

---

### Q14: How do I handle CSV files with 10,000+ rows?

**A:** Large datasets require special handling for optimal performance:

**Best Practices:**

**1. File Management:**
- Split into multiple files by subscription (recommended)
- Each file should have < 2000 recommendations
- Upload and process separately

**2. Upload Strategy:**
- Upload during off-peak hours (evenings/weekends)
- Ensure stable internet connection
- Don't navigate away during upload
- Wait for "Upload Complete" confirmation

**3. Processing Time:**
- 10,000 rows ≈ 8-12 minutes processing time
- System will queue your request
- You'll receive notification when complete
- Check "Recent Activity" for status updates

**4. Report Generation:**
- Generate multiple smaller reports instead of one large report
- Use report type filtering (e.g., Cost-only, Security-only)
- PDF files will be large (50-100+ pages)
- HTML format recommended for very large reports

**5. Performance Optimization:**
- Remove duplicate recommendations in Excel before upload
- Filter out "Informational" impact items
- Exclude resolved recommendations
- Focus on "High" and "Medium" impact only

**Example Strategy for 10,000 Recommendations:**

```
Subscription A (2,500 recs) → Upload 1, Generate Report 1
Subscription B (3,000 recs) → Upload 2, Generate Report 2
Subscription C (2,000 recs) → Upload 3, Generate Report 3
Subscription D (2,500 recs) → Upload 4, Generate Report 4

Result: 4 manageable reports instead of 1 massive report
```

**Benefits of Splitting:**
- Faster processing (parallel uploads)
- Easier to review and share
- More focused recommendations per client/subscription
- Reduced risk of timeout errors

---

### Q15: What happens to my CSV file after upload?

**A:** Your CSV file is processed and stored securely:

**Upload Process:**
1. **Upload** (10-30 seconds)
   - File transmitted to Azure Blob Storage
   - Encrypted in transit (HTTPS)
   - Virus scanned (security)

2. **Validation** (5-10 seconds)
   - File format verification
   - Column structure validation
   - Encoding check

3. **Processing** (15-60 seconds)
   - CSV parsed with pandas
   - Data extracted to database
   - Recommendation records created

4. **Storage** (ongoing)
   - Original CSV stored in Azure Blob Storage (private)
   - Data stored in PostgreSQL database
   - Encrypted at rest

**Retention Policy:**
- **CSV files**: Retained for 30 days, then automatically deleted
- **Extracted data**: Retained indefinitely in database
- **Generated reports**: Retained indefinitely (or per admin policy)

**Security:**
- Files are never shared or exposed publicly
- Only you and admins can access your files
- Automatic encryption (Azure Storage Service Encryption)
- Access audited and logged

**Privacy:**
- CSV files contain Azure resource names (no personal data)
- Azure subscription IDs are visible to your organization only
- No data is shared with third parties
- Compliant with data protection regulations

**Can I delete my CSV files?**
Yes, admins can manually delete CSV files from Azure Blob Storage if needed. However, reports will remain since data has been extracted to the database.

---

## Report Generation

### Q16: What's the difference between the 5 report types?

**A:** Each report type is designed for a specific audience and purpose:

**1. Detailed Report**
- **Audience**: Technical teams, engineers, DevOps
- **Length**: 20-50 pages
- **Content**: All recommendations with full technical details
- **Best for**: Implementation planning, technical reviews, sprint planning
- **Key sections**: Complete recommendation list, remediation steps, resource details

**2. Executive Summary**
- **Audience**: Leadership, C-level executives, decision-makers
- **Length**: 5-8 pages
- **Content**: High-level overview, top 10 priorities, key metrics
- **Best for**: Board meetings, business cases, stakeholder updates
- **Key sections**: Key findings, financial impact, risk assessment, strategic recommendations

**3. Cost Optimization Report**
- **Audience**: Finance teams, procurement, budget owners
- **Length**: 12-20 pages
- **Content**: Cost-focused recommendations with ROI analysis
- **Best for**: Cost reduction initiatives, budget planning, FinOps
- **Key sections**: Total savings potential, quick wins, long-term optimizations, ROI timeline

**4. Security Assessment**
- **Audience**: Security teams, compliance officers, CISOs
- **Length**: 10-18 pages
- **Content**: Security recommendations with risk levels
- **Best for**: Security audits, compliance reviews, risk assessments
- **Key sections**: Critical findings, risk matrix, remediation timelines, compliance impact

**5. Operational Excellence Report**
- **Audience**: DevOps, SRE, operations engineers
- **Length**: 15-25 pages
- **Content**: Reliability and best practices recommendations
- **Best for**: DevOps planning, SRE initiatives, reliability improvements
- **Key sections**: Availability improvements, performance optimizations, automation opportunities

**Which Should I Choose?**

| If you need to... | Use this report |
|------------------|----------------|
| Share with your CEO/CFO | Executive Summary |
| Justify cloud spend reduction | Cost Optimization |
| Pass a security audit | Security Assessment |
| Plan engineering work | Detailed Report |
| Improve uptime/reliability | Operational Excellence |

**Can I generate multiple report types from one CSV?**
Yes! Upload your CSV once, then generate as many report types as needed. Each report uses the same data but presents it differently.

---

### Q17: Can I customize the report templates or branding?

**A:** Currently, report templates use standard branding and cannot be customized by end users. However:

**What You Can Do:**
- ✅ Choose from 5 different report types
- ✅ Select which client the report is for
- ✅ Download as HTML or PDF
- ✅ Add custom cover page (manually, after download)

**What You Cannot Do:**
- ❌ Change report template layout
- ❌ Modify colors or fonts
- ❌ Add custom logo (admin feature only)
- ❌ Remove/add sections
- ❌ Change formatting

**For Administrators:**
- Admins can customize report branding globally
- Contact your system administrator for branding requests
- Custom logos and color schemes can be configured
- See ADMIN_GUIDE.md for customization instructions

**Workaround for Custom Branding:**
1. Download report as HTML
2. Open in text editor or HTML editor
3. Manually add logo, change colors, etc.
4. Save as modified HTML or convert to PDF

**Future Feature:**
Template customization is planned for a future release. Features under consideration:
- Custom cover pages
- Company logo integration
- Color theme selection
- Section visibility toggles

---

### Q18: Can I schedule automatic report generation?

**A:** **Not currently**. Report generation is manual only. However, here's how to streamline the process:

**Current Process:**
1. Export CSV from Azure Advisor (manual)
2. Upload to platform (manual)
3. Select report type (manual)
4. Download generated report (manual)

**Why No Automation?**
- Azure Advisor doesn't provide API access to export CSVs automatically
- Manual export ensures data freshness and accuracy
- Allows review of recommendations before report generation

**Recommended Workflow:**
1. **Set a recurring calendar reminder**
   - Monthly: First Monday of each month
   - Schedule 1 hour for all clients

2. **Batch process all clients**
   - Export all CSVs in one session
   - Upload all files consecutively
   - Generate all reports at once

3. **Use browser bookmarks**
   - Bookmark Azure Advisor → Recommendations
   - Bookmark platform Reports page
   - Quick access saves time

4. **Create a checklist**
   - Track which clients are done
   - Ensure consistency

**Future Roadmap:**
Automated report generation is planned for version 2.0, including:
- Scheduled CSV exports (if Azure provides API)
- Automatic report generation
- Email delivery of reports
- Webhook integrations

**Current Alternative:**
Use Power Automate (Microsoft Flow) to:
- Send reminder emails
- Coordinate with team members
- Track completion status

---

### Q19: Why is my report generation failing?

**A:** Report generation can fail for several reasons:

**Common Causes:**

**1. Corrupted CSV File (40% of failures)**
- **Symptom**: "CSV validation failed" or "Invalid format"
- **Solution**: Re-export CSV from Azure Advisor without modifications
- **Prevention**: Don't open/edit CSV in Excel

**2. Unsupported CSV Structure (25% of failures)**
- **Symptom**: "Missing required columns"
- **Solution**: Ensure CSV is from Azure Advisor (not custom export)
- **Prevention**: Use standard "Download as CSV" button

**3. Very Large File (15% of failures)**
- **Symptom**: Timeout or "Processing failed" after 5+ minutes
- **Solution**: Split file into smaller uploads (see Q14)
- **Prevention**: Keep files under 20 MB

**4. System Error (10% of failures)**
- **Symptom**: "Internal server error" or "Report generation failed"
- **Solution**: Try again in 5 minutes; contact support if persists
- **Prevention**: None (server-side issue)

**5. Insufficient Resources (5% of failures)**
- **Symptom**: Report stuck in "Processing" for 15+ minutes
- **Solution**: Wait or contact admin to check Celery workers
- **Prevention**: Generate reports during off-peak hours

**6. Data Quality Issues (5% of failures)**
- **Symptom**: Report generates but appears empty or incomplete
- **Solution**: Verify CSV has data rows (not just headers)
- **Prevention**: Check CSV has at least one recommendation

**Troubleshooting Steps:**

```
1. Check report status
   - Navigate to Reports page
   - Look for error message
   - Note exact error text

2. Verify CSV file
   - Open in Notepad (not Excel)
   - Check file size
   - Verify data rows exist

3. Try again
   - Re-upload CSV
   - Select same report type
   - Monitor progress

4. Contact support
   - If error persists after 3 attempts
   - Include error message
   - Provide report ID (if available)
```

---

### Q20: Can I regenerate a report if I don't like the first version?

**A:** **Yes**, you can regenerate reports as many times as needed:

**How to Regenerate:**

**Option 1: Upload Same CSV Again**
1. Go to Reports page
2. Upload the same CSV file
3. Select desired report type (can choose different type)
4. Generate new report
5. Both reports will be saved in history

**Option 2: Generate Different Report Type**
1. Same CSV can generate multiple report types
2. No need to re-upload
3. Just select different report type
4. Each version is saved separately

**What You Can Change:**
- ✅ Report type (Detailed → Executive, etc.)
- ✅ Client assignment (if uploaded to wrong client)
- ✅ Generate multiple versions for A/B comparison

**What You Cannot Change:**
- ❌ CSV data (must upload new CSV to change data)
- ❌ Previous reports (cannot edit already generated reports)
- ❌ Report template (consistent formatting)

**Costs:**
- No limit on report generations
- No additional cost per report
- Historical reports remain accessible

**Best Practices:**
1. **Test with small CSV first**
   - Generate sample report
   - Verify format meets expectations
   - Then process large files

2. **Generate multiple report types**
   - Create Detailed + Executive for same CSV
   - Technical team gets Detailed
   - Leadership gets Executive

3. **Keep old versions**
   - Historical comparison
   - Track recommendation trends over time
   - Archive for compliance

**Deleting Old Reports:**
- Managers and Admins can delete reports
- Viewers and Analysts cannot delete
- Delete removes from database and storage permanently

---

## Technical Issues

### Q21: The dashboard isn't updating. How do I refresh it?

**A:** The dashboard auto-refreshes, but you can force a refresh:

**Auto-Refresh Settings:**
- **Normal**: Every 30 seconds (when active)
- **Processing reports**: Every 5 seconds (when reports are generating)
- **Inactive tab**: Paused (resumes when tab becomes active)

**Manual Refresh Methods:**

**Method 1: Refresh Button**
- Look for circular arrow icon (top right of dashboard)
- Click to force immediate refresh
- Data updates within 2-3 seconds

**Method 2: Browser Refresh**
- Press `F5` on Windows/Linux
- Press `Cmd+R` on macOS
- Click browser refresh button

**Method 3: Hard Refresh (clears cache)**
- Windows/Linux: `Ctrl+F5` or `Ctrl+Shift+R`
- macOS: `Cmd+Shift+R`
- Reloads all data from server

**If Dashboard Still Not Updating:**

**Check 1: Verify Network Connection**
```powershell
# Open browser console (F12)
# Look for network errors (red lines)
# Check if API calls are succeeding
```

**Check 2: Clear Browser Cache**
1. Chrome: Settings → Privacy → Clear browsing data
2. Edge: Settings → Privacy → Choose what to clear
3. Firefox: Options → Privacy → Clear Data
4. Select "Cached images and files"
5. Click "Clear data"

**Check 3: Disable Browser Extensions**
- Ad blockers may block dashboard updates
- Try disabling extensions temporarily
- Whitelist your platform domain

**Check 4: Check React Query DevTools (for admins)**
- If enabled, open DevTools
- Check query status
- Look for stale or failed queries

**Still Not Working?**
- Contact your system administrator
- Provide browser console log (F12 → Console tab)
- Mention which metrics aren't updating

---

### Q22: I see "CORS error" in the browser console. What does this mean?

**A:** CORS (Cross-Origin Resource Sharing) errors indicate a configuration issue. This is typically an administrator problem, not a user issue.

**What is CORS?**
CORS is a security mechanism that prevents websites from making requests to different domains without permission.

**Example CORS Error:**
```
Access to fetch at 'https://api.advisor.com/reports/' from origin 'https://advisor.com' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

**What This Means:**
- Frontend (https://advisor.com) is trying to call backend API
- Backend (https://api.advisor.com) is not configured to allow requests from frontend
- Browser blocks the request for security

**For End Users:**
- **This is NOT your fault**
- You cannot fix this yourself
- Contact your system administrator immediately

**For Administrators:**
See ADMIN_GUIDE.md → Environment Variables → CORS Configuration

**Quick Fix:**
```python
# Backend settings.py
CORS_ALLOWED_ORIGINS = [
    "https://advisor.yourcompany.com",
    "https://www.advisor.yourcompany.com",
    "http://localhost:3000",  # Development
]
CORS_ALLOW_CREDENTIALS = True
```

**Workaround for Users:**
- Use incognito/private browsing mode
- Try different browser
- Clear browser cache
- Wait for admin to fix configuration

---

### Q23: Download buttons don't work. Nothing happens when I click them.

**A:** This is a common issue with several possible causes:

**Cause 1: Popup Blocker (80% of cases)**
- **Symptom**: Click download, nothing happens, no error
- **Solution**:
  1. Look for popup blocker icon in address bar
  2. Click to allow popups from this site
  3. Try download again
  - Chrome: Click popup icon, select "Always allow"
  - Edge: Settings → Cookies and site permissions → Popups → Add site
  - Firefox: Options → Privacy → Exceptions → Allow site

**Cause 2: Report Still Generating (10% of cases)**
- **Symptom**: Download buttons are grayed out or disabled
- **Solution**:
  - Check report status badge
  - Wait for "Completed" status (green)
  - Refresh page if stuck in "Processing"
  - Download buttons appear only when report is ready

**Cause 3: Browser Extension Interference (5% of cases)**
- **Symptom**: Click works but download doesn't start
- **Solution**:
  1. Disable browser extensions (especially ad blockers)
  2. Try download again
  3. Enable extensions one by one to find culprit
  - Common culprits: uBlock Origin, AdBlock Plus, Privacy Badger

**Cause 4: Network Issue (3% of cases)**
- **Symptom**: Click works but download fails after few seconds
- **Solution**:
  - Check internet connection
  - Try again
  - Check browser downloads page (Ctrl+J) for error
  - Possible errors: "Network error", "Failed - No file"

**Cause 5: Browser Security Settings (2% of cases)**
- **Symptom**: Browser blocks download as "potentially harmful"
- **Solution**:
  1. Check browser downloads (Ctrl+J)
  2. Click "Keep" or "Allow download"
  3. Whitelist platform domain

**Alternative Download Methods:**

**Method 1: Right-Click**
1. Right-click "Download PDF" button
2. Select "Save link as..."
3. Choose download location
4. Click Save

**Method 2: Open in New Tab**
1. Right-click download button
2. Select "Open link in new tab"
3. File opens in browser
4. Save from browser File menu

**Method 3: Use Different Browser**
- Try Chrome if using Firefox (or vice versa)
- Edge often has fewer restrictions

**Still Not Working?**
1. Clear browser cache (Ctrl+Shift+Delete)
2. Restart browser
3. Try incognito/private mode
4. Contact support with error details

---

### Q24: I accidentally deleted a report. Can I recover it?

**A:** **No**, report deletions are permanent and cannot be undone. However, you have options:

**Recovery Options:**

**Option 1: Regenerate Report**
- If you still have the CSV file:
  1. Upload same CSV again
  2. Select same report type
  3. Generate new report
  4. Result will be identical to deleted report

**Option 2: Check Backups (Admin only)**
- Administrators may have database backups
- Contact your admin
- Provide report ID and deletion timestamp
- Admin may be able to restore from backup
- **Not guaranteed** - depends on backup schedule

**Option 3: Check Email (if notifications enabled)**
- If email notifications are configured
- Check your email for report completion notification
- May contain report details or download link (if link not expired)

**Prevention Tips:**

**For Users:**
- ❌ Don't delete reports unless absolutely necessary
- ✅ Mark reports as inactive instead (if feature available)
- ✅ Download important reports to your computer
- ✅ Keep CSV files in organized folders for easy regeneration

**For Administrators:**
- Enable soft-delete (mark as deleted, don't permanently remove)
- Configure audit logging
- Set up automated backups
- Implement retention policies

**Best Practices:**
1. **Download before deleting**
   - Save HTML and PDF to local drive
   - Archive in OneDrive or SharePoint
   - Keep for compliance/records

2. **Double-check before confirming**
   - Read confirmation dialog carefully
   - Verify you're deleting the correct report
   - Check report name and date

3. **Organize locally**
   ```
   Downloads/
     Azure_Reports/
       2025/
         October/
           Contoso_Executive_2025-10-01.pdf
           Contoso_Detailed_2025-10-01.pdf
         September/
           ...
   ```

---

### Q25: The platform is slow. How can I improve performance?

**A:** Performance can be affected by several factors:

**Client-Side Optimizations (What You Can Do):**

**1. Browser Performance:**
- **Close unused tabs** (each tab uses memory)
- **Disable unnecessary extensions** (ad blockers can slow rendering)
- **Update browser** (use latest version)
- **Clear cache** (Ctrl+Shift+Delete → Clear cache)
- **Use recommended browser** (Chrome or Edge for best performance)

**2. Hardware Resources:**
- **Close other applications** (free up RAM)
- **Check CPU usage** (Task Manager on Windows, Activity Monitor on macOS)
- **Ensure stable internet** (minimum 5 Mbps)
- **Use wired connection** (more stable than WiFi)

**3. Upload Best Practices:**
- **Upload during off-peak hours** (evenings, weekends)
- **One upload at a time** (don't parallel upload)
- **Smaller file sizes** (< 10 MB ideal)
- **Compress large files** (split into multiple CSVs)

**4. Dashboard Optimization:**
- **Limit time range filters** (smaller date ranges load faster)
- **Disable auto-refresh** (if option available)
- **Close unused sections** (minimize panels you're not using)

**Server-Side Issues (Contact Admin):**

**1. High Server Load:**
- Many users processing reports simultaneously
- Ask admin to check server metrics
- Scale up resources if needed

**2. Database Performance:**
- Slow queries
- Admin should run database optimization
- See ADMIN_GUIDE.md → Database Maintenance

**3. Celery Worker Capacity:**
- Insufficient workers for task queue
- Reports stuck in queue
- Admin should scale workers

**Network Troubleshooting:**

```powershell
# Test API response time (Windows PowerShell)
Measure-Command {
    Invoke-WebRequest -Uri "https://your-platform-url/api/health/"
}

# Expected: < 500 ms
# Slow: > 2 seconds
# Problem: > 5 seconds
```

**Expected Performance Benchmarks:**

| Action | Expected Time | Slow | Problem |
|--------|--------------|------|---------|
| Page load | < 2 seconds | 2-5s | > 5s |
| API call | < 500 ms | 0.5-2s | > 2s |
| CSV upload (5 MB) | 10-20 seconds | 20-45s | > 60s |
| Report generation (500 recs) | 2-3 minutes | 3-5min | > 10min |
| Dashboard refresh | < 1 second | 1-3s | > 5s |

**Still Experiencing Issues?**
1. Check platform status page (if available)
2. Contact administrator with performance details
3. Provide browser console log (F12 → Console)
4. Mention specific slow actions

---

## Features and Functionality

### Q26: Can I share reports with people outside my organization?

**A:** Report sharing depends on your organization's configuration and compliance requirements:

**Download and Email (Always Allowed):**
- ✅ Download PDF/HTML to your computer
- ✅ Attach to email and send externally
- ✅ Upload to file sharing service (OneDrive, Dropbox)
- ✅ Print and mail physical copies

**Direct Platform Sharing (May Be Restricted):**
- Platform may have report sharing feature (check with admin)
- Generate shareable link (time-limited, password-protected)
- Link may require recipient to authenticate
- Links can be revoked

**Security Considerations:**
- **Consider data sensitivity**: Reports contain Azure resource names and recommendations
- **Check compliance policies**: Healthcare (HIPAA), finance (SOX), government (FedRAMP) may prohibit external sharing
- **Use secure channels**: Email encryption, secure file transfer
- **Remove sensitive information**: Edit PDF to redact confidential data if needed

**Best Practices for External Sharing:**
1. **Get approval** from manager or security team
2. **Use password-protected PDFs**:
   ```
   Adobe Acrobat → Tools → Protect → Encrypt with Password
   Microsoft Print to PDF (Windows 11) → Security → Require password
   ```
3. **Send password separately** (don't include in same email)
4. **Set expiration date** on shared files
5. **Track who received reports** (maintain log)

**For Clients/External Partners:**
- Create read-only client portal access (ask admin)
- Client logs in with guest account
- View only their own reports
- No access to other clients' data

---

### Q27: Can I export dashboard data to Excel or CSV?

**A:** **Not currently available** in the user interface, but there are workarounds:

**Current Limitations:**
- No built-in export button for dashboard data
- Analytics API exists but requires technical knowledge
- Feature planned for future release

**Workarounds:**

**Option 1: Screenshot/Copy-Paste**
- Take screenshot of dashboard (Windows: Win+Shift+S)
- Copy metrics manually to Excel
- Not ideal but works for quick reports

**Option 2: Use Browser DevTools (Technical)**
```javascript
// Open browser console (F12)
// Paste this code to get dashboard data

fetch('https://your-platform-url/api/analytics/dashboard/')
  .then(res => res.json())
  .then(data => {
    console.log(JSON.stringify(data, null, 2));
    // Copy output and convert to CSV
  });
```

**Option 3: Ask Admin for Database Export**
- Admins have direct database access
- Can export specific data to CSV
- Request custom report from admin

**Option 4: API Access (Developers)**
- Use API endpoints directly
- GET `/api/analytics/dashboard/`
- GET `/api/analytics/trends/?days=30`
- Parse JSON and convert to CSV

**Future Roadmap:**
Version 2.0 will include:
- "Export to Excel" button on dashboard
- Scheduled data exports
- Power BI / Tableau integration
- Custom report builder

**Alternative Approach:**
- Download individual reports as HTML
- Open in Excel (Excel can import HTML tables)
- Extract data from report tables

---

### Q28: What happens when a new version of the platform is released?

**A:** Platform updates are managed by administrators with minimal user disruption:

**Update Process:**

**1. Notification (1 week before)**
- Announcement via email
- In-app notification banner
- Details of new features and changes

**2. Scheduled Maintenance Window**
- Typically: Sunday 2-4 AM (local time)
- Platform unavailable for 30-60 minutes
- Status page shows "Maintenance in Progress"

**3. Deployment**
- Backend and frontend updated simultaneously
- Database migrations run automatically
- No user action required

**4. Post-Update**
- Platform accessible after maintenance
- Clear browser cache (Ctrl+Shift+Delete) if issues
- Test key workflows

**What's Preserved:**
- ✅ All existing reports and data
- ✅ User accounts and settings
- ✅ Client information
- ✅ Historical analytics data

**What Might Change:**
- ⚠️ User interface appearance (minor adjustments)
- ⚠️ New features available (tutorial may appear)
- ⚠️ Deprecated features removed (rare, with advance notice)

**Rollback Plan:**
- If critical issues occur, admin can rollback within 1 hour
- Your work is safe (data not affected by rollback)
- Affected time period: users may experience brief downtime

**Major Version Updates (e.g., 1.0 → 2.0):**
- Extended maintenance window (2-4 hours)
- Additional testing period (beta users)
- Training sessions for new features
- Documentation updates

**How to Prepare:**
1. **Save work before maintenance window**
   - Download any in-progress reports
   - Note any unsaved changes

2. **Clear schedule during maintenance**
   - Don't plan critical report generation during window

3. **Review release notes**
   - Read what's new
   - Watch tutorial videos (if provided)

---

## Billing and Pricing

### Q29: How much does the platform cost?

**A:** Pricing is determined by your organization's subscription model. Contact your administrator or procurement team for pricing details.

**Common Pricing Models:**

**1. Enterprise License (Most Common)**
- Organization pays annual subscription
- Unlimited users
- Unlimited report generation
- Included in IT budget

**2. Per-User License**
- Cost per active user per month
- Typical range: $50-200/user/month (varies by organization)
- Volume discounts available

**3. Consumption-Based**
- Pay per report generated
- Typical range: $5-20/report (depends on report type)
- Monthly invoice

**What's Typically Included:**
- ✅ Unlimited report generation (or per pricing model)
- ✅ All 5 report types
- ✅ Technical support
- ✅ Platform updates and maintenance
- ✅ Data storage and backups

**Additional Costs (May Apply):**
- Azure infrastructure costs (if self-hosted)
- Custom report template design
- Premium support SLA
- Training and onboarding

**For Users:**
- You don't pay directly
- Your organization's IT or finance department manages costs
- Ask your manager or admin for details

---

### Q30: Is there a free trial available?

**A:** Trial availability depends on your organization's procurement process:

**For Organizations:**
- Free trials typically available (30-60 days)
- Contact sales team
- Full access to all features during trial
- No credit card required
- Evaluation support included

**For Individual Users:**
- No individual free trials (enterprise product only)
- Must request through your organization
- Cannot sign up independently

**To Request Trial:**
1. Contact your IT department
2. Request trial for your team/organization
3. IT contacts sales team
4. Trial provisioned (typically within 2 business days)

**Trial Includes:**
- Full feature access
- Up to 25 users
- Unlimited report generation
- Technical support
- Onboarding assistance

**After Trial:**
- Convert to paid subscription
- Export all data if not continuing
- 30-day grace period for data download

---

## Security and Privacy

### Q31: Is my data secure?

**A:** Yes, the platform implements enterprise-grade security:

**Data Encryption:**
- **In transit**: TLS 1.3 (HTTPS) for all communications
- **At rest**: Azure Storage Service Encryption (256-bit AES)
- **Database**: Transparent Data Encryption (TDE)

**Authentication & Authorization:**
- Azure Active Directory integration (enterprise SSO)
- Multi-factor authentication (MFA) supported
- Role-based access control (RBAC)
- Session timeout after inactivity

**Network Security:**
- Web Application Firewall (WAF)
- DDoS protection
- IP whitelisting (optional, admin-configured)
- Private endpoints (for premium deployments)

**Compliance:**
- SOC 2 Type II compliant (Azure infrastructure)
- GDPR compliant (data residency options)
- HIPAA capable (with BAA)
- ISO 27001 certified infrastructure

**Data Isolation:**
- Your organization's data is logically separated
- Multi-tenant architecture with strict isolation
- No data sharing between organizations

**Audit Logging:**
- All actions logged
- Immutable audit trail
- 90-day retention (configurable)

**For Details:**
See Security and Compliance section in API_DOCUMENTATION.md

---

### Q32: Who can see my reports?

**A:** Access control is strictly enforced:

**Within Your Organization:**
- **Your reports**: Always visible to you
- **Managers**: Can see all reports in organization
- **Admins**: Full access to all data
- **Analysts**: See only their own reports + clients they manage
- **Viewers**: Read-only access to shared reports

**Outside Your Organization:**
- ❌ No one (unless you explicitly share)
- ❌ Other Azure Advisor Reports customers cannot see your data
- ❌ Platform administrators cannot access your data (except for support requests with permission)

**Sharing Controls:**
- Share via download (email PDF)
- Share via link (if enabled, time-limited)
- Revoke access at any time

**For Compliance:**
- All access is logged
- Audit trail shows who viewed each report
- GDPR right to access supported

---

## Conclusion

### Still Have Questions?

**Contact Information:**
- **Support Email**: support@yourcompany.com
- **Documentation**: Check USER_MANUAL.md and API_DOCUMENTATION.md
- **Admin Support**: Contact your system administrator
- **Training**: Request onboarding session (training@yourcompany.com)

### Feedback

We value your feedback! If you have:
- Questions not covered in this FAQ
- Suggestions for new features
- Ideas for improvement

Email us at: feedback@yourcompany.com

---

**Last Updated:** October 4, 2025
**Version:** 1.0

**Found an error in this FAQ?** Email documentation@yourcompany.com
